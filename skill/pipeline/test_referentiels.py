#!/usr/bin/env python3
"""Contrôles du lecteur de référentiels — sans réseau, sans base, sans corpus.

Ce fichier ne teste que de la **résolution de source** et des **accès** : c'est de la logique
pure, donc vérifiable à l'égalité exacte. L'appariement d'un document réel relève du filet A
(`outils_appariement/`), qui a besoin des PDF et vit donc hors du paquet.

Ce qui est couvert, et pourquoi chacun compte :

1. **L'ordre de résolution.** Un bundle de run doit toujours battre le snapshot vendoré, sinon un
   run utiliserait des référentiels figés alors qu'il en avait de frais sous la main.
2. **La provenance est rendue.** C'est la garantie qui rend D36 opérant : un repli silencieux
   ferait manquer à un CGP un gabarit adjugé la veille sans qu'il l'apprenne jamais.
3. **Un bundle mal formé échoue tôt et clairement**, plutôt que de rendre des listes vides qui se
   liraient comme une base vide — la confusion exacte que le champ `compte` du MCP évite.
4. **Les accès par alias et par succession.** Sans eux, un émetteur nommé autrement que dans le
   seed n'est jamais reconnu (K1), et un relevé antérieur à un changement de dépositaire reste
   inrattachable (K5).

Lancement :
    cd skill/pipeline && python3 test_referentiels.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import referentiels as R  # noqa: E402

echecs: list[str] = []


def verifie(intitule: str, obtenu, attendu) -> None:
    ok = obtenu == attendu
    print(f"  {'OK   ' if ok else 'ÉCHEC'} {intitule}")
    if not ok:
        print(f"          obtenu  : {obtenu!r}")
        print(f"          attendu : {attendu!r}")
        echecs.append(intitule)


def bundle_minimal(**extra) -> dict:
    base = {
        "schema_version": "0.1-skill",
        "acteurs": [
            {"code": "wealins", "nom": "WEALINS S.A.", "role": "assureur",
             "alias": ["Wealins Capi France", "WEALINS"]},
            {"code": "cic", "nom": "CIC", "role": "depositaire", "alias": []},
        ],
        "successions": [
            {"predecesseur_code": "cic", "successeur_code": "quintet",
             "contexte": "reprise de la poche FID ex-CIC"},
        ],
        "gabarits": [
            {"emetteur_code": "cardif", "gabarit": "g", "valide_depuis": "2025-12-31"},
            {"emetteur_code": "cardif", "gabarit": "g", "valide_depuis": "2024-01-01",
             "valide_jusqu_a": "2025-12-31"},
            {"emetteur_code": "wealins", "gabarit": "annuel", "valide_depuis": "0001-01-01"},
        ],
        "compte": {"acteurs": 2, "successions": 1, "gabarits": 3, "isin": 261},
    }
    base.update(extra)
    return base


with tempfile.TemporaryDirectory(prefix="ref_") as tmp:
    tmp = Path(tmp)
    fichier_run = tmp / R.NOM_BUNDLE_RUN
    fichier_run.write_text(json.dumps(bundle_minimal(), ensure_ascii=False), encoding="utf-8")

    print("1. Ordre de résolution — un bundle de run bat toujours le snapshot vendoré")
    r = R.charger(fichier_run)
    verifie("chemin explicite → provenance 'run'", r.provenance, "run")
    verifie("le snapshot vendoré existe bien par ailleurs", R.SNAPSHOT_VENDORE.is_file(), True)

    _, prov = R.resoudre_source(dossier_run=tmp)
    verifie("dossier de run contenant le bundle → 'run'", prov, "run")

    _, prov = R.resoudre_source(dossier_run=tmp / "vide")
    verifie("aucun bundle de run → repli 'snapshot_vendore'", prov, "snapshot_vendore")

    os.environ[R.VARIABLE_ENV] = str(fichier_run)
    try:
        _, prov = R.resoudre_source(dossier_run=tmp / "vide")
        verifie("variable d'environnement → 'run' malgré un dossier vide", prov, "run")
    finally:
        del os.environ[R.VARIABLE_ENV]

    print("\n2. La provenance est RENDUE, et le repli se voit dans le résumé")
    snap = R.charger(R.SNAPSHOT_VENDORE)
    verifie("snapshot → provenance 'snapshot_vendore'", snap.provenance, "snapshot_vendore")
    verifie("le résumé du repli avertit", "SNAPSHOT VENDORÉ" in snap.resume(), True)
    verifie("le résumé d'un run n'avertit pas", "SNAPSHOT VENDORÉ" in r.resume(), False)
    verifie("le snapshot ne porte PAS les ISIN (doublon évité)",
            "isin" in json.loads(R.SNAPSHOT_VENDORE.read_text(encoding="utf-8")), False)

    print("\n3. Un bundle mal formé échoue tôt, plutôt que de se lire comme une base vide")
    casse = tmp / "casse.json"
    casse.write_text("{ pas du json", encoding="utf-8")
    try:
        R.charger(casse); verifie("JSON invalide → exception", False, True)
    except R.ReferentielsIntrouvables as e:
        verifie("JSON invalide → exception nommant le fichier", casse.name in str(e), True)

    sans_gabarits = tmp / "sans.json"
    sans_gabarits.write_text(json.dumps({"schema_version": "x", "acteurs": [],
                                         "successions": []}), encoding="utf-8")
    try:
        R.charger(sans_gabarits); verifie("section absente → exception", False, True)
    except R.ReferentielsIntrouvables as e:
        verifie("section absente → exception la nommant", "gabarits" in str(e), True)

    try:
        R.resoudre_source(dossier_run=tmp / "vide", chemin=None)
        # le snapshot existe, donc pas d'exception : on vérifie le cas sans snapshot ailleurs
    except R.ReferentielsIntrouvables:
        pass

    print("\n4. Accès — alias, successions, et l'ordre des versions (D42)")
    verifie("acteur par code", r.acteur("wealins")["nom"], "WEALINS S.A.")
    verifie("acteur par alias, accents et casse ignorés",
            r.acteur("wealins capi france")["code"], "wealins")
    verifie("acteur inconnu → None", r.acteur("zzz_inexistant"), None)
    verifie("succession par prédécesseur", r.successeur("cic")["successeur_code"], "quintet")
    verifie("aucune succession → None", r.successeur("wealins"), None)
    verifie("gabarits d'un émetteur triés du plus ancien au plus récent",
            [g["valide_depuis"] for g in r.gabarits_de("cardif")],
            ["2024-01-01", "2025-12-31"])
    verifie("émetteur sans gabarit → liste vide", r.gabarits_de("zzz"), [])

    print("\n5. Le compte du bundle est conservé — un appel partiel ne doit pas se lire vide")
    verifie("compte.isin préservé alors que la section est absente du snapshot",
            snap.compte.get("isin"), 261)

print(f"\n{'ÉCHEC' if echecs else 'OK'} — {len(echecs)} échec(s)")
sys.exit(1 if echecs else 0)
