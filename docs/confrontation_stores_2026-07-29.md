# Confrontation des deux forme-stores — étape ① du chantier L (D48)

> 2026-07-29. Exécute la décision **D48** (CDC v5) : convergence des deux forme-stores par
> confrontation champ à champ, bidirectionnelle. Sources : `skill/pipeline/store_client.schema.json`
> (`2.0-skill`, fork) ; `validation_app/ingest/excel_to_store.py` (626 lignes, lu **et exécuté** sur
> `imports/reporting_durand_01.xlsx` — le store émis fait foi, pas le docstring) ;
> `docs/spec_lecteur_forme_store_2026-07-28.md` §2–§3 (colonnes canoniques du classeur, normatives).
>
> **Le résultat de cette confrontation est le FORMAT CONVERGÉ** : c'est lui que le lecteur (étape ③)
> consomme et que les stores de vérité (étape ②) instancient. Le fork l'implémente maintenant ;
> validation_app s'y range au merge (M7) — on ne touche pas à son dépôt (lecture seule, fil de
> détente D41-a).

---

## 0 — La découverte qui recadre la confrontation : elle est à TROIS colonnes

La sonde sur les fixtures l'a montré d'emblée : le classeur du skill est **plus riche** que ce que
`excel_to_store` sait lire. Onglets du template du skill absents du lecteur validation_app :
**`Lignes`, `Mouvements`, `NC Flux`, `Produits structurés`, `Cours PS`, `Indices`, `Arbitrages`** —
soit exactement les manques MQ3, MQ5, MQ8 et le cœur de MQ1 (les lignes classées).

La confrontation n'est donc pas « fork vs validation_app » : c'est **fork vs validation_app vs le
classeur canonique**, et c'est le classeur qui est le sur-ensemble de vérité — le §3 de la spec du
lecteur (normatif) définit ce que le format convergé doit pouvoir porter. Aucune des deux branches
ne suffit seule ; l'avertissement de Thomas (« l'antériorité ne vaut pas canonicité ») est confirmé
dans **les deux sens** :

- validation_app a des champs que le fork n'a pas (assureur/intermédiaire, catégories typées,
  courbe agrégée, historique typé) — **et** des pertes silencieuses que le fork n'a pas :
  `ownership_pct: 100` **codé en dur** (la colonne propriété/démembrement est ignorée), dettes sans
  date de souscription ni montant initial, non coté lu jusqu'à la colonne 10 seulement (le TRI,
  colonne 11, est perdu — **MQ4 n'est résolu nulle part**), uncalled réel/estimé perdus.
- le fork a les poches complètes (invariant A5), `lines[]`, `ps`, `mouvements` typés — **et** trois
  catégories non modélisées (MQ6), pas d'assureur/intermédiaire (MQ1), pas d'agrégats (MQ7).

## 0-bis — Règle de nommage (à valider par Thomas)

« Tout sous clés françaises » est appliqué ainsi : **les concepts métier Rhétorès sont en français**
(`financier_cote`, `classe_rhetores`, `assureur`, `intermediaire`, `nantissement`, `adossement`),
**les champs techniques génériques gardent leur nom actuel**, déjà commun aux deux branches
(`value_current`, `capital_committed`, `custodian`, `balance`, `label`, `id`). Renommer ces derniers
en français créerait un churn bilatéral (fork + validation_app + rhetores_datastore) sans lever
aucune ambiguïté. Si Thomas veut le français intégral, c'est un renommage mécanique à faire en
étape ② — le reste de ce document n'en dépend pas.

---

## 1 — Sommet du store

