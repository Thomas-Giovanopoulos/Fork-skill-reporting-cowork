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
| **Position** | **Position visée, pas constatée** (précisé le 2026-07-29). `skill/pipeline/store_client.schema.json` **n'a aucun objet `meta`** : ses propriétés racine sont `schema_version, client, reporting, _provisional_ids, valuations, liquidites, immobilier, financier_cote, non_cote, dettes, exotiques, historique_annuel, mouvements`, avec `additionalProperties: false`. La clé n'est donc pas seulement absente, elle serait **refusée** en l'état. Le chemin `meta.reference_tables` est celui de `clients.meta` côté infra, transposé par analogie ; sa transposition au schéma du skill reste à faire (C5) et dépend de R2. |
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
| **Vérifié en base le 2026-07-29 — ce n'est plus une intention** | Le DDL a été joué (schéma `ref`, 6 tables, 6 types, 11 index, 4 triggers, `schema_version` = `0.1-skill`) et la séparation D34 **démontrée par cinq contrôles**, dont deux qui doivent échouer : `ref_mcp` sans `SET ROLE` → `permission denied for schema ref` (le `NOINHERIT` tient) ; `ref_app` → lecture du canonique OK mais `INSERT INTO acteurs` refusé ; `ref_app` → `INSERT INTO adjudications` accepté ; `ref_admin` → `INSERT INTO acteurs` accepté. La garantie est donc portée par la base, pas par une note d'intention. Rejouables : `RUNBOOK.md` §2.3. |
| **Pour le faire bénir** | Replier le contenu dans le datahub une fois R2 tranché ; décider si les rôles survivent ou sont remplacés par l'authz applicative. |

### R4 — Profil de gabarit

| | |
|---|---|
| **Clé / objet** | table `gabarits` : clé **`(emetteur_code, gabarit, valide_depuis)`** *(depuis D42 ; la rédaction d'origine annonçait `(emetteur_code, gabarit, periodicite)`, corrigé dans le titre le 29/07 pour qu'il ne contredise plus le corps de l'entrée)*, colonnes `signature`, `extraction_hints`, `champs_publies`, `invariant_controle`, `template_id_natif`, `emetteur_lisible`, `periodicite` **informative** et `valide_jusqu_a` |
| **Position** | `infra/ddl_referentiels_v0.sql` §5 |
| **Statut** | **invention**, mais **dérivée de 11 cas réels** — pas d'une intuition |
| **Justification** | Nécessaire pour identifier un document par son contenu (D24) et pour primer l'extraction. La forme vient de l'étude empirique du 27/07 : signature en trois couches, nombre de pages exclu du matching, périodicité discriminée par un token de libellé. Voir `docs/etude_signature_gabarits_2026-07-27.md`. |
| **Trois corrections du 2026-07-29, issues du corpus étendu** | **(a) `periodicite` ne peut pas rester dans la clé d'appariement.** La périodicité n'est **pas lisible dans le document** chez trois émetteurs sur quatre — « trimestriels » chez Spirica désigne une offre commerciale, « pour l'année » chez Cardif une fenêtre de cumul YTD, et Himalia n'a aucun token (« 8 années » est la durée du contrat). Seul Wealins en porte un fiable. Or la contrainte d'unicité est `(emetteur_code, gabarit, periodicite)` : si la périodicité n'est pas déterminable à la lecture, elle ne peut être qu'une colonne de **stockage** renseignée par ailleurs (date d'arrêté, contexte du run, saisie CGP), jamais un critère de matching. **À trancher avant le premier `INSERT`.** **(b) `template_id_natif` n'est pas une signature parfaite.** `TYPE_MODELE=66` chez Cardif vaut **avant et après** une refonte à laquelle une seule ancre sur onze survit : il identifie une **famille de document**, pas un gabarit. Bon pré-filtre, raccourci trompeur — il ne peut pas court-circuiter les couches 2 et 3. **(c) `signature` doit distinguer sections requises et optionnelles.** Confirmé sur trois émetteurs : `PRM` et `DÉTAIL DES OPÉRATIONS` chez Spirica, `Fonds Euro` chez Himalia (absent 3 fois sur 5), `Arbitrages` et `Aperçu des fonds` chez Wealins. Ces sections sont **pilotées par la donnée**. Avec une liste à plat, un gabarit à géométrie variable se fait passer pour plusieurs gabarits — et on versionne pour rien. |
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
| **Position** | **Position visée, pas constatée** (précisé le 2026-07-29). La clé est **absente** de `skill/p1_engine/manifest.schema.json` comme du dossier de run : elle n'existe nulle part aujourd'hui. Le manifeste et le dossier de run sont le logement **retenu** par D30, à poser au moment où l'AskUser batché de l'étage 3 sera écrit (J/A3). |
| **Statut** | **invention** |
| **Justification** | Le tri d'étage 3 relève de l'intention et se décide par un AskUser batché au run (D30). Sans persistance, deux runs du même client divergeraient selon l'humeur du répondant. La réponse devient une **donnée du run**, reproductible et auditable. |
| **Pour le faire bénir** | Décider si le tri est une propriété du reporting (table `reportings`, H4) ou du client. |

