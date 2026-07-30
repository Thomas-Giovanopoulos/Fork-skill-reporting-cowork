#!/usr/bin/env python3
"""Appariement d'un document à son profil de gabarit — B10 / N4.

Code **déterministe** : même document, même profil, toujours. C'est ce qui le rend testable à
l'égalité exacte, contrairement à l'extraction des valeurs qui est faite par un subagent et ne se
vérifie que par invariants. La distinction est le fondement de ce module (cf.
`docs/plan_session_dev_2026-07-29.md`).

Ce matcher est écrit d'après ce que le corpus du 29/07 a **établi**, et non d'après ce que l'étude
d'origine supposait. Quatre écarts, chacun motivé par une observation :

**1 — La couche 1 (métadonnées) ne peut que RESTREINDRE, jamais décider.** Chez Cardif, `Producer` et
`Creator` sont identiques de part et d'autre d'une refonte à laquelle une seule ancre sur onze survit.
Et `template_id_natif` (`TYPE_MODELE=66`) vaut la même chose avant et après : il identifie une *famille
de document*, pas un gabarit. La couche 1 sert donc de **pré-filtre d'émetteur**. Un appariement de
gabarit qui reposerait sur elle serait faux sans jamais le signaler.

**2 — Les polices discriminent les émetteurs, pas les gabarits.** Elles séparent parfaitement les deux
gabarits Cardif, mais sont identiques sur les cinq documents Himalia. Le résultat Cardif ne se
généralise pas : les polices entrent dans le pré-filtre d'émetteur, pas dans le score de gabarit.

**3 — Sections REQUISES et OPTIONNELLES sont deux choses différentes.** Confirmé sur trois émetteurs
indépendamment : `PRM` chez Spirica, `Fonds Euro` chez Himalia (absent 3 fois sur 5), `Arbitrages` chez
Wealins (1 sur 7). Ces sections sont **pilotées par la donnée** — elles apparaissent quand le
portefeuille les justifie. Avec une liste à plat, un gabarit à géométrie variable se fait passer pour
plusieurs, et on versionne pour rien. Ici : les requises sont une **barrière** (toutes présentes ou
rejet), les optionnelles n'ajoutent que de la confiance et leur absence ne pénalise pas.

**4 — La version se choisit par DATE D'ARRÊTÉ, pas par périodicité.** D42. La périodicité n'est pas
lisible dans le document chez trois émetteurs sur quatre, elle ne peut donc pas servir au matching.
Plusieurs profils peuvent partager `(emetteur_code, gabarit)` et se distinguer par leur fenêtre de
validité — c'est le cas Cardif, et c'est ce qui permet de lire les archives (limite LIM5 : une fenêtre
sert à *choisir*, jamais à retirer).

Et un acquis de l'étude d'origine, confirmé : **le nombre de pages reste hors matching.** Dauphine va
de 3 à 6 pages, Wealins de 15 à 26, pour le même gabarit.

Enfin, une règle de conduite plutôt qu'un algorithme : **l'ambiguïté est signalée, jamais tranchée en
silence.** La frontière entre « variante » et « nouveau gabarit » est un jugement (limite LIM3) ; le
matcher qui devine à la place de l'humain fabrique des erreurs invisibles. Deux profils à égalité
rendent un verdict `ambigu`, à charge pour l'appelant de proposer une adjudication.
"""
from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Lecture du document
# ---------------------------------------------------------------------------

@dataclass
class Empreinte:
    """Ce qu'on sait d'un document avant tout appariement."""
    fichier: str
    texte: str = ""              # pdftotext -layout, tout le document
    producer: str | None = None
    creator: str | None = None
    version_pdf: str | None = None
    polices: tuple[str, ...] = ()
    n_pages: int | None = None   # informatif — JAMAIS utilisé pour apparier
    erreur: str | None = None


def _exec(argv: list[str]) -> str:
    r = subprocess.run(argv, capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode == 0 else ""


def lire_empreinte(chemin: Path) -> Empreinte:
    """Extrait les trois couches d'un PDF. Tolère l'absence totale de métadonnées.

    Les cinq documents Nortia n'ont AUCUNE métadonnée : couche 1 vide. Un matcher qui
    supposerait `Producer` présent échouerait sur eux — d'où les `None` partout par défaut
    plutôt qu'une exception.
    """
    e = Empreinte(fichier=chemin.name)
    if not chemin.exists():
        e.erreur = "fichier introuvable"
        return e

    for ligne in _exec(["pdfinfo", str(chemin)]).splitlines():
        if ":" not in ligne:
            continue
        cle, _, val = ligne.partition(":")
        cle, val = cle.strip().lower(), val.strip()
        if cle == "producer":
            e.producer = val or None
        elif cle == "creator":
            e.creator = val or None
        elif cle == "pdf version":
            e.version_pdf = val or None
        elif cle == "pages":
            try:
                e.n_pages = int(val)
            except ValueError:
                pass

    # pdffonts : une ligne d'en-tête, une ligne de tirets, puis une police par ligne.
    polices = []
    for ligne in _exec(["pdffonts", str(chemin)]).splitlines()[2:]:
        nom = ligne.split(" ")[0].strip()
        if nom:
            polices.append(nom)
    e.polices = tuple(sorted(set(polices)))

    e.texte = _exec(["pdftotext", "-layout", str(chemin), "-"])
    if not e.texte.strip():
        e.erreur = "aucun texte extrait (document image ? OCR nécessaire ?)"
    return e


# ---------------------------------------------------------------------------
# Normalisation du texte pour la recherche d'ancres
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    """Casse, accents et espaces neutralisés — les ancres doivent survivre à la mise en page.

    Motif tiré du corpus : la refonte Cardif change la CASSE des titres (capitales → casse
    mixte) sans changer les mots. Une ancre sensible à la casse aurait vu deux gabarits là où
    il y avait aussi un changement de mots ; une ancre insensible isole le vrai signal.
    """
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split()).casefold()


