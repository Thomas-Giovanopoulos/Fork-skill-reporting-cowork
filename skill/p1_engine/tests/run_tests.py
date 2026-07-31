#!/usr/bin/env python3
"""Tests de non-régression du moteur de reporting.

Pour chaque fixture (p1_engine/tests/fixtures/*.xlsx) :
  - exécute excel_to_manifest + p2_fill (période T2 2026, store contexte/T2-26.json) ;
  - vérifie que l'auto-contrôle comptable est intégralement vert ;
  - vérifie le déterminisme (deux rendus → empreinte identique) ;
  - compare des valeurs clés (actif brut / dettes / actif net) au golden enregistré.

Usage :
  python3 p1_engine/tests/run_tests.py            # compare au golden (échec si écart)
  python3 p1_engine/tests/run_tests.py --record   # (ré)enregistre le golden
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import json, re, sys, hashlib, subprocess, shutil, tempfile
from pathlib import Path

ENG   = Path(__file__).resolve().parents[1]      # p1_engine
SKILL = ENG.parent                               # racine du skill (pour contexte/)
FIX   = Path(__file__).parent / "fixtures"
GOLD  = Path(__file__).parent / "golden.json"

# Répertoire de travail PROPRE à ce run — correctif T3. Les chemins en dur
# `/tmp/_reg*` collisionnaient avec les résidus d'un run antérieur appartenant à
# un AUTRE utilisateur : l'écriture échouait en PermissionError, remontée en
# CalledProcessError nu. Le symptôme ressemblait à une régression moteur alors
# qu'il n'en était pas une.
TMP = Path(tempfile.mkdtemp(prefix="reg_"))


def _run(argv, label):
    """Exécute une étape du pipeline en RENDANT VISIBLE son erreur.

    L'ancien `check=True` + `capture_output=True` masquait stderr : c'est la
    moitié du coût de T3, indépendamment du chemin en dur. Un échec doit dire
    quelle commande, quel code, et ce qu'elle a écrit sur stderr.
    """
    r = subprocess.run(argv, cwd=SKILL, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(
            f"[{label}] échec (code {r.returncode})\n"
            f"  commande : {' '.join(str(a) for a in argv)}\n"
            f"  stderr   : {(r.stderr or '').strip()[:2000]}\n"
            f"  stdout   : {(r.stdout or '').strip()[:500]}")
    return r.stdout


def render(xlsx, out):
    man = str(TMP / f"{xlsx.stem}.man.json")
    _run([sys.executable, str(ENG/"excel_to_manifest.py"), str(xlsx), man,
          "--quarter", "T2", "--year", "2026"], f"manifeste {xlsx.stem}")
    return _run([sys.executable, str(ENG/"p2_fill.py"), str(xlsx), man, out],
                f"rendu {xlsx.stem}")

def slot(html, name):
    m = re.search(rf'data-slot="{name}">([^<]*)', html)
    return m.group(1).strip() if m else None

def measure(xlsx):
    out1 = str(TMP / f"r1_{xlsx.stem}.html")
    out2 = str(TMP / f"r2_{xlsx.stem}.html")
    sout = render(xlsx, out1); render(xlsx, out2)
    html = open(out1, encoding="utf-8").read()
    qc = re.search(r"Contrôles comptables : (\d+)/(\d+) OK", sout)
    h1 = hashlib.sha256(open(out1,'rb').read()).hexdigest()
    h2 = hashlib.sha256(open(out2,'rb').read()).hexdigest()
    return {
        "qc_pass": (qc.group(1)==qc.group(2)) if qc else False,
        "qc": f"{qc.group(1)}/{qc.group(2)}" if qc else "?",
        "deterministic": h1==h2,
        # D-UI-7 : la courbe dégradée à 2 points doit se DIRE (note de sincérité au rendu).
        # Enregistré au golden pour CHAQUE fixture : True seulement quand le repli s'applique
        # (fx_courbe2pts) — un repli qui cesserait de s'annoncer serait une régression muette.
        "curve_degraded": ("Courbe simplifiée" in html),
        # D-UI-3 : le jeu de colonnes du tableau détail est ADAPTATIF (union, colonne vide
        # non imprimée) — enregistré au golden : un jeu qui change sans décision est une
        # régression. None si le widget est absent de la fixture.
        "cote_cols": (lambda m: ([re.sub(r"<[^>]*>","",t) for t in re.findall(r"<th[^>]*>(.*?)</th>", m.group(1))] if m else None))(re.search(r'cote-acc-tbl">\s*<thead><tr>(.*?)</tr></thead>', html, re.S)),
        "actif_brut": slot(html,"actif_brut"),
        "dettes": (re.search(r"dettes ([\d\s\u202f−-]+€)", sout).group(1).strip() if re.search(r"dettes ([\d\s\u202f−-]+€)", sout) else None),
        "actif_net": (re.search(r"net ([\d\s\u202f−-]+€)", sout).group(1).strip() if re.search(r"net ([\d\s\u202f−-]+€)", sout) else None),
    }

def main():
    results = {x.name: measure(x) for x in sorted(FIX.glob("*.xlsx"))}
    if "--record" in sys.argv or not GOLD.exists():
        json.dump(results, open(GOLD,"w"), ensure_ascii=False, indent=2)
        print(f"Golden enregistré ({len(results)} fixtures) : {GOLD}")
        return 0
    gold = json.load(open(GOLD)); fails = 0
    for name, r in results.items():
        exp = gold.get(name, {})
        key_ok = all(r[k]==exp.get(k) for k in ("actif_brut","dettes","actif_net","curve_degraded"))
        ok = r["qc_pass"] and r["deterministic"] and key_ok
        print(f"  {'✓' if ok else '✗'} {name}  (QC {r['qc']}, déterministe={r['deterministic']})")
        if not ok:
            fails += 1
            if not r["qc_pass"]: print("     ✗ auto-contrôle non vert")
            if not r["deterministic"]: print("     ✗ rendu non déterministe")
            if not key_ok: print(f"     ✗ valeurs: obtenu {r} | attendu {exp}")
    print(f"\n{len(results)-fails}/{len(results)} fixtures OK")
    return 1 if fails else 0

if __name__ == "__main__":
    try:
        code = main()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)   # aucun résidu pour le run suivant (T3)
    sys.exit(code)
