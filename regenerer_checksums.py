#!/usr/bin/env python3
"""Régénère skill/CHECKSUMS.json — À LANCER APRÈS TOUTE MODIFICATION DU SKILL.

    python3 regenerer_checksums.py            met à jour et affiche le delta
    python3 regenerer_checksums.py --verifier n'écrit rien, liste les écarts

Pourquoi ce script existe
-------------------------
`p1_engine/selfcheck.py` contrôle la taille et le md5 de chaque fichier contre
`CHECKSUMS.json`. Or l'étape 0 du protocole du skill impose : **si le self-check
échoue, STOP**. Une modification légitime fait donc échouer le selfcheck, et son
message oriente vers un faux diagnostic — « troncature probable », donc « paquet
corrompu, réinstallez ». Sans ce script, chaque édition du fork casse le skill de
façon trompeuse.

`CHECKSUMS.json` est exclu de son propre manifeste (il ne peut pas contenir son
propre md5). Les caches Python le sont aussi : ce n'est pas de la source.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
SKILL = ICI / "skill"
MANIFESTE = SKILL / "CHECKSUMS.json"

EXCLUS_NOMS = {"CHECKSUMS.json"}
EXCLUS_MOTIFS = ("__pycache__",)


def pertinent(p: Path) -> bool:
    if p.name in EXCLUS_NOMS or p.suffix == ".pyc":
        return False
    return not any(m in p.parts for m in EXCLUS_MOTIFS)


def calculer() -> dict[str, dict]:
    out = {}
    for p in sorted(SKILL.rglob("*")):
        if not p.is_file() or not pertinent(p):
            continue
        data = p.read_bytes()
        rel = p.relative_to(SKILL).as_posix()
        out[rel] = {"size": len(data), "md5": hashlib.md5(data).hexdigest()}
    return out


def main() -> int:
    if not SKILL.is_dir():
        print(f"Dossier introuvable : {SKILL}", file=sys.stderr)
        return 2

    neuf = calculer()
    ancien = json.loads(MANIFESTE.read_text(encoding="utf-8")) if MANIFESTE.exists() else {}

    modifies = sorted(k for k in neuf if k in ancien and neuf[k] != ancien[k])
    ajoutes = sorted(set(neuf) - set(ancien))
    retires = sorted(set(ancien) - set(neuf))

    for titre, lot in (("MODIFIÉS", modifies), ("AJOUTÉS", ajoutes), ("RETIRÉS", retires)):
        if lot:
            print(f"{titre} :")
            for k in lot:
                print(f"    {k}")

    if not (modifies or ajoutes or retires):
        print(f"Aucun écart — le manifeste est à jour ({len(neuf)} fichiers).")
        return 0

    if "--verifier" in sys.argv:
        print("\nMode vérification : rien n'a été écrit.")
        return 1

    MANIFESTE.write_text(json.dumps(neuf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nManifeste régénéré : {len(neuf)} fichiers.")
    print("Relancez `python3 skill/p1_engine/selfcheck.py` pour confirmer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
