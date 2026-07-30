# WEALINS S.A. — combien de gabarits distincts un même émetteur expose-t-il ?

> **2026-07-29.** Test empirique de la décision produit « un assureur peut avoir 50 templates, il
> nous faut les 50 ». Corpus : 7 PDF WEALINS, 2 contrats (FC051727, FC055211), 3 intitulés de
> fichier différents, 4 dates d'édition entre janvier 2025 et juillet 2026.
> Référence amont : `etude_signature_gabarits_2026-07-27.md`, partie A et §B.6.
> Tous les documents sont en **texte natif propre** (zéro OCR). Aucun n'est une réédition : la date
> de création suit de 3 à 4 semaines la date d'arrêté dans les 7 cas.

**Réponse courte.** WEALINS n'expose pas 4 gabarits mais **2**, et les intitulés de fichier se
trompent dans 2 cas sur 4. Les sous-templates **ne circulent pas en autonomie** : les 7 documents
sont composites, y compris celui qui s'appelle « Information annuelle ». La clé qui sépare les deux
gabarits est un **label en capitales dans l'en-tête de l'annexe**, `INFORMATION ANNUELLE :` contre
`INFORMATION TRIMESTRIELLE :`.

---

## (a) Inventaire — pages, métadonnées, structure

Notation utilisée dans tout le document :

| code | fichier | contrat | arrêté | pages |
|---|---|---|---|---|
| `a17` | `2025 Relevé annuel Wealins FC051727 HANAMI.pdf` | FC051727 | 31/12/2025 | 26 |
| `a55` | `2025 Relevé annuel Wealins FC055211 HANAMI.pdf` | FC055211 | 31/12/2025 | 15 |
| `i55` | `Information annuelle FC055211_31 12 24.pdf` | FC055211 | 31/12/2024 | 11 |
| `q17` | `Situation trimestrielle FC051727_31 03 26.pdf` | FC051727 | 31/03/2026 | 19 |
| `q55` | `Situation trimestrielle FC055211.pdf` | FC055211 | 31/03/2026 | 10 |
| `j17` | `FC051727-20260630.pdf` | FC051727 | 30/06/2026 | 18 |
| `j55` | `FC055211-20260630.pdf` | FC055211 | 30/06/2026 | 10 |

### Couche 1 — métadonnées

`pdfinfo` et `pypdf` donnent le **même dictionnaire minimal partout** : `/Author` et
`/CreationDate`, rien d'autre. Pas de `/Producer`, pas de `/Creator`, pas de XMP, pas de signets,
pas de pièces jointes.

| code | Author | CreationDate | version PDF | format |
|---|---|---|---|---|
| `a17` | Lifeware | 27/01/2026 10:46:02 CET | **1.4** | A4 596×843 |
| `a55` | Lifeware | 27/01/2026 10:46:07 CET | **1.4** | A4 596×843 |
| `i55` | Lifeware | 28/01/2025 14:26:04 CET | **1.4** | A4 596×843 |
| `q17` | Lifeware | 22/04/2026 14:50:54 CEST | **1.6** | A4 596×843 |
| `q55` | Lifeware | 22/04/2026 14:37:36 CEST | **1.6** | A4 596×843 |
| `j17` | Lifeware | 17/07/2026 17:18:41 CEST | **1.6** | A4 596×843 |
| `j55` | Lifeware | 17/07/2026 17:29:56 CEST | **1.6** | A4 596×843 |

Deux corrections à apporter à la partie A, qui laissait la ligne WEALINS vide dans le tableau des
moteurs de génération :

1. **`Author: Lifeware` est un identifiant d'émetteur exploitable.** Lifeware est un progiciel de
   gestion de contrats d'assurance vie. Ce champ est présent, identique et sans variation sur les
   7 documents, sur 18 mois d'éditions. La couche 1 de WEALINS n'est donc pas vide : elle est
   *mono-valuée*. Elle sert de pré-filtre émetteur ; elle ne discrimine **aucun** gabarit.
2. **La version PDF sépare exactement les deux familles** — 1.4 pour les trois annuels, 1.6 pour les
   quatre trimestriels. Ce n'est pas un effet de calendrier : `a55` (janvier 2026) est en 1.4 alors
   que `q55` (avril 2026) est en 1.6, à trois mois d'écart. Les deux chaînes d'assemblage sont donc
   réellement distinctes. **Mais je ne recommande pas d'en faire un critère de match** : c'est un
   sous-produit de la bibliothèque d'assemblage, qu'une montée de version côté Lifeware peut aligner
   du jour au lendemain. À conserver comme *indice de confirmation*, jamais comme discriminant.

### Couche 3 — polices, par plage de pages

Les jeux de polices révèlent les frontières de génération mieux que le texte. Relevé sur `a55`
(15 p.) et `q55` (10 p.) :

| pages `a55` | rôle | polices |
|---|---|---|
| 1 | page adresse | Calibri, CalibriBold |
| 2 | courrier | + **Museo300/700/900TT** |
| 3–6 | corps réglementaire | + CalibriItalic |
| 7 | page Loi Pacte | Calibri, CalibriBold, CalibriItalic, **Museo300/700/900TT** |
| 8–15 | annexe booklet | Calibri, CalibriBold, **ArialMT**, CalibriTT — **plus aucun Museo** |

| pages `q55` | rôle | polices |
|---|---|---|
| 1 | page adresse | Calibri, CalibriBold |
| 2 | courrier | + **Museo300/700/900TT** |
| 3–4 | corps situation | + CalibriTT |
| 5–10 | annexe booklet | Calibri, CalibriBold, **ArialMT** — **plus aucun Museo** |

Lecture : **la police Museo (charte WEALINS) est présente sur le courrier, le corps et la page Loi
Pacte, et absente de l'annexe** ; l'annexe est la seule à utiliser ArialMT. Il y a donc
**deux moteurs de rendu**, pas quatre : la chaîne « papier à en-tête WEALINS » et la chaîne
« booklet ». La page Loi Pacte appartient typographiquement à la première.

