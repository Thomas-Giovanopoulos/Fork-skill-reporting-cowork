# -*- coding: utf-8 -*-
"""Lecteur de forme-store — L2, la colonne vertébrale (D20).

Présente un store client 2.1-skill sous l'INTERFACE CLASSEUR que `p2_fill` consomme déjà :
`sheetnames`, `wb[nom].iter_rows(min_row=4, values_only=True)`, et une ligne 3 d'en-têtes vide
(le repli « indices canoniques » de `read_sheet` s'applique alors — les lignes émises ICI SONT
l'ordre canonique, il n'y a rien à reprojeter). **Le moteur ne change pas** : la substitution
tient en un point de chargement dans `main()`.

Trois règles de conduite, chacune héritée d'un constat :

**1 — Échec bruyant sur tout manque (L5).** Un code d'enveloppe inconnu, une poche introuvable
pour une ligne, un type de flux hors vocabulaire : erreur fatale avec le chemin exact. Jamais de
défaut silencieux — un manque comblé par un défaut est un manque qu'on ne corrigera jamais.

**2 — Le store porte la donnée, le lecteur porte l'AFFICHAGE.** C'est ici que vivent les tables
de normalisation (A2) : codes de classe → libellés (`actions` → « Actions »), codes d'enveloppe →
natures (`av_lu` → « AV »), booléens → « Oui »/« — », dates ISO → jj/mm/aaaa, MOIC nombre →
« 2,2x » (A3). Le moteur affiche des cellules verbatim ; le lecteur reconstruit ces verbatims
depuis la donnée typée.

**3 — Les entiers restent des entiers.** openpyxl rend `24000` (int) là où le JSON porte
`24000.0` : les colonnes affichées par `s()` verbatim divergeraient (« 24000.0 »). Toute valeur
numérique entière est ré-émise en int.

Ce que ce lecteur REFUSE encore (et le dit) : les produits structurés (`attributes.ps`) et les
séries Cours PS — leur forme au store est incomplète (pas de logement pour le nominal ni la
valeur si cassé, cf. confrontation §4/MQ5) et aucune fixture ne les exerce. Un store qui en
porte lève une erreur explicite plutôt qu'un rendu amputé.
"""
from __future__ import annotations

import json
import re

# ---------------------------------------------------------------------------
# Tables de normalisation (A2) — le lecteur est leur position canonique.
# ---------------------------------------------------------------------------

CLASSE_VERS_LIBELLE = {
    "actions": "Actions",
    "obligations": "Obligations",
    "produits_structures": "Produits structurés",
    "fonds_euros": "Fonds euros",
    "alternatifs": "Alternatifs",
    "matieres_premieres": "Matières premières",
    "crypto": "Crypto",
    "monetaire": "Monétaire",
    "private_equity": "Private Equity",
    "dette_privee": "Dette privée",
    "immo_non_cote": "Immo non coté",
    "infrastructures": "Infrastructures",
}

ENVELOPPE_VERS_NATURE = {
    "av_lu": "AV", "av_fr": "AV",
    "capi_lu": "Capi", "capi_fr": "Capi",
    "cto": "CTO", "pea": "PEA", "per": "PER",
}

TYPE_FLUX_VERS_LIBELLE = {
    "appel": "Appel", "distribution": "Distribution",
    "appel_prevu": "Appel prévu", "distribution_prevue": "Distribution prévue",
}

TYPE_MVT_VERS_LIBELLE = {"versement": "Versement", "retrait": "Retrait", "frais": "Frais"}

# Codes géo (référentiel/subagents) → libellés d'affichage du moteur (clés de GEO_COLORS).
# Un libellé déjà en clair (fixtures) passe tel quel — la table ne mappe que les codes.
GEO_VERS_LIBELLE = {
    "europe": "Europe développée",
    "amerique_du_nord": "Amérique du Nord",
    "asie_pacifique": "Asie-Pacifique",
    "emergents": "Émergents",
    "monde": "International / Monde",
}

_PREFIXE_CATEGORIE = {"liquidites": "Liq", "immobilier": "Immo",
                      "financier_cote": "Fin coté", "non_cote": "Non coté", "dettes": "Dettes"}


class ErreurLecteur(SystemExit):
    """Erreur fatale du lecteur — toujours avec le chemin de la donnée en cause."""
    def __init__(self, message: str):
        super().__init__(f"LECTEUR DE STORE — {message}")


# ---------------------------------------------------------------------------
# Reconstruction des verbatims
# ---------------------------------------------------------------------------

