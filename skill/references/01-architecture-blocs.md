# Architecture des blocs du reporting

> Description détaillée des 5 blocs (+ Hero + Footer) qui composent un reporting Rhétorès,
> nomenclature "widget" pour parler de leurs composants, et spécification figée du Hero.
> Référencé depuis le SKILL.md.

---

## Structure obligatoire des blocs

Un reporting Rhétorès suit toujours cette structure, dans cet ordre :

```
1. Hero / Chiffres clés       — Actif, Dette, Actif net, Performance YTD
2. Bloc 00 — Contexte de marché — Macro, faits marquants, benchmark indices
3. Bloc 01 — Étude de la performance — Widgets de performance (à spécifier)
4. Bloc 02 — Répartition       — Tableau global + mini-donuts + cards entités
5. Bloc 03 — Tableau exhaustif — Détail ligne à ligne par entité
6. Footer
```

**Logique d'ordre** : synthèse chiffrée d'abord (Hero), puis contexte qui explique les
mouvements (Bloc 00), puis lecture de la performance du portefeuille (Bloc 01), puis
décomposition et allocation graphique du patrimoine (Bloc 02), puis détail ligne par ligne
(Bloc 03). La performance vient avant la répartition : on répond d'abord à "comment ça a
marché ?" avant "de quoi c'est composé ?". Convention alignée sur les reportings UBS /
Pictet / EdR.

---

## Nomenclature widget — vocabulaire à utiliser

Pour éviter toute ambiguïté dans les échanges et le code :

| Niveau | Terme | Définition | Exemple |
|---|---|---|---|
| 1 | **Reporting** | Le document HTML complet | `consolide_HG_v15.html` |
| 2 | **Bloc** | Une grande partie numérotée du reporting | Bloc 00, Bloc 01, Bloc 02, Bloc 03 |
| 3 | **Widget** | Un sous-élément autonome à l'intérieur d'un bloc | Tableau global, card entité, donut |
| 4 | **Élément** | Un composant à l'intérieur d'un widget | Ligne du tableau, part de donut |
| 5 | **Ligne / Colonne / Cellule** | Vocabulaire HTML standard | "ligne Financier coté", "colonne Valo 30/04" |

**Exemples d'usage correct** :
- « Le **Bloc 02** contient 3 **widgets** : le tableau global, la ligne de 4 mini-donuts, les 3 cards entités »
- « Modifier le **widget** cards entités — ajouter une 4e card pour SAS XYZ »
- « Dans le **widget** tableau global, recalculer la **ligne** Financier coté »

**Convention de référence** : Hero, Footer et Blocs 00-03 sont **des blocs** (niveau 2).
Tout ce qu'ils contiennent est un **widget** (niveau 3).

---

## Hero — Chiffres clés (SPÉCIFICATION FIGÉE)

Le Hero est la première chose que le client voit. Sa spécification est figée et **ne doit pas
varier d'un reporting à l'autre**, quel que soit le client ou le CGP qui produit le reporting.

### Structure visuelle

```
┌──────────────────────────────────────────────────────────────────────────┐
│  [Nom client]                              [31 mois 2026 · T1 2026]      │
│  Family office - Reporting                                               │
│  ──────────────────────────────────────────────────────────────────────  │
│                                                                          │
│   Actif          Dette          Actif net     Performance YTD            │
│   X €            X €            X €           + X €                      │
│                  (rouge)                      + X,XX %                   │
│                                               base : X €                 │
└──────────────────────────────────────────────────────────────────────────┘
```

### Composition

**Bandeau navy plein largeur** avec deux zones :

**Zone supérieure (header du Hero)** :
- À gauche : nom du client en grand (format `Prénom + Initiale.`, ex: "Marc D.")
  + sous-titre exact : `Family office - Reporting`
- À droite : date et période, format `31 mars 2026 · T1 2026` (sans préfixe "Au")

**Zone inférieure (KPI strip)** : 4 KPIs côte à côte dans l'ordre suivant :

| # | Libellé | Contenu | Couleur |
|---|---|---|---|
| 1 | `Actif` | Actif brut total (Liq + Immo + Fin coté + Non coté) | Neutre |
| 2 | `Dette` | Total des dettes, affiché **sans signe** | **Rouge** |
| 3 | `Actif net` | Actif − Dette | Neutre |
| 4 | `Performance YTD` | KPI fusionné sur **3 lignes** (voir détail ci-dessous) | **Vert si positif, rouge si négatif** (sur les 2 premières lignes uniquement) |