---

## (b) Matrice gabarit × document

Comptage d'occurrences par document, `grep -c` sur le texte `pdftotext -layout` complet.
`—` = 0 occurrence.

### Ancres présentes sur les 7 documents (niveau émetteur)

| ancre | a17 | a55 | i55 | q17 | q55 | j17 | j55 |
|---|---|---|---|---|---|---|---|
| `Wealins Capi France` | 3 | 3 | 3 | 4 | 4 | 4 | 4 |
| `Contrat de capitalisation` | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| `Caractéristiques du contrat` | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `Profil d'investissement` | 2 | 1 | 1 | 2 | 1 | 2 | 1 |
| `Valeur totale du fonds au` | 2 | 1 | 1 | 2 | 1 | 2 | 1 |
| `R.C.S.: Luxembourg B 53682` | 8 | 6 | 5 | 3 | 3 | 3 | 3 |
| `TVA Intra-com.: LU 166 094 20` | 8 | 6 | 5 | 3 | 3 | 3 | 3 |
| `12, rue Léon Laval` | 8 | 6 | 5 | 3 | 3 | 3 | 3 |
| `wealins.com` | 17 | 13 | 11 | 7 | 7 | 7 | 7 |
| `Client & Partner Services` | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `cps@wealins.com` | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `Chief Operating Officer` | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| `Type d'Actifs` | 6 | 2 | 2 | 6 | 2 | 6 | 2 |
| `<booklet>` | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `LEU.326` | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| `Leudelange, le ` | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

Ces 16 ancres identifient **l'émetteur WEALINS et le produit Wealins Capi France**, pas un gabarit.
Elles sont l'invariant de niveau supérieur.

### Ancres qui séparent les familles

| ancre | a17 | a55 | i55 | q17 | q55 | j17 | j55 |
|---|---|---|---|---|---|---|---|
| **`INFORMATION ANNUELLE :`** | **17** | **8** | **5** | — | — | — | — |
| **`INFORMATION TRIMESTRIELLE :`** | — | — | — | **15** | **6** | **14** | **6** |
| `Information annuelle 20` (titre courrier) | 1 | 1 | 1 | — | — | — | — |
| `Situation de contrat` (titre courrier) | — | — | — | 1 | 1 | 1 | 1 |
| `Annexe:` + `Situation du contrat` | — | — | — | 1 | 1 | 1 | 1 |
| `Information sur l'évolution du contrat` | 1 | 1 | 1 | — | — | — | — |
| `Situation au 3[0-1]/…` | 2 | 2 | 1 | — | — | — | — |
| `Valeur de rachat au 0…` | 1 | 1 | 1 | — | — | — | — |
| `Information sur les services et opérations` | 1 | 1 | 1 | — | — | — | — |
| `Frais de gestion administrative` | 1 | 1 | 1 | — | — | — | — |
| `Informations relatives aux unités de compte` | 1 | 1 | 1 | — | — | — | — |
| `Frais annuels supportés` | 1 | 1 | 1 | — | — | — | — |
| `Autres informations` | 1 | 1 | 1 | — | — | — | — |
| `Opérations de rachat` | 1 | 1 | 1 | — | — | — | — |
| `Transformation du contrat` | 1 | 1 | 1 | — | — | — | — |
| `Loi Pacte` | 1 | 1 | 1 | — | — | — | — |
| `Rendement 20[0-9][0-9]` | 2 | 1 | 1 | — | — | — | — |
| `Frais spécifiques au fonds en` | 2 | 1 | 1 | — | — | — | — |
| `Date de la situation` | — | — | — | 1 | 1 | 1 | 1 |
| `Frais prélevés au titre du` | — | — | — | 1 | 1 | 1 | 1 |
| `La situation du contrat à la date mentionnée` | — | — | — | 1 | 1 | 1 | 1 |

**La coupure est binaire et sans zone grise.** Il n'existe pas une seule ancre qui soit partagée
entre `{a17, a55, i55}` et `{q17, q55, j17, j55}` autrement que dans le bloc des 16 ancres
émetteur. Aucun document intermédiaire, aucun recouvrement partiel.

### Ancres conditionnelles — à ne pas confondre avec des discriminants

| ancre | a17 | a55 | i55 | q17 | q55 | j17 | j55 | condition |
|---|---|---|---|---|---|---|---|---|
| `Aperçu des fonds` | 2 | — | — | 2 | — | 2 | — | **nb FID ≥ 2** |
| `Arbitrages et/ou changement de banque dépositaire` | 1 | — | — | — | — | — | — | **arbitrage survenu dans l'année** |
| `Montant des primes depuis la date d'effet` | 1 | 1 | — | — | — | — | — | annuel **et** exercice N-1 postérieur à la date d'effet |
| `Ces primes ont été allouées comme suit` | 1 | — | 1 | — | — | — | — | prime versée dans l'exercice |

Ces quatre libellés figurent dans la liste d'ancres du §B.6, deux d'entre eux (`Aperçu des fonds`,
`Arbitrages et/ou changement de banque dépositaire`) en position d'ancre de rang égal aux autres.
**C'est une erreur du seed v0** : `Arbitrages…` n'apparaît que dans 1 document sur 7 et
`Aperçu des fonds` dans 3 sur 7, exclusivement quand le contrat porte au moins deux fonds dédiés.
Exiger ces ancres ferait échouer le match de `a55` et `i55`, qui sont pourtant le même moule que
`a17`. Elles doivent passer en `ancres_optionnelles` avec leur condition d'apparition documentée.

**Bilan de la révision du §B.6** : sur les 13 ancres listées, 7 sont de niveau émetteur (donc non
discriminantes), 4 sont de bons discriminants du gabarit annuel, 2 sont conditionnelles et doivent
être rétrogradées.

