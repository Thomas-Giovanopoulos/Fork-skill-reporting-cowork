"""
test_store_builder.py
======================

Construit un mini-client synthetique pour verifier store_builder:
- 1 entite holding
- 1 contrat financier_cote avec 2 lines + 1 pocket
- 1 fonds non_cote
- 2 mouvements (dont un entry_ref pointant vers le contrat fc)

Verifie:
1. Le client valide contre store_client.schema.json (draft 2020-12).
2. Les ids provisoires sont sequentiels (tmp_fc_001, tmp_nc_001, tmp_mv_001,
   tmp_mv_002, ...).
3. Aucune cle a valeur None n'est presente dans le JSON serialise (discipline
   ABSENCE != NULL), sauf cas EXPLICIT_NULL (non utilise ici).
4. Le entry_ref du mouvement resout bien vers un id existant (check_refs).
"""
import json
import sys

from store_builder import (
    EXPLICIT_NULL,
    add_entry,
    check_refs,
    new_client,
    validate,
    validate_all,
)


def _find_none_paths(obj, path="$"):
    """Retourne la liste des chemins ou une valeur JSON est strictement None."""
    bad = []
    if obj is None:
        bad.append(path)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            bad.extend(_find_none_paths(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad.extend(_find_none_paths(v, f"{path}[{i}]"))
    return bad


def build_sample_client() -> dict:
    client = new_client(
        label="Famille Dupont",
        entities=[
            {"label": "Holding Dupont SAS", "type": "holding"},
        ],
        reporting={
            "period_short": "T2 2026",
            "period_long": "2e trimestre 2026",
            "date_reporting": "2026-06-30",
            "date_display": "30/06/2026",
            "version": "1.0",
            "profile": "equilibre",
            # champ volontairement absent pour tester la discipline absence != null
            "commentaire_interne": None,
        },
    )

    holding_id = client["client"]["entities"][0]["id"]

    fc_id = add_entry(
        client,
        "financier_cote",
        {
            "entity_id": holding_id,
            "label": "Contrat AV Lux Multisupport",
            "source": "releve_assureur",
            "envelope_type": "assurance_vie_lux",
            "manager": "Gestion Pilotee Rhetores",
            "custodian": "Depositaire XYZ",
            "management_mode": "gestion_pilotee",
            "risk_profile": "equilibre",
            "invest_date": "2020-03-15",
            "capital_invested": 500000,
            "value_current": 560000,
            "value_jan1": 540000,
            # value_projected volontairement absent (donnee non disponible)
            "value_projected": None,
            "pledged": False,
            "attributes": {
                "lines": [
                    {
                        "isin": "FR0000000001",
                        "label": "Fonds Actions Monde",
                        "value": 300000,
                        "class": "actions",
                        "geography": "monde",
                        "sri": 4,
                        "pocket": "Poche Dynamique",
                    },
                    {
                        "isin": "FR0000000002",
                        "label": "Fonds Obligataire Euro",
                        "value": 260000,
                        "class": "obligations",
                        "geography": "europe",
                        # sri absent (non renseigne par le depositaire)
                        "sri": None,
                    },
                ],
                "pockets": [
                    {
                        "label": "Poche Dynamique",
                        "manager": "Gestion Pilotee Rhetores",
                        "profile": "dynamique",
                        "value": 300000,
                        "capital_invested": 280000,
                    }
                ],
            },
        },
    )

    nc_id = add_entry(
        client,
        "non_cote",
        {
            "entity_id": holding_id,
            "label": "FPCI Croissance France IV",
            "manager": "Gestionnaire NC",
            "classe_rhetores": "private_equity",
            "capital_committed": 150000,
            "capital_called": 90000,
            "value_current": 105000,
            "value_date": "2026-06-30",
            "attributes": {
                "strategy": "buyout",
                "segment": "mid_market",
                "vintage": 2021,
                "moic_target": 2.2,
                # moic_realise absent car fonds encore jeune
                "moic_realise": None,
            },
        },
    )

    mv1_id = add_entry(
        client,
        "mouvements",
        {
            "entry_ref": fc_id,
            "date": "2020-03-15",
            "type": "versement",
            "amount": 500000,
            "comment": "Versement initial",
        },
    )

    mv2_id = add_entry(
        client,
        "mouvements",
        {
            "entry_ref": fc_id,
            "date": "2025-11-10",
            "type": "retrait",
            "amount": -20000,
            # comment absent (pas de commentaire pour ce retrait)
            "comment": None,
        },
    )

    return client, {
        "fc_id": fc_id,
        "nc_id": nc_id,
        "mv1_id": mv1_id,
        "mv2_id": mv2_id,
    }


def run() -> bool:
    ok = True
    client, ids = build_sample_client()

    # --- 1. ids sequentiels ---------------------------------------------
    expected = {
        "fc_id": "tmp_fc_001",
        "nc_id": "tmp_nc_001",
        "mv1_id": "tmp_mv_001",
        "mv2_id": "tmp_mv_002",
    }
    if ids != expected:
        print(f"[FAIL] ids sequentiels: attendu {expected}, obtenu {ids}")
        ok = False
    else:
        print(f"[PASS] ids provisoires sequentiels: {ids}")

    # --- 2. validation JSON Schema ---------------------------------------
    errors = validate_all(client)
    if errors:
        print("[FAIL] validation schema:")
        for e in errors:
            print(f"    - {e}")
        ok = False
    else:
        try:
            validate(client)
            print("[PASS] validation schema (draft 2020-12) OK")
        except Exception as exc:  # pragma: no cover
            print(f"[FAIL] validate() a leve une exception inattendue: {exc}")
            ok = False

    # --- 3. discipline ABSENCE != NULL -----------------------------------
    serialized = json.dumps(client, ensure_ascii=False)
    none_paths = _find_none_paths(client)
    # verification supplementaire via round-trip JSON (ceinture + bretelles)
    reparsed = json.loads(serialized)
    none_paths_reparsed = _find_none_paths(reparsed)
    if none_paths or none_paths_reparsed:
        print(f"[FAIL] cles a valeur None trouvees: {none_paths or none_paths_reparsed}")
        ok = False
    else:
        print("[PASS] aucune cle a valeur None dans le client / JSON serialise")

    # --- 4. check_refs -----------------------------------------------------
    problems = check_refs(client)
    if problems:
        print("[FAIL] check_refs a trouve des problemes:")
        for p in problems:
            print(f"    - {p}")
        ok = False
    else:
        print("[PASS] check_refs: tous les entry_ref resolvent vers un id existant")

    # --- bonus: verifier qu'un entry_ref invalide est bien detecte ----------
    broken_client = json.loads(json.dumps(client))
    broken_client["mouvements"].append(
        {
            "id": "tmp_mv_099",
            "entry_ref": "tmp_fc_999",
            "date": "2026-01-01",
            "type": "frais",
            "amount": -100,
        }
    )
    broken_problems = check_refs(broken_client)
    if not broken_problems:
        print("[FAIL] check_refs aurait du detecter un entry_ref casse")
        ok = False
    else:
        print(f"[PASS] check_refs detecte bien un entry_ref casse: {broken_problems}")

    # ------------------------------------------------------------------
    # Invariant A5 : un contrat finance cote a TOUJOURS au moins une poche.
    # ------------------------------------------------------------------
    # Le tableau de rendu a une ligne par poche : un contrat sans poche reelle en
    # declare une qui le decrit lui-meme. C'est ce qui donne au lecteur de
    # forme-store un chemin de code unique, et rend le compte de poches exact par
    # construction. Sans ce test, l'invariant n'est qu'un commentaire : rien
    # n'empecherait un futur constructeur de reintroduire des contrats sans poche,
    # et le lecteur retomberait silencieusement sur deux chemins.
    import copy as _copy

    sans_poche = _copy.deepcopy(client)
    del sans_poche["financier_cote"][0]["attributes"]["pockets"]
    erreurs_sans_poche = validate_all(sans_poche)
    if not erreurs_sans_poche:
        print("[FAIL] un contrat SANS poche aurait du etre refuse (invariant A5)")
        ok = False
    else:
        print(f"[PASS] contrat sans poche refuse (invariant A5): {erreurs_sans_poche[0][:90]}")

    poche_vide = _copy.deepcopy(client)
    poche_vide["financier_cote"][0]["attributes"]["pockets"] = []
    erreurs_poche_vide = validate_all(poche_vide)
    if not erreurs_poche_vide:
        print("[FAIL] une liste de poches VIDE aurait du etre refusee (minItems: 1)")
        ok = False
    else:
        print(f"[PASS] liste de poches vide refusee: {erreurs_poche_vide[0][:90]}")

    # Les champs ajoutes a `pocket` par A5 doivent etre ACCEPTES : `pocket` est
    # additionalProperties:false, donc un oubli d'amendement se verrait ici.
    poche_riche = _copy.deepcopy(client)
    poche_riche["financier_cote"][0]["attributes"]["pockets"][0].update({
        "type": "FAS",
        "custodian": "CA Indosuez (Switzerland) S.A.",
        "value_jan1": 290000,
        "invest_date": "2024-11-05",
        "pledged": False,
    })
    erreurs_poche_riche = validate_all(poche_riche)
    if erreurs_poche_riche:
        print(f"[FAIL] les champs A5 de pocket sont refuses: {erreurs_poche_riche}")
        ok = False
    else:
        print("[PASS] pocket accepte type/custodian/value_jan1/invest_date/pledged (A5)")

    return ok


if __name__ == "__main__":
    success = run()
    if success:
        print("\n=== TOUS LES TESTS PASSENT ===")
        sys.exit(0)
    else:
        print("\n=== ECHEC D'AU MOINS UN TEST ===")
        sys.exit(1)
