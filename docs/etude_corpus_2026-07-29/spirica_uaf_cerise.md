# Dérive de gabarit dans le temps — Spirica (dist. UAF Life Patrimoine), contrat Cerise

> **2026-07-29.** Prolongement de `etude_signature_gabarits_2026-07-27.md` (§B.3) sur l'axe
> temporel, non couvert par l'étude d'origine.
> Corpus : 6 relevés du **même contrat** (n° 443909428, « Version Absolue 2 », date d'effet
> 14 décembre 2022), arrêtés du 31/12/2022 au 30/06/2026.
> Méthode : signature en trois couches (1 métadonnées PDF, 2 ancres texte, 3 marqueurs de
> structure). Nombre de pages hors matching, conformément à la partie A §A.3.
> Extractions : `pdfinfo`, `pdffonts`, `pdftotext -layout`, `pdftotext -bbox` (coordonnées).

---

## (a) Inventaire des 6 documents

Tous dans `Données assureur/`, nommés `AAAA.MM relevé UAF Cerise.pdf`.

| Arrêté | Fichier (octets) | Pages | Creator | Producer | CreationDate PDF | Format page | PDF |
|---|---|---|---|---|---|---|---|
| 31/12/2022 | 36 909 | 2 | JasperReports Library 6.19.1-867c00bf88cd4d784d404379d6c05e1b419e8a4c | OpenPDF 1.3.40 | 24/07/2026 14:02:36 | 595×842 (A4) | 1.5 |
| 31/12/2023 | 45 008 | 4 | idem | OpenPDF 1.3.40 | 24/07/2026 14:01:42 | 595×842 | 1.5 |
| 31/12/2024 | 45 042 | 4 | idem | OpenPDF 1.3.40 | 24/07/2026 14:01:08 | 595×842 | 1.5 |
| 31/12/2025 | 45 027 | 4 | idem | OpenPDF 1.3.40 | 24/07/2026 14:00:39 | 595×842 | 1.5 |
| 31/03/2026 | 48 157 | 4 | idem | OpenPDF 1.3.40 | 24/07/2026 14:00:14 | 595×842 | 1.5 |
| 30/06/2026 | 50 299 | 4 | idem | OpenPDF 1.3.40 | 24/07/2026 13:58:53 | 595×842 | 1.5 |

Attributs identiques sur les six : `Tagged: no`, `Metadata Stream: no`, `Custom Metadata: no`,
`Form: none`, `JavaScript: no`, `Encrypted: no`, `Optimized: no`, `Page rot: 0`.

Polices (`pdffonts`) — **jeu identique sur les six**, aucune police embarquée :

```
Times-Roman   Type 1  WinAnsi  emb=no
Helvetica     Type 1  WinAnsi  emb=no
Times-Bold    Type 1  WinAnsi  emb=no
```

Texte natif propre sur les six (zéro OCR).

**Point d'interprétation important sur la couche 1.** Les six `CreationDate` sont regroupés dans
un intervalle de ~4 minutes le **24/07/2026**, et les six documents portent la même date de
courrier « `LYON, le 24 juillet 2026` ». Ce sont donc **six rééditions simultanées** produites par
le même binaire, le même jour, depuis l'extranet. Conséquence : `CreationDate` ne mesure **rien**
de l'axe temporel étudié — elle mesure la date de téléchargement. La version de générateur qui
aurait été en service en 2022 ou 2023 est **inobservable dans ce corpus** (voir §g). L'écart
arrêté ↔ édition atteint ici **+3 ans 7 mois** (arrêté 31/12/2022, édition 24/07/2026), ce qui
confirme et amplifie le piège « réédition à +4 ans » du §B.3.

Répartition des sections par page :