---

## (c) Verdict — 2 gabarits, et la clé qui les sépare

### Le nombre

**Deux gabarits, pas quatre.** Les trois intitulés de fichier et le motif `FC…-AAAAMMJJ` se
répartissent ainsi :

| gabarit | documents | intitulés de fichier concernés |
|---|---|---|
| **G1 — information annuelle** | `a17`, `a55`, `i55` | « 2025 Relevé annuel Wealins … », « Information annuelle … » |
| **G2 — situation de contrat trimestrielle** | `q17`, `q55`, `j17`, `j55` | « Situation trimestrielle … », « FC…-20260630 » |

Deux résultats à souligner, parce qu'ils vont dans deux directions opposées :

**Faux positifs du nom de fichier — 2 cas sur 4.** `Information annuelle FC055211_31 12 24.pdf`
et `2025 Relevé annuel Wealins FC055211 HANAMI.pdf` portent des intitulés que rien ne relie, et
sont le même gabarit à un an d'écart. `FC055211-20260630.pdf` n'a aucun mot en commun avec
`Situation trimestrielle FC055211.pdf`, et c'est le même gabarit au trimestre suivant. Le §A.1
point 3 (« l'identification se fait sur le contenu, jamais sur le nom de fichier ») est ici vérifié
de façon quantitative : **le nom de fichier se trompe dans 2 cas sur 4.**

**Mais la décision produit reste fondée.** Ce même émetteur, sur un seul produit
(Wealins Capi France) et un seul distributeur, expose bel et bien **2 gabarits irréductibles**, dont
l'un contient un bloc réglementaire (Loi Pacte) que l'autre n'a pas et dont le corps n'a aucune
ancre en commun avec l'autre. Extrapoler : WEALINS commercialise plusieurs produits
(assurance vie, capitalisation, contrats de droit belge/français/…), chacun avec ses variantes de
périodicité. L'ordre de grandeur « quelques dizaines de gabarits par assureur » est cohérent avec
ce qu'on observe. **La décision « il nous faut les N templates » est confirmée ; ce qui est
infirmé, c'est qu'on puisse les compter en comptant les noms de fichier.** Ici on aurait
sur-compté (4 au lieu de 2). Ailleurs on pourrait sous-compter.

### La clé, formulée précisément

```
Discriminant primaire (couche 2, un seul token) :
  le label en CAPITALES suivi de « : » dans l'en-tête de chaque page de l'annexe booklet
    ^INFORMATION\s+(ANNUELLE|TRIMESTRIELLE)\s*:\s*<date>\s*-\s*<n° contrat>
  → G1 si le mot capté est ANNUELLE, G2 si c'est TRIMESTRIELLE.
```

Trois propriétés font de ce token le bon candidat :

1. **Il est répété sur chaque page de l'annexe**, pas une seule fois — vérifié : présent sur les
   pages 10 à 26 de `a17` (17 pages d'annexe), 8 à 15 de `a55`, 7 à 11 de `i55`, 5 à 19 de `q17`,
   5 à 10 de `q55` et `j55`, 5 à 18 de `j17`. Aucun trou. Une page d'annexe manquante ou mal
   extraite ne fait donc pas perdre le discriminant.
2. **C'est un intitulé de nature de document, pas une fenêtre de cumul.** Il qualifie le document
   (« voici l'information annuelle du contrat X arrêtée au JJ/MM/AAAA »), et non une période
   d'agrégation de montants. C'est précisément ce qui le distingue des faux amis de la section (e).
3. **Il survit à la dérive** : identique au caractère près entre `i55` (édition janvier 2025) et
   `a55`/`a17` (édition janvier 2026), alors que d'autres ancres du même document ont bougé
   (section f).

```
Confirmation secondaire (couche 3, structurelle) : nombre de sous-templates présents.
  G1 = 4 blocs  (courrier | corps réglementaire | page Loi Pacte | annexe booklet)
  G2 = 3 blocs  (courrier | corps situation     | ———————————— | annexe booklet)
  → la présence/absence du bloc Loi Pacte est un discriminant structurel binaire.
```

Le nombre de sous-templates est donc **une clé valable, mais de rang secondaire** : il faut avoir
segmenté le document pour l'évaluer, alors que le token de la clé primaire se lit d'un `grep`.
Ordre d'évaluation recommandé : (1) les 16 ancres émetteur → WEALINS ; (2) le token
`INFORMATION (ANNUELLE|TRIMESTRIELLE) :` → G1 ou G2 ; (3) comptage des blocs de pagination →
confirmation.

### Convention de nommage proposée

```
wealins__capi-france__information-annuelle__annuel        (G1)
wealins__capi-france__situation-de-contrat__trimestriel   (G2)
```

Le segment produit (`capi-france`) est explicitement dans le texte (`Wealins Capi France`, présent
3 à 4 fois par document) et anticipe les autres produits du même émetteur. Le segment gabarit
reprend le titre du courrier, le segment périodicité reprend le token de l'annexe.

---

## (d) Le composite — quels documents, quelles frontières, autonomie des sous-templates

### Le composite se confirme, et sur les 7 documents

Le §B.6 décrivait le composite pour le seul relevé annuel. **Il est en réalité l'architecture
générale de l'émetteur** : les 7 documents sont des concaténations de blocs à pagination locale
propre. La preuve la plus directe est l'artefact `<booklet>`, une balise de template restée en
texte brut, **présente exactement une fois dans chacun des 7 fichiers**, en tête de la première
page de l'annexe (page 8 de `a55`, page 7 de `i55`, page 5 de `q55`). Un même document ne
contiendrait pas la balise d'ouverture d'un autre moteur s'il n'était pas assemblé.

### Frontières, mesurées

Trois signaux concordent pour délimiter les blocs : la **pagination locale**, le **jeu de polices**
et le **disclaimer d'annexe** (`Les données, qui ont été obtenues de différentes sources…`, présent
sur toutes les pages d'annexe et sur aucune autre).

**G1 — `a55` (15 p.)**

| pages | bloc | pagination | frontière détectable par |
|---|---|---|---|
| 1 | page adresse | **aucun footer** | absence totale de footer |
| 2 | courrier « Information annuelle 2025 » | `1/1` | dénominateur = 1 |
| 3–6 | corps réglementaire | `1/4` → `4/4` | changement de dénominateur |
| 7 | page Loi Pacte | **aucun compteur** | absence de compteur + titre `Loi Pacte` |
| 8–15 | annexe booklet | `Page 1 / 8` → `Page 8 / 8` | préfixe littéral `Page `, ArialMT, `<booklet>`, disclaimer |

**G1 — `a17` (26 p.)** : 1 / 2 / 3–8 (`1/6`→`6/6`) / 9 (Loi Pacte) / 10–26 (`Page 1/17`→`17/17`).
**G1 — `i55` (11 p.)** : 1 / 2 / 3–5 (`1/3`→`3/3`) / 6 (Loi Pacte) / 7–11 (`Page 1/5`→`5/5`).

**G2 — `q55` et `j55` (10 p.)**

| pages | bloc | pagination |
|---|---|---|
| 1 | page adresse | aucun footer |
| 2 | courrier « Situation de contrat » | `1/1` |
| 3–4 | corps situation | `1/2` → `2/2` |
| 5–10 | annexe booklet | `Page 1 / 6` → `Page 6 / 6` |

**G2 — `q17` (19 p.)** : 1 / 2 / 3–4 (`1/2`→`2/2`) / 5–19 (`Page 1/15`→`15/15`).
**G2 — `j17` (18 p.)** : 1 / 2 / 3–4 (`1/2`→`2/2`) / 5–18 (`Page 1/14`→`14/14`).

Observation utile pour l'extraction : **le corps de G2 est figé à 2 pages** sur les 4 documents,
indépendamment du nombre de FID (1 ou 2), alors que le corps de G1 varie de 3 à 6 pages. G2 est
donc structurellement plus prévisible que G1.

### Les sous-templates circulent-ils seuls ? — Non

C'était l'hypothèse la plus lourde de conséquences de la mission, et **elle est réfutée**.

`Information annuelle FC055211_31 12 24.pdf` n'est **pas** le sous-template n°2 extrait seul. C'est
le composite complet à 4 blocs, arrêté au 31/12/2024 :

- p. 1 — page adresse ;
- p. 2 — courrier `Information annuelle 2024`, signé COO/CEO, pagination `1/1` ;
- p. 3–5 — corps réglementaire, `1/3` → `3/3` ;
- p. 6 — page Loi Pacte, sans compteur ;
- p. 7–11 — annexe booklet, `Page 1 / 5` → `Page 5 / 5`, en-tête
  `INFORMATION ANNUELLE : 31/12/2024 - FC055211`, artefact `<booklet>` en p. 7.

Le fichier fait 11 pages là où le sous-template n°2 seul en ferait 3. Son nom reprend simplement
le titre du courrier (`Information annuelle`), là où les deux autres fichiers de 2026 ont été
renommés par un tiers en « Relevé annuel ». **Aucun des 7 documents n'est un sous-template isolé.**

Conséquence pour le produit : le découpage en enfants **reste une commodité de parsing**, il n'est
pas — sur ce corpus — une réalité de circulation chez l'émetteur. Le profil doit donc être
**composite unique avec segmentation interne** plutôt que « un profil par sous-template », et le
point 3 du §A.5 se tranche en faveur de la première branche pour WEALINS.

Réserve honnête : ce corpus ne contient aucun envoi partiel, et rien n'interdit à WEALINS d'émettre
un jour la page Loi Pacte seule (elle est autoportante : titre réglementaire, tableau complet,
footer propre). L'architecture de segmentation devrait rester capable d'accueillir un sous-template
reconnu isolément, sans que ce soit le cas nominal.

---

## (e) Périodicité — le token, et les pièges écartés

La périodicité **est lisible dans le document**, mais un seul token la porte proprement.

### Le token retenu

```
^INFORMATION\s+(ANNUELLE|TRIMESTRIELLE)\s*:\s*
```
en-tête de chaque page d'annexe. Capitales significatives. Nature de document, pas fenêtre de cumul.
Zéro ambiguïté sur les 7 documents, présent sur 100 % des pages d'annexe.

### Les pièges — quantifiés, et c'est spectaculaire

Le corpus WEALINS fournit un contre-exemple qui invalide toute approche par comptage du mot
« trimestre ». Occurrences de la sous-chaîne, insensible à la casse :

| sous-chaîne | a17 (G1) | a55 (G1) | i55 (G1) | q17 (G2) | q55 (G2) | j17 (G2) | j55 (G2) |
|---|---|---|---|---|---|---|---|
| `trimestre` | **10** | **5** | **5** | 3 | 2 | 3 | 2 |
| `trimestriel` | — | — | — | 15 | 6 | 14 | 6 |
| `annuel` | 22 | 13 | 10 | — | — | — | — |

**Le mot « trimestre » est plus fréquent dans les documents ANNUELS que dans les trimestriels** —
10 contre 3, 5 contre 2. Un classifieur naïf par fréquence de « trimestre » rangerait les relevés
annuels en trimestriels. Trois sources à ce piège :

1. Le tableau `Rendement 2025` de l'annexe annuelle, dont les colonnes sont
   `1er trimestre | 2e trimestre | 3e trimestre | 4e trimestre | Année` — 4 occurrences de
   « trimestre » dans un document annuel (`a55` p. 9).
2. La note de bas de page `(*)` de la page 1 d'annexe, présente **dans les 7 documents** :
   « … s'explique par le prélèvement des frais d'assurance **du dernier trimestre** sur la valeur
   du (des) fonds… ». C'est du boilerplate, il ne dit rien de la périodicité du document.
3. Dans G2, le libellé `Frais prélevés au titre du 1 er trimestre 2026:` (`q55` p. 3) et
   `Frais prélevés au titre du 2 ème trimestre 2026:` (`j55` p. 3).

**Le piège Cardif est reproduit à l'identique sur le point 3.** `Frais prélevés au titre du
[n]e trimestre [AAAA]` est une **fenêtre de cumul de frais**, structurellement analogue au
« Cumul des opérations pour l'année » de Cardif, et son pendant annuel existe :
`Information sur les services et opérations et les coûts et frais y relatifs en 2025` (`a55` p. 4).
Ces deux libellés coïncident ici avec la périodicité réelle, mais **par construction ils décrivent
la période d'agrégation des montants, pas la fréquence d'émission** — un relevé mensuel pourrait
afficher un cumul trimestriel de frais. Ils sont donc utilisables comme **confirmation
convergente**, pas comme discriminant.

**Le piège Spirica (mot commercial) n'est pas présent** : rien dans le corpus WEALINS n'emploie
« annuel »/« trimestriel » pour désigner une offre ou un service. Vérifié : les 22 occurrences de
`annuel` dans `a17` sont toutes dans des libellés de nature de document, de section
(`Frais annuels supportés par chaque unité de compte`) ou dans l'en-tête d'annexe.

**Le piège de la date d'arrêté est vérifié** : `i55` est un document **annuel** arrêté au
**31/12/2024**, et un trimestriel WEALINS tomberait aussi un 31/12. La date d'arrêté ne discrimine
pas — conformément au §A.4 point 2.

### Récapitulatif de la décision de périodicité

| signal | poids | commentaire |
|---|---|---|
| `INFORMATION (ANNUELLE\|TRIMESTRIELLE) :` en en-tête d'annexe | **décisif** | label de nature, répété par page |
| titre du courrier : `Information annuelle [AAAA]` vs `Situation de contrat` | fort côté G1, **nul côté G2** | le courrier trimestriel ne porte aucun mot de périodicité |
| présence du bloc Loi Pacte | fort | obligation réglementaire annuelle |
| présence de `Rendement [AAAA]` / `Frais spécifiques au fonds en [AAAA]` | fort | pages d'annexe propres à G1 |
| `Frais prélevés au titre du [n]e trimestre` / `…y relatifs en [AAAA]` | confirmation seulement | fenêtre de cumul (piège Cardif) |
| fréquence du mot `trimestre` | **contre-indiqué** | plus fréquent dans les annuels |
| date d'arrêté | nul | un trimestriel peut tomber au 31/12 |

---

## (f) Dérive temporelle — `i55` (éd. 28/01/2025) contre `a55`/`a17` (éd. 27/01/2026)

Le phénomène Cardif se reproduit, mais **avec une amplitude radicalement moindre**. Chez Cardif,
une seule ancre sur onze survivait à 12 mois. Ici, sur les 16 ancres émetteur et les
~12 ancres du gabarit G1, **une seule a changé**, et deux éléments hors signature ont bougé.

### Dérive n°1 — le titre de la page Loi Pacte s'allonge (vraie dérive de gabarit)

`i55` p. 6 :
> `Informations relatives à la performance* brute de frais, aux frais prélevés et aux rétrocessions de commissions`

`a55` p. 7 et `a17` p. 9 :
> `Informations relatives à la performance* brute de frais, à la performance nette de frais, aux frais prélevés et aux rétrocessions de commissions`

Le segment `à la performance nette de frais` a été **inséré** entre janvier 2025 et janvier 2026.
La dérive est présente sur **les deux** réplicats de 2026 : c'est bien un changement d'édition, pas
un artefact d'un contrat. Les **9 colonnes du tableau Loi Pacte sont inchangées** (`Nom du fonds`,
`Société de gestion`, `Indicateur de risque (SRI)`, `Performance brute* [AAAA] (A)`,
`Frais de gestion de l'unité de compte (B)`, `Performance* nette [AAAA] (A-B)`,
`Frais de gestion administrative du contrat (C)`, `Frais totaux (B+C)`,
`Performance finale (A-B-C)`) : seul l'intitulé de page a été mis en conformité avec un contenu qui
existait déjà. Conséquence de matching : ce titre doit être **matché par fragment stable**
(`Informations relatives à la performance` + `aux frais prélevés et aux rétrocessions de`), jamais
par chaîne exacte.

### Dérive n°2 — une phrase supprimée du corps

`i55` p. 4, après le tableau des frais de gestion administrative :
> `Une information plus détaillée concernant les services, opérations, coûts et frais est disponible sur simple demande ou par voie électronique.`

**Absente de `a55` et de `a17`.** Symétriquement, `a55`/`a17` portent un intitulé de section
`Information sur les services et opérations et les coûts et frais y relatifs en 2025` qui existe
aussi dans `i55` (p. 4) — donc l'intitulé n'est pas nouveau, c'est bien la phrase de renvoi qui a
été retirée. Une ancre de moins, sans compensation.

### Ce qui n'a PAS dérivé

L'ordre des sections du corps réglementaire est **identique au libellé près** sur les trois
documents G1, seules les sections conditionnelles s'intercalant :

| section | i55 | a55 | a17 |
|---|---|---|---|
| `Caractéristiques du contrat` | p. 3 | p. 3 | p. 3 |
| `Information sur l'évolution du contrat` | p. 3 | p. 3 | p. 3 |
| `Montant des primes depuis la date d'effet…` *(cond.)* | — | p. 3 | p. 3 |
| `Montants des rachats depuis la date d'effet…` *(cond.)* | — | p. 3 | p. 3 |
| `Situation au [31/12/N-1]` *(cond.)* | — | p. 4 | p. 4 |
| `Situation au [31/12/N]` | p. 3 | p. 4 | p. 4 |
| `Valeur de rachat au [01/01/N+1]` | p. 3 | p. 4 | p. 4 |
| `Information sur les services et opérations et les coûts et frais y relatifs en [N]` | p. 4 | p. 4 | p. 5 |
| `Ces primes ont été allouées comme suit` *(cond.)* | p. 4 | — | p. 5 |
| `Arbitrages et/ou changement de banque dépositaire` *(cond.)* | — | — | p. 6 |
| `Frais de gestion administrative` | p. 4 | p. 5 | p. 7 |
| `Informations relatives aux unités de compte` | p. 5 | p. 5 | p. 7 |
| `Frais annuels supportés par chaque unité de compte` | p. 5 | p. 5 | p. 7 |
| `Autres informations` | p. 5 | p. 5 | p. 7 |
| `Opérations de rachat` | p. 5 | p. 5 | p. 7 |
| `Transformation du contrat` | p. 5 | p. 6 | p. 7 |

L'absence de `Situation au [31/12/N-1]` et de `Montant(s) … depuis la date d'effet` dans `i55`
**n'est pas une dérive** : le contrat FC055211 a pris effet le 11/11/2024, donc l'exercice N-1 de
l'information annuelle 2024 précède la souscription et le moteur supprime les blocs. Point à
signaler comme **incertitude résiduelle** : je ne peux pas distinguer, sur ce seul corpus, cette
suppression conditionnelle d'un enrichissement du gabarit en 2026. Il faudrait une information
annuelle 2024 d'un contrat plus ancien (par exemple FC051727, effet 25/03/2022) pour trancher.
La lecture « conditionnelle » me paraît nettement la plus probable, l'ordre des sections étant
sinon strictement conservé.

### Dérive hors signature — le numéro de fax, et la correction d'un marqueur du §B.6

Le §B.6 érigeait le footer fax en marqueur de sous-template : « Footer fax DIFFÉRENT sur la page
Loi Pacte (26 43 12 74 vs 42 88 84) = marqueur de sous-template ». **Ce marqueur n'est pas
structurel.** Relevé page par page :

| document | pages avec `F: (+352) 42 88 84` | pages avec `F: (+352) 26 43 12 74` |
|---|---|---|
| `i55` (éd. 01/2025) | **aucune** | **2, 3, 4, 5, 6** — toutes |
| `a55` (éd. 01/2026) | 2, 3, 4, 5, 6 | **7** — Loi Pacte seulement |
| `a17` (éd. 01/2026) | 2, 3, …, 8 | **9** — Loi Pacte seulement |
| `q55`, `j55` (éd. 2026) | 2, 3, 4 | aucune |

Lecture : dans l'édition de janvier 2025, **tout le document portait 26 43 12 74, page Loi Pacte
incluse** — il n'y avait aucun différentiel. WEALINS a changé de numéro de fax entre les deux
éditions, la mise à jour a été propagée au courrier et au corps mais **pas au sous-template Loi
Pacte**, resté sur l'ancien numéro. Le « marqueur » du §B.6 est donc le **fossile d'une mise à jour
non propagée**, daté et réversible : il disparaîtra dès que WEALINS corrigera la page Loi Pacte.
À rétrograder de « marqueur de sous-template » à « indice fragile, non daté-stable », et à exclure
de toute condition de match. Les frontières de sous-template doivent s'appuyer sur la pagination,
les polices et le disclaimer d'annexe, qui sont eux invariants sur les 7 documents.

### Dérive hors signature — le signataire

`i55` est signé **Benoit Van Lerberghe**, Chief Operating Officer ; les 6 documents de 2026 sont
signés **Gaëlle Leclaire**, Chief Operating Officer. Le CEO **Luc Rasschaert** est inchangé sur les
7. Conforme au §A.3 : la **fonction** est stable, la **personne** non. Seuls
`Chief Operating Officer` et `Chief Executive Officer` (2 occurrences chacun, sur les 7 documents)
sont utilisables.

---

## (g) Ce qui varie entre réplicats du même gabarit

Comparaison `a17` vs `a55` (même gabarit G1, même édition, deux contrats) puis `q55` vs `j55`
(même gabarit G2, deux trimestres consécutifs du même contrat).

### À exclure formellement du matching

| élément | valeurs observées | cause |
|---|---|---|
| **nombre de pages total** | G1 : 11, 15, 26 — G2 : 10, 18, 19 | nb de FID × nb de lignes de portefeuille |
| **dénominateur de pagination du corps** | `n/3` (i55), `n/4` (a55), `n/6` (a17), `n/2` (les 4 G2) | sections conditionnelles |
| **dénominateur de pagination d'annexe** | `/5`, `/6`, `/8`, `/14`, `/15`, `/17` | nb de FID et de lignes |
| **nombre de blocs FID dans l'annexe** | 1 (FC055211) / 2 (FC051727) | structure du contrat |
| **présence de `Aperçu des fonds`** | seulement si ≥ 2 FID | conditionnelle |
| **présence de `Arbitrages et/ou changement de banque dépositaire`** | seulement `a17` | événement de gestion |
| **noms de FID** | `540709 Banque Thaler SA`, `1719249 CA Indosuez Switzerland S.A.`, `K00149Q5 Quintet Private Bank (Europe) S.A.`, `K00149YU Quintet Private Bank (Europe) S.A.` | dépositaire du fonds dédié — **change même à contrat constant** : FC051727 porte `540709 Banque Thaler SA` au 31/12/2025 et `1719249 CA Indosuez Switzerland S.A.` au 31/03/2026 |
| **adresse du souscripteur** | `50, allée des Pailles en Queue, Boucan Canot…, RE-97434 Saint-Denis` jusqu'au 31/03/2026, puis `57 avenue Georges Mandel, F-75116 Paris` au 30/06/2026 | déménagement entre avril et juillet 2026 |
| **dates d'effet / d'échéance** | FC051727 : 25/03/2022 → 25/03/2052 ; FC055211 : 11/11/2024 → 11/11/2054 | contrat |
| **taux de frais de rachat** | 0,50 % (i55, an 1) → 0,40 % (a55, an 2) → 0,00 % (a17, an 4) | barème dégressif — ressemble à un paramètre de gabarit, c'est une **donnée** |
| **nom du signataire COO** | Benoit Van Lerberghe → Gaëlle Leclaire | §A.3 |
| **numéro de fax** | 26 43 12 74 → 42 88 84 (sauf page Loi Pacte) | section (f) |
| **tous montants, quantités, ISIN, cours, taux de change** | — | données |

### Stable entre réplicats

Les 16 ancres émetteur de la section (b) ; l'ordre des sections ; les en-têtes de colonnes de tous
les tableaux ; le code agence `LEU.326` (2 occurrences par document, sur les 7) ; `Client & Partner
Services` / `cps@wealins.com` ; la ville d'émission `Leudelange, le ` ; les intitulés
`Chief Operating Officer` / `Chief Executive Officer` ; l'artefact `<booklet>`.

Point notable : **`LEU.326` est stable sur les 7 documents et sur les deux contrats**. Le §B.6 le
signalait comme piège (« ne pas le prendre pour un n° de contrat ») — c'est juste, mais on peut
aller plus loin : sa stabilité inter-contrats et inter-gabarits en fait un **candidat d'ancre
émetteur/agence**, à condition de l'exclure de l'extraction des identifiants de contrat.

---

## (h) Pièges du §B.6 — confirmés, disparus, nouveaux

### Confirmés

| piège §B.6 | statut | preuve |
|---|---|---|
| Composite, paginations locales multiples, ne jamais segmenter par pagination globale | **confirmé et généralisé aux 7 documents** | section (d) |
| Le mot « Fonds » a 3 sens (FID / catégorie d'actif / titre de sous-tableau) | **confirmé** | `a55` p. 8 : `Fonds 506 844,78 49,03` comme catégorie ; p. 11 titre `Fonds` du tableau OPC ; `Fonds : K00149Q5 …` comme FID |
| Deux tableaux `Situation au` (N-1 / N) — capturer la date du titre | **confirmé** | `a55` p. 4 : `Situation au 31/12/2024` puis `Situation au 31/12/2025`, colonnes identiques |
| `Type d'Actifs` apparaît plusieurs fois avec contenus différents | **confirmé et aggravé** | 2 occurrences dans les documents 1 FID, **6** dans les documents 2 FID (`a17`, `q17`, `j17`) — la désambiguïsation doit être par (page, FID), pas par ordre d'apparition |
| Détail `Fonds` multi-pages sans sous-total intermédiaire | **confirmé** | `a55` p. 11 → 13, `Sous-total 506 844,78` seulement en p. 13 |
| 3 niveaux de totaux par FID | **confirmé** | `a55` p. 13/14/15 : sous-totaux `Fonds`, `Fonds alternatifs / non UCITS`, `Liquidités`, puis `Valeur totale du fonds au 31/12/2025 EUR 1 033 847,56` |
| Séparateur de milliers incohérent dans le même PDF | **confirmé** | corps `a55` p. 4 : `1.033.847,56 EUR` ; annexe p. 8 : `1 033 847,56` — même montant, deux écritures |
| Colonne `Année` ≠ somme des trimestres | **confirmé** | `a55` p. 9 : `-1,59 % / 1,81 % / 2,44 % / 0,83 %` → `Année 3,50 %` (somme arithmétique 3,49 %) |
| Loi Pacte : perf `non disponible` avec frais renseignés | **confirmé** | `i55` p. 6 et `a17` p. 9 : `non disponible` en perf brute/nette/finale, `0,1184 %` et `1,05 %` renseignés |
| `Open Cost Order` négatif dans Liquidités | **confirmé** | `a55` p. 15 : `Open Cost Order  - 2 720,99` ; `j55` : `- 2 721,73`, montant égal aux frais de gestion du trimestre |
| Nom du FID ≈ nom de la banque dépositaire | **confirmé** | `540709 Banque Thaler SA`, `1719249 CA Indosuez Switzerland S.A.` |
| Artefact `<booklet>` en texte brut | **confirmé sur les 7** | et **promu** : c'est le meilleur marqueur de début d'annexe |
| En-têtes empilés sur 2–3 lignes | **confirmé** | en-tête Loi Pacte étalé sur 4 lignes en `-layout` |
| `LEU.326` confondu avec un n° de contrat | **confirmé** | p. 1 et p. 2 de chaque document |
| Noms de fonds wrappés sur 2 lignes | **confirmé** | `a55` p. 11 : `HANETF SPROTT GL.URANIUM` / `MINING ETF` ; `VANECK ETF - MORNINGSTAR DM` / `DIVIDEND` |

### Disparus / à corriger

1. **« Footer fax différent sur la page Loi Pacte = marqueur de sous-template »** — invalidé
   comme marqueur structurel. Voir section (f) : le différentiel n'existait pas dans l'édition de
   janvier 2025, où toutes les pages portaient 26 43 12 74. C'est une mise à jour non propagée,
   pas une intention de gabarit.
2. **`Arbitrages et/ou changement de banque dépositaire` et `Aperçu des fonds` comme ancres de
   rang plein** — à rétrograder en ancres conditionnelles. Présentes respectivement dans 1/7 et
   3/7 documents. Voir section (b).
3. **« Le marqueur fort est structurel : DOUBLE pagination »** — imprécis. Il y a **trois ou
   quatre** blocs de pagination (`1/1`, `n/M` du corps, page sans compteur pour Loi Pacte,
   `Page n/M` de l'annexe), plus une page de garde sans footer. « Double » sous-estime la structure
   et, appliqué littéralement, ferait manquer la frontière corps/annexe.
4. **Ambiguïté date/pagination** — le §B.6 la signalait ; je ne l'ai pas rencontrée sous forme
   bloquante. Le préfixe littéral `Page ` de l'annexe et le suffixe `  FC0xxxxx` accolé au
   compteur du corps (`1/4      FC055211`) lèvent l'ambiguïté : un compteur de pagination WEALINS
   est **toujours** soit précédé de `Page `, soit suivi du numéro de contrat. Une date au format
   `JJ/MM/AAAA` n'a jamais cette forme. Le piège existe en théorie (`1/4` ressemble à un début de
   date) mais est **résolu par le contexte immédiat**. À reformuler en ce sens plutôt qu'à
   maintenir comme risque ouvert.

### Nouveaux

1. **Le mot « trimestre » est plus fréquent dans les documents annuels que dans les trimestriels**
   (10 vs 3, 5 vs 2). Piège majeur pour toute détection de périodicité par mot-clé insensible à la
   casse. Voir section (e).
2. **Le nom de fichier est faux 2 fois sur 4** chez cet émetteur : deux gabarits, quatre familles
   de noms. Ne jamais dériver la périodicité ni le gabarit du nom.
3. **Le courrier de G2 ne contient aucun mot de périodicité** — juste `Situation de contrat`. Un
   pipeline qui ne lirait que la page de courrier serait incapable de déterminer la fréquence de G2.
   Il faut lire l'annexe.
4. **`Frais prélevés au titre du 1 er trimestre 2026:`** — le nombre ordinal est **découpé par un
   espace** dans la couche texte (`1 er`, `2 ème`). Toute regex sur `1er trimestre` échouera ; il
   faut `1\s*er` / `2\s*ème`. Même phénomène sur les en-têtes de colonnes du tableau `Rendement` :
   `1 er` / `2e` / `3e` / `4e`.
5. **La version PDF diffère entre gabarits d'un même émetteur** (1.4 pour G1, 1.6 pour G2) à trois
   mois d'intervalle. Utile à savoir, dangereux à utiliser.
6. **Le FID (fonds dédié) change d'identifiant et de dépositaire à contrat constant** — FC051727
   passe de `540709 Banque Thaler SA` (31/12/2025) à `1719249 CA Indosuez Switzerland S.A.`
   (31/03/2026). Toute clé d'appariement de séries temporelles construite sur le nom ou le numéro de
   FID cassera. La clé stable est le **numéro de contrat** (`FC051727`), présent dans le footer de
   chaque page du courrier et du corps et dans l'en-tête de chaque page d'annexe.
7. **L'invariant de contrôle du §B.6 se vérifie** — sur `a55` : `506 844,78 + 502 631,58 +
   24 371,20 = 1 033 847,56` = `Valeur totale du fonds au 31/12/2025`, au centime. Sur `a17` :
   `545 975,50 + 468 670,81 = 1 014 646,31` = `Total` de l'`Aperçu des fonds`. Utilisable comme
   auto-validation d'extraction sur les deux gabarits.

---

## (i) Ce que je n'ai pas pu établir

1. **Le nombre réel de gabarits WEALINS.** Ce corpus couvre **un seul produit**
   (`Wealins Capi France`), **un seul distributeur** (agence `LEU.326`), **un seul souscripteur**
   (HANAMI INVESTISSEMENTS, personne morale) et **une seule langue**. Les variantes personne
   physique, les autres produits, les autres juridictions de commercialisation et une éventuelle
   périodicité mensuelle ou semestrielle sont hors champ. Le chiffre « 2 » est un minorant valable
   pour ce produit, pas une mesure du catalogue de l'émetteur. **La question posée par la mission —
   « combien de gabarits un même émetteur expose » — reçoit donc une réponse partielle : au moins 2
   pour un seul produit, ce qui rend l'ordre de grandeur « quelques dizaines » plausible sans le
   démontrer.**
2. **La nature de la suppression des blocs `Situation au [N-1]` et `Montant(s) … depuis la date
   d'effet` dans `i55`.** Conditionnelle (contrat souscrit en cours d'exercice N) ou dérive de
   gabarit ? Je penche fortement pour conditionnelle, l'ordre des sections étant par ailleurs
   strictement conservé, mais il faudrait une information annuelle 2024 d'un contrat antérieur à
   2024 pour trancher. **Incertitude assumée.**
3. **Si un sous-template peut circuler seul.** Réfuté sur ce corpus (7/7 composites), mais
   l'absence de contre-exemple n'est pas une preuve d'impossibilité. La page Loi Pacte est
   autoportante et pourrait techniquement être envoyée seule.
4. **La stabilité pluriannuelle de G2.** Je n'ai que deux trimestres consécutifs (Q1 et Q2 2026),
   édités à 3 mois d'écart. Aucune dérive observée entre eux — mais 3 mois ne testent rien. La
   dérive G1 mesurée à 12 mois (2 changements) laisse attendre un ordre de grandeur comparable
   pour G2.
5. **L'existence d'un identifiant de template natif.** Aucun, contrairement à Cardif
   (`<MODELE>…</MODELE>`). Les métadonnées se réduisent à `/Author` et `/CreationDate`, pas de XMP.
   L'artefact `<booklet>` est la seule balise de template visible et elle ne nomme que le
   sous-template d'annexe, sans version ni identifiant.
6. **Le sens du différentiel de version PDF (1.4 / 1.6).** Corrélé aux deux gabarits sur ce corpus,
   mais je n'ai pas de troisième famille pour savoir si la corrélation est causale (deux chaînes
   d'assemblage distinctes) ou fortuite.
