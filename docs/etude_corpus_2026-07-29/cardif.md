# Cardif — dérive de gabarit dans le temps (originaux 2024 vs 2025)

> **2026-07-29.** Série Cardif Elite Capitalisation Personnes Morales, contrat n° 92700569
> (souscripteur HANAMI INVESTISSEMENTS, CGP EMERAUDE GESTION PRIVEE).
> Prolonge le §B.7 de `etude_signature_gabarits_2026-07-27.md`.
> Méthode : `pdfinfo`, `pdffonts`, `pdftotext -layout`, `pdftotext -raw`, `pypdf`.
> Nombre de pages traité **hors matching** (cf. A.3).

---

## (a) Inventaire

| Fichier | Nature | CreationDate | Creator / Producer | Pages | Taille | Arrêté (`DATE_EFFET`) |
|---|---|---|---|---|---|---|
| `2024.12 relevé Cardif Elite Capi HANAMI.pdf` | **ORIGINAL** | 28/01/2025 12:29 CET | BdocPDF V7.0 / Apache FOP `SVN tags/fop-2_2/fop-core` | **2** | 13 167 o | 31/12/2024 |
| `2025.12 Relevé Cardif Elite Capi HANAMI.pdf` | **ORIGINAL** | 23/01/2026 10:02 CET | idem | **3** | 26 851 o | 31/12/2025 |
| `2026.03 Relevé Cardif Elite Capi HANAMI.pdf` | réédition | 24/07/2026 15:46 CEST | idem | 3 | 26 978 o | **30/03/2026** |
| `2026.06 Relevé Cardif Elite Capi HANAMI.pdf` | réédition | 24/07/2026 15:43 CEST | idem | 3 | 26 680 o | 30/06/2026 |

Communs aux quatre : A4 portrait 595,275 × 841,889 pts, PDF 1.7, non taggé, non chiffré,
non optimisé, `Metadata Stream: yes`, `Custom Metadata: no`, texte natif (zéro OCR).

La distinction original / réédition est reprise telle quelle de la vérification `pdfinfo` amont
et n'est pas rediscutée. Conséquence assumée ici : **seuls 2024.12 et 2025.12 servent au jugement
de dérive** ; 2026.03 et 2026.06 ne servent qu'à deux choses — confirmer que le gabarit courant est
bien celui de 2025.12, et tester le token de périodicité sur des dates d'arrêté non annuelles.

Note d'arrêté : `DATE_EFFET = 30/03/2026`, et non 31/03. Une date de fin de trimestre fausse d'un
jour, dans un modèle nommé « front-office », oriente vers une **génération à la demande** avec
date choisie par le demandeur plutôt que vers une campagne trimestrielle.

---

## (b) Comparaison des trois couches — original 2024 vs original 2025

### Couche 1 — metadata et moteur

| Élément | 2024.12 | 2025.12 | Verdict |
|---|---|---|---|
| Creator | `BdocPDF V7.0` | `BdocPDF V7.0` | identique |
| Producer | `Apache FOP … fop-2_2` | `Apache FOP … fop-2_2` | identique |
| Polices (`pdffonts`) | **Times-Roman / Times-Bold / Times-Italic / Times-BoldItalic** + Helvetica | **Helvetica / -Bold / -Oblique / -BoldOblique** + `EAAAAA+Wingdings-Regular` (CID TrueType, embarquée) | **divergent** |

Le couple Creator/Producer ne bouge pas d'un pouce alors que le document est entièrement
recomposé. C'est la démonstration la plus nette, dans ce corpus, du point A.2 « la couche 1
sous-discrimine et n'est jamais suffisante seule » : ici elle ne discrimine **rien du tout**.