| Arrêté | p.1 | p.2 | p.3 | p.4 |
|---|---|---|---|---|
| 31/12/2022 | courrier + `SITUATION AU` + `Valeur de rachat*` | clôture + signature + interlocuteurs | — | — |
| 31/12/2023 | courrier seul | `SITUATION AU` | `PRIX DE REVIENT MOYEN` + `Valeur de rachat*` | clôture |
| 31/12/2024 | courrier seul | `SITUATION AU` | `PRIX DE REVIENT MOYEN` + `Valeur de rachat*` | clôture |
| 31/12/2025 | courrier seul | `SITUATION AU` | `PRIX DE REVIENT MOYEN` + `Valeur de rachat*` | clôture |
| 31/03/2026 | courrier + `SITUATION AU` | `PRIX DE REVIENT MOYEN` + `Valeur de rachat*` | `DÉTAIL DES OPÉRATIONS` (2 groupes) | clôture |
| 30/06/2026 | courrier + `SITUATION AU` | `PRIX DE REVIENT MOYEN` + `Valeur de rachat*` | `DÉTAIL DES OPÉRATIONS` (2 groupes) | `DÉTAIL DES OPÉRATIONS` (3ᵉ groupe) **+ clôture** |

Nombre de lignes supports du tableau `SITUATION` : 1 (2022), 15 (2023, 2024, 2025), 10 (2026.03,
2026.06). La pagination suit mécaniquement ce nombre — voir §c.

---

## (b) Comparaison des couches, date par date

### Couche 1 — métadonnées

| Élément | 2022.12 | 2023.12 | 2024.12 | 2025.12 | 2026.03 | 2026.06 |
|---|---|---|---|---|---|---|
| Creator (chaîne complète, hash de build inclus) | = | = | = | = | = | = |
| Producer `OpenPDF 1.3.40` | = | = | = | = | = | = |
| Jeu de polices (3, non embarquées) | = | = | = | = | = | = |
| Format A4 595×842, PDF 1.5, non taggé | = | = | = | = | = | = |

**Zéro divergence.** Y compris le hash de build JasperReports
(`6.19.1-867c00bf88cd4d784d404379d6c05e1b419e8a4c`), identique aux six. Rappel : cette égalité est
un artefact de réédition simultanée, pas une preuve de stabilité du générateur sur 4 ans.

### Couche 2 — ancres texte

Comparaison exhaustive des lignes normalisées (trim + collapse des espaces, tri, `comm`) entre le
document le plus ancien et le plus récent, hors lignes porteuses de valeurs :

**Ancres présentes en 2022.12 et absentes en 2026.06** — après exclusion des lignes de valeur et
des compteurs de page, il ne reste qu'**une seule** ligne :

```
l'ensemble des opérations intervenues sur votre contrat depuis son origine.
```

remplacée en 2023→2026 par :

```
l'ensemble des opérations intervenues sur votre contrat depuis le dernier État de Situation.
```

**Aucun libellé n'a été supprimé, aucun n'a été renommé.** L'ensemble des ancres du §B.3 est
vérifié verbatim sur les six documents :

| Ancre (§B.3) | 2022 | 2023 | 2024 | 2025 | 2026.03 | 2026.06 |
|---|---|---|---|---|---|---|
| `Objet : Relevé de Situation` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `SITUATION AU` (bandeau centré) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `Montant de la valeur atteinte au` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `Valeur de rachat*` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `Le Relevé de Situation n'engage en rien la responsabilité de SPIRICA.` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `Ce document n'a pas de valeur contractuelle.` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `Vos interlocuteurs à votre service :` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `Directrice Générale de Spirica` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `Le rachat est l'opération par laquelle vous demandez` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |

Ancres supplémentaires stables non listées au §B.3, vérifiées sur les six :

```
Votre contrat Version Absolue 2
Votre numéro de contrat :
Date d'effet :
Cadre fiscal : Assurance Vie
LYON, le
Nous avons le plaisir de vous remettre votre Relevé de Situation arrêté au
Nous vous rappelons que les relevés de situation trimestriels pourront être mis à votre disposition
Toujours attentifs au suivi de votre dossier, votre conseiller et nous-mêmes restons à votre disposition
Nous vous prions de croire, [civilité], en l'expression de nos respectueuses salutations.
Gestion libre
Anaïd Chahinian
EMERAUDE GESTION PRIVEE / en partenariat avec UAF LIFE PATRIMOINE
Il vous permet de prendre connaissance de la valeur atteinte de votre contrat avant réception de
votre prochain État de Situation. […]
```

**Ancres apparaissant à partir de 2023.12** (bloc PRM, 4 notes de bas de page) :

