#!/usr/bin/env python3
"""Régression fixture PAR fixture, avec résultat écrit au fur et à mesure.

Raison d'être — une limite de l'environnement de l'agent, pas du moteur. Chaque
appel shell est coupé à **45 s** et s'exécute dans un namespace PID isolé : toute
tâche de fond est tuée au retour de l'appel, un `nohup … &` suivi de sondages ne
sert donc à rien. Or `run_tests.py` construit le dict complet des résultats
**avant** d'imprimer quoi que ce soit : sur sept fixtures à ~7 s, il dépasse la
limite sans avoir rien affiché, et l'on ne distingue pas un run long d'un blocage.

Ce script ne réécrit **aucune** logique de contrôle : il importe `run_tests.py` et
appelle son `measure()` tel quel, puis compare au même `golden.json`. Il ne peut
donc pas diverger du verdict de la régression complète — il ne fait que la
découper et rendre visible l'avancement.

Il vit **hors de `skill/`** à dessein : y toucher imposerait de régénérer
`CHECKSUMS.json`, alors que ce fichier n'a rien à faire dans le paquet livré.

Usage :
    python3 run_une_fixture.py                       # toutes, dans l'ordre
    python3 run_une_fixture.py fx_simple.xlsx        # une seule
    python3 run_une_fixture.py fx_a.xlsx fx_b.xlsx   # quelques-unes
    python3 run_une_fixture.py --reset               # vide le cumul

Le cumul est conservé entre les appels dans `.reg_partiel.json` (à côté de ce
script) : on peut donc traiter deux ou trois fixtures par appel et lire le total
à la fin, ce qui est précisément ce que la limite de 45 s impose.
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent
ENG = RACINE / "skill" / "p1_engine"
CUMUL = RACINE / ".reg_partiel.json"


def charger_run_tests():
    chemin = ENG / "tests" / "run_tests.py"
    if not chemin.exists():
        sys.exit(f"Introuvable : {chemin}\nCe script doit rester à la racine du fork.")
    spec = importlib.util.spec_from_file_location("run_tests", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if "--reset" in sys.argv:
        if CUMUL.exists():
            CUMUL.write_text("{}", encoding="utf-8")
        print("Cumul remis à zéro.")
        if not args:
            return 0

    rt = charger_run_tests()
    gold = json.load(open(rt.GOLD, encoding="utf-8"))

    noms = args or [p.name for p in sorted(rt.FIX.glob("*.xlsx"))]
    inconnues = [n for n in noms if not (rt.FIX / n).exists()]
    if inconnues:
        sys.exit(f"Fixture(s) introuvable(s) : {inconnues}\n"
                 f"Disponibles : {[p.name for p in sorted(rt.FIX.glob('*.xlsx'))]}")

    acc = json.loads(CUMUL.read_text(encoding="utf-8")) if CUMUL.exists() else {}

    for nom in noms:
        t0 = time.time()
        r = rt.measure(rt.FIX / nom)
        r["secondes"] = round(time.time() - t0, 1)
        exp = gold.get(nom, {})
        cles = ("actif_brut", "dettes", "actif_net")
        r["key_ok"] = all(r[k] == exp.get(k) for k in cles)
        r["ok"] = bool(r["qc_pass"] and r["deterministic"] and r["key_ok"])
        if not r["key_ok"]:
            r["attendu"] = {k: exp.get(k) for k in cles}
            r["obtenu"] = {k: r[k] for k in cles}
        acc[nom] = r
        # Écriture APRÈS CHAQUE fixture : si l'appel est coupé, ce qui a été
        # mesuré n'est pas perdu. C'est tout l'intérêt du découpage.
        CUMUL.write_text(json.dumps(acc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {'OK   ' if r['ok'] else 'ECHEC'} {nom}  QC {r['qc']}  "
              f"déterministe={r['deterministic']}  {r['secondes']} s", flush=True)
        if not r["ok"]:
            if not r["qc_pass"]:
                print("        auto-contrôle non vert")
            if not r["deterministic"]:
                print("        rendu non déterministe")
            if not r["key_ok"]:
                print(f"        valeurs : obtenu {r['obtenu']} | attendu {r['attendu']}")

    verts = sum(1 for v in acc.values() if v["ok"])
    total_attendu = len(list(rt.FIX.glob("*.xlsx")))
    print(f"\n{verts}/{len(acc)} fixtures OK (cumul ; {total_attendu} au total)")
    return 0 if verts == len(acc) else 1


if __name__ == "__main__":
    sys.exit(main())
