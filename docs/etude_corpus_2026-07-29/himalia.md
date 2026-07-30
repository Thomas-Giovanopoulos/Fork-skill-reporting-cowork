# Himalia — dérive de gabarit sur originaux (2024 vs 2025)

> **2026-07-29.** Mission : confirmer ou infirmer une dérive de gabarit dans le temps chez
> l'émetteur du produit « HIMALIA CAPITALISATION » (émetteur non nommé en texte, cas connu
> du corpus — non recherché ici).
> Référence de départ : `docs/etude_signature_gabarits_2026-07-27.md`, partie A et profil **B.5**.
> Corpus : `/sessions/epic-happy-ritchie/mnt/Données assureur/`.
> Outils : `pdfinfo`, `pdffonts`, `pdftotext -layout` / `-bbox`, `pdfimages -list`, `pypdf`.
> Lecture seule sur le corpus. Aucun autre fichier écrit.

---

## (a) Inventaire — pages, métadonnées, polices

Distinction ORIGINAL / RÉÉDITION reprise telle quelle de la vérification `pdfinfo` antérieure
(non remise en cause ici, et confirmée par les `CreationDate` ci-dessous).

| Fichier | Statut | Arrêté | CreationDate | Pages | Supports | Épargne atteinte |
|---|---|---|---|---|---|---|
| `2023.12 Relevé Himalia Capi HANAMI.pdf` | réédition | 31/12/2023 | 24/07/2026 13:50 | 3 | 9 | 212 336,12 € |
| `2024.12 Relevé Himalia Capi HANAMI.pdf` | **ORIGINAL** | 31/12/2024 | **28/01/2025 11:23** | 4 | 16 | 220 545,63 € |
| `2025.12.31 Relevé Himalia Cpai HANAMI.pdf` | **ORIGINAL** | 31/12/2025 | **05/03/2026 10:18** | 4 | 21 | 242 144,68 € |
| `2026.03 Relevé Himalia Capi HANAMI.pdf` | réédition | 31/03/2026 | 24/07/2026 13:49 | 4 | 17 | 252 812,12 € |
| `2026.06 Relevé Himalia Capi HANAMI.pdf` | réédition | 30/06/2026 | 24/07/2026 13:48 | 4 | 16 | 257 526,82 € |

