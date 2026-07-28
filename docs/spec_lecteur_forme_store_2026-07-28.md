# Spécification du lecteur de forme-store — A1 / L2

> 2026-07-28. Établit le joint entre le forme-store (`store_client.schema.json`, `2.0-skill`) et le
> moteur de rendu, **et l'inventaire des manques** que cette mise en regard fait apparaître.
>
> **Conclusion à lire en premier : le forme-store, en l'état, ne permet pas de reproduire le rendu.**
> Neuf manques bloquants, cinq ambiguïtés. C'est le résultat attendu de D20 — « tant que le moteur ne
> consomme pas le pivot, les extensions de schéma se décident à l'aveugle » — et c'est pour cela que A1
> est la colonne vertébrale plutôt qu'une tâche d'intendance. Écrire le lecteur avant cet inventaire
> aurait été inventer neuf extensions au fil du clavier.

---

## 1 — Le joint est étroit, et c'est une bonne nouvelle

Tout ce que le moteur lit du classeur passe par **une seule fonction** :

```python
read_sheet(wb, prefix, suffix) -> list[list]       # p2_fill.py L358
```

Elle rend des **listes positionnelles en ordre canonique**, reprojetées par `colmap` quand l'onglet y a
une entrée. Les fonctions `rows_*` et le reste de `main()` n'accèdent ensuite aux données que par
`g(row, i)`. Le contrat d'entrée du moteur est donc : *pour chaque (catégorie, entité), une liste de
lignes en ordre canonique*. Rien d'autre.

**Le moteur ne change pas** (L2). Le lecteur doit produire ces mêmes listes depuis le store. La
substitution se fait en un point : `read_sheet` dispatche selon le type de son premier argument.

Onze types d'onglet sont lus. Quatre sont reprojetés par `colmap` (`Fin coté` 22 colonnes, `Non coté` 16,
`Lignes` 9, `Mouvements` 5) ; **sept ne le sont pas** — `Liq`, `Immo`, `Dettes`, `NC Flux`, `Cours PS`,
`Produits structurés`, `Arbitrages` — et pour ceux-là **l'ordre physique des colonnes du classeur EST le
contrat**, sans aucune tolérance de réordonnancement. Le lecteur devient donc, pour ces sept, la seule
définition écrite de l'ordre attendu : elle est fixée au §3.

---

## 2 — Ce que le store couvre proprement

Là où le store a été pensé, la correspondance est directe et sans perte.

### `Lignes` ← `financier_cote[].attributes.lines[]`

| i | Sémantique | Chemin store |
|---|---|---|
| 0 | Clé contrat | *implicite* — la ligne est imbriquée dans son entrée (**mais cf. M1**) |
| 1 | Libellé | `lines[].label` |
| 2 | ISIN | `lines[].isin` |
| 3 | Valeur | `lines[].value` |
| 4 | Perf % | `lines[].perf_pct` |
| 5 | Poche | `lines[].pocket` |
| 6 | Classe Rhétorès | `lines[].class` |
| 7 | Géographie | `lines[].geography` |
| 8 | SRI | `lines[].sri` |

L'imbrication est un **gain** : la jointure par clé texte normalisée disparaît. C'est le seul endroit où
le pivot est franchement supérieur à la projection Excel.

### `Mouvements` ← `mouvements[]`

| i | Sémantique | Chemin store | Remarque |
|---|---|---|---|
| 0 | Date | `date` (ISO) | `pdate()` accepte l'ISO |
| 1 | Clé contrat | `entry_ref` (**id**) | jointure par id, plus par texte (C2) |
| 2 | Type | `type` (`versement`\|`retrait`\|`frais`) | s'aligne exactement sur `_n_mvt` 0/1/2 |
| 3 | Montant | `amount` | **cf. A4** — convention de signe |
| 4 | Commentaire | `comment` | jamais lu par le moteur |

### `Non coté` — couvert sauf trois colonnes

`label`→0, `manager`→1, `attributes.strategy`→2, `attributes.moic_target`→3, `capital_committed`→4,
`capital_called`→5, `attributes.moic_realise`→8, `value_current`→9, `classe_rhetores`→10,
`attributes.segment`→12, `attributes.duration_target`→13, `attributes.instrument_type`→15.
Manquent 6, 7, 11 et 14 — cf. §4.