### R7 — `segments` (→ `extraction_hints.segments`) : documents composites

| | |
|---|---|
| **Clé / objet** | `segments` — au **premier niveau** du profil dans le seed, dans `extraction_hints` dans le bundle et en base |
| **Position** | `infra/ddl_referentiels_v0.sql` §5 (colonne JSONB `extraction_hints`) · `seed/gabarits.json`, profil Wealins annuel, où `segments` est une clé de **premier niveau** du profil, **pas** une sous-clé d'`extraction_hints`. **Précisé le 29/07** : la clé ne rejoint `extraction_hints` qu'au passage par `seed/construire_bundle.py`, qui la recopie sous ce nom (« les segments voyagent dans `extraction_hints` : aucune modification de DDL »). Chercher `extraction_hints.segments` dans le seed ne rend donc rien, et l'entrée le laissait croire. |
| **Statut** | **invention**, mais **sans coût structurel** : `extraction_hints` est déjà une colonne JSONB, aucune modification de DDL |
| **Justification** | Décision **O11**. Le relevé annuel Wealins est la concaténation de 4 sous-templates aux paginations locales distinctes. Deux modélisations étaient possibles : un profil par sous-template (matching par segments, couche supplémentaire) ou un profil composite. Retenu : **un profil, avec segments déclarés**, et le **drift évalué par segment**. Un seul appariement, donc pas de couche de matching en plus ; mais une évolution de la seule page Loi Pacte ne remet pas en cause tout le profil et produit une proposition `mise_a_jour` ciblée. Deux éléments empiriques justifient ce découpage : les frontières sont détectables au caractère près et se sont vérifiées **identiques sur deux exemplaires de tailles très différentes** (26 p./2 FID et 15 p./1 FID) ; et la page Loi Pacte porte un **pied de page au numéro de fax différent**, preuve qu'elle est produite par un autre générateur — donc de cycles de vie indépendants. |
| **Vérification empirique du 2026-07-29 — R7 avait raison, mon amendement était faux** | Le corpus étendu (7 documents Wealins, tous originaux) **réfute** l'amendement ci-dessous. `Information annuelle FC055211_31 12 24.pdf` n'est pas le sous-template n°2 circulant seul : c'est le composite complet à 4 blocs, 11 pages. **7 documents sur 7 sont composites** — les sous-templates ne circulent **jamais** en autonomie. Donc un **profil composite unique à segmentation interne**, exactement la forme retenue par cette entrée à l'origine. Les segments restent des segments ; ils ne sont pas des documents. Détail : `docs/etude_corpus_2026-07-29/wealins.md`. *Deux corrections induites à B.6 : le pied de page au fax différent sur la page Loi Pacte n'est pas la preuve d'un générateur distinct mais le fossile d'un changement de numéro non propagé (en janvier 2025 toutes les pages portaient le même) ; `Arbitrages` (1/7) et `Aperçu des fonds` (3/7) sont des ancres **conditionnelles**, pas structurelles.* |
| **Amendement du 2026-07-29, INFIRMÉ le même jour — conservé pour la trace du raisonnement** | **D38** (« un profil par template ») a d'abord paru contredire cette entrée, jusqu'à vérification de l'étude de signature §B.6 : Wealins n'est **pas** quatre documents mais **un seul PDF composite**. Or le matcher apparie un *document*. D38 vaut donc pleinement pour le cas « 50 relevés distincts → 50 profils » ; les **sections d'un composite ne sont pas des templates** et n'ont pas de signature au niveau document. Un profil unique pour Wealins reste donc juste — c'était l'apport de cette entrée. **Ce qui change** : les sous-templates cessent d'être une `segments.liste` informelle et deviennent des **enfants de plein droit**, chacun avec ses propres `extraction_hints` et son `invariant_controle`. Motif, mot de Thomas : ne pas généraliser le store de schémas au point de le réduire à « un bout d'infra inutile ». La granularité est conservée, le matcher reste cohérent. **À implémenter dans `seed/gabarits.json` avant tout chargement.** |
| **Pour le faire bénir** | Vérifier sur un second émetteur composite si le cas se présente. Aucun des **8** autres profils du seed n'en a besoin — il en compte **9** depuis que Wealins est scindé en deux gabarits (annuel et trimestriel), seul le profil annuel portant des segments : ne pas généraliser prématurément. |