En revanche la **liste des polices** discrimine parfaitement : bascule d'une base sérif Times vers
une base sans-sérif Helvetica, plus une police Wingdings embarquée apparue en 2025 (elle porte la
puce décorative devant « Cumul des opérations pour l'année », p.1). Aucune police n'est embarquée
en 2024 ; une seule l'est en 2025. Proposition : ajouter `polices[]` + `polices_embarquees` comme
**couche 1bis** — coût quasi nul, pouvoir discriminant réel là où Creator/Producer est muet.

### Couche 2 — ancres boilerplate

| Ancre du §B.7 | 2024.12 | 2025.12 |
|---|---|---|
| `Cardif Elite Capitalisation Personnes Morales` | **en capitales** : `CARDIF ELITE CAPITALISATION PERSONNES MORALES` (p.1) | casse mixte, telle quelle (p.1) |
| `Contrat de capitalisation` (bandeau) | **absent** | présent (p.1, à droite du titre) |
| `Cumul des opérations pour l'année` | **absent** → `SYNTHÈSE DES OPÉRATIONS DE L'ANNÉE 2024` (p.1) | présent (p.1) |
| `Situation du contrat au` | `SITUATION DU CONTRAT AU 31/12/2024` (p.1) | `Situation du contrat au 31 décembre 2025` (p.2) |
| `Garanties au terme du contrat` | **absent** | présent (p.3) |
| `Valeur du contrat au` | **absent** → `Valeur de rachat en euros au 31/12/2024` (p.1) | `Valeur du contrat au 31/12/2025` (p.2) |
| `(1) Net de frais de gestion.` | **absent** (aucune footnote) | présent (p.2) |
| `Cardif Assurance Vie` (nom de l'assureur en texte) | **absent** | présent (p.2, clause UC) |
| `Votre Conseil en Gestion de Patrimoine` | **absent** → `VOTRE CORRESPONDANT` (p.1) | présent (p.1) |
| `Souscripteur` | `SOUSCRIPTEUR` (p.1) | `Souscripteur` (p.1) |
| `Informations relatives au contrat` | **absent** | présent (p.1) |

Sur les onze ancres du profil B.7, **une seule survit à l'identique** dans l'original 2024
(`Situation du contrat au`, et seulement si l'on tolère la casse), et **aucune** en respectant la
casse. Le profil B.7 tel qu'il est écrit **ne matcherait pas** l'original 2024.

Boilerplate légal — la divergence n'est pas qu'une affaire de casse, du texte est **retiré** :

- Commun aux deux : `Nous vous communiquons la valorisation provisoire de votre contrat selon les
  informations en notre possession…` (2024 p.2, 2025 p.3). C'est **la seule ancre de boilerplate
  véritablement partagée** par les deux originaux.
- 2024 seulement (p.2) : `En aucun cas, cette valorisation provisoire … ne saurait donc se
  substituer aux relevés de situation établis par la société d'assurance QUI SEULS FONT FOI`,
  puis `les instruments financiers … demeurent la propriété de la société d'assurance`,
  puis la formule de clôture `Fait à Paris, le 28 janvier 2025` / `Direction des Opérations`.
- 2025 seulement : clause de rémunération du Fonds Général sur 12 mois avec pénalité de rachat
  avant la 4e année (p.2), clause valeurs estimatives / actifs non cotés / PEA PME-ETI avec l'URL
  `https://document-information-cle.cardif.fr/cgpi` (p.2), clause
  `Cardif Assurance Vie ne s'engage que sur le nombre d'unités de compte, mais pas sur leur valeur`
  (p.2), et `Ces valeurs ne prennent pas en compte l'affectation des revenus financiers…` (p.3).

Le bloc de clôture épistolaire (« Fait à Paris, le … », « Direction des Opérations ») **disparaît**
en 2025 : le document passe d'une forme de courrier signé à une forme de relevé structuré.

### Couche 3 — structure

Ordre des blocs :

| | 2024.12 (2 p.) | 2025.12 (3 p.) |
|---|---|---|
| p.1 | Titre capitales · `VOTRE CORRESPONDANT` \| `SOUSCRIPTEUR` en deux colonnes · `DATE D'EFFET DU CONTRAT` (phrase libre : « Le contrat a pris effet le 23 octobre 2024 ») · `SYNTHÈSE DES OPÉRATIONS DE L'ANNÉE 2024` · `SITUATION DU CONTRAT AU 31/12/2024` (tableau supports) · ligne total | Titre + bandeau · `Informations relatives au contrat` (`Références` \| `Votre Conseil en Gestion de Patrimoine`) · `Souscripteur` · `Cumul des opérations` |
| p.2 | boilerplate légal + clôture signée | `Situation du contrat au 31 décembre 2025` (tableau supports) · total · footnote · 4 blocs légaux |
| p.3 | — | `Garanties au terme du contrat` (tableau à colonnes réduites) · clause · rappel valorisation provisoire |

Le tableau des supports change de **page** (p.1 → p.2), de **jeu de colonnes** et de **tri** :

- 2024, en-têtes empilés : `Support` | `Code Isin` | `Nombre d'unités de compte au 31/12/2024` |
  `Valeur de l'unité de compte au dernier cours connu` | `Valorisation en euros` — **5 colonnes**,
  intitulés **portant la date d'arrêté** (cas A.3 : matcher par pattern tolérant, jamais verbatim).
- 2025 : `Support` | `Code ISIN` | `Répartition` | `Nombre d'unités de compte` |
  `Valeur de l'unité de compte` | `Valorisation` — **6 colonnes**, colonne `Répartition` (%)
  **créée**, dates retirées des intitulés, `Isin` → `ISIN`.
- Tri des lignes : 2024 **non trié** (ABERDEEN, IVO, LYXOR, CARMIGNAC, ISHARES, AMUNDI, AXA,
  EUROPE, AXIOM, ISHARES), avec `FONDS GENERAL` **en première ligne** ; 2025 **trié
  alphabétiquement**, `FONDS GENERAL (1)` inséré à sa place alphabétique (entre `EUROPE A CAP` et
  `ISHARES …`). Le fonds euro n'est donc plus repérable par sa position.

Bloc technique XML : présent et **répété identique en bas de chaque page** dans les deux originaux
(2 occurrences en 2024, 3 en 2025) — marqueur de structure confirmé, cf. (c).

Pagination : `1/2`, `2/2` **absents** en 2024 (aucune pagination imprimée) ; `1/3` `2/3` `3/3`
présents en 2025. La pagination imprimée est donc elle-même un marqueur de version, pas une
constante Cardif.

Conventions numériques :

| | 2024.12 | 2025.12 |
|---|---|---|
| Symbole monétaire | **`euros` en mot**, 0 occurrence de `€` | **`€`**, 33 occurrences, 0 de `euros` |
| Montants | `500 000,00 euros`, `502 246,58` (colonne « en euros », sans unité) | `0 €`, `200 633,23 €`, `328 263,19 €` |
| Cours UC | `56,40` (nu) | `79,93 €` |
| Pourcentages | aucun | `2,24%`, `24,24%` (sans espace avant `%`) |
| Nb d'UC | `360,786790` (6 déc.) | `92,189195` (6 déc.) — inchangé |
| Séparateurs | espace milliers, virgule décimale | idem |

Séparateurs et nombre de décimales sont stables ; l'unité monétaire bascule complètement.

---

## (c) Verdict `TYPE_MODELE`

**`TYPE_MODELE = 66` sur les quatre documents, sans exception.** Relevé par `pypdf` (voir (g) pour
la raison de ne pas se fier ici à `pdftotext`), sur chaque page de chaque fichier :

| Fichier | Occurrences `<TYPE_MODELE>` | Valeur | `<MODELE>` |
|---|---|---|---|
| 2024.12 (original) | 2 (1/page) | `66` | `Relevé situation front-office` |
| 2025.12 (original) | 3 (1/page) | `66` | `Relevé situation front-office` |
| 2026.03 (réédition) | 3 | `66` | `Relevé situation front-office` |
| 2026.06 (réédition) | 3 | `66` | `Relevé situation front-office` |

Le couple `<MODELE>Relevé situation front-office</MODELE>` + `<TYPE_MODELE>66</TYPE_MODELE>` est
donc **strictement invariant à travers une refonte complète de la mise en page**.

**Conséquence, et c'est un retournement du point A.4-1 :** `TYPE_MODELE` n'est **pas** un
identifiant de gabarit au sens du store. C'est un identifiant de **famille de document** (« quel
type de courrier Cardif produit-on »), stable au fil des versions de la composition. Le §A.4
qualifiait ce champ de « signature parfaite quand elle existe » : sur ce corpus, cette qualification
est **fausse**. Un ID natif qui ne change pas quand le gabarit change ne peut pas court-circuiter le
matching — il ne peut que le **cadrer**.

Statut à retenir pour le schéma de profil :

- `template_id_natif` reste utile comme **pré-filtre très bon marché et très sélectif**
  (il identifie l'émetteur, le produit et la famille de document en un seul token), mais il
  **n'autorise pas** à sauter les couches 2 et 3.
- Il faut renommer le champ pour ne pas rejouer l'erreur : `famille_document_native` ou
  `template_id_natif` **avec un drapeau explicite `versionnant: false`**.
- Le seul champ du bloc XML qui bouge entre 2024 et 2025 est l'apparition de `<RECOMMANDE>`
  (39 balises distinctes en 2024, 40 en 2025, aucune balise perdue). C'est un signal de version
  très faible — un champ d'affranchissement, pas un numéro de gabarit — mais c'est **le seul
  indice de version présent dans le bloc technique**, et il devrait donc être surveillé.

Aucun champ du bloc XML ne porte de numéro de version de composition. **Cardif versionne son
gabarit sans le dire.**

---

## (d) Verdict dérive

**Deux gabarits distincts pour un même `TYPE_MODELE`, à un an d'écart.**

- **Gabarit Cardif-v1** — original 2024.12, généré le 28/01/2025.
- **Gabarit Cardif-v2** — original 2025.12, généré le 23/01/2026 ; c'est celui du §B.7 actuel,
  et c'est celui que les rééditions 2026 reproduisent à l'identique (mêmes ancres, mêmes 6 colonnes,
  même ordre de blocs, `Code ISIN`, `€`, `(1) Net de frais de gestion.`, `Garanties au terme`).

Ce qui les sépare, par ordre de force discriminante :

1. **Le jeu d'ancres est presque entièrement remplacé** (11 ancres du profil, 1 survivante en
   tolérant la casse, 0 en casse exacte). Ce n'est pas un habillage, c'est une réécriture des
   libellés : `VOTRE CORRESPONDANT` → `Votre Conseil en Gestion de Patrimoine`,
   `SYNTHÈSE DES OPÉRATIONS DE L'ANNÉE 2024` → `Cumul des opérations pour l'année`,
   `Valeur de rachat en euros au` → `Valeur du contrat au`.
2. **Un tableau change de jeu de colonnes** (5 → 6, `Répartition` créée) et de tri
   (non trié → alphabétique).
3. **Deux sections apparaissent** : `Informations relatives au contrat` / `Références` (durée,
   date de terme) et `Garanties au terme du contrat`.
4. **Le registre du document change** : courrier signé (« Fait à Paris, le … »,
   « Direction des Opérations ») → relevé paginé sans signature.
5. **Base typographique** Times → Helvetica, avec Wingdings embarquée.
6. **Convention monétaire** `euros` → `€`.
7. Casse des titres : capitales → casse mixte, de façon systématique.

Une dérive de cette ampleur doit produire un **nouveau gabarit** dans le store, pas un simple
avertissement de drift. La date de bascule est encadrée mais pas datée : elle tombe **entre le
28/01/2025 et le 23/01/2026**, et le corpus ne contient aucun original intermédiaire pour la
resserrer.

Ce que la dérive **ne** touche pas : l'émetteur, le produit, la famille de document
(`TYPE_MODELE=66`), le moteur (BdocPDF/FOP 2.2), le principe du bloc technique XML en pied de
page, le format A4, le nombre de décimales des UC, la présence du groupe `Gestion libre` portant
son total sur sa propre ligne, la présence d'une ligne `FONDS GENERAL` à `--`, et l'invariant
comptable Σ = total. Ce noyau-là est le vrai squelette de la série.

---

## (e) Sections requises vs optionnelles

L'enseignement Spirica (trois gabarits apparents = un gabarit à blocs conditionnels pilotés par la
donnée) **se vérifie chez Cardif, et Cardif fournit en plus la liste de ses propres interrupteurs.**

Le bloc XML de pied de page contient une série de champs **vides ou à `NON`** qui n'ont de sens que
comme conditions d'affichage. Valeurs relevées, identiques sur les quatre documents :

```
<MANDAT>NON</MANDAT>          <OPE_MANDAT></OPE_MANDAT>
<PROFILE_TYPE_NAME></PROFILE_TYPE_NAME>   <ALLOCATION_TYPE_NAME></ALLOCATION_TYPE_NAME>
<LISTE_ISIN></LISTE_ISIN>     <LISTE_IMMO_ISIN></LISTE_IMMO_ISIN>
<REVENU_OST></REVENU_OST>     <OPE_MT></OPE_MT>          <ANNEXE></ANNEXE>
```

Lecture : `MANDAT=NON` explique que le tableau des supports ne comporte qu'**un seul** groupe,
`Gestion libre`. Le gabarit prévoit donc au moins un second groupe (gestion sous mandat /
gestion pilotée), avec son propre sous-total, qui apparaîtrait si `MANDAT=OUI` — exactement la
mécanique Spirica. De même `LISTE_IMMO_ISIN` vide et `ANNEXE` vide pointent vers un bloc
immobilier et une annexe conditionnels, `PROFILE_TYPE_NAME` / `ALLOCATION_TYPE_NAME` vides vers un
encart de profil de gestion non affiché faute de mandat.

Sur la ligne `FONDS GENERAL` — l'indice était bon, mais il ne désigne pas une section optionnelle :

```
2024 p.1  FONDS GENERAL           --      --       --      301 595,48
2025 p.2  FONDS GENERAL (1)   --  24,24%   --      --       79 558,17 €
```

C'est une **ligne à cardinalité de colonnes variable** dans un tableau par ailleurs homogène : le
fonds euro n'a ni ISIN, ni nombre d'UC, ni valeur d'UC, mais il a une valorisation (et, en v2, une
répartition). Les `--` sont des marqueurs de non-applicabilité, pas des valeurs manquantes. Le
phénomène est donc réel mais d'un cran plus fin que chez Spirica : **bloc conditionnel** chez
Spirica, **type de ligne conditionnel** ici. Le profil doit distinguer les deux niveaux.