*(« Cpai » dans le nom du fichier 2025 est une coquille du nom de fichier ; le contenu est bien le
relevé Himalia au 31/12/2025. Rappel A.1 : le nom de fichier n'est jamais un critère.)*

### Métadonnées PDF (couche 1)

Identiques sur **les 5 documents**, originaux et rééditions confondus :

```
Creator     : JasperReports (report name)
Producer    : iText 2.1.7 by 1T3XT
PDF version : 1.4
Page size   : 595 x 842 pts (A4)
Tagged      : no    Encrypted : no    Form : none    JavaScript : no
Metadata Stream : no    Custom Metadata : no
```

Seuls `CreationDate` / `ModDate` (toujours égaux entre eux) et la taille de fichier varient.
`/Root` ne contient que `/Names /Type /Pages /ViewerPreferences` — **aucun identifiant de
template natif** (pas d'équivalent du `<MODELE>` Cardif, cf. A.4 point 1). La chaîne Creator
est littéralement `JasperReports (report name)` : le placeholder n'a jamais été renseigné, donc
pas de nom de rapport exploitable.

### Polices

Identiques sur **les 5 documents**, y compris les deux originaux :

| Nom | Type | Encodage | Embarquée | Sous-ensemble | Unicode |
|---|---|---|---|---|---|
| Helvetica | Type 1 | WinAnsi | non | non | non |
| Helvetica-Bold | Type 1 | WinAnsi | non | non | non |

Deux polices, aucune embarquée, objets 2 0 et 3 0 dans les deux originaux.

### Objets graphiques

`pdfimages -list` : **aucune image de contenu**. Les seules images sont deux bitmaps 1×1 px
indexés (objet 12) sur la page 2, étirés — des aplats de couleur, pas un logo.
La page 2 porte en revanche **deux Form XObjects** identiques dans les deux originaux :

```
/Xf1  /Form  BBox [0, 0, 520, 373]
/Xf2  /Form  BBox [0, 0, 500, 290]
```

Ce sont des graphiques vectoriels (blocs de type diagramme, sans texte extractible) placés sous
le titre « Répartition ». **Incertitude signalée** : je n'ai pas ouvert le contenu de ces Forms
pour établir leur nature exacte (camembert, barres…) ; ce qui est établi c'est qu'ils sont
présents, aux mêmes BBox, sur la page 2 des cinq documents, et qu'ils ne portent aucun texte.

> **Point à consigner** : sur ces deux originaux, l'émetteur n'est pas porté par un logo image —
> il n'y a aucune image de contenu dans le PDF. L'émetteur est simplement **absent du document**,
> texte comme image. C'est une nuance par rapport à la formulation de §A.1 (« identité portée par
> un logo image non-OCR »), qui reste peut-être vraie pour Nortia mais ne l'est pas ici.
> Le seul jeton textuel évoquant un groupe assureur est le **nom d'un support** — « Actif Général
> Generali Vie » (p.3, 2024 et 2025) — donc une **donnée de portefeuille, pas une ancre** : ce
> support est absent des documents 2023, 2026.03 et 2026.06. À n'utiliser en aucun cas comme
> indice d'identification.

---

## (b) Comparaison des trois couches — original 2024 vs original 2025

### Couche 1 — métadonnées

| Champ | 2024 (orig.) | 2025 (orig.) | Verdict |
|---|---|---|---|
| Creator | `JasperReports (report name)` | `JasperReports (report name)` | identique |
| Producer | `iText 2.1.7 by 1T3XT` | `iText 2.1.7 by 1T3XT` | identique |
| PDF version | 1.4 | 1.4 | identique |
| Polices | Helvetica, Helvetica-Bold | Helvetica, Helvetica-Bold | identique |
| Pages | 4 | 4 | identique (coïncidence — cf. rééditions à 3 p.) |
| CreationDate | 28/01/2025 | 05/03/2026 | 13 mois d'écart réel |

**Aucune évolution du moteur en 13 mois** : ni version d'iText, ni version de PDF, ni jeu de
polices. Le générateur est figé sur une version ancienne (iText 2.1.7, PDF 1.4).

Complément utile : la couche 1 de Spirica (`2024.12`/`2025.12 relevé UAF Cerise.pdf`) est
`Creator = JasperReports Library version 6.19.1-867c00bf…` / `Producer = OpenPDF 1.3.40` /
PDF 1.5 / polices `Times-Roman, Helvetica, Times-Bold`. Voir §(g) : la collision annoncée en
B.5 est une collision de **mot**, pas de **chaîne**.

### Couche 2 — ancres boilerplate

Les 10 ancres de B.5, plus 20 chaînes candidates supplémentaires relevées sur les originaux,
testées verbatim (espaces normalisés) sur les deux documents :

| Ancre | 2024 | 2025 |
|---|---|---|
| `Relevé de situation au` | OK | OK |
| `Ce document n'est pas assimilable à un état de situation.` | OK | OK |
| `Souscripteur` | OK | OK |
| `Nom du produit` / `HIMALIA CAPITALISATION` | OK | OK |
| `N° du contrat` | OK | OK |
| `Durée de contrat` | OK | OK |
| `Date d'effet du contrat` / `Date d'effet fiscale` | OK | OK |
| `Option Fiscale` / `Profil de gestion` / `Option de prévoyance` | OK | OK |
| `Total versé depuis l'origine` | OK | OK |
| `Total investi depuis l'origine` | OK | OK |
| `Total racheté depuis l'origine` | OK | OK |
| `Epargne atteinte au` | OK | OK |
| `Répartition de l'investissement` | OK | OK |
| `Plus/moins-values***` | OK | OK |
| `Support(s)` / `Nb de` / `Date de valeur` / `Valeur de part(€)` / `Montant(€)` / `%**` | OK | OK |
| `Prix d'Achat Moyen` | OK | OK |
| `Fonds Euro` / `Fonds UC` | OK | OK |
| `Le montant de l'épargne atteinte est obtenu à partir des dernières valeurs connues.` | OK | OK |
| `Point d'attention :` | OK | OK |
| `Cette information est donnée à titre indicatif et n'a aucune valeur contractuelle.` | OK | OK |

**30 / 30 ancres survivent.** Aucune disparition, aucune reformulation, aucun changement de casse.

Preuve la plus dure — `diff` du texte `-layout` de la **page 1** entre les deux originaux :

```
1c1
<                   Relevé de situation au 31/12/2024
>                   Relevé de situation au 31/12/2025
37c37
<   Epargne atteinte au 31/12/2024   : 220 545,63 €
>   Epargne atteinte au 31/12/2025   : 242 144,68 €
```

Deux lignes, portant uniquement la date d'arrêté et un montant : la page 1 est **octet pour
octet identique**, indentation comprise, entre janvier 2025 et mars 2026. Elle l'est aussi vis-à-vis
des trois rééditions (mêmes deux lignes de diff pour 2023 et 2026.06).

Sur l'ensemble du document, en isolant les lignes sans chiffre (donc sans donnée), le `diff`
2024↔2025 ne retourne que : (i) les largeurs de colonnes du rendu `-layout`, (ii) les lignes de
noms de supports. **Zéro divergence de boilerplate.**

### Couche 3 — structure

Sections ordonnées, identiques sur les deux originaux :

| # | Section | 2024 | 2025 |
|---|---|---|---|
| 1 | Titre `Relevé de situation au JJ/MM/AAAA` + disclaimer | p.1 | p.1 |
| 2 | Bloc identité souscripteur (raison sociale + adresse) | p.1 | p.1 |
| 3 | Bloc contractuel — 9 champs `libellé : valeur` | p.1 | p.1 |
| 4 | Bloc totaux — 4 lignes (versé / investi* / racheté / épargne atteinte) | p.1 | p.1 |
| 5 | Titre `Répartition` + 2 Form XObjects graphiques | p.2 | p.2 |
| 6 | Tableau `Répartition de l'investissement` + `Plus/moins-values***` | p.3 | p.3 |
| 7 | Bloc notes (*)(**)(***) + `Point d'attention :` + clause finale | **p.3** | **p.4** |
| — | page vierge de texte en fin de document | **p.4** | — |

En-têtes de colonnes : séquence de jetons strictement identique
(`Support(s)` · `Nb de parts` · `Date de valeur` · `Valeur de part(€)` · `Montant(€)` · `%**` ·
`Prix d'Achat Moyen` · `Montant(€)` · `%**`), même wrapping sur deux lignes (`Nb de` / `parts`,
`Prix d'Achat` / `Moyen`), mêmes deux groupes parents homonymes.

Et la géométrie est **identique au centième de point** (`pdftotext -bbox`, page 3) :

| Mot | 2024 xMin / yMin | 2025 xMin / yMin |
|---|---|---|
| `Répartition` (titre de page) | 274.11 / 38.28 | 274.11 / 38.28 |
| `Répartition` (titre groupe) | 156.53 / 75.526 | 156.53 / 75.526 |
| `Plus/moins-values***` | 443.21 / 75.526 | 443.21 / 75.526 |
| `Support(s)` | 50.78 / 100.026 | 50.78 / 100.026 |
| `Montant(€)` (groupe Répartition) | 310.06 / 100.026 | 310.06 / 100.026 |
| `Prix` / `d'Achat` / `Moyen` | 412.32 / 429.664 / 422.83 | 412.32 / 429.664 / 422.83 |
| `Montant(€)` (groupe PMV) | 478.56 / 100.026 | 478.56 / 100.026 |

**Attention méthodologique** : les largeurs de colonnes du rendu `pdftotext -layout` diffèrent
visiblement entre les deux documents (le tableau 2025 « paraît » plus étroit). C'est un artefact
de l'heuristique de colonnage de pdftotext, qui réagit à la longueur des chaînes de données.
Les coordonnées PDF réelles sont identiques. **Ne jamais signer sur l'espacement `-layout`.**

Invariant de contrôle (A.4 point 3) revérifié sur les deux originaux :

| | Σ `Montant(€)` groupe Répartition | `Epargne atteinte au` | Écart |
|---|---|---|---|
| 2024 (16 lignes) | 220 545,63 | 220 545,63 | **0,00** |
| 2025 (21 lignes) | 242 144,68 | 242 144,68 | **0,00** |

Σ `%**` groupe Répartition : **100,00** (2024) et **100,03** (2025) → la tolérance sur les
arrondis reste indispensable, et l'écart peut être positif comme négatif.

---

## (c) Verdict sur la dérive et amplitude comparée

> **Aucune dérive de gabarit entre décembre 2024 et décembre 2025.**

Sur les trois couches, entre deux originaux générés à **13 mois d'écart** (28/01/2025 et
05/03/2026) :