### R8 — Outillage du serveur des référentiels : `uv` au lieu de `pip`

| | |
|---|---|
| **Clé / objet** | `infra/mcp_referentiels/pyproject.toml` + `uv.lock` ; `requirements.txt` conservé mais **remplacé** |
| **Position** | `infra/mcp_referentiels/` · pas-à-pas dans `infra/RUNBOOK.md` §2.4 |
| **Statut** | **rattrapage** — le protocole existe déjà côté infra (`mcp-o2s-server` est piloté par uv depuis toujours) ; le fork avait inventé une seconde façon de faire, on revient à la première |
| **Justification** | Décision de Thomas du 2026-07-29 : **un seul protocole pour les deux serveurs MCP**. Trois motifs, dont un s'est vérifié dans l'heure. **(a)** `uv` crée et gère le `.venv` lui-même : plus d'activation, donc les pièges Windows du §2.0 (`source` inexistant en PowerShell, `bin/` vs `Scripts\`) cessent de s'appliquer au lieu d'être documentés. **(b)** Un protocole unique supprime la question « lequel est en pip, lequel est en uv ». **(c)** Le décisif : `requirements.txt` *affirmait* aligner ses versions sur `mcp-o2s-server` avec des `>=` qui ne garantissaient rien. Le premier `uv lock` a résolu **`mcp` 2.0.0**, version qui a **supprimé `mcp.server.fastmcp`** — `server.py` ne s'important plus du tout. La divergence que le fichier disait vouloir éviter était donc déjà là, invisible faute de lock. Corrigé par `mcp[cli]>=1.27.2,<2`. |
| **Effet de bord relevé** | `mcp-o2s-server` porte **la même** dépendance non bornée (`mcp[cli]>=1.0`) : seul son `uv.lock` (1.27.2) le protège, et son prochain `uv lock --upgrade` produira la même panne d'import. **Y poser `<2` avant que ça arrive** — c'est le vrai enseignement de cet écart, et il concerne l'infra, pas le fork. |
| **Dérive assumée** | `mcp` verrouillé à **1.29.0** ici contre **1.27.2** côté O2S. Même majeure, API intacte, écart toléré : la validation de token vit dans `rhetores_authz` (partagé, version unique), pas dans `mcp`. |
| **Pour le faire bénir** | Rien à faire bénir côté Code : c'est un choix d'outillage, pas une forme de donnée. À solder en même temps que l'extraction de `mcp_referentiels/` en dépôt propre, qui rendra caduque l'override par chemin relatif de `rhetores_authz`. |

### R9 — `adjudications.source_*`, `succession_contexte_sans_reference`, et la règle « aucun identifiant client dans un référentiel partagé »

