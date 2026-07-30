"""Tools MCP — Référentiels du skill de reporting (acteurs, gabarits, ISIN).

Portage de ``infra/referentiels_skill.py`` vers le serveur MCP **dédié** (D37).
La logique des quatre outils est inchangée ; seules deux corrections y sont
appliquées, signalées en place par ``CORRECTIF AU PORTAGE`` :

  1. ``_identity()`` lit ``claims["roles"]`` (liste) au lieu de ``claims["role"]``
     (singulier, jamais présent) — cf. le contrat de ``jwt_auth`` ;
  2. dans ``ref_adjudications``, la répartition par statut est calculée **sur le
     même périmètre** que la liste retournée.

Ces référentiels vivent dans une base SÉPARÉE de la projection du datahub (D33) :
on ne pollue pas ses tables. Trois tables canoniques + une file d'adjudication
(cf. ``../ddl_referentiels_v0.sql``).

Séparation « proposer ≠ canoniser » (D34) — appliquée DEUX fois :
  1. côté application : ``_require_admin()`` avant tout arbitrage ;
  2. côté base : ``SET LOCAL ROLE`` par transaction (``ref_app`` n'a pas le
     GRANT d'écriture sur le canonique). La base est la vraie frontière ; le
     contrôle applicatif n'est qu'une politesse qui donne un message clair.

Pourquoi un prédicat d'admin distinct de ``rhetores_authz.authorize`` :
``authorize(claims, client_id, store)`` est scopé par **client**, or ces
référentiels sont **globaux** (transverses aux clients). Il n'y a pas de
``client_id`` à autoriser. On lit donc le rôle du périmètre reconstruit par le
middleware, qui le tient du registre utilisateurs — même source de vérité.

Variables d'environnement :
    REFERENTIELS_DATABASE_URL   DSN de la base des référentiels.
                                DÉLIBÉRÉMENT distinct de ``DATABASE_URL`` :
                                c'est ce qui garantit la séparation (D33).
"""
from __future__ import annotations

import os
import json
from contextlib import contextmanager
from typing import Any, Iterator

from mcp.server.fastmcp import FastMCP

from jwt_auth import current_claims
from tools._logging import logged
import user_store

# ---------------------------------------------------------------------------
# Connexion
# ---------------------------------------------------------------------------
# Import différé de psycopg (comme ``tools/datahub.py`` pour ``DatahubStore``) :
# le serveur doit pouvoir démarrer sans ce module si les référentiels ne sont
# pas configurés.

_ENV_DSN = "REFERENTIELS_DATABASE_URL"


def _dsn() -> str:
    dsn = os.environ.get(_ENV_DSN)
    if not dsn:
        raise RuntimeError(
            f"{_ENV_DSN} n'est pas défini : les référentiels du skill ne sont pas "
            "configurés sur cette instance. (Ne PAS retomber sur DATABASE_URL : "
            "la base des référentiels est séparée de la projection du datahub.)"
        )
    return dsn


@contextmanager
def _tx(role: str) -> Iterator[Any]:
    """Ouvre une transaction sous le rôle Postgres demandé.

    ``role`` vaut ``ref_app`` (lecture + proposition) ou ``ref_admin``
    (écriture du canonique). Le rôle de connexion est NOINHERIT : sans ce
    ``SET LOCAL ROLE``, aucune écriture n'est possible. ``SET LOCAL`` est
    annulé à la fin de la transaction, y compris en cas d'erreur.

    Une connexion par appel d'outil, pas de pool : simple et sûr. À remplacer
    par un pool si le dashboard d'adjudication rafraîchit souvent.
    """
    import psycopg  # import différé
    from psycopg.rows import dict_row

    if role not in ("ref_app", "ref_admin"):
        raise ValueError(f"Rôle inattendu : {role!r}")

    with psycopg.connect(_dsn(), row_factory=dict_row) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                # Identifiant statique et validé ci-dessus : pas d'interpolation
                # de valeur utilisateur ici.
                cur.execute(f"SET LOCAL ROLE {role}")
                cur.execute("SET LOCAL search_path TO ref, public")
                yield cur