Découpage proposé pour le profil Cardif-v2 :

**`sections_requises`**
- En-tête `Cardif Elite Capitalisation Personnes Morales` + `Situation du contrat N° … au …`
  + bandeau `Contrat de capitalisation`
- `Informations relatives au contrat` > `Références`
- `Souscripteur`
- `Cumul des opérations` > `Cumul des opérations pour l'année`
- `Situation du contrat au [date en lettres]` — tableau supports + total `Valeur du contrat au`
- Bloc technique XML en pied de chaque page

**`sections_optionnelles`** (avec leur condition, quand elle est lisible)
- `Votre Conseil en Gestion de Patrimoine` — conditionné au réseau intermédié
  (`<RESEAU>DIRECT-CGPI</RESEAU>`, `<MODE_GENERATION>Apporteur CGPI</MODE_GENERATION>`) ;
  attendu absent en distribution directe. **Non vérifié** : pas de document hors CGPI au corpus.
- Groupe `Gestion libre` — présent ici ; un groupe mandat est attendu si `MANDAT=OUI`.
  **Non vérifié**, aucun document `MANDAT=OUI` au corpus.
- Ligne `FONDS GENERAL (1)` + footnote `(1) Net de frais de gestion.` — conditionnée à la
  présence d'une poche fonds euro. Corrélation stricte observée v2 : `(1)` sur la ligne **et**
  footnote **et** clause de rémunération du Fonds Général, les trois ensemble ou aucune.
