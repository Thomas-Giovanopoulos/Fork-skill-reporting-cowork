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
  - unicité du couple (emetteur_code, gabarit, periodicite) ;
  - toute référence d'acteur (gabarits, successions) résolue.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
FORK = ICI.parent
ISIN_CSV = FORK / "skill" / "assets" / "isin_referentiel_v0.csv"

SCHEMA_VERSION = "0.1-skill"


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
                "source": (r.get("source") or "").strip() or None,
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

    couples = []
    for g in gabarits:
        if g["emetteur_code"] not in connus:
            erreurs.append(
                f"gabarit {g['gabarit']!r} : emetteur_code {g['emetteur_code']!r} inconnu "
                "(la clé étrangère vers les acteurs est le lien entre les deux tables, D22)")
        couples.append((g["emetteur_code"], g["gabarit"], g["periodicite"]))
    dbl = {c for c in couples if couples.count(c) > 1}
    if dbl:
        erreurs.append(f"couples (émetteur, gabarit, périodicité) en doublon : {sorted(dbl)}")

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


def ecrire_sql(bundle: dict, dest: Path) -> None:
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
        L.append(
            "INSERT INTO gabarits (emetteur_code, gabarit, periodicite, template_id_natif, "
            "signature, n_pages_indicatif, extraction_hints, champs_publies, invariant_controle, "
            "emetteur_lisible, provenance, confiance) VALUES ("
            f"{q(g['emetteur_code'])}, {q(g['gabarit'])}, {q(g['periodicite'])}, "
            f"{q(g.get('template_id_natif'))}, {qjson(g.get('signature'))}, "
            f"{q(g.get('n_pages_indicatif'))}, {qjson(hints)}, {qjson(g.get('champs_publies'))}, "
            f"{q(g.get('invariant_controle'))}, {q(g.get('emetteur_lisible', True))}, "
            f"{q(g.get('provenance','seed'))}, {q(g.get('confiance','medium'))}) "
            "ON CONFLICT (emetteur_code, gabarit, periodicite) DO UPDATE SET "
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
    dest.write_text("\n".join(L), encoding="utf-8")


# -------------------------------------------------------------------------- main

def main() -> int:
    acteurs = charger("acteurs.json")["acteurs"]
    successions = charger("successions.json")["successions"]
    gabarits = charger("gabarits.json")["gabarits"]
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

    (ICI / "referentiels.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    ecrire_sql(bundle, ICI / "seed.sql")

    print("Intégrité OK — références résolues, aucun doublon de clé.")
    print(f"  acteurs     : {len(acteurs)}")
    print(f"  successions : {len(successions)}")
    print(f"  gabarits    : {len(gabarits)}")
    print(f"  isin        : {len(isins)}"
          f"  (dont {sum(1 for i in isins if not i['geo_code'])} sans géographie — E6)")
    print(f"  confiance high : {sum(1 for i in isins if i['confiance'] == 'high')}")
    print("\n  seed/referentiels.json  → utilisable par le skill dès maintenant")
    print("  seed/seed.sql           → à charger dans la base (B4)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
