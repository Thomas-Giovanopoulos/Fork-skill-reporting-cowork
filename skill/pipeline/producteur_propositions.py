"""Producteur de propositions — N5, la boucle de self-healing.

Ferme la boucle du fork : le matcher **détecte** qu'un document ne s'apparie à aucun gabarit connu
(ou dérive d'un existant), et ce module **rédige la proposition** correspondante. L'admin
**arbitre**, et le run suivant d'un autre CGP voit le gabarit canonisé. C'est ce qui fait qu'un
apprentissage ne meurt plus avec le run où il a eu lieu (D36).

## Le pipeline ne parle pas au MCP — il écrit un fichier

Même contrainte, même symétrie que `referentiels.py` : le sandbox du pipeline n'a aucun réseau,
seul l'AGENT peut appeler `ref_propose`. Ce module produit donc `propositions.json` dans le dossier
de run ; c'est l'agent qui relaie ensuite chaque entrée au MCP. Le pipeline reste une fonction pure
de ses fichiers, donc reproductible.

## Ce que ce module NE fait pas, et c'est le cœur de sa correction

**Il ne fabrique aucune signature.** La frontière « variante vs nouveau gabarit » est un jugement
(limite LIM3), et un détecteur de drift ne sait pas si un changement est bénin ou cassant (LIM4).
Le producteur **signale et fournit la matière** ; il ne devine pas le profil. Une proposition n'est
donc pas un gabarit prêt à canoniser : c'est une **demande de travail** posée dans la file. L'admin,
aidé d'une analyse, complète la signature avant d'accepter — et `ref_arbitrer` refusera d'ailleurs
d'écrire un gabarit sans `signature` (contrainte de `_upsert_canonique`).

**Il ne met AUCUNE donnée client dans la proposition (D44).** Le texte extrait d'un relevé regorge
de noms, de montants, de numéros de contrat. Or la file d'adjudication est lue par l'admin — et le
store est partagé. La proposition ne porte donc que : l'**empreinte** du document (sha256, non
révélateur), l'**émetteur candidat** s'il est connu (code technique), les **scores** d'appariement,
et un motif. La matière d'analyse — le texte — reste dans le dossier de run, jamais dans la
proposition. C'est la même règle que pour `source_document` retiré en D44 : ce qui identifie un
client ne monte pas dans un référentiel partagé.

## Trois issues du matcher, trois traitements

- **`apparie`** — rien à proposer. Le document a trouvé son gabarit.
- **`aucun`** — aucun profil ne franchit la barrière. On propose de créer un gabarit. On ne tranche
  PAS entre « nouvel émetteur » et « nouveau gabarit d'un émetteur connu » : c'est une qualification
  qui demande l'œil humain. Le meilleur candidat rejeté (s'il en reste un, même sous la barrière)
  est joint comme indice d'émetteur, et la `nature` est marquée `a_confirmer`.
- **`ambigu`** — deux profils trop proches. On propose une `mise_a_jour` portant les deux candidats ;
  l'admin tranche lequel est le bon, ou constate qu'il faut les distinguer davantage.
- **`illisible`** — pas de proposition : un document sans texte relève de l'OCR, pas du référentiel.
  Signalé à part pour que l'agent le remonte au CGP.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matcher_gabarit as M  # noqa: E402

NOM_FICHIER_PROPOSITIONS = "propositions.json"


def empreinte_document(chemin: Path) -> str:
    """sha256 du CONTENU. Non identifiant, et reconnaît deux fois le même document (D44)."""
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            h.update(bloc)
    return h.hexdigest()


@dataclass
class Proposition:
    """Une entrée prête à passer à `ref_propose`. Sans aucune donnée client (D44)."""
    cible: str
    nature: str
    cle: dict
    proposition: dict
    source_empreinte: str
    source_gabarit: str | None
    source_arrete: str | None
    motif: str

    def pour_ref_propose(self, run_id: str | None = None) -> dict:
        d = {"cible": self.cible, "nature": self.nature, "cle": self.cle,
             "proposition": self.proposition, "source_empreinte": self.source_empreinte,
             "source_gabarit": self.source_gabarit, "source_arrete": self.source_arrete,
             "motif": self.motif}
        if run_id:
            d["run_id"] = run_id
        return d


@dataclass
class Bilan:
    """Ce qu'un run a produit côté référentiels — propositions et signalements."""
    propositions: list[Proposition] = field(default_factory=list)
    illisibles: list[dict] = field(default_factory=list)
    apparies: list[dict] = field(default_factory=list)  # trace, pas une proposition

    def resume(self) -> str:
        parts = [f"{len(self.apparies)} apparié(s)"]
        if self.propositions:
            parts.append(f"{len(self.propositions)} proposition(s)")
        if self.illisibles:
            parts.append(f"{len(self.illisibles)} illisible(s)")
        return " · ".join(parts)


def _candidat_principal(verdict) -> dict | None:
    return verdict.candidats[0] if verdict.candidats else None


