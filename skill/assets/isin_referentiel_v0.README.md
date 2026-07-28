# Référentiel ISIN v0 — `isin_referentiel_v0.csv`

## Rôle

Table de correspondance **ISIN → classe d'actif Rhétorès / géographie / SRI**, utilisée par le skill
de reporting pour classifier automatiquement les lignes de portefeuille dont l'ISIN est déjà connu,
sans ressaisie manuelle à chaque nouveau run.

Colonnes :

| colonne      | contenu                                                                 |
|--------------|--------------------------------------------------------------------------|
| `isin`       | code ISIN (identifiant unique de la ligne)                               |
| `label`      | libellé du fonds/titre tel que vu dans la source                         |
| `class_code` | classe d'actif Rhétorès, code provisoire (voir liste ci-dessous)          |
| `geo_code`   | zone géographique, code provisoire — **vide** si non connue              |
| `sri`        | indicateur de risque 1-7 — **vide** si non connu                         |
| `source`     | provenance du mapping (`interagyr_valide` ou `gronier_categories`)        |
| `confidence` | `high` (validé Tristan) ou `medium` (déduit, à confirmer)                |

Une cellule vide signifie "non connu" — ne jamais écrire la chaîne `null`.

## Codes PROVISOIRES — À CONFIRMER via le canal Code avec Tristan

Ces codes sont des noms de travail choisis pour ce v0. Ils ne sont pas encore validés comme
nomenclature officielle du skill et peuvent être renommés/fusionnés avant la v1.

**Classes (`class_code`)**

| Libellé FR | Code |
|---|---|
| Actions | `actions` |
| Obligations | `obligations` |
| Monétaire | `monetaire` |
| Fonds euros | `fonds_euros` |
| Produits structurés | `produits_structures` |
| Alternatifs | `alternatifs` |
| Matières premières | `matieres_premieres` |
| Crypto | `crypto` |
| Private Equity | `private_equity` |
| Actions non cotées | `actions_non_cotees` |
| Dette privée | `dette_privee` |
| Immo non coté | `immo_non_cote` |
| Infrastructures | `infrastructures` |

**Géographie (`geo_code`)**

| Libellé FR | Code |
|---|---|
| International / Monde | `monde` |
| Amérique du Nord | `amerique_du_nord` |
| Europe développée | `europe` |
| Asie-Pacifique | `asie_pacifique` |
| Émergents | `emergents` |

## Sources utilisées pour ce v0

- **`interagyr_valide`** (confidence `high`) — feuille « Lignes — INTERAGYR » de
  `Reporting_INTERAGYR_v3.xlsx`. Classes et géographies validées par Tristan. 43 ISIN uniques.
- **`gronier_categories`** (confidence `medium`) — feuilles « Cat. des fonds » (référentiel ISIN →
  sous-catégorie) + « Lien Cat. et Sous-Cat. » (sous-catégorie → catégorie) du fichier
  `Analyse Catégories Portefeuille Global_N Gronier_23 04 2026.xlsx`. Mapping déduit, pas de
  validation Tristan — à vérifier avant tout usage en confiance haute. 212 ISIN uniques retenus.
  Cette source ne fournit pas de géographie exploitable : `geo_code` est laissé vide pour toutes
  ses lignes.
- Le fichier `Catégories et Perf HANAMI_T1 2026.xlsx` a été exploré mais **ne contient aucune
  colonne ISIN** (labels de contrats/fonds uniquement) — il n'a donc alimenté aucune ligne du
  référentiel.

En cas de doublon d'ISIN entre les deux sources, la ligne `interagyr_valide` est conservée
systématiquement (priorité qualité). Les rares cas où l'ISIN existe dans les deux sources ont été
vérifiés : aucun conflit de classe constaté sur ce run (les 15 ISIN en commun ont la même classe
dans les deux sources).

Certaines lignes de la source Gronier ont été volontairement **exclues** du référentiel car
ambiguës :
- ISIN où deux libellés/sous-catégories différentes de « Cat. des fonds » aboutissent à des
  classes contradictoires (3 ISIN : conflit interne non résolu, ex. un même ISIN catégorisé
  à la fois "Gestion alternative" et "Actions émergentes" selon la ligne).
- Sous-catégories intrinsèquement mixtes/non tranchables : « Fonds Flexible », « Fonds
  diversifié » (allocation flexible, pas une classe pure) et « Liquidités » telle que catégorisée
  dans ce fichier (le tableau de correspondance source associe ce libellé à une catégorie vide, et
  regroupe à la fois du monétaire pur et des fonds en euros mal étiquetés — ambigu).

## Process de proposition d'ajout (ISIN inconnus d'un run)

1. À chaque run du skill, tout ISIN rencontré dans les données client qui **n'est pas** déjà présent
   dans `isin_referentiel_v0.csv` doit être collecté dans une liste de diff (nouveaux ISIN +
   libellé + classe/géo si renseignées dans la source client du run).
2. Cette liste de diff est présentée à Tristan pour validation — jamais ajoutée automatiquement au
   référentiel sans son accord (règle métier Rhétorès : classes/géo doivent rester une décision
   humaine validée).
3. Une fois validée par Tristan, la ligne est ajoutée au CSV avec `source=interagyr_valide` (ou une
   source équivalente "validée manuellement") et `confidence=high`.
4. Les lignes `gronier_categories` (confidence `medium`) restent utilisables en attendant mais
   doivent être requalifiées en `high` dès qu'un humain les confirme — ne pas les traiter comme
   fiables à 100% pour des décisions reporting sensibles.