### `Fin coté` — couvert pour la moitié des colonnes

`manager`→4, `custodian`→5, `management_mode`→6, `risk_profile`→7, `invest_date`→8, `pledged`→9,
`capital_invested`→10, `value_jan1`→11, `value_current`→12, `value_projected`→20, et par poche
`attributes.pockets[].{label→16, manager→4, capital_invested→10, value→12}`.

Les colonnes 17/18/19 (versement, retrait, frais) n'ont pas à figurer au store : le moteur les **dérive
déjà** des mouvements et les écrit dans la ligne (L583-587). Le lecteur les laisse à `None`. La colonne
21 (nombre de poches) se dérive de `len(attributes.pockets)`.

---

## 3 — L'ordre canonique des sept onglets sans `colmap`

Reconstitué en croisant la ligne 3 du template, les contrôles de `lint.py` et les indices réellement lus.
**Cette section est normative** : ces sept onglets n'ont aucune autre définition écrite de leur ordre.

**`Liq` (3)** — 0 intitulé du compte · 1 banque · 2 solde.

**`Immo` (8)** — 0 nom du bien · 1 fonction (RP/RS/usage/rendement) · 2 propriété ou démembrement ·
3 hypothèque · 4 loyer annuel · 5 date d'acquisition · 6 valeur d'acquisition · 7 valeur courante.
*Note de rendu : le loyer (4) est affiché en texte brut, sans formatage €.*

**`Dettes` (11)** — 0 intitulé · 1 établissement · 2 type in fine/amortissable · 3 date de souscription ·
4 montant initial · 5 taux · 6 échéance · 7 périodicité des intérêts · 8 garantie financière ·
9 capital restant dû · 10 adossement (catégorie).
*L'indice 2 de `Dettes` est présent au template et **n'a aucun consommateur** — ni `p2_fill`, ni `lint`.
Le lecteur le laisse à `None` plutôt que d'inventer une source.*

**`NC Flux` (4)** — 0 nom du fonds (jointure **exacte**, non normalisée, vers `Non coté` 0) · 1 date ·
2 type · 3 montant (toujours positif ; le sens vient du type).

**`Cours PS` (3)** — 0 date · 1 ISIN (jointure vers `Produits structurés` 1) · 2 niveau en % de l'initial.

**`Produits structurés` (12)** — 0 nom · 1 ISIN · 2 enveloppe/dépositaire · 3 nominal (**filtre : ligne
ignorée si vide**) · 4 coupon %/an · 5 date de début · 6 durée en années · 7 seuil de protection % ·
8 niveau du sous-jacent % · 9 valeur actuelle si cassé · 10 classe Rhétorès · 11 barrière de rappel %.

**`Arbitrages` (2)** — 0 date · 1 libellé (**filtre : ligne ignorée si vide**).

---

## 4 — Les manques du forme-store

Classés par ce qu'ils empêchent. **M** = manque, **A** = ambiguïté.

### Bloquants — le rendu actuel est irreproductible sans eux

