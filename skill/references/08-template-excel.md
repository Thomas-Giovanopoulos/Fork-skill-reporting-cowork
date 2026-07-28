# Template Excel de collecte des données

> Source unique de vérité pour les valeurs et caractéristiques d'un reporting patrimonial.
> Référencé depuis le SKILL.md (workflow de production étape 1).

---

### Fichier de référence

Un template Excel vierge et uniformisé est inclus dans le skill, à l'emplacement :

```
references/Reporting_data_template.xlsx
```

C'est la **base systématique** pour démarrer un nouveau reporting patrimonial, quel que soit le client. Le template contient 18 onglets pré-structurés couvrant toutes les catégories d'actifs d'un patrimoine consolidé.

### Chaîne de production des données — Source unique

Le fichier Excel source est la **source unique de vérité** pour la production du reporting HTML. Voici la chaîne complète :

```
┌──────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
│   SOURCES AMONT          │      │   FICHIER EXCEL SOURCE   │      │   REPORTING HTML         │
│   (relevés dépositaires) │  →   │  Reporting_[Client].xlsx │  →   │  consolide_[Client].html │
│                          │      │                          │      │                          │
│ • Relevés UBS Wealins    │      │ Source UNIQUE pour       │      │ Bloc 00 — Contexte       │
│ • Relevés EdR (CTO,AV)   │      │ toutes les valeurs et    │      │ Bloc 02 — Répartition    │
│ • Relevés Indosuez       │      │ caractéristiques :       │      │ Bloc 03 — Tableau exh.   │
│ • Relevés CA (Prédica,   │      │  - Valeur 01/01          │      │                          │
│   CNP, Generali)         │      │  - Valeur au [Date]      │      │ Produit par Claude       │
│ • Relevés Tilvest        │      │  - Nominal investi       │      │ à partir du fichier      │
│ • Relevés Lombard/UBS    │      │  - Date d'investissement │      │ Excel uniquement         │
│ • Relevés Allianz        │      │  - Flux (Mouvements)     │      │                          │
│ • Actes notariés         │      │  - Immo, dettes, PE      │      │                          │
│ • Reportings GP (PE)     │      │                          │      │                          │
└──────────────────────────┘      └──────────────────────────┘      └──────────────────────────┘
         CGP                              CGP                              Claude
   (collecte manuelle)              (fichier de référence)         (production automatique)
```

**Responsabilités** :

- Le **CGP** (Tristan ou tout autre CGP utilisateur du skill) est responsable de la collecte des données depuis les relevés dépositaires et du remplissage / fiabilisation du fichier Excel source. C'est lui le garant de l'exactitude des données.

- **Claude** ne consulte pas directement les relevés dépositaires pour produire le reporting HTML. Sa source unique est le fichier Excel source. Il met en forme, calcule les sous-totaux et la consolidation, et génère le HTML conforme à la charte FO Rhétorès.

**Exception unique — Classification fine ligne par ligne** : pour le travail de classification d'un fonds en classe Rhétorès / géographie (méthode M1-M5 de la section 3.3), Claude peut consulter les relevés des dépositaires pour identifier les positions individuelles via leur ISIN et leur sous-jacent. C'est un travail distinct de la collecte des valeurs.

**Bénéfices de cette architecture** :
- Point de vérité unique (le fichier Excel) — toute correction se fait à un seul endroit
- Séparation claire des responsabilités (collecte ≠ production)
- Audit trail : le fichier Excel est un snapshot daté et opposable
- Démocratisation facilitée : un autre CGP peut produire son reporting sans connaître les spécificités de chaque dépositaire
- Reproductibilité : à partir du même fichier Excel, le HTML est toujours identique

### Convention de démarrage — Première action obligatoire pour tout nouveau reporting

**Avant toute autre action**, lors du démarrage d'un reporting pour un nouveau client (ou la première fois pour un client existant), Claude doit **systématiquement** :

1. **Demander combien d'entités** composent le patrimoine du client (typiquement 1 PP + N holdings)
2. **Demander le nom de chaque entité** en distinguant clairement :
   - La **Personne Physique (PP)** : généralement formatée en `Prénom + Initiale nom` (ex : "Hervé G.", "Sophie L.")
   - Les **Holdings** : nom social complet ou abréviation usuelle (ex : "SAS AX", "SCI Patrimoine", "Holding LG")
3. **Adapter le template** :
   - Renommer les onglets : `Liq — PP` → `Liq — [Nom PP]`, `Liq — Holding 1` → `Liq — [Nom Holding 1]`, etc.
   - Renommer les titres A1 de chaque onglet en conséquence : `LIQUIDITÉS — PP` → `LIQUIDITÉS — [Nom PP]`
   - **Ajouter des onglets supplémentaires** si le client a 3+ holdings : dupliquer la série complète (Liq + Immo + Fin coté + Mouvements + Non coté + Dettes) pour chaque nouvelle holding
   - **Supprimer des onglets** si le client a moins d'entités : supprimer la série complète d'une entité non utilisée
