#!/usr/bin/env python3
"""Contrôles de l'apply et du valideur de diffs — B-ii, sans réseau, sans corpus.

Chaque responsabilité de l'apply est prouvée, et prouvée AUSSI par le refus : un invariant
qu'on n'a pas vu échouer n'est qu'un commentaire (leçon des suites précédentes).

Lancement :
    cd skill/pipeline && python3 test_apply.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appliquer_diffs as AP  # noqa: E402
import referentiels as R  # noqa: E402
import store_builder as SB  # noqa: E402
from valider_diff import valider  # noqa: E402

echecs: list[str] = []


def verifie(intitule: str, obtenu, attendu) -> None:
    ok = obtenu == attendu
    print(f"  {'OK   ' if ok else 'ÉCHEC'} {intitule}")
    if not ok:
        print(f"          obtenu  : {obtenu!r}")
        print(f"          attendu : {attendu!r}")
        echecs.append(intitule)


REFS = R.charger(R.SNAPSHOT_VENDORE)


def base_store() -> dict:
    client = SB.new_client(
        label="Client Exemple",
        entities=[{"id": "pp", "label": "Client Exemple", "type": "pp", "order": 0}],
        reporting={"period_short": "T2-26", "period_long": "T2 2026",
                   "date_reporting": "2026-06-30", "date_display": "30 juin 2026",
                   "version": "v1", "profile": "Équilibré"},
    )
    SB.add_entry(client, "financier_cote", {
        "entity_id": "pp", "label": "AV — Wealins", "assureur": "wealins",
        "envelope_type": "av_lu", "manager": "Gérant A", "value_current": 100000,
        "attributes": {"pockets": [{"id": "pck_001", "label": "AV — Wealins",
                                    "value": 100000}]},
    })
    return client


def diff_minimal(**kw) -> dict:
    d = {"client_id": "tmp_c_001", "source_document": "releve_test.pdf",
         "status": "pending_validation", "changes": [], "unrecognized_data": []}
    d.update(kw)
    return d


# ---------------------------------------------------------------------------
print("1. Le valideur — refus prouvés, avertissements prouvés")

ok_create = diff_minimal(changes=[{
    "category": "financier_cote", "entry_id": None, "entry_label": "CTO — Banque Fictive",
    "entity_id": "pp", "action": "create", "confidence": "high",
    "fields": [{"path": "value_current", "old_value": None, "new_value": 50000,
                "source_page": 1}],
}])
e, a = valider(ok_create)
verifie("un diff bien formé passe", (e, a), ([], []))

upd_sans_id = copy.deepcopy(ok_create)
upd_sans_id["changes"][0]["action"] = "update"
e, _ = valider(upd_sans_id)
verifie("update sans entry_id refusé", bool(e), True)

mvt_negatif = diff_minimal(changes=[{
    "category": "mouvements", "entry_id": None, "entry_label": "versement",
    "entity_id": "pp", "action": "create", "confidence": "high",
    "fields": [{"path": "amount", "old_value": None, "new_value": -500}],
}])
e, _ = valider(mvt_negatif)
verifie("montant négatif refusé (A4)", any("A4" in x for x in e), True)

variantes = diff_minimal(changes=[{
    "category": "financier_cote", "entry_id": None, "entry_label": "X",
    "entity_id": "pp", "action": "create", "confidence": "high",
    "fields": [{"path": "attributes.lines", "old_value": None,
                "new_value": [{"label": "F1", "value_eur": 100, "class_code": "actions"}]}],
}])
e, a = valider(variantes)
verifie("variantes connues = avertissement, pas erreur", (len(e), len(a) >= 2), (0, True))

inconnue = copy.deepcopy(variantes)
inconnue["changes"][0]["fields"][0]["new_value"] = [{"label": "F1", "value": 100,
                                                     "class": "actions", "montant_brut": 1}]
e, _ = valider(inconnue)
verifie("clé de ligne inconnue refusée (donnée qui se perdrait)", bool(e), True)

# ---------------------------------------------------------------------------
print("\n2. Création : poche 0 (A5), pocket.id (C7), jointure par libellé résolue")

diff_creation = diff_minimal(changes=[
    {"category": "financier_cote", "entry_id": None,
     "entry_label": "CTO — Banque Alpha", "entity_id": "pp", "action": "create",
     "confidence": "high",
     "fields": [
         {"path": "assureur", "old_value": None, "new_value": "Banque Alpha"},
         {"path": "envelope_type", "old_value": None, "new_value": "cto"},
         {"path": "manager", "old_value": None, "new_value": "Gérant B"},
         {"path": "value_current", "old_value": None, "new_value": 50000},
         {"path": "attributes.lines", "old_value": None,
          "new_value": [{"label": "Fonds X", "value_eur": 50000, "class_code": "actions",
                         "pocket": "CTO — Banque Alpha"}]},
     ]},
])
store, rapport = AP.appliquer(base_store(), [diff_creation], {"date_arrete": "2026-06-30"}, REFS)
fc = store["financier_cote"][1]
poche = fc["attributes"]["pockets"][0]
verifie("poche 0 auto-créée (A5), id attribué en séquence globale",
        (poche["label"], poche["id"]), ("CTO — Banque Alpha", "pck_002"))
verifie("lines[].pocket résolu du libellé vers l'id", fc["attributes"]["lines"][0]["pocket"],
        "pck_002")
verifie("variante value_eur normalisée en value", fc["attributes"]["lines"][0]["value"], 50000)
verifie("acteur inconnu : verbatim conservé + signalé (K3, jamais de code inventé)",
        (fc["assureur"], rapport.acteurs_non_resolus), ("Banque Alpha", ["Banque Alpha"]))
verifie("store final valide (2.1-skill) et refs OK", rapport.erreurs, [])

print("\n3. Résolution acteur par alias, et provenance D49 posée depuis le contexte")

diff_wealins = copy.deepcopy(diff_creation)
diff_wealins["changes"][0]["fields"][0]["new_value"] = "Wealins"  # alias -> code
# gabarit à perf_par_ligne = "oui" (Wealins publie PAR POCHE — mauvais candidat pour MQ11,
# première version de ce test corrigée : la matrice champs_publies fait foi)
contexte = {"date_arrete": "2026-06-30",
            "documents": {"releve_test.pdf": {"empreinte": "a" * 64,
                                              "gabarit": "evaluation_portefeuille_mandat"}}}
store, rapport = AP.appliquer(base_store(), [diff_wealins], contexte, REFS)
fc = store["financier_cote"][1]
verifie("alias « Wealins » résolu vers le code", fc["assureur"], "wealins")
verifie("provenance D49 complète sur l'entrée",
        (fc.get("source_document"), fc.get("source_empreinte") == "a" * 64,
         fc.get("source_gabarit"), fc.get("source_arrete")),
        ("releve_test.pdf", True, "evaluation_portefeuille_mandat", "2026-06-30"))

print("\n4. MQ11 : le gabarit publie la perf, une ligne sans perf_pct est signalée")
verifie("avertissement MQ11 présent",
        any("MQ11" in a for a in rapport.avertissements), True)

# ---------------------------------------------------------------------------
print("\n5. Update : conflit old_value ≠ store → champ NON appliqué (jamais last-write-wins)")

diff_conflit = diff_minimal(changes=[{
    "category": "financier_cote", "entry_id": "tmp_fc_001",
    "entry_label": "AV — Wealins", "entity_id": "pp", "action": "update",
    "confidence": "high",
    "fields": [
        {"path": "value_current", "old_value": 99999, "new_value": 123456},   # conflit
        {"path": "value_jan1", "old_value": None, "new_value": 95000},        # applicable
    ]}])
store, rapport = AP.appliquer(base_store(), [diff_conflit], {}, REFS)
fc = store["financier_cote"][0]
verifie("champ en conflit inchangé au store", fc["value_current"], 100000)
verifie("conflit rapporté pour la réconciliation (B3)", len(rapport.conflits), 1)
verifie("champ sans conflit appliqué dans le même change", fc.get("value_jan1"), 95000)

print("\n6. Un diff invalide ne s'applique pas, les autres du lot oui")
lot = [upd_sans_id, diff_creation]
store, rapport = AP.appliquer(base_store(), lot, {}, REFS)
verifie("diff invalide → erreurs rapportées", bool(rapport.erreurs), True)
verifie("le diff valide du lot est appliqué", len(store["financier_cote"]), 2)

print("\n7. D44/L5 — rien d'inventé : un champ non fourni est ABSENT, pas défauté")
fc = store["financier_cote"][1]
verifie("custodian non fourni → absent", "custodian" in fc, False)
verifie("intermediaire non fourni → absent", "intermediaire" in fc, False)

print(f"\n{'ÉCHEC' if echecs else 'OK'} — {len(echecs)} échec(s)")
sys.exit(1 if echecs else 0)