# ---------------------------------------------------------------------------
# Identité et autorisation
# ---------------------------------------------------------------------------

def _identity() -> tuple[str, bool]:
    """Retourne (email, is_admin) de l'appelant courant.

    Source de vérité : le périmètre reconstruit par ``JWTAuthMiddleware`` depuis
    le registre utilisateurs partagé. Le middleware a déjà résolu l'utilisateur
    et **ignoré** tout rôle porté par le token : les claims de contexte sont donc
    fiables, et il n'y a pas à relire le registre.

    CORRECTIF AU PORTAGE — la version initiale du module lisait
    ``claims.get("role")`` au **singulier**, clé que le middleware ne produit
    jamais (il écrit ``"roles": [user.role]``). Le prédicat retombait donc
    systématiquement sur ``user_store.get_user(oid)``, c'est-à-dire un accès au
    registre — et une lecture disque ou une requête — à **chaque appel d'outil**,
    alors que l'information était déjà en contexte. Le repli reste en place pour
    les claims d'une autre provenance (test unitaire, futur second émetteur),
    mais il n'est plus le chemin normal.

    Repli **fail-safe** : identité inconnue -> non-admin. Cohérent avec le
    deny-by-default assumé de ``tools/datahub.py``.
    """
    claims = current_claims.get() or {}
    email = claims.get("email") or claims.get("preferred_username") or ""

    roles = claims.get("roles")
    if roles is None:
        # Tolérance : claims ne venant pas du middleware de ce serveur.
        single = claims.get("role")
        roles = [single] if single else None

    if roles is None:
        oid = claims.get("oid") or claims.get("sub")
        user = user_store.get_user(oid) if oid else None
        if user is not None:
            role = getattr(user, "role", None)
            roles = [role] if role else []
            email = email or getattr(user, "email", "") or ""
        else:
            roles = []

    return email, ("admin" in roles)


def _require_identified() -> str:
    email, _ = _identity()
    if not email:
        raise PermissionError(
            "Appelant non identifié : impossible de tracer la proposition. "
            "Toute entrée doit porter son auteur (validated_by / propose_par)."
        )
    return email


def _require_admin() -> str:
    email, is_admin = _identity()
    if not is_admin:
        raise PermissionError(
            "Arbitrage réservé à l'administrateur. Un run peut proposer, "
            "il ne canonise jamais (D34)."
        )
    return email


# ---------------------------------------------------------------------------
# Mapping proposition -> table canonique
# ---------------------------------------------------------------------------
# Chaque cible déclare : la table, les colonnes acceptées, celles qui sont
# obligatoires, et la clé de conflit pour l'UPSERT. Rien n'est deviné : une
# colonne absente de cette liste est REFUSÉE plutôt que silencieusement ignorée
# (« rien ne se perd en silence »).