def _entier(v):
    """float entier → int : openpyxl rend des int, s() les affiche sans « .0 »."""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _jjmmaaaa(v):
    """ISO → jj/mm/aaaa ; tout autre texte (« Févr. 2024 ») est un verbatim, rendu tel quel."""
    if v is None:
        return None
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(v))
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else v


def _oui_tiret(v):
    if v is None:
        return None
    return "Oui" if v else "—"


def _moic(v):
    """Nombre → « 2,2x » / « 1,06x » (A3) : le classeur écrit le multiple en texte, virgule
    française, avec AUTANT de décimales que la valeur en porte (au moins une). Un `.1f` aveugle
    arrondissait 1,06x en 1,1x — attrapé par le premier smoke test L3a du 30/07 : le formatage
    doit préserver la valeur, jamais la résumer."""
    if v is None:
        return None
    t = f"{float(v):.4f}".rstrip("0")
    if t.endswith("."):
        t += "0"
    return t.replace(".", ",") + "x"


def _classe(v):
    """Code → libellé ; un verbatim déjà lisible (non mappé) passe tel quel."""
    if v is None:
        return None
    return CLASSE_VERS_LIBELLE.get(v, v)


def _geo(v):
    """Code géo → libellé moteur ; verbatim inchangé sinon."""
    if v is None:
        return None
    return GEO_VERS_LIBELLE.get(v, v)


def _nature(envelope_type: str, ou: str) -> str:
    n = ENVELOPPE_VERS_NATURE.get(envelope_type)
    if n is None:
        raise ErreurLecteur(f"code d'enveloppe inconnu {envelope_type!r} sur {ou} — la table "
                            f"ENVELOPPE_VERS_NATURE du lecteur ne sait pas l'afficher (A2).")
    return n


# ---------------------------------------------------------------------------
# Feuille — le strict nécessaire de l'interface openpyxl que p2_fill utilise
# ---------------------------------------------------------------------------

class _Feuille:
    def __init__(self, titre: str, lignes: list[tuple]):
        self.title = titre
        self._lignes = [tuple(l) for l in lignes]

    def __getitem__(self, idx):
        # ws[3] : ligne d'en-têtes pour colmap. Vide → build_mapping rend None →
        # repli « indices canoniques » de read_sheet, qui est exactement notre contrat.
        return []

    def iter_rows(self, min_row=4, values_only=True):
        yield from self._lignes


# ---------------------------------------------------------------------------
# Classeur-façade
# ---------------------------------------------------------------------------

