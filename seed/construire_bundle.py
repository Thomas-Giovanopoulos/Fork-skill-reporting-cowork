#!/usr/bin/env python3
"""Assemble le seed des référentiels — deux sorties, une seule source.

    python3 seed/construire_bundle.py

Produit :
  seed/referentiels.json   le bundle au format du contrat (§3 du RUNBOOK).
                           Utilisable IMMÉDIATEMENT par le skill, sans aucune infra :
                           c'est le substitut fidèle de l'appel MCP `ref_bundle`.
  seed/seed.sql            les INSERT pour charger la base (jalon B4), à passer à psql.

Pourquoi les deux : le sandbox du skill n'a pas d'accès réseau et ne peut pas joindre
Postgres. La conversation skill ↔ base passe par un FICHIER. Le bundle JSON est donc
le contrat, et la base n'en est qu'une provenance possible (D35/D36).

Contrôles avant écriture — rien ne sort si l'intégrité n'est pas vérifiée :
  - unicité des codes d'acteur ;
  - `valide_depuis` présent et non null sur CHAQUE gabarit (voir plus bas) ;
  - unicité du triplet (emetteur_code, gabarit, valide_depuis) — D42 ;
  - cohérence de la fenêtre de validité (valide_jusqu_a >= valide_depuis) ;
  - toute référence d'acteur (gabarits, successions) résolue ;
  - AUCUN identifiant client, nulle part — ni dans ce qui part en base, ni dans le bundle
    vendoré (D44, voir le bloc « garde-fou D44 » plus bas).

La périodicité est SORTIE de la clé (D42) : elle n'est pas lisible dans le document chez trois
émetteurs sur quatre, et ses tokens candidats sont des faux amis (offre commerciale chez Spirica,
fenêtre de cumul YTD chez Cardif, durée de contrat chez Himalia). C'est la fenêtre de validité qui
la remplace, parce qu'un émetteur change de maquette : Cardif a produit deux gabarits en douze mois
et une seule ancre sur onze survit de l'un à l'autre. Cf. infra/migration_001_d42_fenetre_validite.sql.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
FORK = ICI.parent
ISIN_CSV = FORK / "skill" / "assets" / "isin_referentiel_v0.csv"

SCHEMA_VERSION = "0.1-skill"


# =========================================================================== garde-fou D44
# `ref_bundle` rend le store EN ENTIER à CHAQUE CGP — c'est tout l'objet de D36. Conséquence
# rarement énoncée : **tout identifiant client qui entre dans cette base est visible de tous
# les CGP.** Ce n'est pas une précaution de conformité, c'est une divulgation entre confrères,
# et elle était opérante en local avant la migration 002.
#
# Le contrôle est donc au même rang que `valide_depuis` : il BLOQUE l'écriture, il n'avertit
# pas. Un garde-fou qui n'échoue pas est un garde-fou qu'on ne sait pas lire — celui-ci a été
# vérifié en injectant un faux identifiant dans le seed et en constatant le refus, avec le
# chemin JSON fautif nommé. Cf. infra/migration_002_purge_identifiants_clients.sql, qui pose
# la même barrière côté base (CHECK succession_contexte_sans_reference).
#
# Ce qu'il faut retenir de la règle de réécriture : on ne SUPPRIME pas la provenance, on la
# DÉ-IDENTIFIE. Une provenance a une valeur réelle — savoir sur quoi une ancre a été établie.
# Ce qui compte est le TYPE de document et le NOMBRE de réplicats, jamais le client.

# Forme des références rencontrées chez Wealins et Quintet : deux lettres suivies de cinq à huit
# chiffres (forme synthétique 'AB1234567'). Les valeurs réelles ne sont volontairement PAS citées
# ici — documenter une fuite en la recopiant la laisse ouverte. Motif volontairement étroit : une
# contrainte trop large serait désactivée au premier faux positif, ce qui est pire qu'aucune.
MOTIF_REFERENCE_CONTRAT = re.compile(r"[A-Z]{2}[0-9]{5,8}")

# Un ISIN est un code de MARCHÉ, pas un identifiant client — et il a exactement la forme d'une
# référence de contrat : `DK0062498333` (Novo Nordisk) contient « K0062498 ». On retire donc les
# ISIN bien formés AVANT de chercher. Sans cette soustraction le garde-fou se déclenche sur les
# 261 lignes ISIN du seed, personne ne le croit, et il finit désarmé.
MOTIF_ISIN = re.compile(r"\b[A-Z]{2}[0-9A-Z]{9}[0-9]\b")

# Noms de clients et d'entités clientes connus du corpus. `interagyr` est le piège : les quatre
# fichiers « Interagyr » ne désignent PAS un partenaire ni un émetteur — c'est un CLIENT
# (découverte A.1-1 de l'étude de signature). Il se purge au même titre que « gronier ».
# `cerise` / `pollux` sont deux contrats clients du corpus Spirica, même nature.
NOMS_CLIENTS = ("hanami", "shida", "matsu", "gronier", "interagyr", "cerise", "pollux")

# La colonne `source` du CSV des ISIN porte des noms de clients ('gronier_categories',
# 'interagyr_valide') et part TELLE QUELLE dans `isin.source` en base. Le CSV est un asset du
# skill, hors périmètre d'écriture : la dé-identification se fait donc ici, à l'assemblage.
# Les libellés restent distincts entre eux — l'information conservée est le type de source.
SOURCE_ISIN_DEIDENTIFIEE = {
    "gronier_categories": "excel_categories_run_reel",
    "gronier_T2_run": "run_reel_T2",
    "interagyr_valide": "reporting_mandat_valide",
}


def deidentifier_source_isin(valeur: str | None) -> str | None:
    """Réécrit la colonne `source` du CSV ISIN, jeton par jeton (séparateur '+')."""
    if not valeur:
        return valeur
    return "+".join(SOURCE_ISIN_DEIDENTIFIEE.get(j, j) for j in valeur.split("+"))


def _textes(noeud, chemin: str):
    """Rend (chemin JSON, texte) pour toute chaîne atteignable — clés de dict incluses."""
    if isinstance(noeud, dict):
        for cle, val in noeud.items():
            enfant = f"{chemin}.{cle}"
            if isinstance(cle, str):
                yield (f"{enfant} (nom de clé)", cle)
            yield from _textes(val, enfant)
    elif isinstance(noeud, (list, tuple)):
        for i, val in enumerate(noeud):
            yield from _textes(val, f"{chemin}[{i}]")
    elif isinstance(noeud, str):
        yield (chemin, noeud)


def chercher_identifiants_clients(racine, etiquette: str) -> list[tuple[str, str]]:
    """Parcours récursif. Rend la liste des (chemin fautif, ce qui a été reconnu)."""
    trouves: list[tuple[str, str]] = []
    for chemin, texte in _textes(racine, etiquette):
        reste = MOTIF_ISIN.sub(" ", texte)
        for m in MOTIF_REFERENCE_CONTRAT.finditer(reste):
            trouves.append((chemin, f"référence de contrat {m.group(0)!r}"))
        bas = texte.lower()
        for nom in NOMS_CLIENTS:
            if nom in bas:
                trouves.append((chemin, f"nom de client {nom!r}"))
    return trouves


def charger(nom: str) -> dict:
    with open(ICI / nom, encoding="utf-8") as f:
        return json.load(f)


def charger_isin() -> list[dict]:
    """Promeut l'asset CSV v0 tel quel — mêmes colonnes que la table (E1/E4)."""
    if not ISIN_CSV.exists():
        print(f"  ! {ISIN_CSV.name} introuvable : bundle produit sans ISIN.", file=sys.stderr)
        return []
    with open(ISIN_CSV, encoding="utf-8-sig", newline="") as f:
        lignes = []
        for r in csv.DictReader(f):
            if not (r.get("isin") or "").strip():
                continue
            sri = (r.get("sri") or "").strip()
            lignes.append({
                "isin": r["isin"].strip(),
                "label": (r.get("label") or "").strip() or None,
                "class_code": (r.get("class_code") or "").strip() or None,
                # geo vide = NON TAGUÉ, jamais une géographie fausse (règles GEO).
                "geo_code": (r.get("geo_code") or "").strip() or None,
                "sri": int(sri) if sri.isdigit() else None,
                # D44 : la colonne `source` du CSV nomme des clients ; elle est
                # dé-identifiée ICI, avant d'atteindre le bundle et la base.
                "source": deidentifier_source_isin((r.get("source") or "").strip()) or None,
                # La confiance du CSV fait foi : 'high' = validé par Tristan.
                "confiance": (r.get("confidence") or "medium").strip() or "medium",
                "provenance": "seed",
            })
    return lignes


