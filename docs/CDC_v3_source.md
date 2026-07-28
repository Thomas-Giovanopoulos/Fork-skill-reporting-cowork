# CDC — Pipeline de reporting Rhétorès : du skill-agrégateur au skill-consommateur

**Version 3 — 27/07/2026.** Amende la v2 du même jour (v1 du 22/07 conservée comme référence figée).
Rédigé en atelier (Thomas × Cowork). Document de référence pour les amendements au process.

---

## Section 0 — Ce qui change depuis la v2

La v2 plaçait en tête de son chemin critique un addendum de schéma à soumettre à Code, dont tout le
reste dépendait. **Cette stratégie est abandonnée.** On ne touche pas à `validation_app` maintenant.

| | Objet | Nature du changement |
|---|---|---|
| 1 | Rapport à l'infra | Le skill **forke** et développe ses extensions de schéma unilatéralement. Retour vers Code **en une fois**, quand les formes auront été éprouvées (D18). |
| 2 | Convention de nommage | Les clés non encore bénies sont posées à leur **position canonique présumée** ; `schema_version` conserve le suffixe `-skill` ; un **registre des écarts** énumère ce qui n'est pas validé (D19). |
| 3 | O6 tranché | La divergence des sources de rendu est résolue en faveur de (b) : `p2_fill` gagne un lecteur de forme-store. Ce n'est plus un point ouvert mais le **principe directeur du fork** (D20). |
| 4 | Chemin critique | Refait. Le lecteur de store passe en premier jalon, l'addendum en dernier. L'attente d'un aller-retour avec Code disparaît. |
| 5 | Nouveaux chantiers | **L** (lecteur de forme-store) et **M** (fork, registre et convergence). |
| 6 | C5–C7 | Ne passent plus par le canal Code : décidés dans le fork, consignés au registre. |
| 7 | I2 | Le canal formel est **suspendu** pendant le fork, réactivé au retour en un seul addendum avec bump. |

---

## Section 1 — Résumé de la discussion (amendé)

### 1.1 Le constat fondateur

*Inchangé.* Le skill de reporting (`reporting-fo-rhetores-alt`) est né avant le datahub. Par nature, c'est un **consommateur** : il devrait lire des données consolidées et en faire un reporting. Faute de datahub en place, l'agrégation de données (extraction des relevés, classification, réconciliation) s'est installée *dans* le skill. C'est assumé et temporaire : on continue d'agréger ici, mais en visant une forme interne strictement compatible avec l'infra prévue, pour qu'un jour la partie agrégation soit **débranchée** sans que le reste ne s'en aperçoive.

*Lecture v3* : le fork ne contredit pas ce constat, il l'assume jusqu'au bout. Le skill était déjà en avance sur l'infra par accident ; il le devient par méthode, avec une dette explicitement tenue.

### 1.2 Le rôle de l'Excel — rétrogradé deux fois, puis une troisième

- L'Excel n'est plus la **source de vérité unique**. Pipeline validé : *Excel de structure minimal (CGP) + reportings gestionnaires/PE (PDF)* → le skill complète, réconcilie, génère.
- L'Excel de transition (format v5) est une **projection** volontairement lossy, interne au skill, rectifiable par le CGP sur demande.
- L'artefact prêt-pour-datahub d'un run = le **JSON forme-store + les diffs**, pas l'Excel.
- **Troisième rétrogradation (v3)** : avec D20, l'Excel de transition cesse d'être le porteur de données du moteur. Il ne subsiste que comme surface de rectification pour le CGP. Ce n'est plus un maillon de la chaîne de rendu, c'est une dérivation latérale.

### 1.3 L'architecture cible du skill

```
Excel de structure (CGP) + PDFs gestionnaires/PE
        │
  subagents extraction (1/document) ──► diffs (contrat validation_app :
        │                                category, entry, fields old/new,
        │                                source_page, confidence, unrecognized_data)
        ▼
  réconciliation vs structure ──► AskUser sur écarts / low confidence
        │                         (le CGP tranche ; s'il ignore, on ignore)
        ▼
  apply ──► dict client FORME-STORE  ◄────── mode (b) D6 : {client}.json direct
        │      (= le pivot interne)          (PJ à l'intérim, MCP datahub à terme)
        │
        ├──► store_to_manifest ─────────────► manifeste (blocs_enabled)      [J]
        │
        ├──► lecteur de store ──────────────► données de rendu               [L]
        │         │
        │         └──► p2_fill (structure figée de bank/) ──► HTML (livrable)
        │
        └──► writer (json_to_excel vendoré) ──► Excel de transition
                                                (rectification CGP, latéral)
```

