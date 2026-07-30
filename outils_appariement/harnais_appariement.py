#!/usr/bin/env python3
"""Filet A — vérifie l'appariement des documents du corpus contre la table de vérité.

C'est le filet qui manquait, et sa raison d'être est la limite **LIM8** : les 7 fixtures de
régression exercent le *rendu* (`p2_fill`), alors que signatures et pièges pilotent
l'*extraction*. Tout ce que l'étude de corpus a établi était donc, jusqu'ici, invérifiable.

Ce harnais ne teste que ce qui est **déterministe** : l'appariement d'un document à son profil,
du code sur du texte. La qualité de l'extraction des valeurs, faite par un subagent, relève d'un
second filet qui n'assertera jamais l'égalité de chaînes mais des invariants (`invariant_controle`,
présence des champs de `champs_publies`). Confondre les deux condamnerait soit à des tests
fragiles, soit à n'en écrire aucun — c'est vraisemblablement pourquoi il n'y en avait pas.

Trois choix de conduite :

**Les documents `a_etablir` sont SIGNALÉS, pas comptés en échec.** Les cinq Nortia n'ont pas été
étudiés ; les faire échouer donnerait un rouge permanent qu'on apprendrait à ignorer, ce qui est
pire que pas de test. Ils sortent dans une rubrique distincte.

**Les documents `presume_reedition` sont vérifiés, mais leur réussite ne prouve rien sur le passé.**
Ce sont des rééditions du 24/07/2026 : elles portent le format actuel de l'émetteur, pas celui de
leur arrêté. Le harnais le rappelle dans son verdict pour qu'on ne lise pas « 12/12 chez Spirica »
comme une preuve de stabilité sur quatre ans.

**L'affichage est incrémental.** `run_tests.py` n'imprime qu'à la fin et devient indistinguable
d'un blocage sur un sandbox lent ; on ne refait pas cette erreur. Filtrable par émetteur pour
tenir dans la limite de 45 s d'un appel.

**Les chemins du corpus ne sont PAS codés en dur.** Ils l'ont été, sur le montage de sandbox du
jour (`/sessions/<session>/mnt/…`), ce qui rendait le filet injouable ailleurs — un filet qui ne se
rejoue pas sur une autre machine n'est pas un filet. Ils se règlent désormais par variable
d'environnement ou par option, le défaut restant ce montage. Et l'absence du corpus est signalée
explicitement, avec les chemins essayés : un `FileNotFoundError` par document donnerait 37 échecs
d'appariement pour un dossier mal monté, ce qui est le diagnostic exactement inverse du vrai.

Usage :
    python3 harnais_appariement.py                      # tout le corpus, profils de ce dossier
    python3 harnais_appariement.py cardif wealins       # seulement ces émetteurs
    python3 harnais_appariement.py --verbeux            # + l'explication de chaque appariement
    python3 harnais_appariement.py --profils ../seed/gabarits.json
    python3 harnais_appariement.py --corpus /chemin/vers/le/parent   # racine des deux dossiers
    CORPUS_RACINE=/chemin/vers/le/parent python3 harnais_appariement.py

Le `--profils` n'est pas une commodité : c'est **le** contrôle qui prouve que le seed porte bien
les ancres vérifiées. `profils_corpus.json` est le brouillon validé par ce harnais ; le seed en
est la conversion, et une conversion ne se croit pas, elle se rejoue. Faire passer les 37
documents en lisant le seed, c'est vérifier que la conversion n'a rien perdu en route.

Résolution des chemins du corpus, par ordre de priorité :

1. `--corpus <racine>` ou `CORPUS_RACINE` : dossier **parent** contenant `Données assureur/` et
   `15.7.26/`. C'est le cas courant, les deux dossiers voyageant ensemble.
2. `CORPUS_DONNEES_ASSUREUR` / `CORPUS_15_7_26` : un chemin complet par dossier, pour le cas où
   ils ne partagent pas de parent.
3. À défaut, le montage de sandbox `/sessions/epic-happy-ritchie/mnt/` — le défaut historique,
   conservé pour que la commande d'origine continue de fonctionner sans argument.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matcher_gabarit import apparier, charger_profils  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
TABLE = RACINE / "docs" / "etude_corpus_2026-07-29" / "table_verite_appariement.json"
PROFILS = Path(__file__).resolve().parent / "profils_corpus.json"

# Défaut historique : le montage de sandbox sur lequel le corpus a été étudié le 2026-07-29.
CORPUS_RACINE_DEFAUT = Path("/sessions/epic-happy-ritchie/mnt")
# Nom du sous-dossier -> variable d'environnement qui permet de le pointer seul.
SOUS_DOSSIERS = {
    "Données assureur": "CORPUS_DONNEES_ASSUREUR",
    "15.7.26": "CORPUS_15_7_26",
}


def resoudre_dossiers(racine_cli: str | None) -> dict[str, Path]:
    """Rend {nom logique: chemin}, sans vérifier l'existence — c'est `verifier_dossiers` qui le fait."""
    racine = Path(racine_cli or os.environ.get("CORPUS_RACINE") or CORPUS_RACINE_DEFAUT).expanduser()
    dossiers = {}
    for nom, var in SOUS_DOSSIERS.items():
        surcharge = os.environ.get(var)
        dossiers[nom] = Path(surcharge).expanduser() if surcharge else racine / nom
    return dossiers


def verifier_dossiers(dossiers: dict[str, Path], requis: set[str]) -> None:
    """Échoue tôt et en nommant les chemins essayés, plutôt que 37 fois à l'ouverture d'un PDF."""
    manquants = [(nom, chemin) for nom, chemin in dossiers.items()
                 if nom in requis and not chemin.is_dir()]
    if not manquants:
        return
    lignes = [f"  · {nom!r} attendu à : {chemin}" for nom, chemin in manquants]
    sys.exit(
        "Corpus introuvable — le harnais ne peut pas s'exécuter.\n"
        + "\n".join(lignes)
        + "\n\nLe corpus n'est pas dans le dépôt (documents clients). Indiquer où il se trouve :\n"
          "  python3 harnais_appariement.py --corpus /chemin/vers/le/parent\n"
          "  CORPUS_RACINE=/chemin/vers/le/parent python3 harnais_appariement.py\n"
          "La racine attendue est le dossier PARENT de "
        + " et ".join(repr(n) for n in SOUS_DOSSIERS)
        + ".\nPour les pointer séparément : "
        + ", ".join(f"{var} ({nom!r})" for nom, var in SOUS_DOSSIERS.items())
        + "."
    )


def main() -> int:
    args = sys.argv[1:]
    verbeux = "--verbeux" in args
    source = PROFILS
    racine_cli = None
    if "--corpus" in args:
        i = args.index("--corpus")
        if i + 1 >= len(args):
            sys.exit("--corpus attend un chemin")
        racine_cli = args[i + 1]
        args = args[:i] + args[i + 2:]
    if "--profils" in args:
        i = args.index("--profils")
        if i + 1 >= len(args):
            sys.exit("--profils attend un chemin")
        source = Path(args[i + 1])
        if not source.is_absolute():
            source = (Path.cwd() / source).resolve()
        args = args[:i] + args[i + 2:]
    filtres = [a for a in args if not a.startswith("--")]

    table = json.loads(TABLE.read_text(encoding="utf-8"))
    profils = charger_profils(source)
    if source != PROFILS:
        print(f"profils lus depuis : {source}")
    docs = table["documents"]
    if filtres:
        docs = [d for d in docs if d["emetteur_code"] in filtres]
        if not docs:
            emetteurs = sorted({d["emetteur_code"] for d in table["documents"]})
            sys.exit(f"Aucun document pour {filtres}. Émetteurs : {emetteurs}")

    dossiers = resoudre_dossiers(racine_cli)
    verifier_dossiers(dossiers, {d.get("dossier", "Données assureur") for d in docs})

    print(f"{len(profils)} profils · {len(docs)} documents\n")
    ok, echecs, signales = [], [], []

    for d in docs:
        # Le nom est pris TEL QUEL dans la table : trois fichiers portent un nom mojibake et
        # aucune normalisation Unicode ne le reconstruit (cf. _a_propos.piege_encodage).
        chemin = dossiers[d.get("dossier", "Données assureur")] / d["fichier"]
        t0 = time.time()
        v = apparier(chemin, profils, d.get("arrete"))
        dt = time.time() - t0

        attendu = (d["emetteur_code"], d["gabarit"], d.get("valide_depuis_attendu"))
        obtenu = (v.emetteur_code, v.gabarit, v.valide_depuis)
        # `valide_depuis` n'est comparé que si la table l'exige : la plupart des gabarits n'ont
        # pas de fenêtre, et en inventer une pour uniformiser serait fabriquer une contrainte.
        conforme = (obtenu[0], obtenu[1]) == (attendu[0], attendu[1]) and (
            attendu[2] is None or obtenu[2] == attendu[2])

        nom = d.get("nom_lisible", d["fichier"])
        if d["certitude"] == "a_etablir":
            signales.append((nom, v, conforme))
            marque, suffixe = "SIGNALÉ", "  (profil non établi — non compté)"
        elif conforme and v.statut == "apparie":
            ok.append((nom, v))
            marque, suffixe = "OK     ", ""
        else:
            echecs.append((nom, v, attendu, obtenu))
            marque, suffixe = "ÉCHEC  ", ""

        print(f"  {marque} {nom[:58]:58s} {v.resume():48s} {dt:4.1f}s{suffixe}")
        if verbeux or (marque.strip() == "ÉCHEC"):
            for l in v.explication[:6]:
                print(f"            · {l[:150]}")
            if marque.strip() == "ÉCHEC":
                print(f"            attendu : {attendu}")
                print(f"            obtenu  : {obtenu}")

    total_compte = len(ok) + len(echecs)
    print(f"\n{len(ok)}/{total_compte} appariés" + (f" · {len(signales)} signalé(s)" if signales else ""))

    reeditions = sum(1 for d in docs if d.get("certitude") == "presume_reedition")
    if reeditions:
        print(f"\n⚠ {reeditions} des documents vérifiés sont des RÉÉDITIONS du 24/07/2026 : leur "
              f"appariement confirme le format ACTUEL de l'émetteur et ne dit rien du format\n"
              f"  d'époque. Ne pas lire ce résultat comme une preuve de stabilité dans le temps.")

    if echecs:
        print(f"\n{len(echecs)} échec(s) — voir les explications ci-dessus.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