def verifier(acteurs, successions, gabarits) -> list[str]:
    erreurs = []
    codes = [a["code"] for a in acteurs]
    doublons = {c for c in codes if codes.count(c) > 1}
    if doublons:
        erreurs.append(f"codes d'acteur en doublon : {sorted(doublons)}")
    connus = set(codes)

    triplets = []
    for g in gabarits:
        if g["emetteur_code"] not in connus:
            erreurs.append(
                f"gabarit {g['gabarit']!r} : emetteur_code {g['emetteur_code']!r} inconnu "
                "(la clé étrangère vers les acteurs est le lien entre les deux tables, D22)")

        # `valide_depuis` NON NULL, sans exception. Ce n'est pas du zèle : en SQL deux NULL sont
        # DISTINCTS dans une contrainte d'unicité, donc deux profils (cardif, x, NULL) passeraient
        # tous les deux et `gabarit_version_unique` ne protégerait plus rien. Pire, une cible d'ON
        # CONFLICT contenant un NULL ne matche JAMAIS : chaque adjudication acceptée par
        # `ref_arbitrer` insérerait un doublon au lieu de mettre à jour, silencieusement, et
        # `ref_bundle` rendrait plusieurs profils pour le même gabarit. La convention est donc
        # '0001-01-01' = « depuis toujours » (colonne NOT NULL DEFAULT '0001-01-01').
        # Cf. infra/migration_001_d42_fenetre_validite.sql, § « le piège qui justifie le NOT NULL ».
        if not g.get("valide_depuis"):
            erreurs.append(
                f"gabarit {g['emetteur_code']}/{g['gabarit']} : `valide_depuis` absent ou null. "
                "Écrire '0001-01-01' (« depuis toujours »), jamais null : la colonne est NOT NULL "
                "DEFAULT '0001-01-01', deux NULL sont distincts dans une contrainte d'unicité, et "
                "une cible d'ON CONFLICT contenant un NULL ne matche jamais — l'UPSERT de "
                "ref_arbitrer insérerait des doublons au lieu de mettre à jour (migration_001).")
        elif g.get("valide_jusqu_a") and g["valide_jusqu_a"] < g["valide_depuis"]:
            erreurs.append(
                f"gabarit {g['emetteur_code']}/{g['gabarit']} : fenêtre incohérente "
                f"({g['valide_depuis']} → {g['valide_jusqu_a']}) — CHECK gabarit_fenetre_coherente.")

        triplets.append((g["emetteur_code"], g["gabarit"], g.get("valide_depuis")))
    dbl = {c for c in triplets if triplets.count(c) > 1}
    if dbl:
        erreurs.append(
            "triplets (émetteur, gabarit, valide_depuis) en doublon : "
            f"{sorted(str(c) for c in dbl)} — c'est la clé d'unicité gabarit_version_unique (D42). "
            "Deux versions d'un même gabarit se distinguent par leur date de début de validité.")

    for s in successions:
        for champ in ("predecesseur_code", "successeur_code"):
            if s[champ] not in connus:
                erreurs.append(f"succession {s.get('contexte','?')!r} : {champ} {s[champ]!r} inconnu")
        if s["predecesseur_code"] == s["successeur_code"]:
            erreurs.append(f"succession réflexive : {s['predecesseur_code']}")
    return erreurs