- `Garanties au terme du contrat` (p.3) — présente sur les trois documents v2, absente du v1.
  **Ambigu** : effet de version ou bloc conditionnel ? Cf. (h).
- Blocs immobilier / annexe / revenus OST — inférés des balises vides, **jamais observés**.

---

## (f) Périodicité et son token

**Le token `pour l'année` ne discrimine pas la périodicité. Le §A.4-2 est démenti par le corpus.**

Test direct :

| Fichier | `DATE_EFFET` | Libellé du bloc cumul |
|---|---|---|
| 2025.12 (original) | 31/12/2025 | `Cumul des opérations pour l'année` |
| 2026.03 (réédition) | **30/03/2026** | `Cumul des opérations pour l'année` |
| 2026.06 (réédition) | **30/06/2026** | `Cumul des opérations pour l'année` |

Aucune occurrence de `pour le mois` ni de `pour le trimestre` nulle part dans le corpus Cardif.
Le libellé reste `pour l'année` sur un arrêté au 30 mars comme au 30 juin : il ne décrit pas la
fréquence d'émission du document, il décrit la **fenêtre d'agrégation du cumul**, qui est l'année
civile en cours (cumul depuis le 1er janvier). C'est un token de **périmètre de cumul**, pas de
périodicité. Le distinguer explicitement dans le schéma : `fenetre_cumul` ≠ `periodicite`.

