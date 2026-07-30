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

### Étape 0-bis — charger les référentiels partagés (D36)

**Toi, l'agent, appelles le MCP ; le pipeline, non.** Les scripts Python tournent dans un sandbox sans
réseau : ils ne peuvent joindre ni Postgres ni un serveur MCP. C'est à toi de rapatrier les
référentiels et de les **écrire sur disque** — après quoi le pipeline les lit comme un fichier. C'est
ce qui rend un run **reproductible** : deux exécutions du même dossier rendent le même HTML, et le
bundle devient une pièce du dossier archivé.

Si le connecteur **`referentiels-rhetores`** est disponible :

1. appeler `ref_bundle(sections=["gabarits", "acteurs", "successions"])` — **demander les sections**,
   ne pas tout prendre : le bundle complet dépasse la taille qu'un résultat d'outil peut porter, les
   ISIN en faisant à eux seuls près de 70 % ;
2. écrire la réponse telle quelle dans **`referentiels.json`**, à la racine du dossier de run ;
3. le pipeline la trouvera seul (`pipeline/referentiels.py`).

Si le connecteur est **absent ou en échec** : ne pas bloquer. Le paquet embarque un repli,
`assets/referentiels_snapshot.json` — mais **le dire au CGP**, en une phrase :

> « Référentiels lus depuis le snapshot embarqué (figé à l'installation) : un gabarit validé depuis
> n'y figure pas. »

Ce n'est pas une formalité. Tout l'objet de D36 est qu'un gabarit validé par un CGP soit visible au
run suivant d'un autre **sans réinstallation** ; un repli silencieux annulerait ce bénéfice sans que
personne ne s'en aperçoive. `pipeline/referentiels.py` signale la provenance de son côté — ton rôle est
de la relayer au CGP.

**Les ISIN restent hors de ce bundle**, à dessein : ils vivent dans `assets/isin_referentiel_v0.csv`
(§7), qui reste leur source et que tu continues de lire comme avant. Les charger deux fois créerait
deux copies à faire diverger.

### Étape finale — relayer les propositions de gabarit (D36 / N5)

La lecture du bundle (0-bis) ouvre la boucle ; ceci la referme. Pendant l'identification des relevés,
`pipeline/producteur_propositions.py` compare chaque document aux gabarits connus et, quand un document
**ne s'apparie à aucun** ou reste **ambigu**, écrit une entrée dans **`propositions.json`** à la racine
du dossier de run. Le pipeline n'a pas le réseau : ces propositions sont donc à **toi** de les relayer.

En fin de run, si `propositions.json` existe :

1. pour chaque entrée de `propositions`, appeler **`ref_propose`** avec ses champs
   (`cible`, `nature`, `cle`, `proposition`, `source_empreinte`, `source_gabarit`, `source_arrete`,
   `run_id`) — ils sont déjà au bon format ;
2. **vérifier la réponse** : `provenance_recue` doit renvoyer l'empreinte que tu as passée. Si un
   `avertissement_provenance` apparaît, ton client ne connaît pas le contrat d'outil courant —
   rafraîchir la liste des outils (relancer Cowork) avant de rejouer, sinon la provenance est perdue ;
3. les entrées de `illisibles` ne sont **pas** des propositions : les remonter au CGP (document image,
   OCR requis), sans appeler le MCP.

Un run ne **canonise jamais** un gabarit : il propose (D34). C'est l'admin qui arbitre. Et une
proposition ne porte **aucune donnée client** (D44) — seulement une empreinte, des codes de gabarit et
des scores ; le texte des relevés reste dans le dossier de run. Ne complète jamais une proposition avec
un extrait de document pour « aider » l'arbitre : ce serait rouvrir la fuite que D44 ferme.

| Signal en entrée | Mode | Action |
|---|---|---|
| Un `{client}.json` conforme à `store_client.schema.json` (PJ, ou plus tard servi par le MCP datahub) | **CONSOMMATION** | Sauter directement à l'**Egress** (§2.e) : `store_to_manifest.py` + `p2_fill.py` **directement sur le JSON** — aucun Excel intermédiaire. Ne pas relancer l'extraction. |
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

**Nomenclature** — Reporting (`consolide_client_exemple_v15.html`) › Bloc (00, 01, Hero…) › Widget (tableau,
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
2. **Identifier chaque document AVANT de dispatcher** (B10 — déterministe, pas un jugement) :
   ```
   python3 pipeline/producteur_propositions.py <profils> <doc.pdf> [arrêté AAAA-MM-JJ]
   ```
   ou par lot via `pipeline/matcher_gabarit.py` (`apparier`), les profils venant du
   `referentiels.json` du run (étape 0-bis), l'arrêté du contexte du run — jamais du nom de
   fichier. Quatre verdicts, quatre traitements :
   - **`apparie`** → le subagent sera **primé** par ce profil (étape 4 ci-dessous) ;
   - **`ambigu` / `aucun`** → le document est **extrait quand même**, en prompt générique
     (sans hints — signaler dans le diff `notes` que l'extraction n'était pas primée), et la
     proposition part dans `propositions.json` (étape finale, §0) ;
   - **`illisible`** → OCR requis : signaler au CGP, ne pas dispatcher.
3. Dans **un seul message**, émettre **N blocs d'appel Agent (Task)** — un par document. Ne jamais
   envoyer un premier subagent, attendre son retour, puis en envoyer un second : les N appels
   partent ensemble.
4. **Ne jamais lire ou parser le contenu d'un PDF dans le fil principal** — même « pour se faire une
   idée » avant de déléguer. C'est strictement le rôle du subagent. Le fil principal ne fait que
   lister, identifier (métadonnées et texte via le matcher, jamais d'interprétation), dispatcher,
   puis consolider les diffs reçus (§2.c).

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
4. **Le PROFIL DE GABARIT apparié (B10/N3) — c'est lui qui porte les pièges, plus ce fichier.**
   Depuis le `referentiels.json` du run, section `gabarits`, l'entrée du verdict d'appariement.
   Copier dans le prompt du subagent, **verbatim, sans paraphrase ni tri** :
   - `extraction_hints.pieges` — les pièges de parsing de CE gabarit (filigranes, colonnes
     ambiguës, lignes repliées, conventions numériques…). Ils ont été établis sur documents
     réels ; un piège « qui ne semble pas s'appliquer » se copie quand même.
   - `extraction_hints.ancrage_tableaux` et `extraction_hints.format_numerique` — où sont les
     tableaux, comment se lisent les nombres.
   - `champs_publies` — ce que CE gabarit publie : `perf_par_ligne` = `oui` → `perf_pct`
     obligatoire sur toute ligne titre/fonds, la `forme` dit quelle colonne et l'`horizon` va
     dans `validation_note` ; `derivable` → dériver (la forme dit comment) ; `non` → ne pas
     inventer, le comblement éventuel est un choix explicite (D40). Seules les lignes de
     liquidités/compte courant peuvent rester sans perf.
   - `invariant_controle` — à vérifier **avant** d'émettre le diff (B8/D25) : au centime sauf
     tolérance déclarée dans l'invariant lui-même. Invariant en échec = le diff part quand même,
     avec l'échec **signalé** dans `notes` — un signal, jamais une correction silencieuse.
   Un document non apparié (verdict `ambigu`/`aucun`) s'extrait **sans** ce bloc, en le disant
   dans `notes`. Mettre à jour un piège = mettre à jour le **profil** (proposition → arbitrage,
   §0 étape finale), jamais ce fichier : c'est ce qui fait qu'un piège appris par un CGP profite
   au suivant.
5. **Excel CGP en entrée** (générique, hors profils) — formules saisies par le CGP → charger
   `data_only=True` depuis le fichier **original** (une resauvegarde openpyxl détruit le cache de
   formules) ; ignorer les lignes de légende `ℹ`/`•` en zone de données.
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
clés diffèrent (ex. « UBS (Gérant A — Offensif) », « UBS (Gérant B) »). Indice mais pas
preuve : des lignes séparées dans l'Excel de structure suggèrent des comptes séparés — la question
reste obligatoire.

### c. Réconciliation

Comparer chaque diff à la valeur d'ancre de l'Excel de structure (ou du JSON en ré-entrée). **Tout
écart hors tolérance ou toute entrée `confidence: low`** déclenche un **AskUserQuestion** — jamais de
correction silencieuse. Le CGP tranche. **S'il dit d'ignorer un écart, on ignore — mais on trace**
(dans les `notes` du diff et le rapport d'apply) : qui a décidé, et pourquoi.

### d. Apply — consolidation forme-store (outillé depuis B-ii, 30/07)

L'apply n'est plus un geste manuel : deux outils déterministes portent la consolidation.

```
python3 pipeline/valider_diff.py diff1.json diff2.json …          # forme + règles (A4, vocabulaire)
python3 pipeline/appliquer_diffs.py base.json sortie.json diff*.json \
    --arrete 2026-06-30 --referentiels referentiels.json \
    --documents contexte_docs.json --rapport rapport_apply.json
```

`--documents` vient de l'étape d'identification (§2.b étape 2) : `{source_document: {empreinte,
gabarit, arrete}}`. L'apply pose la **provenance D49** sur chaque entrée touchée, attribue les
**`pocket.id`** (la jointure par libellé meurt à l'entrée), résout **`assureur` → code acteur**
par les alias (non résolu = verbatim conservé + à proposer via K3, jamais de code inventé), et
signale les lignes sans `perf_pct` quand le gabarit la publie (**MQ11**). Règle dure : un
`old_value` qui ne correspond pas au store est un **CONFLIT** — champ non appliqué, rapporté
pour la réconciliation (§2.c), **jamais de last-write-wins**. Lire le rapport avant de
continuer : conflits et acteurs non résolus sont des décisions à prendre, pas du bruit.

Rappels qui restent à la charge du run :

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

### e. Egress — moteur direct sur le store (bascule ⑤, 30/07)

1. **Moteur, directement sur le store** — plus aucun Excel intermédiaire (D45/D46) :
   ```
   python3 p1_engine/store_to_manifest.py {client}.json manifest.json --quarter T2 --year 2026
   python3 p1_engine/p2_fill.py {client}.json manifest.json reporting.html
   ```
   `p2_fill` reconnaît un `.json` comme forme-store (2.1-skill) et le lit par la façade
   `lecteur_store.py` ; le moteur lui-même est inchangé. **Équivalence prouvée** avec l'ancien
   chemin Excel : manifeste et HTML identiques à l'octet près sur les 7 fixtures
   (`p1_engine/tests/test_l3a.py`, rejouable).
   > Un store qui échoue au lecteur (enveloppe inconnue, poche non résolue, `attributes.ps`
   > présent — machinerie PS pas encore lisible depuis le store) échoue **bruyamment** avec le
   > chemin exact : signaler au CGP, ne jamais contourner en regénérant un Excel à la main.
   > L'ancien chemin (`excel_to_manifest.py` + `p2_fill.py` sur un Excel de transition) reste
   > fonctionnel pour la **reprise de classeurs historiques** uniquement — il n'est plus le
   > chemin nominal, et le writer `json_to_excel` est abandonné (D46) : on ne produit plus
   > d'Excel de transition. Correction du CGP → **circuit diff**, jamais un classeur.
2. Avant de livrer : les **9 contrôles comptables** de `p2_fill.py` doivent tous passer (« Contrôles comptables : X/9 OK »). Ne pas livrer sur un contrôle en échec sans le signaler.

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