def proposer_pour(chemin: Path, profils: list[dict], arrete: str | None = None) -> Proposition | dict | None:
    """Examine UN document et rend soit une Proposition, soit un signalement dict (illisible),
    soit None (apparié, rien à proposer).

    `arrete` vient du contexte du run, jamais du document (D42/D44) : il sert à choisir la version
    de gabarit et n'est pas identifiant.
    """
    verdict = M.apparier(chemin, profils, arrete)
    empreinte = empreinte_document(chemin)

    if verdict.statut == "apparie":
        return None

    if verdict.statut == "illisible":
        return {"fichier_empreinte": empreinte, "raison": verdict.explication,
                "action": "OCR requis — hors périmètre du référentiel"}

    if verdict.statut == "ambigu":
        deux = verdict.candidats[:2]
        return Proposition(
            cible="gabarit", nature="mise_a_jour",
            cle={"candidats": [{"emetteur_code": c["emetteur_code"], "gabarit": c["gabarit"],
                                "valide_depuis": c["valide_depuis"]} for c in deux]},
            proposition={"statut_matcher": "ambigu", "candidats": deux,
                         "a_faire": "départager les deux profils, ou renforcer leurs signatures "
                                    "pour qu'ils cessent de se confondre"},
            source_empreinte=empreinte,
            source_gabarit=deux[0]["gabarit"] if deux else None,
            source_arrete=arrete,
            motif=("Document à moins de "
                   f"{M.ECART_AMBIGUITE} de deux profils : appariement non tranché par le matcher, "
                   "arbitrage humain requis (limite LIM3)."))

    # statut == "aucun"
    principal = _candidat_principal(verdict)
    emetteur_indice = principal["emetteur_code"] if principal else None
    return Proposition(
        cible="gabarit", nature="nouveau_gabarit",
        cle={"emetteur_code": emetteur_indice or "a_qualifier",
             "gabarit": "a_qualifier", "valide_depuis": arrete or "a_qualifier"},
        proposition={"statut_matcher": "aucun",
                     "nature_a_confirmer": "nouvel_emetteur ou nouveau_gabarit — à qualifier par "
                                           "l'analyse, le matcher ne peut pas trancher (LIM3)",
                     "meilleur_candidat_rejete": principal,
                     "a_faire": "analyser le document (resté dans le dossier de run, PAS ici — "
                                "D44), établir la signature, puis compléter cette proposition "
                                "avant de l'accepter"},
        source_empreinte=empreinte,
        source_gabarit=None,          # justement : aucun gabarit reconnu
        source_arrete=arrete,
        motif=("Aucun gabarit connu ne franchit la barrière des ancres requises. "
               + (f"Indice d'émetteur d'après le meilleur candidat rejeté : {emetteur_indice}. "
                  if emetteur_indice else "Aucun émetteur reconnu par le pré-filtre. ")
               + "À qualifier : nouvel émetteur, ou nouveau gabarit d'un émetteur connu."))


def produire(documents: list[tuple[Path, str | None]], profils: list[dict]) -> Bilan:
    """Traite une liste de (chemin, arrêté) et rassemble le bilan du run."""
    bilan = Bilan()
    for chemin, arrete in documents:
        r = proposer_pour(chemin, profils, arrete)
        if r is None:
            v = M.apparier(chemin, profils, arrete)
            bilan.apparies.append({"fichier_empreinte": empreinte_document(chemin),
                                   "emetteur_code": v.emetteur_code, "gabarit": v.gabarit,
                                   "valide_depuis": v.valide_depuis})
        elif isinstance(r, Proposition):
            bilan.propositions.append(r)
        else:
            bilan.illisibles.append(r)
    return bilan


def ecrire(bilan: Bilan, dossier_run: Path, run_id: str | None = None) -> Path | None:
    """Écrit `propositions.json` si le run a produit quelque chose à relayer.

    N'écrit RIEN si aucune proposition ni aucun illisible : un fichier vide inviterait l'agent à
    faire un appel MCP inutile. Le fichier est destiné à l'agent, qui rejoue chaque entrée dans
    `ref_propose`.
    """
    if not bilan.propositions and not bilan.illisibles:
        return None
    dest = Path(dossier_run) / NOM_FICHIER_PROPOSITIONS
    contenu = {
        "_a_propos": (
            "Propositions à relayer au MCP par l'AGENT (le pipeline n'a pas le réseau). Pour "
            "chacune : appeler `ref_propose` avec les champs de `pour_ref_propose`. AUCUNE donnée "
            "client ici (D44) : seulement empreintes, codes de gabarit et scores. Le texte des "
            "documents reste dans le dossier de run."),
        "run_id": run_id,
        "propositions": [p.pour_ref_propose(run_id) for p in bilan.propositions],
        "illisibles": bilan.illisibles,
    }
    dest.write_text(json.dumps(contenu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dest


if __name__ == "__main__":
    # Usage : producteur_propositions.py <profils.json> <doc.pdf> [arrete AAAA-MM-JJ]
    if len(sys.argv) < 3:
        raise SystemExit("Usage: producteur_propositions.py <profils.json> <doc.pdf> [AAAA-MM-JJ]")
    profils = M.charger_profils(Path(sys.argv[1]))
    arrete = sys.argv[3] if len(sys.argv) > 3 else None
    r = proposer_pour(Path(sys.argv[2]), profils, arrete)
    if r is None:
        print("apparié — aucune proposition")
    elif isinstance(r, Proposition):
        print(json.dumps(r.pour_ref_propose(), ensure_ascii=False, indent=2))
    else:
        print("illisible :", json.dumps(r, ensure_ascii=False))