**La couture** : tout ce qui précède le dict forme-store est le *module d'agrégation amovible*. Tout ce qui suit ne connaît que ce dict. Le jour du débranchement, le module est remplacé par un `get_client()` (via MCP datahub).

**Ce que la v3 déplace** : l'Excel de transition sort du chemin de rendu. En v2, le manifeste venait du pivot mais les données d'une projection lossy du même pivot — deux sources pour un rendu. En v3, manifeste et données viennent du même endroit, et H5 devient atteignable sans réécriture.

### 1.4 Alignement sur l'infra (rapports Code)

- **validation_app** : hub d'ingestion multi-source (PDF/Excel/XML → contrat de diff → revue CGP → store + audit). Couvre tout le patrimoine, exotiques compris. **On n'y touche pas dans ce cycle.**
- **Store Postgres** (rhetores_datastore) : jamais de client entier en une cellule JSONB. Découpage : `clients.meta` (JSONB : client, reporting, `reference_tables`, valuations, courbe_performance), `entries` (1 ligne/entrée, 10 colonnes promues + `payload` JSONB), `ignored`. 8 catégories dont `mouvements` et `historique_annuel`. Round-trip lossless (present_keys, position, version+verrou).
- **json_to_excel.py** (fo-data-store) : la bifurcation egress existante, à **vendorer**, pas à réécrire. Émet le format legacy 15 colonnes, compatible moteur grâce au colmap, mais sans les richesses v5.
- **Le contrat de diff est le format pivot d'ingestion**. Adaptation skill : pas de store → `old_value` = valeur de l'Excel de structure (ou null en création). Les diffs produits ici resteront ingérables le jour venu — **c'est le point de contact à ne pas casser pendant le fork.**
- **Ce que le fork parie, et ce qu'il ne parie pas** : `reference_tables` est déjà nommé dans le `clients.meta` côté infra ; il manque seulement au `pipeline/store_client.schema.json` du skill. Le fork ne fabrique donc pas un concept, il rattrape un concept déjà déclaré, et ne devine que la **forme d'une ligne**. Pour les inventions réelles (identifiant de poche, logement du contexte), le pari est plus large et le registre d'autant plus nécessaire.

### 1.5 Usage et positionnement

*Inchangé.* Le chat est l'atelier ; la génération de routine n'a pas besoin de LLM (chaîne Python pure et déterministe) ; Claude est irremplaçable en amont (extraction/complétion PDF) et en latéral (raffinement conversationnel). Entrée de l'atelier à l'intérim : PJ HTML + JSON forme-store. Sortie à terme : PUT/PATCH via MCP datahub. L'accès direct à la base depuis le sandbox est off-limits par design.

### 1.6 Le tri des blocs

Constat de relecture : `blocs_enabled` se décide aujourd'hui dans `excel_to_manifest.py`, en un seul littéral de dict, et **mélange trois natures de règles** :

| Nature | Question posée | Ce qui la porte aujourd'hui |
|---|---|---|
| Intention | *Veut-on montrer ce bloc ?* | `repartition` et `exhaustif` = `mode != presentee` ; `hero`, `contexte`, `supervision`, `performance`, `footer` = `True` en dur — intention implicite, jamais énoncée |
| Faisabilité | *La donnée permet-elle ce bloc ?* | `historique` = onglet Historique non vide ; `performance_nc` = une entité a un onglet non coté avec des données |
| Pertinence | *Ce bloc se justifie-t-il ?* | Rien. Un bloc PE entier s'affiche pour 0,4 % du patrimoine ; un Historique à un seul point produit un tableau d'une ligne |

Deux couplages rendent l'état actuel intenable :

