# Charte visuelle et design du dashboard HTML

> Palette de couleurs, polices, CSS du tableau patrimonial, configuration Chart.js des donuts.
> Référencé depuis le SKILL.md (Étape 5 du workflow).

---

## Palette de couleurs

```css
--navy: #0D1B2A        /* fond hero, lignes groupe tableau */
--gold: #B8975A        /* accents, titres, bordures */
--gold-light: #D4B07A  /* valeurs hero, éléments mis en avant */
--gold-pale: #F5EDD8   /* fond sous-totaux, encadrés clairs */
--cream: #FAF7F2       /* fond page */
--muted: #7A8899       /* textes secondaires, mentions */
--up: #2D6E4E          /* performances positives (vert) */
--dn: #8B2E2E          /* performances négatives (rouge) */
```

**Convention couleurs perf** :
- Performances positives : couleur `#2D6E4E` (vert sombre élégant)
- Performances négatives : couleur `#8B2E2E` (rouge bordeaux discret)
- Pas de vert vif ou rouge criard (style FO sobre)

---

## Typographie

- **Titres / chiffres principaux** : `Cormorant Garamond` (serif élégant)
- **Corps / tableaux** : `DM Sans` (sans-serif moderne, weight 300)
- **Code / monospace** : si besoin, `JetBrains Mono`

Import Google Fonts en début de `<style>` :
```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
```

---

## Structure de page

- **Hero navy** : bandeau plein largeur avec KPI strip (4-5 métriques en grand format)
- **Sections numérotées** : 00 / 01 / 02 / 03 avec numéro en gold
- **Scroll fluide** : fade-in au scroll via IntersectionObserver
- **Format optimisé** : impression A4 paysage (largeur ~1200px)

---

## CSS du tableau patrimonial

Classes principales pour les lignes :

| Classe | Description | Style |
|---|---|---|
| `rg` | Ligne groupe (nom entité) | Fond navy, texte white, lettrage espacé uppercase |
| `rcat` | Ligne catégorie | Fond gold pâle, texte gold, séparateur |
| `rc` | Ligne contrat/bien | Ligne standard, border-bottom subtil |
| `rtot` | Sous-total catégorie | Fond gold-pale, font-weight 500 |
| `rst` | Total entité | Fond navy semi-transparent, texte gold-light |

Badges pour les performances et tags :

| Classe | Style |
|---|---|
| `badge-pos` | `background: rgba(45,110,78,0.08); color: #2D6E4E` |
| `badge-neg` | `background: rgba(139,46,46,0.08); color: #8B2E2E` |
| `badge-ph` | `background: rgba(184,151,90,0.1); color: #B8975A; font-style: italic` |
| `tag-gold` | Fond gold pâle, bordure gold (pour Nantissement = "Oui") |

**Convention** : badges semi-transparents (pas de fond plein), texte coloré. Donne un effet
élégant et discret.

---

## Donuts allocation (Chart.js)

### Palette par classe d'actifs

```js
Actions             → '#0D1B2A'  // navy (principal)
Obligations         → '#B8975A'  // gold (secondaire)
Produits structurés → '#5A7A9B'  // bleu-gris
Fonds euros         → '#D4B07A'  // gold-light
Alternatifs         → '#7A8899'  // muted
Matières premières  → '#C8853A'  // or chaud
Crypto              → '#3F4A5C'  // navy clair
Monétaire           → '#9BB5A0'  // vert pâle
Private Equity      → '#5D4E37'  // brun PE
Dette privée        → '#8B7355'  // brun moyen
Immo non coté       → '#A88D6D'  // brun clair
Infrastructures     → '#6B7C5D'  // vert pétrole
```

### Configuration Chart.js standard

- `cutout: '65%'` pour les mini-donuts du Bloc 02
- `borderWidth: 0` (style propre sans bordures entre segments)
- Légendes positionnées à droite ou en dessous selon la largeur
- **Plafond `devicePixelRatio`** (`partials/head.html.j2`, juste après le `<script>` CDN Chart.js) :
  `Chart.defaults.devicePixelRatio = Math.min(window.devicePixelRatio||1, 2)`. Sans ce plafond,
  Chart.js dimensionne le buffer interne du canvas en multipliant sa taille CSS par le DPR lu à
  l'instant du rendu ; un DPR aberrant (lu pendant une transition d'affichage, ex. bascule Mac →
  vidéoprojecteur en mode « dupliquer ») peut faire calculer un buffer disproportionné et provoquer
  une perte de contexte 2D — symptôme observé : le graphique commence à se tracer puis abandonne,
  remplacé par l'icône « sad face » de Chrome. 2x couvre tous les écrans Retina réels sans perte de
  netteté visible.

### Graphiques cartésiens (ligne/barres — perf_evolution, perf_nc_bars, hist_chart)

Contrairement aux donuts (sans axes), ces 3 graphiques ont un axe Y linéaire dont Chart.js calcule
dynamiquement le nombre de graduations. **Règle obligatoire pour tout nouveau graphique cartésien** :

- Le conteneur direct du `<canvas>` doit avoir une **hauteur CSS fixe** (`height` en px, pas `auto`,
  pas dépendant du contenu) — jamais seulement l'attribut HTML `height="…"` du canvas, qui n'est
  qu'un indice initial ignoré dès que Chart.js prend la main.
- `options.maintainAspectRatio: false` **toujours explicite** — sans ça, Chart.js déduit la hauteur
  de la largeur du conteneur (aspectRatio par défaut ≈2), ce qui crée une dépendance largeur→hauteur
  fragile, aggravée ici par le mécanisme de mise à l'échelle globale du reporting (`.rpt-canvas`,
  `transform:scale()` piloté en JS, cf. `foot.html.j2`). Un incident réel de mise en page cassée
  (structure entière + widgets surdimensionnés) lors d'un branchement Mac → vidéoprojecteur en mode
  « dupliquer » a été tracé à cette combinaison (axe non figé + hauteur non figée + double calcul de
  scale). Les 3 graphiques concernés vivent dans `.pnc-page[data-pnc-page="chart"]` (hauteur fixée en
  CSS, 270px) ou `.histo-chart-wrap` (260px, `historique.html.j2`) — réutiliser l'un de ces conteneurs
  plutôt que de recréer un canvas nu.

### Légende des donuts

Toujours afficher le nominal en K€ sous le libellé de chaque ligne :
```html
<div class="leg-name">Actions</div>
<div class="leg-nom">~8 500 K€</div>
```

---

## Notes de bas de tableau

Inclure systématiquement une `note-box` gold pour expliciter :
- Les valorisations indicatives (relevé non aligné, ex: Saint Honoré au 17/04)
- Les retraits importants (ex: retrait Wealins Capi −2,3 M€)
- Les placeholders PE (valorisation au coût)
- La mention "actif net = brut − dettes"

Format :
```html
<div class="note-box">
  <p>* Valorisation indicative au 17/04/2026 (dernier relevé Saint Honoré disponible).</p>
</div>
```

---

## Format des montants

- **Euros** : format `1 234 567 €` (espace fin comme séparateur de milliers, signe € à la fin)
- **Pourcentages** : 1 décimale standard, 2 décimales pour les perf YTD
- **Variations** : signe explicite `+1,2 %` ou `−1,2 %` (avec tiret bas)
- **K€ / M€** : utiliser pour les valeurs très grandes en légende (`~8 500 K€`, `~12,5 M€`)