| Champ | Fork | validation_app | **Arbitrage convergé** |
|---|---|---|---|
| `schema_version` | `"2.0-skill"` (const) | émet `"1.0"` (doc dit v2.0 — O18) | **`2.0-skill`** jusqu'au merge (M4). Le lecteur ne discrimine jamais sur ce champ (CDC v5 §2.3). |
| `reference_tables` | absent | **embarqué dans chaque store client** (asset_classes, envelope_types, geography_zones codés en dur dans le module) | **Fork gagne : PAS de référentiels embarqués.** D36 a tranché — les référentiels se lisent au store partagé à chaque run (MCP `ref_bundle`, snapshot en secours). L'embarqué de validation_app est un legacy pré-MCP ; l'y laisser recréerait le « dites aux CGP d'updater » à l'échelle du store client. C5 (« créer `meta.reference_tables` ») est **caduc dans sa lettre**, réalisé dans son esprit par D33/D36. |
| `courbe_performance` | absent (moitié de MQ7) | `[{date, cote, nc?}]` depuis l'onglet Valorisations | **validation_app gagne** : forme adoptée telle quelle. Couvre le volet « agrégats par date » de MQ7 — l'onglet Valorisations (3 colonnes) s'y projette sans perte. |
| `historique_annuel` | `genericEntry` (non typé, `entity_id` requis à tort — MQ7) | `[{year, rendement, rendement_nc?, commentaire?}]`, **sans entity_id** (agrégat patrimonial), rendements en **fraction** (6,34 % → 0.0634) | **validation_app gagne** : forme typée adoptée. Sans `entity_id` — la spec MQ7 le disait déjà. Unité : la fraction est conservée (donnée non ambiguë) ; le **lecteur** formate en % pour le moteur. |
| `exotiques` | présent | absent | **Conservé** (chantier A, A5 : catégories hors périmètre acceptées, transitent, ignorées au rendu). |
| `mouvements` | typé (`entry_ref`, enum `versement\|retrait\|frais`, `amount`) | toujours `[]` (onglet jamais lu) | **Fork gagne.** Extension d'enum MQ3 à poser (§4). |
| `valuations` | par `position_id` | points émis depuis val_01/val_cur des poches | **Fork gagne la forme** (identique), et validation_app apporte la **pratique** : les poches y ont un `id` qui sert de `position_id` — cf. §2, c'est la résolution de C7/D16. |
| `client.id` | pattern `^(tmp_\|C-)` | dérivé du nom de fichier (`stem.split("_")[0]` → `"reporting"` sur le fichier de démo : **violerait le pattern du fork**) | **Fork gagne** : le pattern tient, la dérivation par nom de fichier est un défaut du convertisseur (contredit D24 par ailleurs — rien ne se déduit du nom de fichier). L'id vient du contexte de run. |
| `blocs_enabled` | absent du store — vit au **manifeste** | dans `reporting{}` — calculé par **faisabilité** (`bool(fc_contracts)`…) | **Fork gagne, et corrige la CDC v5 §2.2 qui disait l'inverse.** MQ9 a été tranché par la donnée (spec §7.8) : zéro recouvrement store/manifeste, les commutateurs de rendu restent au manifeste. Ce que fait validation_app — déduire l'activation de la présence de données — est exactement le travail de `store_to_manifest` (J1), pas un fait client à stocker. Le store répond « peut-on ? », pas « veut-on ? » (CDC 1.6). |
| `reporting.version` / verrou optimiste | `version` (string, requis) | `Store.save_client` ajoute `version`/`base_version`/`updated_at` au niveau racine | Deux choses différentes : `reporting.version` = version du **reporting** (v1, v2…) ; le verrou optimiste est un champ du **datastore**, hors contrat du skill. **Tolérés, pas requis** au format convergé. |

---

## 2 — `financier_cote` : le gros de la confrontation

### 2.1 Niveau contrat

