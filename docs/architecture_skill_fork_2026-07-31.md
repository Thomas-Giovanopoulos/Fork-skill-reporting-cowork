# Architecture — le `.skill` et le fork

> 2026-07-31. Document technique de référence : comment le paquet distribué fonctionne, comment
> l'atelier (le fork) est organisé, et pourquoi. Les décisions citées (D24…D56) vivent au
> registre : `docs/roadmap_2026-07-27.md` et documents liés. Public : développeur ou admin
> reprenant le projet — pas les CGP (voir `guide_cgp_skill_reporting.md`).

## 1 — Deux objets, deux vies

**Le `.skill`** est le paquet distribué, installé chez chaque CGP. Il contient le protocole de
l'agent (`SKILL.md`), le moteur déterministe (`p1_engine/`), les assets (snapshot des
référentiels, référentiel ISIN, template Excel de structure) et son propre filet de tests. Il
est **scellé** : `CHECKSUMS.json` porte taille + md5 de chacun des 134 fichiers, et
`selfcheck.py` refuse de tourner sur un paquet corrompu (étape 0 obligatoire du protocole).

**Le fork** (ce dépôt) est l'atelier : le paquet y vit dans `skill/`, entouré de tout ce qui le
fait évoluer sans jamais y entrer — registre des décisions, contrôles d'époque, dossiers de
runs, outillage de dérivation, seed, dashboard. Depuis **D54**, le fork n'a plus vocation à être
mergé vers main : il EST le véhicule du PoC, et le registre des écarts (R1–R11) est la
**spécification documentée** de ce que main devrait apprendre du fork le jour d'un portage.

## 2 — Le flux d'un run, de bout en bout

```
PDFs + Excel structure
   │  étape 0 : selfcheck (paquet intègre ?)
   │  étape 0-bis : AGENT → MCP ref_bundle → referentiels.json sur disque
   ▼
Identification (matcher par signatures 3 couches — profils de gabarits du référentiel)
   ▼
1 SUBAGENT PAR PDF (bloquant), primé par le profil apparié
   │  (extraction_hints, champs_publies, invariant_controle copiés verbatim du profil)
   │  → un DIFF par document (jamais d'écriture directe)
   ▼
valider_diff.py   — jsonschema Draft 2020-12 + règles hors-schéma (update sans cible,
   │                montant négatif, vocabulaire de lignes à 2 niveaux)
appliquer_diffs.py — provenance D49 posée partout · pocket.id en séquence globale ·
   │                acteurs résolus par alias (inconnu = verbatim + signalement, jamais inventé) ·
   │                enrichissement sri/class/geo depuis le référentiel ISIN quand absents ·
   │                old_value ≠ store = CONFLIT rapporté, champ non appliqué (pas de last-write-wins)
   ▼
client.store.json (format convergé 2.1-skill)
   ▼
p2_fill.py — rendu DIRECT depuis le store via la façade lecteur (D20/D48)
   │         contrôles comptables 9/9 dont QC n°10 de TRAVERSÉE (Σ lignes rendues = Σ store)
   ▼
reporting.html + dossier de run archivé, rejouable
```

Points structurants :

- **L'agent parle au MCP, le pipeline lit des fichiers** (D35/D36). Le sandbox Python n'a pas
  de réseau : l'agent rapatrie le bundle et l'écrit sur disque — ce qui rend le run
  reproductible et archive le bundle comme pièce du dossier.
- **Le store est le chemin nominal** (bascule ⑤). `lecteur_store.py` présente le store sous
  l'interface classeur (`ClasseurStore`) : le moteur ne connaît qu'une interface, Excel ou JSON.
  La preuve de non-régression est **L3a** : les deux chemins rendent le même HTML à l'octet.
- **La réconciliation ne tranche jamais seule** : écart → AskUser batché (une seule salve de
  questions), réponses persistées.
