"""Lecture des référentiels par le pipeline — D35 / D36.

Ce module résout **un fichier**, jamais une connexion. La distinction à ne pas confondre — elle a
été posée en question, elle mérite d'être écrite noir sur blanc :

- **L'AGENT peut appeler le MCP.** Claude a `ref_bundle` dans ses outils : les instructions du
  skill lui demandent de l'appeler en début de run et d'écrire le résultat sur disque.
- **LE PIPELINE ne peut pas.** Les scripts tournent dans un sandbox lancé en `--unshare-net` :
  ni réseau, ni DNS, ports 443/53/5432 fermés. Un client MCP ou un `psycopg.connect()` y
  échouerait toujours.

    agent Claude ──appelle──► ref_bundle ──lit──► Postgres
          └──écrit──► <run>/referentiels.json ──lu par──► CE MODULE

D'où la formule du RUNBOOK §1 : **le fichier est le contrat, pas la connexion.** Le jour où la
base change d'hébergeur, rien ici ne bouge.

**Et c'est un avantage, pas seulement une contrainte.** Un pipeline qui est une fonction pure de
ses fichiers est **reproductible** : deux exécutions du même run rendent le même HTML, et le
bundle devient une pièce du dossier archivé (D4). Si le code appelait le réseau, deux runs du même
client pourraient différer sans que rien ne le signale — et le déterminisme que la régression
vérifie à chaque fixture ne voudrait plus rien dire.

## Ce que ce module NE fait pas, et pourquoi

Il ne lit pas les **ISIN**. Le référentiel ISIN vit dans `assets/isin_referentiel_v0.csv` et il
est consommé par les **subagents**, qui lisent le fichier en suivant SKILL.md §2.b — aucun code
ne le lit. Le vendorer une seconde fois dans un bundle mettrait 261 lignes en double dans le
paquet, avec deux sources de vérité à faire diverger. Le CSV reste donc le snapshot ISIN ; la
bascule vers le bundle pour cette partie relève de N3, qui touche le chemin d'extraction — lequel
n'a **aucun filet de régression** (limite LIM8). On ne le fait pas à l'aveugle.

## Le repli est un secours, et il doit se voir

Un run qui retomberait en silence sur le snapshot vendoré utiliserait des référentiels figés à
l'installation : un CGP manquerait un gabarit adjugé la veille sans jamais l'apprendre. C'est
exactement ce que D36 corrige. La provenance est donc **toujours** rendue, et un appelant qui
l'ignore est un appelant fautif : `charger()` la retourne dans l'objet, et `resume()` la nomme.
"""
from __future__ import annotations

import json
import os
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ICI = Path(__file__).resolve().parent
PAQUET = ICI.parent

# Snapshot vendoré : le repli hors ligne (D35). Produit par `seed/construire_bundle.py`, il ne
# porte PAS les ISIN (cf. l'en-tête). Son absence n'est pas une erreur : elle signifie seulement
# qu'il n'y a pas de repli, et l'appelant l'apprendra par une exception explicite.
SNAPSHOT_VENDORE = PAQUET / "assets" / "referentiels_snapshot.json"

# Emplacement conventionnel du bundle écrit par le client au début d'un run.
NOM_BUNDLE_RUN = "referentiels.json"

VARIABLE_ENV = "REFERENTIELS_BUNDLE"

SECTIONS_ATTENDUES = ("acteurs", "successions", "gabarits")


class ReferentielsIntrouvables(RuntimeError):
    """Aucune source de référentiels — ni bundle de run, ni snapshot vendoré."""


@dataclass
class Referentiels:
    """Les référentiels d'un run, avec leur provenance."""

    provenance: str          # 'run' | 'snapshot_vendore'
    chemin: Path
    schema_version: str | None = None
    acteurs: list[dict] = field(default_factory=list)
    successions: list[dict] = field(default_factory=list)
    gabarits: list[dict] = field(default_factory=list)
    compte: dict = field(default_factory=dict)

    # -- accès ------------------------------------------------------------
    def gabarits_de(self, emetteur_code: str) -> list[dict]:
        """Les profils d'un émetteur, du plus ancien au plus récent (D42).

        Le tri par `valide_depuis` n'est pas cosmétique : c'est l'ordre dans lequel un matcher
        doit présenter les versions d'un gabarit, et `'0001-01-01'` (« depuis toujours ») s'y
        place naturellement en tête.
        """
        return sorted(
            (g for g in self.gabarits if g.get("emetteur_code") == emetteur_code),
            key=lambda g: g.get("valide_depuis") or "0001-01-01",
        )

    def acteur(self, code_ou_alias: str) -> dict | None:
        """Cherche par `code`, puis par `alias`, à la casse et aux accents près.

        Les alias existent parce qu'un même acteur apparaît sous plusieurs raisons sociales dans
        les relevés (K1) ; les ignorer reviendrait à ne jamais reconnaître un émetteur nommé
        autrement que dans le seed.
        """
        cible = _norm(code_ou_alias)
        for a in self.acteurs:
            if _norm(a.get("code", "")) == cible:
                return a
        for a in self.acteurs:
            if any(_norm(x) == cible for x in (a.get("alias") or [])):
                return a
        return None

    def successeur(self, code: str) -> dict | None:
        """La succession dont `code` est le prédécesseur, s'il en existe une (K5).

        Sert à réconcilier un relevé antérieur à un changement de dépositaire : sans elle, un
        acteur disparu rend le document inrattachable.
        """
        for s in self.successions:
            if _norm(s.get("predecesseur_code", "")) == _norm(code):
                return s
        return None

    def resume(self) -> str:
        base = (f"{len(self.acteurs)} acteurs · {len(self.successions)} successions · "
                f"{len(self.gabarits)} gabarits · schema {self.schema_version}")
        if self.provenance == "snapshot_vendore":
            return (f"⚠ SNAPSHOT VENDORÉ ({self.chemin.name}) — {base}. Référentiels figés à "
                    f"l'installation : un gabarit adjugé depuis ne s'y trouve pas (D36).")
        return f"bundle du run ({self.chemin.name}) — {base}"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split()).casefold()


