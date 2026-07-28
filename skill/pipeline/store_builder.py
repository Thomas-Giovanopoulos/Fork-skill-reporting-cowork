"""
store_builder.py
=================

Construit le dict client "forme-store" (schema_version "2.0-skill") destine
au datahub Postgres de Rhetores Finance, conformement a
`store_client.schema.json`.

Discipline ABSENCE != NULL
---------------------------
Une donnee absente doit se traduire par une cle ABSENTE du dict, jamais par
une cle presente avec la valeur None. Le helper `_clean` applique cette regle
recursivement sur les dicts/listes lors de l'ecriture des entrees.

Si, dans de rares cas, un null JSON explicite est reellement voulu (ex: "on a
verifie et il n'y a pas de valeur, ce n'est pas un oubli"), on peut passer le
sentinel `EXPLICIT_NULL` comme valeur: il sera converti en None mais la cle
sera CONSERVEE dans le dict final (contrairement a un None nu, qui est omis).

Prefixes d'id provisoire par categorie
---------------------------------------
    financier_cote     -> fc
    non_cote            -> nc
    mouvements          -> mv
    liquidites          -> lq
    immobilier          -> im
    dettes              -> dt
    exotiques           -> ex
    historique_annuel   -> ha   (extension raisonnable, non fournie dans la
                                 liste de prefixes du brief mais necessaire
                                 pour couvrir les 8 categories du schema)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Le module 'jsonschema' est requis. Installer avec: "
        "pip install --break-system-packages jsonschema"
    ) from exc


# ---------------------------------------------------------------------------
# Sentinel pour null explicite
# ---------------------------------------------------------------------------

class _ExplicitNull:
    """Sentinel: force l'ecriture d'un null JSON explicite (cle conservee)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:  # pragma: no cover
        return "EXPLICIT_NULL"


EXPLICIT_NULL = _ExplicitNull()


# ---------------------------------------------------------------------------
# Prefixes d'id provisoire par categorie
# ---------------------------------------------------------------------------

CATEGORY_PREFIX: dict[str, str] = {
    "financier_cote": "fc",
    "non_cote": "nc",
    "mouvements": "mv",
    "liquidites": "lq",
    "immobilier": "im",
    "dettes": "dt",
    "exotiques": "ex",
    "historique_annuel": "ha",
}

_SCHEMA_PATH = Path(__file__).parent / "store_client.schema.json"


# ---------------------------------------------------------------------------
# Discipline ABSENCE != NULL
# ---------------------------------------------------------------------------

def _clean(value: Any) -> Any:
    """Nettoie recursivement une structure (dict / list / scalaire).

    - Une cle dont la valeur est None (None "nu", pas le sentinel) est omise.
    - Une cle dont la valeur est EXPLICIT_NULL est conservee avec la valeur
      JSON `null` (None) dans la sortie.
    - Les listes sont nettoyees element par element (les None nus a
      l'interieur d'une liste sont retires : une liste ne doit pas contenir
      de "trous").
    - Les dicts imbriques sont nettoyes recursivement; un dict qui devient
      vide APRES nettoyage est conserve tel quel (vide != absent : c'est
      l'appelant qui decide de ne pas inclure la cle parente s'il le souhaite).
    """
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, val in value.items():
            if val is None:
                # None nu => absence => on omet la cle
                continue
            if val is EXPLICIT_NULL:
                cleaned[key] = None
                continue
            cleaned[key] = _clean(val)
        return cleaned
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            if item is None:
                continue
            if item is EXPLICIT_NULL:
                out.append(None)
                continue
            out.append(_clean(item))
        return out
    return value


# ---------------------------------------------------------------------------
# Construction du client
# ---------------------------------------------------------------------------