4. **Confirmer la nomenclature avec l'utilisateur** avant de procéder au remplissage

**Exemple de démarrage type** :
> Utilisateur : "Je veux démarrer un reporting pour un nouveau client."
> Claude : "Bien noté. Avant de commencer, quelques précisions sur la structure patrimoniale :
> - Combien d'entités composent le patrimoine ? (typiquement 1 personne physique + N sociétés / holdings)
> - Quel est le nom de la personne physique (format : prénom + initiale du nom) ?
> - Quel(s) est/sont le(s) nom(s) des holdings / sociétés ?"

Cette convention garantit que le template est personnalisé dès le départ et évite toute confusion ultérieure entre les entités générique du template et les entités réelles du client.

### Quand utiliser ce template

- Au démarrage d'un nouveau reporting client (premier reporting ou nouveau cycle)
- À chaque nouvelle période de reporting (trimestre, semestre, année)
- Quand on doit collecter ou mettre à jour les valeurs d'un patrimoine consolidé

**À ne pas utiliser** : pour des analyses ponctuelles sur un seul contrat, des simulations rapides, ou des extractions ciblées. Le template est calibré pour un reporting complet multi-entités.

### Structure du template

**21 onglets organisés en 7 catégories × 3 entités** :

| Catégorie | Onglets | Usage |
|---|---|---|
| Liquidités | `Liq — PP`, `Liq — Holding 1`, `Liq — Holding 2` | Comptes courants, livrets, comptes titres ordinaires |
| Immobilier | `Immo — PP`, `Immo — Holding 1`, `Immo — Holding 2` | Biens immobiliers (RP, RS, investissement) |
| Financier coté | `Fin coté — PP`, `Fin coté — Holding 1`, `Fin coté — Holding 2` | Contrats AV, capi, CTO (multi-poches détaillé) |
| Lignes | `Lignes — PP`, `Lignes — Holding 1`, `Lignes — Holding 2` | Détail par actif de chaque contrat coté (ISIN, classe, géo, perf) |
| Mouvements | `Mouvements — PP`, `Mouvements — Holding 1`, `Mouvements — Holding 2` | Versements, retraits avec dates précises (Modified Dietz) |
| Non coté | `Non coté — PP`, `Non coté — Holding 1`, `Non coté — Holding 2` | Private Equity, dette privée, immo non coté, infrastructures |
| NC Flux | `NC Flux — PP`, `NC Flux — Holding 1`, `NC Flux — Holding 2` | Flux datés du non coté : appels, distributions, valorisations + échéancier prévisionnel |
| Dettes | `Dettes — PP`, `Dettes — Holding 1`, `Dettes — Holding 2` | Prêts, in fine, amortissables |

**Convention "PP + 2 Holdings"** : structure de base à adapter selon le client.
- **PP** = Personne Physique (le client lui-même)
- **Holding 1 / Holding 2** = sociétés du client (SAS, SARL, SCI…)

Pour un client à 1 seule entité : utiliser uniquement les onglets PP, ignorer ou supprimer les onglets Holding. Pour un client à 3+ holdings : dupliquer les onglets Holding 2 en "Holding 3", "Holding 4", etc.

**Profil simple (cadrage P0 raccourci)** : pour un client « 1 PP avec 1-2 comptes, ± 1 PM associée » — le cas à industrialiser — supprimer d'emblée tous les onglets Holding 2 (et Holding 1 si pas de PM), ainsi que les onglets `Non coté` / `NC Flux` / `Dettes` non utilisés. Le manifeste et le squelette s'adaptent automatiquement : aucune autre configuration n'est nécessaire.

### Onglet Lignes — détail par actif du financier coté

Un onglet par entité. **Une ligne par actif**, données dès la ligne 4 :

| Colonne | Contenu | Convention |
|---|---|---|
| A — Contrat | Clé de jointure vers l'onglet `Fin coté` | **= libellé exact** « Nature — Assureur/Banque » (ex. « Assurance-vie — Wealins Lux ») |
| B — Libellé | Nom de l'actif | Tel qu'affiché au dépositaire |
| C — ISIN | Code ISIN | Vide autorisé pour liquidités/compte courant |
| D — Valeur (€) | Valorisation de la ligne | |
| E — Perf % | Performance de la ligne **telle que publiée par le dépositaire** | À renseigner **systématiquement** dès que le relevé la fournit ; **vide autorisé uniquement pour les liquidités/compte courant**. L'horizon (YTD / depuis achat / période) dépend de la source — le préciser en note de run (cf. `SKILL.md` §2.b, règle de performance par ligne). Une valeur absente produit un `0 €` / `—` silencieux dans le rendu (la Perf € est dérivée par le moteur) |
| F — Poche | Libellé de poche | Uniquement pour les contrats multi-poches |
| G — Classe Rhétorès | Classe d'actif | Alimente le donut classes |
| H — Géographie | Zone géographique | Optionnelle, toutes classes (cf. `pipeline/GEO_RULES.md`) |
| I — SRI (1-7) | Niveau de risque | Optionnel, repli par classe si absent |