_SPECS: dict[str, dict[str, Any]] = {
    "acteur": {
        "table": "acteurs",
        "conflict": ("code",),
        "requis": ("code", "nom", "role"),
        "colonnes": (
            "code", "nom", "role", "domiciliation", "est_depositaire_tiers",
            "alias", "payload",
        ),
        "jsonb": ("payload",),
    },
    "succession": {
        "table": "acteur_successions",
        "conflict": None,  # pas de clé naturelle : on insère
        "requis": ("predecesseur_code", "successeur_code"),
        "colonnes": (
            "predecesseur_code", "successeur_code", "date_effet", "date_cloture",
            "contexte", "payload",
        ),
        "jsonb": ("payload",),
    },
    # D42 (2026-07-29) — la clé de conflit suit la contrainte d'unicité de la base :
    # `periodicite` en sort, `valide_depuis` y entre. Deux conséquences à ne pas défaire.
    #
    # `periodicite` n'est plus REQUISE : elle n'est pas lisible dans le document chez trois
    # émetteurs sur quatre (offre commerciale chez Spirica, fenêtre YTD chez Cardif, rien du
    # tout chez Himalia). L'exiger obligerait l'appelant à inventer une valeur.
    #
    # `valide_depuis` n'est pas requise non plus, mais pour une autre raison : la base lui donne
    # le défaut '0001-01-01' (« depuis toujours »). Elle ne doit JAMAIS être NULL — deux NULL
    # étant distincts dans une contrainte d'unicité, l'ON CONFLICT ci-dessous ne matcherait
    # jamais et chaque adjudication acceptée insérerait un doublon en silence. Cf.
    # `infra/migration_001_d42_fenetre_validite.sql`.
    "gabarit": {
        "table": "gabarits",
        "conflict": ("emetteur_code", "gabarit", "valide_depuis"),
        "requis": ("emetteur_code", "gabarit", "signature"),
        "colonnes": (
            "emetteur_code", "gabarit", "valide_depuis", "valide_jusqu_a",
            "periodicite", "template_id_natif",
            "signature", "n_pages_indicatif", "extraction_hints",
            "champs_publies", "invariant_controle", "emetteur_lisible",
        ),
        "jsonb": ("signature", "extraction_hints", "champs_publies"),
    },
    "isin": {
        "table": "isin",
        "conflict": ("isin",),
        "requis": ("isin",),
        "colonnes": ("isin", "label", "class_code", "geo_code", "sri", "source"),
        "jsonb": (),
    },
}


def _upsert_canonique(cur, cible: str, proposition: dict, email: str) -> dict:
    """Écrit une proposition acceptée dans sa table canonique.

    Appelé UNIQUEMENT sous le rôle ``ref_admin``, dans la transaction de
    l'arbitrage : accepter et écrire sont atomiques.
    """
    spec = _SPECS[cible]

    inconnues = set(proposition) - set(spec["colonnes"])
    if inconnues:
        raise ValueError(
            f"Champs non reconnus pour la cible {cible!r} : {sorted(inconnues)}. "
            "Refusés plutôt qu'ignorés — corriger la proposition ou étendre le schéma "
            "(et l'inscrire au registre des écarts)."
        )
    manquants = [c for c in spec["requis"] if proposition.get(c) in (None, "")]
    if manquants:
        raise ValueError(f"Champs obligatoires manquants pour {cible!r} : {manquants}")

    cols = [c for c in spec["colonnes"] if c in proposition]
    vals = [
        json.dumps(proposition[c], ensure_ascii=False) if c in spec["jsonb"] else proposition[c]
        for c in cols
    ]

    # Une entrée arbitrée est, par construction, validée par l'admin.
    cols += ["provenance", "confiance", "validated_by"]
    vals += ["valide_admin", "high", email]

    placeholders = ", ".join(["%s"] * len(cols))
    collist = ", ".join(cols)

    if spec["conflict"]:
        maj = [c for c in cols if c not in spec["conflict"]]
        set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in maj)
        sql = (
            f"INSERT INTO {spec['table']} ({collist}) VALUES ({placeholders}) "
            f"ON CONFLICT ({', '.join(spec['conflict'])}) DO UPDATE SET {set_clause}, "
            f"version = {spec['table']}.version + 1 "
            f"RETURNING *"
        )
    else:
        sql = f"INSERT INTO {spec['table']} ({collist}) VALUES ({placeholders}) RETURNING *"

    cur.execute(sql, vals)
    return cur.fetchone()


def _jsonable(row: dict | None) -> dict | None:
    """Rend une ligne sérialisable (dates, uuid) sans dépendre du codec JSON."""
    if row is None:
        return None
    out = {}
    for k, v in row.items():
        out[k] = v if isinstance(v, (str, int, float, bool, type(None), list, dict)) else str(v)
    return out


# Champs de pure traçabilité, retirés du BUNDLE (jamais de la base). Le skill ne les lit pas :
# il consomme des référentiels, il n'audite pas leur cycle de vie. Mesuré le 2026-07-29 sur le
# premier bundle réel (17 acteurs + 2 successions + 9 gabarits + 261 ISIN) : 185 ko, 4 936
# lignes, dont 1 732 de métadonnées — assez pour dépasser la limite d'un résultat d'outil MCP.
#
# `provenance` et `confiance` sont CONSERVÉS : ce sont des enums courts, et la confiance est une
# information métier que le skill peut légitimement pondérer (B9). `id` reste aussi, il sert de
# référence stable dans une proposition de mise à jour.
_CHAMPS_AUDIT = ("created_at", "updated_at", "version", "validated_by")

