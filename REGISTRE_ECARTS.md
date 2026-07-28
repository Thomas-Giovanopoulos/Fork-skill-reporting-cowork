# Registre des écarts du fork

> **Ce fichier est l'addendum du jour du retour vers Code** (M7). Il énumère toute clé, table ou forme
> posée **unilatéralement** par le fork, sans validation de l'infra.
>
> **Règle non négociable (D21)** : aucune décision de schéma n'est prise sans son entrée ici, **dans le
> même mouvement**. Jamais reconstitué à la fin — c'est la leçon HANAMI, où le registre rédigé après
> coup a coûté une session entière par saturation de contexte.

## Comment lire une entrée

| Champ | Sens |
|---|---|
| **Clé / objet** | le nom exact posé, à sa position |
| **Position** | où il vit (fichier, table, chemin dans le JSON) |
| **Statut** | `rattrapage` = le concept est déjà nommé côté infra, on ne devine que la forme · `invention` = concept nouveau, pari plus large |
| **Justification** | pourquoi c'était nécessaire maintenant |
| **Pour le faire bénir** | ce qu'il faudrait côté Code pour l'officialiser |

`schema_version` conserve le suffixe **`-skill`** tant que ce registre n'est pas soldé (D19/M4). On ne
revendique jamais un numéro officiel.

---

## Entrées

### R1 — `meta.reference_tables`

| | |
|---|---|
| **Clé / objet** | `meta.reference_tables` |
| **Position** | `skill/pipeline/store_client.schema.json` |
| **Statut** | **rattrapage** |
| **Justification** | La clé est **déjà déclarée** dans `clients.meta` côté infra (rapport Code : `client, reporting, reference_tables, valuations, courbe_performance`), mais absente du schéma du skill. Sans elle, aucun logement pour les codes canoniques (C3, C5). |
| **Pour le faire bénir** | Confirmer la forme d'une ligne pour chacune des trois tables. Voir R2 — une question de modélisation reste ouverte. |

### R2 — Portée de `reference_tables` : globale vs par client