### Onglet NC Flux — flux datés du non coté

Un onglet par entité ayant du non coté. **Une ligne par événement**, données dès la ligne 4 :

| Colonne | Contenu | Convention |
|---|---|---|
| A — Nom du fonds / Véhicule | Fonds concerné | **= libellé exact** de la colonne A de l'onglet `Non coté` (clé de jointure) |
| B — Date | Date de l'événement | DD/MM/YYYY ; date **future autorisée** pour les types « prévu » |
| C — Type | Nature du flux | `Appel` · `Distribution` · `Valorisation` · `Appel prévu` · `Distribution prévue` (liste déroulante) |
| D — Montant (€) | Montant | **Toujours positif** ; le sens est porté par le Type |

Conventions dérivées (calculées par `p2_fill.py`, jamais saisies) :
- **NAV d'un fonds à une date** = dernière `Valorisation` ≤ date, maintenue en palier ; à défaut, capital appelé cumulé (proxy au coût). `Valorisation` = NAV **totale** du fonds à la date, pas un delta.
- **Appelé / Distribué** = cumuls des flux `Appel` / `Distribution` ≤ date de reporting. **Reste à appeler** = engagement − appelé.
- Les types **« prévu »** n'alimentent que l'échéancier prévisionnel affiché dans le reporting (page « Détails » de la vue fonds) — **jamais les KPIs**.
- **TVPI** = (distribué + NAV) / appelé · **DPI** = distribué / appelé · **RVPI** = NAV / appelé.
- **TRI** : jamais calculé — saisi dans la colonne `TRI (%)` de l'onglet `Non coté` (valeur fournie par l'assureur / le GP, ex : `12,5`). Le TRI consolidé du portefeuille est la moyenne des TRI fonds pondérée par le capital appelé (approximation, affichée comme telle).

