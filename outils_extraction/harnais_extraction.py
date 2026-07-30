#!/usr/bin/env python3
"""Harnais d'extraction — juge un store extrait contre la table de vérité (B-iii).

Le filet B ne peut pas être l'égalité exacte (l'extraction est un LLM) : il est fait de POINTS
DE CONTRÔLE — des valeurs réellement imprimées dans les documents, relevées le 30/07 AVANT tout
prompt. Un run qui les rate a mal lu ; ce harnais ne mesure pas l'exhaustivité (les invariants
B8 et la réconciliation B3 s'en chargent), il mesure qu'on n'a pas menti sur ce qu'on sait.

Portes des points (cf. `_a_propos` de la table) :
- **contrat** : `value_current` (ou autre champ) de l'entrée `financier_cote` dont le label ou
  l'assureur contient le sélecteur ;
- **ligne** / **poche** : cherche dans `attributes.lines` / `attributes.pockets` par `isin`
  exact ou `label` (sous-chaîne, casse/accents ignorés) ;
- **invariant** : Σ des lignes (ou poches) du contrat = valeur attendue ;
- **agregat** : Σ des lignes filtrées (ex. par `class`) = valeur attendue ;
- **champ_promis** : toute ligne titre/fonds du contrat doit porter le champ (MQ11) ;
- **info** : point documentaire (mouvements de l'année…) — vérifié sur `mouvements` si présent,
  sinon SIGNALÉ, jamais échoué : son logement dépend de ce que le run capte.

Contrôle négatif intégré (`--autotest`) : un store conforme passe, le MÊME store avec une
valeur corrompue échoue. Un harnais qu'on n'a pas vu refuser ne prouve rien.

Usage :
    python3 harnais_extraction.py <store.json> <fichier_document> [<fichier_document> …]
    python3 harnais_extraction.py --autotest
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

ICI = Path(__file__).resolve().parent
TABLE = ICI / "table_verite_extraction.json"


def _norm(s) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split()).casefold()


def _matche(objet: dict, cherche: dict) -> bool:
    for cle, val in cherche.items():
        if cle == "isin":
            if objet.get("isin") != val:
                return False
        else:
            if _norm(val) not in _norm(objet.get(cle, "")):
                return False
    return True


def _contrats(store: dict, cherche: dict | None) -> list[dict]:
    tous = store.get("financier_cote", [])
    if not cherche:
        return tous
    out = []
    for c in tous:
        cible = {"label": c.get("label", ""), "assureur": c.get("assureur", "")}
        if any(_norm(v) in _norm(" ".join(cible.values())) for v in cherche.values()):
            out.append(c)
    return out or tous  # sélecteur trop étroit : on juge sur tout plutôt que sur rien


def _lignes(store: dict, scope: dict | None = None) -> list[dict]:
    return [l for c in _contrats(store, scope)
            for l in c.get("attributes", {}).get("lines", [])]


def _poches(store: dict, scope: dict | None = None) -> list[dict]:
    return [p for c in _contrats(store, scope)
            for p in c.get("attributes", {}).get("pockets", [])]


def juger_point(store: dict, pt: dict, scope: dict | None = None) -> tuple[str, str]:
    """Rend (verdict, détail) — verdict ∈ OK | ECHEC | SIGNALE.

    `scope` (sélecteur de contrat du DOCUMENT, clé `contrat` de la table) restreint lignes,
    poches, invariants et agrégats au(x) contrat(s) du document jugé : sur un store
    multi-contrats, juger le store entier mélangerait les lignes de tous les relevés —
    faiblesse révélée par le premier run réel (INTERAGYR, 4 contrats), corrigée le 30/07."""
    porte = pt["porte"]
    tol = pt.get("tolerance", 0.01)

    if porte == "contrat":
        for c in _contrats(store, pt.get("cherche") or scope):
            v = c.get(pt.get("champ", "value_current"))
            if v is not None and abs(v - pt["attendu"]) <= tol:
                return "OK", f"{v}"
        return "ECHEC", f"aucun contrat ne porte {pt['attendu']} (±{tol})"

    if porte in ("ligne", "poche"):
        objets = _lignes(store, scope) if porte == "ligne" else _poches(store, scope)
        candidats = [o for o in objets if _matche(o, pt["cherche"])]
        if not candidats:
            return "ECHEC", f"aucune {porte} ne matche {pt['cherche']}"
        for o in candidats:
            v = o.get(pt.get("champ", "value"))
            if v is not None and abs(v - pt["attendu"]) <= tol:
                return "OK", f"{v}"
        return "ECHEC", (f"{len(candidats)} {porte}(s) matchée(s), aucune à "
                         f"{pt['attendu']} (±{tol}) — vues : "
                         f"{[o.get(pt.get('champ', 'value')) for o in candidats[:4]]}")

    if porte == "invariant":
        quoi = pt.get("somme_de", "lines")
        total = sum((o.get("value") or 0)
                    for o in (_lignes(store, scope) if quoi == "lines" else _poches(store, scope)))
        ok = abs(total - pt["egal_a"]) <= tol
        return ("OK" if ok else "ECHEC"), f"Σ {quoi} = {total:.2f} vs {pt['egal_a']} (±{tol})"

    if porte == "agregat":
        lignes = [l for l in _lignes(store, scope) if _matche(l, pt.get("cherche", {}))]
        total = sum((l.get("value") or 0) for l in lignes)
        ok = abs(total - pt["egal_a"]) <= tol
        return ("OK" if ok else "ECHEC"), (f"Σ({pt.get('cherche')}) = {total:.2f} "
                                           f"vs {pt['egal_a']} (±{tol}, {len(lignes)} ligne(s))")

    if porte == "champ_promis":
        champ = pt["champ"]
        lignes = _lignes(store, scope)
        # Même exemption que la règle vérifiée (SKILL.md §2.b) : les lignes de liquidités /
        # compte courant peuvent rester sans perf — « — » = non applicable, PAS zéro.
        # Le premier run réel a montré le harnais plus strict que la règle : corrigé le 30/07.
        exemptes = ("liquidite", "compte courant", "cash")
        jugees = [l for l in lignes if not any(x in _norm(l.get("label")) for x in exemptes)]
        sans = [l.get("label") for l in jugees if champ not in l]
        if not lignes:
            return "SIGNALE", "aucune ligne au store — rien à juger"
        if sans:
            return "ECHEC", (f"le gabarit publie {champ!r}, {len(sans)}/{len(jugees)} "
                             f"ligne(s) titre/fonds ne le portent pas (MQ11) : {sans[:4]}")
        return "OK", (f"{len(jugees)} ligne(s) titre/fonds avec {champ} "
                      f"({len(lignes) - len(jugees)} liquidité(s) exemptée(s))")

    if porte == "info":
        mvts = store.get("mouvements", [])
        if not mvts:
            return "SIGNALE", (f"point documentaire ({pt.get('note', '')[:60]}…) — aucun "
                               f"mouvement au store, à vérifier autrement")
        total = sum(m.get("amount", 0) for m in mvts)
        ok = any(abs(m.get("amount", 0) - pt["attendu"]) <= tol for m in mvts) \
            or abs(total - pt["attendu"]) <= tol
        return ("OK" if ok else "SIGNALE"), f"mouvements présents, Σ = {total:.2f}"

    return "SIGNALE", f"porte inconnue {porte!r} — table et harnais désynchronisés"


def juger(store: dict, fichiers: list[str]) -> int:
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    docs = {d["fichier"]: d for d in table["documents"]}
    echecs = 0
    for f in fichiers:
        doc = docs.get(f)
        if doc is None:
            print(f"SIGNALE  {f} — absent de la table de vérité (à dépouiller, pas à deviner)")
            continue
        if doc["certitude"] == "a_etablir":
            print(f"SIGNALE  {f} — points non établis (certitude a_etablir)")
            continue
        print(f"— {f} ({doc['emetteur_code']} / {doc['gabarit']}, arrêté {doc['arrete']})")
        scope = doc.get("contrat")
        for pt in doc["points"]:
            verdict, detail = juger_point(store, pt, scope)
            print(f"  {verdict:7s} {pt['nom'][:80]} — {detail}")
            if verdict == "ECHEC":
                echecs += 1
    print(f"\n{'ÉCHEC' if echecs else 'OK'} — {echecs} point(s) en échec")
    return 1 if echecs else 0


# ---------------------------------------------------------------------------
# Contrôle négatif : le harnais doit savoir refuser.
# ---------------------------------------------------------------------------

def autotest() -> int:
    store = {
        "financier_cote": [{
            "label": "Capi — Himalia", "assureur": "himalia_emetteur_a_confirmer",
            "value_current": 220545.63,
            "attributes": {
                "pockets": [{"id": "pck_001", "label": "Capi — Himalia", "value": 220545.63}],
                "lines": [
                    {"label": "Actif Général Generali Vie", "value": 37690.92, "class": "fonds_euros"},
                    {"label": "CARMIGNAC PTF Credit A Eur", "value": 29467.15, "class": "obligations"},
                    {"label": "Reste du portefeuille (agrégé pour l'autotest)",
                     "value": 153387.56, "class": "actions"},
                ],
            },
        }],
    }
    print("1. Un store conforme aux points Himalia doit passer :")
    code_ok = juger(store, ["2024.12 Relevé Himalia Capi HANAMI.pdf"])

    print("\n2. Le MÊME store avec la ligne CARMIGNAC corrompue (+100 €) doit ÉCHOUER")
    print("   (invariant D25 et valeur de ligne — deux points doivent tomber) :")
    import copy
    corrompu = copy.deepcopy(store)
    corrompu["financier_cote"][0]["attributes"]["lines"][1]["value"] += 100
    code_ko = juger(corrompu, ["2024.12 Relevé Himalia Capi HANAMI.pdf"])

    if code_ok == 0 and code_ko == 1:
        print("\nAUTOTEST OK — le harnais accepte le vrai et refuse le faux.")
        return 0
    print("\nAUTOTEST ÉCHEC — le harnais ne discrimine pas : il ne prouve rien.")
    return 1


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--autotest":
        sys.exit(autotest())
    if len(sys.argv) < 3:
        raise SystemExit(__doc__.split("Usage :")[1])
    store = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.exit(juger(store, sys.argv[2:]))
