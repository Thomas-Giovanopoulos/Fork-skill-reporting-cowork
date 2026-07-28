# Formalisme transversal du reporting

> Règles de nommage, casse, format des montants, pourcentages, dates et couleurs qui
> s'appliquent à **tous les blocs** du reporting (Hero + Bloc 00 à 03 + Footer).
> Référencé depuis le SKILL.md et depuis `references/01-architecture-blocs.md`.
>
> **Ce fichier est la source unique de vérité pour le formalisme**. En cas de divergence
> entre ce fichier et un autre, ce fichier prévaut.

---

## Statut

Ce fichier est construit **incrémentalement** au fil des décisions prises en collaboration
avec Tristan. Les règles ci-dessous sont **figées** (validées par Tristan) sauf mention contraire.
Les blocs non encore couverts (00, 01 Performance, 02 Répartition, 03 Exhaustif) auront
leurs règles spécifiques ajoutées au fur et à mesure.

---

## 1. Libellés des KPIs du Hero

| Libellé | Usage |
|---|---|
| `Actif` | KPI 1 — Actif brut total |
| `Dette` | KPI 2 — Total des dettes |
| `Actif net` | KPI 3 — Actif − Dette |
| `Performance YTD` | KPI 4 — Performance fusionnée (€ + % + base) |

**Casse** : capitalisation initiale uniquement, le reste en minuscules.
- ✅ `Actif net`
- ❌ `ACTIF NET`
- ❌ `actif net`
- ❌ `Actif Net`

---

## 2. Format des montants en euros

### Règles de base

- **Séparateur de milliers** : espace fin (U+202F idéalement, ou espace normal acceptable)
- **Symbole €** : positionné à la fin, séparé du montant par une espace
- **Pas d'abréviation** : ne jamais raccourcir en K€ ou M€. Toujours afficher le format complet.
  - ✅ `6 073 000 €`
  - ❌ `6,07 M€`
  - ❌ `6073 K€`

### Valeurs négatives

- Signe `-` (tiret simple du clavier) collé au montant, suivi d'une espace
  - ✅ `- 1 100 000 €`
  - ❌ `(1 100 000 €)`
  - ❌ `1 100 000 € -`

### Cas spécifique : KPI Dette du Hero

Le KPI Dette du Hero est **affiché sans signe**, le libellé "Dette" suffisant à indiquer
la nature passive du montant. La couleur rouge complète l'information sémantique.
- ✅ `1 100 000 €` (avec couleur rouge)
- ❌ `- 1 100 000 €` (le signe est redondant avec le libellé)

### Valeur nulle ou absente

Afficher `—` (tiret cadratin U+2014) plutôt que `0 €` ou vide.
Évite le bruit visuel des zéros, et signale clairement l'absence de la catégorie.

---

## 3. Format des pourcentages

- **Nombre de décimales** : 2 (`+ 2,04 %`, pas `+ 2 %` ni `+ 2,0 %`)
- **Espace avant le `%`** : aucune
  - ✅ `2,04%`
  - ❌ `2,04 %`
- **Signe explicite pour les positifs** : oui, `+` collé au chiffre
  - ✅ `+2,04%`
  - ❌ `2,04%`
- **Signe pour les négatifs** : `-` collé au chiffre
  - ✅ `-1,80%`

> Note d'écriture : ce fichier utilise par endroits une espace avant `%` pour la lisibilité
> de la doc. **Dans le reporting généré, appliquer la règle stricte : pas d'espace.**

---

## 4. Format des dates

### Dans le Hero

Format long en lettres : `31 mars 2026`
- Jour : nombre sans zéro initial (1, 2, ..., 31)
- Mois : nom complet en lettres, minuscules (`janvier`, `février`, ..., `décembre`)
- Année : 4 chiffres

### Mention de la période — Règle de double format

La période est affichée sous **deux formats distincts selon le contexte d'usage** :

**Format long** : `T1 2026` (avec espace, sans tiret)
- Usage : Hero, titres de bloc, mentions formelles dans la prose
- Variantes : T1 / T2 / T3 / T4 (trimestres), S1 / S2 (semestres), année seule pour annuel

**Format court** : `T1-26` (avec tiret, année sur 2 chiffres)
- Usage : libellés de cards, en-têtes de tableau, légendes — toute zone à largeur contrainte
- Variantes : `T1-26` / `T2-26` / `S1-26` / `26` (annuel)

**Pourquoi cette double règle** : le format long est plus lisible et plus institutionnel dans
les zones où la place ne manque pas. Le format court permet de respecter la cohérence visuelle
des cards et tableaux sans débordement de libellé. La règle est explicite : pas de choix au
cas par cas, le contexte d'usage commande le format.

### Mention de la période dans le Hero

Le Hero utilise le **format long** : `T1 2026`
- Concaténation Hero : `31 mars 2026 · T1 2026` (séparateur point médian `·` avec espaces)

### Mention de la période dans les libellés de cards (Bloc 00)

Les cards du Bloc 00 utilisent le **format court** :
- `T1-26 - Faits marquants`
- `T1-26 - Performance des indices`

### Dans les autres blocs

Le format des dates **varie selon le contexte**. Notamment, le tableau patrimonial exhaustif
(Bloc 03) utilisera souvent un format court `JJ/MM/AAAA` pour densifier la lecture des colonnes.

Les règles spécifiques par bloc seront définies au fur et à mesure.

---

## 5. Couleurs sémantiques

### Performance et valeurs financières

