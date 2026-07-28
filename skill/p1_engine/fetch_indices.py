#!/usr/bin/env python3
"""Récupère niveau + variation + perf YTD des 8 indices via yfinance et
actualise le STORE DE PÉRIODE (contexte/[période].json), réutilisé pour tous
les clients du trimestre.

Usage : python3 fetch_indices.py contexte/T2-26.json [--year 2026]

Crée le fichier s'il n'existe pas (macro_text / faits_marquants restent à rédiger).
Met à jour uniquement la section "indices". Nécessite yfinance + accès réseau.
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import sys, argparse, json, datetime as dt
from pathlib import Path

# Libellé figé Rhétorès -> (ticker Yahoo, unité de variation)
TICKERS = [
    ("S&P 500", "^GSPC", "pts"),
    ("Nasdaq Composite", "^IXIC", "pts"),
    ("DJ Euro Stoxx 50", "^STOXX50E", "pts"),
    ("CAC 40", "^FCHI", "pts"),
    ("Once d'or (USD / once)", "GC=F", "$"),
    ("Pétrole USD Brent", "BZ=F", "$"),
    ("EUR / USD", "EURUSD=X", ""),
    ("Bitcoin", "BTC-USD", "$"),
]

def fr_num(x, dec=0):
    s = f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s

def fetch(ticker, year):
    import yfinance as yf
    df = yf.download(ticker, start=f"{year}-01-01", progress=False, auto_adjust=True)
    if df is None or df.empty: return None, None
    c = df["Close"].dropna()
    if len(c) < 2: return None, None
    first, last = float(c.iloc[0]), float(c.iloc[-1])
    return last, last - first  # niveau actuel, variation absolue YTD

def var_str(delta, unit):
    if delta is None: return ""
    sign = "−" if delta < 0 else "+"
    if unit == "":   # change : 3 décimales
        return f"{sign}{fr_num(abs(delta),3)}"
    return f"{sign}{fr_num(abs(delta),0)} {unit}".strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("store"); ap.add_argument("--year", type=int, default=dt.date.today().year)
    a = ap.parse_args()
    p = Path(a.store)
    store = json.loads(p.read_text(encoding="utf-8")) if p.exists() else \
            {"period_short": p.stem, "macro_text": [], "faits_marquants": [], "indices": []}
    indices = []
    for name, tk, unit in TICKERS:
        lvl, delta = fetch(tk, a.year)
        ytd = round(delta / (lvl - delta) * 100, 1) if (lvl is not None and (lvl - delta)) else None
        indices.append({"name": name, "var": var_str(delta, unit), "ytd": ytd})
        print(f"  {name:28s} {tk:12s} var={var_str(delta,unit) or 'n/a':>12s}  ytd={ytd}")
    store["indices"] = indices
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK store actualisé : {a.store}  ({len(indices)} indices)")

if __name__ == "__main__": main()