- Le formatage du lecteur **préserve la valeur** (`_moic`, `_duree` : « 1,06x » ne devient
  jamais « 1,1x », `7` devient « 7y ») — le template attend du pré-formaté et ne calcule pas.

## 3 — Le moteur et sa banque

`p2_fill.py` (~2000 lignes) calcule tout ; `bank/` dessine. Blocs : hero, contexte (00),
supervision (01), performance (02), performance_nc (03), repartition, exhaustif — assemblés par
`base.html.j2` selon `blocs_enabled` du manifeste. Deux modes : `presentee` (défaut, figée,
présentation client) et `envoyee` (interactive : accordéons, pages Détails).

Principes de rendu, tous nés d'arbitrages (chantier UI du 31/07, dossier
`chantier_ui_design_2026-07-31.md`) :

- **Sincérité** : une valeur estimée se DIT — PE « au coût (capital appelé) » quand la NAV est
  un proxy d'appels, « courbe simplifiée » à 2 points pour un client sans historique, perf de
  ligne > ±100 % caviardée (la ligne reste, la valeur aberrante non — D-UI-9).
- **Adaptivité par la donnée** : le jeu de colonnes du tableau détail est calculé
  (`perf["cote_cols"]`, union des jeux des contrôles d'époque, colonne 100 % vide non
  imprimée) ; chapeau PE nommant les classes réellement présentes ; widget vide supprimé, pas
  excusé. Le template obéit (D28), il ne décide plus.
- **Échec bruyant** (L5) : enveloppe inconnue → « Autre (à qualifier) » + ⚠ au rapport (jamais
  de repli silencieux) ; ligne perdue entre store et HTML → QC de traversée rouge, le
  reporting ne s'imprime pas amputé.
- **Règles uniques partagées** : `classe_liquidite()` sert le donut Classes ET le widget
  Disponibilités — une taxonomie, deux consommateurs.

## 4 — Les référentiels partagés (MCP)

Serveur MCP `referentiels-rhetores`, adossé à Postgres, **conteneur Docker local** (D55 — pas
de Railway). Quatre tables : acteurs, successions, gabarits, ISIN. Quatre verbes :

| Verbe | Qui | Quoi |
|---|---|---|
| `ref_bundle` | tous | lecture par sections (le bundle complet dépasse la taille d'un résultat d'outil) |
| `ref_propose` | tous | dépôt d'une proposition dans la file d'adjudication — un run PROPOSE, ne canonise jamais (D34) |
| `ref_arbitrer` | **admin** | accepte (écriture canonique + marquage, même transaction) ou rejette (tracé, jamais supprimé) |
| `ref_adjudications` | admin : tout ; autres : les leurs | la file, par statut |

La **provenance ne porte jamais de nom de fichier** (D44) : empreinte sha256 du contenu +
gabarit apparié + date d'arrêté. Motif : le bundle est servi à chaque CGP — un nom de fichier
divulguerait un client entre confrères. Le paquet embarque un **snapshot vendoré** en repli
(D35), avec obligation de dire au CGP quand il sert.