1. **La faisabilité est déduite d'une topologie d'onglets** — `PREFIX_TO_CAT`, le scan des feuilles `[Catégorie] — [suffixe]`, `sheet_has_data()`. Or **A1 supprime exactement cela** (3 feuilles, colonne Entité, plus d'onglet par structure). Le mécanisme de tri est adossé à un format de fichier qui disparaît.
2. **La décision est prise après le writer**, à partir d'une projection volontairement lossy — ce qui contredit I1.

**L'argument qui tranche** est D6 : les deux modes d'entrée convergent sur le forme-store, et en mode (b) il n'y a aucun Excel. Si le tri reste dans `excel_to_manifest`, le mode consommation doit écrire un classeur puis le relire pour savoir quels blocs afficher.

À ne pas perdre : **le store répond « peut-on ? », il ne répond pas « veut-on ? ».** `repartition`, `exhaustif` et `contexte` restent gouvernés par l'intention. Le gain de D12 n'est pas « tout vient du store », c'est « les deux questions cessent d'être emmêlées ».

### 1.7 Référentiels et routage documentaire

**La table des couples partenaires existe déjà, en version dégradée et éclatée** dans `p1_engine/p2_fill.py` :

- `DEPO_COLORS` — 6 partenaires en dur, clé = libellé ; référentiel de fait du donut Partenaires ;
- `ENV_COLORS` — les 7 enveloppes ;
- `envelope(nature, depo)` — la domiciliation est déduite de `depo == "NC"` littéral. **« Non communiqué » sert de proxy pour « France »** : un dépositaire simplement non renseigné bascule le contrat en AV FR. C'est un faux silencieux, pas une approximation.

Le couple *(assureur, dépositaire)* est déjà lu ligne par ligne, il n'est jamais confronté à un référentiel.

**Sur le routage**, D14 tranche : le relevé énonce lui-même qu'il porte sur une poche de gestion du contrat X. Le document transporte donc la jointure, et le couple n'a pas à porter l'identité de la poche. Cela *résout* la question de granularité plutôt que de la reporter : les poches restent en `attributes.pockets`, puisque le routage n'en dépend plus.

Deux réserves à encoder :

- **La référence contrat est la clé primaire, la table des couples le validateur de repli.** Chez Gronier, la lignée des poches a dû être reconstituée (Intesa→Indosuez, CIC→Quintet) depuis le relevé annuel Wealins : la référence au contrat peut être présente sans que les libellés de poche soient stables d'un relevé à l'autre.
- **C'est le libellé de poche qui dérive**, et c'est lui qui sert de clé de regroupement (colonne 16 du Fin coté). Sans identifiant stable, deux relevés successifs créent deux poches → D16.

Rôle net de la table, le routage sorti de son périmètre : normaliser les raisons sociales et leurs alias tels qu'ils apparaissent dans les PDFs, porter les successions datées, dériver la domiciliation et l'enveloppe, et coter mécaniquement la `confidence` d'un rattachement (couple exact = high, alias = medium, partenaire inconnu = low → AskUser B3, `unrecognized_data`, proposition d'ajout). Ce circuit est **rigoureusement le mécanisme E3 des ISIN** : deuxième table, même gouvernance.

### 1.8 Le fork : pourquoi, et à quelles conditions *(nouveau)*

**Pourquoi.** La v2 faisait dépendre tout le programme d'un aller-retour avec Code, alors qu'on ne connaît pas encore la bonne forme d'une ligne de partenaire. Formaliser avant d'avoir construit, c'est se condamner à bumper `schema_version` deux fois. On apprend la forme en la consommant — d'où D20, qui met le lecteur de store en tête plutôt qu'en fin de parcours : chaque extension est alors validée par son propre usage et non par intuition.

**À quelles conditions.** Le merge HANAMI vient de montrer ce que coûte une branche isolée : il n'a été sûr que grâce à un registre — tableau de md5, description fichier par fichier, protocole d'écriture. Ce registre a été rédigé *à la fin*, au prix d'une session perdue par saturation de contexte. Un fork de schéma présente le même risque à un niveau où les md5 ne servent à rien, puisque la divergence y est **sémantique**.

