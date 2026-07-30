"""Validation déterministe d'un contrat de diff — B-ii, première couche du filet B.

Le jsonschema (`diff_contract.schema.json`) vérifie la FORME ; ce module ajoute les règles que
le schéma ne sait pas dire, chacune héritée d'une décision ou d'un incident :

- **`entry_id` ⇔ `action`** : `update` sans `entry_id` ne peut viser personne ; c'est une
  création déguisée ou une erreur de subagent — refusé, jamais deviné.
- **A4 figé** : un montant de `mouvements` est ≥ 0, le sens vient du type. Un signe négatif est
  une erreur qui attend son heure (spec §7.6) — refusé à l'entrée, pas à l'apply.
- **Vocabulaire des lignes** : les `new_value` de `attributes.lines` emploient les noms du
  `$defs.line` du schéma de store. Deux runs réels ont produit des variantes (`value_eur`,
  `class_code`, `geo_code`…) : les variantes CONNUES sont signalées en avertissement (l'apply
  les normalise) ; une clé INCONNUE est une erreur — un champ qu'on ne reconnaît pas est une
  donnée qui se perdrait en silence.

Usage :
    python3 valider_diff.py diff1.json [diff2.json …]     # 0 si tout passe, 1 sinon
    from valider_diff import valider                      # -> (erreurs, avertissements)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover
    raise ImportError("pip install --break-system-packages jsonschema") from exc

_SCHEMA_PATH = Path(__file__).parent / "diff_contract.schema.json"

# Variantes observées sur des runs réels → nom canonique du $defs.line. L'apply normalise,
# le valideur signale : la variance est tolérée en entrée, jamais silencieuse.
SYNONYMES_LIGNE = {
    "value_eur": "value", "valuation_eur": "value",
    "class_code": "class", "asset_class": "class",
    "geo_code": "geography",
}
CLES_LIGNE = {"isin", "label", "value", "class", "geography", "sri", "pocket", "perf_pct"}


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def valider(diff: dict, nom: str = "<diff>") -> tuple[list[str], list[str]]:
    """Rend (erreurs, avertissements). Erreurs non vides = diff inapplicable."""
    erreurs: list[str] = []
    avert: list[str] = []

    v = Draft202012Validator(_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER)
    for e in sorted(v.iter_errors(diff), key=lambda x: list(x.path)):
        chemin = "/".join(str(p) for p in e.path) or "<racine>"
        erreurs.append(f"{nom}:{chemin}: {e.message}")
    if erreurs:
        return erreurs, avert  # forme invalide : les règles métier n'ont pas de base saine

    for i, ch in enumerate(diff.get("changes", [])):
        ou = f"{nom}:changes[{i}] ({ch.get('entry_label', '?')})"

        # entry_id ⇔ action
        if ch["action"] == "update" and not ch.get("entry_id"):
            erreurs.append(f"{ou}: update sans entry_id — ne vise personne. Création déguisée "
                           f"ou erreur : à corriger à la source, pas à deviner ici.")
        if ch["action"] == "create" and ch.get("entry_id"):
            avert.append(f"{ou}: create avec entry_id {ch['entry_id']!r} — référence intra-lot "
                         f"tolérée, l'apply attribue l'id définitif.")

        for f in ch.get("fields", []):
            path, nv = f["path"], f.get("new_value")

            # A4 : montants de mouvements toujours positifs
            if ch["category"] == "mouvements" and path == "amount" and isinstance(nv, (int, float)):
                if nv < 0:
                    erreurs.append(f"{ou}: amount = {nv} — A4 figé : montant ≥ 0, le sens vient "
                                   f"du type. Corriger le diff, pas absorber le signe.")

            # vocabulaire des lignes
            if path == "attributes.lines" and isinstance(nv, list):
                for j, ligne in enumerate(nv):
                    if not isinstance(ligne, dict):
                        erreurs.append(f"{ou}: attributes.lines[{j}] n'est pas un objet")
                        continue
                    for cle in ligne:
                        if cle in CLES_LIGNE:
                            continue
                        if cle in SYNONYMES_LIGNE:
                            avert.append(f"{ou}: lines[{j}].{cle} — variante connue, "
                                         f"normalisée en {SYNONYMES_LIGNE[cle]!r} à l'apply. "
                                         f"À éviter à la source.")
                        else:
                            erreurs.append(f"{ou}: lines[{j}].{cle} — clé inconnue du "
                                           f"$defs.line : cette donnée se perdrait en silence. "
                                           f"Noms canoniques : {sorted(CLES_LIGNE)}.")
    return erreurs, avert


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: valider_diff.py diff1.json [diff2.json …]")
    code = 0
    for chemin in sys.argv[1:]:
        diff = json.loads(Path(chemin).read_text(encoding="utf-8"))
        erreurs, avert = valider(diff, Path(chemin).name)
        for a in avert:
            print(f"  AVERT  {a}")
        for e in erreurs:
            print(f"  ERREUR {e}")
        print(f"{'ÉCHEC ' if erreurs else 'OK    '}{chemin} — "
              f"{len(erreurs)} erreur(s), {len(avert)} avertissement(s)")
        if erreurs:
            code = 1
    return code


if __name__ == "__main__":
    sys.exit(main())
