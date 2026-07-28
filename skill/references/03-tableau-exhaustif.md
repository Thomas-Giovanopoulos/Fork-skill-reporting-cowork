# Architecture du tableau patrimonial exhaustif (Bloc 03)

> Le tableau exhaustif est le cœur du reporting. Détail ligne par ligne par entité, structuré
> en 5 catégories : Liquidités, Immobilier, Financier coté, Non coté, Dettes.
> Référencé depuis le SKILL.md (Étape 5 du workflow).

---

## Règles structurelles fondamentales

### Ordre des entités

L'ordre dans le tableau exhaustif suit toujours la même logique :
1. **Personne Physique (PP)** en premier
2. **Holdings** ensuite, dans l'ordre déclaré au démarrage du reporting

### Ordre des catégories au sein d'une entité

Pour chaque entité, les catégories apparaissent dans cet ordre :
```
1. Liquidités
2. Immobilier
3. Financier coté
4. Non coté (PE, dette privée, immo non coté, infrastructures)
5. Dettes
```

### Hiérarchie visuelle des lignes (5 niveaux)

Les lignes du tableau ont 5 niveaux hiérarchiques distincts (classes CSS) :

| Niveau | Classe CSS | Description | Style |
|---|---|---|---|
| 1 | `rg` | Ligne groupe : nom de l'entité | Bandeau navy plein largeur |
| 2 | `rcat` | Ligne catégorie : "Liquidités", "Immobilier"... | Fond gold pâle, séparateur |
| 3 | `rc` | Ligne contrat / bien / position | Ligne standard |
| 4 | `rtot` | Sous-total de catégorie | Fond clair, gras |
| 5 | `rst` | Total entité | Bandeau navy semi-transparent |

### Contrats multi-poches

Pour les contrats avec plusieurs poches (Wealins, Cardif Lux, etc.) :
- Une **ligne mère** consolidée pour le contrat global
- Des **lignes filles** pour chaque poche, avec préfixe "↳" et indentation visuelle
- Le total consolidé est sur la ligne mère, pas dans une ligne séparée

### Nommage des sous-totaux et totaux

**Convention stricte** : tiret long (—) entre "Sous-total" et le nom de la catégorie. Jamais mentionner l'entité dans un sous-total.

- Sous-totaux de catégorie :
  - ✅ "Sous-total — Liquidités"
  - ✅ "Sous-total — Immobilier"
  - ✅ "Sous-total — Financier coté"
  - ✅ "Sous-total — Financier non coté"
  - ✅ "Sous-total — Dettes"
  - ❌ "Sous-total Liquidités Hervé G." (jamais mentionner l'entité)
  - ❌ "Sous-total Liquidités" (manque le tiret long)
  - ❌ "Sous-total PE SAS AX" (jamais l'entité, et "PE" n'est pas une catégorie de Bloc 03)

- Total entité (ligne `rst`) : "Total [Nom entité]" — l'entité DOIT figurer ici
  - ✅ "Total Hervé G."
  - ✅ "Total SAS AX"
  - ✅ "Total SAS LG"

**Pourquoi cette rigidité** : le sous-total est une agrégation de catégorie indépendamment de l'entité (la catégorie "Liquidités" est la même pour tous). Le total d'entité est par nature spécifique à une entité. Mélanger les deux brouille la hiérarchie visuelle.

### Colspan des lignes de totaux

Les lignes `rtot` (sous-total) et `rst` (total entité) doivent avoir un `colspan` qui couvre
la pleine largeur du tableau (sauf la première colonne libellé et la dernière colonne valeur).

---

## Colonnes par catégorie

Chaque catégorie a son propre jeu de colonnes. Voici la version canonique de référence.

### Liquidités (4 colonnes)

```
Compte | Banque | — | Solde au [Date]
```

- "Compte" : nom du compte (ex: "Compte courant", "Livret A")
- "Banque" : nom de l'établissement
- 3e colonne vide (alignée avec les autres catégories pour la grille visuelle)
- "Solde au [Date]" : valeur à la date du reporting

### Immobilier (6 colonnes)

```
Bien | Fonction | Propriété | Hypothèque | Valeur acquisition | Valeur au [Date]
```

- "Bien" : nom du bien (ville, adresse courte)
- "Fonction" : RP / RS / Usage / Rendement
- "Propriété" : Pleine propriété / Usufruit / Nue-propriété / SCI (avec parts)
- "Hypothèque" : "Oui" ou "—" (jamais supposer, confirmé explicitement uniquement)
- "Valeur acquisition" : prix d'achat
- "Valeur au [Date]" : valeur courante (expertise ou estimation)

**Convention** : "Loyer annuel" et "Date acquisition" sont dans le fichier Excel source mais
**ne sont pas affichées** dans le widget HTML du reporting (gain de place et de lisibilité).

### Financier coté (8 colonnes)

```
Contrat / Poche | Date d'investissement | Nantissement | Nominal investi | Gain € | Gain % | Gain % YTD | Valeur au [Date]
```

**Sémantique des colonnes** :

- **Date d'investissement** : date de souscription du contrat ou de la poche (pour les contrats
  multi-poches, au niveau de chaque poche pour identifier la perf de chaque gestion)
