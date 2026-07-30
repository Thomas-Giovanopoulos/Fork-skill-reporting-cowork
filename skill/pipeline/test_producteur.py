#!/usr/bin/env python3
"""Contrôles du producteur de propositions — sans base, sans réseau.

Les PDF de test sont fabriqués à la volée (reportlab), donc le test est autonome : il ne dépend ni
du corpus assureur, ni de la base. Si reportlab manque, les contrôles qui en ont besoin sont
sautés avec un message clair plutôt que de faire échouer la suite pour une raison sans rapport.

Le contrôle qui compte le plus est le n°4 : **aucune donnée du document ne doit fuir dans la
proposition** (D44). On le prouve en glissant des sentinelles — une chaîne reconnaissable et un
faux numéro de contrat — dans le texte du PDF, puis en vérifiant qu'elles n'apparaissent nulle part
dans la proposition sérialisée. C'est la contrepartie de la règle : la file d'adjudication est
partagée, le texte des relevés ne doit pas y monter.

Lancement :
    cd skill/pipeline && python3 test_producteur.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import producteur_propositions as P  # noqa: E402
import referentiels as R  # noqa: E402

echecs: list[str] = []


def verifie(intitule: str, obtenu, attendu) -> None:
    ok = obtenu == attendu
    print(f"  {'OK   ' if ok else 'ÉCHEC'} {intitule}")
    if not ok:
        print(f"          obtenu  : {obtenu!r}")
        print(f"          attendu : {attendu!r}")
        echecs.append(intitule)


def _pdf(chemin: Path, lignes: list[str]) -> bool:
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except ImportError:
        return False
    c = canvas.Canvas(str(chemin), pagesize=A4)
    for i, l in enumerate(lignes):
        c.drawString(60, 780 - i * 20, l)
    c.save()
    return True


# Profils : on lit le snapshot vendoré du paquet — la source de vérité hors ligne, toujours là.
PROFILS = R.charger(R.SNAPSHOT_VENDORE).gabarits

with tempfile.TemporaryDirectory(prefix="prod_") as tmp:
    tmp = Path(tmp)
    # Le numéro de contrat de la sonde utilise le préfixe XX, réservé aux références FICTIVES :
    # le garde-fou D44 de regenerer_checksums.py l'exempte, sinon ce fichier de test empêcherait
    # le scellement du paquet. Le contrôle n°4 ci-dessous reste valable — il cherche la sentinelle
    # par sous-chaîne, indépendamment du garde-fou.
    dispo = _pdf(tmp / "sonde.pdf", [
        "BANQUE FICTIVE DE TEST — RELEVE",
        "SENTINELLE_CLIENT_A_NE_PAS_FUITER",
        "Contrat n° XX99887766",
        "Valorisation au 30/06/2026 : 1 000 000 EUR",
    ])

    if not dispo:
        print("  —     reportlab absent : contrôles 1-4 sautés (à rejouer en environnement complet)")
    else:
        print("1. Un document d'émetteur inconnu → proposition 'nouveau_gabarit' à qualifier")
        prop = P.proposer_pour(tmp / "sonde.pdf", PROFILS, "2026-06-30")
        verifie("une Proposition est produite", isinstance(prop, P.Proposition), True)
        verifie("nature = nouveau_gabarit", prop.nature, "nouveau_gabarit")
        verifie("émetteur laissé à qualifier", prop.cle["emetteur_code"], "a_qualifier")
        verifie("aucun gabarit source (rien de reconnu)", prop.source_gabarit, None)
        verifie("empreinte présente (64 hex)", len(prop.source_empreinte), 64)
        verifie("arrêté repris du contexte, pas du document", prop.source_arrete, "2026-06-30")

        print("\n2. Le fichier de propositions n'est écrit que s'il y a de quoi le remplir")
        vide = P.Bilan()
        verifie("bilan vide → pas de fichier", P.ecrire(vide, tmp), None)
        bilan = P.produire([(tmp / "sonde.pdf", "2026-06-30")], PROFILS)
        dest = P.ecrire(bilan, tmp, run_id="test_run")
        verifie("bilan non vide → fichier écrit", dest is not None and dest.exists(), True)

        print("\n3. Le format écrit est directement relayable à ref_propose")
        ecrit = json.loads((tmp / P.NOM_FICHIER_PROPOSITIONS).read_text(encoding="utf-8"))
        p0 = ecrit["propositions"][0]
        verifie("porte les clés attendues par ref_propose",
                {"cible", "nature", "cle", "proposition", "source_empreinte"} <= set(p0), True)
        verifie("run_id propagé", p0.get("run_id"), "test_run")

        print("\n4. D44 — AUCUNE donnée du document ne fuit dans la proposition")
        print("   (sentinelle et numéro de contrat glissés dans le PDF ne doivent pas ressortir)")
        serialise = json.dumps(ecrit, ensure_ascii=False)
        verifie("la sentinelle de contenu n'apparaît pas",
                "SENTINELLE_CLIENT_A_NE_PAS_FUITER" in serialise, False)
        verifie("le numéro de contrat n'apparaît pas", "XX99887766" in serialise, False)
        verifie("le montant client n'apparaît pas", "1 000 000" in serialise, False)
        verifie("l'empreinte, elle, est bien là", len(ecrit["propositions"][0]["source_empreinte"]), 64)

        print("\n5. Un document illisible est signalé à part, pas proposé")
        _pdf(tmp / "vide.pdf", [])  # PDF sans texte
        r = P.proposer_pour(tmp / "vide.pdf", PROFILS, None)
        verifie("document sans texte → signalement, pas Proposition",
                isinstance(r, dict) and "OCR" in r["action"], True)

# Contrôle 6 : indépendant de reportlab — la logique de bilan sur des entrées connues.
print("\n6. Le résumé du bilan compte chaque catégorie")
b = P.Bilan(propositions=[P.Proposition("gabarit", "nouveau_gabarit", {}, {}, "x" * 64, None, None, "m")],
            illisibles=[{"a": 1}], apparies=[{"b": 2}, {"c": 3}])
verifie("résumé compte apparié/proposition/illisible",
        b.resume(), "2 apparié(s) · 1 proposition(s) · 1 illisible(s)")

print(f"\n{'ÉCHEC' if echecs else 'OK'} — {len(echecs)} échec(s)")
sys.exit(1 if echecs else 0)