D'où la seule condition non négociable : **le registre des écarts s'écrit dans un fichier du fork, tenu au fil de l'eau, jamais reconstitué à la fin.** Il est l'addendum du jour du retour. Tenu régulièrement il ne coûte presque rien ; laissé s'accumuler il redevient une session perdue.

Deux conventions mineures qui suivent :

- Le fork est nommé **par son sujet**, pas par un client. HANAMI portait un nom de client pour du travail moteur, ce qui a brouillé la lecture au moment du merge.
- Le **contrat de diff est le point de contact à préserver** : c'est par lui que les runs du fork resteront ingérables. Les extensions peuvent enrichir le forme-store ; elles ne doivent pas déformer le contrat de diff.

### 1.9 Décisions actées

D1 à D11 : *voir v1.* D12 à D17 : *voir v2.* Ajouts du 27/07 (deuxième atelier) :

| # | Décision |
|---|----------|
| D18 | On ne touche pas à `validation_app` dans ce cycle. Le skill forke et développe ses extensions unilatéralement ; retour vers Code **en une fois**, quand les formes auront été éprouvées sur un run réel. |
| D19 | Convention du fork : les clés non encore bénies sont posées à leur **position canonique présumée** ; `schema_version` conserve le suffixe `-skill` (précédent déjà en place dans `store_builder.py`) ; un **registre des écarts** énumère les clés non validées, avec leur justification. Le registre constitue l'addendum. |
| D20 | O6 est tranché en faveur de (b) : **`p2_fill` gagne un lecteur de forme-store**, et ce lecteur est le premier livrable du fork. L'Excel de transition sort du chemin de rendu et ne subsiste que comme surface de rectification. |
| D21 | Le registre des écarts est un **fichier du fork tenu au fil de l'eau**. Aucune décision de schéma unilatérale n'est prise sans y être consignée dans le même mouvement. |

---

## Section 2 — État des lieux du code au 27/07

### 2.1 Ce qui est livré et vérifié

Paquet de référence : le merge HANAMI du 27/07 — 118 entrées, `selfcheck` OK, régression **7/7** fixtures (QC 9/9, déterministe), jsdom **24 assertions OK**, audit post-zip intégral sans anomalie.

Acquis moteur, stables et hors chantier :

- colmap bi-format (lecture par en-têtes), cascade KPI, Mouvements, agrégations par lignes ;
- Dietz modifié, en KPI et par contrat, sur deux horizons (YTD et origine) ;
- tableau Historique du patrimoine à 9 colonnes, réconciliable ligne à ligne ;
- poches reconstruites depuis les étiquettes de l'onglet Lignes, avec versements/retraits/frais par poche ;
- non coté scindé Fonds / Titres (`attributes.instrument_type`), multiples portefeuille recalculés sur les fonds seuls ;
- référentiel ISIN v0 : 261 lignes, 177 `geo_code` complétés et validés CGP le 24/07.

### 2.2 Dette technique constatée

| # | Constat | Effet |
|---|---|---|
| T1 | **Collision de noms** : `blocs_enabled.historique` désigne le bloc *Rendement annuel*, alors que le tableau *Historique du patrimoine* vit dans le bloc `supervision`. | Deux objets distincts, un seul mot. Quiconque écrit le mapping store→manifeste se tromperait naturellement. À renommer avant J. |
| T2 | **Documentation périmée** : `manifest.schema.json` annonce sept blocs en « ordre canonique figé », alors que `BLOCK_ORDER` (assemble.py) en compte neuf, avec `performance_nc` et `historique` intercalés après `performance`. | Un lecteur qui se fie au schéma se trompe sur l'ordre. Correction documentaire. |
| T3 | **`run_tests.py` écrit en dur dans `/tmp/_reg*`.** Des fichiers résiduels d'un run antérieur appartenant à un autre utilisateur font remonter un `PermissionError` en `CalledProcessError` nu, sans message. | Le symptôme ressemble à une régression moteur alors qu'il n'en est pas une. Correctif : `tempfile.mkdtemp()`. |
| T4 | **`jsonschema` 3.2.0** par défaut dans les sandbox, alors que `store_builder.py` exige ≥ 4.x (`Draft202012Validator`). | `selfcheck` le détecte et le signale. `pip install -U jsonschema` dans tout nouvel environnement. |