SECTIONS = ("acteurs", "successions", "gabarits", "isin")

# ---------------------------------------------------------------------------
# Contrat d'outil et détection du retrait silencieux d'arguments
# ---------------------------------------------------------------------------
# Le problème, constaté DEUX fois le 2026-07-29 : le client MCP met le schéma des outils en
# cache. Quand le serveur gagne un paramètre, un client au schéma périmé **retire l'argument de
# l'appel sans un mot**. La première fois, `ref_bundle(sections=…)` a rendu tout le bundle en
# ignorant le filtre. La seconde, plus grave, `ref_propose` a enregistré une proposition dont les
# trois champs de provenance étaient à `null` — donc une provenance qui **paraissait vide par
# choix de l'appelant** alors qu'elle avait été perdue en transport. Un arbitre n'avait aucun
# moyen de le savoir.
#
# LA FAUSSE BONNE IDÉE, écartée : faire déclarer sa version au client. Un appelant parfaitement à
# jour qui omettrait ce champ serait alors accusé d'être en retard — on échangerait un faux
# négatif silencieux contre un faux positif bruyant, et personne ne fait confiance à un contrôle
# qui accuse à tort.
#
# CE QU'ON PEUT SAVOIR AVEC CERTITUDE : non pas ce que le client EST, mais ce que le serveur A
# REÇU. Le signal est donc **descriptif, jamais accusatoire** — deux mécanismes :
#
#   1. Le serveur annonce SON contrat (`CONTRAT_OUTIL`). L'appelant compare à ce qu'il attendait.
#   2. Chaque écriture **renvoie ce qu'elle a reçu** pour les champs qui comptent. Un argument
#      retiré en route se voit immédiatement dans la réponse, sans rien supposer de personne.
#
# Aucun faux positif possible : la réponse énonce des faits. Et cela couvre TOUT argument perdu,
# pas seulement ceux qu'on avait anticipés.
CONTRAT_OUTIL = "2026-07-29.d44"


def _alleger(lignes: list[dict]) -> list[dict]:
    return [{k: v for k, v in l.items() if k not in _CHAMPS_AUDIT} for l in lignes]


# ---------------------------------------------------------------------------
# Enregistrement des tools
# ---------------------------------------------------------------------------

