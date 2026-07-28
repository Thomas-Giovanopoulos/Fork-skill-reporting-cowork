# -*- coding: utf-8 -*-
"""Projection des colonnes par en-têtes (schéma source v3 « spec Thomas »).

Les moteurs lisent les onglets par INDICES canoniques. Ce module détecte les
en-têtes (ligne 3) et reprojette chaque ligne de données vers l'ordre canonique,
quels que soient l'ordre et les libellés réels des colonnes. Si aucun en-tête
n'est reconnu, la ligne est renvoyée telle quelle (repli legacy par indices).

Les colonnes de perf (« Perf € », « Perf % », « Perf annualisée ») sont
IGNORÉES : elles sont calculées (Excel côté saisie, moteur côté rendu).
"""
import unicodedata

def _n(x):
    t = unicodedata.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode()
    return " ".join(t.split()).casefold()

# (mot(s)-clé(s) à trouver, indice canonique) — premier match gagne, dans l'ordre.
FIN_COTE = [
    (("valeur projetee",), 20),
    (("valeur 01/01", "valeur 0101", "valeur au 01"), 11),
    (("valeur au", "valeur du", "valeur ("), 12),
    (("nombre de poches", "nb poches"), 21),
    (("type poche",), 3),
    (("poche",), 16),                              # « Poche (libellé) »
    (("nature",), 0),                              # nature du placement / du contrat ; APRÈS « nature de la gestion » (voir mode)
    (("assureur", "banque"), 1),
    (("intermediaire",), 2),
    (("societe de gestion", "gerant"), 4),
    (("depositaire",), 5),
    (("classe",), 13),                             # classe dominante / classe rhetores / categorie
    (("categorie", "cathegorie"), 13),
    (("geographie",), 14),
    (("sri",), 15),
    (("mode de gestion", "nature de la gestion"), 6),
    (("profil",), 7),
    (("date d'investissement", "date dinvestissement", "date d'invest"), 8),
    (("nantissement",), 9),
    (("nominal", "capital investi"), 10),
    (("versement",), 17),
    (("retrait", "rachat"), 18),
    (("frais",), 19),
]
NON_COTE = [
    (("type (fonds", "type fonds/titre", "type\n(fonds"), 15),
    (("nom du fonds", "vehicule", "véhicule"), 0),
    (("gestionnaire", "gerant"), 1),
    (("strategie",), 2),
    (("cible moic", "multiple cible", "cible"), 3),
    (("engage",), 4),
    (("non appele reel", "non appelé réel"), 6),
    (("non appele estime",), 7),
    (("appele",), 5),
    (("moic realise", "moic"), 8),
    (("valeur liquidative", "valeur au", "vl"), 9),
    (("classe",), 10),
    (("tri",), 11),
    (("segment",), 12),
    (("duree",), 13),
    (("date d'investissement", "date dinvest"), 14),
]
LIGNES = [
    (("contrat",), 0), (("libelle",), 1), (("isin",), 2),
    (("valeur",), 3), (("perf",), 4), (("poche",), 5),
    (("classe",), 6), (("geographie",), 7), (("sri",), 8),
]
MOUVEMENTS = [
    (("date",), 0), (("contrat",), 1), (("type",), 2),
    (("montant",), 3), (("commentaire", "libelle"), 4),
]
NCANON = {"Fin coté": 22, "Non coté": 16, "Lignes": 9, "Mouvements": 5}
MAPS   = {"Fin coté": FIN_COTE, "Non coté": NON_COTE, "Lignes": LIGNES, "Mouvements": MOUVEMENTS}
# ordre spécial : « nature de la gestion » doit matcher AVANT « nature »
_PRIORITY = {"Fin coté": [(("nature de la gestion", "mode de gestion"), 6)]}

def build_mapping(header_row, sheet_kind):
    """header_row -> dict {canonical_index: actual_index} ou None si en-têtes legacy/inconnus."""
    rules = MAPS.get(sheet_kind)
    if not rules: return None
    pri = _PRIORITY.get(sheet_kind, [])
    mapping, used = {}, set()
    hdrs = [_n(h) for h in header_row]
    for j, h in enumerate(hdrs):
        if not h: continue
        if sheet_kind == "Fin coté" and ("perf" in h or h.startswith("cle contrat")): continue
        hit = None
        for keys, ci in list(pri) + list(rules):
            if ci in used: continue
            if any(k in h for k in keys): hit = ci; break
        if hit is not None:
            mapping[hit] = j; used.add(hit)
    # sanité : il faut au moins les colonnes vitales pour accepter le mapping
    vital = {"Fin coté": (1, 12), "Non coté": (0, 4), "Lignes": (0, 3), "Mouvements": (0, 3)}[sheet_kind]
    if not all(v in mapping for v in vital): return None
    # mapping identique à l'identité -> inutile
    if all(mapping.get(i) == i for i in mapping) and len(mapping) >= len([h for h in hdrs if h]):
        return None
    return mapping

def project(row, mapping, sheet_kind):
    out = [None] * NCANON[sheet_kind]
    for ci, j in mapping.items():
        if j < len(row): out[ci] = row[j]
    return out