| | |
|---|---|
| **Clé / objet** | (a) trois colonnes `adjudications.source_empreinte` (sha256 du **contenu**), `adjudications.source_gabarit`, `adjudications.source_arrete`, **en remplacement de `source_document`, supprimée** ; (b) contrainte `succession_contexte_sans_reference` sur `acteur_successions.contexte` — `CHECK (contexte IS NULL OR contexte !~ '[A-Z]{2}[0-9]{5,8}')` ; (c) règle transverse **D44** : aucun identifiant client dans un référentiel partagé, tenue à l'assemblage par `seed/construire_bundle.py` (`MOTIF_REFERENCE_CONTRAT`, `NOMS_CLIENTS`, `SOURCE_ISIN_DEIDENTIFIEE`). |
| **Position** | `infra/migration_002_purge_identifiants_clients.sql` (bases existantes) · `infra/ddl_referentiels_v0.sql` §4 et §7 (installations neuves — **les deux doivent aboutir au même schéma**, comme pour migration_001) · `seed/construire_bundle.py`, garde-fou D44 appelé depuis `main()` avant toute écriture · valeurs réécrites dans `seed/acteurs.json` (payloads), `seed/successions.json` (`contexte`, `payload.note`), `seed/gabarits.json` (`_source`, `_note_ancres`, `_regles`). |
| **Statut** | **invention** |
| **Justification** | Ce n'est pas une précaution de conformité, c'est une **fuite active**. `ref_bundle` rend le store **en entier à chaque CGP** — c'est tout l'objet de D36 : un gabarit validé par l'un doit être visible du suivant. Conséquence rarement énoncée : **tout identifiant client qui entre dans cette base est visible de tous les CGP**, et le défaut était déjà opérant en local, indépendamment de tout hébergement (D43). Les deux `contexte` du seed portaient un **numéro de contrat réel** ; `acteurs[6].payload.source` citait deux numéros de relevés ; la colonne `source` du CSV des ISIN nomme des clients sur **261 lignes**. La distinction qui tranche : **une succession est un fait de marché — le contrat où on l'a observée appartient au dossier de run du client.** Trois choix méritent d'être défendus. **(1)** `source_document` est **supprimée**, pas conservée « au cas où » : une colonne de PII conservée est une PII conservée. Son remplacement est en outre **plus utile** — l'empreinte du *contenu* reconnaît deux propositions issues du même document, ce qu'un nom de fichier ne garantit jamais. **(2)** Le motif est volontairement **étroit** (deux lettres, cinq à huit chiffres) : une contrainte trop large serait désactivée au premier faux positif, ce qui est pire qu'aucune contrainte. **(3)** L'information n'est pas supprimée mais **dé-identifiée** — le *type* de document et le *nombre* de réplicats sont conservés (« deux relevés annuels du même émetteur »), parce que c'est le réplicat qui rend une ancre fiable. Les e-mails de CGP (`propose_par`, `arbitre_par`, `validated_by`) sont en revanche **conservés** : la responsabilité nominative est la contrepartie exacte du privilège d'arbitrage (D34). |
| **Vérifié en provoquant l'échec — le garde-fou a été vu refuser** | Un garde-fou qu'on n'a pas vu échouer ne prouve rien. Trois injections, trois refus, **aucune sortie réécrite** : une pseudo-référence dans `acteurs[6].payload.source` → `seed/acteurs.json.acteurs[6].payload.source : référence de contrat 'ZZ9876543'`, plus le même chemin dans le bundle et `seed/seed.sql:14` ; un nom de client dans un champ anodin → `seed/gabarits.json.gabarits[6].n_pages_indicatif : nom de client 'interagyr'` ; la table `SOURCE_ISIN_DEIDENTIFIEE` neutralisée → `bundle.isin[0].source : nom de client 'gronier'`. Le contrôle a aussi trouvé de lui-même une fuite non listée : **un nom de fichier de `docs/etude_corpus_2026-07-29/` portant le nom d'un contrat client**, cité dans un `_source` de gabarit ; la citation a été remplacée par le répertoire et le titre de l'étude, `docs/` étant hors périmètre d'écriture. **Faux positif à connaître** : `[A-Z]{2}[0-9]{5,8}` matche l'intérieur de tout ISIN (`DK0062498333` contient `K0062498`, Novo Nordisk). Les ISIN bien formés sont donc **soustraits avant recherche** ; sans cela le garde-fou se déclenche sur 261 lignes légitimes et finit désarmé. C'est aussi pourquoi la contrainte SQL ne porte que sur `contexte`, jamais sur `isin`. |
| **Pour le faire bénir** | Trois questions à Code. **(a)** Le datahub a-t-il déjà une convention d'empreinte de document (nom de colonne, algorithme, salage) à laquelle `source_empreinte` doit s'aligner plutôt que d'en inventer une ? **(b)** La règle « aucun identifiant client dans un référentiel partagé » doit-elle être portée par le **schéma** (des CHECK par colonne texte, comme ici) ou par une **revue de contenu** au chargement, côté application ? Le fork a tranché pour le schéma là où la colonne est étroite, et pour un contrôle d'assemblage ailleurs — le partage définitif est à décider. **(c)** La colonne `source` de `skill/assets/isin_referentiel_v0.csv` doit être **corrigée à la source** : la dé-identification par table de correspondance dans `construire_bundle.py` est une rustine, l'asset restant porteur des noms de clients. Tant qu'elle est là, le chargement **ne doit pas** se faire par `\copy` sur le CSV brut mais par `seed/seed.sql`. |