### Détail du KPI Performance YTD (composition à 3 lignes)

Ce KPI fusionne plusieurs informations dans une seule case :

```
Performance YTD
+ 70 000 €          ← Ligne 1 : Gain € YTD en grand (couleur perf)
+ 2,04 %            ← Ligne 2 : Gain % YTD en dessous (couleur perf)
base : 3 750 000 €  ← Ligne 3 : Base financière de calcul en petit (couleur neutre)
```

**Base financière** = **Financier coté + Financier non coté uniquement**
- Exclut : Liquidités, Immobilier, Dettes
- Affichée pour rendre explicite le périmètre de calcul de la performance

### Règles strictes du Hero

- Les **holdings n'apparaissent jamais dans le Hero** : seule la PP figure en titre
- Le sous-titre est **figé** : `Family office - Reporting` (libellé exact, casse comprise)
- L'ordre des 4 KPIs est **figé** : Actif → Dette → Actif net → Performance YTD
- La couleur **rouge sur Dette** est appliquée même si la valeur est neutre (la sémantique commande la couleur)
- La couleur **verte/rouge sur Performance YTD** s'applique aux lignes 1 et 2 (€ et %), pas à la base
- Aucun signe `-` ou `+` n'est affiché sur le KPI Dette : le libellé "Dette" suffit à indiquer la nature passive

### Formalisme du Hero

→ **Référence obligatoire** : `references/09-formalisme.md` pour le format des libellés,
des montants, des pourcentages, des dates et des couleurs. Toutes les règles transversales
y sont consignées.

---

## Bloc 00 — Contexte de marché (SPÉCIFICATION FIGÉE)

Le Bloc 00 plante le décor macroéconomique de la période. Il vient juste après le Hero,
avant la lecture de la performance du portefeuille (Bloc 01). Il répond à la question :
"dans quel environnement de marché s'est déroulé ce trimestre ?".

### Structure visuelle

```
┌──────────────────────────────────────────────────────────────────────────┐
│  00   Contexte de marché                                                 │
│  ──────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  [Texte macro narratif — 5 paragraphes thématiques, 600-750 mots]        │
│                                                                          │
│  ┌────────────────────────────┐    ┌────────────────────────────┐        │
│  │  T1-26 - Faits marquants   │    │  T1-26 - Perf. des indices │        │
│  │  • bullet 1                │    │  S&P 500             +X,XX%│        │
│  │  • bullet 2                │    │  Nasdaq Composite    +X,XX%│        │
│  │  • bullet 3                │    │  DJ Euro Stoxx 50    +X,XX%│        │
│  │  • bullet 4                │    │  CAC 40              +X,XX%│        │
│  │  • bullet 5                │    │  Once d'or           +X,XX%│        │
│  │                            │    │  Pétrole Brent       +X,XX%│        │
│  │                            │    │  EUR / USD           +X,XX%│        │
│  │                            │    │  Bitcoin             +X,XX%│        │
│  └────────────────────────────┘    └────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────────┘
```

### Composition — 3 widgets

| Ordre | Widget | Position |
|---|---|---|
| 1 | Texte macro narratif | Pleine largeur, au-dessus |
| 2 | Card `T1-26 - Faits marquants` | Demi-largeur gauche |
| 3 | Card `T1-26 - Performance des indices` | Demi-largeur droite |

### Titre du bloc

- Format : numéro `00` en gold, suivi du libellé `Contexte de marché`
- Libellé figé (ne pas modifier) : `Contexte de marché`

---

### Widget 1 — Texte macro narratif

#### Caractéristiques générales