| # | Manque | Conséquence |
|---|---|---|
| **M1** | `Fin coté` 1 **assureur/banque** et 2 **intermédiaire**. Le store n'a que `label`, texte libre. | M1 n'est pas une colonne d'affichage : c'est la **clé de jointure** `Lignes`/`Mouvements` (`f"{nature} — {assureur}"`), le libellé de contrat, et la clé du donut « participants ». Sans elle, ni les lignes ni les mouvements ne se rattachent à leur contrat. **C'est le manque le plus lourd.** |
| **M2** | `Fin coté` 13/14/15 — classe dominante, géographie, SRI **au niveau contrat**. | Le store ne les porte qu'au niveau `lines[]`. Or le moteur a un repli explicite pour les contrats **sans** lignes classées (L622). Ce repli perd sa source : tout contrat sans lignes tomberait sur le défaut « Actions », silencieusement. |
| **M3** | **`NC Flux` en entier.** | `mouvements.type` est un enum fermé `versement\|retrait\|frais` : **`Appel`, `Distribution`, `Appel prévu`, `Distribution prévue` n'ont aucun logement**. Sans eux : plus de séries trimestrielles par fonds, plus de TVPI/DPI/RVPI, plus d'échéancier prévisionnel. |
| **M4** | `Non coté` 11 **TRI**. | Valeur fournie par le GP, jamais calculée. Alimente `summary.tri`, `stats.tri` et le TRI consolidé pondéré. |
| **M5** | **ISIN du produit structuré**, et **`Cours PS`**. | L'ISIN est la clé de `Cours PS` *et* du snapshot `ps_status` (gel des coupons N-1). `financierCoteEntry` n'a pas d'`isin`. La jointure est impossible en l'état. |
| **M6** | `Liq`, `Immo`, `Dettes` : `genericEntry` ne déclare **aucune colonne de valeur**. | Il n'expose que `id`, `entity_id`, `label`, `source`, `source_document`, `validated_by`, `validation_note`. Manquent notamment `Dettes` 9 (capital restant dû), `Dettes` 10 (adossement) et `Immo` 7 (valeur courante) — **les trois entrent dans les contrôles comptables** (L1688-1692). `additionalProperties: true` tolère des clés libres, mais rien n'est normé, donc rien n'est fiable. |
| **M7** | Séries **`Valorisations`** (agrégat coté / non coté par date) et **`Historique`** (perf annuelle coté, non coté, commentaire). | `valuations[]` est **par position** (`position_id`) : reconstituer l'agrégat exigerait une valorisation de *chaque* position à *chaque* date, ce que rien ne garantit. `historique_annuel` est un `genericEntry` sans champ de perf, et son `entity_id` est *requis* alors que la donnée est un agrégat patrimonial. |
| **M8** | **`Arbitrages`** en entier. | Aucun logement pour les (date, libellé) des faits marquants de gestion. |
| **M9** | Commutateurs de rendu : `mode`, `show_benchmark`, `show_ps_corrige`, `subtitle`, `blocs_enabled`, et `entities[].categories`. | Vivent aujourd'hui au manifeste. `categories` est **dérivable** (les catégories ayant au moins une entrée pour cette entité) ; les autres sont des choix de rendu, pas de la donnée client — **ils ont probablement raison de rester au manifeste**, cf. §5. |

### Ambiguïtés — à trancher, pas à deviner