| Concept | Fork | validation_app | **Convergé** |
|---|---|---|---|
| Assureur / banque (**MQ1**) | absent — fusionné dans `label`, irréversible | `assureur` (texte du classeur) | **`assureur`**, requis. Valeur = **code du référentiel acteurs** quand il résout, verbatim sinon (le circuit K3 propose l'ajout). C'est la jointure store client ↔ référentiels. |
| Intermédiaire (**MQ1**) | absent | `intermediaire` | **`intermediaire`**, optionnel (absence ≠ null). Troisième terme de la clé de regroupement du moteur (spec §7.10) — sans lui, deux contrats du même assureur via des intermédiaires différents fusionnent. |
| Libellé | `label` requis (porte tout, MQ1) | `contract_label` **dérivé** (`f"{nature.upper()} – {assureur}"`) | **`label`**, et il redevient un libellé : la sémantique (nature, assureur, intermédiaire) vit dans ses champs. Le lecteur reconstruit l'affichage ; jamais l'inverse (le découpage de label est irréversible). |
| Nantissement | `pledged` (bool) | `nantissement` (bool) | **`nantissement`** — même concept, deux noms ; la règle française tranche. `pledged` retiré (posé il y a un jour, churn fork uniquement). Idem sur `pocket`. |
| Date (colonne 8 du classeur) | `invest_date` | `date_ouverture` | **`invest_date`** — même colonne (« Date d'invest. »), le nom validation_app est un renommage trompeur. Champ technique, règle 0-bis. *(À valider : si français intégral, `date_investissement` partout, y compris pocket et non coté.)* |
| `envelope_type` (vocabulaire) | store réel : `AV`/`Capi`/`CTO` (libellés moteur) | codes normés `av_lu`/`av_fr`/`capi_lu`/`capi_fr`/`cto`/`direct`, **déduits** par `_envelope_from_nature(nature, custodian)` | **Codes normés (validation_app)** au store ; le **lecteur** porte la table code → libellé moteur (c'est la place de la normalisation, A2). Mais la **déduction** LU/FR par heuristique dépositaire est remplacée à terme par la domiciliation du référentiel acteurs (G4/D26 — l'homonymie NC reste à lever). |
| Reste du jeu contrat | `manager`, `management_mode`, `risk_profile`, `capital_invested`, `value_jan1`, `value_current`, `value_projected`, `custodian` | `custodian`, `date_ouverture`, rien d'autre | **Fork gagne** (postérieur, et c'est ce que le moteur lit — spec §2). |

### 2.2 Poches

| Concept | Fork | validation_app | **Convergé** |
|---|---|---|---|
| Logement | `attributes.pockets[]`, **requis, minItems 1** (invariant A5) | `pockets[]` de premier rang, présent mais peuplé selon les lignes | **`attributes.pockets`, requis, minItems 1** — le logement suit **C2** (décision CDC : `payload.attributes.lines/pockets` sur `financier_cote`), l'invariant A5 est conservé tel quel. validation_app se range au merge. |
| **`id` de poche** | absent — jointure `lines[].pocket` par **libellé texte**, défaut connu (C7/D16) | **`id` présent** (`pck_001`…), et les `valuations` du datastore le référencent déjà comme `position_id` | **validation_app gagne, et c'est la résolution de C7/D16** : `pocket.id` requis au format convergé, `lines[].pocket` et `valuations[].position_id` visent l'id. Le libellé cesse d'être une clé — le run Gronier a prouvé qu'il diverge entre artefacts pour la même poche (spec §7.7). |
| Jeu de la poche | `type`, `profile`, `manager`, `custodian`, `value`, `capital_invested`, `value_jan1`, `invest_date`, `pledged` (A5 complet) | `label`, `classe_rhetores`, `nominal`, `value_current`, `attributes.geography` | **Fork gagne le jeu A5** (postérieur, requis pour la perf YTD par poche). `nominal` est la colonne 10 du classeur = **`capital_invested`** (renommage). `value_current` (v-app) = **`value`** (fork). |
| Classe / géo / SRI par poche (**MQ2**) | absent (MQ2 le voulait « au niveau contrat ») | `classe_rhetores` et `attributes.geography` **par poche** | **validation_app gagne, et résout MQ2 plus proprement que MQ2 ne le demandait** : dans le classeur, une ligne = une poche (A5), donc les colonnes 13/14/15 sont par-poche de fait. `classe_rhetores`, `geography`, `sri` **optionnels sur `pocket`** ; le repli du moteur (contrat sans lignes classées, L622) lit la poche 0. Pas de champ contrat redondant. |

### 2.3 Lignes, PS, mouvements — le fork est seul en piste

`lines[]` (9 colonnes, spec §2), `ps` (6 champs), `mouvements` typés : **aucun équivalent côté
validation_app** (onglets non lus). Le format convergé reprend les formes du fork telles quelles,
avec deux amendements déjà identifiés : `lines[].pocket` vise `pocket.id` (§2.2), et l'ISIN du
produit structuré + la série `Cours PS` restent à poser (MQ5, §4).

---

## 3 — Les trois catégories MQ6 : formes typées adoptées, complétées des colonnes perdues

Principe : la forme validation_app est le socle, **complétée** là où son parseur perd des colonnes
que le classeur porte (spec §3, normative).

**`liquidites`** — `{id, entity_id, label, custodian, balance}` : adopté tel quel, couvre Liq(3)
exactement.

**`immobilier`** — adopté : `{id, entity_id, label, function, value_acquisition, value_current}` +
`attributes.{date_acquisition, loyer_annuel}`. **Complété** : `ownership` (colonne 2, propriété ou
démembrement — texte, pas un pourcentage codé en dur : le `ownership_pct: 100` de validation_app est
une perte silencieuse) et `mortgage` conservé (bool, colonne 3).

**`dettes`** — adopté : `{id, entity_id, label, bank, type, rate, maturity, frequency, guarantee,
capital_remaining, adossement}`. **Complété** : `date_souscription` (colonne 3) et
`montant_initial` (colonne 4), que le parseur validation_app ne lit pas. Note : la colonne 2 (type
in fine/amortissable) n'a **aucun consommateur** au rendu (spec §3) — elle est portée (`type`) mais
le lecteur n'en dépend pas.

`genericEntry` ne sert plus qu'à `exotiques`. Trois catégories cessent d'être « tolérées » pour
être **modélisées** — c'était le diagnostic MQ6.

---

## 4 — Ce qu'aucune des deux branches ne porte : formes à poser depuis le classeur

Dérivées des colonnes canoniques (§3 de la spec), à poser en étape ② avec leur entrée au registre
chacune :

| Manque | Forme à poser au format convergé |
|---|---|
| **MQ3** — NC Flux | extension de l'enum `mouvements.type` : + `appel`, `distribution`, `appel_prevu`, `distribution_prevue` ; `entry_ref` → id de l'entrée `non_cote`. `amount ≥ 0`, le sens vient du type (A4, figé). *Complété le 30/07 par l'échec bruyant du dérivateur : `FLUX_TYPES` du moteur connaît un **cinquième** type, `Valorisation` — qui n'est pas un flux mais un point de VL par fonds. Son logement est `valuations[]` (position_id = l'entrée non coté), pas `mouvements`. MQ3 se scinde donc en deux logements existants, aucune forme nouvelle.* |
| **MQ4** — TRI | `non_cote[].tri_pct` (nombre, optionnel — communiqué par le GP, jamais calculé). Perte prouvée sur Gronier (10 et 7 au classeur, rien au store), et validation_app ne le lit pas non plus. |
| **MQ5** — PS | `isin` sur l'objet `ps` (clé de jointure), et série `ps_cours: [{date, isin, niveau_pct}]` (logement : `attributes.ps_cours` sur l'entrée, à confirmer à l'usage en étape ③). |
| **MQ8** — Arbitrages | `arbitrages: [{date, label}]` au sommet du store — deux colonnes, filtre « ligne ignorée si libellé vide » reproduit par le lecteur. |
| **MQ7** — agrégats | couvert par `courbe_performance` + `historique_annuel` typé (§1). |
| **MQ10** — `invest_date` non coté | déclaré au schéma (aujourd'hui réfugié dans le texte de `validation_note`). |
| **D49** — provenance | `source_empreinte`, `source_gabarit`, `source_arrete` optionnels sur toute entrée, à côté de `source_document` (légitime dans le store client). MQ11 (moic_realise jamais rempli) reste un défaut de remplissage, pas de schéma. |
| **A3** — MOIC/durée | **nombres** au store (fork) ; validation_app garde le texte (« 2.0x ») — c'est le lecteur qui formate à l'affichage. Écart de rendu attendu, inscrit au contrôle L3a. |

---

## 5 — Ce que cette confrontation corrige dans les documents du jour

- **CDC v5 §2.2, `blocs_enabled`** : la phrase « le manifeste et le store convergent d'eux-mêmes »
  était une erreur d'appréciation — le fait que validation_app loge `blocs_enabled` dans le store
  **contredit** MQ9 (tranché par la donnée) et la séparation intention/faisabilité du chantier J.
  Corrigée dans le CDC v5, arbitrage au §1 ci-dessus. C'est d'ailleurs le logement que la vision
  O17 (review présentation-only) rend le plus important à garder propre : la surface de review
  togglera le **manifeste**, jamais le store.
- **CDC v5 §2.2, MQ2** : « la convergence les rapatrie » se précise — MQ2 se résout **par la
  poche** (§2.2), pas par des champs au niveau contrat.

## 6 — Questions résiduelles pour Thomas (rien de bloquant pour l'étape ②)

1. **Règle de nommage 0-bis** : concepts métier en français, champs techniques inchangés — ou
   français intégral (renommage mécanique en plus, churn bilatéral) ?
2. **`assureur` en code d'acteur** : d'accord pour que la valeur soit le code du référentiel quand
   il résout (verbatim + proposition K3 sinon) ? C'est ce qui fait du store client un consommateur
   des référentiels.
3. **`envelope_type` en codes normés** (av_lu/av_fr/capi_lu/capi_fr/cto/direct) avec table
   d'affichage dans le lecteur — ou libellés moteur au store comme le store Gronier actuel ?

Défaut retenu si pas d'objection : les trois recommandations ci-dessus (0-bis, code d'acteur,
codes normés).