Nuance de méthode, à ne pas escamoter : les deux documents à arrêté non annuel sont des
**rééditions**. Le test reste valide pour ce qu'il prouve — le système Cardif actuel écrit
`pour l'année` sur un arrêté au 30/03 — mais il ne prouve pas qu'un vrai relevé trimestriel de
campagne écrirait la même chose. La réfutation du token comme discriminant est solide ; la nature
réelle de la périodicité de la série ne l'est pas.

Le v1 était sur ce point **plus** informatif que le v2 : `SYNTHÈSE DES OPÉRATIONS DE L'ANNÉE 2024`
nommait l'année. La refonte a **retiré** l'année du libellé. Bénéfice pour le matching (libellé sans
date embarquée, cf. A.3), perte pour l'extraction (la fenêtre de cumul n'est plus explicite dans le
libellé ; il faut la déduire de `DATE_EFFET`).

Ce qui reste effectivement lisible dans le document :

- **Date d'arrêté** : `DATE_EFFET` dans le bloc XML (machine, non ambigu), reprise en clair
  p.1 (`au 31/12/2025`) et p.2 en toutes lettres (`au 31 décembre 2025`) en v2. En v1, numérique
  seulement — le doublement numérique/lettres est une **acquisition du v2**.
- **Nature du document** : `<MODELE>Relevé situation front-office</MODELE>`. « front-office »
  suggère une édition à la demande par le distributeur, ce que corrobore l'arrêté au 30/03.