---

## Section 3 — CDC : les points à tacler

### Chantier A — Excel de structure (CGP-facing, minimal)

- [ ] **A1.** 3 feuilles : **Identité**, **Coté** (1 ligne = 1 contrat, colonne Entité), **Non coté** (1 ligne = 1 fonds). ⚠️ *A1 supprime la topologie d'onglets dont dépend le tri actuel : A1 ne peut pas être livré sans J.*
- [ ] **A2.** Colonnes coté minimales : entité, nature, banque, gérant, nature de gestion, profil, date d'invest., capital investi, valeur si connue.
- [ ] **A3.** Poches : **jamais saisies** par le CGP. Colonne optionnelle « Nombre de poches attendu » = contrôle de réconciliation.
- [ ] **A4.** PS : une ligne d'ancrage (nature, nominal, enveloppe), expansée par le skill. Convention anti-double-compte à verrouiller.
- [ ] **A5.** Catégories hors périmètre présentée (liq/immo/dettes/exotiques) : acceptées, transitent vers le forme-store, ignorées par le rendu présentée.
- [ ] **A6.** La colonne « Type (Fonds/Titre) » du non coté doit survivre à la refonte. Rappel : les validations de données ne survivent pas à openpyxl — les recréer en natif après toute retouche.

### Chantier B — Extraction & réconciliation

- [ ] **B1.** Un subagent par document PDF (parallélisables, contexte isolé). Sortie = contrat de diff JSON, validé par jsonschema avant toute écriture.
- [ ] **B2.** Profil skill du contrat de diff : `old_value` = valeur structure ou null ; `source_page` systématique ; `unrecognized_data` alimenté.
- [ ] **B3.** Réconciliation : écart hors tolérance ou confidence low → **AskUser**. Décision du CGP appliquée et tracée. Jamais de correction silencieuse.
- [ ] **B4.** Pièges à encoder dans les prompts : PDFs sans filets de tableaux, artefacts verticaux (Dauphine), reclassements métier (fonds monétaire classé « Obligations » chez PPT), formules Excel du CGP (charger data_only), lignes de légende ℹ/• en zone de données.
- [ ] **B5.** **Capter la référence de rattachement énoncée par le relevé** (D14) : contrat X, et le cas échéant la poche. Champ de sortie obligatoire du subagent, pas une déduction de la réconciliation.
- [ ] **B6.** **Coter la `confidence` depuis le référentiel partenaires** (K) : couple exact = high, alias = medium, inconnu = low. Aujourd'hui la cotation dépend du jugement du subagent, donc non reproductible.
- [ ] **B7.** *(v3)* **Ne pas déformer le contrat de diff.** C'est le point de contact avec `validation_app`, qu'on n'amende pas dans ce cycle : les enrichissements du fork vont dans le forme-store, pas dans le contrat.

### Chantier C — Pivot forme-store & extensions de schéma

*Amendement v3 : ces extensions ne passent plus par le canal Code. Elles sont décidées dans le fork, posées à leur position canonique présumée, et consignées au registre (D19, D21).*

- [ ] **C1.** Le skill émet le dict client forme-store. Ids `tmp_`, `_provisional_ids: true` dans le meta.
- [ ] **C2.** Extensions à poser dans le fork :
  - `payload.attributes.lines: [{isin, label, value, class, geography, sri, pocket}]` et `pockets: [...]` sur les entries `financier_cote` ;
  - `entry_ref` (entry_id du contrat) sur les entrées `mouvements` — remplace la jointure par clé texte ;
  - `unit` sur `meta.valuations` (niveaux PS en %, pas en €) ; valuations par `position_id` ;
  - attributs PS dans le payload (coupon, seuils, barrière…).
- [ ] **C3.** Discipline : codes `reference_tables` partout ; absence ≠ null ; ordre des listes stable.
- [ ] **C4.** Fixer les ids provisoires de Gronier et INTERAGYR. *Devient prérequis de L1, qui a besoin d'un forme-store réel comme fixture.*
- [ ] **C5.** **Créer `meta.reference_tables` dans `store_client.schema.json`.** Position canonique (la clé est déjà nommée côté infra), inscrite au registre.
- [ ] **C6.** **Loger la donnée du bloc Contexte.** Invention réelle, pas un rattrapage : à motiver au registre (cf. O7).
- [ ] **C7.** **Identifiant stable de poche** (D16), distinct du libellé d'affichage. Invention réelle, à motiver au registre.