```
PRIX DE REVIENT MOYEN AU [date]
* Le PRM représente le prix d'achat moyen d'un support, frais de gestion déduits.
** Pour chaque support en unité de compte on calcule la plus ou moins-value estimée en montant […]
À noter : pour les unités de compte qui distribuent des dividendes ou des revenus (par exemple les SCPI) […]
*** Pour chaque support en unité de compte on calcule la plus ou moins-value estimée en % […]
```

**Ancres apparaissant à partir de 2026.03** (bloc opérations) :

```
DÉTAIL DES OPÉRATIONS
Liste des opérations réalisées depuis le dernier État de Situation.
Arbitrage ponctuel        Date de valeur : […]   Montant brut : […]
Frais de gestion sur UC   Date de valeur : […]   Montant brut : […]
```

Ces libellés sont **ajoutés, jamais substitués** : la couche 2 est strictement croissante sur la
série. Le libellé 2022 est un **sous-ensemble** du libellé 2026, à l'exception de la variante de
phrase d'introduction ci-dessus.

### Couche 3 — marqueurs de structure

En-têtes de colonnes du tableau `SITUATION` — libellé, découpage sur 3 lignes et césure
**strictement identiques** sur les six (extraits `-layout`, 2022 à gauche, 2026.06 à droite) :

```
2022.12  Valeur de la part | Date de | Nombre de parts    | Valeur atteinte au    | %
         en euros          | valeur  | au 31/12/2022      | 31/12/2022 en euros
2026.06  Valeur de la part | Date de | Nombre de parts    | Valeur atteinte au    | %
         en euros          | valeur  | au 30/06/2026      | 30/06/2026 en euros
```

Vérification par coordonnées (`pdftotext -bbox`, en points, origine haut-gauche) — les cellules
d'en-tête sont **au même pixel** d'un bout à l'autre de la série :

| Tableau | Mot d'en-tête | 2022.12 | 2023.12 | 2026.06 |
|---|---|---|---|---|
| `SITUATION` | `Support` (xMin) | 124,00 | 124,00 | 124,00 |
| `SITUATION` | `Nombre` (xMin) | 368,12 | 368,12 | 368,12 |
| `SITUATION` | `atteinte` (xMin) | 466,67 | 466,67 | 466,67 |
| `SITUATION` | y de la bande d'en-tête (quand le tableau suit le courrier sur p.1) | 460,81 / 465,41 | — (tableau seul en p.2 : y=164,81) | 460,81 / 465,41 |
| `PRIX DE REVIENT MOYEN` | `Support` (xMin) | — | 139,50 | 139,50 |
| `DÉTAIL DES OPÉRATIONS` | `Support` / `Nombre` (xMin) | — | — | 139,50 / 449,12 |
| Pied de page (3 lignes disclaimer) | y | 752,80 / 760,85 | 752,80 / 760,85 | 752,80 / 760,85 |

Autres marqueurs :

| Marqueur | 2022 | 2023–2025 | 2026.03–06 |
|---|---|---|---|
| Bandeau centré `SITUATION AU [date en clair]` | ✔ | ✔ | ✔ |
| En-tête `Contrat n° [n°]` seul, sur **toutes les pages sauf la p.1** | ✔ (p.2) | ✔ (p.2-3-4) | ✔ (p.2-3-4) |
| Pied `Page X / Y` + 3 lignes de disclaimer SPIRICA, **sur chaque page** | ✔ | ✔ | ✔ |
| Sous-titre mode de gestion `Gestion libre` avant chaque tableau | ✔ | ✔ | ✔ |
| Bloc final 3 paires label:valeur (conseiller / Adresse / Téléphone) | ✔ | ✔ | ✔ |
| Signature nominative + fonction | ✔ | ✔ | ✔ |
| Colonnes à date embarquée dans le libellé | 2 | 2 (+1 dans PRM) | 2 (+1 dans PRM) |

Conventions numériques — identiques sur les six, vérifiées à l'octet :

- séparateur de milliers = **espace ordinaire U+0020** (`70 036,94` → `37 30 20 30 33 36 2c 39 34`) ;
  ce n'est pas une espace insécable.
