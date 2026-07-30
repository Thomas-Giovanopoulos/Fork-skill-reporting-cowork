#!/usr/bin/env python3
"""Garde-fou du portage : n'accepte que les écarts de code voulus, au grain de la DÉFINITION.

Compare `../referentiels_skill.py` (module d'origine, écrit pour être greffé sur mcp-o2s-server)
à `tools/referentiels.py` (portage vers le serveur dédié), **hors docstrings et commentaires** —
seul ce qui s'exécute est comparé, via l'AST. La documentation des deux fichiers diverge
largement et à dessein.

Pourquoi ce garde-fou existe. Le portage consistait à recopier 400 lignes en n'en changeant que
deux passages. Une recopie de cette forme échoue silencieusement : une ligne perdue, un `not`
inversé, un paramètre oublié ne se voient ni à la lecture ni au premier essai contre la base.

## Deux versions ont précédé celle-ci, et la deuxième a menti

La première comparait ligne à ligne, en admettant toute ligne contenant l'un d'une liste de
fragments. Le 2026-07-29 elle a **laissé passer sans le signaler** le changement de clé de
conflit D42 sur `_SPECS` : `ast.unparse` écrase tout ce dictionnaire sur **une seule ligne**,
laquelle contient `'role'` — fragment alors admis pour une raison sans aucun rapport (la spec
`acteur` a un champ requis nommé `role`). Un garde-fou validant une modification de schéma par
coïncidence de sous-chaîne est pire qu'aucun garde-fou : il donne une confiance fausse.

La deuxième version imprimait le motif d'admission de chaque ligne, ce qui rendait la
coïncidence visible. Mais elle exigeait alors un marqueur pour des lignes comme `else:` — trop
génériques pour être des marqueurs sûrs. Le problème n'était pas la liste, c'était le **grain**.

D'où cette version : on ne compare plus des lignes mais des **définitions de premier niveau**
(fonctions, classes, affectations). Un écart se lit « la définition X a changé », et seules
les définitions explicitement déclarées ci-dessous peuvent avoir changé. Aucune coïncidence de
texte n'est possible, et les lignes de structure ne demandent plus de justification.

Sortie : 0 si les définitions modifiées sont exactement celles attendues, 1 sinon.

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

# Les SEULES définitions autorisées à différer, avec le motif de chacune. Toute autre
# définition modifiée, ajoutée ou supprimée fait échouer le contrôle.
ECARTS_ATTENDUS = {
    "_identity": (
        "Correctif 1 — lit claims['roles'] (liste) au lieu de claims['role'] (singulier, jamais "
        "produit par le middleware). Le module d'origine retombait donc sur user_store.get_user() "
        "à chaque appel d'outil alors que l'information était déjà en contexte."
    ),
    "register.ref_adjudications": (
        "Correctif 2 — la répartition par statut est calculée sur le périmètre de l'appelant et "
        "non sur toute la table. Un non-admin y apprenait le volume global de propositions de "
        "ses confrères."
    ),
    "register.ref_bundle": (
        "Taille du bundle — paramètre `sections` et retrait des champs de pure traçabilité. "
        "La version initiale affirmait « les référentiels sont petits, lus en entier : pas de "
        "pagination » : vrai sur base vide, faux au premier chargement réel (185 ko, 4 936 "
        "lignes, au-delà de ce qu'un résultat d'outil MCP peut porter, dont 70 % d'ISIN). Le "
        "compte porte toujours sur les quatre tables, pour qu'un appel partiel ne se lise pas "
        "comme une base à moitié vide. Le tri des gabarits suit aussi la clé D42."
    ),
    "register.ref_propose": (
        "D44 — la provenance ne porte plus de nom de fichier. `source_document` est remplacé par "
        "`source_empreinte` (sha256 du contenu) + `source_gabarit` + `source_arrete`. Motif : "
        "`ref_bundle` rend le store en entier à CHAQUE CGP, or un nom de fichier porte le client "
        "en clair (« Relevé Himalia Capi HANAMI.pdf ») — divulgation entre confrères. Le "
        "remplacement est aussi plus utile à l'arbitre : l'empreinte du contenu reconnaît deux "
        "propositions issues du même document. Un `source_empreinte` mal formé est refusé "
        "explicitement, pour qu'un vieux client ne voie pas sa provenance avalée en silence."
    ),
    "CONTRAT_OUTIL": (
        "Détection du retrait silencieux d'arguments. Le client MCP met le schéma des outils en "
        "cache : un client périmé retire de l'appel un argument qu'il ne connaît pas, SANS ERREUR. "
        "Constaté deux fois le 29/07 — `sections` ignoré, puis une provenance enregistrée à `null` "
        "alors qu'elle avait été passée. La fausse bonne idée écartée : faire déclarer sa version "
        "au client, ce qui accuserait à tort un appelant à jour n'ayant pas rempli le champ. Retenu "
        "à la place : le serveur annonce SON contrat et **renvoie ce qu'il a reçu**. Descriptif, "
        "donc sans faux positif possible, et couvrant tout argument perdu et non les seuls prévus."
    ),
    "SECTIONS": "Taille du bundle — énumération des sections demandables.",
    "_CHAMPS_AUDIT": "Taille du bundle — champs retirés du payload, conservés en base.",
    "_alleger": "Taille du bundle — applique _CHAMPS_AUDIT aux lignes retournées.",
    "_SPECS": (
        "D42 — la clé de conflit des gabarits devient (emetteur_code, gabarit, valide_depuis) : "
        "la périodicité n'est pas lisible dans le document chez 3 émetteurs sur 4, elle sort donc "
        "du matching. valide_depuis ne doit jamais être NULL, sans quoi l'ON CONFLICT ne "
        "matcherait jamais et chaque adjudication acceptée insérerait un doublon."
    ),
}


def _sans_docstring(noeud):
    corps = getattr(noeud, "body", None)
    if corps and isinstance(corps[0], ast.Expr) and isinstance(corps[0].value, ast.Constant) \
            and isinstance(corps[0].value.value, str):
        noeud.body = corps[1:] or [ast.Pass()]
    return noeud


def definitions(chemin: Path) -> dict[str, str]:
    """Rend {nom de définition -> code normalisé}, docstrings et commentaires ôtés.

    Les fonctions IMBRIQUÉES sont extraites séparément, sous la clé `parent.enfant`, et
    remplacées par un marqueur dans le corps du parent. Sans cela, `register` — qui contient
    les quatre outils MCP — serait une seule définition : une réécriture de `ref_bundle` s'y
    dissimulerait derrière une déclaration faite pour `ref_adjudications`. C'est arrivé le
    2026-07-29, et c'est la deuxième fois que le GRAIN, et non la liste, était le défaut.
    """
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    out: dict[str, str] = {}

    def enregistrer(noeud, prefixe: str) -> None:
        nom = f"{prefixe}{noeud.name}"
        # Les enfants directs sont sortis, puis remplacés par un marqueur : le parent ne porte
        # plus que sa propre structure, et un changement d'enfant ne le fait pas diverger.
        corps = []
        for sous in noeud.body:
            if isinstance(sous, (ast.FunctionDef, ast.AsyncFunctionDef)):
                enregistrer(sous, f"{nom}.")
                corps.append(ast.parse(f"_enfant_{sous.name} = ...").body[0])
            else:
                corps.append(sous)
        copie = ast.parse(ast.unparse(noeud)).body[0]
        copie.body = corps
        for n in ast.walk(copie):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                _sans_docstring(n)
        out[nom] = ast.unparse(ast.fix_missing_locations(copie))

    for noeud in arbre.body:
        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
            enregistrer(noeud, "")
            continue
        if isinstance(noeud, ast.ClassDef):
            nom = noeud.name
        elif isinstance(noeud, ast.Assign) and len(noeud.targets) == 1 \
                and isinstance(noeud.targets[0], ast.Name):
            nom = noeud.targets[0].id
        elif isinstance(noeud, ast.AnnAssign) and isinstance(noeud.target, ast.Name):
            nom = noeud.target.id
        elif isinstance(noeud, (ast.Import, ast.ImportFrom)):
            continue  # les imports diffèrent par construction (chemins de modules)
        else:
            continue
        for sous in ast.walk(noeud):
            if isinstance(sous, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                _sans_docstring(sous)
        out[nom] = ast.unparse(ast.fix_missing_locations(noeud))
    return out


def main() -> int:
    if not ORIGINE.exists():
        print(f"Module d'origine absent ({ORIGINE.name}) — retiré du dépôt ?\n"
              "Ce garde-fou n'a plus d'objet : le supprimer, ou figer une copie de référence.")
        return 0

    a, b = definitions(ORIGINE), definitions(PORTAGE)
    modifiees = sorted(n for n in set(a) & set(b) if a[n] != b[n])
    ajoutees, supprimees = sorted(set(b) - set(a)), sorted(set(a) - set(b))

    print(f"{len(set(a) | set(b))} définitions comparées · "
          f"{len(modifiees)} modifiée(s), {len(ajoutees)} ajoutée(s), {len(supprimees)} supprimée(s)\n")

    problemes = []
    for nom in modifiees:
        motif = ECARTS_ATTENDUS.get(nom)
        if motif:
            print(f"  OK      {nom} — {motif}")
        else:
            problemes.append(f"définition MODIFIÉE non déclarée : {nom}")
            print(f"  ✗ ÉCART {nom} — modifiée sans être déclarée")
            for l in list(difflib.unified_diff(a[nom].splitlines(), b[nom].splitlines(),
                                               "origine", "portage", lineterm="", n=1))[:14]:
                print(f"             {l[:130]}")
    # Une définition AJOUTÉE est un écart comme un autre : elle peut être légitime (le portage
    # introduit un helper) mais elle doit être déclarée, sinon un module entier pourrait grossir
    # sans contrôle.
    for nom in ajoutees:
        motif = ECARTS_ATTENDUS.get(nom)
        if motif:
            print(f"  OK      {nom} — ajoutée · {motif}")
        else:
            problemes.append(f"définition AJOUTÉE non déclarée : {nom}")
            print(f"  ✗ ÉCART {nom} — ajoutée sans être déclarée")
    for nom in supprimees:
        # Une suppression n'est jamais anodine : c'est du code qui existait et ne s'exécute plus.
        problemes.append(f"définition SUPPRIMÉE : {nom}")
        print(f"  ✗ ÉCART {nom} — supprimée")

    # Un écart déclaré qui ne se produit plus est du bruit : soit il a été résorbé, soit il
    # était mal nommé. Le signaler évite qu'ECARTS_ATTENDUS devienne une liste d'autorisations
    # périmées — c'est ainsi que le faux négatif du 29/07 est arrivé.
    jamais = sorted(set(ECARTS_ATTENDUS) - set(modifiees) - set(ajoutees))
    if jamais:
        print(f"\n⚠ {len(jamais)} écart(s) déclaré(s) ne se produi(sen)t plus — à retirer :")
        for n in jamais:
            print(f"      {n}")

    if problemes:
        print(f"\n{len(problemes)} problème(s). Soit c'est voulu — déclarer la définition dans "
              f"ECARTS_ATTENDUS et le documenter dans le README —, soit c'est une erreur de recopie.")
        return 1

    print(f"\nAucun écart non déclaré. Les {len(modifiees)} définitions modifiées sont celles annoncées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
