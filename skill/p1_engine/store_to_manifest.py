#!/usr/bin/env python3
"""Pont forme-store -> manifeste (J1) — miroir exact d'`excel_to_manifest.py`.

Même interface CLI, même manifeste en sortie, une seule différence : la source est un store
client 2.1-skill au lieu du classeur. La preuve d'équivalence est le harnais `test_l3a.py`
(étendu à la bascule ⑤) : manifeste-depuis-store ≡ manifeste-depuis-Excel, à l'égalité JSON.

Deux principes :

- **`entities[].categories` est un FAIT, pas un choix** (MQ9, tranché par la donnée — spec
  §7.8) : une catégorie est présente pour une entité si le store porte au moins une entrée.
  C'est l'équivalent exact de `sheet_has_data` côté classeur.
- **Les commutateurs de rendu restent des ARGUMENTS** (`--mode`, `--show-benchmark`…), jamais
  des champs du store : le store répond « peut-on ? », le manifeste répond « veut-on ? »
  (CDC 1.6). Ce module est précisément l'endroit où les deux se rencontrent.

Usage : python3 store_to_manifest.py store.json manifest.json [--quarter T2 --year 2026] […]
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import argparse
import json

CAT_ORDER = ["liquidites", "immobilier", "financier_cote", "non_cote", "dettes"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("store")
    ap.add_argument("out")
    ap.add_argument("--client")
    ap.add_argument("--period-long", default="T1 2026")
    ap.add_argument("--period-short", default="T1-26")
    ap.add_argument("--date", default="2026-03-31")
    ap.add_argument("--date-display", default="31 mars 2026")
    ap.add_argument("--version", default="v1")
    ap.add_argument("--quarter", choices=["T1", "T2", "T3", "T4"],
                    help="Dérive automatiquement période et date de clôture (T4 = année complète).")
    ap.add_argument("--profile", choices=["Prudent", "Équilibré", "Dynamique"],
                    help="Profil de risque (sinon store.reporting.profile, défaut Équilibré).")
    ap.add_argument("--show-benchmark", action="store_true")
    ap.add_argument("--mode", choices=["presentee", "envoyee"], default="presentee")
    ap.add_argument("--show-ps-corrige", action="store_true")
    ap.add_argument("--year", type=int)
    a = ap.parse_args()

    if a.quarter:
        import datetime as _dt
        yr = a.year or _dt.date.today().year
        QEND = {"T1": (3, 31, "31 mars"), "T2": (6, 30, "30 juin"),
                "T3": (9, 30, "30 septembre"), "T4": (12, 31, "31 décembre")}
        m, d, disp = QEND[a.quarter]
        a.period_long = f"Année {yr}" if a.quarter == "T4" else f"{a.quarter} {yr}"
        a.period_short = f"{a.quarter}-{str(yr)[2:]}"
        a.date = f"{yr}-{m:02d}-{d:02d}"
        a.date_display = f"{disp} {yr}"

    store = json.load(open(a.store, encoding="utf-8"))
    if store.get("schema_version") != "2.1-skill":
        raise SystemExit(f"schema_version {store.get('schema_version')!r} — ce pont consomme le "
                         f"format convergé 2.1-skill (D48).")

    ents = []
    for e in sorted(store["client"]["entities"], key=lambda x: x["order"]):
        # catégorie présente = au moins une entrée du store pour cette entité (fait dérivé,
        # équivalent exact de sheet_has_data : une ligne de données réelle existe).
        cats = [c for c in CAT_ORDER
                if any(item.get("entity_id") == e["id"] for item in store.get(c, []))]
        ents.append({"id": e["id"], "label": e["label"], "type": e["type"],
                     "categories": cats})
    if not ents:
        raise SystemExit("Store sans entité : impossible de déduire libellés et types.")

    _has_nc = any("non_cote" in e["categories"] for e in ents)
    prof = a.profile or store.get("reporting", {}).get("profile") or ""
    pl = prof.lower()
    prof = ("Prudent" if pl.startswith("prud")
            else "Dynamique" if pl.startswith("dynam") else "Équilibré")
    _mode = a.mode
    client = a.client or next((e["label"] for e in ents if e["type"] == "pp"), ents[0]["label"])
    manifest = {
        "manifest_version": "1.0",
        "reporting": {"client_label": client, "subtitle": "Family office - Reporting",
                      "period_long": a.period_long, "period_short": a.period_short,
                      "date_reporting": a.date, "date_display": a.date_display,
                      "version": a.version, "profile": prof,
                      "show_benchmark": bool(a.show_benchmark), "mode": _mode,
                      "show_ps_corrige": bool(a.show_ps_corrige)},
        "blocs_enabled": {"hero": True, "contexte": True, "supervision": True,
                          "performance": True, "performance_nc": _has_nc,
                          "repartition": (_mode != "presentee"),
                          "exhaustif": (_mode != "presentee"), "footer": True},
        "entities": ents,
    }
    json.dump(manifest, open(a.out, "w"), ensure_ascii=False, indent=2)
    print(f"OK manifeste: {a.out}")
    for e in ents:
        print(f"   {e['label']} [{e['type']}] -> {e['categories']}")


if __name__ == "__main__":
    main()