# --------------------------------------------------------------------------- SQL

def q(v) -> str:
    """Littéral SQL. Les identifiants ne viennent jamais d'ici, seulement des valeurs."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def qjson(v) -> str:
    return q(json.dumps(v or {}, ensure_ascii=False)) + "::jsonb"


def qarray(v) -> str:
    if not v:
        return "'{}'::text[]"
    return "ARRAY[" + ", ".join(q(x) for x in v) + "]::text[]"


def rendre_sql(bundle: dict) -> str:
    """Rend le texte du seed SQL. N'écrit rien : le garde-fou D44 le relit d'abord."""
    L = [
        "-- Seed des référentiels — généré par seed/construire_bundle.py, ne pas éditer à la main.",
        "-- Rejouable : les INSERT sont idempotents (ON CONFLICT DO UPDATE).",
        "--   psql -d rhetores_ref -v ON_ERROR_STOP=1 -f seed.sql",
        "BEGIN;",
        "SET LOCAL search_path TO ref, public;",
        "",
        "-- Acteurs ---------------------------------------------------------------",
    ]
    for a in bundle["acteurs"]:
        L.append(
            "INSERT INTO acteurs (code, nom, role, domiciliation, est_depositaire_tiers, "
            "alias, payload, provenance, confiance) VALUES ("
            f"{q(a['code'])}, {q(a['nom'])}, {q(a['role'])}, {q(a.get('domiciliation'))}, "
            f"{q(a.get('est_depositaire_tiers'))}, {qarray(a.get('alias'))}, "
            f"{qjson(a.get('payload'))}, {q(a.get('provenance','seed'))}, {q(a.get('confiance','medium'))}) "
            "ON CONFLICT (code) DO UPDATE SET nom=EXCLUDED.nom, role=EXCLUDED.role, "
            "domiciliation=EXCLUDED.domiciliation, est_depositaire_tiers=EXCLUDED.est_depositaire_tiers, "
            "alias=EXCLUDED.alias, payload=EXCLUDED.payload, confiance=EXCLUDED.confiance, "
            "version=acteurs.version+1;")

    L += ["", "-- Successions (K5) -------------------------------------------------------"]
    for s in bundle["successions"]:
        L.append(
            "INSERT INTO acteur_successions (predecesseur_code, successeur_code, date_effet, "
            "date_cloture, contexte, payload, provenance, confiance) VALUES ("
            f"{q(s['predecesseur_code'])}, {q(s['successeur_code'])}, {q(s.get('date_effet'))}, "
            f"{q(s.get('date_cloture'))}, {q(s.get('contexte'))}, {qjson(s.get('payload'))}, "
            f"{q(s.get('provenance','seed'))}, {q(s.get('confiance','medium'))});")

    L += ["", "-- Gabarits (N) ----------------------------------------------------------"]
    for g in bundle["gabarits"]:
        # Les segments (O11) voyagent dans extraction_hints : aucune modification de DDL.
        hints = dict(g.get("extraction_hints") or {})
        if g.get("segments"):
            hints["segments"] = g["segments"]
        # La cible d'ON CONFLICT suit la clé d'unicité gabarit_version_unique (D42) :
        # (emetteur_code, gabarit, valide_depuis). `periodicite` en sort — elle passe en colonne
        # mise à jour comme les autres. `valide_jusqu_a` est mis à jour, jamais dans la cible : il
        # est nullable (NULL = toujours en cours) et un NULL en cible ne matcherait jamais.
        L.append(
            "INSERT INTO gabarits (emetteur_code, gabarit, valide_depuis, valide_jusqu_a, "
            "periodicite, template_id_natif, "
            "signature, n_pages_indicatif, extraction_hints, champs_publies, invariant_controle, "
            "emetteur_lisible, provenance, confiance) VALUES ("
            f"{q(g['emetteur_code'])}, {q(g['gabarit'])}, {q(g['valide_depuis'])}, "
            f"{q(g.get('valide_jusqu_a'))}, {q(g.get('periodicite'))}, "
            f"{q(g.get('template_id_natif'))}, {qjson(g.get('signature'))}, "
            f"{q(g.get('n_pages_indicatif'))}, {qjson(hints)}, {qjson(g.get('champs_publies'))}, "
            f"{q(g.get('invariant_controle'))}, {q(g.get('emetteur_lisible', True))}, "
            f"{q(g.get('provenance','seed'))}, {q(g.get('confiance','medium'))}) "
            "ON CONFLICT (emetteur_code, gabarit, valide_depuis) DO UPDATE SET "
            "valide_jusqu_a=EXCLUDED.valide_jusqu_a, periodicite=EXCLUDED.periodicite, "
            "template_id_natif=EXCLUDED.template_id_natif, signature=EXCLUDED.signature, "
            "n_pages_indicatif=EXCLUDED.n_pages_indicatif, extraction_hints=EXCLUDED.extraction_hints, "
            "champs_publies=EXCLUDED.champs_publies, invariant_controle=EXCLUDED.invariant_controle, "
            "emetteur_lisible=EXCLUDED.emetteur_lisible, confiance=EXCLUDED.confiance, "
            "version=gabarits.version+1;")

    L += ["", f"-- ISIN (E1/E4) — {len(bundle['isin'])} lignes promues de l'asset v0 ------------"]
    for i in bundle["isin"]:
        L.append(
            "INSERT INTO isin (isin, label, class_code, geo_code, sri, source, provenance, confiance) "
            f"VALUES ({q(i['isin'])}, {q(i.get('label'))}, {q(i.get('class_code'))}, "
            f"{q(i.get('geo_code'))}, {q(i.get('sri'))}, {q(i.get('source'))}, "
            f"{q(i.get('provenance','seed'))}, {q(i.get('confiance','medium'))}) "
            "ON CONFLICT (isin) DO UPDATE SET label=EXCLUDED.label, class_code=EXCLUDED.class_code, "
            "geo_code=EXCLUDED.geo_code, sri=EXCLUDED.sri, source=EXCLUDED.source, "
            "confiance=EXCLUDED.confiance, version=isin.version+1;")

    L += ["", "COMMIT;", ""]
    return "\n".join(L)


# -------------------------------------------------------------------------- main

def main() -> int:
    documents = {nom: charger(nom) for nom in ("acteurs.json", "successions.json", "gabarits.json")}
    acteurs = documents["acteurs.json"]["acteurs"]
    successions = documents["successions.json"]["successions"]
    gabarits = documents["gabarits.json"]["gabarits"]
    isins = charger_isin()

    erreurs = verifier(acteurs, successions, gabarits)
    if erreurs:
        print("INTÉGRITÉ EN ÉCHEC — rien n'a été écrit :", file=sys.stderr)
        for e in erreurs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "acteurs": acteurs,
        "successions": successions,
        "gabarits": gabarits,
        "isin": isins,
        "compte": {"acteurs": len(acteurs), "successions": len(successions),
                   "gabarits": len(gabarits), "isin": len(isins)},
    }

    sql = rendre_sql(bundle)

    # Garde-fou D44 — trois périmètres, parce qu'ils ne se recouvrent pas :
    #  (a) les documents sources ENTIERS : leurs clés de documentation (_note, _source,
    #      _note_ancres…) ne partent pas en base, mais seed/referentiels.json a vocation à
    #      être livré dans le paquet du skill (D35) — un CGP y lirait ces noms ;
    #  (b) le bundle assemblé, qui est le contrat rendu par ref_bundle ;
    #  (c) le texte SQL, ligne à ligne, qui est littéralement ce qui entre dans les colonnes.
    fuites: list[tuple[str, str]] = []
    for nom, doc in documents.items():
        fuites += chercher_identifiants_clients(doc, f"seed/{nom}")
    fuites += chercher_identifiants_clients(bundle, "bundle")
    for n, ligne in enumerate(sql.splitlines(), start=1):
        fuites += chercher_identifiants_clients(ligne, f"seed/seed.sql:{n}")
    if fuites:
        print("IDENTIFIANT CLIENT DÉTECTÉ — rien n'a été écrit (D44) :", file=sys.stderr)
        vus = set()
        for chemin, quoi in fuites:
            if (chemin, quoi) in vus:
                continue
            vus.add((chemin, quoi))
            print(f"  - {chemin} : {quoi}", file=sys.stderr)
        print("\n  ref_bundle rend le store EN ENTIER à chaque CGP (D36) : ce qui entre ici est\n"
              "  visible de TOUS les CGP. Ne supprimez pas la provenance, DÉ-IDENTIFIEZ-la — gardez\n"
              "  le type de document et le nombre de réplicats, retirez le client. Exemples :\n"
              "    « relevés annuels <réf> et <réf> » -> « deux relevés annuels du même émetteur »\n"
              "    « deux fonds chez <client> »       -> « deux fonds observés chez un client »\n"
              "  Un identifiant client dans la colonne `source` du CSV des ISIN se dé-identifie dans\n"
              "  SOURCE_ISIN_DEIDENTIFIEE, pas dans l'asset du skill.\n"
              "  Cf. infra/migration_002_purge_identifiants_clients.sql.", file=sys.stderr)
        return 1

    (ICI / "referentiels.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    (ICI / "seed.sql").write_text(sql, encoding="utf-8")

    # --- Snapshot vendoré dans le paquet (D35) --------------------------------------------
    # Repli hors ligne du pipeline, lu par `skill/pipeline/referentiels.py` quand aucun bundle
    # de run n'est disponible (MCP non branché, cold start, réseau indisponible).
    #
    # Il est produit ICI, par le même script, pour une raison précise : un snapshot fabriqué à
    # la main divergerait du bundle au premier changement, et personne ne s'en apercevrait.
    #
    # Les ISIN en sont VOLONTAIREMENT absents. Ils vivent déjà dans le paquet sous
    # `assets/isin_referentiel_v0.csv` — qui est d'ailleurs la SOURCE de la section `isin` de ce
    # bundle. Les vendorer une seconde fois mettrait 261 lignes en double dans le paquet, avec
    # deux copies à faire diverger. La bascule des ISIN vers le bundle relève de N3, qui touche
    # le chemin d'extraction — lequel n'a aucun filet de régression (limite LIM8).
    snapshot = {k: v for k, v in bundle.items() if k != "isin"}
    snapshot["_a_propos"] = (
        "SNAPSHOT VENDORÉ (D35) — repli hors ligne, figé à l'installation du paquet. Un gabarit "
        "adjugé après cette date n'y est PAS : la source de vérité est la base, lue par l'agent "
        "via `ref_bundle` et écrite dans le dossier de run (D36). `skill/pipeline/referentiels.py` "
        "signale explicitement quand il retombe ici. Les ISIN sont absents à dessein : voir "
        "`assets/isin_referentiel_v0.csv`, qui est leur source. Généré par "
        "seed/construire_bundle.py — ne pas éditer à la main."
    )
    dest_snapshot = FORK / "skill" / "assets" / "referentiels_snapshot.json"
    dest_snapshot.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")

    print("Intégrité OK — références résolues, aucun doublon de clé, "
          "valide_depuis renseigné partout.")
    print("Garde-fou D44 OK — aucun identifiant client (référence de contrat "
          f"{MOTIF_REFERENCE_CONTRAT.pattern}, ni l'un des {len(NOMS_CLIENTS)} noms de clients "
          "connus) dans les 3 seeds, le bundle et le SQL. Les ISIN bien formés sont soustraits "
          "avant recherche : DK0062498333 n'est pas une référence de contrat.")
    print(f"  acteurs     : {len(acteurs)}")
    print(f"  successions : {len(successions)}")
    versionnes = sum(1 for g in gabarits if g.get("valide_jusqu_a"))
    print(f"  gabarits    : {len(gabarits)}"
          f"  (clé (émetteur, gabarit, valide_depuis) — D42 ; "
          f"{versionnes} avec une fenêtre fermée)")
    print(f"  isin        : {len(isins)}"
          f"  (dont {sum(1 for i in isins if not i['geo_code'])} sans géographie — E6)")
    print(f"  confiance high : {sum(1 for i in isins if i['confiance'] == 'high')}")
    print("\n  seed/referentiels.json  → bundle au contrat du RUNBOOK §3")
    print("  seed/seed.sql           → à charger dans la base (B4)")
    print(f"  {dest_snapshot.relative_to(FORK)}  → repli vendoré du pipeline (D35), "
          f"sans les ISIN")
    print("  ⚠ modification de skill/ : relancer `python3 regenerer_checksums.py`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