- couche 1 : identique en tout point (Creator, Producer, version PDF, polices) ;
- couche 2 : **30 ancres sur 30** survivent, page 1 identique à l'octet hors date et montant ;
- couche 3 : mêmes sections dans le même ordre, mêmes en-têtes de colonnes, **mêmes coordonnées
  au centième de point**.

Positionnement sur l'échelle de dérive du corpus :

| Émetteur | Écart entre originaux | Amplitude observée |
|---|---|---|
| **Cardif** | 12 mois | **rupture** — 1 ancre sur 11 survit, polices changent, casse change, nb de colonnes change → deux gabarits distincts |
| **Wealins** | 12 mois | **dérive mineure** — 1 ancre + 1 phrase |
| **Himalia** | **13 mois** | **dérive nulle** — 0 ancre touchée, 0 changement de police, géométrie au centième identique |

Himalia est le **plancher** de l'échelle : c'est le cas le plus stable des trois, et il est
qualitativement différent de Wealins (Wealins bouge un peu ; Himalia ne bouge pas du tout).
Explication plausible, à confirmer : le moteur est gelé sur iText 2.1.7 / PDF 1.4, une pile
figée depuis longtemps ; il n'y a apparemment pas de cycle de refonte du modèle Jasper.

Élément corroborant, hors périmètre « originaux » mais informatif : les trois rééditions du
24/07/2026, produites par le **système actuel**, sortent la **même page 1 à l'octet** (mêmes deux
lignes de diff) et les mêmes en-têtes de colonnes que l'original de janvier 2025. Autrement dit,
le gabarit n'a pas bougé non plus entre 01/2025 et 07/2026 — ce que les rééditions ne peuvent pas
prouver pour la **couche 1** (leur métadonnée est celle du système actuel, donc non contemporaine),
mais qu'elles établissent pour les couches 2 et 3, puisque le contenu boilerplate y est identique.