| # | Ambiguïté | Enjeu |
|---|---|---|
| **A1** | `Fin coté` 3 (**type de poche** : FID/FAS/FE/mono) et 7 (**profil**) sont deux sémantiques pour un seul champ candidat (`pocket.profile` / `risk_profile`). | Un mauvais choix décale deux colonnes d'affichage sans rien casser visiblement. **→ TRANCHÉ au §7.4.** |
| **A2** | Vocabulaires. `envelope_type` vaut `assurance_vie_lux` dans la fixture du store, alors que le moteur attend `av`/`capi`/`cto`/`pea`/`nominatif`. Idem `classe_rhetores` : `private_equity` vs `Private Equity`. | **Sans table de normalisation, les donuts et `NATURE` cassent silencieusement** — pas d'erreur, juste des agrégats faux. À écrire dans le lecteur, pas dans le moteur. **→ SÉVÉRITÉ RÉVISÉE au §7.5 : la fixture était l'exception, pas la règle.** |
| **A3** | Types. `moic_target`, `moic_realise`, `duration_target` sont des **nombres** au store et du **texte pré-formaté** dans l'Excel (« 1,8x », « 10y »), affiché tel quel. | Produit des **écarts de rendu attendus**, à inscrire comme tels au contrôle L3 plutôt qu'à corriger. |
| **A4** | Signe des montants de `mouvements` : la fixture du store écrit un retrait à `-20000`, le moteur applique `abs()`. | Un signe non figé est une erreur qui attend son heure. |
| **A5** | Explosion contrat → poches. Le classeur a **une ligne par poche** (nature/assureur/intermédiaire répétés) ; le store a **une entrée par contrat** avec `attributes.pockets[]`. Sur une ligne-poche, que valent 8 (date d'investissement), 9 (nantissement) et 11 (valeur 01/01), absents de `pocket` ? | Détermine si la base de perf YTD par poche est calculable. |

---

## 5 — Ce que cet inventaire dit du fork

Trois observations qui dépassent la mécanique.

**Le forme-store a été conçu pour le datahub, pas pour le rendu.** Ses points forts (lignes imbriquées,
jointure par id, discipline ABSENCE ≠ NULL) sont ceux d'un modèle de données. Ses manques sont tous du
même genre : les informations **d'origine documentaire** que le CGP recopie d'un relevé — assureur,
intermédiaire, TRI communiqué, flux d'appels et de distributions, adossement d'une dette. Le pivot a
modélisé les *positions* ; il a sous-modélisé la *provenance*.

**M6 est le plus révélateur.** Trois catégories entières — liquidités, immobilier, dettes — reposent sur
`genericEntry`, qui ne déclare aucune valeur. Elles fonctionnent aujourd'hui parce que
`additionalProperties: true` laisse passer n'importe quelle clé. C'est-à-dire qu'elles ne sont pas
modélisées : elles sont tolérées. Et deux d'entre elles entrent dans les contrôles comptables.

**L3 ne mesurera pas ce qu'on croyait.** Le critère annoncé — « rendu depuis l'Excel ≡ rendu depuis le
store » — devait *accessoirement* mesurer la perte de la projection Excel. Mais si l'on fabrique les
forme-stores **à partir des** classeurs de fixtures, l'équivalence est en partie tautologique : ce que
l'Excel perd, le store le perd aussi. Deux contrôles distincts, donc, et il faut les nommer séparément :

- **L3a — fidélité du lecteur** : store dérivé d'une fixture Excel → rendu identique. Prouvable ici,
  sans donnée client, sur les 7 fixtures. C'est aussi L4.
- **L3b — perte de la projection** : store construit depuis une vérité *plus riche* que l'Excel → écarts
  explicables un par un. **Exige les données réconciliées de Gronier, qui ne sont pas dans le fork.**

L1 (« produire un forme-store de référence pour un client réel ») n'est donc pas exécutable ici en
l'état, faute de données. L3a l'est entièrement.

---

## 6 — Ordre de travail proposé

1. **Trancher A1–A5** (cinq questions courtes ; A2 et A3 je peux les proposer, A1/A4/A5 sont des choix de
   modèle).
2. **Écrire le lecteur pour ce qui existe**, et le faire **échouer bruyamment** sur chaque manque plutôt
   que combler par un défaut. C'est l'application littérale de L5 : on consomme avant de déclarer stable.
   Un manque silencieusement comblé est un manque qu'on ne corrigera jamais.
3. **Dériver les 7 forme-stores** des fixtures Excel, prouver **L3a**, étendre la régression (**L4**).
4. **Amender le schéma** manque par manque, chacun avec son entrée au `REGISTRE_ECARTS.md` — et chacun
   validé par son propre usage, jamais par anticipation.
5. **L3b** quand les données Gronier seront disponibles.

Sur **M9**, un avis : les commutateurs de rendu (`mode`, `show_benchmark`, `blocs_enabled`) n'ont **pas**
leur place au store. Le store porte ce qui est vrai du client ; le manifeste porte ce qu'on a choisi de
montrer. Les confondre ferait du store le réceptacle de décisions éditoriales, et rendrait deux rendus
différents du même patrimoine impossibles à exprimer. Seul `entities[].categories` mérite d'être dérivé
du store, puisqu'il n'est pas un choix mais un fait.

---

## 7 — Confrontation au run Gronier réel

> Ajouté le 2026-07-28, après examen de `run_gronier_T2/` (session « Reporting skill (Gronier) »).
> Un forme-store **réel** existe : `client.store.json`, avec son manifeste, son classeur de transition et
> son HTML. Les §1 à §6 ci-dessus étaient une analyse *de schéma* ; ce §7 les confronte à la donnée.
> **Trois conclusions sont corrigées, deux manques s'ajoutent, une erreur factuelle est rectifiée.**

### 7.1 — Le store réel valide le schéma, et ce fait ne prouve rien

`schema_version` = `2.0-skill`. `Draft202012Validator` avec `FORMAT_CHECKER` : **0 erreur**.
`check_refs()` : les 4 `entry_ref` résolvent. Aucun `null` nu — la discipline ABSENCE ≠ NULL tient.

**Zéro erreur n'est pas zéro perte.** Le store passe parce que **six des dix tableaux du schéma sont
absents** — et facultatifs : `valuations`, `liquidites`, `immobilier`, `dettes`, `exotiques`,
`historique_annuel`. Et parce que `additionalProperties: true` ne contraint rien sur les entrées. La
validation du pivot ne dit *rien* sur sa capacité à porter un reporting. C'est l'argument de D20 sous sa
forme la plus nue : seul le rendu est un juge.

### 7.2 — Le run est rejouable, et il bute sur un défaut déjà tracé

`p2_fill.py` sur le couple (classeur, manifeste) du run **échoue avant même d'ouvrir le classeur** :

```
blocs_enabled: Additional properties are not allowed ('historique' was unexpected)
```

C'est exactement **T1 / D31** (renommage `blocs_enabled.historique` → `rendement_annuel`), inscrit au
registre, chantier A2. Le manifeste du run porte l'ancien nom ; le schéma du fork ne le connaît plus.

La seule clé retirée, la chaîne repasse entièrement : **contrôles comptables 9/9**, actif brut
**4 608 966 €** (3 982 294,76 coté + 626 670,92 non coté), et un diff de **9 lignes** vis-à-vis du HTML
livré — un commentaire HTML et le texte éditorial P4 injecté après coup. **Nous avons donc une référence
de rendu sur client réel, exploitable immédiatement.** Cela déplace A2 : le renommage n'est plus de
l'hygiène, c'est le prérequis d'exécution de la référence L3.

### 7.3 — Le store réel est PÉRIMÉ par rapport au classeur : L3 est piégé

|  | store | classeur | Δ |
|---|---|---|---|
| Σ coté | 3 988 765,97 € | 3 982 294,76 € | **6 471,21 €** |
| Σ non coté | 626 670,92 € | 626 670,92 € | 0 |
| FC051727 capital investi | 951 627 € | 550 750,75 € (Σ 2 poches) | **400 876 €** |
| Cardif capital | 300 000 € | 500 000 € | 200 000 € |
| Nortia capital | 1 035 000 € | 900 000 € | 135 000 € |

`rapport_apply.md` l'explique : le store est resté sur les valorisations « Catégories & Perf » du 23/07,
le classeur a été recalé le 24/07 sur les **relevés officiels** (« le versement 251 627 de C&P n'existe
pas dans l'officiel »). Les libellés de poche divergent aussi : `"1719249CA Indosuez Switzerland S.A."`
au store contre `"FAS — CA Indosuez (1719249)"` au classeur. **Le HTML livré vient du classeur.**

Conséquence directe, et elle vaut d'être dite : **un contrôle L3 sur ce couple mesurerait la dérive de
deux artefacts désynchronisés, pas la fidélité du lecteur.** Le §5 avait identifié le risque de
tautologie ; le run en révèle le symétrique — un store désynchronisé produit du bruit qu'on prendrait
pour de la perte de projection. **L3b exige un store et un classeur issus du MÊME recalage.** À défaut,
le premier travail de L3b est de régénérer le store depuis les relevés officiels.

### 7.4 — A1 tranché : deux colonnes distinctes, dans l'Excel de transition seulement

Thomas avait raison, et plus précisément qu'énoncé. Le gabarit canonique
(`skill/assets/Reporting_data_template.xlsx`, onglet `Fin coté — PP`) porte bien **deux colonnes
séparées** : index 3 `Type poche (FID/FAS/FE/Mono)` et index 7 `Profil`. Confirmé sur les 7 fixtures —
`fx_lignes_classes` a `Type poche="Mono"`, `Profil="Équilibré"`. Le consommateur est
`rows_financier_cote`, qui rend `↳ {col3} · {col4}`, conforme à `references/03-tableau-exhaustif.md`.

L'**Excel de structure** (v1, v2, Gronier — en-têtes identiques) n'a **qu'une** colonne `Profil`, **pas
de `Type poche`**, et **pas de ligne par poche** : les poches y sont un simple compteur `Nb poches
attendu`, qui sert de contrôle de réconciliation (Gronier : 1 partout sauf FC051727 = 2).

Les deux Excel sont définis au CDC v3 §L35-38 : l'**Excel de structure** est *CGP-facing, minimal*
(4 onglets : `Identité`/`Coté`/`Non coté`/`Réf`) — les ancres que le conseiller saisit, le détail étant
complété ensuite depuis les PDF ; l'**Excel de transition** est le format v5 interne, ~15 onglets,
**projection volontairement lossy** du pivot, et depuis D20 il ne subsiste que comme *surface de
rectification*.

**Décision : `pocket.type` → colonne 3, `pocket.profile` → colonne 7.** Pas de détournement de `profile`.
`pocket` est `additionalProperties: false`, l'ajout doit donc passer par un amendement du schéma, avec son
entrée au registre.

*À noter, et ce n'est pas agréable : le classeur de transition **réellement produit** pour Gronier ne
porte ni `Type poche`, ni `Intermédiaire`, ni `Géographie`, ni `SRI` au niveau contrat. C'est une variante
réduite, absorbée silencieusement par la projection d'en-têtes de `colmap`. Le rendu
`↳ [Type poche] · [Société de gestion]` s'affiche donc amputé, sans que rien ne le signale.*

### 7.5 — A2 : sévérité fortement revue à la baisse

La fixture de `test_store_builder.py` était l'exception, pas la règle. Le store réel emploie des
vocabulaires **déjà compatibles** avec le moteur : `envelope_type` vaut `AV` / `Capi` / `CTO`, et
`classe_rhetores` vaut `Dette privée` / `Private Equity`. Aucune table de normalisation nécessaire là.

Elle reste requise pour **`lines[].class`** (`actions`, `dette_privee`, `matieres_premieres`,
`monetaire`, `obligations`, `produits_structures`, `alternatifs`) et **`lines[].geography`** (`monde`,
`europe`, `emergents`, `amerique_du_nord`, `asie_pacifique`), qui sont en snake_case là où le moteur
attend les libellés d'affichage.

### 7.6 — A4 tranché, et confirmé par la donnée

`amount` est **toujours positif** dans le store réel (le retrait vaut `100000`), conforme au `abs()` du
moteur et à la convention de `NC Flux`. **Convention figée : `amount ≥ 0`, le sens vient de `type`.**
La fixture au retrait négatif est à corriger — c'est elle qui était fautive.

### 7.7 — A5 : le modèle de Thomas est le modèle du classeur, et le store en est loin

Arbitrage de Thomas : une liste au niveau du contrat portant les données par poche, l'indice 0 portant le
contrat lui-même quand il n'y a pas de poche. Le store réel s'en approche **par accident**, pas par
conception :

- `attributes.pockets[]` est **facultatif et absent 5 fois sur 7** ;
- quand il existe, `pocket` ne porte que **3 champs** (`label`, `value`, `manager`) — et `profile`,
  pourtant déclaré, est vide 3/3 ;
- `tmp_fc_007` est le précédent le plus proche : une poche unique dont la `value` égale `value_current`.
  Mais le classeur, lui, ne met aucune étiquette de poche sur ce contrat.

Or la **ligne-poche du classeur porte tout le jeu contrat** : capital investi (302 317,66 / 248 433,09),
valeur 01/01 (545 975 / 468 670), versements (250 000 / 200 000), frais (1 750 / 1 500), dépositaire,
date d'investissement, nantissement. **Aucun** des six n'a de logement dans `pocket` — c'est A5 au
complet, et c'est pourquoi la perf YTD par poche n'est pas calculable depuis le store.

**Le modèle retenu est donc bien celui du classeur**, et il demande un amendement franc de `pocket` :
`type`, `profile`, `capital_invested`, `value_jan1`, `custodian`, `invest_date`, `pledged`, et les flux
dérivés. Avec la règle d'uniformité de Thomas — **toujours au moins une poche**, l'indice 0 portant le
contrat quand il n'y en a pas — le lecteur n'a plus qu'un seul chemin de code au lieu de deux. C'est
aussi ce qui rend `Fin coté` 21 (nombre de poches) trivialement exact.

Reste, non résolu : la jointure ligne ↔ poche passe par le **libellé en texte libre**
(`lines[].pocket == pockets[].label`). Déjà au registre comme invention réelle (D16/C7, identifiant stable
de poche) — et le run le prouve nécessaire, puisque les libellés divergent entre store et classeur pour la
même poche.

### 7.8 — Verdict des neuf manques face à la donnée

| # | Verdict | Ce que le run apporte |
|---|---|---|
| **M1** | **Confirmé, et aggravé** | L'assureur est **fusionné dans `label`** en texte libre : `"Capitalisation — Wealins FC051727"` au store contre `Nature="Capi"` + `Assureur="Wealins (FC051727)"` au classeur. **Le découpage est irréversible sans heuristique.** Et `p2_fill` L629 confirme la gravité : le donut « participants » est indexé sur la colonne assureur, pas sur le libellé. |
| **M2** | Confirmé, **non exercé** | `Classe dominante` est `None` sur les 8 lignes du classeur, `Géographie` et `SRI` n'existent pas au niveau contrat dans le v5 produit. Le repli de L622 n'est jamais emprunté sur ce run : le manque tient en théorie, la donnée ne l'objective pas. |
| **M3** | Confirmé, **non exercé** | Les 3 onglets `NC Flux` du classeur sont **vides** (en-têtes seuls). `capital_called` suffit à ce run ; il ne suffirait pas à un échéancier. |
| **M4** | **Confirmé — perte PROUVÉE** | Le classeur porte `TRI (%)` = **10** (OCA MGM1) et **7** (SOMNOO S Invest Hotels 4). Rien dans le store. Le manque le mieux démontré. |
| **M5** | **Partiellement comblé, par un autre chemin** | Gronier ne passe pas par la machinerie PS : ses 3 produits structurés sont des **`lines[]` ordinaires** avec `class:"produits_structures"` **et leur ISIN**. L'ISIN a donc un logement ; la **série de niveaux en %** n'en a aucun, et le snapshot `ps_status` reste sans clé. |
| **M6** | Confirmé, **non testable** | Les trois tableaux sont absents du store, les trois onglets absents du classeur : `genericEntry` n'est **jamais instancié**. Aucune observation, ni contre-exemple, ni précédent de forme. |
| **M7** | **Confirmé — perte prouvée, et donnée orpheline** | `Valorisations` (6 lignes) et `Historique` (2025 = +6,34 %, 2024 = +4,08 %) existent au classeur, absents du store. Pire : **`cp_valos.json` porte 9 séries par contrat × 5 dates** — exactement le grain `position_id` + `date` de `valuations[]` — **hors du forme-store**. La donnée existe, le logement existe, ils ne se sont pas rencontrés. *Note : l'onglet `Historique` n'a pas de colonne « perf non coté ».* |
| **M8** | Confirmé, non exercé | Aucun onglet `Arbitrages`. |
| **M9** | **Tranché par la donnée** | Le store ne porte que `reporting.profile` ; le manifeste porte `mode`, `show_benchmark`, `show_ps_corrige`, `subtitle`, `blocs_enabled`, `entities[].categories`. **Zéro recouvrement.** Et `categories` est **exactement dérivable** du store — vérifié sur les 4 entités. L'avis du §6 se confirme : les commutateurs restent au manifeste, `categories` se dérive. |

### 7.9 — Deux manques que l'analyse de schéma n'avait pas vus

| # | Manque | Pourquoi il compte |
|---|---|---|
| **M10** | `invest_date` sur `nonCoteEntry` **n'est pas déclaré au schéma**. Le classeur porte `21/03/2025` et `30/07/2025` ; le store les a rangés **dans le texte de `validation_note`** (`"Date d'investissement 2025-03-21"`). | Une date métier réfugiée dans un commentaire libre. Non requêtable, non validable, invisible à tout contrôle. C'est le symptôme exact du diagnostic du §5 : faute de champ pour la provenance, elle se réfugie où elle peut. |
| **M11** | `moic_realise` **est déclaré au schéma et jamais rempli** (0/8), alors que le classeur porte `1,42x`, `1,79x`, `1,0x`. | Un manque d'un genre différent des dix autres : ici le logement existe. Ce n'est pas le schéma qui a échoué, c'est le remplissage. À traiter comme un défaut du constructeur de store, pas comme une extension. |

### 7.10 — Rectification d'une erreur du §4

Le §4 (**A1**, tableau des ambiguïtés) laissait entendre que `Fin coté` index 2 « Intermédiaire » était
sans consommateur. **C'est faux** : `rows_financier_cote` l'utilise comme **troisième terme de sa clé de
regroupement** `(nature, assureur, intermédiaire)` et l'affiche dans le `cdet`. La moitié
« intermédiaire » de M1 est donc plus sévère qu'écrit — deux contrats du même assureur passant par des
intermédiaires différents seraient **fusionnés** par le lecteur. Corrigé.

