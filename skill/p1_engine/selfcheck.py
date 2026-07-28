#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-check d'intégrité du skill — À EXÉCUTER EN PREMIER, avant toute extraction (SKILL.md §2, étape 0).

Vérifie (~1 s) :
  1. que chaque .py du paquet compile (ast.parse) ;
  2. que chaque template .j2 parse (jinja2) ;
  3. que chaque .json charge ;
  4. si CHECKSUMS.json est présent : taille + md5 de chaque fichier vs manifeste
     (détecte les troncatures de fin de fichier même syntaxiquement invisibles) ;
  5. que l'environnement a un jsonschema assez récent (Draft202012Validator) pour store_builder.py.

Sortie : code 0 si tout est sain, 1 sinon (liste des fichiers en échec sur stderr).
En cas d'échec : NE PAS réparer à la main en silence — resignaler le paquet corrompu au mainteneur
(cause connue : bug de copie/synchronisation à l'installation ; réinstaller le .skill ou relancer
l'application résout généralement le problème).

Usage : python3 p1_engine/selfcheck.py   (depuis la racine du skill)
"""
import ast, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"__pycache__", "node_modules", ".git"}
errors = []

def walk_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            yield os.path.join(dirpath, f)

# 1-3 : validité syntaxique
try:
    import jinja2
    jenv = jinja2.Environment()
except ImportError:
    jenv = None
    errors.append(("<env>", "jinja2 absent — pip install jinja2"))

for path in walk_files():
    rel = os.path.relpath(path, ROOT)
    try:
        if path.endswith(".py"):
            with open(path, encoding="utf-8") as fh:
                ast.parse(fh.read())
        elif path.endswith(".j2") and jenv is not None:
            with open(path, encoding="utf-8") as fh:
                jenv.parse(fh.read())
        elif path.endswith(".json"):
            with open(path, encoding="utf-8") as fh:
                json.load(fh)
    except Exception as e:
        errors.append((rel, f"{type(e).__name__}: {e}"))

# 4 : manifeste de checksums (si présent)
manifest_path = os.path.join(ROOT, "CHECKSUMS.json")
if os.path.exists(manifest_path):
    try:
        manifest = json.load(open(manifest_path, encoding="utf-8"))
        for rel, meta in manifest.items():
            full = os.path.join(ROOT, rel)
            if not os.path.exists(full):
                errors.append((rel, "fichier manquant (présent au manifeste)"))
                continue
            data = open(full, "rb").read()
            if len(data) != meta["size"]:
                errors.append((rel, f"taille {len(data)} != {meta['size']} attendue (troncature probable)"))
            elif hashlib.md5(data).hexdigest() != meta["md5"]:
                errors.append((rel, "md5 différent du manifeste"))
    except Exception as e:
        errors.append(("CHECKSUMS.json", f"illisible: {e}"))
else:
    print("  (i) CHECKSUMS.json absent — contrôle syntaxique seul.", file=sys.stderr)

# 5 : version de jsonschema pour store_builder.py
try:
    import jsonschema
    if not hasattr(jsonschema, "Draft202012Validator"):
        errors.append(("<env>", f"jsonschema {jsonschema.__version__} trop ancien — "
                                "pip install -U jsonschema (>= 4.x requis par store_builder.py)"))
except ImportError:
    errors.append(("<env>", "jsonschema absent — pip install jsonschema"))

if errors:
    print(f"SELF-CHECK ÉCHEC — {len(errors)} problème(s) :", file=sys.stderr)
    for rel, msg in errors:
        print(f"  ✗ {rel} : {msg}", file=sys.stderr)
    sys.exit(1)
print("Self-check OK — paquet intègre, environnement prêt.")