class ClasseurStore:
    """Un store 2.1-skill présenté comme le classeur de transition — même interface, mêmes
    listes canoniques, mêmes verbatims d'affichage. Le suffixe d'onglet EST l'id d'entité."""

    def __init__(self, store: dict):
        v = store.get("schema_version")
        if v != "2.1-skill":
            raise ErreurLecteur(f"schema_version {v!r} — ce lecteur consomme le format convergé "
                                f"2.1-skill (D48). Un store 2.0 se migre, il ne se devine pas.")
        self._store = store
        self._feuilles: dict[str, _Feuille] = {}
        self._construire()

    @classmethod
    def depuis_fichier(cls, chemin: str) -> "ClasseurStore":
        with open(chemin, encoding="utf-8") as fh:
            return cls(json.load(fh))

    @property
    def sheetnames(self):
        return list(self._feuilles)

    def __getitem__(self, nom):
        return self._feuilles[nom]

    # -- construction -------------------------------------------------------

    def _poser(self, nom: str, lignes: list[tuple]):
        self._feuilles[nom] = _Feuille(nom, lignes)

    def _entrees(self, categorie: str, eid: str) -> list[dict]:
        return [e for e in self._store.get(categorie, []) if e.get("entity_id") == eid]

    def _construire(self):
        s = self._store
        entites = sorted(s["client"]["entities"], key=lambda e: e["order"])

        # Entités : (id, label, type, suffixe) — le suffixe est l'id lui-même.
        self._poser("Entités", [(e["id"], e["label"], e["type"], e["id"]) for e in entites])

        mouvements = s.get("mouvements", [])
        valuations = s.get("valuations", [])

        for e in entites:
            eid = e["id"]
            self._construire_liq(eid)
            self._construire_immo(eid)
            self._construire_fin_cote(eid)
            self._construire_lignes_et_mouvements(eid, mouvements)
            self._construire_non_cote(eid, mouvements, valuations)
            self._construire_dettes(eid)

        # Arbitrages : agrégat patrimonial au store, onglet de la première entité au classeur.
        if s.get("arbitrages"):
            self._poser(f"Arbitrages — {entites[0]['id']}",
                        [(_jjmmaaaa(a["date"]), a["label"]) for a in s["arbitrages"]])

        if s.get("courbe_performance"):
            self._poser("Valorisations",
                        [(_jjmmaaaa(p["date"]), _entier(p["cote"]), _entier(p.get("nc")))
                         for p in s["courbe_performance"]])

        if s.get("historique_annuel"):
            # Rendements stockés en FRACTION (convention 2.1) ; le classeur écrit des %.
            self._poser("Historique",
                        [(h["year"],
                          _entier(round(h["rendement"] * 100, 6)) if "rendement" in h else None,
                          _entier(round(h["rendement_nc"] * 100, 6)) if "rendement_nc" in h else None,
                          h.get("commentaire"))
                         for h in s["historique_annuel"]])

    def _construire_liq(self, eid):
        lignes = [(l["label"], l.get("custodian"), _entier(l.get("balance")))
                  for l in self._entrees("liquidites", eid)]
        if lignes:
            self._poser(f"Liq — {eid}", lignes)

    def _construire_immo(self, eid):
        lignes = []
        for i in self._entrees("immobilier", eid):
            attrs = i.get("attributes", {})
            lignes.append((i["label"], i.get("function"), i.get("ownership"),
                           _oui_tiret(i.get("mortgage")), _entier(attrs.get("loyer_annuel")),
                           attrs.get("date_acquisition"), _entier(i.get("value_acquisition")),
                           _entier(i.get("value_current"))))
        if lignes:
            self._poser(f"Immo — {eid}", lignes)

    def _construire_dettes(self, eid):
        lignes = []
        for d in self._entrees("dettes", eid):
            taux = d.get("taux")
            if taux is None and d.get("rate") is not None:
                taux = _entier(d["rate"])
            lignes.append((d["label"], d.get("bank"), d.get("type"),
                           _jjmmaaaa(d.get("date_souscription")), _entier(d.get("montant_initial")),
                           taux, _jjmmaaaa(d.get("maturity")), d.get("frequency"),
                           d.get("guarantee"), _entier(d.get("capital_remaining")),
                           d.get("adossement")))
        if lignes:
            self._poser(f"Dettes — {eid}", lignes)

    def _construire_fin_cote(self, eid):
        lignes, lignes_classees = [], []
        for c in self._entrees("financier_cote", eid):
            if c.get("attributes", {}).get("ps"):
                raise ErreurLecteur(
                    f"le contrat {c['label']!r} porte attributes.ps : la machinerie Produits "
                    f"structurés n'est pas encore lisible depuis le store (forme MQ5 incomplète "
                    f"— pas de logement pour le nominal ni la valeur si cassé). Refus explicite "
                    f"plutôt que rendu amputé.")
            # La nature VERBATIM prime : c'est le mot du client qui fait les clés de
            # jointure du rendu (bug du 30/07 : « Compte Titres » ≠ « CTO »).
            nature = c.get("nature") or _nature(c["envelope_type"], f"financier_cote/{c['id']}")
            poches = c["attributes"]["pockets"]
            if not poches:
                raise ErreurLecteur(f"contrat {c['id']} sans poche — l'invariant A5 garantit "
                                    f"au moins la poche 0 ; ce store est invalide.")
            poche_id_vers_label = {}
            for p in poches:
                poche_id_vers_label[p["id"]] = p["label"]
                libelle_poche = p["label"] if p["label"] != c["label"] else None
                lignes.append((
                    nature,                                   # 0 — clé de regroupement
                    c["assureur"],                            # 1
                    c.get("intermediaire"),                   # 2
                    p.get("type"),                            # 3
                    p.get("manager") or c.get("manager"),     # 4
                    p.get("custodian") or c.get("custodian"), # 5
                    c.get("management_mode"),                 # 6
                    p.get("profile") or c.get("risk_profile"),# 7
                    _jjmmaaaa(p.get("invest_date")),          # 8 — verbatim si non ISO
                    _oui_tiret(p.get("nantissement", c.get("nantissement"))),  # 9
                    _entier(p.get("capital_invested")),       # 10
                    _entier(p.get("value_jan1")),             # 11
                    _entier(p.get("value")),                  # 12
                    _classe(p.get("classe_rhetores")),        # 13
                    _geo(p.get("geography")),                 # 14
                    p.get("sri"),                             # 15
                    libelle_poche,                            # 16
                    None, None, None,                         # 17-19 — dérivés des mouvements
                    _entier(c.get("value_projected")),        # 20
                    None,                                     # 21 — len(pockets), dérivé
                ))
            for l in c.get("attributes", {}).get("lines", []):
                ref_poche = l.get("pocket")
                if ref_poche is not None and ref_poche not in poche_id_vers_label:
                    raise ErreurLecteur(
                        f"lines[].pocket = {ref_poche!r} sur {c['label']!r} ne résout vers "
                        f"aucune poche du contrat (C7/D16 : la jointure est par ID).")
                lignes_classees.append((
                    c["label"], l["label"], l.get("isin"), _entier(l["value"]),
                    l.get("perf_pct"),
                    poche_id_vers_label.get(ref_poche) if ref_poche else None,
                    _classe(l["class"]), _geo(l.get("geography")), l.get("sri"),
                ))
        if lignes:
            self._poser(f"Fin coté — {eid}", lignes)
        self._lignes_classees_courantes = lignes_classees

    def _construire_lignes_et_mouvements(self, eid, mouvements):
        # Lignes : construites avec Fin coté (jointure interne poche → label), posées ici.
        if getattr(self, "_lignes_classees_courantes", None):
            self._poser(f"Lignes — {eid}", self._lignes_classees_courantes)
        self._lignes_classees_courantes = []

        contrats = {c["id"]: c for c in self._entrees("financier_cote", eid)}
        lignes = []
        for m in mouvements:
            c = contrats.get(m["entry_ref"])
            if c is None:
                continue  # référence une autre entité ou le non coté (traité par NC Flux)
            t = TYPE_MVT_VERS_LIBELLE.get(m["type"])
            if t is None:
                continue  # flux non coté — logement NC Flux
            lignes.append((_jjmmaaaa(m["date"]), c["label"], t,
                           _entier(m["amount"]), m.get("comment")))
        if lignes:
            self._poser(f"Mouvements — {eid}", lignes)

    def _construire_non_cote(self, eid, mouvements, valuations):
        entrees = self._entrees("non_cote", eid)
        lignes = []
        for n in entrees:
            attrs = n.get("attributes", {})
            lignes.append((
                n["label"], n.get("manager"), attrs.get("strategy"),
                _moic(attrs.get("moic_target")),          # 3 — verbatim « 2,2x »
                _entier(n.get("capital_committed")),      # 4
                _entier(n.get("capital_called")),         # 5
                _entier(attrs.get("uncalled_reel")),      # 6
                _entier(attrs.get("uncalled_estime")),    # 7
                _moic(attrs.get("moic_realise")),         # 8
                _entier(n.get("value_current")),          # 9
                _classe(n.get("classe_rhetores")),        # 10
                n.get("tri_pct"),                         # 11 — MQ4
                attrs.get("segment"),                     # 12
                attrs.get("duration_target"),             # 13
                _jjmmaaaa(n.get("invest_date")),          # 14 — MQ10
                attrs.get("instrument_type"),             # 15
            ))
        if lignes:
            self._poser(f"Non coté — {eid}", lignes)

        # NC Flux : flux (mouvements) + points de VL (valuations) du fonds, par fonds
        # dans l'ordre du store, chronologiques — l'ordre observé des classeurs.
        ids = {n["id"]: n["label"] for n in entrees}
        flux = []
        for n in entrees:
            evenements = []
            for m in mouvements:
                if m["entry_ref"] == n["id"]:
                    t = TYPE_FLUX_VERS_LIBELLE.get(m["type"])
                    if t is None:
                        if m["type"] in TYPE_MVT_VERS_LIBELLE:
                            raise ErreurLecteur(
                                f"mouvement {m['id']} de type {m['type']!r} sur l'entrée non "
                                f"coté {n['label']!r} — un flux de contrat coté ne peut pas "
                                f"viser un fonds (entry_ref suspect).")
                        raise ErreurLecteur(f"type de flux inconnu {m['type']!r} ({m['id']}).")
                    evenements.append((m["date"], t, m["amount"]))
            for v in valuations:
                if v["position_id"] == n["id"]:
                    evenements.append((v["date"], "Valorisation", v["value"]))
            for d, t, montant in sorted(evenements, key=lambda x: x[0]):
                flux.append((ids[n["id"]], _jjmmaaaa(d), t, _entier(montant)))
        if flux:
            self._poser(f"NC Flux — {eid}", flux)
