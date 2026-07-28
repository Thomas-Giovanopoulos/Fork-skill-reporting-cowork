#!/usr/bin/env python3
"""Garde-fou du portage : n'accepte que les écarts de code voulus.

Compare ``../referentiels_skill.py`` (module d'origine, écrit pour être greffé
sur mcp-o2s-server) à ``tools/referentiels.py`` (portage vers le serveur dédié),
**hors docstrings et commentaires** — seul ce qui s'exécute est comparé, via
l'AST. La documentation des deux fichiers diverge largement et à dessein ; le
code, lui, ne doit différer que par les deux correctifs annoncés :

  1. ``_identity`` : lecture de ``roles`` (liste) plutôt que ``role`` ;
  2. ``ref_adjudications`` : répartition filtrée sur le périmètre de l'appelant.

Pourquoi ce test existe. Le portage consistait à recopier 400 lignes en n'en
changeant que deux passages. Une recopie de cette forme échoue silencieusement :
une ligne perdue, un ``not`` inversé, un paramètre oublié ne se voient ni à la
lecture ni au premier essai contre la base. Ce script transforme « j'ai
recopié fidèlement » en assertion vérifiable, et il reste utile ensuite : tant
que le module d'origine n'est pas retiré, il signale toute correction appliquée
d'un côté seulement.

Sortie : 0 si les écarts sont exactement ceux attendus, 1 sinon (avec le diff).

Lancement :
    cd infra/mcp_referentiels && python3 tests/verifier_diff.py
"""
import ast
import difflib
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
ORIGINE = RACINE.parent / "referentiels_skill.py"
PORTAGE = RACINE / "tools" / "referentiels.py"

# Marqueurs des seuls écarts de code admis. Un écart est accepté s'il ne touche
# que des lignes contenant l'un de ces fragments.
ADMIS = (
    "roles",            # correctif 1
    "role",             # correctif 1 (repli au singulier)
    "email = email or",  # correctif 1 (branche de repli inchangée, redécoupée)
    "user = user_store",
    "oid = claims",
    "if user is not None",
    "else:",
    "count(*)",         # correctif 2
    "is_admin",         # correctif 2
    "repartition",
)


def squelette(chemin: Path) -> list[str]:
    """Code sans docstrings ni commentaires, normalisé par ``ast.unparse``."""
    tree = ast.parse(chemin.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            corps = node.body
            if (corps and isinstance(corps[0], ast.Expr)
                    and isinstance(corps[0].value, ast.Constant)
                    and isinstance(corps[0].value.value, str)):
                node.body = corps[1:] or [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree)).splitlines()


def main() -> int:
    if not ORIGINE.exists():
        print(f"Module d'origine absent ({ORIGINE.name}) — retiré du dépôt ?\n"
              "Ce garde-fou n'a plus d'objet : le supprimer, ou figer une copie de référence.")
        return 0

    diff = list(difflib.unified_diff(
        squelette(ORIGINE), squelette(PORTAGE),
        fromfile=f"origine/{ORIGINE.name}", tofile=f"portage/{PORTAGE.name}",
        lineterm="", n=1))

    if not diff:
        print("Aucun écart de code — portage strictement identique.")
        return 0

    modifiees = [l for l in diff
                 if l[:1] in "+-" and not l.startswith(("+++", "---")) and l[1:].strip()]
    inattendues = [l for l in modifiees if not any(m in l for m in ADMIS)]

    print("\n".join(diff))
    print(f"\n{len(modifiees)} ligne(s) d'écart, {len(inattendues)} inattendue(s).")

    if inattendues:
        print("\nÉCART NON PRÉVU — le portage a divergé au-delà des deux correctifs :")
        for l in inattendues:
            print(f"    {l}")
        print("Soit c'est voulu (mettre à jour ADMIS et le README), soit c'est une "
              "erreur de recopie.")
        return 1

    print("Écarts conformes aux deux correctifs annoncés (cf. README).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