---

## (d) Réponse aux questions 2 et 3

### Q2 — la signature 2025 apparie-t-elle le document 2024 ?

> **Oui, sans réserve.**

Une signature construite sur le document du 31/12/2025 (couche 1 exacte + les 30 ancres
+ la structure) apparie le document du 31/12/2024 à **100 %** sur les trois couches. Et la
réciproque est vraie.

**Conséquence pour le store** : sur cet émetteur, **pas besoin de profils versionnés ni de
fenêtre de validité**. Un profil unique suffit, sans borne temporelle. C'est l'exact opposé du
besoin identifié chez Cardif. À maintenir sous surveillance simple : une divergence de couche 1
(version d'iText, apparition d'un `Metadata Stream`, changement de jeu de polices) serait le
signal avancé d'une refonte du moteur, à traiter comme une proposition « nouveau gabarit d'un
émetteur connu » (§A.5 point 1).

### Q3 — couches stables vs volatiles, et les polices

| Élément | Statut sur les 2 originaux | Utilisable en signature ? |
|---|---|---|
| Creator (chaîne exacte) | stable | **oui**, sous forme de chaîne exacte |
| Producer (chaîne exacte) | stable | **oui** |
| Version PDF (1.4) | stable | oui, en appoint |
| **Liste des polices** | **strictement stable** (2 polices, non embarquées) | oui **pour séparer les émetteurs**, **non pour séparer les millésimes** — voir ci-dessous |
| Ancres boilerplate (30) | stable | **oui — cœur discriminant** |
| Titres de sections + ordre | stable | oui |
| En-têtes de colonnes + wrapping | stable | oui |
| Géométrie (x/y des en-têtes) | stable au centième | oui, en confirmation forte (mais coûteux) |
| Invariant Σ = Épargne atteinte | vérifié exact 2 fois | oui, comme contrôle d'extraction |
| Nombre de pages | 3 ↔ 4 sur le corpus | **non** |
| Page portant le bloc notes | p.3 (2024) ↔ p.4 (2025) | **non** |
| Page vierge terminale | présente (2024) ↔ absente (2025) | **non** |
| Nombre de lignes de supports | 9 → 21 | **non** |
| Présence de la catégorie `Fonds Euro` | conditionnelle | **non** (cf. §e) |
| Noms de supports | volatils | **non** |
| Largeurs de colonnes du rendu `-layout` | artefact de pdftotext | **non** |
| CreationDate / ModDate / taille fichier | volatils par nature | **non** (A.3) |