def _provenance_de(p: Path) -> str:
    """`snapshot_vendore` si le chemin EST le snapshot du paquet, `run` sinon.

    Comparaison sur le chemin résolu : un lien symbolique ou un chemin relatif désignant le
    snapshot doit être reconnu comme tel, sans quoi l'avertissement de repli sauterait.
    """
    try:
        return "snapshot_vendore" if p.resolve() == SNAPSHOT_VENDORE.resolve() else "run"
    except OSError:
        return "run"


def resoudre_source(chemin: str | Path | None = None,
                    dossier_run: str | Path | None = None) -> tuple[Path, str]:
    """Rend (chemin, provenance) en essayant les sources dans l'ordre de fraîcheur décroissante.

    L'ordre compte : un bundle de run est toujours préféré au snapshot, parce qu'il vient de la
    base et porte donc les adjudications récentes. Le snapshot ne sert que si tout le reste
    manque — réseau indisponible, MCP non branché, cold start.
    """
    candidats: list[Path] = []
    if chemin:
        candidats.append(Path(chemin))
    depuis_env = os.environ.get(VARIABLE_ENV)
    if depuis_env:
        candidats.append(Path(depuis_env))
    if dossier_run:
        candidats.append(Path(dossier_run) / NOM_BUNDLE_RUN)
    candidats.append(Path.cwd() / NOM_BUNDLE_RUN)
    candidats.append(SNAPSHOT_VENDORE)

    for p in candidats:
        if p.is_file():
            # La provenance est une propriété de la SOURCE, pas de la façon dont on l'a demandée.
            # Premier jet : tout chemin explicite était étiqueté « run ». Conséquence, trouvée par
            # `test_referentiels.py` — pointer volontairement le snapshot vendoré (cas légitime :
            # forcer le mode hors ligne) le faisait passer pour un bundle frais et **supprimait
            # l'avertissement**. C'était exactement le repli silencieux que ce module existe pour
            # empêcher. On compare donc le chemin résolu, pas l'intention de l'appelant.
            return p, _provenance_de(p)

    essayes = "\n".join(f"    {p}  ({prov})" for p, prov in candidats)
    raise ReferentielsIntrouvables(
        "Aucune source de référentiels trouvée. Chemins essayés :\n" + essayes +
        f"\n\nUn run doit soit recevoir le bundle écrit par le client "
        f"(appel MCP `ref_bundle`, puis fichier `{NOM_BUNDLE_RUN}`), soit disposer du snapshot "
        f"vendoré `{SNAPSHOT_VENDORE.relative_to(PAQUET)}`. Le pipeline ne peut PAS joindre la "
        f"base lui-même : son sandbox n'a aucun accès réseau (RUNBOOK §1)."
    )


def charger(chemin: str | Path | None = None,
            dossier_run: str | Path | None = None) -> Referentiels:
    """Charge les référentiels et rend leur provenance avec eux.

    Le contrôle de forme est volontairement minimal : on vérifie que les trois sections attendues
    sont des listes, et on s'arrête là. Le bundle est produit soit par le MCP, soit par
    `construire_bundle.py`, qui valident tous deux en amont — redoubler la validation ici
    donnerait un troisième endroit à maintenir, et c'est ainsi qu'on fabrique des divergences.
    """
    p, provenance = resoudre_source(chemin, dossier_run)
    try:
        brut = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReferentielsIntrouvables(f"{p} n'est pas un JSON valide : {exc}") from exc

    manquantes = [s for s in SECTIONS_ATTENDUES if not isinstance(brut.get(s), list)]
    if manquantes:
        raise ReferentielsIntrouvables(
            f"{p} : section(s) absente(s) ou mal formée(s) : {manquantes}. "
            f"Attendu un bundle au contrat du RUNBOOK §3. Si le bundle a été demandé par "
            f"sections, vérifier que celles-ci ont bien été demandées — un tableau vide peut "
            f"être un choix de l'appelant, pas une base vide (voir la clé `compte`)."
        )

    return Referentiels(
        provenance=provenance,
        chemin=p,
        schema_version=brut.get("schema_version"),
        acteurs=brut.get("acteurs") or [],
        successions=brut.get("successions") or [],
        gabarits=brut.get("gabarits") or [],
        compte=brut.get("compte") or {},
    )


if __name__ == "__main__":
    import sys
    r = charger(sys.argv[1] if len(sys.argv) > 1 else None)
    print(r.resume())
    for g in r.gabarits:
        fenetre = g.get("valide_depuis") or "?"
        if g.get("valide_jusqu_a"):
            fenetre += f" → {g['valide_jusqu_a']}"
        print(f"   {g.get('emetteur_code'):32s} {g.get('gabarit'):34s} {fenetre}")