def _present(ancre: str | dict, texte_norm: str, texte_brut: str) -> bool:
    """Une ancre est soit une chaîne (recherche normalisée), soit {"regex": "..."}.

    La forme regex existe pour les cas où la position compte — par exemple le discriminant
    Wealins `^INFORMATION\\s+(ANNUELLE|TRIMESTRIELLE)\\s*:`, qui doit être en tête de ligne :
    le mot « trimestre » apparaît DIX fois dans les documents annuels (tableau Rendement et
    note de bas de page), donc une simple recherche de sous-chaîne conclurait à l'inverse.
    """
    if isinstance(ancre, dict):
        motif = ancre.get("regex")
        if not motif:
            return False
        drapeaux = re.MULTILINE
        if not ancre.get("sensible_casse"):
            drapeaux |= re.IGNORECASE
        return re.search(motif, texte_brut, drapeaux) is not None
    return _norm(ancre) in texte_norm


# ---------------------------------------------------------------------------
# Résultat
# ---------------------------------------------------------------------------

@dataclass
class Verdict:
    statut: str                      # apparie | ambigu | aucun | illisible
    emetteur_code: str | None = None
    gabarit: str | None = None
    valide_depuis: str | None = None
    score: float = 0.0
    candidats: list[dict] = field(default_factory=list)
    explication: list[str] = field(default_factory=list)

    def resume(self) -> str:
        if self.statut == "apparie":
            v = f"@{self.valide_depuis}" if self.valide_depuis else ""
            return f"{self.emetteur_code}/{self.gabarit}{v} (score {self.score:.2f})"
        return self.statut.upper()


# ---------------------------------------------------------------------------
# Appariement
# ---------------------------------------------------------------------------

# Poids des couches. La couche 1 est VOLONTAIREMENT absente de ce barème : elle ne participe
# pas au score de gabarit, seulement au pré-filtre d'émetteur (cf. écart n°1 de l'en-tête).
POIDS_ANCRE_REQUISE = 1.0
POIDS_ANCRE_OPTIONNELLE = 0.3
POIDS_DISCRIMINANT = 3.0     # une ancre déclarée discriminante vaut plus que les autres
ECART_AMBIGUITE = 0.15       # deux candidats plus proches que cela => ambigu, pas de choix


def _prefiltre_emetteur(emp: Empreinte, profils: list[dict]) -> tuple[list[dict], list[str]]:
    """Restreint les candidats par la couche 1. Ne décide JAMAIS seul.

    Un profil sans indice de couche 1 (cas Nortia, aucune métadonnée) reste toujours candidat :
    le pré-filtre ne peut qu'écarter sur preuve, jamais sur absence de preuve.
    """
    notes, retenus = [], []
    for p in profils:
        c1 = p.get("couche1") or {}
        if not c1:
            retenus.append(p)
            continue
        attendus = c1.get("producer_contient")
        if attendus and emp.producer and not any(_norm(a) in _norm(emp.producer) for a in attendus):
            continue
        attendus = c1.get("creator_contient")
        if attendus and emp.creator and not any(_norm(a) in _norm(emp.creator) for a in attendus):
            continue
        pol = c1.get("polices")
        if pol and emp.polices and not set(pol) & set(emp.polices):
            continue
        retenus.append(p)

    if len(retenus) < len(profils):
        notes.append(f"pré-filtre couche 1 : {len(profils)} → {len(retenus)} candidat(s)")
    if not retenus:
        notes.append("pré-filtre trop strict — tous les profils écartés, on repart de la liste entière")
        retenus = list(profils)
    return retenus, notes