Si l'onglet `NC Flux` est absent ou vide pour un fonds : repli sur les colonnes `Capital engagé` / `Capital appelé` / `Valeur liquidative` de l'onglet `Non coté` (distribué = 0, pas d'échéancier).

### Workflow type — Démarrer un nouveau reporting

**Étape 1 — Préparation du template client**
1. Copier `references/Reporting_data_template.xlsx` → `Reporting_[Client]_[Date].xlsx`
2. Renommer les onglets selon les entités réelles du client (ex : `Liq — PP` → `Liq — Hervé G.` ; `Liq — Holding 1` → `Liq — SAS AX`)
3. Mettre à jour les titres A1 de chaque onglet en cohérence (ex : `LIQUIDITÉS — Hervé G.`)
4. Ajouter ou supprimer les onglets selon le nombre d'entités du client

**Étape 2 — Paramétrage de la période**
1. Pour chaque onglet `Mouvements`, renseigner :
   - **Cellule G2** : date de fin de période (format DD/MM/YYYY)
   - **Cellule H2** : nombre de jours total de la période (ex : 90 pour T1, 120 pour 4 mois, 181 pour S1)
2. Pour les onglets `Liq`, `Immo`, `Fin coté` : l'en-tête "Valeur au [Date]" sera affiché tel quel — la date réelle sera renseignée dans le HTML du reporting final

**Étape 3 — Collecte des données**
Remplir les cellules en **bleu sur fond jaune** = saisie manuelle obligatoire.
Les cellules en **noir sans fond** sont des formules qui se calculent automatiquement (ne pas modifier).

**Sources amont qui alimentent le fichier Excel** (à consulter par le CGP, pas par Claude au moment du HTML) :
- **Liquidités** : relevés bancaires de la période
- **Immobilier** : actes notariés (acquisition), expertise ou estimation (valeur courante)
- **Financier coté** : relevés trimestriels des dépositaires (UBS, EdR, Indosuez, CA, Tilvest, Allianz, etc.), souscriptions initiales (nominal investi, date)
- **Mouvements** : extraits bancaires / relevés (versements, retraits, dates exactes)
- **Non coté** : reportings GP (Altaroc, Essling, Andera, etc.) + appels de fonds. Le TRI (%) est repris tel quel du reporting assureur/GP.
- **NC Flux** : avis d'appel de fonds, avis de distribution, reportings trimestriels GP (NAV) + échéancier prévisionnel communiqué par le GP
- **Dettes** : tableaux d'amortissement, contrats de prêt

Une fois le fichier Excel rempli et fiabilisé, **il devient la source unique** pour la production du reporting HTML par Claude. Les relevés des dépositaires ne sont plus consultés directement pour les valeurs (seulement pour la classification fine ligne par ligne — voir section 5).

**Étape 4 — Validation des cohérences**
Vérifier :
- Les totaux par catégorie (lignes TOTAL navy) matchent la somme des données
- Les formules Modified Dietz (onglets Mouvements colonnes E et F) calculent bien le poids des flux
- Les classes Rhétorès sont saisies (colonne Classe Rhétorès dans Non coté et Immo)

**Étape 5 — Génération du HTML reporting**
Une fois le template rempli, l'utiliser comme source pour générer le widget tableau exhaustif du Bloc 03 dans le reporting HTML, selon les règles de la section 16 (V10 référence).

### Conventions de remplissage

**Code couleur des cellules** :
- 🟦 **Texte bleu (#0000FF) sur fond jaune (#FFFDE7)** = donnée à saisir manuellement
- ⬛ **Texte noir sur fond blanc** = formule calculée automatiquement (ne pas modifier)
- 🟨 **Fond gold pâle (#F5EDD8)** = titre d'onglet (ligne 1)
- 🟪 **Fond navy (#0D1B2A)** = en-tête de colonne ou ligne TOTAL

**Saisie des dates** : format DD/MM/YYYY uniquement. Pour les années seules (date d'acquisition immobilier, année d'échéance dette) : format numérique 4 chiffres.

**Saisie des montants** : en euros, sans symbole (le format est appliqué automatiquement). Saisir `1500000`, pas `1 500 000 €`.

**Cellule Nominal investi (Fin coté)** : pour les contrats multi-poches, renseigner au niveau de **chaque poche** (pas de la ligne mère). Permet d'identifier la performance de chaque gestion de manière indépendante.

**Cellule Nantissement** : "Oui" (avec majuscule) si confirmé explicitement, "—" sinon. Ne jamais supposer un nantissement à partir de l'existence d'une dette.

### Cohérence avec la charte visuelle du reporting HTML

Le template Excel utilise la **même palette de couleurs** que le reporting HTML final, pour cohérence du cabinet :
- Navy `#0D1B2A`
- Gold `#B8975A` / Gold pâle `#F5EDD8`
- Jaune saisie `#FFFDE7`
- Police Arial (police de référence du fichier source ; le HTML utilise DM Sans / Cormorant Garamond pour le rendu client final)

### Évolutions futures du template

Le template est conçu pour évoluer avec le skill. Toute modification doit respecter :
1. La structure "PP + N Holdings" (générique, indépendante du client)
2. La charte couleurs (cohérence visuelle avec le reporting HTML)
3. La police Arial uniforme sur tous les onglets
4. La logique cellules de saisie (bleu/jaune) vs cellules formules (noir/blanc)
5. La cohérence des en-têtes avec les colonnes documentées en section 16 du skill

Toute évolution du template doit être documentée dans cette section 17 et le fichier `references/Reporting_data_template.xlsx` mis à jour en parallèle.

### ⚠ Points en suspens du template (à traiter ultérieurement)

**Calcul automatique des Gain € / Gain % / Gain % YTD dans Fin coté** : à ce jour, les 3 colonnes Gain ne sont **pas alimentées par des formules**. Elles sont vides dans le template.

Logique cible (3 niveaux de complexité possibles) :

- **Niveau A — formules simples** : `Gain € = Valeur date − Nominal investi` · `Gain % = Gain € / Nominal investi` · `Gain % YTD = (Valeur date − Valeur 01/01) / Valeur 01/01`. Limite : Gain % YTD faussé si flux dans la période.

- **Niveau B — Modified Dietz partiel** : Gain € et Gain % en formules simples (niveau A), mais Gain % YTD calculé via Modified Dietz en agrégeant les flux de l'onglet Mouvements (SUMIFS sur le contrat/poche). Nécessite une clé de jointure propre entre Fin coté et Mouvements.

- **Niveau C — Modified Dietz complet + contrôles** : niveau B + vérifications de cohérence (somme des poches = total contrat, contrôle d'erreurs, etc.).

**État actuel** : aucun niveau implémenté. À traiter quand la priorité le justifiera. Pour les clients à faibles flux (peu de versements/retraits dans la période), le niveau A est suffisant. Pour les clients à flux fréquents (versements programmés, rachats partiels), passer directement au niveau B.

**Prérequis pour niveau B** : ajouter une colonne "ID poche" ou utiliser une concaténation (contrat + société de gestion) comme clé de jointure entre Fin coté et Mouvements.