- Ce que le document **ne** dit **pas** : sa propre fréquence d'émission. Aucun token ne l'énonce.

Recommandation : pour Cardif, `periodicite` = `"à la demande"` avec
`token_discriminant: null` et une note explicite. Ne pas inférer « annuel » de l'arrêté au 31/12
(piège A.3 dans sa forme la plus directe).

---

## (g) Pièges de parsing — confirmés / disparus / nouveaux

### Confirmés sur le v2 (et sur le v1 sauf mention)

1. **Positionnement absolu FOP → espacements extrêmes en `-layout`.** Confirmé, et **bien pire en
   v1** : le titre de p.1 sort avec ~180 espaces de tête, la ligne `Valeur de rachat` avec des
   blocs de plus de 300 espaces. Le découpage par largeur de colonne est inutilisable.
   Extraction par positions (bbox) requise.
2. **`FONDS GENERAL` à `--`.** Confirmé v1 et v2. Cf. (e).
3. **Noms de supports wrappés sur 2 lignes, ISIN et chiffres sur la 1re.** Confirmé v2
   (`AMUNDI MSCI AC ASIA PACIFIC EX JAPAN UCITS` / `ETF ACC`). Confirmé v1, **en pire** : le nom
   est wrappé et l'ISIN + les chiffres tombent sur la **2e** ligne, pas la 1re
   (`ABERDEEN STANDARD SICAV I ASIAN` puis `LU0231459107 360,786790 56,40 20 348,37` puis
   `SMALLER COMPANIES FUND A Acc USD`). Le nom est donc **coupé en deux par la ligne de données**.
   Un recollage qui suppose « données sur la première ligne » casse sur le v1.
4. **`Gestion libre` porte le total du groupe sur la ligne du libellé.** Confirmé v1 et v2.
5. **En-têtes empilés sur plusieurs lignes.** Confirmé et **aggravé** : le bloc cumul v2 s'étale
   sur 2 lignes (`Montant brut` / `des versements`), l'en-tête du tableau supports v1 sur **5**
   lignes entrelacées (`Valeur de l'unité` / `Nombre d'unités` / `de compte Valorisation` /
   `Support Code Isin de compte au` / `au dernier en euros` / `31/12/2024` / `cours connu`) —
   l'ordre de sortie ne suit ni les colonnes ni les lignes. Reconstruction par bbox obligatoire.