- séparateur décimal = virgule ; symbole `€` = U+20AC, **précédé d'une espace ordinaire**, postfixé.
- pourcentage postfixé, espace avant `%`.
- nombre de parts à **5 décimales** (`213,64128`), sans symbole.
- négatifs par signe `-` collé au chiffre (`-11 390,11 €`, `-88,03610`).
- **le pourcentage n'est pas à décimales fixes** : `100 %` en 2022.12 p.1 (pas `100,00 %`), contre
  `31,33 %` en 2026.06. Les montants, eux, sont systématiquement à 2 décimales.

---

## (c) Verdict sur la dérive

**Un seul gabarit sur toute la série. La dérive de gabarit n'est pas démontrée.** Les six documents
sont, sur les trois couches, le même modèle : mêmes métadonnées, mêmes polices, mêmes ancres (par
inclusion), mêmes libellés de colonnes avec la même césure, mêmes coordonnées de cellules
d'en-tête et de pied de page au centième de point, mêmes conventions numériques.

Ce qui varie n'est pas le gabarit mais la **présence de blocs conditionnels** et la
**pagination du flux**. Trois configurations observées :

| Config | Blocs présents | Observée sur | Cause établie ou probable |
|---|---|---|---|
| C1 | courrier + `SITUATION` + `Valeur de rachat` + clôture | 2022.12 | contrat mono-support en fonds euro (1 ligne, 100 %) ; contrat vieux de 17 jours |
| C2 | C1 + `PRIX DE REVIENT MOYEN` | 2023.12, 2024.12, 2025.12 | apparition d'unités de compte au portefeuille |
| C3 | C2 + `DÉTAIL DES OPÉRATIONS` | 2026.03, 2026.06 | fenêtre d'opérations non vide sur la période |

Le bloc `PRIX DE REVIENT MOYEN` est **piloté par la donnée, non par le gabarit** : le PRM n'a de
sens que pour les unités de compte (« *Pour chaque support en unité de compte on calcule…* »), et
le contrat n'en détenait aucune au 31/12/2022 — le tableau `SITUATION` de 2022 ne comporte que la
ligne `Fonds Euro Nouvelle Génération` à 100 %. L'absence du bloc en 2022 ne prouve donc rien sur
le modèle.

Le bloc `DÉTAIL DES OPÉRATIONS` est **probablement** conditionnel de la même façon, sa fenêtre
étant « *depuis le dernier État de Situation* » — fenêtre vide sur un arrêté au 31/12 si l'État de
Situation réglementaire est lui-même arrêté au 31/12. Cette lecture n'est pas complètement
établie : voir §g, point 2.

La pagination est un pur effet de flux, et l'observation est concluante : en 2022 (1 ligne) comme
en 2026 (10 lignes) le tableau `SITUATION` tient sur la page 1 et démarre à **y=460,81 exactement**
sous le courrier ; en 2023–2025 (15 lignes) il ne tient plus et le moteur le renvoie en tête de
page 2 (y=164,81). Le même gabarit produit donc 2 ou 4 pages, et 1 ou 2 pages de tableau
d'opérations (2026.06 : le 3ᵉ groupe d'opérations déborde en p.4, **où il cohabite avec le bloc de
clôture**). Confirmation directe du §A.3 : le nombre de pages est inutilisable comme critère, et
même l'affectation d'une section à un numéro de page l'est.

### Question décisive pour O15 : la signature 2026 apparie-t-elle le document 2022 ?

**Oui, à une condition, et cette condition est le résultat le plus important de l'étude.**

- Si la signature est définie comme « **noyau requis + blocs optionnels** » : le document de 2022
  apparie parfaitement. Le noyau (couche 1 complète, les 9 ancres du §B.3, les 5 marqueurs de
  structure, les en-têtes du tableau `SITUATION`) est présent aux six dates sans une seule
  divergence.
- Si la signature exige la présence des ancres du bloc PRM ou du bloc opérations, alors le
  document 2022 **échoue le match** — et 2023–2025 échoueraient aussi sur le bloc opérations.
  On créerait alors 3 profils versionnés là où il n'y a qu'un gabarit et un portefeuille qui
  évolue : trois profils qui se déclencheraient par tirage au sort selon l'année.

