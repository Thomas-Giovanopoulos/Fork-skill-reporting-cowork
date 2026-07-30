# Plan de la session de développement — 2026-07-29

> Périmètre arbitré avec Thomas : **le filet d'extraction d'abord**, puis le seed corrigé, puis le
> producteur de propositions. Motif : la limite **LIM8** — les 7 fixtures de régression exercent le *rendu*,
> alors que signatures et pièges pilotent l'*extraction*. Écrire le producteur de propositions sans filet
> reviendrait à produire du code dont la justesse ne se constaterait qu'à la lecture d'un reporting client.

## L'idée directrice : deux filets, pas un

C'est le point de conception de cette session, et il vient d'une distinction qu'on n'avait pas faite.
« Tester l'extraction » recouvre deux choses de nature opposée :

| | Ce qui est testé | Nature | Assertion possible |
|---|---|---|---|
| **Filet A** | L'**appariement** d'un document à son profil | **déterministe** — du code sur du texte extrait | **égalité exacte** : ce document doit donner ce profil |
| **Filet B** | La **qualité de l'extraction** des valeurs | non déterministe — un subagent lit le document | **invariants tolérants** : Σ lignes = total ± 1 €, ISIN présents, champs requis peuplés |

Les confondre, c'est se condamner soit à des tests fragiles (comparer du texte produit par un LLM), soit à
n'en écrire aucun. **Le filet A est celui qu'il faut construire d'abord** : il est exactement ce que le
corpus du 29/07 permet, il est rigoureusement vérifiable, et il n'existe pas du tout aujourd'hui.

Le filet B viendra ensuite, et il n'assertera **jamais** l'égalité de chaînes : seulement les invariants que
les profils déclarent déjà (`invariant_controle`) et la présence des champs que `champs_publies` annonce.

## Séquence

### 1 — Table de vérité de l'appariement

Pour chacun des **37 documents** du corpus, le triplet attendu `(emetteur_code, gabarit, valide_depuis)`,
plus la périodicité *informative* et la provenance (original / réédition du 24/07). Dérivée des quatre
études d'émetteur, pas devinée.

> **Corrigé le 29/07 : 37, pas 38.** Le corpus compte **37 PDF** — c'est ce que la table de vérité
> énumère —, plus `Positions Overview (1).xlsx`, qui n'est pas un PDF et reste **hors périmètre** de
> cette session (voir « Ce qui reste hors de cette session »). Le compte de 38 additionnait les deux.

C'est une **fixture**, écrite avant le code qu'elle vérifie. Elle a une valeur propre indépendamment du
matcher : c'est la première fois que « quel profil pour quel document » est écrit noir sur blanc et
opposable.

Points d'attention connus, tous documentés : Wealins fait **2 gabarits et non 1**, et le nom de fichier s'y
trompe **2 fois sur 4** ; Cardif fait **2 gabarits successifs** (fenêtre de validité) ; Himalia **1 seul**,
sans borne ; Spirica **1 seul**, mais sa série est faite de rééditions donc muette sur la dérive.

### 2 — Le matcher (B10 / N4)

Code déterministe, conforme à ce que le corpus a établi — et non à ce que l'étude d'origine supposait :

- **couche 1 = pré-filtre d'émetteur**, jamais signature de gabarit (LIM6). Les polices y servent, le
  `Producer` seul ne suffit pas, et `template_id_natif` est un pré-filtre de *famille* — il ne court-circuite
  rien (`TYPE_MODELE=66` survit à la refonte Cardif).
- **couches 2 et 3 portent l'appariement**, avec `sections_requises` / `sections_optionnelles` : sans cette
  distinction, un gabarit à géométrie variable se fait passer pour plusieurs (constaté sur trois émetteurs).
- **choix de version par date d'arrêté**, selon la fenêtre de validité de D42.
- **le nombre de pages reste hors matching** (acquis de l'étude d'origine, confirmé).

### 3 — Le harnais

Exécute le matcher sur les 37 documents, compare à la table de vérité, et **affiche de façon incrémentale**
— la leçon de `run_tests.py`, qui n'imprime qu'à la fin et devient indistinguable d'un blocage. Découpable
par émetteur, pour tenir dans la limite de 45 s d'un appel.

### 4 — Le seed corrigé

Une fois le matcher vérifié, appliquer au `seed/gabarits.json` ce que le corpus impose : Wealins scindé en
deux profils, `Arbitrages` et `Aperçu des fonds` rétrogradées en ancres conditionnelles, la distinction
requis / optionnel sur les sept profils, et la fenêtre de validité de D42. **Rien ne doit être chargé en
base avant cette étape.**

### 5 — Le producteur de propositions

Alors seulement, et avec un filet : détecter un drift, émettre un `ref_propose`. Le MCP est vérifié de bout
en bout depuis le 29/07, la boucle est donc démontrable.

## Ce qui reste hors de cette session, et pourquoi

- **Le lecteur de forme-store (A1/L2)** : la colonne vertébrale D20, mais elle ne mène pas au test de
  réussite du projet. À reprendre juste après.
- **La 8ᵉ fixture Historique** : validée par Thomas, courte, mais elle couvre le *rendu* — elle ne comble
  pas LIM8, qui est le motif de cette session.
- **Le test D34 depuis un compte non-admin** : seul contrôle manquant du MCP.
- **Nortia** (aucune métadonnée PDF), **Spirica sur archives réelles**, et `Positions Overview (1).xlsx`.

## Le critère de réussite de la session

Un énoncé, vérifiable : **32 des 37 documents du corpus s'apparient à leur profil attendu et les 5 autres
sont signalés, et un document Cardif de 2024 ne s'apparie pas au profil Cardif de 2025.** Ce second membre
est le plus important — c'est lui qui prouve que la fenêtre de validité fonctionne, et c'est le cas que le
profil B.7 actuel échouerait à traiter.

> **Reformulé le 29/07.** L'énoncé disait « les 38 documents s'apparient » : littéralement faux, et de
> deux façons. Le corpus fait 37 PDF, et **5 d'entre eux — les Nortia — sont non établis par
> construction** : aucun profil n'a été écrit pour eux, ils n'ont aucune métadonnée PDF, et le harnais
> les sort dans une rubrique `SIGNALÉ` sans les compter en échec. Exiger leur appariement rendrait le
> critère inatteignable ; le taire rendrait le « 32/32 » flatteur. La forme juste est donc **32 appariés
> et 5 signalés** — le second terme fait partie du critère, il n'en est pas l'exception.