### R10 — Format convergé `2.1-skill` (D48) : MQ1–MQ8, MQ10, C7/D16, A4, D49, en un amendement

| | |
|---|---|
| **Clé / objet** | Amendement d'ensemble de `store_client.schema.json`, `schema_version` **`2.0-skill` → `2.1-skill`** (les stores 2.0 ne valident plus — échec bruyant voulu, L5, migration mécanique). Détail : **(a)** `assureur` (requis) et `intermediaire` sur `financierCoteEntry` — MQ1 ; **(b)** `pocket.id` **requis**, visé par `lines[].pocket` et `valuations[].position_id` — C7/D16 ; **(c)** `classe_rhetores`/`geography`/`sri` optionnels sur `pocket` — MQ2 résolu *par la poche* (une ligne classeur = une poche, A5), pas au niveau contrat comme la spec le proposait ; **(d)** `liqEntry`/`immoEntry`/`detteEntry` typés, `genericEntry` réservé à `exotiques` — MQ6, avec les colonnes que le parseur validation_app **perdait** : `ownership` texte (démembrement, son `ownership_pct: 100` était codé en dur), `date_souscription`, `montant_initial` ; **(e)** `histoEntry` typé **sans `entity_id`** (fraction, pas %) + `courbe_performance` racine `[{date, cote, nc?}]` — MQ7 ; **(f)** `arbitrages` racine `[{date, label}]` — MQ8 ; **(g)** enum `mouvements.type` + `appel`/`distribution`/`appel_prevu`/`distribution_prevue`, `entry_ref` → entrée `non_cote` — MQ3 (logement de NC Flux) ; et `amount: minimum 0` — A4 figé au schéma ; **(h)** `tri_pct`, `invest_date`, `attributes.uncalled_reel`/`uncalled_estime` sur `nonCoteEntry` — MQ4/MQ10 ; **(i)** `ps.isin` + `ps.cours[{date, niveau_pct}]` — MQ5 ; **(j)** `pledged` → **`nantissement`** (contrat et poche) — règle de nommage 0-bis ; **(k)** provenance **D49** (`source_empreinte`/`source_gabarit`/`source_arrete`) déclarée sur toutes les entrées, miroir côté store client de R9 (où `source_document` reste **légitime** : le store client vit chez le client). |
| **Position** | `skill/pipeline/store_client.schema.json` (réécrit) · `store_builder.py` (version) · `test_store_builder.py` (15 contrôles, dont 5 refus prouvés : sans assureur, poche sans id, montant négatif, dette sans capital restant, plus les deux refus A5 existants). |
| **Statut** | **rattrapage** pour (a)(b)(d)(e) — les concepts existent côté validation_app/datastore, la confrontation ne fait que les rapatrier en corrigeant leurs pertes ; **invention dérivée du classeur canonique** (spec §3, normative) pour (c)(f)(g)(h)(i) ; **renommage** pour (j) ; **invention** pour (k), symétrique de R9. |
| **Justification** | C'est l'exécution de **D48** : chaque écart est arbitré dans `docs/confrontation_stores_2026-07-29.md` (§1, §2, §3, §4), avec son motif individuel. La règle d'ensemble : le classeur canonique est le sur-ensemble de vérité, aucune des deux branches ne suffit, l'antériorité ne vaut pas canonicité. Deux non-changements notables, décidés là-bas : `blocs_enabled` reste **hors** du store (MQ9, spec §7.8 — son logement validation_app est une confusion intention/faisabilité), et `reference_tables` reste **hors** du store client (D36 — legacy pré-MCP, cf. R1/R2 qui restent ouvertes sur la question de la portée). |
| **Pour le faire bénir** | Soumettre le format convergé en un lot au retour (M7) : c'est le cœur de l'addendum D48, validation_app s'y range au merge. Les questions résiduelles §6 de la confrontation (nommage 0-bis, `assureur` en code d'acteur, `envelope_type` en codes normés) ont été validées par Thomas le 29/07 — « aucune objection ». |