**Sur les polices, la question posée directement.** Chez Cardif, la liste des polices discrimine
parfaitement deux gabarits que Creator et Producer ne séparaient pas. **Ce n'est pas le cas ici.**
La liste est `{Helvetica, Helvetica-Bold}` sur les cinq documents Himalia — donc identique entre
les deux originaux comme entre originaux et rééditions. Elle a **zéro pouvoir discriminant sur
l'axe temporel** chez cet émetteur.

Elle en a en revanche sur l'axe **inter-émetteurs** : `{Helvetica, Helvetica-Bold}` (Himalia)
contre `{Times-Roman, Helvetica, Times-Bold}` (Spirica) sépare les deux émetteurs « JasperReports »
sans ambiguïté. Formulation prudente à retenir : **la liste des polices est un discriminant
d'émetteur ici, pas un détecteur de dérive** ; son pouvoir dépend de l'émetteur et ne se
généralise pas depuis le cas Cardif.

---

## (e) Sections requises vs optionnelles

Le phénomène Spirica (« ce qui ressemble à plusieurs gabarits n'est qu'un gabarit dont des
sections apparaissent selon la donnée ») **existe ici aussi**, sur deux niveaux.

### Requis — présent dans les 5 documents, sans exception

1. Titre `Relevé de situation au JJ/MM/AAAA` + disclaimer.
2. Bloc identité souscripteur (raison sociale, adresse).
3. Bloc contractuel — les **9 champs**, toujours les 9, toujours dans le même ordre
   (`Souscripteur`, `Nom du produit`, `N° du contrat`, `Durée de contrat`,
   `Date d'effet du contrat`, `Date d'effet fiscale`, `Option Fiscale`, `Profil de gestion`,
   `Option de prévoyance`). Aucun champ ne disparaît quand il est vide : il est rempli par un
   marqueur (`Option de prévoyance : N.C.`).
4. Bloc totaux — les **4 lignes**, y compris à zéro (`Total racheté depuis l'origine : 0,00 €`
   dans les cinq documents). Une valeur nulle **ne supprime pas** la ligne.
5. Titre `Répartition` + les 2 Form XObjects graphiques (p.2, BBox identiques dans les 5).
6. Tableau `Répartition de l'investissement` / `Plus/moins-values***` avec ses 9 en-têtes.
7. Bloc notes (*)(**)(***) + `Point d'attention :` + `Cette information est donnée à titre
   indicatif et n'a aucune valeur contractuelle.`

### Conditionnel — dépend de la donnée

| Élément | Condition | Preuve dans le corpus |
|---|---|---|
| **Catégorie `Fonds Euro`** (titre + sa ligne unique) | le portefeuille détient un fonds euros | présente 2024 et 2025 ; **absente** de 2023, 2026.03, 2026.06 (`grep` : 0 occurrence) |
| Cellules `Nb de parts` et `Valeur de part(€)` de la ligne fonds euros | toujours vides sur cette ligne | 2024 et 2025 : `Actif Général Generali Vie` n'a que la date de valeur et le montant |
| Colonnes `Prix d'Achat Moyen` / `Montant(€)` / `%**` du groupe PMV, sur la ligne fonds euros | jamais renseignées | 2024, 2025 |
| Cellule `%**` du groupe PMV, sur une ligne UC | vide quand `PAM = 0,00 €` | **0 cas en 2024**, **4 cas en 2025** (`AURIS Active Diversif Beta R`, `GENERALI Trésorerie ISR Act B`, `ODDO BHF Avenir CR`, `R-CO Thematic Real Estate C`) |
| Répétition du titre de catégorie `Fonds UC` en page suivante | absente | non reproductible sur les originaux (tableau tenant sur p.3) ; observable sur la réédition 2023 (tableau p.2→p.3, `Fonds UC` 1 seule occurrence) |
| Position du bloc notes | p.3 si le tableau laisse la place, sinon p.4 | 2024 → p.3 ; 2025 → p.4 |
| Page terminale vierge de texte | apparaît quand les notes tiennent sur la page du tableau | 2024, 2026.03, 2026.06 : p.4 à 0 caractère ; 2025 : pas de page vierge |

