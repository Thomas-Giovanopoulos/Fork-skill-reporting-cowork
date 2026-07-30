#!/usr/bin/env python3
"""N3 — SOLDÉ le 2026-07-30 (B-i) : ce script garde désormais l'invariant INVERSE.

Histoire courte. Jusqu'au 30/07, SKILL.md §2.b portait des pièges de parsing PAR ÉMETTEUR en dur
(PPT, Dauphine), dupliqués — et moins riches — que `extraction_hints.pieges` des profils du seed.
La première version de ce script rendait la duplication *détectable* (chaque piège d'émetteur de
SKILL.md devait avoir son pendant au seed), en attendant que le skill sache lire les profils.

Ce jour est arrivé : depuis B-i, le prompt des subagents se **prime depuis le profil apparié**
(`referentiels.json` du run — vérifié le 30/07 : les 9 gabarits du bundle ET du snapshot portent
`extraction_hints`, `champs_publies`, `invariant_controle`). La part « émetteurs » du §2.b a été
retirée ; ne restent dans SKILL.md que les pièges portant sur les **entrées du skill** (Excel CGP
en `data_only`, lignes de légende), qui n'ont jamais relevé de N3.

**L'invariant à garder est donc retourné** : SKILL.md ne doit plus JAMAIS porter de piège
d'émetteur en dur. Un piège nominatif qui y revient est une régression de N3 — la connaissance
recommencerait à vivre à deux endroits, et une correction apportée au profil ne parviendrait plus
au prompt. Ce script échoue si un nom d'émetteur réapparaît dans le §2.b.

Usage :
    python3 verifier_pieges.py          # 0 si le §2.b est propre, 1 si un émetteur y revient
"""
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
SKILL = RACINE / "skill" / "SKILL.md"

# Marqueurs d'émetteurs — si l'un d'eux réapparaît dans le §2.b, un piège nominatif est revenu.
# Liste dérivée des émetteurs du seed ; à étendre quand un émetteur entre au référentiel.
MARQUEURS_EMETTEUR = (
    "de pury", "pictet", "ppt", "dauphine", "spirica", "uaf", "himalia",
    "wealins", "cardif", "nortia",
)


def section_2b(texte: str) -> str:
    m = re.search(r"### b\. Un subagent par PDF.*?(?=\n### |\n## )", texte, re.DOTALL)
    if not m:
        sys.exit("Section §2.b introuvable dans SKILL.md — la structure a changé, "
                 "mettre ce script à jour plutôt que de le laisser vérifier du vide.")
    return m.group(0).lower()


def main() -> int:
    if not SKILL.exists():
        sys.exit(f"Introuvable : {SKILL}")
    corps = section_2b(SKILL.read_text(encoding="utf-8"))

    revenus = []
    for m in MARQUEURS_EMETTEUR:
        # mot entier, pour éviter les faux positifs de sous-chaîne (« ppt » dans un mot)
        if re.search(rf"(?<![a-zà-ÿ]){re.escape(m)}(?![a-zà-ÿ])", corps):
            revenus.append(m)

    if revenus:
        print("RÉGRESSION N3 — des pièges d'émetteur sont revenus en dur dans SKILL.md §2.b :")
        for m in revenus:
            print(f"  - marqueur {m!r}")
        print("\nLa place d'un piège d'émetteur est `extraction_hints.pieges` du PROFIL "
              "(proposition → arbitrage → visible au run suivant de chaque CGP). Le remettre "
              "dans SKILL.md recrée les deux vérités divergentes que N3 a soldées.")
        return 1

    print("OK — SKILL.md §2.b ne porte aucun piège d'émetteur en dur : le priming vient du "
          "profil apparié (N3 soldé le 2026-07-30, B-i). Les pièges « entrées du skill » "
          "(Excel CGP, légendes) y restent à bon droit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