def new_client(label: str, entities: Iterable[dict], reporting: dict) -> dict:
    """Cree le squelette du dict client "forme-store".

    Parameters
    ----------
    label:
        Label du client (personne physique ou groupe familial).
    entities:
        Iterable de dicts `{"label": str, "type": "pp"|"holding"}`.
        Les cles `id` et `order` sont assignees automatiquement (sequentiel,
        1-based) si absentes.
    reporting:
        Dict meta de reporting: period_short, period_long, date_reporting,
        date_display, version, profile (cles absentes => omises, cf _clean).

    Returns
    -------
    dict pret a recevoir des entrees via `add_entry`.
    """
    entity_list = []
    for idx, ent in enumerate(entities, start=1):
        entity_list.append(
            _clean(
                {
                    "id": ent.get("id") or f"tmp_ent_{idx:03d}",
                    "label": ent["label"],
                    "type": ent["type"],
                    "order": ent.get("order", idx),
                }
            )
        )

    client_dict = {
        "schema_version": "2.0-skill",
        "client": _clean(
            {
                "id": "tmp_c_001",
                "label": label,
                "entities": entity_list,
            }
        ),
        "reporting": _clean(dict(reporting)),
        "_provisional_ids": True,
    }
    return client_dict


def add_entry(client: dict, category: str, entry: dict) -> str:
    """Ajoute une entree dans `client[category]` et retourne l'id provisoire.

    L'id est genere sequentiellement a partir du nombre d'entrees deja
    presentes dans la categorie: `tmp_<prefixe>_<NNN>` (NNN sur 3 chiffres,
    1-based).

    L'entree est nettoyee via `_clean` avant insertion (discipline
    ABSENCE != NULL): toute cle a valeur None dans `entry` est omise du dict
    final. Si l'appelant passe `id` dans `entry`, il est ignore/ecrase par
    l'id genere (l'id provisoire est toujours attribue par ce module).
    """
    if category not in CATEGORY_PREFIX:
        raise ValueError(
            f"Categorie inconnue: {category!r}. "
            f"Categories valides: {sorted(CATEGORY_PREFIX)}"
        )

    prefix = CATEGORY_PREFIX[category]
    bucket = client.setdefault(category, [])
    seq = len(bucket) + 1
    new_id = f"tmp_{prefix}_{seq:03d}"

    entry_copy = dict(entry)
    entry_copy["id"] = new_id

    cleaned_entry = _clean(entry_copy)
    bucket.append(cleaned_entry)
    return new_id


# ---------------------------------------------------------------------------
# Validation JSON Schema
# ---------------------------------------------------------------------------

def _load_schema() -> dict:
    with open(_SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def validate(client: dict) -> None:
    """Valide `client` contre `store_client.schema.json` (draft 2020-12).

    Leve `jsonschema.exceptions.ValidationError` (premiere erreur) si le
    client n'est pas valide ; ne retourne rien en cas de succes.

    Pour un rapport complet (toutes les erreurs), voir `validate_all`.
    """
    schema = _load_schema()
    validator = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    validator.validate(client)


def validate_all(client: dict) -> list[str]:
    """Retourne la liste (eventuellement vide) de tous les messages d'erreur
    de validation, chemin JSON inclus, sans lever d'exception.
    """
    schema = _load_schema()
    validator = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    errors = sorted(validator.iter_errors(client), key=lambda e: list(e.path))
    return [
        f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
        for err in errors
    ]


# ---------------------------------------------------------------------------
# Verification des references croisees (mouvements -> entry_ref)
# ---------------------------------------------------------------------------

# Categories dans lesquelles un entry_ref de mouvement peut resoudre.
_REFERENCABLE_CATEGORIES = (
    "financier_cote",
    "non_cote",
    "liquidites",
    "immobilier",
    "dettes",
    "exotiques",
    "historique_annuel",
)


def check_refs(client: dict) -> list[str]:
    """Verifie que chaque `entry_ref` des entrees `mouvements` correspond a
    un `id` existant dans une des categories referencables du client.

    Returns
    -------
    Liste des problemes rencontres (chaine vide si tout resout). Une liste
    vide signifie que toutes les references sont valides.
    """
    known_ids: set[str] = set()
    for category in _REFERENCABLE_CATEGORIES:
        for item in client.get(category, []):
            item_id = item.get("id")
            if item_id:
                known_ids.add(item_id)

    problems: list[str] = []
    for mvt in client.get("mouvements", []):
        ref = mvt.get("entry_ref")
        mvt_id = mvt.get("id", "<sans id>")
        if not ref:
            problems.append(f"mouvement {mvt_id}: entry_ref absent")
        elif ref not in known_ids:
            problems.append(
                f"mouvement {mvt_id}: entry_ref={ref!r} ne resout vers aucune entree connue"
            )
    return problems