`Fonds Euro` est donc l'analogue exact du cas Spirica : une **section absente parce que le
portefeuille ne la justifie pas**, pas un gabarit différent. Un profil qui exigerait `Fonds Euro`
rejetterait à tort trois documents sur cinq.

**Incertitude** : rien dans le corpus ne dit s'il existe d'autres catégories possibles
(immobilier, structuré, titres vifs…). Deux valeurs observées seulement, `Fonds Euro` et
`Fonds UC`. À traiter comme une **liste ouverte** de catégories, dont aucune n'est requise
individuellement, et non comme une énumération fermée.

---

## (f) Périodicité et son token

> **Aucun token de périodicité n'est lisible dans le document.** Ni sur les originaux, ni sur
> les rééditions.

Recherche exhaustive, insensible à la casse, sur les cinq documents
(`annuel*`, `trimestr*`, `mensuel*`, `semestr*`, `périod*`, `cumul*`, `Page [0-9]+`) :
**zéro occurrence** de chacun de ces motifs, sur les cinq documents. Il n'y a pas non plus de
`Page X/Y`.

Les trois enseignements à ne pas répéter ont été instruits, et un quatrième piège local écarté :

| Piège | Vérification | Écarté parce que |
|---|---|---|
| Spirica : « trimestriels » = offre commerciale | mot absent ici | pas d'occurrence |
| Cardif : « pour l'année » = fenêtre de cumul YTD | motif absent ici | pas de bloc « cumul des opérations » du tout |
| Wealins : seul token fiable = label d'en-tête d'annexe en capitales | pas d'annexe ici | document non composite, pas d'en-tête de ce type |
| **Local — `Durée de contrat : 8 années`** | seule occurrence du radical « anné » dans les 5 documents | c'est la **durée du contrat**, pas une cadence. Exactement le faux ami de type Cardif : le mot « année » apparaît, mais dans un champ contractuel |

Vérification demandée dans les deux sens (le mot est-il présent ? et s'il est présent, désigne-t-il
bien la cadence ?) : le seul candidat est « années », et il ne désigne pas la cadence. Confirmé
par le fait qu'il porte la valeur `8` et non une fréquence.

Ce que le corpus dit, indirectement, de la cadence réelle :

- Le titre est `Relevé de situation au <date>` — un **instantané à une date**, sans mention de
  période couverte, sans dates de début/fin, sans aucun agrégat de flux sur période. Toutes les
  grandeurs sont soit « depuis l'origine », soit valorisées à la date d'arrêté.
- Les deux originaux ont un arrêté au 31/12, et sont produits **28/01/2025** et **05/03/2026** :
  soit des délais de production très différents (28 jours, puis 64 jours) pour un même type
  d'arrêté. Un envoi périodique réglementaire aurait plutôt un délai stable. Indice faible en
  faveur d'une production **à la demande**.
- Les rééditions portent des arrêtés au **31/03/2026** et **30/06/2026** avec un gabarit strictement
  identique. Le modèle accepte donc n'importe quelle date d'arrêté. **Réserve importante** : ces
  arrêtés ont été choisis lors de la régénération du 24/07/2026 ; ils prouvent que la date d'arrêté
  est **paramétrable**, pas qu'il existe une cadence trimestrielle native.

**Conclusion.** La périodicité **n'est pas inscrite dans le document** et n'est pas déductible du
contenu. Le champ `periodicite` du profil B.5 (« indéterminée sur 1 spécimen, arrêté 31/12 →
annuel probable ») doit être corrigé : non pas « annuel probable » mais **« non inscrite dans le
document ; arrêté paramétrable ; à la demande »**. La mention « annuel probable » était une
inférence à partir de la seule date d'arrêté du spécimen unique — c'est-à-dire précisément
l'erreur que §A.4 point 2 interdit (« la date d'arrêté ne discrimine PAS »).

Corollaire pour le modèle de clé : sur cet émetteur, la troisième dimension
`émetteur × gabarit × périodicité` **n'est pas observable dans le document**. Soit elle vaut
`sur_demande` / `non_inscrite`, soit elle doit être renseignée depuis une source externe au PDF.
C'est le premier cas du corpus où cette dimension est structurellement inaccessible.

---

## (g) Pièges du §B.5 — confirmés, disparus, nouveaux