### R11 — `nature` verbatim sur `financier_cote` (+ QC de traversée, + enrichissement référentiel à l'apply)

| | |
|---|---|
| **Clé / objet** | (a) `financierCoteEntry.nature` — la nature du contrat TELLE QUE LE CLASSEUR L'ÉCRIT (« Compte Titres », « AV »…), optionnelle, préférée par le lecteur au code d'enveloppe pour la colonne 0 ; (b) **QC n°10 « traversée »** dans `p2_fill` : Σ lignes classées jointes au rendu = Σ lignes lues, échec bruyant sinon ; (c) enrichissement **déterministe** des lignes par le référentiel ISIN à l'apply (class/geography/sri, priorité absolue) + table `GEO_VERS_LIBELLE` au lecteur. |
| **Position** | `skill/pipeline/store_client.schema.json` · `skill/p1_engine/lecteur_store.py` · `skill/p1_engine/p2_fill.py` (QC) · `skill/pipeline/appliquer_diffs.py` (e). |
| **Statut** | **invention**, née d'un bug prouvé — pas d'une intuition. |
| **Justification** | Premier run réel (30/07) : « Compte Titres » → `cto` → réaffiché « CTO » a cassé la clé de jointure `norm("{nature} — {banque}")` — **53 lignes perdues du rendu, QC 7/7 au vert**. Deux réponses : la donnée (le mot du client est une donnée, pas un affichage — il fait les clés) et le juge (aucune couche ne surveillait la traversée store → HTML ; désormais un reporting qui perd une ligne ÉCHOUE, il ne s'imprime pas amputé). L'enrichissement (e) rend mécanique la règle « priorité absolue du référentiel » — constat honnête au passage : la colonne `sri` du référentiel est **vide sur 261 lignes**, l'enrichissement SRI ne produira rien tant qu'elle n'est pas remplie (chantier de donnée). Contrôle négatif exécuté : le QC a échoué 0/53 sur le run fautif AVANT correctif, passe 53/53 après ; L3a 7/7 inchangé ; golden 7/7 (10/10 QC sur la fixture à lignes). |
| **Pour le faire bénir** | Avec le lot D48. Question associée pour Code : le datastore veut-il `nature` verbatim aussi, ou considère-t-il l'enveloppe normée suffisante côté hub (le verbatim ne servant qu'au rendu) ? |

---

## À inscrire dès qu'on y touche

Ces écarts sont **décidés** mais pas encore posés dans le code. Chacun devra recevoir son entrée
complète au moment de l'implémentation, pas avant, pas après.

> **Purge du 2026-07-29 (soir)** : les onze lignes MQ1–MQ8/MQ10 + identifiant de poche sont
> **posées par R10** et sorties de cette liste. Il ne reste qu'une dette décidée non posée.