- **Longueur cible** : 600-750 mots selon la richesse de l'actualité du trimestre
- **Voix narrative** : pas de "nous", pas de "je", ton institutionnel impersonnel
- **Engagement** : maîtrisé. Décrire principalement, prendre position avec mesure quand pertinent (notamment dans le §5)
- **Précision chiffrée** : chiffres clés pour illustrer (taux directeurs, niveaux d'indices, spreads), sans abus. Un chiffre par idée, pas un catalogue de statistiques.

#### Structure thématique en 5 paragraphes

Cette structure est **standard** et doit être respectée à chaque reporting. Les thèmes peuvent
être ajustés selon les thématiques fortes de la période, mais la trame en 5 § est conservée.

| § | Thème | Contenu attendu |
|---|---|---|
| **§1** | **La question dominante du trimestre** | Une seule idée centrale qui a structuré la période (pas un catalogue). Exemple : "Le trimestre a été dominé par la divergence des cycles monétaires entre la Fed et la BCE." |
| **§2** | **Politiques monétaires et inflation** | Lecture combinée Fed / BCE / BoJ / BoE. Distinction inflation core vs headline. Marché du travail US (variable clé Fed). Présenter une dialectique des banques centrales, pas une liste pays par pays. |
| **§3** | **Régime de marché et rotation** | Risk-on vs risk-off. Rotation sectorielle (cycliques/défensives, value/growth). Comportement des actions (Europe vs US, large vs small). Comportement des taux (10Y US/Bund, forme de la courbe). Devises majeures (EUR/USD, USD/JPY). |
| **§4** | **Matières premières et actifs alternatifs** | Or (rôle de refuge), pétrole, métaux industriels. Crypto (Bitcoin comme proxy d'appétit pour le risque). |
| **§5** | **Le thème ou la tension à suivre** | Un point de vigilance ou un thème structurel émergent. Exemples : "désynchronisation des cycles BCE/Fed", "concentration sectorielle US/AI", "fragmentation géopolitique et chaînes d'approvisionnement". C'est le paragraphe où la maison engage le plus son regard. |

#### Logique de cohérence avec la card "Indices"

Les §3 et §4 du texte couvrent **précisément les classes d'actifs** présentes dans la card
des indices (actions développées, oblig via taux, change, or, pétrole, crypto). Le texte
donne le récit, la card donne les chiffres. **Pas de redondance** : ne pas réciter dans le
texte les chiffres déjà dans la card.

#### Sources de données pour la rédaction du texte macro

La rédaction du texte macro s'appuie **exclusivement sur des sources web officielles et de
qualité institutionnelle**, utilisées par les analystes financiers seniors :

- **Banques centrales** : Federal Reserve (federalreserve.gov), BCE (ecb.europa.eu), BoJ, BoE
- **Institutions** : FMI (imf.org), OCDE (oecd.org), Banque Mondiale
- **Statistiques officielles** : BLS (US labor), Eurostat, INSEE
- **Notes de recherche des grandes banques** : Goldman Sachs Research, JPM Markets, BlackRock Investment Institute, Pictet WM, Lombard Odier, Carmignac, Amundi Research, Allianz Research
- **Données de marché** : Bloomberg, Reuters, FT Markets, WSJ Markets

**À éviter** : agrégateurs grand public, blogs, contenus non sourcés.

> ⚠ **Distinction importante** : les sources listées ci-dessus servent à **alimenter le récit
> macroéconomique du texte** (politiques monétaires, contexte géopolitique, dynamiques de
> marché, thèmes structurels). Elles **ne sont pas la source des chiffres affichés dans la
> card "Performance des indices"** — voir Widget 3 ci-dessous pour la règle de sourcing des
> 8 indices (document UBS + source officielle pour Bitcoin).

#### Auteur

Claude rédige le texte macro. Le CGP (Tristan) valide et corrige avant livraison.

---

### Widget 2 — Card `T1-26 - Faits marquants`

#### Caractéristiques

- **Libellé exact figé** : `T1-26 - Faits marquants` (utilise la forme courte de période, voir `references/09-formalisme.md` § 4)
- **Nombre de bullets** : 5 cible
- **Format des bullets** : phrases rédigées synthétiques, environ 15 mots par bullet
- **Style** : phrases nominales ou verbales complètes, pas de télégramme

#### Cohérence avec le texte macro

La sélection des 5 faits marquants est **libre** : Claude choisit trimestre par trimestre
selon la richesse de l'actualité. Ils peuvent reprendre certaines idées clés des § du texte
macro (cohérence forte) ou des micro-événements datés complémentaires (cohérence
narrative). Pas de règle rigide — juger au cas par cas pour le meilleur impact lecteur.

#### Exemples de bullets bien calibrés

- "La BCE poursuit son cycle d'assouplissement avec une baisse de 25 pb portant le taux dépôt à 2,25%."
- "L'or atteint un plus haut historique à 2 480 USD/once, porté par les achats des banques centrales."
- "Le S&P 500 corrige de -1,8% YTD, pénalisé par les valeurs technologiques et les inquiétudes tarifaires."

---

### Widget 3 — Card `T1-26 - Performance des indices`

#### Caractéristiques

- **Libellé exact figé** : `T1-26 - Performance des indices`
- **Colonnes** : 2 colonnes — nom de l'indice + performance YTD uniquement
- **Pas de colonne supplémentaire** (1 an, 3 ans, etc.)

#### Liste figée des 8 indices (à afficher systématiquement, dans cet ordre exact)

| # | Libellé exact à afficher | Source du chiffre |
|---|---|---|
| 1 | `S&P 500` | Document UBS de situation trimestrielle |
| 2 | `Nasdaq Composite` | Document UBS de situation trimestrielle |
| 3 | `DJ Euro Stoxx 50` | Document UBS de situation trimestrielle |
| 4 | `CAC 40` | Document UBS de situation trimestrielle |
| 5 | `Once d'or (USD / once)` | Document UBS de situation trimestrielle |
| 6 | `Pétrole USD Brent` | Document UBS de situation trimestrielle |
| 7 | `EUR / USD` | Document UBS de situation trimestrielle |
| 8 | `Bitcoin` | Source officielle internet (CoinMarketCap, CoinGecko, ou équivalent) |

#### Sources des chiffres — Règle stricte

**Pour les 7 premiers indices** : les performances YTD sont **exclusivement extraites du
document de situation UBS** que Tristan fournit à chaque trimestre. Claude ne fait **aucune
recherche web** pour ces chiffres. Si le document UBS n'est pas fourni ou ne contient pas
un des 7 indices, Claude doit le signaler à Tristan plutôt que de chercher ailleurs.

**Pour le Bitcoin** : le chiffre est recherché par Claude sur une source officielle internet
(CoinMarketCap, CoinGecko, ou équivalent d'autorité reconnue). Le Bitcoin n'est pas couvert
par le document UBS, c'est la seule exception.

**Pourquoi cette règle** : la source UBS garantit la **cohérence et l'opposabilité** des
chiffres face au client (même source pour tous les indices, pas de divergence entre sites web).
Le Bitcoin fait exception car non couvert par l'univers UBS.

#### Règle de lecture du tableau UBS — Cas Or / Pétrole / Devises

Le document UBS de situation présente le tableau "Niveaux et évolution des grands indices et
ratios" en deux blocs distincts qui se lisent différemment :

**Bloc 1 — Indices Actions** (MSCI World, DJ Stoxx 50, DJ Euro Stoxx 50, CAC 40, FTSE 100,
DAX 30, Dow Jones, S&P 500, Nasdaq Composite, Nikkei 225) :
- Le tableau donne directement les **pourcentages de variation** (% Var. semaine / 1 mois / 3 mois / 6 mois / **YTD 31/12/2025**)
- La colonne "Niveau" indique le niveau au 31/03/2026
- **YTD lu directement** dans la colonne "YTD 31/12/2025" (ex: S&P 500 → `-4,63%`)

**Bloc 2 — Marché de taux + Devises + Autres** (Taux interbancaire, Bund 10 ans, Treasury 10 ans,
EUR/USD, USD/JPY, Or USD/once, Pétrole USD/Brent) :
- Le tableau donne des **niveaux**, pas des pourcentages (note explicite UBS : *"Les valeurs
  sont données en niveaux et non pas en performances"*)
- Les 5 colonnes (Aujourd'hui / 1 semaine / 1 mois / 3 mois / YTD 31/12/2025) donnent les
  niveaux à chacune de ces dates de référence
- **YTD à calculer** : `(Niveau Aujourd'hui − Niveau 31/12/2025) / Niveau 31/12/2025 × 100`

**Exemples de calcul (T1 2026)** :
- Or USD/once : Aujourd'hui 4 638,27 vs 31/12/2025 4 322,02 → YTD `+7,32%`
- Pétrole USD/Brent : Aujourd'hui 125,62 vs 31/12/2025 62,45 → YTD `+101,15%`
- EUR/USD : Aujourd'hui 1,1541 vs 31/12/2025 1,1736 → YTD `-1,66%`

**Mapping des libellés UBS → Libellés figés du reporting** :

| Libellé figé du reporting | Mapping vers libellé UBS |
|---|---|
| `S&P 500` | S&P 500 (Bloc Indices Actions) |
| `Nasdaq Composite` | Nasdaq Composite (Bloc Indices Actions) |
| `DJ Euro Stoxx 50` | DJ Euro Stoxx 50 (Bloc Indices Actions) |
| `CAC 40` | CAC 40 (Bloc Indices Actions) |
| `Once d'or (USD / once)` | Or (USD/once) — Bloc Autres, YTD à calculer |
| `Pétrole USD Brent` | Pétrole (USD/Brent) — Bloc Autres, YTD à calculer |
| `EUR / USD` | EUR/USD — Bloc Devises, YTD à calculer |

**Pourquoi cette précision** : sans cette règle de lecture, un utilisateur peut confondre la
colonne "YTD 31/12/2025" (qui pour Or/Pétrole/Devises donne un **niveau de référence**, pas un
pourcentage) avec un pourcentage de variation déjà calculé. L'erreur silencieuse serait
massive : afficher 4322,02% au lieu de +7,32% pour l'Or, par exemple.

#### Règles strictes (suite)

- La liste est **fermée** : aucun indice n'est ajouté ou retiré, même si l'actualité du trimestre en justifierait un autre
- L'ordre est **figé** (Actions US → Actions Europe → MP → Change → Crypto)
- Les libellés sont **exacts** (espaces, majuscules, ponctuation conformes au tableau ci-dessus)
- Le format des performances suit `references/09-formalisme.md` § 3 (signe explicite, 2 décimales, pas d'espace avant `%`)
- Couleur des performances : vert si positif, rouge si négatif (`references/09-formalisme.md` § 5)

---

### Mise en page du Bloc 00

- Texte macro en pleine largeur, au-dessus
- En dessous, grille 2 colonnes : card Faits marquants à gauche, card Performance des indices à droite
- Cohérence visuelle des deux cards : même hauteur, même style de bordure, même typographie

---

## Bloc 01 — Étude de la performance

> ⚠ Spécification à définir en collaboration avec Tristan.
> Les widgets de ce bloc seront détaillés ultérieurement.
> Logique : ce bloc répond à "comment le portefeuille a-t-il performé sur la période ?",
> avant la lecture de la composition patrimoniale (Bloc 02).

---

## Bloc 02 — Répartition patrimoniale

3 widgets dans cet ordre :

### 1. Tableau global de synthèse

Tableau récapitulatif avec une ligne par catégorie d'actif :
- Liquidités, Immobilier, Financier coté, Non coté, Dettes
- Colonnes : Brut | Dettes | Net | % du net

### 2. Ligne de 4 mini-donuts

4 donuts compacts côte à côte :
1. Classes d'actifs (12 classes Rhétorès)
2. Géographie (sur Actions + PE uniquement)
3. Dépositaires (banques/assureurs)
4. Enveloppes (AV, Capi, CTO, Direct, etc.)

### 3. Cards par entité (struct-card)

Une card par entité (PP + Holdings). **Chaque card respecte une structure de 6 lignes fixes** dans cet ordre :

```
1. Liquidités          [montant €]
2. Immobilier          [montant €]
3. Financier coté      [montant €]
4. Financier non coté  [montant €]
5. Dettes              [montant € en rouge]
6. Total [Entité]      [montant € en gras]
```

**Règles strictes** :
- Les 6 lignes sont **toujours présentes** dans cet ordre, même si une catégorie est vide pour l'entité (afficher `—`)
- La ligne **Dettes** ne se ventile **jamais** entre les autres catégories — c'est une ligne globale, en rouge
- Les **valeurs sont uniformes** : pas de muted sur les libellés, pas de muted sur les zéros (afficher `—` plutôt que `0 €`)
- Le label de la ligne 6 reprend le nom exact de l'entité : "Total Hervé G.", "Total SAS AX", etc.

**Pourquoi cette rigidité** : la cohérence visuelle entre les cards permet au client de comparer instantanément la composition patrimoniale des différentes entités. Si une card a 4 lignes et l'autre 5, l'œil ne sait plus comparer.

---

## Bloc 03 — Tableau patrimonial exhaustif

Widget unique : le tableau exhaustif, détail ligne par ligne par entité.

→ Architecture détaillée : `references/03-tableau-exhaustif.md`

---

## Footer

Mention discrète : nom du cabinet, date de génération, version du reporting.
Format : `Rhétorès Finance — Reporting généré le DD/MM/YYYY — V[X]`