### Confirmés

| Piège B.5 | Statut | Preuve |
|---|---|---|
| Colonnes **homonymes** `Montant(€)` et `%**` sous 2 groupes parents différents | **confirmé** | les 2 originaux ; `Montant(€)` à x=310.06 (groupe Répartition) et x=478.56 (groupe PMV), même y=100.026 → désambiguïsation par x ou par groupe parent obligatoire |
| Sans `-layout`, réordonnancement total | **confirmé** | sans `-layout` sur 2025 p.3, les en-têtes sortent dans l'ordre `Support(s)` / `Nb de parts` / `Date de valeur Valeur de part(€)` / `Plus/moins-values***` / `Montant(€)` / `%**` / `Prix d'Achat Moyen` / `Montant(€)` / `%**` — les deux groupes sont entremêlés. `-layout` impératif |
| Colonne `%**` du groupe PMV **vide** quand `PAM = 0,00 €` | **confirmé et renforcé** | 4 cas en 2025 (`AURIS`, `GENERALI Trésorerie ISR`, `ODDO BHF Avenir CR`, `R-CO Thematic Real Estate`) ; 0 cas en 2024 → un parseur validé sur le seul millésime 2024 aurait cassé sur 2025 |
| **Aucune ligne Total** dans le tableau, recalcul obligatoire | **confirmé** | vérifié au centime deux fois : Σ 16 lignes = 220 545,63 € (2024), Σ 21 lignes = 242 144,68 € (2025) |
| Titre de catégorie non répété en page suivante | **confirmé mais conditionnel** | non reproductible sur les originaux (tableau sur une seule page) ; observable sur la réédition 2023 (tableau p.2→p.3, `Fonds UC` une seule occurrence) |
| Noms de supports **wrappés sur 2 lignes** | **confirmé** | fréquent dans les deux originaux (`CARMIGNAC PTF Credit` / `A Eur`, `INDEPENDANCE Fr Sm` / `& Mid A`…) |
| `€` explicite dans `Prix d'Achat Moyen`, implicite dans `Montant(€)` | **confirmé** | `107,70 €` vs `3 795,97` sur la même ligne (2024 p.3) |
| **Pas d'ISIN** — référentiel externe nom→ISIN requis | **confirmé** | aucun code ISIN dans les 2 originaux |
| **Aucune pagination texte** (`Page X/Y` absent) | **confirmé** | 0 occurrence de « Page » dans les 5 documents ; position uniquement par `pdfinfo` / index de page |
| Σ `%**` ≈ 99,99, jamais exiger 100,00 strict | **confirmé et précisé** | 100,00 (2024) et **100,03** (2025) → l'écart est **bilatéral**, la tolérance doit être ± et non « au plus 100,00 » |

Aucun piège de B.5 n'a disparu. Un seul (« Fonds UC non répété p.3 ») n'est pas reproductible sur
les originaux, faute de tableau multi-pages — il reste réel, simplement conditionnel.

### Nuancé — la mise en garde couche 1

B.5 avertit : « JasperReports aussi chez Spirica, jamais suffisant seul ». **Vrai au niveau du mot,
faux au niveau de la chaîne exacte.**

| | Himalia | Spirica (UAF Cerise) |
|---|---|---|
| Creator | `JasperReports (report name)` | `JasperReports Library version 6.19.1-867c00bf88cd4d784d404379d6c05e1b419e8a4c` |
| Producer | `iText 2.1.7 by 1T3XT` | `OpenPDF 1.3.40` |
| PDF version | 1.4 | 1.5 |
| Polices | Helvetica, Helvetica-Bold | Times-Roman, Helvetica, Times-Bold |

Le triplet (Creator exact, Producer, liste de polices) **sépare parfaitement** les deux émetteurs.
La reformulation correcte du piège : *ne jamais réduire Creator au mot « JasperReports » ; la
chaîne complète, elle, discrimine — et reste stable dans le temps chez chacun des deux émetteurs
(vérifié sur 2 millésimes chacun).* Le pré-filtre couche 1 est donc plus utile que ne le laissait
penser B.5, sans pour autant remplacer la couche 2.

### Nouveaux

