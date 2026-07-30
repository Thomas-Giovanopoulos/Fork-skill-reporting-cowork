# L'historique du patrimoine — l'arrêté comme objet de première classe (D50/D51)

> 2026-07-30. Sidetrack demandé par Thomas : « il faudra dans la db des sections/shards par année
> pour garder un historique, et c'est cet historique qu'on consultera pour les reportings.
> Actuellement le tableau d'historique est un peu reconstruit comme on peut dans le skill. »
> Ce document constate le « comme on peut », pose le modèle cible, et le raccorde aux décisions
> existantes (R3 et l'invariant §8 du CDC plateforme, D6, D33, D49, MQ7).

---

## 1 — Le constat : quatre sources, trois fragiles, une orpheline

Le tableau « Historique du patrimoine » et les comparaisons temporelles du rendu sont aujourd'hui
reconstruits à chaque run depuis :

| Source | Ce qu'elle porte | Fragilité |
|---|---|---|
| Onglet `Valorisations` | points agrégés datés (coté, non coté) — lignes **trimestrielles** de l'année courante, Dietz par trimestre | saisie manuelle, aucune provenance |
| Onglet `Historique` | perfs **annuelles** des années passées + commentaire | la perf est **déclarée par le CGP, jamais recalculée** — un chiffre de reporting client sans source |
| `snapshots/{client}_{période}.json` | actif brut/net, poids par catégorie, `ps_status` (gel des coupons PS) | écrit par `p2_fill` **en local, relatif au cwd**. La comparaison N-1 dépend **de la machine** : un autre CGP, un autre poste → le N-1 disparaît **silencieusement** (pas d'erreur, juste pas de bloc). C'est la famille de bugs que D36 a tuée pour les référentiels. En prime : donnée client sur disque hors de tout store (la fuite `tmp_ent_001` de la baseline venait de là), et pollution du cwd (constat du 29/07). |
| `cp_valos.json` (run de référence) | 9 séries par contrat × 5 dates | **orpheline** — exactement le grain de `valuations[]`, jamais entrée au store (spec §7.8, MQ7) |

Le forme-store 2.1 a déjà les logements de *lecture* (`valuations`, `courbe_performance`,
`historique_annuel` typé) — ce qui manque est **l'amont** : où l'histoire VIT, qui l'écrit,
et pourquoi on lui ferait confiance.

## 2 — Le modèle : l'ARRÊTÉ, partitionné par année

**Le grain logique est l'arrêté** (une date de fin de période, un état validé), **la partition
physique est l'année** — la demande « shard par année » est satisfaite par le partitionnement
Postgres (`PARTITION BY RANGE (date_arrete)`), mais le grain ne peut pas être l'année seule :
le tableau Historique affiche des lignes **trimestrielles** pour l'année courante et annuelles
pour le passé. L'année est un rollup d'arrêtés (celui du 31/12 clôt l'année) ; en faire le grain
détruirait les trimestres.

Conformément à l'invariant §8 du CDC plateforme (« JSON déplié par défaut »), l'arrêté est
**déplié en colonnes requêtables** — pas un store JSON en cellule :

```
arretes            (client_id, date_arrete, period_short, statut,
                    actif_brut, actif_net, dettes, valeur_cote, valeur_nc,
                    flux_nets, perf_cote_pct, perf_nc_pct, commentaire,
                    valide_par, valide_le, version)
arrete_categories  (client_id, date_arrete, categorie, valeur, poids_pct)
arrete_positions   (client_id, date_arrete, position_id, valeur)      -- grain de valuations[]
arrete_ps_status   (client_id, date_arrete, isin, statut)             -- gel des coupons N-1
```

Chaque ligne issue d'un document porte sa **provenance D49** (`source_empreinte`,
`source_gabarit`, `source_arrete`) ; chaque ligne issue d'une revue porte son audit
(`validated_by/at`) — même grammaire que le reste du datahub.

**Trois règles de conduite :**

1. **Un arrêté validé est immuable.** Le reporting T2 rejoué en octobre rend le même document —
   c'est la reproductibilité du pipeline, étendue au temps. Une correction est une **nouvelle
   version** d'arrêté, auditée ; jamais un UPDATE silencieux.
2. **Le rendu consomme l'historique, il ne le reconstruit plus.** `courbe_performance`,
   `historique_annuel`, la comparaison N-1 et `ps_status` deviennent des **projections dérivées**
   des arrêtés. Même symétrie que les référentiels (D35/D36) : le pipeline n'a pas le réseau,
   l'AGENT lit l'historique (MCP datahub) et écrit un fichier dans le dossier de run — le fichier
   reste le contrat. Les perfs annuelles sont **recalculées** (Dietz sur arrêtés + flux), plus
   jamais déclarées ; l'onglet `Historique` ne survit que comme surface de **reprise** (années
   antérieures au système) avec `source: "declare_cgp"` explicite.
3. **`snapshots/` meurt — mais pas avant son remplaçant.** Discipline de bascule identique à
   D45 : double lecture (arrêtés d'abord, snapshots en repli) tant que l'historique n'est pas
   peuplé, puis retrait. On ne coupe pas un filet, même mauvais, avant d'avoir tendu le suivant.

## 3 — Où ça vit : le datahub client, PAS la base des référentiels

D6 l'a tranché : validation_app **est** le datahub, Postgres. L'historique est un **fait client**
— confidentiel par client, soumis aux permissions D2 — là où la base des référentiels (D33) ne
porte que des **faits de marché** partagés entre tous les CGP (D44 y interdit tout identifiant
client). Les arrêtés vont donc dans le **store client** (côté `rhetores_datastore`/schema du
datahub), jamais dans `ref`. Le fork ne touche pas validation_app (fil de détente D41-a) : il
pose la **forme** (ce document + entrée au registre au moment où le schéma SQL sera écrit), la
pose physique se fait côté datahub — c'est une brique de R3 (« historisation / as-of »), dont
ceci est la version *reporting-grade* : R3 complet (wayback, time-travel OneLake) reste en
vague 4, on n'en a pas besoin pour les reportings.

## 4 — L'UX de l'historique (D51)

- **Les relevés historiques passent par le pipeline NORMAL.** Le matcher lit déjà les archives —
  c'est tout l'objet de la fenêtre de validité D42 et de la limite LIM5 (le run de référence
  remonte à 2022). Un relevé 2023 déposé aujourd'hui produit un **arrêté rétroactif**, avec sa
  provenance. Zéro machinerie neuve.
- **Le déclencheur est un AskUser, le geste est le drag & drop du chat.** La notice
  (« transmettez aussi les relevés antérieurs ») est la v1 ; l'élégant est à portée de main :
  quand le skill détecte des contrats anciens sans arrêtés passés, il pose un AskUserQuestion —
  « l'historique est vide pour 2023–2025 : déposez les relevés annuels dans la conversation, ou
  continuez sans le tableau » — et le CGP glisse ses PDFs dans le chat. Le drop existe déjà ;
  l'AskUser ne sert qu'à le provoquer au bon moment.
- **Disponibilités / matières premières : la donnée vient des relevés, l'AskUser porte sur
  l'INTENTION.** *(Précisé par Thomas le 30/07.)* La présence de la donnée ne dit pas que le CGP
  veut la section — c'est exactement la séparation MQ9/CDC 1.6 : le store répond « peut-on ? »,
  le manifeste répond « veut-on ? ». Donc : la donnée entre au store **inconditionnellement**
  (elle est dans les comptes, aucun effort CGP) ; l'AskUser ne se pose **que s'il y a matière à
  construire la section** (faisabilité vraie), il demande « voulez-vous l'afficher ? », et sa
  réponse se **persiste** via `tri_decisions` (D30/R6) — batchée avec les autres questions de
  tri, jamais reposée à chaque run. Un AskUser sur une section sans matière serait du bruit ;
  une section affichée sans accord serait une décision éditoriale volée au CGP.

## 5 — Décisions

| # | Décision |
|---|----------|
| **D50** | **L'arrêté est un objet de première classe du datahub client**, grain = date d'arrêté, partition physique par **année**, colonnes dépliées (§8 CDC plateforme), provenance D49/audit par ligne. Immuable une fois validé (correction = nouvelle version auditée). Le rendu **consomme** l'historique en projections dérivées (courbe, historique annuel, N-1, ps_status) relayées par l'agent dans le dossier de run ; les perfs annuelles sont recalculées, plus jamais déclarées. `snapshots/` est déprécié, retiré seulement après double lecture. Vit dans le store client (D6/D2), jamais dans la base des référentiels (D33/D44). C'est la part *reporting-grade* de R3. |
| **D51** | **Les relevés historiques passent par le pipeline normal** (arrêtés rétroactifs via la fenêtre D42/LIM5) ; le skill **détecte** l'historique manquant et le **demande** par AskUser, le dépôt se faisant par le drag & drop du chat. Disponibilités et matières premières : la **donnée** vient des relevés et entre au store inconditionnellement ; l'**AskUser** porte sur l'intention d'afficher la section, ne se pose que si la faisabilité existe, et sa réponse se persiste via `tri_decisions` (D30) — séparation MQ9 : peut-on au store, veut-on au manifeste. *(Amendée le 30/07 : la première rédaction faisait de l'AskUser un repli de collecte ; c'est un choix éditorial conditionné à la matière.)* |

## 6 — Ce que ça change, et quand

| Quoi | Quand |
|---|---|
| Forme SQL des tables d'arrêtés + méthodes `Store` (get/save arrêté) | avec la pose côté datahub — entrée au registre à ce moment-là (M3) |
| Projections dérivées dans le dossier de run (`historique.json` ou sections du store de run) + double lecture snapshots | après la bascule ⑤ du chantier L, avec le chantier B |
| 8ᵉ fixture Historique (déjà validée par Thomas) | inchangée — elle exerce le RENDU du tableau, quelle que soit la source amont ; elle documente aussi la divergence relevée le 30/07 entre le template (4 colonnes) et la lecture du moteur (commentaire en colonne 2 ou 3 selon présence de la perf NC) |
| Onglets `Valorisations`/`Historique` du classeur | rétrogradés en surface de reprise, `source: "declare_cgp"` |
