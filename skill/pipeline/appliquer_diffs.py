"""Apply — consolidation des diffs validés en forme-store 2.1 (B-ii).

Jusqu'ici l'apply était un GESTE d'agent (« consolider via store_builder », SKILL.md §2.d) ; le
voici outil déterministe, testable, avec les quatre responsabilités que les chantiers clos lui
ont données (roadmap B §3.1) :

**(a) Provenance D49.** Chaque entrée touchée reçoit `source_document` (du diff) et, si le
contexte du run les fournit, `source_empreinte`/`source_gabarit`/`source_arrete`. C'est ce qui
rend chaque ligne du store auditable, et ce qui évitera au self-healing de crier au drift sur
une archive. En cas d'updates successifs par plusieurs documents, la provenance d'ENTRÉE porte
le dernier — le grain champ-par-champ est le travail de l'audit du datahub, pas du run.

**(b) `pocket.id` déterministe (C7/D16).** Les poches sans id reçoivent `pck_NNN` (séquence
globale du store, ordre du document) ; les `lines[].pocket` qui référencent un LIBELLÉ sont
résolus vers l'id. La jointure par texte meurt ici, à l'entrée.

**(c) Résolution acteurs (K3).** `assureur` est résolu vers le code du référentiel par les
alias (casse/accents ignorés). Non résolu → le VERBATIM reste (jamais de code inventé) et le
rapport le signale : c'est à l'agent d'émettre la proposition K3, pas à l'apply d'écrire dans
un référentiel.

**(d) Contrôle MQ11 piloté par `champs_publies`.** Si le gabarit du document publie la perf par
ligne, toute ligne créée sans `perf_pct` est signalée — le défaut « logement déclaré jamais
rempli » cesse d'être silencieux.

Et une règle de conduite, héritée de D4 plateforme : **jamais de last-write-wins**. Un `update`
dont `old_value` ne correspond pas à la valeur courante du store est un CONFLIT : le champ n'est
PAS appliqué, le rapport le porte, la réconciliation (B3) tranche avec le CGP.

Usage :
    python3 appliquer_diffs.py base.json sortie.json diff1.json [diff2 …]
        [--arrete AAAA-MM-JJ] [--referentiels referentiels.json]
        [--documents contexte_docs.json] [--rapport rapport.json]

`--documents` : {source_document: {"empreinte": sha256?, "gabarit": code?, "valide_depuis": ?}}
— produit par l'étape d'identification (§2.b étape 2). Absent → provenance partielle (ABSENCE
≠ NULL, on ne fabrique rien).
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import store_builder  # noqa: E402
import referentiels as R  # noqa: E402
from valider_diff import SYNONYMES_LIGNE, valider  # noqa: E402

CATEGORIES = ("liquidites", "immobilier", "financier_cote", "non_cote",
              "dettes", "exotiques", "historique_annuel", "mouvements")

# ---------------------------------------------------------------------------
# (e) Enrichissement par le référentiel ISIN — la « priorité absolue » devient mécanique.
# La règle du SKILL.md (« priorité absolue pour classe/géographie/SRI dès que l'ISIN y
# figure ») était une consigne de prompt : depuis le 30/07 l'apply l'APPLIQUE — un subagent
# qui classe autrement est corrigé, un champ manquant est complété, et le rapport compte.
# État de la donnée : class_code et geo_code sont peuplés (261) ; `sri` est VIDE sur toute la
# colonne — l'enrichissement SRI ne produira rien tant que le référentiel n'est pas rempli
# (chantier de donnée constaté le 30/07, pas un défaut de ce code).
# ---------------------------------------------------------------------------

_REF_ISIN_CACHE: dict | None = None


def _ref_isin() -> dict:
    global _REF_ISIN_CACHE
    if _REF_ISIN_CACHE is None:
        import csv
        chemin = Path(__file__).resolve().parents[1] / "assets" / "isin_referentiel_v0.csv"
        _REF_ISIN_CACHE = {}
        if chemin.exists():
            for r in csv.DictReader(open(chemin, encoding="utf-8")):
                _REF_ISIN_CACHE[r["isin"]] = r
    return _REF_ISIN_CACHE


# ---------------------------------------------------------------------------
# Chemins pointés
# ---------------------------------------------------------------------------

def _poser(entree: dict, chemin: str, valeur) -> None:
    parts = chemin.split(".")
    d = entree
    for p in parts[:-1]:
        d = d.setdefault(p, {})
        if not isinstance(d, dict):
            raise ValueError(f"chemin {chemin!r} : {p!r} n'est pas un objet")
    d[parts[-1]] = valeur


def _lire(entree: dict, chemin: str):
    d = entree
    for p in chemin.split("."):
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def _normaliser_lignes(lignes: list) -> list:
    """Variantes connues → noms canoniques du $defs.line (cf. valider_diff)."""
    out = []
    for l in lignes:
        out.append({SYNONYMES_LIGNE.get(k, k): v for k, v in l.items()})
    return out


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

class Rapport:
    def __init__(self):
        self.appliques: list[str] = []
        self.conflits: list[dict] = []
        self.avertissements: list[str] = []
        self.acteurs_non_resolus: list[str] = []
        self.erreurs: list[str] = []

    def dict(self) -> dict:
        return {"appliques": self.appliques, "conflits": self.conflits,
                "avertissements": self.avertissements,
                "acteurs_non_resolus": sorted(set(self.acteurs_non_resolus)),
                "erreurs": self.erreurs}

    def resume(self) -> str:
        return (f"{len(self.appliques)} changement(s) appliqué(s) · "
                f"{len(self.conflits)} conflit(s) (réconciliation B3) · "
                f"{len(set(self.acteurs_non_resolus))} acteur(s) non résolu(s) · "
                f"{len(self.avertissements)} avertissement(s)")


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def _prochain_pck(store: dict) -> int:
    n = 0
    for c in store.get("financier_cote", []):
        for p in c.get("attributes", {}).get("pockets", []):
            pid = str(p.get("id", ""))
            if pid.startswith("pck_"):
                try:
                    n = max(n, int(pid[4:]))
                except ValueError:
                    pass
    return n


def _trouver(store: dict, categorie: str, entry_id: str):
    for e in store.get(categorie, []):
        if e.get("id") == entry_id:
            return e
    return None


def appliquer(store: dict, diffs: list[dict], contexte: dict | None = None,
              refs: "R.Referentiels | None" = None) -> tuple[dict, Rapport]:
    """Applique des diffs VALIDÉS à une copie du store. Rend (store', rapport)."""
    contexte = contexte or {}
    docs = contexte.get("documents", {})
    store = copy.deepcopy(store)
    rapport = Rapport()
    pck = [_prochain_pck(store)]

    gabarits_par_cle = {}
    if refs is not None:
        for g in refs.gabarits:
            gabarits_par_cle[(g.get("emetteur_code"), g.get("gabarit"))] = g

    for diff in diffs:
        src = diff["source_document"]
        erreurs, avert = valider(diff, src)
        rapport.avertissements += avert
        if erreurs:
            rapport.erreurs += erreurs
            continue  # un diff invalide ne s'applique pas, les autres oui

        meta_doc = docs.get(src, {})
        provenance = {k: v for k, v in {
            "source_document": src,
            "source_empreinte": meta_doc.get("empreinte"),
            "source_gabarit": meta_doc.get("gabarit"),
            "source_arrete": meta_doc.get("arrete") or contexte.get("date_arrete"),
        }.items() if v is not None}

        # champs_publies du gabarit de CE document (contrôle MQ11)
        publie_perf = False
        g = gabarits_par_cle.get((meta_doc.get("emetteur"), meta_doc.get("gabarit")))
        if g is None and meta_doc.get("gabarit") and refs is not None:
            g = next((x for x in refs.gabarits if x.get("gabarit") == meta_doc["gabarit"]), None)
        if g is not None:
            publie_perf = (g.get("champs_publies", {}).get("perf_par_ligne") == "oui")

        refs_intra_lot: dict[str, str] = {}  # entry_id provisoire du diff -> id réel du store

        for i, ch in enumerate(diff.get("changes", [])):
            ou = f"{src}:changes[{i}] ({ch.get('entry_label', '?')})"
            cat = ch["category"]

            # ------------------------------------------------ création ------
            if ch["action"] == "create":
                entree: dict = {"entity_id": ch.get("entity_id"),
                                "label": ch["entry_label"], "source": "extraction"}
                for f in ch["fields"]:
                    nv = f["new_value"]
                    if f["path"] == "attributes.lines" and isinstance(nv, list):
                        nv = _normaliser_lignes(nv)
                    _poser(entree, f["path"], nv)
                entree.update(provenance)

                if cat == "financier_cote":
                    _preparer_financier_cote(entree, pck, refs, rapport, ou)
                    if publie_perf:
                        sans_perf = [l.get("label") for l in
                                     entree.get("attributes", {}).get("lines", [])
                                     if "perf_pct" not in l]
                        if sans_perf:
                            rapport.avertissements.append(
                                f"{ou}: le gabarit publie la perf par ligne (champs_publies), "
                                f"{len(sans_perf)} ligne(s) créée(s) sans perf_pct (MQ11) : "
                                f"{sans_perf[:4]}")
                nid = store_builder.add_entry(store, cat, entree)
                if ch.get("entry_id"):
                    refs_intra_lot[ch["entry_id"]] = nid
                rapport.appliques.append(f"{ou}: créé {nid}")
                continue

            # ------------------------------------------------ mise à jour ---
            cible_id = refs_intra_lot.get(ch["entry_id"], ch["entry_id"])
            entree = _trouver(store, cat, cible_id)
            if entree is None:
                rapport.erreurs.append(f"{ou}: entry_id {cible_id!r} introuvable dans "
                                       f"{cat} — rien n'est appliqué pour ce changement.")
                continue
            champs_ok = 0
            for f in ch["fields"]:
                courant = _lire(entree, f["path"])
                old = f.get("old_value")
                if old is not None and courant is not None and courant != old:
                    rapport.conflits.append({
                        "ou": ou, "path": f["path"], "store": courant,
                        "old_value_diff": old, "new_value_diff": f["new_value"],
                        "regle": "jamais de last-write-wins (D4) : le champ n'est PAS "
                                 "appliqué, la réconciliation (B3) tranche avec le CGP."})
                    continue
                nv = f["new_value"]
                if f["path"] == "attributes.lines" and isinstance(nv, list):
                    nv = _normaliser_lignes(nv)
                _poser(entree, f["path"], nv)
                champs_ok += 1
            if champs_ok:
                entree.update(provenance)
                if cat == "financier_cote":
                    _preparer_financier_cote(entree, pck, refs, rapport, ou)
                rapport.appliques.append(f"{ou}: {champs_ok} champ(s) mis à jour sur {cible_id}")

    # nettoyage + validation finale : un store qui ne valide pas ne SORT pas.
    store = store_builder._clean(store)
    erreurs = store_builder.validate_all(store)
    refs_err = store_builder.check_refs(store)
    rapport.erreurs += erreurs + refs_err
    return store, rapport


def _preparer_financier_cote(entree: dict, pck: list, refs, rapport: Rapport, ou: str) -> None:
    """(b) pocket.id + jointure lignes, (c) résolution acteur, invariant A5."""
    attrs = entree.setdefault("attributes", {})

    # A5 : toujours au moins une poche — la poche 0 décrit le contrat lui-même.
    poches = attrs.setdefault("pockets", [])
    if not poches:
        poches.append({"label": entree["label"],
                       "value": entree.get("value_current", 0.0)})

    for p in poches:
        if not p.get("id"):
            pck[0] += 1
            p["id"] = f"pck_{pck[0]:03d}"

    # lignes : libellé de poche -> id (C7 — la jointure par texte meurt à l'entrée)
    label_vers_id = {p["label"]: p["id"] for p in poches}
    for l in attrs.get("lines", []):
        ref = l.get("pocket")
        if ref and ref not in {p["id"] for p in poches}:
            if ref in label_vers_id:
                l["pocket"] = label_vers_id[ref]
            else:
                rapport.erreurs.append(f"{ou}: lines[].pocket {ref!r} ne résout ni vers un id "
                                       f"ni vers un libellé de poche du contrat.")

    # (c) assureur -> code acteur par alias ; non résolu = verbatim + signalement (K3)
    assureur = entree.get("assureur")
    if assureur and refs is not None:
        act = refs.acteur(assureur)
        if act is not None:
            entree["assureur"] = act["code"]
        else:
            rapport.acteurs_non_resolus.append(assureur)

    # (e) référentiel ISIN — priorité absolue sur class/geography/sri des lignes
    ref = _ref_isin()
    corriges = completes = 0
    for l in attrs.get("lines", []):
        r = ref.get(l.get("isin"))
        if not r:
            continue
        for cle_ligne, cle_ref in (("class", "class_code"), ("geography", "geo_code"),
                                   ("sri", "sri")):
            v = (r.get(cle_ref) or "").strip()
            if not v:
                continue
            if cle_ligne == "sri":
                try:
                    v = int(v)
                except ValueError:
                    continue
            if cle_ligne not in l:
                l[cle_ligne] = v
                completes += 1
            elif l[cle_ligne] != v:
                l[cle_ligne] = v
                corriges += 1
    if corriges or completes:
        rapport.avertissements.append(
            f"{ou}: référentiel ISIN appliqué — {completes} champ(s) complété(s), "
            f"{corriges} corrigé(s) (priorité absolue, SKILL.md §2.b)")


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Applique des diffs validés à un forme-store 2.1")
    ap.add_argument("base")
    ap.add_argument("sortie")
    ap.add_argument("diffs", nargs="+")
    ap.add_argument("--arrete")
    ap.add_argument("--referentiels")
    ap.add_argument("--documents", help="JSON {source_document: {empreinte, gabarit, arrete}}")
    ap.add_argument("--rapport")
    a = ap.parse_args()

    store = json.loads(Path(a.base).read_text(encoding="utf-8"))
    diffs = [json.loads(Path(d).read_text(encoding="utf-8")) for d in a.diffs]
    contexte = {"date_arrete": a.arrete}
    if a.documents:
        contexte["documents"] = json.loads(Path(a.documents).read_text(encoding="utf-8"))
    refs = R.charger(Path(a.referentiels)) if a.referentiels else R.charger(R.SNAPSHOT_VENDORE)

    store2, rapport = appliquer(store, diffs, contexte, refs)

    print(rapport.resume())
    for c in rapport.conflits:
        print(f"  CONFLIT {c['ou']} {c['path']}: store={c['store']!r} vs "
              f"old_value={c['old_value_diff']!r}")
    for x in sorted(set(rapport.acteurs_non_resolus)):
        print(f"  ACTEUR NON RÉSOLU {x!r} — verbatim conservé, proposition K3 à émettre")
    for e in rapport.erreurs:
        print(f"  ERREUR {e}")

    if a.rapport:
        Path(a.rapport).write_text(json.dumps(rapport.dict(), ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    if rapport.erreurs:
        print("ÉCHEC — le store de sortie n'est PAS écrit (il ne valide pas, ou des diffs "
              "sont invalides).")
        return 1
    Path(a.sortie).write_text(json.dumps(store2, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    print(f"OK → {a.sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
