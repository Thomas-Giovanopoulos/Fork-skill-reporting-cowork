---
name: reporting-fo-rhetores-alt
description: >
  VERSION ALTERNATIVE (alt) du skill de reporting Family Office Rhétorès Finance. NE PAS confondre avec le skill
  standard "reporting-fo-rhetores". Déclencher ce skill UNIQUEMENT lorsque l'utilisateur demande EXPLICITEMENT la
  version alternative — par ex. : "reporting alt", "version alternative", "skill alt", "reporting-fo-rhetores-alt",
  ou "la nouvelle version du reporting FO". En l'absence de mention explicite de la version alternative, NE PAS
  déclencher ce skill et laisser le skill standard "reporting-fo-rhetores" prendre la main. Une fois déclenché, ce
  skill produit un reporting patrimonial consolidé de type Family Office (collecte des données, classification des
  actifs, génération du dashboard HTML) selon les règles métier validées par Tristan (dépositaires, classes d'actifs,
  géographie OPC, architecture tableau, colonnes immo/non coté) et fournit un template Excel de collecte des données
  (assets/Reporting_data_template.xlsx).
---

# Reporting Family Office Rhétorès Finance — VERSION ALTERNATIVE (pipeline)

> **Version alt.** Ce skill est né *avant* le datahub Rhétorès. Par nature il devrait être un
> **consommateur** (lire des données consolidées, produire un reporting) ; faute d'infra, il fait
> aussi l'**agrégation** (extraction des relevés, classification, réconciliation). C'est assumé et
> temporaire : le module d'agrégation est construit pour être **débranchable sans impact aval** le
> jour où le datahub sert un JSON forme-store directement. Tout ce qui suit le pivot forme-store
> (writer → moteur P1-P4 → HTML) est inchangé et ne connaît que ce dict.

---

## 0 — Mode d'entrée : à détecter EN PREMIER