| # | Piège | Détail |
|---|---|---|
| N1 | **Page 2 quasi vide en texte, mais porteuse de deux graphiques vectoriels** | `pdftotext` rend 11 caractères (`Répartition`) là où le document affiche 2 Form XObjects (BBox 520×373 et 500×290). Un filtre du type « page vide → ignorer » supprimerait une section requise. La section 5 doit être détectée par la présence des XObjects, pas par le texte |
| N2 | **Page terminale vierge de texte, apparaissant ou non** | p.4 à 0 caractère en 2024, 2026.03, 2026.06 ; absente en 2025. Renforce l'exclusion du nombre de pages, et interdit « dernière page = notes » |
| N3 | **Le bloc notes change de page selon la longueur du tableau** | p.3 en 2024, p.4 en 2025. Le bloc notes doit être cherché en fin de document, pas sur un numéro de page |
| N4 | **Continuation de nom de support purement numérique** | 2024 p.3, dernier support : `Tempo Quot Degr CA` puis, en ligne suivante, `1.05 Nov 24`. Un parseur qui décide « ligne commençant par un chiffre = ligne de données » la prendra pour une donnée. Voir aussi `K SG Degressif Mai 2024`, dont le nom contient une année |
| N5 | **Les largeurs de colonnes du rendu `-layout` varient sans que le gabarit change** | la géométrie PDF est identique au centième, seul le colonnage heuristique de pdftotext bouge avec la longueur des données. Ni signature ni parsing ne doivent dépendre du nombre d'espaces |
| N6 | **Aucun identifiant de template natif** | contrairement à Cardif (`<MODELE>`), `/Root` ne contient rien d'exploitable et le Creator est un placeholder non renseigné (`(report name)`). Le champ `template_id_natif` du profil reste vide chez cet émetteur |
| N7 | **`Generali` apparaît en texte, mais comme nom de support** | `Actif Général Generali Vie` (2024 et 2025 p.3), absent des trois autres documents. Une heuristique « chercher un nom d'assureur dans le texte » produirait ici une identification correcte par accident en 2024-2025, et échouerait en 2023/2026. À exclure formellement |
| N8 | **Aucune image de contenu dans le PDF** | l'émetteur n'est pas porté par un logo image : il n'y a aucune image (hors deux bitmaps 1×1 px d'aplat). Nuance vis-à-vis de la formulation de §A.1 |

---

## (h) Ce que je n'ai pas pu établir

1. **Nature exacte des deux Form XObjects de la page 2.** Établi : présents dans les 5 documents,
   mêmes BBox, sans texte extractible. Non établi : ce qu'ils représentent (camembert de
   répartition, histogramme…). Je n'ai pas décompressé leurs flux.
2. **La cadence réelle d'émission.** Le document ne la porte pas. Les délais de production
   observés (28 j puis 64 j après l'arrêté) suggèrent une production à la demande, mais deux
   points ne font pas une démonstration. À trancher hors PDF (contrat, échange avec l'assureur).
3. **La liste complète des catégories de supports.** Seules `Fonds Euro` et `Fonds UC` observées.
   Impossible de savoir si d'autres existent, ni si `Fonds Euro` précède toujours `Fonds UC`
   dans l'ordre (une seule configuration observée).
4. **Le comportement en tableau multi-pages sur un original.** Les deux originaux tiennent sur une
   page de tableau. Le piège « catégorie non répétée » et l'éventuelle répétition des en-têtes de
   colonnes en page suivante ne sont documentés que via la réédition 2023.
5. **La stabilité de la couche 1 au-delà de mars 2026.** Les rééditions du 24/07/2026 montrent
   `iText 2.1.7` / PDF 1.4, mais leur métadonnée est celle du système de régénération : rien ne
   garantit que le flux de production courant utilise la même pile. Un original postérieur à
   mars 2026 serait nécessaire.
6. **La variabilité inter-contrats.** Un seul contrat dans le corpus (83150223, HANAMI
   INVESTISSEMENTS, personne morale, option `Capitalisation`, profil `Versement Libre`). Les
   comportements liés à un autre profil de gestion, à une personne physique, à une option de
   prévoyance renseignée ou à un contrat avec rachats (`Total racheté` ≠ 0) sont hors corpus.
   Aucun réplicat intra-millésime, contrairement à Spirica et Wealins.
7. **L'identité de l'émetteur.** Hors mission, et de toute façon non lisible : ni texte, ni image.
   Le nommage humain au seed reste requis (§A.1 point 4).