| | |
|---|---|
| **Clé / objet** | portée de `reference_tables` |
| **Position** | question de modélisation, pas encore une clé |
| **Statut** | **invention** (par défaut, en attendant l'arbitrage) |
| **Justification** | Le CDC place `reference_tables` dans `clients.meta`, donc **par client**. Or les référentiels du skill (acteurs, gabarits, ISIN) sont **globaux, transverses aux clients** : les loger par client les dupliquerait N fois. Le fork tranche provisoirement pour une **base séparée** (D33), ce qui évite de préjuger. |
| **Pour le faire bénir** | Décision Code : le `reference_tables` de `clients.meta` est-il un instantané dénormalisé des codes utilisés par ce client (et le maître vit ailleurs), ou faut-il un logement global dédié ? |

### R3 — Base de référentiels séparée + rôles Postgres

| | |
|---|---|
| **Clé / objet** | base `rhetores_ref` (nom à confirmer), schéma `ref`, tables `acteurs`, `acteur_successions`, `gabarits`, `isin`, `adjudications`, `ref_meta` ; rôles `ref_app` / `ref_admin` |
| **Position** | `infra/ddl_referentiels_v0.sql` |
| **Statut** | **invention** |
| **Justification** | Il faut un store partagé pour que l'apprentissage d'un CGP profite aux autres sans réinstallation (D36). Base **séparée** de la projection du datahub pour ne pas polluer ses tables (D33). La séparation « proposer ≠ canoniser » (D34) est portée par des **GRANT Postgres** et un rôle de connexion `NOINHERIT` : un bug applicatif ne peut pas canoniser à la place d'un CGP. |
| **Pour le faire bénir** | Replier le contenu dans le datahub une fois R2 tranché ; décider si les rôles survivent ou sont remplacés par l'authz applicative. |

### R4 — Profil de gabarit

| | |
|---|---|
| **Clé / objet** | table `gabarits` : clé `(emetteur_code, gabarit, periodicite)`, colonnes `signature`, `extraction_hints`, `champs_publies`, `invariant_controle`, `template_id_natif`, `emetteur_lisible` |
| **Position** | `infra/ddl_referentiels_v0.sql` §5 |
| **Statut** | **invention**, mais **dérivée de 11 cas réels** — pas d'une intuition |
| **Justification** | Nécessaire pour identifier un document par son contenu (D24) et pour primer l'extraction. La forme vient de l'étude empirique du 27/07 : signature en trois couches, nombre de pages exclu du matching, périodicité discriminée par un token de libellé. Voir `docs/etude_signature_gabarits_2026-07-27.md`. |
| **Pour le faire bénir** | Éprouver sur un run réel (jalon A9, INTERAGYR), puis soumettre la forme stabilisée. |

### R5 — `attributes.instrument_type`

| | |
|---|---|
| **Clé / objet** | `payload.attributes.instrument_type` (valeurs : `Fonds`, `Titre`) |
| **Position** | `skill/pipeline/store_client.schema.json` |
| **Statut** | **invention** — déjà posée avant l'ouverture du fork (merge HANAMI) |
| **Justification** | Scinde le non coté : la grammaire des fonds (engagé/appelé/MOIC/cible) ne s'applique pas à une obligation non cotée. Effet mesuré : les multiples portefeuille recalculés sur les fonds seuls passent de ~1,0× à 1,53×/1,52× chez Gronier — la performance réelle des fonds devient visible. |
| **Pour le faire bénir** | Soumettre avec le lot ; la valeur est démontrée sur un cas réel. |

### R6 — `tri_decisions` au manifeste

| | |
|---|---|
| **Clé / objet** | `tri_decisions` |
| **Position** | manifeste (`skill/p1_engine/manifest.schema.json`) + dossier de run |
| **Statut** | **invention** |
| **Justification** | Le tri d'étage 3 relève de l'intention et se décide par un AskUser batché au run (D30). Sans persistance, deux runs du même client divergeraient selon l'humeur du répondant. La réponse devient une **donnée du run**, reproductible et auditable. |
| **Pour le faire bénir** | Décider si le tri est une propriété du reporting (table `reportings`, H4) ou du client. |

### R7 — `extraction_hints.segments` : documents composites

| | |
|---|---|
| **Clé / objet** | `segments` dans `extraction_hints` d'un profil de gabarit |
| **Position** | `infra/ddl_referentiels_v0.sql` §5 (colonne JSONB) · `seed/gabarits.json` (profil Wealins) |
| **Statut** | **invention**, mais **sans coût structurel** : `extraction_hints` est déjà une colonne JSONB, aucune modification de DDL |
| **Justification** | Décision **O11**. Le relevé annuel Wealins est la concaténation de 4 sous-templates aux paginations locales distinctes. Deux modélisations étaient possibles : un profil par sous-template (matching par segments, couche supplémentaire) ou un profil composite. Retenu : **un profil, avec segments déclarés**, et le **drift évalué par segment**. Un seul appariement, donc pas de couche de matching en plus ; mais une évolution de la seule page Loi Pacte ne remet pas en cause tout le profil et produit une proposition `mise_a_jour` ciblée. Deux éléments empiriques justifient ce découpage : les frontières sont détectables au caractère près et se sont vérifiées **identiques sur deux exemplaires de tailles très différentes** (26 p./2 FID et 15 p./1 FID) ; et la page Loi Pacte porte un **pied de page au numéro de fax différent**, preuve qu'elle est produite par un autre générateur — donc de cycles de vie indépendants. |
| **Pour le faire bénir** | Vérifier sur un second émetteur composite si le cas se présente. Aucun autre des 7 profils du seed n'en a besoin : ne pas généraliser prématurément. |

---

## À inscrire dès qu'on y touche

Ces écarts sont **décidés** mais pas encore posés dans le code. Chacun devra recevoir son entrée
complète au moment de l'implémentation, pas avant, pas après.

| Objet | Décision | Chantier |
|---|---|---|
| `attributes.lines[]` et `pockets[]` sur `financier_cote` | C2 | A1/L5 |
| `entry_ref` sur les entrées `mouvements` | C2 — remplace la jointure par clé texte | A1/L5 |
| `unit` sur `meta.valuations` + valuations par `position_id` | C2 — niveaux PS en %, pas en € | A1/L5 |
| Attributs PS dans le payload (coupon, seuils, barrière) | C2 | A1/L5 |
| Identifiant stable de poche, distinct du libellé | D16 / C7 — **invention réelle** | A1 |
| Logement de la donnée du bloc Contexte | C6 / O7 — **invention réelle**. Orienté le 28/07 : la donnée **vit dans le store** (précédent INTERAGYR). La forme du logement reste à discuter — c'est elle, et non le principe, qui conditionne A3. | A3 |
| Renommage `blocs_enabled.historique` → `rendement_annuel` | D31 — clôt la collision T1 | A2 |
| `insurer` / `intermediary` sur `financier_cote` | **M1** — clé de jointure `Lignes`/`Mouvements`, pas une colonne d'affichage. Le manque le plus lourd. | A1/L2 |
| `class` / `geography` / `sri` au niveau contrat `financier_cote` | **M2** — rend sa source au repli des contrats sans lignes classées | A1/L2 |
| Types de flux non coté `appel`, `distribution`, `appel_prevu`, `distribution_prevue` | **M3** — l'enum `mouvements.type` est fermé sur versement/retrait/frais ; sans extension, ni TVPI/DPI/RVPI ni échéancier | A1/L2 |
| `attributes.irr_pct` sur `non_cote` | **M4** — TRI communiqué par le GP, jamais calculé | A1/L2 |
| `isin` sur `financierCoteEntry` + logement des cours PS | **M5** — clé de `Cours PS` *et* du snapshot `ps_status` | A1/L2 |
| Colonnes de valeur sur `liquidites` / `immobilier` / `dettes` | **M6** — `genericEntry` n'en déclare aucune ; trois catégories tolérées par `additionalProperties` plutôt que modélisées, dont deux entrent dans les contrôles comptables | A1/L2 |
| Séries agrégées `valuations` et perf annuelle sur `historique_annuel` | **M7** — `valuations` est par position, l'agrégat coté/non coté n'est pas reconstituable | A1/L2 |
| `arbitrages[]` | **M8** — aucun logement pour les faits marquants de gestion | A1/L2 |
| `invest_date` sur `nonCoteEntry` | **M10** — le store réel range la date dans le TEXTE de `validation_note` (« Date d'investissement 2025-03-21 »). Une date métier réfugiée dans un commentaire : non requêtable, invisible à tout contrôle. | A1/L2 |
| `pocket.type` (FID/FAS/FE/mono) + `capital_invested`, `value_jan1`, `custodian`, `invest_date`, `pledged` sur `pocket` | **A5 tranché par Thomas** : liste au niveau du contrat, **toujours au moins une poche**, l'indice 0 portant le contrat quand il n'y en a pas. `pocket` est `additionalProperties: false` → amendement franc. Sans ces champs, la perf YTD par poche n'est pas calculable. | A1/L2 |

**Pas des écarts de schéma, mais à ne pas perdre** — `moic_realise` est déclaré au schéma et **jamais
rempli** (0/8) alors que le classeur porte les valeurs (**M11**) : défaut du constructeur de store, pas du
schéma. Et la convention de signe des mouvements est **figée à `amount ≥ 0`** (A4), le sens venant de
`type` : le store réel le respecte, c'est la fixture de `test_store_builder.py` qui est fautive.

Les neuf manques M1–M9 et les cinq ambiguïtés A1–A5 sont détaillés dans
`docs/spec_lecteur_forme_store_2026-07-28.md`. Chacun recevra son entrée complète **au moment où il sera
posé**, validé par son propre usage — pas avant.

---

## Critère d'arrêt du fork (O9 — non tranché)

Reste à décider : jusqu'où le fork peut aller avant que le merge ne devienne déraisonnable. Deux
critères candidats — retour vers Code dès que ce registre dépasse un nombre d'entrées convenu, ou dès
qu'une extension **touche le contrat de diff** (ce qui est de toute façon interdit par B7). Un critère
posé d'avance coûte moins cher qu'un constat tardif.