| Sémantique | Couleur | Code |
|---|---|---|
| Performance positive (gain, plus-value) | Vert | `#2D6E4E` (vert sombre élégant) |
| Performance négative (perte, moins-value) | Rouge | `#8B2E2E` (rouge bordeaux discret) |
| Dette / passif | Rouge | `#8B2E2E` (cohérent avec la moins-value) |
| Neutre / standard | Navy | `#0D1B2A` |

### Application dans le Hero

| KPI | Couleur appliquée |
|---|---|
| `Actif` (valeur) | Navy (neutre) |
| `Dette` (valeur) | **Rouge** (`#8B2E2E`) |
| `Actif net` (valeur) | Navy (neutre) |
| `Performance YTD` ligne 1 (Gain €) | Vert si positif, **Rouge** si négatif |
| `Performance YTD` ligne 2 (Gain %) | Vert si positif, **Rouge** si négatif |
| `Performance YTD` ligne 3 (base : X €) | Couleur muted neutre |

### Cohérence avec la charte visuelle

Ces couleurs sont alignées avec la palette définie dans `references/04-charte-visuelle.md`.
En cas de divergence ponctuelle, **ce fichier prévaut** pour la sémantique. La charte définit
les variables CSS techniques (`--up`, `--dn`, `--navy`, etc.).

---

## 6. Formalisme spécifique du Bloc 00 — Contexte de marché

### Titre du bloc

- Libellé exact figé : `Contexte de marché`
- Préfixé par le numéro `00` en gold

### Libellés des cards (format figé)

| Card | Libellé exact |
|---|---|
| Card faits marquants | `T1-26 - Faits marquants` |
| Card indices | `T1-26 - Performance des indices` |

(Le préfixe période s'adapte à la période : `T1-26`, `T2-26`, `S1-26`, etc. selon la règle
du § 4 ci-dessus.)

### Texte macro narratif

- **Voix** : narrative impersonnelle. **Pas de "nous", pas de "je"**, pas de pronom personnel.
- **Engagement** : maîtrisé. Décrire principalement, prendre position avec mesure quand pertinent (notamment au §5).
- **Longueur** : 600 à 750 mots selon la richesse de l'actualité du trimestre.
- **Précision chiffrée** : chiffres clés pour illustrer, sans abus.
- **Structure** : 5 paragraphes thématiques (voir `references/01-architecture-blocs.md` Bloc 00 pour le détail des thèmes).

### Bullets de la card "Faits marquants"

- **5 bullets** cibles
- **~15 mots par bullet**
- **Phrases rédigées synthétiques** : phrases nominales ou verbales complètes, pas de style télégraphique

### Liste figée des indices (card Performance des indices)

Liste fermée de 8 indices, à afficher systématiquement, dans cet ordre exact :

1. `S&P 500`
2. `Nasdaq Composite`
3. `DJ Euro Stoxx 50`
4. `CAC 40`
5. `Once d'or (USD / once)`
6. `Pétrole USD Brent`
7. `EUR / USD`
8. `Bitcoin`

**Règles strictes** :
- Aucun indice n'est ajouté ou retiré
- Ordre figé (Actions US → Actions Europe → MP → Change → Crypto)
- Libellés exacts (espaces, majuscules, ponctuation)
- Colonne unique : performance YTD (pas de 1 an, 3 ans, etc.)
- Format des perfs : voir § 3 (signe explicite, 2 décimales, pas d'espace avant `%`)
- Couleur des perfs : voir § 5 (vert si positif, rouge si négatif)

### Sources de données — Règle de double sourcing

**Pour les chiffres de la card "Performance des indices"** :
- **7 indices sur 8** (S&P 500, Nasdaq Composite, DJ Euro Stoxx 50, CAC 40, Once d'or, Pétrole Brent, EUR/USD) → extraits **exclusivement** du document de situation UBS fourni par Tristan à chaque trimestre
- **Bitcoin** → source officielle internet (CoinMarketCap, CoinGecko, ou équivalent d'autorité reconnue)
- **Aucune recherche web pour les 7 indices UBS** : si le document n'est pas fourni, signaler le manque à Tristan plutôt que de chercher ailleurs

**Pour la rédaction du texte macro** (récit narratif, politiques monétaires, contexte géopolitique, dynamiques de marché, thèmes structurels) — sources web autorisées :
- Banques centrales (Fed, BCE, BoJ, BoE)
- Institutions internationales (FMI, OCDE, Banque Mondiale)
- Statistiques officielles (BLS, Eurostat, INSEE)
- Notes de recherche des grandes banques (Goldman Sachs, JPM, BlackRock, Pictet, Lombard Odier, Carmignac, Amundi, Allianz Research)
- Données de marché (Bloomberg, Reuters, FT Markets, WSJ Markets)

**Sources à éviter dans tous les cas** : agrégateurs grand public, blogs, contenus non sourcés.

**Pourquoi cette double règle** : la source UBS garantit la cohérence et l'opposabilité des
chiffres face au client (même source pour tous les indices, pas de divergence entre sites web).
Les sources web institutionnelles permettent de bâtir un récit macro à la hauteur des
meilleurs analystes de la place.

---

## 7. Règles complémentaires (à enrichir au fil des décisions)

Les sections suivantes seront ajoutées au fur et à mesure de la spécification des blocs
01 (Performance), 02 (Répartition) et 03 (Exhaustif) :

- Format des dates dans le tableau exhaustif
- Format des libellés de contrats / poches multi-poches
- Format des libellés de fonds non cotés
- Règles d'arrondi pour les pourcentages d'allocation
- Format des KPIs des widgets de performance (à définir avec le Bloc 01)

> **À chaque décision validée par Tristan, ajouter une section à ce fichier**, plutôt que
> d'enfouir la règle dans la spécification d'un bloc spécifique. C'est la condition pour
> que le formalisme reste cohérent à travers tout le reporting.