**Conclusion opérationnelle : un profil unique suffit, à condition que le schéma de profil
distingue explicitement `sections_requises` de `sections_optionnelles`.** Le §B.3 actuel liste
`sections_ordonnees` à plat, sans cette distinction — c'est le correctif à apporter.

Un seul point exigerait une tolérance textuelle et non structurelle : la phrase d'introduction,
dont la fin varie (`depuis son origine` / `depuis le dernier État de Situation`). Elle doit être
ancrée sur son préfixe stable `l'ensemble des opérations intervenues sur votre contrat depuis`.

---

## (d) Couches stables vs volatiles

### Stables sur les 6 dates — utilisables comme ancre durable

| # | Élément | Couche | Confiance |
|---|---|---|---|
| 1 | `Creator = JasperReports Library 6.19.1-<hash>` + `Producer = OpenPDF 1.3.40` | 1 | forte sur le corpus, **mais** artefact de réédition simultanée (§g point 1) — et sous-discriminant (JasperReports aussi chez Himalia) |
| 2 | Jeu de polices exact : Times-Roman + Helvetica + Times-Bold, Type 1, WinAnsi, non embarquées | 1 | forte ; même réserve |
| 3 | Les 9 ancres du §B.3, verbatim | 2 | **très forte — cœur du matching** |
| 4 | Bloc légal en pied de page : 3 lignes constantes + `Page X / Y`, sur chaque page, y=752,80/760,85 | 2+3 | **très forte** |
| 5 | En-têtes du tableau `SITUATION` : libellés, césure sur 3 lignes, xMin 124,00 / 368,12 / 466,67 | 3 | **très forte** |
| 6 | En-tête `Contrat n°` seul sur toutes les pages sauf p.1 | 3 | forte |
| 7 | Sous-titre `Gestion libre` (mode de gestion) devant chaque tableau | 3 | forte, mais **valeur variable** si gestion pilotée (jamais observée ici) |
| 8 | Bandeau centré `SITUATION AU [date en clair majuscules]` | 2+3 | très forte |
| 9 | Conventions numériques (espace U+0020 milliers, virgule décimale, `€` postfixé espacé, 5 décimales de parts) | 3 | forte (sauf décimales du `%`, voir volatiles) |
| 10 | Bloc final 3 paires label:valeur + signature nominative + fonction | 3 | forte pour la structure |
| 11 | Invariants de contrôle (§f) | — | **vérifiés exactement 6/6** |

### Volatiles — à exclure du matching

| Élément | Amplitude observée |
|---|---|
| Nombre de pages | 2 → 4 |
| Affectation section ↔ n° de page | `SITUATION` en p.1 (2022, 2026) ou p.2 (2023-2025) ; clôture en p.2 ou p.4 ; p.4 mixte tableau+clôture en 2026.06 |
| Présence du bloc `PRIX DE REVIENT MOYEN` + ses 4 notes | absent 2022, présent 2023→2026 |
| Présence du bloc `DÉTAIL DES OPÉRATIONS` + son en-tête | absent 2022→2025, présent 2026.03 et 2026.06 |
| Fin de la phrase d'introduction | `depuis son origine` ↔ `depuis le dernier État de Situation` |
| Nombre de lignes supports | 1 → 15 → 10 |
| Nombre de groupes d'opérations | 0 → 2 → 3 |
| `CreationDate` PDF et date du courrier | ne portent pas l'information temporelle (réédition en lot) |
| Décimales du `%` | `100 %` vs `31,33 %` |
| Nom du signataire | stable ici (`Anaïd Chahinian` 6/6) mais déjà signalé volatile au §A.3 — ne pas ancrer |
| Libellés de colonnes à date embarquée | 3 occurrences, à matcher par pattern |
| Composition du portefeuille | 14 supports renouvelés à ~64 % entre 2025.12 et 2026.03 |

---

## (e) Périodicité et son token

**Résultat négatif, et il est net : le document ne dit pas sa propre périodicité.**

Le seul token de périodicité présent est un unique mot, `trimestriels`, dans une phrase **identique
aux six documents**, y compris les quatre annuels :

