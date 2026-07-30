#!/usr/bin/env python3
"""L3a — équivalence de rendu : store ≡ classeur, à l'octet près.

Pour chaque fixture, deux rendus du MÊME manifeste (généré par excel_to_manifest, inchangé) :
l'un depuis le classeur Excel, l'autre depuis le forme-store dérivé
(`fixtures/stores/{stem}.store.json`, produit par `outils_lecteur/deriver_stores.py`).
Le critère est le hash SHA-256 du HTML : ÉGALITÉ EXACTE, pas de tolérance.

Ce que ce contrôle prouve — et ne prouve pas (spec §5) :
- il prouve la **fidélité du lecteur** (L3a) : le chemin store → listes canoniques → p2_fill
  reproduit le rendu du chemin classeur → read_sheet → p2_fill ;
- il ne mesure PAS la perte de la projection Excel (L3b) : les stores étant dérivés des
  classeurs, cette équivalence-là est en partie tautologique. L3b attend le store du client
  de référence régénéré depuis les relevés officiels.

Écart attendu documenté (aucun observé au 30/07) : les multiples MOIC transitent en NOMBRE au
store et sont reformatés « 1,06x » par le lecteur (A3) — une valeur à plus de 4 décimales ou un
format exotique (« 2x » sans décimale) produirait un diff, à arbitrer à ce moment-là.

Usage :
    python3 p1_engine/tests/test_l3a.py               # les 7 fixtures
    python3 p1_engine/tests/test_l3a.py fx_simple …   # sous-ensemble (utile sous timeout)
"""
import difflib
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ENG = Path(__file__).resolve().parents[1]          # p1_engine
SKILL = ENG.parent
FIX = Path(__file__).parent / "fixtures"
STORES = FIX / "stores"
TMP = Path(tempfile.mkdtemp(prefix="l3a_"))


def _run(argv, label):
    r = subprocess.run(argv, cwd=SKILL, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"[{label}] échec (code {r.returncode})\n"
                         f"  stderr : {(r.stderr or '').strip()[:1500]}")
    return r.stdout


def main() -> int:
    voulu = set(sys.argv[1:])
    fixtures = [f for f in sorted(FIX.glob("fx_*.xlsx")) if not voulu or f.stem in voulu]
    if not fixtures:
        raise SystemExit(f"aucune fixture ne correspond à {sorted(voulu)}")

    echecs = []
    for fx in fixtures:
        store = STORES / f"{fx.stem}.store.json"
        if not store.exists():
            echecs.append(fx.stem)
            print(f"ABSENT     {fx.stem} — store non dérivé ; lancer "
                  f"outils_lecteur/deriver_stores.py d'abord")
            continue
        # Bascule ⑤ : chaque chemin génère SON manifeste — l'équivalence se prouve sur la
        # chaîne complète (source → manifeste → HTML), pas seulement sur le rendu.
        man_e = str(TMP / f"{fx.stem}.man.excel.json")
        man_s = str(TMP / f"{fx.stem}.man.store.json")
        _run([sys.executable, str(ENG / "excel_to_manifest.py"), str(fx), man_e,
              "--quarter", "T2", "--year", "2026"], f"manifeste excel {fx.stem}")
        _run([sys.executable, str(ENG / "store_to_manifest.py"), str(store), man_s,
              "--quarter", "T2", "--year", "2026"], f"manifeste store {fx.stem}")
        m_e = json.load(open(man_e, encoding="utf-8"))
        m_s = json.load(open(man_s, encoding="utf-8"))
        if m_e != m_s:
            echecs.append(fx.stem)
            print(f"DIFF       {fx.stem}: les MANIFESTES divergent (store_to_manifest ≠ "
                  f"excel_to_manifest) :")
            for k in set(list(m_e) + list(m_s)):
                if m_e.get(k) != m_s.get(k):
                    print(f"    {k}: excel={json.dumps(m_e.get(k), ensure_ascii=False)[:120]}")
                    print(f"    {'':{len(k)}}  store={json.dumps(m_s.get(k), ensure_ascii=False)[:120]}")
            continue
        out_e = str(TMP / f"{fx.stem}.excel.html")
        out_s = str(TMP / f"{fx.stem}.store.html")
        _run([sys.executable, str(ENG / "p2_fill.py"), str(fx), man_e, out_e],
             f"rendu excel {fx.stem}")
        _run([sys.executable, str(ENG / "p2_fill.py"), str(store), man_s, out_s],
             f"rendu store {fx.stem}")
        h_e = hashlib.sha256(open(out_e, "rb").read()).hexdigest()
        h_s = hashlib.sha256(open(out_s, "rb").read()).hexdigest()
        if h_e == h_s:
            print(f"IDENTIQUE  {fx.stem} (manifeste + rendu)")
        else:
            echecs.append(fx.stem)
            a = open(out_e, encoding="utf-8").read().splitlines()
            b = open(out_s, encoding="utf-8").read().splitlines()
            diff = [l for l in difflib.unified_diff(a, b, "excel", "store", lineterm="")]
            n = sum(1 for l in diff if l.startswith(("+", "-"))
                    and not l.startswith(("+++", "---")))
            print(f"DIFF       {fx.stem}: {n} ligne(s) — extrait :")
            for l in diff[2:12]:
                print(f"    {l[:200]}")

    print(f"\n{'ÉCHEC' if echecs else 'OK'} — {len(fixtures) - len(echecs)}/{len(fixtures)} "
          f"équivalence(s) exacte(s)" + (f" ; en écart : {echecs}" if echecs else ""))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