def register(mcp: FastMCP) -> None:

    @mcp.tool()
    @logged
    async def ref_bundle(sections: list[str] | None = None) -> dict:
        """Retourne les référentiels canoniques du skill.

        Appelé au début d'un run de reporting. C'est ce qui remplace la copie vendorée
        dans le paquet du skill (D36) — un gabarit validé est donc visible au run suivant
        de N'IMPORTE QUEL CGP, sans réinstallation.

        ``sections`` : sous-ensemble de 'acteurs' | 'successions' | 'gabarits' | 'isin'.
        Par défaut, tout est retourné.

        Pourquoi ce paramètre existe, alors que la version initiale affirmait « les
        référentiels sont petits et lus en entier : pas de pagination » — cette phrase
        était vraie sur une base vide, elle a cessé de l'être au premier chargement réel.
        Mesuré le 2026-07-29 : 185 ko et 4 936 lignes, **au-delà de ce qu'un résultat
        d'outil MCP peut porter**. Les 261 ISIN en font près de 70 % à eux seuls, alors
        que la plupart des besoins d'un run ne portent que sur les gabarits ou les
        acteurs. Demander une section, c'est donc l'usage normal ; tout demander reste
        possible et le restera, mais ne passera pas toujours.

        Le compte porte TOUJOURS sur les quatre tables, même si une seule est demandée :
        sans quoi un appel partiel pourrait se lire comme une base à moitié vide.
        """
        _require_identified()
        if sections is None:
            demandees = set(SECTIONS)
        else:
            inconnues = [s for s in sections if s not in SECTIONS]
            if inconnues:
                raise ValueError(
                    f"Section(s) inconnue(s) : {inconnues} (attendu : {list(SECTIONS)})")
            demandees = set(sections)

        vide: list[dict] = []
        acteurs = successions = gabarits = isins = vide
        with _tx("ref_app") as cur:
            cur.execute("SELECT valeur FROM ref_meta WHERE cle = 'schema_version'")
            row = cur.fetchone()
            schema_version = row["valeur"] if row else None

            # Les comptes sont lus séparément du contenu : un appel partiel doit quand même
            # dire la vérité sur l'état de la base.
            cur.execute(
                "SELECT (SELECT count(*) FROM acteurs) AS acteurs,"
                "       (SELECT count(*) FROM acteur_successions) AS successions,"
                "       (SELECT count(*) FROM gabarits) AS gabarits,"
                "       (SELECT count(*) FROM isin) AS isin")
            compte = dict(cur.fetchone())

            if "acteurs" in demandees:
                cur.execute("SELECT * FROM acteurs ORDER BY code")
                acteurs = _alleger([_jsonable(r) for r in cur.fetchall()])
            if "successions" in demandees:
                cur.execute("SELECT * FROM acteur_successions "
                            "ORDER BY predecesseur_code, date_effet NULLS LAST")
                successions = _alleger([_jsonable(r) for r in cur.fetchall()])
            if "gabarits" in demandees:
                # Tri par la clé réelle (D42) : la périodicité n'en fait plus partie, et
                # `valide_depuis` place les versions d'un gabarit dans l'ordre chronologique.
                cur.execute("SELECT * FROM gabarits "
                            "ORDER BY emetteur_code, gabarit, valide_depuis")
                gabarits = _alleger([_jsonable(r) for r in cur.fetchall()])
            if "isin" in demandees:
                cur.execute("SELECT * FROM isin ORDER BY isin")
                isins = _alleger([_jsonable(r) for r in cur.fetchall()])

        resultat = {
            "schema_version": schema_version,
            "contrat_outil": CONTRAT_OUTIL,
            "sections_recues": sections,          # ce que l'appel portait vraiment
            "sections_retournees": sorted(demandees),
            "acteurs": acteurs,
            "successions": successions,
            "gabarits": gabarits,
            "isin": isins,
            "compte": compte,
            "_note": (
                "Les champs de pure traçabilité (created_at, updated_at, version, "
                "validated_by) sont retirés du bundle — ils restent en base. `compte` porte "
                "sur les quatre tables, y compris celles non demandées."
                if sections is None else
                f"Sections demandées : {sorted(demandees)}. Les autres tableaux sont vides par "
                f"choix de l'appelant, PAS parce que la base l'est — voir `compte`."
            ),
        }
        if sections is None:
            # Même ambiguïté que pour la provenance de `ref_propose`, et même traitement : on
            # énonce les deux lectures sans en choisir une. Ici l'enjeu est concret — le bundle
            # complet dépasse la taille qu'un résultat d'outil peut porter, donc un `sections`
            # retiré en route se manifeste par un échec de transport, pas par un mauvais résultat.
            resultat["avertissement_sections"] = (
                "Aucune section demandée : tout est retourné. Deux lectures possibles, et le "
                "serveur ne peut pas les distinguer : soit l'appel n'en demandait pas, soit "
                "l'argument `sections` a été RETIRÉ en route par un schéma d'outil en cache. Si "
                f"vous l'avez bien passé, votre client ne connaît pas le contrat {CONTRAT_OUTIL} : "
                "rafraîchissez la liste des outils (relancer Cowork). Attention, le bundle "
                "complet dépasse souvent la taille qu'un résultat d'outil peut porter."
            )
        return resultat

    @mcp.tool()
    @logged
    async def ref_propose(
        cible: str,
        nature: str,
        cle: dict,
        proposition: dict,
        motif: str | None = None,
        source_empreinte: str | None = None,
        source_gabarit: str | None = None,
        source_arrete: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        """Dépose une proposition dans la file d'adjudication.

        Ouvert à tout appelant authentifié : un run PROPOSE. Il ne canonise
        jamais — l'écriture du canonique exige le rôle admin (D34).

        ``cible`` : 'acteur' | 'succession' | 'gabarit' | 'isin'
        ``nature`` : 'nouvel_emetteur' | 'nouveau_gabarit' | 'variante_periodicite'
                   | 'nouvel_acteur' | 'nouvelle_succession' | 'nouvel_isin'
                   | 'mise_a_jour'
        Les trois premières sont les natures de N6 : elles n'appellent pas le
        même arbitrage, d'où leur distinction explicite.

        **La provenance ne porte plus de nom de fichier (D44).** Elle se décrit par trois
        champs : ``source_empreinte`` (sha256 du CONTENU du document), ``source_gabarit``
        (le gabarit apparié) et ``source_arrete`` (la date d'arrêté). Motif : ce store est
        rendu **en entier à chaque CGP** par ``ref_bundle``, or un nom de fichier porte le
        client en clair (« Relevé Himalia Capi HANAMI.pdf ») — ce serait une divulgation
        entre confrères. Le remplacement est aussi **plus utile** à l'arbitre : l'empreinte
        du contenu reconnaît deux propositions issues du même document, ce qu'un nom de
        fichier ne garantit jamais.
        """
        email = _require_identified()
        if cible not in _SPECS:
            raise ValueError(f"Cible inconnue : {cible!r} (attendu : {sorted(_SPECS)})")

        # Refus explicite plutôt qu'écriture silencieuse dans une colonne disparue : un vieux
        # client qui passerait encore `source_document` doit l'apprendre, pas voir sa provenance
        # avalée. C'est la leçon du paramètre `sections` retiré en silence par un schéma en cache.
        if source_empreinte is not None and len(source_empreinte) not in (0, 64):
            raise ValueError(
                f"source_empreinte doit être un sha256 hexadécimal (64 caractères), "
                f"reçu {len(source_empreinte)} caractères. Ne PAS y mettre un nom de fichier : "
                f"le store est lu par tous les CGP (D44)."
            )

        with _tx("ref_app") as cur:
            cur.execute(
                "INSERT INTO adjudications "
                "(cible, nature, cle, proposition, motif, "
                " source_empreinte, source_gabarit, source_arrete, run_id, propose_par) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "RETURNING id, propose_le, statut",
                (cible, nature, json.dumps(cle, ensure_ascii=False),
                 json.dumps(proposition, ensure_ascii=False),
                 motif, source_empreinte, source_gabarit, source_arrete, run_id, email),
            )
            row = cur.fetchone()

        # La provenance REÇUE est renvoyée telle quelle. C'est le garde-fou contre le retrait
        # silencieux d'argument par un schéma en cache : si l'appelant a passé une empreinte et
        # lit `null` ici, il sait immédiatement qu'elle a été perdue en route — sans que le
        # serveur ait à deviner quoi que ce soit de son client.
        provenance_recue = {"source_empreinte": source_empreinte,
                            "source_gabarit": source_gabarit,
                            "source_arrete": source_arrete}
        reponse = {"adjudication_id": str(row["id"]), "statut": row["statut"],
                   "propose_le": str(row["propose_le"]), "propose_par": email,
                   "contrat_outil": CONTRAT_OUTIL,
                   "provenance_recue": provenance_recue}

        if not any(provenance_recue.values()):
            # Un constat, pas une accusation : on ne peut pas distinguer « l'appelant n'avait pas
            # de provenance » de « le client a retiré les arguments ». On énonce donc les deux
            # lectures possibles et on laisse l'appelant trancher — lui sait ce qu'il a envoyé.
            reponse["avertissement_provenance"] = (
                "Aucune provenance enregistrée. Deux lectures possibles, et le serveur ne peut pas "
                "les distinguer : soit l'appel n'en portait pas, soit les arguments "
                "`source_empreinte` / `source_gabarit` / `source_arrete` ont été RETIRÉS en route "
                "par un schéma d'outil en cache. Si vous les avez bien passés, votre client ne "
                f"connaît pas encore le contrat {CONTRAT_OUTIL} : rafraîchissez la liste des "
                "outils (relancer Cowork) et rejouez la proposition."
            )
        return reponse

    @mcp.tool()
    @logged
    async def ref_adjudications(statut: str = "en_attente",
                               limit: int = 50, offset: int = 0) -> dict:
        """Liste la file d'adjudication — alimente le dashboard admin.

        L'admin voit toutes les propositions ; un non-admin ne voit que les
        siennes (même philosophie de grain fin que ``tools/datahub.py``).
        """
        email, is_admin = _identity()
        if not email:
            raise PermissionError("Appelant non identifié.")
        if statut not in ("en_attente", "accepte", "rejete", "tous"):
            raise ValueError(f"Statut inattendu : {statut!r}")

        clauses, params = [], []
        if statut != "tous":
            clauses.append("statut = %s")
            params.append(statut)
        if not is_admin:
            clauses.append("propose_par = %s")
            params.append(email)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params += [min(limit, 500), offset]

        with _tx("ref_app") as cur:
            cur.execute(
                f"SELECT * FROM adjudications {where} "
                f"ORDER BY propose_le DESC LIMIT %s OFFSET %s", params)
            lignes = [_jsonable(r) for r in cur.fetchall()]

            # CORRECTIF AU PORTAGE — la répartition était calculée sur TOUTE la
            # table, y compris pour un non-admin dont la liste est filtrée : un
            # CGP apprenait le volume global de propositions de ses confrères
            # (et, par différence, celui des autres). Fuite modeste mais gratuite.
            # La répartition suit désormais le même périmètre que la liste, et
            # elle porte sur TOUS les statuts (pas seulement celui demandé) :
            # c'est ce qui permet au dashboard d'afficher ses compteurs d'onglets.
            if is_admin:
                cur.execute("SELECT statut, count(*) AS n FROM adjudications GROUP BY statut")
            else:
                cur.execute(
                    "SELECT statut, count(*) AS n FROM adjudications "
                    "WHERE propose_par = %s GROUP BY statut", (email,))
            repartition = {r["statut"]: r["n"] for r in cur.fetchall()}

        return {"adjudications": lignes, "repartition": repartition,
                "portee": "toutes" if is_admin else "les vôtres"}

    @mcp.tool()
    @logged
    async def ref_arbitrer(adjudication_id: str, decision: str,
                          commentaire: str | None = None) -> dict:
        """Arbitre une proposition — ADMIN uniquement.

        ``decision`` : 'accepte' ou 'rejete'. Sur 'accepte', l'écriture dans la
        table canonique et le marquage de la proposition se font dans la MÊME
        transaction : on ne peut pas accepter sans écrire, ni écrire sans tracer.

        Un rejet est tracé, pas supprimé : on garde qui a décidé et pourquoi.
        """
        email = _require_admin()
        if decision not in ("accepte", "rejete"):
            raise ValueError(f"Décision inattendue : {decision!r}")

        with _tx("ref_admin") as cur:
            cur.execute(
                "SELECT * FROM adjudications WHERE id = %s FOR UPDATE",
                (adjudication_id,))
            adj = cur.fetchone()
            if adj is None:
                raise ValueError(f"Adjudication inconnue : {adjudication_id!r}")
            if adj["statut"] != "en_attente":
                raise ValueError(
                    f"Déjà arbitrée ({adj['statut']}) par {adj['arbitre_par']} "
                    f"le {adj['arbitre_le']}.")

            ecrit = None
            if decision == "accepte":
                ecrit = _upsert_canonique(cur, adj["cible"], adj["proposition"], email)

            cur.execute(
                "UPDATE adjudications SET statut = %s, arbitre_par = %s, "
                "arbitre_le = now(), commentaire_arbitrage = %s WHERE id = %s",
                (decision, email, commentaire, adjudication_id))

        return {"adjudication_id": adjudication_id, "decision": decision,
                "arbitre_par": email, "entree_canonique": _jsonable(ecrit)}