**Le dashboard admin** est un artefact live Cowork (validé en conditions réelles le 31/07 :
proposition déposée, visible en file, rejetée depuis l'artefact, trace au Postgres).
Gouvernance **D56** : la source versionnée fait foi (`dashboard/dashboard_admin_artifact.html`),
l'artefact n'est qu'un déploiement ; règles et garde-fous dans `dashboard/README.md`.

**Visibilité en remote (futur)** : les CGP n'atteignent que `ref_bundle` + `ref_propose` ;
l'arbitrage et la mise à jour du contexte de marché (D52 : drag & drop admin, jamais les CGP)
restent admin-only ; les stores clients ne transitent jamais par le MCP. Seul chantier neuf au
portage : l'authentification.

## 5 — Le filet (ce qui empêche de régresser)

| Garde | Ce qu'elle prouve | Où |
|---|---|---|
| `selfcheck.py` + `CHECKSUMS.json` | paquet intègre (134 fichiers) | skill, étape 0 |
| **Golden** (8 fixtures) | valeurs clés (actif brut/dettes/net), QC vert, déterminisme, `curve_degraded`, `cote_cols` — un affichage qui change sans décision est une régression | `tests/run_tests.py` (`--record` = golden déplacé, diff PROUVÉ obligatoire) |
| **L3a** | équivalence Excel/store **à l'octet** (manifeste + HTML) | `tests/test_l3a.py` (stores dérivés par `outils_lecteur/deriver_stores.py`, D47) |
| **test_pnc.mjs** | bloc PE : présence W1–W4, bascule de vues, D-UI-2 — bi-mode, HORS suite courante, à lancer si le PE bouge | `tests/` (jsdom hors paquet) |
| QC comptables 9/9 + traversée | identités internes du rendu, aucune ligne perdue | `p2_fill.py` |
| Garde **D44** | aucun identifiant client dans le paquet (mord aussi les commentaires et les exemples trop plausibles) | `regenerer_checksums.py` (racine du fork) |
| `verifier_pieges.py` (N3) | aucun piège d'émetteur en dur dans SKILL.md — le priming vient des profils | racine du fork |
| Contrôles d'époque (3) | parité de blocs perçue par le CGP — se CONFRONTENT, ne se recopient pas | `reference/controles_epoque/` |

Discipline associée : resceller après tout changement de `skill/` ; rendre les clients réels
depuis un répertoire **jetable** ; une livraison se vérifie **au contenu du fichier livré** ;
dé-identifier, ne jamais supprimer la provenance.

## 6 — Le fork comme atelier

```
FORK-Cowork/
├── skill/                    le paquet distribué (scellé, 134 fichiers)
│   ├── SKILL.md              protocole de l'agent (§0 modes → §7 assets)
│   ├── p1_engine/            moteur + bank/ + lecteur_store + tests (golden, L3a, test_pnc)
│   └── assets/               snapshot référentiels, ISIN v0, template structure
├── docs/                     registre D32–D56, CDC v5, specs, revues, chantier UI, CE document
├── reference/controles_epoque/   les 3 rendus-juges + README (défauts connus consignés)
├── runs/                     dossiers de runs réels, archivés, rejouables (interagyr_2026-07)
├── outils_lecteur/           dérivation des stores de vérité (importe validation_app, D47)
├── dashboard/                source versionnée du dashboard admin (D56)
├── seed/                     construction du bundle référentiels initial
├── regenerer_checksums.py    rescellement (garde D44 intégrée)
├── verifier_pieges.py        garde N3
├── REPRISE.md                l'état courant en une page — À LIRE EN PREMIER
└── JOURNAL.md                entrées datées + « À faire ensuite »
```

La mémoire du projet est **sur disque, pas dans les conversations** : chaque session s'ouvre
sur `REPRISE.md`, chaque décision a un numéro et un motif au registre, chaque écart au schéma
de main a son entrée R*. Un renversement de décision d'époque s'arbitre explicitement et se
consigne (précédent : D53, le canvas PE supprimé le 23/07 « à la demande du CGP » et rétabli
le 31/07 sur arbitrage — le test qui gardait l'absence a été retourné en garde de présence).

## 7 — État au 31/07/2026 et fronts ouverts

**Fait et prouvé** : pipeline complet sur run réel (INTERAGYR, 11 min vs 25, QC 9/9), chantier
UI soldé 8/8, dashboard admin validé, MCP local vivant. **Fronts** (détail au JOURNAL « À faire
ensuite ») : contexte de marché T3-26 (dernier bloc vide), canal éditorial (spec courte),
arrêtés D50 (l'historique par accumulation — c'est lui qui transforme les courbes dégradées en
vraies courbes), run Gronier B-v, chantiers de données (courbe à sauts de flux E7, Modified
Dietz lignes, VL non cotées, SRI du référentiel ISIN vide sur 261 lignes).