> `Nous vous rappelons que les relevés de situation trimestriels pourront être mis à votre`
> `disposition sur demande auprès de votre conseiller habituel.` (p.1, 6/6)

Cette phrase énonce une **offre commerciale**, pas la nature du document courant. Elle est
présente sur les relevés au 31/12 comme sur ceux au 31/03 et 30/06. Aucune occurrence de
« annuel », « mensuel », « semestriel » ni « périodicité » dans aucun des six documents (recherche
insensible à la casse sur l'intégralité du texte).

Il n'y a donc **pas d'équivalent Spirica du token Cardif** « *Cumul des opérations pour l'année* ».
L'aubaine §A.4 point 2 **ne se transpose pas ici**.

Deux substituts imparfaits, aucun suffisant seul :

1. **Le mois de la date d'arrêté** (`Relevé de Situation arrêté au 31/12/2022` / `au 31/03/2026`).
   Explicitement rejeté au §A.4 comme critère de périodicité : un trimestriel tombe aussi au 31/12.
   Ici, 31/03 et 30/06 excluent l'annuel, mais 31/12 n'exclut pas le trimestriel.
2. **La présence du bloc `DÉTAIL DES OPÉRATIONS`.** Corrélée à la périodicité sur ce corpus
   (0/4 sur les annuels, 2/2 sur les trimestriels) mais l'explication est un effet de fenêtre, pas
   un marqueur de périodicité — voir §g point 2. Un annuel avec fenêtre non vide l'afficherait.

**Recommandation** : ne pas ouvrir de variante de périodicité dans le store pour cet émetteur.
Traiter la périodicité comme un attribut **non lisible dans le document**, à dériver de la date
d'arrêté au niveau applicatif et non au niveau de la signature. C'est la position inverse de celle
retenue pour Cardif, et la différence doit être assumée profil par profil : le §A.4 point 2 est
valide comme aubaine opportuniste, pas comme règle générale.

---

## (f) Pièges de parsing : confirmés, disparus, nouveaux

### Confirmés

| Piège §B.3 | Statut sur la série |
|---|---|
| Sans `-layout`, le flux réordonne en-têtes et valeurs | **Confirmé, aggravé.** Sur 2026.06 sans `-layout` : les en-têtes sortent en colonne (`Date de` / `valeur` / `Nombre de parts` / `au 30/06/2026` / …) puis les valeurs isolées (`116,57 €`, `213,64128`, `24 904,16 €`, `31,33 %`) **sans le libellé du support**, celui-ci sortant ailleurs dans le flux. L'extraction par coordonnées reste impérative. |
| Libellés de colonnes à date embarquée | **Confirmé.** 3 occurrences : `Nombre de parts au [date]`, `Valeur atteinte au [date] en euros`, et depuis 2023 `Prix de revient moyen (PRM) au [date] en euros*`. |
| Deux dates éloignées : arrêté vs édition | **Confirmé et amplifié à +3 ans 7 mois** (arrêté 31/12/2022, édition 24/07/2026). Seul `Relevé de Situation arrêté au` / `SITUATION AU` fait foi. |
| Cellule `Nombre de parts` vide pour le fonds euro | **Confirmé 6/6.** La ligne `Fonds Euro Nouvelle Génération` n'a ni valeur de part ni nombre de parts : deux cellules vides au milieu de la ligne. |
| `Valeur atteinte` = `Valeur de rachat` sans que l'égalité soit garantie | **Confirmé 6/6** : égalité exacte aux six dates. Ne pas en faire une règle pour autant. |
| Civilité variable modifie les accords | Non testable ici (`Mademoiselle` 6/6). Piège reporté, pas infirmé. |
| Bloc conseiller en 2 colonnes juxtaposées | **Confirmé 6/6.** Ligne mêlant `Votre conseiller :`, la raison sociale sur 3 lignes, `Adresse :`, `Téléphone :`. |
| Mono-support / profil valide 0..N lignes | **Confirmé nécessaire** : 1 ligne en 2022, 15 en 2024. |
| N° contrat sous 2 formats | **Confirmé 6/6** : `Votre numéro de contrat : 443909428` en p.1, `Contrat n° 443909428` en en-tête des pages suivantes. |

### Disparus

| Piège §B.3 | Ce qui a changé |
|---|---|
| « Pas d'ISIN — identification supports par libellé seul → référentiel externe nom→ISIN » | **Levé dès 2023.12.** L'ISIN est présent, **entre parenthèses à la fin du libellé du support** : `Morgan Stanley Investment Funds - Global Opportunity Fund A (LU0552385295)`, `Renaissance Europe (FR0000295230)`. Vérifié dans les trois tableaux (`SITUATION`, `PRM`, `DÉTAIL DES OPÉRATIONS`) de 2023.12 à 2026.06. Le référentiel externe n'est plus nécessaire. **Deux réserves** : (i) l'ISIN n'était pas *observable* en 2022 parce que le seul support était le fonds euro, qui n'a pas d'ISIN — le piège pouvait donc être une conclusion tirée d'un cas dégénéré plutôt qu'une propriété du gabarit ; (ii) la ligne fonds euro reste sans ISIN à toutes les dates, l'ISIN est donc **optionnel par ligne**. |

### Nouveaux

1. **Les opérations sont cumulatives depuis le dernier État de Situation, pas depuis le relevé
   précédent.** Le relevé 2026.06 (p.3) réimprime **à l'identique** l'arbitrage du 06/03/2026
   (montant brut 48 247,67 €) et les frais du 20/03/2026 déjà présents dans 2026.03 (p.3), puis
   ajoute en p.4 les frais du 19/06/2026. Concaténer deux relevés trimestriels **double-compte**
   toute la période antérieure. C'est le piège le plus coûteux du lot.
2. **`Montant brut` d'un groupe d'opérations ≠ somme des montants nets des lignes du groupe.**
   Sur l'arbitrage du 06/03/2026 : `Montant brut : 48 247,67 €` = exactement la somme des débits
   (−48 247,67 €), alors que la somme des crédits vaut 48 151,17 € et la somme algébrique des
   14 lignes **−96,50 €** (frais d'arbitrage non détaillés en ligne). Ne jamais recalculer le
   montant brut comme Σ des nets, ni supposer un arbitrage à somme nulle.
3. **La césure du libellé de support diffère d'un tableau à l'autre dans le même document.**
   `Fidelity Funds - Chinan Consumer Fund A-Acc-EUR (LU0594300096)` occupe **2 lignes** dans le
   tableau `SITUATION` (nom, puis `(LU0594300096)` seul sur la 2ᵉ ligne) et **1 seule ligne** dans
   le tableau `PRIX DE REVIENT MOYEN` — les colonnes n'ont pas la même largeur (`Support` à
   xMin=124,00 dans `SITUATION`, 139,50 dans `PRM` et `OPÉRATIONS`). Le recollement des lignes
   continuées doit être paramétré **par tableau**, pas globalement.
4. **Un `%` peut être imprimé sans décimales** : `100 %` (2022.12, p.1). Parser tolérant sur les
   décimales, y compris pour le contrôle Σ% = 100.
5. **Une page peut mélanger une continuation de tableau et le bloc de clôture** (2026.06, p.4 :
   3ᵉ groupe d'opérations puis `Toujours attentifs au suivi de votre dossier…`). Aucun bloc ne
   peut être localisé par un numéro de page, ni supposé seul sur sa page.
6. **La ligne fonds euro porte l'arrêté comme `Date de valeur` et une valeur figée entre deux
   arrêtés annuels.** `Fonds Euro Nouvelle Génération` vaut `102,89 €` au 31/12/2025, au
   31/03/2026 **et** au 30/06/2026, avec des `Date de valeur` respectives 31/12/2025, 31/03/2026,
   30/06/2026. Trois valeurs identiques à trois dates différentes ne sont pas un doublon
   d'extraction ni une erreur : les intérêts sont crédités annuellement.
7. **Le tri des tableaux n'est pas le même d'un tableau à l'autre** : `SITUATION` est trié par
   valeur atteinte décroissante, `PRM` par +/- value en % décroissante. L'ordre des lignes n'est
   donc pas un appariement possible entre les deux tableaux ; il faut apparier par libellé/ISIN.
8. **Les ancres du bloc PRM et du bloc opérations sont des faux positifs de signature** : leur
   présence dépend du portefeuille et de la période. Voir §c.

### Invariants de contrôle — vérifiés

| Invariant | Résultat |
|---|---|
| Σ des `Valeur atteinte` des lignes = `Montant de la valeur atteinte au [date]` | **exact au centime, 6/6** (écart 0,00 € sur les six) |
| Σ colonne `%` = 100 | **exact, 6/6** (100,00 sur les six) |
| `Valeur de rachat*` = `Montant de la valeur atteinte` | vrai 6/6 — à contrôler, non à supposer |
| `Montant brut` d'un groupe = Σ des débits du groupe | vrai sur l'arbitrage du 06/03/2026 ; **1 seule observation**, à ne pas ériger en invariant |

Les deux premiers confirment l'invariant du §B.3 et sont exploitables pour l'auto-validation
d'extraction sans intervention humaine.

---

## (g) Ce que je n'ai pas pu établir

1. **La version réelle du générateur en 2022, 2023, 2024, 2025.** Les six PDF ont été réédités le
   même jour (24/07/2026, en 4 minutes) par le même binaire. La couche 1 de ce corpus décrit l'état
   du générateur **au 24/07/2026**, projeté sur six arrêtés. Toute dérive de générateur survenue
   entre 2022 et 2026 est **structurellement invisible** ici. Il faudrait des PDF téléchargés
   *à l'époque* de chaque arrêté pour trancher. Corollaire méthodologique important : sur un
   extranet qui régénère à la demande, **la dérive de gabarit dans le temps ne s'observe pas sur
   des rééditions** — ce qu'on observe est la dérive du *contenu*, pas celle du modèle. La question
   posée ne peut donc recevoir de réponse pleine sur ce corpus, et la réponse « un seul gabarit »
   du §c doit se lire : *un seul gabarit de rendu au 24/07/2026, capable de restituer six arrêtés
   sans divergence de signature*.
2. **Pourquoi `DÉTAIL DES OPÉRATIONS` est absent des quatre relevés annuels.** Deux hypothèses
   restent ouvertes, et je ne peux pas les séparer :
   (i) fenêtre vide — l'État de Situation réglementaire étant arrêté au 31/12, un relevé au 31/12
   n'a rien à afficher ; (ii) le bloc n'est réellement émis que sur les relevés intermédiaires.
   Un **contre-indice** à l'hypothèse (i) : le relevé 2022.12 annonce « *l'ensemble des opérations
   intervenues sur votre contrat depuis son origine* » alors que le contrat, effectif le
   14/12/2022, avait nécessairement reçu son versement initial (~70 000 €) avant le 31/12/2022 —
   et aucun bloc n'est imprimé. Soit le versement initial n'est pas une « opération » au sens de
   cette section, soit le bloc n'existait pas dans le rendu de 2022. Trancher demande un relevé
   annuel de ce même contrat avec des opérations dans la fenêtre, ou un relevé trimestriel sans
   opération.
3. **Le comportement du gabarit hors gestion libre.** `Gestion libre` est le seul mode observé
   6/6. Le §B.3 supposait le profil valide en gestion pilotée ; ce corpus ne l'infirme ni ne le
   confirme, et l'existence éventuelle d'un bandeau de mode différent, d'un sous-total par mode ou
   d'une répétition du tableau reste non testée.
4. **La sensibilité aux accords de civilité.** `Mademoiselle` 6/6 : la normalisation avant ancrage
   reste une précaution théorique sur ce corpus.
5. **Le seuil de tolérance du matcher.** Je constate que le noyau est à 100 % et que les blocs
   optionnels pèsent 0 à 5 ancres sur ~20. Je n'ai pas les moyens de fixer ici le seuil de score
   à partir duquel un document manquant N ancres optionnelles doit encore apparier : cela dépend
   du schéma de pondération du store, hors périmètre de cette étude.
6. **La généralisation au réplicat Pollux et aux autres contrats Spirica.** Étude volontairement
   limitée à la série Cerise, contrat unique, pour isoler l'axe temporel. Les six fichiers
   `Pollux` de mêmes dates sont présents dans le corpus et permettraient de croiser axe temporel
   et axe réplicat ; non traités ici.