### Chantier D — Writer & Excel de transition

*Amendement v3 : le writer sort du chemin de rendu (D20). Il reste utile, mais son urgence baisse.*

- [ ] **D1.** Vendorer `json_to_excel.py` dans le skill (asset). Gouvernance de la copie : O4.
- [ ] **D2.** Compléter la sortie avec les feuilles v5 absentes du legacy : Lignes classées, Mouvements, PS enrichis, poches.
- [ ] **D3.** L'Excel de transition reste rectifiable : les corrections du CGP repassent par le circuit diff, pas d'écriture directe dans le pivot.
- [ ] **D4.** Dossier de run archivé : JSON forme-store + diffs + Excel de transition + HTML. Rejouable à l'import datahub.

### Chantier E — Référentiel ISIN

- [ ] **E1.** Asset CSV : `isin → {label, class_code, geo_code, sri}`. **Livré en v0** (261 lignes).
- [x] **E2.** Amorce Gronier + INTERAGYR. *Fait : 177 geo_code validés CGP le 24/07.*
- [ ] **E3.** Mécanisme « propositions d'ajout » : les ISIN inconnus d'un run sortent en diff à valider (Tristan) avant intégration.
- [ ] **E4.** Cible : table du datahub dont l'asset est le snapshot.
- [ ] **E5.** Mutualiser E3 avec le circuit partenaires (K3) : un seul mécanisme pour les deux référentiels.

### Chantier F — Expositions géographiques

*Inchangé.* Hiérarchie de sources (titres vifs → siège ; ETF → indice du nom ; fonds actifs → ventilation gestionnaire, sinon zone dominante, sinon **non tagué**) ; donut affichant la **couverture** ; V1 à une zone par ligne, look-through proportionnel différé.

### Chantier G — Moteur (périmètre volontairement minimal)

- [ ] **G1.** **Inliner Chart.js + polices** (base64, sous-setting OFL, ~350 Ko/document). Consultation hors-ligne, pourrissement d'URL, chaîne d'approvisionnement, reproductibilité. **Avant le premier PUT en base.**
- [x] **G2.** Colmap, cascade KPI, Mouvements, agrégations : livrés et testés.
- [ ] **G3.** Corriger T1 (collision `historique`) et T2 (description périmée) **avant** d'écrire `store_to_manifest`.
- [ ] **G4.** Sortir `envelope()` de sa déduction `depo == "NC"` → domiciliation lue du référentiel partenaires (dépend de K).

### Chantier H — Couture & intégration infra

- [ ] **H1.** SKILL.md : spécifier le **double mode d'entrée** (D6) — détection structure+PDFs vs `{client}.json`.
- [ ] **H2.** Intérim : PJ HTML + JSON à l'entrée de l'atelier.
- [ ] **H3.** Cible : MCP datahub — GET client, PUT/PATCH reporting. Jamais d'accès direct à la base.
- [ ] **H4.** À spécifier au retour vers Code : table `reportings` (client_id, date, mode, html TEXT, source_json JSONB, generated_by).
- [ ] **H5.** Le débranchement final : suppression du module d'agrégation, zéro impact en aval. *D20 le rend atteignable sans réécriture du moteur.*

### Chantier I — Gouvernance & méthode

- [ ] **I1.** Toute évolution du reporting se définit d'abord comme une forme dans le dict store, jamais comme une colonne Excel.
- [ ] **I2.** Canal formel : addendum écrit → revue Code → store.template.json + CDC + bump `schema_version`. **Suspendu pendant le fork** (D18) ; réactivé au retour, en un seul passage alimenté par le registre.
- [ ] **I3.** Banc d'essai de bout en bout : **INTERAGYR** (PDFs disponibles, structure connue, trois versions de vérité à réconcilier).
- [ ] **I4.** Ordre d'exécution : *voir section 4.*