| Objet | Décision | Chantier |
|---|---|---|
| Logement de la donnée du bloc Contexte | C6 / O7 — **invention réelle**. **Clos par D39 le 29/07 : la donnée vit dans une table SÉPARÉE, par période, partagée par tous les clients** — pas dans le store client. Motif : c'est un fait de marché, pas un fait client ; la loger par client dupliquerait le même texte autant de fois qu'il y a de clients. *(Correction du 29/07 : cette ligne annonçait « la donnée vit dans le store », orientation du 28/07 que D39 a renversée.)* Les `contexte/*.json` deviennent le snapshot de secours (D35). Reste à poser : la forme d'une ligne de cette table. | A3 |

### Déjà posées — inscrites à tort comme à venir

Audit du 2026-07-29. La liste ci-dessus en comptait dix-sept lignes ; **six** décrivaient comme « décidé,
pas encore posé » des clés **déjà présentes dans le schéma**. Quatre le sont vraisemblablement **depuis
avant le fork**, donc héritées de HANAMI : le constructeur qui les alimente,
`skill/pipeline/store_builder.py`, est inchangé vs `BASELINE_MD5.txt`, et rien au journal ne mentionne leur
pose. Elles n'ont jamais été des écarts du fork. Les deux dernières ont bien été posées ici, le
2026-07-28, mais leur ligne n'a pas suivi.

| Objet | Où la clé se trouve réellement | Époque |
|---|---|---|
| `attributes.lines[]` et `pockets[]` sur `financier_cote` | `store_client.schema.json`, `$defs.financierCoteEntry.properties.attributes` : `lines` → `$defs.line` (isin, label, value, class, geography, sri, pocket, perf_pct), `pockets` → `$defs.pocket`. `attributes` est requis, et `pockets` requis et `minItems: 1` **depuis A5** (28/07). | avant le fork, resserré le 28/07 |
| `entry_ref` sur les entrées `mouvements` | `$defs.mouvementEntry.required` = `['id','entry_ref','date','type','amount']`. Un test l'exerce **dans les deux sens** : `check_refs` (`store_builder.py:266`) est vérifié sur un store sain *et* sur un `entry_ref` volontairement cassé (`test_store_builder.py` §4). Ce n'est donc pas seulement déclaré, c'est contraint. | avant le fork |
| `unit` sur les valuations + valuations par `position_id` | `$defs.valuation` : `position_id` est **requis** (avec `date` et `value`), et `unit` est un `enum` fermé (`eur`, `pct`). *Au passage, la ligne parlait de `meta.valuations` : il n'y a **pas** d'objet `meta` — `valuations` est une propriété racine. Même position fantôme que R1.* | avant le fork |
| Attributs PS dans le payload | `$defs.ps` (`additionalProperties: false`) porte `coupon`, `start_date`, `duration_years`, `protection_pct`, `recall_pct`, `underlying_level`, référencé depuis `attributes.ps` de `financierCoteEntry`. | avant le fork |
| Renommage `blocs_enabled.historique` → `rendement_annuel` (D31) | **Fait, et fait autrement** : le bloc a été renommé puis **supprimé**, pas renommé — son tableau synthétique est relocalisé sous le tableau Historique, `BLOCK_ORDER` est passé de 9 à 8 blocs et `blocs/rendement_annuel.html.j2` a été retiré. `blocs_enabled` n'accepte donc plus ni `historique` ni `rendement_annuel` : les vieux manifestes se **migrent** (`migrer_reference.py`), ils ne se renomment pas. Cf. `JOURNAL.md`, « A2 » et « Suppression du bloc Rendement annuel ». | posé le 2026-07-28 |
| `pocket.type` (FID/FAS/FE/mono) + `capital_invested`, `value_jan1`, `custodian`, `invest_date`, `pledged` sur `pocket` | `$defs.pocket`, avec `profile` maintenu distinct de `type` (colonnes 7 et 3 du gabarit de transition). Trois tests ancrent l'invariant, `test_store_builder.py` passant de 5 à 8 contrôles. | posé le 2026-07-28 |