**Étape 0 obligatoire, avant toute autre action** : exécuter `python3 p1_engine/selfcheck.py` depuis
la racine du skill (~1 s). Il compile chaque `.py`, parse chaque `.j2`/`.json`, vérifie taille + md5
de chaque fichier contre `CHECKSUMS.json`, et contrôle la version de `jsonschema` (Draft 2020-12
requis par `store_builder.py`). **Si le self-check échoue : STOP** — le paquet installé est corrompu
(bug connu de copie à l'installation : fichiers tronqués en fin) ; ne pas réparer à la main en
silence, signaler au CGP et réinstaller le `.skill` (ou relancer l'application) avant de continuer.

| Signal en entrée | Mode | Action |
|---|---|---|
| Un `{client}.json` conforme à `store_client.schema.json` (PJ, ou plus tard servi par le MCP datahub) | **CONSOMMATION** | Sauter directement à l'**Egress** (§2.e) : writer → moteur P1/P2 → HTML. Ne pas relancer l'extraction. |
| Un Excel de structure (3 feuilles) + des PDFs de relevés du coté (le PE vient de la feuille Non coté, jamais de PDFs — §2.a) | **AGRÉGATION** | Dérouler la **boucle complète** (§2). |
| Les deux à la fois (JSON existant + nouveaux PDFs) | **AGRÉGATION en ré-entrée** | Le JSON fourni devient la base « old » de la réconciliation (§2.c) au lieu de l'Excel de structure. |
| Rien de tout ça | — | AskUser : demander l'Excel de structure + les relevés, ou le JSON forme-store existant. En cas de doute, demander confirmation plutôt que supposer. |

---

## 1 — Vue d'ensemble du reporting produit

Un reporting Rhétorès (**version présentée**) est un **document HTML autonome**. Ordre canonique des
blocs (numérotation 00, 01… calculée automatiquement selon les blocs activés) :

```
Hero / Chiffres clés          — identité client + Capitaux sous supervision
Bloc 00 — Contexte de marché  — Macro, faits marquants, benchmark indices
Bloc 01 — Patrimoine sous supervision — KPI + 4 donuts (classes/coté-non coté, géographie, enveloppes, partenaires)
Bloc 02 — Étude de la performance (coté) — KPI, courbe mensuelle, commentaire, tableau par contrat en accordéon
Bloc — Performance non coté (Private Equity) — CONDITIONNEL — barres trimestrielles, panneau de composition
Bloc — Répartition patrimoniale — Tableau global + mini-donuts + cards entités
Bloc — Tableau exhaustif — Détail ligne à ligne par entité
Footer
```

Fork **`reporting.mode`** : `presentee` (défaut, figée, animation Hero) ou `envoyee` (WIP, stub sans
animation) — toute divergence de l'envoyée passe par une condition `mode`, jamais par une modif du
chemin `presentee`.

**Nomenclature** — Reporting (`consolide_HG_v15.html`) › Bloc (00, 01, Hero…) › Widget (tableau,
card, donut) › Élément (ligne, part de donut, KPI) › Ligne/Colonne/Cellule (HTML standard).

→ Détails : `references/01-architecture-blocs.md`, `references/03-tableau-exhaustif.md`,
`references/04-charte-visuelle.md`

---

## 2 — La boucle d'agrégation (mode AGRÉGATION)

```
Excel de structure (CGP) + PDFs relevés coté (PE : feuille Non coté seule)
        │
  subagents extraction (1 par document, PARALLÈLE obligatoire — §2.b) ──► diffs JSON
        ▼
  réconciliation vs structure ──► AskUser sur écarts / low confidence
        ▼
  apply ──► dict client FORME-STORE (pivot interne, ids tmp_)
        ▼
  writer ──► Excel de transition (sur demande)
        ▼
  moteur P1/P2 (inchangé) ──► reporting HTML (le livrable)
```

**La couture** : tout ce qui précède le dict forme-store est amovible ; au débranchement, remplacé par un `get_client()` via MCP datahub, sans toucher au reste.

### a. Lire l'Excel de structure

Excel **minimal** à 3 feuilles fourni par le CGP — ce n'est plus la source de vérité unique, juste le
squelette + les ancres de réconciliation :

- **Identité** : entités (pp/holdings), labels, profil de risque, date du reporting.
- **Coté** : **1 ligne = 1 contrat** (plus d'onglet par structure). Colonnes minimales : entité,
  nature, banque, gérant, nature de gestion, profil, date d'invest., capital investi, valeur si
  connue. Le reste (lignes détaillées, classes, géo) vient des PDFs.
- **Non coté** : 1 ligne = 1 fonds/titre — et c'est la **source exclusive et complète du PE**. Colonnes :
  entité, gérant, nom du fonds, capital engagé, capital appelé, segment, stratégie, multiple cible
  (format `1,8x`), durée cible (format `10y`), date d'investissement, MOIC, TVPI, **Type (Fonds/Titre)**.
  Le Type est structurant : **Fonds** = véhicule à engagement/appels (Altaroc…) → colonnes engagé/appelé/
  MOIC pertinentes, inclus dans les multiples agrégés ; **Titre** = détention directe ou via support
  (OCA, obligations, actions non cotées) → suivi au nominal avec TRI cible, rendu dans une sous-section
  dédiée, exclu des multiples MOIC/TVPI. Store : `attributes.instrument_type` (fonds|titre). **Ne jamais lire
  ni parser les rapports des fonds de PE** (relevés GP, quarterly reports…) : ces documents sont
  trop complexes pour le gain attendu — décision d'architecture, pas une limitation. Si une colonne
  attendue est vide (engagé, appelé, segment, stratégie, cible, durée, MOIC…), poser la question au
  CGP via **AskUserQuestion** plutôt que d'aller chercher dans un rapport ou d'inventer. Les
  subagents d'extraction (§2.b) ne concernent donc que les relevés du **coté**.

Règles :
- **Poches jamais saisies** par le CGP. Colonne optionnelle « Nombre de poches attendu » = contrôle
  de réconciliation (attendu vs trouvé), pas une description.
- **Produits structurés (PS)** : une ligne d'ancrage dans Coté (nature = « Produit structuré »,
  nominal, enveloppe) ; le skill l'expanse vers PS/Cours PS de l'Excel de transition.
  **Anti-double-compte** : la ligne d'ancrage migre entièrement, jamais comptée comme position coté
  ordinaire — contrôle comptable dédié à l'étape d.
- Chaque valeur de cette feuille devient la valeur **« old »** de la réconciliation (§2.c).

### b. Un subagent par PDF (impératif — bloquant, pas une option)

Périmètre : **relevés du coté uniquement** (banques, gestionnaires de mandats). Les rapports de
fonds de PE sont **hors périmètre** — le non coté vient exclusivement de la feuille Non coté (§2.a).

**Protocole d'exécution, dans cet ordre strict** :

1. Lister **tous** les documents PDF du run, sans en ouvrir aucun. Écarter d'office les rapports
   de fonds PE (les signaler au CGP comme non traités, sans les ouvrir).
2. Dans **un seul message**, émettre **N blocs d'appel Agent (Task)** — un par document. Ne jamais
   envoyer un premier subagent, attendre son retour, puis en envoyer un second : les N appels
   partent ensemble.
3. **Ne jamais lire ou parser le contenu d'un PDF dans le fil principal** — même « pour se faire une
   idée » avant de déléguer. C'est strictement le rôle du subagent. Le fil principal ne fait que
   lister, dispatcher, puis consolider les diffs reçus (§2.c).

**Pourquoi cette règle est non négociable** : un run traité PDF-par-PDF en série (lecture inline ou
subagents lancés un par un) a été mesuré à **~25 min pour 4 documents**. En parallèle réel (étape 1
ci-dessus), la durée de cette étape tombe à celle du **plus lent des 4 subagents**, pas à leur somme
— gain attendu de l'ordre de 4×. Si l'environnement d'exécution ne dispose pas de l'outil Agent/Task,
le signaler explicitement au CGP plutôt que de basculer silencieusement en lecture séquentielle
dans le fil principal (dégradation à tracer, pas à cacher).

Contexte isolé par source (pas de contamination entre relevés). Chaque subagent lit son PDF et
**seulement** son PDF, puis émet un **contrat de diff JSON** validé contre le schéma de diff (profil
`skill_v1` : `old_value` = valeur de l'Excel de structure, ou `null` en création — pas d'accès au
store).

Le prompt de chaque subagent doit inclure, sans les paraphraser :

1. **Le référentiel ISIN** (`assets/isin_referentiel_v0.csv` — §7) : **priorité absolue**
   pour classe/géographie/SRI dès que l'ISIN y figure. Ne jamais improviser une classe si l'ISIN est
   référencé.
2. **Les règles géo** (`pipeline/GEO_RULES.md`) : hiérarchie de sources — référentiel ISIN →
   titre vif (pays du siège) → ETF (indice du nom) → fonds actif (ventilation gestionnaire ou nom) →
   sinon **non tagué**, jamais de géo fausse. Une zone par ligne en v1, pas de look-through.
3. **Les codes classes/géo** : classes `actions`, `obligations`, `monetaire`, `fonds_euros`,
   `produits_structures`, `alternatifs`, `matieres_premieres`, `crypto`, `private_equity`,
   `actions_non_cotees`, `dette_privee`, `immo_non_cote`, `infrastructures` ; géo `monde`,
   `amerique_du_nord`, `europe`, `asie_pacifique`, `emergents`.
4. **Pièges de parsing par source** (à reprendre tels quels, pas à redécouvrir) :
   - **PPT (de Pury Pictet)** — pas de filets de tableau ; « RESULTAT YTD » affiche deux %, le bon
     est la **2ᵉ ligne** (résultat depuis achat) ; fonds monétaires classés à tort « Obligations » →
     reclasser `monetaire`.
   - **Dauphine AM** — filigrane vertical qui pollue le texte extrait (« U s e a x g … ») ; totaux
     imprimés ne somment pas exactement (**±1-2 €**, à absorber sur Liquidités) ; +/-value affichée
     **hebdomadaire, pas YTD** — ne pas confondre avec un autre relevé YTD du même run.
   - **Excel CGP en entrée** — formules saisies par le CGP → charger `data_only=True` depuis le
     fichier **original** (une resauvegarde openpyxl détruit le cache de formules) ; ignorer les
     lignes de légende `ℹ`/`•` en zone de données.
5. **Performance par ligne (obligatoire dès que le relevé la publie)** :
   - **PPT (de Pury Pictet)** — colonne « RESULTAT YTD » : deux valeurs empilées, retenir la
     **2ᵉ ligne** (résultat *depuis achat*, en EUR). Reporter en `perf_pct` de la ligne.
   - **Dauphine AM** — colonne « +/- % » du détail des positions : c'est la variation *de la
     période du relevé* (hebdomadaire ici), **pas** un YTD. Reporter en `perf_pct` et préciser
     l'horizon dans `validation_note`.
   - Renseigner `perf_pct` pour **toute ligne titre/fonds**. Seules les lignes de **liquidités /
     compte courant** peuvent rester sans performance. Une perf % absente produit un `0 €` / `—`
     silencieux dans le rendu (la Perf € est dérivée par le moteur) — ne jamais laisser vide par
     défaut.
6. **Σ lignes = total ± 1 €** : tout écart est **absorbé sur une ligne Liquidités** du contrat
   (jamais réparti au prorata, jamais ignoré) et **documenté** dans les `notes` du diff.

Sortie attendue : un fichier de diff conforme à `diff_contract.schema.json`, `unrecognized_data`
peuplé pour tout ce qui ne rentre dans aucun champ (rien ne se perd en silence).

**Noms de champs des lignes — canoniques, pas de variantes** : dans les `new_value` du chemin
`attributes.lines`, utiliser exactement les noms du `$defs.line` de `pipeline/store_client.schema.json` :
`label`, `value`, `class` (obligatoires), `isin`, `perf_pct`, `geography`, `sri`, `pocket` (optionnels).
Deux runs réels ont produit des variantes (`value_eur`/`valuation_eur`, `class_code`/`asset_class`,
`geo_code`) — normalisées à l'apply, mais c'est une variance à éviter à la source : inclure cette
liste dans le prompt de chaque subagent, copiée du schéma (pas de mémoire).

**Multi-mandats même Nature — même Banque** (cas fréquent, ex. 4 CTO UBS confiés à 4 gérants) : la
clé de jointure contrat `Nature — Banque` ne les distingue pas. **Ne jamais trancher seul** — c'est
un **AskUserQuestion obligatoire** : « poches d'un même contrat, ou comptes séparés ? ». Si le CGP
répond *poches* → un contrat unique à N poches (une poche par mandat/gérant, lignes rattachées).
Si *comptes séparés* → garder N contrats distincts, en désambiguïsant la colonne banque pour que les
clés diffèrent (ex. « UBS (Dauphine — Offensif) », « UBS (De Pury Pictet) »). Indice mais pas
preuve : des lignes séparées dans l'Excel de structure suggèrent des comptes séparés — la question
reste obligatoire.

### c. Réconciliation

Comparer chaque diff à la valeur d'ancre de l'Excel de structure (ou du JSON en ré-entrée). **Tout
écart hors tolérance ou toute entrée `confidence: low`** déclenche un **AskUserQuestion** — jamais de
correction silencieuse. Le CGP tranche. **S'il dit d'ignorer un écart, on ignore — mais on trace**
(dans les `notes` du diff et le rapport d'apply) : qui a décidé, et pourquoi.

### d. Apply — consolidation forme-store

Consolider les diffs validés en dict client **forme-store** via `pipeline/store_builder.py` (§7) :

- Chaque ligne classée (`attributes.lines[]`) doit porter `perf_pct` dès que la source la publie
  (chemin de diff : `attributes.lines[].perf_pct`). Le champ existe déjà au schéma
  (`pipeline/store_client.schema.json`, `$defs.line.perf_pct`) — ne pas l'omettre à l'extraction.

- Ids provisoires préfixés par catégorie (`tmp_fc_`, `tmp_nc_`, `tmp_mv_`…), `_provisional_ids: true`
  dans le meta. **Le skill ne stamp jamais d'id définitif.**
- **Absence ≠ null** : une donnée non renseignée est une clé **absente**, jamais une clé présente à
  `None` (sauf null explicite volontaire, sentinelle `EXPLICIT_NULL`).
- `validated_by` = email de session du CGP sur chaque entrée modifiée/créée ; `source_document` sur
  chaque entrée.
- Valider avant écriture : `validate_all()` (conformité schéma) puis `check_refs()` (intégrité des
  références, ex. `entry_ref` des mouvements).
- Ce qui ne rentre dans aucun champ (`unrecognized_data` des diffs + champs droppés à l'apply) va
  dans un **fichier séparé** (`unrecognized.json`) — jamais perdu, jamais forcé au prix d'un champ
  inventé.
- Tout ISIN classé pendant le run et absent du référentiel → **proposition d'ajout** en diff distinct
  (§4), jamais écrit directement dans `isin_referentiel_v0.csv`.

### e. Egress — writer, moteur, HTML

1. **Writer** : projeter le dict forme-store vers l'**Excel de transition** (format
   `Reporting_data_template` v5 : Identité/Coté/Non coté + Lignes classées + Mouvements + PS +
   Contrôles). Projection **lossy**, interne au skill, rectifiable par le CGP **sur demande** — pas
   l'artefact d'archive (§3).
   > **Note d'étape** : le writer officiel `json_to_excel.py` n'est **pas encore vendoré** (chantier D
   > du CDC, arbitrage de gouvernance en attente). En attendant, générer l'Excel de transition selon
   > le format v5 existant (`p1_engine/colmap.py` lit les deux formats). Correction du CGP sur cet
   > Excel → **repasse par le circuit diff**, jamais d'écriture directe dans le pivot.
2. **Moteur** : `excel_to_manifest.py` puis `p2_fill.py` sur l'Excel de transition — pipeline P1-P4 inchangé (§5).
3. Avant de livrer : les **9 contrôles comptables** de `p2_fill.py` doivent tous passer (« Contrôles comptables : X/9 OK »). Ne pas livrer sur un contrôle en échec sans le signaler.

---

## 3 — Livrables d'un run

- **Le HTML** : seul livrable présenté par défaut.
- **L'Excel de transition** : uniquement **sur demande** explicite du CGP.
- **Le dossier de run archivé** : diffs (1/document) + `client.store.json` + `unrecognized.json` + rapport d'apply + HTML + **store de période** `contexte/<période>.json` (§5, P4 — réutilisé, jamais regénéré, pour tout autre client de la même période). C'est cet ensemble, pas l'Excel, qui est **rejouable à l'import datahub**.

---

## 4 — Règles transverses

- **Aucun stamp d'id définitif** : le skill n'écrit jamais dans le datahub, il produit des artefacts
  (`tmp_*`, diffs) qu'un processus de validation externe transforme en ids définitifs.
- **ISIN inconnus** → propositions d'ajout au référentiel, à valider par **Tristan**. Jamais
  d'écriture directe dans `isin_referentiel_v0.csv` pendant un run.
- **Présentée = version principale, figée** ; divergences envoyée systématiquement gated par
  `reporting.mode != 'presentee'`.
- **Contrôles comptables 9/9 obligatoires** avant de livrer un HTML (§2.e).
- **Écart de réconciliation → AskUser, jamais de correction silencieuse** (règle d'or, §2.c).

---

## 5 — Le moteur : pipeline P0-P4 (inchangé, condensé)

Pipeline déterministe par phases, chacune produisant un artefact validé avant la suivante. Règle de
ré-entrée : toute modification de données ré-entre en **P2**, jamais en P1 — le squelette validé ne
se régénère pas.

| Phase | Régime | Rôle | Artefact |
|---|---|---|---|
| **P0 — Cadrage** | jugement humain | Nombre/nom des entités, personnalisation de l'Excel. En mode agrégation, couvert par la feuille Identité (§2.a). | Fiche de cadrage |
| **P1 — Structure** | déterministe, figé | `p1_engine/assemble.py manifest.json squelette.html` : ordre des blocs, charte CSS, jeux de colonnes — figés dans `p1_engine/bank/`. | Squelette HTML vide validé |
| **P2 — Remplissage** | automatisé + 1 îlot | `excel_to_manifest.py` puis `p2_fill.py` : détail, sous-totaux, KPIs, donuts, Bloc Performance. Seul jugement humain : classification M1-M5, capturée en **donnée d'entrée**, pas au rendu. | HTML rempli |
| **P3 — Cohérence** | vérification | Assurée par construction (mêmes sources pour les 5 zones). Vérifier qu'aucun `data-slot` ne reste à `—` et que Σ nets catégories = actif net total. | HTML cohérent |
| **P4 — Polissage** | additif, bridé | Bloc 00 via le **store de période** (voir ci-dessous) — copié verbatim, jamais regénéré. **Commentaire de gestion obligatoire en présentée** (le placeholder ne part jamais chez un client ; un QC éditorial le signale). **Arbitrages** : uniquement l'onglet Arbitrages validé par le CGP — jamais les transactions des relevés (un achat dans un mandat n'est pas un arbitrage). | `consolide_[Client].html` final |

**Store de période (Bloc 00 — Contexte de marché)** : le contenu éditorial du Bloc 00 (macro 5 §,
faits marquants, indices) est chargé par `p2_fill.py` depuis `contexte/<période>.json` (chemin
surchargeable via l'argument `ctx_path`). **Un store validé est vendoré dans le paquet**
(`contexte/S29 2026.json`) : pour tout reporting de cette période, il se **copie-colle tel quel** —
aucune regénération, aucune « amélioration », aucun ajout. Protocole : (1) chercher le store de la
période (dans le paquet, puis dans le dossier de travail) ; s'il existe, l'utiliser verbatim ;
(2) s'il n'existe pas (nouvelle période), le produire **une fois** puis l'archiver (§3). Contrat de
contenu pour une nouvelle période : le texte macro est un commentaire **de marché** (macro, taux,
actions, matières premières, crypto), sourcé du commentaire de marché des lettres gérants (Dauphine
AM en publie chaque semaine) + niveaux d'indices YTD fiables — **jamais** l'actualité des lignes du
client, **jamais** de méta-texte (« store produit à partir de… ») dans un slot rendu, **jamais**
d'indices laissés à « — » sans le signaler au CGP. Clés : `macro_text` (liste de §),
`faits_marquants` (tag/tone/text), `indices` (name/var/ytd).

→ Détails : `p1_engine/README.md`, `p1_engine/README-pont-P2.md`, `p1_engine/manifest.schema.json`

---

## 6 — Index des références

| Sujet | Fichier | Rôle |
|---|---|---|
| Template Excel structure/transition | `references/08-template-excel.md` | Structure, workflow, conventions |
| Architecture des blocs | `references/01-architecture-blocs.md` | Les 5 blocs, nomenclature widget, specs Hero/Bloc 00 |
| Tableau exhaustif | `references/03-tableau-exhaustif.md` | Colonnes par type d'actif, nomenclature Financier coté |
| Charte visuelle | `references/04-charte-visuelle.md` | Palette, polices, CSS, config Chart.js || Classification | `references/02-classification.md` | 12 classes Rhétorès, M1-M5, géographie — **lookup ISIN d'abord** (§2.b) |
| Mappings fonds | `references/06-mappings-fonds.md` | Fonds déjà validés (spécifique-client) |
| Cas particuliers | `references/07-cas-particuliers.md` | Saint Honoré Innovation, "Autres invest" UBS, GAMA vs DNCA, flux |
| Formalisme | `references/09-formalisme.md` | Libellés, casse, format montants/%/dates, couleurs |
| Cohérence globale | `references/05-coherence-globale.md` | Règle des 5 zones (P3) |
| Règles géographie | `pipeline/GEO_RULES.md` | Hiérarchie de sources géo, v1 sans look-through (§2.b) |
| Contrat de diff | `pipeline/diff_contract.schema.json` | Schéma de sortie des subagents d'extraction (§2.b) |
| Schéma forme-store | `pipeline/store_client.schema.json` | Schéma cible du dict pivot (§2.d) |
| Constructeur forme-store | `pipeline/store_builder.py` | `new_client`/`add_entry`/`validate_all`/`check_refs` (§2.d) |

---

## 7 — Fichiers à disposition (assets)

- `assets/Excel_structure_v2.xlsx` — template de l'**Excel de structure** (Identité / Coté / Non coté
  + Réf) à remettre au CGP en début de run. Feuille Non coté enrichie (segment, stratégie, multiple
  cible `1,8x`, durée `10y`, MOIC, TVPI) = **source exclusive du PE** (§2.a).
- `assets/Reporting_data_template.xlsx` — template Excel v5 (transition), à adapter par
  client en P0.

**Assets intégrés au paquet** :
- `assets/isin_referentiel_v0.csv` + `.README.md` — ISIN → classe/géo/SRI, priorité absolue en §2.b.
- `pipeline/GEO_RULES.md` — règles d'exposition géographique.
- `pipeline/diff_contract.schema.json`, `pipeline/store_client.schema.json`, `pipeline/store_builder.py`
  — contrat de diff et pivot forme-store (validés par `pipeline/test_store_builder.py`).

**Writer egress (§2.e) — état actuel** : le writer officiel `json_to_excel.py` de l'infra n'est pas
encore vendoré (en attente côté équipe Code, cf. CDC chantier D). En son absence, produire l'Excel de
transition en respectant le format v5 (voir `assets/Reporting_data_template.xlsx` et `p1_engine/colmap.py`
pour les en-têtes reconnus par catégorie) — un writer générique dédié reste à construire.

Tant que ces fichiers n'ont pas été copiés dans le skill, les charger depuis leur emplacement de
travail actuel ; ne pas bloquer un run en leur absence, mais le signaler.