### Chantier J — Tri des blocs

- [ ] **J1.** Écrire `store_to_manifest.py` : entités depuis le store, `blocs_enabled` calculé, mêmes garde-fous métier que `assemble.validate` (au plus 1 PP, PP en tête, ids uniques).
- [ ] **J2.** Établir le **tableau de faisabilité** bloc par bloc. Cas à trancher explicitement — `supervision` (valuations + classification), `performance` (courbe + indices, donnée externe), `contexte` (aucun logement, cf. C6).
- [ ] **J3.** Séparer l'intention : `mode` reste porteur de `repartition`/`exhaustif` ; expliciter les `True` en dur qui sont de l'intention déguisée.
- [ ] **J4.** Appliquer D17 : un bloc sans donnée est désactivé, jamais rendu en squelette. Revoir les templates qui « restent en mode squelette » par défaut.
- [ ] **J5.** `excel_to_manifest.py` conservé en legacy, sans évolution.
- [ ] **J6.** Ne pas toucher `assemble.compute_layout` : il prend déjà un `blocs_enabled` opaque et renumérote seul.

### Chantier K — Table des couples partenaires

- [ ] **K1.** Contenu : code canonique, **rôle** (assureur / dépositaire / gérant / plateforme — Nortia est un grossiste, pas un assureur), alias tels qu'ils apparaissent dans les PDFs, domiciliation, **successions datées**, et les **couples admissibles**.
- [ ] **K2.** Logement : `meta.reference_tables` du store, à sa position canonique (C5), inscrit au registre.
- [ ] **K3.** Circuit « partenaire inconnu » : `unrecognized_data` + proposition d'ajout à valider, mutualisé avec E3/E5.
- [ ] **K4.** Retirer les référentiels de fait du moteur : `DEPO_COLORS`, `ENV_COLORS`, et la déduction `depo == "NC"` de `envelope()` (cf. G4). Les couleurs restent une préoccupation de rendu ; la liste des partenaires ne vit plus dans `p2_fill.py`.
- [ ] **K5.** Les successions doivent permettre de réconcilier un relevé antérieur à un changement de nom (cas Wealins FC051727 / relevé 2024).

### Chantier L — Lecteur de forme-store *(nouveau — colonne vertébrale)*

- [ ] **L1.** Produire un **forme-store de référence pour un client réel** (Gronier, déjà réconcilié) et en faire la fixture du lecteur. Prérequis : C4 (ids provisoires).
- [ ] **L2.** Écrire le lecteur : du dict forme-store vers les structures de données que `p2_fill` consomme aujourd'hui depuis le classeur. Le contrat de sortie est celui qui existe déjà — le moteur ne change pas.
- [ ] **L3.** **Équivalence de rendu prouvée** : pour un même client, rendu depuis l'Excel et rendu depuis le store doivent être identiques (ou leurs écarts explicables un par un). C'est le test qui valide le lecteur, et accessoirement il mesure la perte réelle de la projection Excel.
- [ ] **L4.** Étendre la régression : les 7 fixtures actuelles sont des classeurs. Prévoir leur pendant forme-store, ou une conversion à la volée, pour que les deux chemins soient testés.
- [ ] **L5.** Chaque extension de C2 est livrée **lecteur d'abord** : on la consomme avant de la déclarer stable. C'est ce qui rend les décisions de schéma honnêtes plutôt qu'intuitives.

### Chantier M — Fork, registre et convergence *(nouveau)*

