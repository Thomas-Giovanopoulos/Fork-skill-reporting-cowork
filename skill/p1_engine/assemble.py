#!/usr/bin/env python3
"""Assembleur P1 — manifeste -> squelette HTML vide (déterministe).

Usage : python3 assemble.py <manifeste.json> <sortie.html>
Le LLM ne génère AUCUN HTML : il produit/valide le manifeste puis lance ce script.
Même manifeste -> squelette identique au bit près. Toute la structure vit dans bank/.
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parent
BANK = ROOT / "bank"

BLOCK_ORDER = [
    {"name": "hero",        "numbered": False},
    {"name": "contexte",    "numbered": True},
    {"name": "supervision","numbered": True},
    {"name": "performance", "numbered": True},
    {"name": "performance_nc", "numbered": True},
    {"name": "repartition", "numbered": True},
    {"name": "exhaustif",   "numbered": True},
    {"name": "footer",      "numbered": False},
]
CATEGORY_ORDER = ["liquidites", "immobilier", "financier_cote", "non_cote", "dettes"]
CATEGORY_LABELS = {"liquidites":"Liquidités","immobilier":"Immobilier","financier_cote":"Financier coté","non_cote":"Financier non coté","dettes":"Dettes"}
COLSPANS = {"liquidites":2,"immobilier":7,"financier_cote":8,"non_cote":7,"dettes":8}

def load_json(p):
    with open(p, encoding="utf-8") as f: return json.load(f)

def validate(m, schema):
    Draft202012Validator.check_schema(schema)
    errs = sorted(Draft202012Validator(schema).iter_errors(m), key=lambda e: list(e.path))
    if errs: raise SystemExit("Manifeste invalide:\n"+"\n".join(f"  - {list(e.path)}: {e.message}" for e in errs))
    ents = m["entities"]; pps=[e for e in ents if e["type"]=="pp"]
    if len(pps)>1: raise SystemExit(f"Regle metier: au plus 1 PP, trouve {len(pps)}.")
    if pps and ents[0]["type"]!="pp": raise SystemExit("Regle metier: PP en premiere position.")
    if len({e["id"] for e in ents})!=len(ents): raise SystemExit("Regle metier: id uniques.")

def frdate(iso): y,m,d=iso.split("-"); return f"{d}/{m}/{y}"
def client_label_html(label):
    p=label.rsplit(" ",1); return f"{p[0]} <em>{p[1]}</em>" if len(p)==2 else label

def compute_layout(be):
    out, num = [], 0
    for spec in BLOCK_ORDER:
        if not be.get(spec["name"], False): continue
        disp = None
        if spec["numbered"]: disp=f"{num:02d}"; num+=1
        out.append({**spec, "display_num": disp})
    return out

def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python3 assemble.py <manifeste.json> <sortie.html>")
    mp, op = sys.argv[1], sys.argv[2]
    schema = load_json(ROOT/"manifest.schema.json")
    manifest = load_json(mp)
    validate(manifest, schema)
    env = Environment(loader=FileSystemLoader(str(BANK)), undefined=StrictUndefined,
                      autoescape=False, trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    env.filters["frdate"] = frdate
    rep = dict(manifest["reporting"]); rep["client_label_html"] = client_label_html(rep["client_label"])
    layout = compute_layout(manifest["blocs_enabled"])
    bloc_num = {b["name"]: b["display_num"] for b in layout if b["display_num"] is not None}
    ctx = {"reporting":rep, "blocs_enabled":manifest["blocs_enabled"], "bloc_num":bloc_num,
           "entities":manifest["entities"], "category_order":CATEGORY_ORDER,
           "category_labels":CATEGORY_LABELS, "colspans":COLSPANS, "data":{"rows":{},"subtotals":{},"entity_totals":{},"synth":{},"hero":{},"cards":{},"donuts":{},"supervision":{},"perf":{},"contexte":{},"compare_n1":{},"perf_nc":None}}
    html = env.get_template("base.html.j2").render(**ctx)
    out = Path(op); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html, encoding="utf-8")
    print(f"OK squelette: {op} ({len(html)} octets) | numeros: {bloc_num}")

if __name__ == "__main__": main()