Ce que l'erreur coûtait : ces six lignes gonflaient le compte des « dettes décidées non posées », qui est
précisément le repère du fil de détente (b) de D41. Après correction, **11 lignes restent à venir**, dont
`C7` — vérifié absent. Le repère complet de D41 au 29/07 est donc **8 entrées posées (R1–R8) et
11 dettes décidées non posées** ; la formulation « 7 entrées posées » qui circulait ailleurs datait
d'avant R8.

**Pas des écarts de schéma, mais à ne pas perdre** — `moic_realise` est déclaré au schéma et **jamais
rempli** (0/8) alors que le classeur porte les valeurs (**MQ11**) : défaut du constructeur de store, pas du
schéma. Et la convention de signe des mouvements est **figée à `amount ≥ 0`** (A4), le sens venant de
`type` : le store réel le respecte, c'est la fixture de `test_store_builder.py` qui est fautive.

Les **onze** manques MQ1–MQ11 (MQ10 et MQ11 découverts en confrontant la spec au store Gronier réel) et les
cinq ambiguïtés A1–A5 sont détaillés dans
`docs/spec_lecteur_forme_store_2026-07-28.md`. Chacun recevra son entrée complète **au moment où il sera
posé**, validé par son propre usage — pas avant.

> **Renumérotation du 2026-07-29 : les manques passent de `M1`…`M11` à `MQ1`…`MQ11`.** Le préfixe `M` est
> déjà celui du **chantier M** du CDC (`M1`–`M7` : fork, registre, suffixe `-skill`, protocole de merge),
> et ce registre s'en sert lui-même — son encadré d'ouverture cite `M7` (retour vers Code) et le §
> `schema_version` cite `M4` (suffixe maintenu), qui ne sont pas le manque n°7 ni le manque n°4. Une
> collision de préfixe rend la référence ambiguë sans qu'aucun lecteur ne puisse s'en apercevoir ; c'est
> la dette T1 sur la clé `historique`, reproduite dans la numérotation. Les numéros sont conservés, seul
> le préfixe change.

---

## Critère d'arrêt du fork (O9 — clos par D41)

**Tranché le 2026-07-29 par D41.** La cible est le **traitement de tous les points du CDC** : on ne
divergera pas au-delà. Mais une cible n'est pas un critère, et s'y ajoutent **deux fils de détente** qui
provoquent un retour anticipé vers Code :

- **(a)** Code touche `store_client.schema.json` ou `validation_app` pendant le fork. La divergence
  deviendrait bilatérale, donc irréconciliable par ce registre seul — il n'enregistre que nos écarts.
- **(b)** Le nombre de dettes « décidées non posées » croît sans qu'aucune ne soit posée. C'est le mode
  de défaillance HANAMI exact : accumuler du schéma plus vite qu'on ne le valide par l'usage. C'est ce
  fil que la section précédente instrumente, et pourquoi son décompte doit rester juste.

**Repère au 29/07 (matin) : 8 entrées posées (R1–R8), 11 dettes décidées non posées.**
**Repère au 29/07 (soir) : 10 entrées posées (R1–R10), 1 dette décidée non posée** (la forme d'une
ligne de la table de contexte, D39). R10 a soldé d'un coup les onze dettes MQ — c'est le mouvement
inverse du mode de défaillance HANAMI que le fil (b) surveille : on a posé plus vite qu'on n'a décidé.

*Historique des deux critères candidats, conservé parce qu'il explique la forme retenue.* Le fork
envisageait au départ **(a)** un seuil sur le nombre d'entrées de ce registre, **(b)** un retour dès
qu'une extension **touche le contrat de diff**. Le candidat (b) était **inopérant** : B7 interdit déjà
de toucher le contrat de diff, le fil ne se serait donc jamais déclenché. Le candidat (a) survit, mais
transformé — non plus un seuil absolu sur le nombre d'entrées, qui aurait puni la tenue régulière du
registre, mais la **croissance des dettes non posées à posées constantes**, qui mesure ce qu'on voulait
réellement surveiller.