def _score_profil(emp: Empreinte, profil: dict, texte_norm: str) -> tuple[float, list[str]]:
    """Score des couches 2 et 3. Rend -1 si une ancre REQUISE manque (barrière)."""
    sig = profil.get("signature") or {}
    requises = sig.get("sections_requises") or sig.get("ancres_requises") or []
    optionnelles = sig.get("sections_optionnelles") or sig.get("ancres_optionnelles") or []
    discriminants = sig.get("discriminants") or []
    notes = []

    manquantes = [a for a in requises if not _present(a, texte_norm, emp.texte)]
    if manquantes:
        apercu = ", ".join(str(m)[:40] for m in manquantes[:3])
        notes.append(f"REJET — {len(manquantes)}/{len(requises)} ancre(s) requise(s) absente(s) : {apercu}")
        return -1.0, notes

    score = POIDS_ANCRE_REQUISE * len(requises)
    if requises:
        notes.append(f"{len(requises)}/{len(requises)} requises présentes")

    trouvees_opt = [a for a in optionnelles if _present(a, texte_norm, emp.texte)]
    score += POIDS_ANCRE_OPTIONNELLE * len(trouvees_opt)
    if optionnelles:
        notes.append(f"{len(trouvees_opt)}/{len(optionnelles)} optionnelles présentes "
                     f"(absence NON pénalisée — sections pilotées par la donnée)")

    for d in discriminants:
        if _present(d, texte_norm, emp.texte):
            score += POIDS_DISCRIMINANT
            notes.append(f"discriminant satisfait : {str(d)[:60]}")
        else:
            notes.append(f"REJET — discriminant absent : {str(d)[:60]}")
            return -1.0, notes

    # Normalisation : un profil à 30 ancres ne doit pas battre un profil à 5 par le volume.
    plafond = (POIDS_ANCRE_REQUISE * max(len(requises), 1)
               + POIDS_ANCRE_OPTIONNELLE * len(optionnelles)
               + POIDS_DISCRIMINANT * len(discriminants))
    return score / plafond, notes


def _fenetre_contient(profil: dict, arrete: str | None) -> bool:
    """La fenêtre de validité couvre-t-elle cet arrêté ? (D42)

    Sans arrêté connu, on ne peut pas choisir : tous les profils restent éligibles et
    l'appelant tranchera — ou recevra un verdict ambigu. Deviner « le plus récent » ici
    donnerait un faux positif silencieux sur un document d'archive.
    """
    depuis, jusqu_a = profil.get("valide_depuis"), profil.get("valide_jusqu_a")
    if depuis is None and jusqu_a is None:
        return True
    if arrete is None:
        return True
    d = date.fromisoformat(arrete)
    if depuis and d < date.fromisoformat(depuis):
        return False
    if jusqu_a and d > date.fromisoformat(jusqu_a):
        return False
    return True


def apparier(chemin: Path, profils: list[dict], arrete: str | None = None) -> Verdict:
    """Apparie un document à son profil. Déterministe.

    ``arrete`` est la date d'arrêté du document, fournie par le contexte du run — jamais lue
    dans le document (D42 : la périodicité n'y est pas lisible, et l'arrêté ne l'est pas
    toujours non plus). Elle ne sert qu'à choisir entre versions d'un même gabarit.
    """
    emp = lire_empreinte(chemin)
    if emp.erreur and not emp.texte.strip():
        return Verdict(statut="illisible", explication=[emp.erreur])

    texte_norm = _norm(emp.texte)
    candidats, notes = _prefiltre_emetteur(emp, profils)

    scores = []
    for p in candidats:
        if not _fenetre_contient(p, arrete):
            notes.append(f"écarté (fenêtre) : {p['emetteur_code']}/{p['gabarit']}"
                         f"@{p.get('valide_depuis')} ne couvre pas {arrete}")
            continue
        s, n = _score_profil(emp, p, texte_norm)
        if s >= 0:
            scores.append((s, p, n))

    if not scores:
        return Verdict(statut="aucun", explication=notes + ["aucun profil ne franchit la barrière des ancres requises"])

    scores.sort(key=lambda t: t[0], reverse=True)
    meilleur, profil, notes_profil = scores[0]
    resultat = Verdict(
        statut="apparie",
        emetteur_code=profil["emetteur_code"],
        gabarit=profil["gabarit"],
        valide_depuis=profil.get("valide_depuis"),
        score=meilleur,
        candidats=[{"emetteur_code": p["emetteur_code"], "gabarit": p["gabarit"],
                    "valide_depuis": p.get("valide_depuis"), "score": round(s, 3)}
                   for s, p, _ in scores],
        explication=notes + notes_profil,
    )

    if len(scores) > 1 and (meilleur - scores[1][0]) < ECART_AMBIGUITE:
        second = scores[1][1]
        resultat.statut = "ambigu"
        resultat.explication.append(
            f"AMBIGU — {profil['emetteur_code']}/{profil['gabarit']} et "
            f"{second['emetteur_code']}/{second['gabarit']} à {meilleur - scores[1][0]:.3f} d'écart. "
            "Non tranché à dessein : la frontière variante / nouveau gabarit est un jugement (limite LIM3). "
            "À porter en adjudication."
        )
    return resultat


def charger_profils(chemin: Path) -> list[dict]:
    brut = json.loads(Path(chemin).read_text(encoding="utf-8"))
    return brut if isinstance(brut, list) else brut.get("profils", brut.get("gabarits", []))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        raise SystemExit("Usage: matcher_gabarit.py <profils.json> <document.pdf> [AAAA-MM-JJ]")
    v = apparier(Path(sys.argv[2]), charger_profils(Path(sys.argv[1])),
                 sys.argv[3] if len(sys.argv) > 3 else None)
    print(v.resume())
    for l in v.explication:
        print("   ·", l)