- **Nominal investi** : capital initial versé sur le contrat / la poche
- **Gain €** = `Valeur date − Nominal investi` (perf depuis l'origine en €)
- **Gain %** = `(Valeur date − Nominal investi) / Nominal investi` (perf depuis l'origine en %)
- **Gain % YTD** = `(Valeur date − Valeur 01/01) / Valeur 01/01` (perf YTD en %, calculée via la
  colonne technique "Valeur 01/01" du fichier source, non affichée dans le widget HTML)

**Fichier Excel source** — onglets "Fin coté" : la colonne "Valeur 01/01" est conservée comme
colonne technique nécessaire au calcul du Gain % YTD, bien qu'elle ne soit pas affichée dans le HTML.

**Détail par actif (onglet `Lignes`)** : chaque contrat se déplie sur ses actifs (ISIN, libellé,
valeur, classe, géo, poche). Les colonnes **Perf € / Perf %** de ce détail sont un champ **attendu**
(non décoratif), pas seulement pour la présentation la plus riche : la Perf € est **dérivée** de la
Perf % par le moteur (`p1_engine/p2_fill.py`), donc une Perf % absente produit silencieusement
`0 € / —` au lieu d'une alerte. Toujours renseigner la Perf % de la ligne dès que la source la publie
— cf. `SKILL.md` §2.b (règle de performance par ligne) pour l'horizon par source (PPT = depuis achat,
Dauphine = période du relevé, etc.).

### Non coté (6 colonnes)

```
Fonds / Véhicule | Gestionnaire | Stratégie | Cap. engagé | Cap. appelé | Valorisation
```

- "Fonds / Véhicule" : nom du fonds (ex: "Altaroc Odyssey 2026", "Essling Co-Invest")
- "Gestionnaire" : GP (ex: "Altaroc", "Essling Capital")
- "Stratégie" : LBO / Co-invest / Secondaire / Growth / Distressed / Real Estate / Infrastructure
- "Cap. engagé" : engagement total signé avec le GP
- "Cap. appelé" : montant déjà versé (appels de fonds reçus)
- "Valorisation" : NAV actuelle (généralement = capital appelé tant que pas de relevé GP)

### Dettes (4 colonnes)

```
Intitulé | Établissement | Type | Capital restant dû
```

- "Intitulé" : libellé du prêt (ex: "Prêt Sanary", "Prêt Lombard UBS")
- "Établissement" : banque créancière
- "Type" : "In fine" ou "Amortissable"
- "Capital restant dû" : à la date du reporting (en rouge dans le rendu visuel)

---

## Nomenclature détaillée du Financier coté

Pour les contrats avec plusieurs poches, la nomenclature des libellés dans la colonne 1
"Contrat / Poche" suit cette convention :

### Ligne mère (multi-poches)

- `cname` (libellé principal) : `[Nature] — [Assureur/Banque]`
  Exemples : "Assurance-vie — Wealins Lux", "Contrat de capitalisation — Wealins Lux"
- `cdet` (sous-libellé) : `[Intermédiaire] · [N] poches`
  Exemples : "Rhétorès · 4 poches", "Indosuez · 2 poches"

### Ligne poche (fille d'une multi-poches)

- `cname` : `↳ [Type poche] · [Société de gestion]`
  Exemples : "↳ FID · Dauphine AM", "↳ FAS · Rhétorès", "↳ Fonds euros · Cardif"
- `cdet` : `[Dépositaire] · [Mode de gestion] · [Profil]`
  Exemples : "UBS · Déléguée · Équilibré", "Indosuez · Déléguée · Sécuritaire"

### Ligne mono-poche

- `cname` : `[Nature] — [Assureur/Banque]`
- `cdet` : `[Intermédiaire] · [Mode de gestion] · [Profil]`
  Exemple : "Crédit Agricole · Déléguée · Équilibré"

### Orthographe exacte des sociétés de gestion

À respecter pour la cohérence visuelle :
- "Dauphine AM" (et non "Dauphine")
- "De Pury Pictet" (et non "PPT" ou "De Pury Pictet Turrettini")
- "Edmond de Rothschild" (et non "EdR")
- "Rhétorès" (avec l'accent)
- "UBS" (en capitales, pas "Ubs")

### Colonne Dépositaire — Convention Luxembourg vs France

Cette règle est **critique pour l'exactitude réglementaire** du reporting.

**Pour les contrats d'assurance-vie de droit luxembourgeois** :
- Toujours identifier la **banque dépositaire nommée**, distincte de l'assureur
- Exemples : Wealins contrats FR056470 / FC056913 → dépositaire **UBS** · Cardif Lux Vie / Aster Horizon → dépositaire **Indosuez** · Cardif Lux 2 → dépositaire **Edmond de Rothschild**
- Cette information figure obligatoirement dans le contrat (triangle de sécurité luxembourgeois)

**Pour les contrats d'assurance-vie de droit français** :
- Dépositaire = `NC` (non communicable)
- Pourquoi : l'assureur français porte la responsabilité bilantielle sans dépositaire tiers identifiable. La séparation triangle Lux n'existe pas.
- **Ne jamais inscrire le nom de l'assureur comme dépositaire** pour les AV françaises. Exemple : pour Prédica France, dépositaire = `NC`, pas "Prédica" et pas "Crédit Agricole"

**Tableau récapitulatif** :

| Type de contrat | Exemple | Dépositaire à inscrire |
|---|---|---|
| AV Luxembourg multi-poches | Wealins FR056470 (Hervé G.) | UBS |
| Capi Luxembourg multi-poches | Wealins FC056913 (SAS AX) | UBS |
| AV Luxembourg | Cardif Lux 1 / Aster Horizon | Indosuez |
| AV Luxembourg | Cardif Lux 2 (EdR) | Edmond de Rothschild |
| AV France | Prédica, CNP, Generali | **NC** |
| Capi France | (cas rare) | **NC** |
| CTO direct | CTO EdR Axynapse | Edmond de Rothschild |
| CTO direct | CTO Tilvest | Tilvest |

### Colonne Nantissement

Tag gold "Oui" si le contrat sert de garantie pour un prêt, "—" sinon.
**Règle d'or** : ne jamais supposer un nantissement à partir de l'existence d'une dette.
Toujours confirmé explicitement par le CGP.

---

## Standard de présentation — V10 (référence absolue)

Le fichier `consolidé_HG_v10.html` est le **standard de présentation absolu** pour Hervé G.
Toute évolution du Bloc 03 doit respecter sa structure visuelle :

### Structure générale du Bloc 03

- Tableau unique avec toutes les entités
- Largeur fixe optimisée pour impression A4 paysage
- Polices : Cormorant Garamond (titres) + DM Sans (corps)
- Couleurs : navy `#0D1B2A` + gold `#B8975A`

### Notes complémentaires

- Les montants sont affichés en € avec espace fin comme séparateur de milliers
- Pas de signe € sur les valeurs (déjà dans l'en-tête de colonne)
- Les pourcentages sont affichés avec 1 décimale, sauf perf YTD avec 2 décimales
- Variations positives en vert `#2D6E4E`, négatives en rouge `#8B2E2E`

→ Charte visuelle complète : `references/04-charte-visuelle.md`
