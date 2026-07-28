#!/usr/bin/env python3
"""Migre un run de référence (manifeste + forme-store) vers l'état courant du fork.

Deux migrations indépendantes, toutes deux idempotentes :

**Manifeste — retrait des clés `blocs_enabled` obsolètes.** En session 1 le bloc *Rendement annuel* a
été renommé (D31) puis **retiré** : son tableau synthétique a été relocalisé sous le tableau Historique,
et `BLOCK_ORDER` est passé de neuf à huit blocs. `blocs_enabled` est `additionalProperties: false`, donc
un manifeste antérieur portant `historique` — ou `rendement_annuel`, l'état intermédiaire — **échoue à la
validation avant même que le classeur soit ouvert**. Ce n'est pas un renommage à faire : la clé n'a plus
de destination. On la retire, en journalisant sa valeur pour que le retrait ne soit pas muet.

**Forme-store — matérialisation de la poche unique (A5).** Le schéma exige désormais
`attributes.pockets` non vide sur tout contrat financier coté : le tableau de rendu a une ligne par
poche, donc un contrat sans poche réelle en déclare une qui le décrit lui-même. Cette migration la
fabrique à partir du contrat, ce qui donne au lecteur un chemin de code unique.

Sur les contrats qui ont déjà des poches, la migration **complète** ce qui est dérivable sans rien
inventer : `custodian`, `invest_date`, `pledged` propagés du contrat (attributs du contenant, vrais de
chacune de ses poches). Elle ne touche PAS `capital_invested` ni `value_jan1` — ceux-là sont **propres à
chaque poche** et les répartir au prorata serait fabriquer une donnée. Ils restent absents, donc la perf
YTD par poche reste non calculable pour ces contrats : c'est le manque, il doit rester visible.

Usage :
    python3 migrer_reference.py --verifier   <manifeste.json> [store.json]   # dit ce qui changerait
    python3 migrer_reference.py <manifeste.json> [store.json]                # écrit, .bak à côté
"""
import json
import shutil
import sys
from pathlib import Path

# Clés de `blocs_enabled` qui ont existé et n'ont plus de destination.
BLOCS_OBSOLETES = ("historique", "rendement_annuel")

# Attributs du CONTRAT qui sont vrais de chacune de ses poches : un dépositaire, une date d'ouverture
# et un nantissement portent sur le contenant. Volontairement PAS `capital_invested` ni `value_jan1`,
# qui sont propres à chaque poche et qu'aucune règle ne permet de répartir.
PROPAGEABLES = (("custodian", "custodian"), ("invest_date", "invest_date"), ("pledged", "pledged"))


def charger(chemin: Path):
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def migrer_manifeste(man: dict) -> tuple[list[str], list[str]]:
    """Retire les clés `blocs_enabled` obsolètes.

    Retourne (changements, remarques). La distinction n'est pas cosmétique : seules les
    **changements** justifient de réécrire le fichier. Les confondre rendait la migration
    non idempotente — une seconde passe annonçait du travail alors qu'elle n'en avait plus.
    """
    changements: list[str] = []
    be = man.get("blocs_enabled")
    if not isinstance(be, dict):
        return changements, []
    for cle in BLOCS_OBSOLETES:
        if cle in be:
            valeur = be.pop(cle)
            changements.append(
                f"blocs_enabled.{cle} retiré (valait {valeur!r}) — le bloc a été retiré du moteur en "
                f"session 1 (D31) ; la clé n'a plus de destination")
    return changements, []


def migrer_store(store: dict) -> tuple[list[str], list[str]]:
    """Matérialise la poche unique et propage les attributs de contenant.

    Retourne (changements, remarques) — cf. ``migrer_manifeste``. Les manques signalés sont des
    **remarques** : ils doivent rester visibles à chaque passage, sans jamais déclencher d'écriture.
    """
    changements: list[str] = []
    remarques: list[str] = []
    for entree in store.get("financier_cote", []) or []:
        eid = entree.get("id", "?")
        attrs = entree.setdefault("attributes", {})
        poches = attrs.get("pockets")

        if not poches:
            # Poche unique décrivant le contrat. `label` reprend celui du contrat : c'est bien la même
            # chose, et le lecteur affichera donc exactement ce qu'il affichait avant.
            poche = {"label": entree["label"], "value": entree["value_current"]}
            for src, dst in (("manager", "manager"), ("custodian", "custodian"),
                            ("risk_profile", "profile"), ("capital_invested", "capital_invested"),
                            ("value_jan1", "value_jan1"), ("invest_date", "invest_date"),
                            ("pledged", "pledged")):
                if src in entree:
                    poche[dst] = entree[src]
            attrs["pockets"] = [poche]
            changements.append(f"{eid} : poche unique matérialisée depuis le contrat "
                               f"({len(poche)} champs, value={poche['value']})")
            continue

        # Contrat déjà multi-poches : on ne complète que ce qui est vrai par contenance.
        ajouts = []
        for poche in poches:
            for src, dst in PROPAGEABLES:
                if src in entree and dst not in poche:
                    poche[dst] = entree[src]
                    ajouts.append(dst)
        if ajouts:
            changements.append(f"{eid} : {len(poches)} poches — propagé depuis le contrat "
                               f"{sorted(set(ajouts))}")
        manquants = [c for c in ("capital_invested", "value_jan1")
                     if any(c not in p for p in poches)]
        if manquants:
            remarques.append(f"{eid} : {manquants} absents des poches — propres à chacune, les "
                             f"répartir serait fabriquer une donnée. Perf YTD par poche non calculable.")
    return changements, remarques


def valider(store: dict) -> list[str]:
    """Valide le store contre le schéma du fork, si jsonschema est disponible."""
    schema_path = Path(__file__).resolve().parent / "skill" / "pipeline" / "store_client.schema.json"
    if not schema_path.exists():
        return [f"schéma introuvable ({schema_path}) — validation sautée"]
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["jsonschema absent — validation sautée (pip install -U jsonschema)"]
    schema = charger(schema_path)
    v = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    return [f"{list(e.path)}: {e.message}" for e in sorted(v.iter_errors(store),
                                                          key=lambda e: list(e.path))]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verifier = "--verifier" in sys.argv
    if not args:
        print(__doc__)
        return 2

    chemins = [Path(a) for a in args]
    for c in chemins:
        if not c.exists():
            sys.exit(f"Introuvable : {c}")

    total = 0
    for chemin in chemins:
        doc = charger(chemin)
        est_store = "schema_version" in doc and "financier_cote" in doc
        changements, remarques = migrer_store(doc) if est_store else migrer_manifeste(doc)

        print(f"\n── {chemin.name} ({'forme-store' if est_store else 'manifeste'}) ──")
        if not changements:
            print("  rien à migrer (déjà à jour)")
        for n in changements:
            print(f"  · {n}")
        for n in remarques:
            print(f"  ⚠ {n}")
        total += len(changements)

        if est_store:
            erreurs = valider(doc)
            print(f"  validation : {'OK — 0 erreur' if not erreurs else str(len(erreurs)) + ' erreur(s)'}")
            for e in erreurs[:10]:
                print(f"      {e}")

        if changements and not verifier:
            sauvegarde = chemin.with_suffix(chemin.suffix + ".bak")
            if not sauvegarde.exists():
                shutil.copy2(chemin, sauvegarde)
                print(f"  sauvegarde : {sauvegarde.name}")
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print("  écrit")

    if verifier and total:
        print(f"\n{total} changement(s) à appliquer — relancer sans --verifier.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
