"""Tools MCP — Référentiels du skill de reporting (acteurs, gabarits, ISIN).

À déposer dans ``mcp-o2s-server/tools/referentiels_skill.py`` et enregistrer
dans ``server.py`` (``referentiels_skill.register(mcp)``).

⚠️ Ne pas confondre avec ``tools/referentials.py``, qui est un proxy de lecture
vers les référentiels **O2S** (assets/products/institutions). Ce module-ci sert
les référentiels **du skill de reporting**, dans une base SÉPARÉE de la
projection du datahub (D33) : on ne pollue pas ses tables.

Trois tables canoniques + une file d'adjudication (cf. ``ddl_referentiels_v0.sql``).

Séparation « proposer ≠ canoniser » (D34) — appliquée DEUX fois :
  1. côté application : ``_require_admin()`` avant tout arbitrage ;
  2. côté base : ``SET LOCAL ROLE`` par transaction (``ref_app`` n'a pas le
     GRANT d'écriture sur le canonique). La base est la vraie frontière ; le
     contrôle applicatif n'est qu'une politesse qui donne un message clair.

Pourquoi un prédicat d'admin distinct de ``rhetores_authz.authorize`` :
``authorize(claims, client_id, store)`` est scopé par **client**, or ces
référentiels sont **globaux** (transverses aux clients). Il n'y a pas de
``client_id`` à autoriser. On lit donc le rôle du registre utilisateurs
(``user_store.get_user``), même source de vérité que le middleware JWT.

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

    Source de vérité : le registre utilisateurs partagé (``user_store``), le
    même que celui du middleware JWT — pas une seconde instance. Le rôle est lu
    des claims s'il y figure déjà (le middleware reconstruit le périmètre),
    sinon résolu par ``get_user(oid)``.

    Repli **fail-safe** : identité inconnue -> non-admin. Cohérent avec le
    deny-by-default assumé de ``tools/datahub.py``.
    """
    claims = current_claims.get() or {}
    email = claims.get("email") or claims.get("preferred_username") or ""
    role = claims.get("role")

    if role is None:
        oid = claims.get("oid") or claims.get("sub")
        user = user_store.get_user(oid) if oid else None
        if user is not None:
            role = getattr(user, "role", None)
            email = email or getattr(user, "email", "") or ""

    return email, (role == "admin")


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
    "gabarit": {
        "table": "gabarits",
        "conflict": ("emetteur_code", "gabarit", "periodicite"),
        "requis": ("emetteur_code", "gabarit", "periodicite", "signature"),
        "colonnes": (
            "emetteur_code", "gabarit", "periodicite", "template_id_natif",
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


# ---------------------------------------------------------------------------
# Enregistrement des tools
# ---------------------------------------------------------------------------

def register(mcp: FastMCP) -> None:

    @mcp.tool()
    @logged
    async def ref_bundle() -> dict:
        """Retourne l'intégralité des référentiels canoniques du skill.

        Appelé une fois au début d'un run de reporting. Les référentiels sont
        petits et lus en entier : pas de pagination, pas de requête par ligne.
        C'est ce qui remplace la copie vendorée dans le paquet du skill (D36) —
        un gabarit validé est donc visible au run suivant de N'IMPORTE QUEL
        CGP, sans réinstallation.
        """
        _require_identified()
        with _tx("ref_app") as cur:
            cur.execute("SELECT valeur FROM ref_meta WHERE cle = 'schema_version'")
            row = cur.fetchone()
            schema_version = row["valeur"] if row else None

            cur.execute("SELECT * FROM acteurs ORDER BY code")
            acteurs = [_jsonable(r) for r in cur.fetchall()]
            cur.execute(
                "SELECT * FROM acteur_successions ORDER BY predecesseur_code, date_effet NULLS LAST"
            )
            successions = [_jsonable(r) for r in cur.fetchall()]
            cur.execute("SELECT * FROM gabarits ORDER BY emetteur_code, gabarit, periodicite")
            gabarits = [_jsonable(r) for r in cur.fetchall()]
            cur.execute("SELECT * FROM isin ORDER BY isin")
            isins = [_jsonable(r) for r in cur.fetchall()]

        return {
            "schema_version": schema_version,
            "acteurs": acteurs,
            "successions": successions,
            "gabarits": gabarits,
            "isin": isins,
            "compte": {
                "acteurs": len(acteurs), "successions": len(successions),
                "gabarits": len(gabarits), "isin": len(isins),
            },
        }

    @mcp.tool()
    @logged
    async def ref_propose(
        cible: str,
        nature: str,
        cle: dict,
        proposition: dict,
        motif: str | None = None,
        source_document: str | None = None,
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
        """
        email = _require_identified()
        if cible not in _SPECS:
            raise ValueError(f"Cible inconnue : {cible!r} (attendu : {sorted(_SPECS)})")

        with _tx("ref_app") as cur:
            cur.execute(
                "INSERT INTO adjudications "
                "(cible, nature, cle, proposition, motif, source_document, run_id, propose_par) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id, propose_le, statut",
                (cible, nature, json.dumps(cle, ensure_ascii=False),
                 json.dumps(proposition, ensure_ascii=False),
                 motif, source_document, run_id, email),
            )
            row = cur.fetchone()

        return {"adjudication_id": str(row["id"]), "statut": row["statut"],
                "propose_le": str(row["propose_le"]), "propose_par": email}

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
            cur.execute(
                "SELECT statut, count(*) AS n FROM adjudications GROUP BY statut")
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