- [ ] **M1.** Créer le fork, nommé **par son sujet** (pas par un client), à partir du paquet mergé du 27/07.
- [ ] **M2.** Créer le **registre des écarts** dès le premier commit : une entrée par décision de schéma unilatérale — clé, position, forme, justification, statut (rattrapage d'un concept déjà nommé côté infra / invention réelle), et ce qu'il faudrait pour la faire bénir.
- [ ] **M3.** Tenir le registre **au fil de l'eau** (D21). Aucune clé posée sans son entrée dans le même mouvement.
- [ ] **M4.** Maintenir le suffixe `-skill` sur `schema_version`. Ne jamais revendiquer un numéro officiel.
- [ ] **M5.** Préserver le contrat de diff intact (B7).
- [ ] **M6.** Protocole de merge, tiré de HANAMI : tableau de md5 base→cible, écriture par copie et jamais par l'outil d'édition, vérification après chaque écriture, audit du paquet fichier par fichier. À écrire **avant** d'en avoir besoin.
- [ ] **M7.** Au retour vers Code : l'addendum est le registre, relu et ordonné. Un seul passage, un seul bump.

---

## Section 4 — Chemin critique

L'ordre de la v2 est refait : il commençait par un aller-retour avec Code dont tout dépendait. Le fork le supprime.

| Jalon | Contenu | Pourquoi ici |
|---|---|---|
| **① Fork et registre** | M1–M4. Quelques minutes de mise en place. | Rien de ce qui suit ne doit être posé hors registre |
| **② Lecteur de forme-store** | L1–L4, avec C4 en prérequis. | La colonne vertébrale (D20). Tant que le moteur ne consomme pas le pivot, les extensions se décident à l'aveugle |
| **③ Hygiène préalable** | G3 (T1 collision, T2 doc périmée). | À faire avant d'écrire le mapping, sinon il hérite de la confusion |
| **④ Tri des blocs** | J1–J6. | Manifeste et données viennent enfin du même endroit |
| **⑤ Référentiels** | C5, K1–K5, E3/E5. | Un seul circuit de proposition d'ajout pour les deux tables |
| **⑥ Structure 3 feuilles** | A1–A6, le tri désormais affranchi de la topologie d'onglets. | Débloqué par ④ |
| **⑦ Extraction & profil diff** | B1–B7, `confidence` cotée depuis K. | Débloqué par ⑤ |
| **⑧ Writer & feuilles v5** | D1–D2. | Plus dans le chemin de rendu : urgence retombée |
| **⑨ Run INTERAGYR de bout en bout** | I3. | Éprouve les formes sur trois versions de vérité |
| **⑩ Retour vers Code** | M7, H4. | Les formes sont éprouvées ; l'addendum s'écrit tout seul |

**Ce que ce réordonnancement gagne** : plus aucune attente externe. Le premier jour de travail est productif, et chaque forme de schéma est validée par un usage réel avant d'être soumise.

**Ce qu'il coûte** : une dette explicite, portée par le registre, et un merge à faire un jour. C'est exactement le prix qu'on a déjà payé sur HANAMI — la différence est qu'on le sait d'avance et que M6 est écrit avant d'en avoir besoin.

---

## Section 5 — Points ouverts

| # | Sujet | État |
|---|-------|------|
| O1 | Propriété de l'egress à terme : le skill consomme le JSON (et garde json_to_excel), ou l'infra sert l'Excel/le HTML ? | Thomas y réfléchit. *D20 fait pencher vers « le skill consomme le JSON ».* |
| O2 | UUID vs autre pour les ids définitifs | Différé, non bloquant (D7) |
| O3 | Drop de l'export Excel dans la validation_app | Sensible politiquement, en réflexion |
| O4 | Gouvernance du vendoring `json_to_excel` | À trancher avec Code, au retour |
| O5 | Ids provisoires Gronier / INTERAGYR | *Devient bloquant : prérequis de L1 (C4).* |
| ~~O6~~ | ~~Divergence des sources de rendu~~ | **Tranché par D20** : `p2_fill` lit le store, l'Excel sort du chemin de rendu |
| O7 | Le bloc Contexte est-il alimenté depuis le store (C6), ou reste-t-il une entrée de run fournie à chaque génération ? | Non tranché. Conditionne J2 et une entrée du registre |
| O8 | Seuils de pertinence (D13) : à partir de quelle part du patrimoine un bloc PE se justifie-t-il ? Combien de points pour un Historique ? Seuils codés, ou proposition + AskUser ? | Non tranché |
| O9 | *(v3)* Jusqu'où le fork peut-il aller avant que le merge ne devienne déraisonnable ? Un critère d'arrêt vaut mieux qu'un constat tardif — par exemple : retour vers Code dès que le registre dépasse N entrées, ou dès qu'une extension touche le contrat de diff. | Nouveau, à trancher |