6. **Ligne total sans séparateur net.** Confirmé : `Valeur du contrat au 31/12/2025 328 263,19 €`
   (v2), `Valeur de rachat en euros au 31/12/2024 502 246,58` (v1).
7. **Balise XML coupée en fin de ligne physique.** Confirmé, et **plus grave que décrit** : cf.
   nouveau piège n°14.
8. **Tableau `Garanties` (p.3) = mêmes supports, colonnes réduites.** Confirmé v2
   (`Support` | `Nombre d'unités de compte`, mêmes 13 libellés triés, sans ISIN ni valorisation,
   `FONDS GENERAL` **absent** de ce tableau — traité à part par la phrase
   `la valeur de rachat minimale sur le Fonds Général … sera de 72 199,51 €`). Risque de confusion
   réel : les libellés sont identiques à ceux du tableau de la p.2.
9. **Variante Personnes Physiques non présumable.** Toujours valide, toujours non testable :
   aucun document PP au corpus.

### Disparus / non reproduits

10. **Artefact d'encodage `sociét?`** — **non reproduit**. `société` sort proprement en UTF-8 sur
    les deux originaux, en `-layout`, en `-raw` et via `pypdf`. Le mot lui-même n'apparaît plus
    qu'en v1 (clause `propriété de la société d'assurance`, retirée en v2). Piège probablement lié
    à l'environnement d'extraction de l'étude initiale, non au document. À retirer du profil, mais
    conserver l'hygiène UTF-8 générale.
11. **`(1)` sur la ligne `FONDS GENERAL` + footnote** — **absent du v1** : la ligne s'écrit
    `FONDS GENERAL` sans appel de note et il n'y a aucune footnote. Un parseur v2 qui exige `(1)`
    pour reconnaître le fonds euro rate le v1. À traiter comme optionnel (cf. (e)).
12. **Date d'arrêté doublée numérique + lettres** — marqueur **absent du v1** (numérique
    seulement). L'invariant de contrôle croisé date-numérique / date-en-lettres du §B.7 n'existe
    donc que sur le v2.
13. **Pagination `n/3`** — **absente du v1** (aucune pagination imprimée). À ne pas utiliser comme
    ancre de série.

### Nouveaux

14. **`pdftotext` perd des caractères dans le bloc technique XML.** Le plus sérieux de la liste.
    Sur 2025.12 p.1, `pdftotext` (`-layout` **et** `-raw`) rend
    `…<RECEIVER_EMAIL></RECEIVERRECEIVER_DO_NO_DISTURB><PROFILE_TYPE_NAME>…` :
    la sous-chaîne `_EMAIL><RECEIVER_DO_NO_DISTURB>0</` est **perdue**. `pypdf` sur la même page
    rend correctement `…<RECEIVER_EMAIL></RECEIVER_EMAIL><RECEIVER_DO_NO_DISTURB>0</\nRECEIVER_DO_NO_DISTURB>…`.
    Effet mesuré : un diff naïf des ensembles de balises entre 2024 et 2025 fait faussement
    apparaître `<RECEIVER_DO_NO_DISTURB>` comme « présent en 2024, absent en 2025 ».
    **Conséquence opérationnelle : lire le bloc technique — donc `TYPE_MODELE` — avec `pypdf`,
    jamais avec `pdftotext`.** La perte n'a pas frappé `TYPE_MODELE` sur ces quatre fichiers, mais
    rien ne garantit qu'elle l'épargnera ailleurs. La règle de lecture doit être robuste par
    construction.
15. **L'`ID_COURRIER` est imprimé en marge et atterrit au milieu du tableau.** Le jeton
    `I13640829` (v1) / `I14746359` (v2) — valeur de `<APP_CODE>` et `<ID_COURRIER>` — est estampé
    verticalement dans la marge et ressort comme **une ligne isolée à l'intérieur du tableau des
    supports** (v1 p.1 : entre la ligne `AXIOM OBLIGATAIRE` et la ligne
    `ISHARES MSCI USA SMALL CAP`). Un parseur ligne-à-ligne le prend pour un support. Le filtrer
    par pattern `^I\d{8}$`, et le **conserver** : c'est un identifiant d'édition unique.
16. **Le tri des lignes de support n'est pas stable entre versions** (non trié en v1, alphabétique
    en v2). Ne jamais s'appuyer sur la position d'une ligne, en particulier celle du
    `FONDS GENERAL` (1re ligne en v1, position alphabétique en v2).
17. **Tolérance d'arrondi sur l'invariant de contrôle.** Vérifié :
    v1 Σ des 11 lignes = `502 246,58` = `Valeur de rachat` — **exact au centime** ;
    v2 Σ des 14 lignes = `328 263,20` contre `328 263,19` affiché — **écart de 1 centime**.
    L'invariant tient, mais avec une tolérance non nulle. Le §A.4-3 (« au centime ») est trop
    strict pour le v2 : prévoir `±0,01 × nb_lignes` ou `±0,05` en absolu.
18. **Le sous-total `Gestion libre` égale le total du contrat** quand c'est le seul groupe (v1 et
    v2 : `502 246,58` et `328 263,19` des deux côtés). Le doublon est structurel et n'indique pas
    une erreur — mais il tombera si un groupe mandat apparaît (cf. (e)).
19. **Casse des libellés non fiable entre versions.** Tout le v1 est en capitales, tout le v2 en
    casse mixte. Le matching d'ancres doit être **insensible à la casse**, et l'insensibilité
    doit être une propriété du moteur, pas une variante stockée dans chaque ancre.

---

## (h) Ce que je n'ai pas pu établir

1. **La date de bascule v1 → v2**, au-delà de la fenêtre 28/01/2025 – 23/01/2026. Il n'existe pas
   d'original intermédiaire au corpus.
2. **Si `Garanties au terme du contrat` est une section de v2 ou un bloc conditionnel.** Deux
   lectures tiennent : (i) section créée par la refonte ; (ii) bloc conditionnel à la garantie
   plancher, absent en 2024 parce que le contrat n'avait que deux mois (effet le 23/10/2024,
   arrêté le 31/12/2024). L'hypothèse (i) est la plus économique — le v1 n'a pas non plus le bloc
   `Références` d'où sortent la durée et la date de terme, sans lesquelles la notion de « terme »
   n'est pas posée — mais je n'ai aucun original v1 sur un contrat mûr pour trancher. **Traitée
   comme optionnelle par prudence.**
3. **Si `Informations relatives au contrat` / `Références` est requis en v2.** Présent sur les
   trois documents v2, mais tous portent le même contrat : aucune variance testée.
4. **Toutes les sections conditionnelles inférées des balises vides** (`MANDAT=OUI`,
   `LISTE_IMMO_ISIN`, `ANNEXE`, `REVENU_OST`, `PROFILE_TYPE_NAME`) sont des **hypothèses de
   lecture des balises**, jamais des observations. Les libellés réels des blocs correspondants
   sont inconnus.
5. **Le comportement du token de cumul sur un original non annuel.** Établi sur rééditions
   seulement. Un vrai relevé de campagne mensuelle ou trimestrielle pourrait écrire autre chose ;
   je n'ai pas le document qui le dirait.
6. **La variante Personnes Physiques**, et plus généralement le comportement hors
   `RESEAU=DIRECT-CGPI` : aucun échantillon.
7. **Si le v1 est lui-même le premier gabarit de la série** : le contrat a pris effet le
   23/10/2024, le relevé 2024.12 est donc probablement le premier émis. Aucune antériorité
   consultable, donc aucune information sur les gabarits antérieurs à 2024.
8. **Ce que couvre `TYPE_MODELE` en dehors de 66.** Le champ est une valeur dans une nomenclature
   Cardif dont je ne vois qu'un point. Rien ne dit ici si un autre produit Cardif, ou un autre
   type de courrier, porterait une autre valeur — donc rien ne dit si `66` est sélectif au sens
   du store. Ce point est probablement le plus utile à vérifier au prochain document Cardif.
