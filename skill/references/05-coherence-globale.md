# Règle de cohérence globale — propagation des modifications

> La règle des 4 zones à propager systématiquement après toute modification de donnée.
> Référencé depuis le SKILL.md.

---

## Le principe

Un reporting Rhétorès consolidé affiche la même donnée sous plusieurs angles différents :
en KPI synthétique (Hero), en lecture de performance (Bloc 01), en tableau global et en
allocation graphique (Bloc 02), en détail ligne par ligne (Bloc 03). Toute modification
d'une valeur doit donc être propagée dans **tous les endroits** où cette donnée apparaît.

**Pourquoi c'est critique** : une incohérence (par exemple, un actif net dans le Hero qui ne
correspond pas à la somme des cards entités) **fait perdre la confiance du client**. C'est
l'erreur la plus visible et la plus dommageable d'un reporting.

---

## Les 5 zones à propager

Après toute modification d'un paramètre (valeur, dette, catégorie, entité, classification),
vérifier ces 5 zones avant de livrer :

### Zone 1 — Hero
Conformément à la spécification figée (voir `references/01-architecture-blocs.md` § Hero
et `references/09-formalisme.md`), les 4 KPIs du Hero sont :
- `Actif` (brut total)
- `Dette` (total des dettes)
- `Actif net` (Actif − Dette)
- `Performance YTD` (KPI fusionné : Gain € + Gain % + base de calcul)
  - La base = Financier coté + Financier non coté

### Zone 2 — Bloc 01 (Étude de la performance)
- Widgets de performance (à spécifier ultérieurement)
- Toute modification d'une valeur impactant la performance doit être propagée ici

### Zone 3 — Bloc 02 (Tableau global + Mini-donuts d'allocation + Cards entités)
- Tableau global de synthèse : Brut / Dettes / Net par catégorie
- Mini-donuts d'allocation :
  - Classes d'actifs (12 classes Rhétorès)
  - Géographie (sur Actions + PE)
  - Dépositaires
  - Enveloppes
- Cards entités (PP + Holdings) : Brut / Dettes / Net par entité

### Zone 4 — Bloc 03 (Sous-totaux par catégorie)
- Sous-total Liquidités, Sous-total Immobilier, Sous-total Financier coté,
  Sous-total Non coté, Sous-total Dettes — par entité

### Zone 5 — Bloc 03 (Totaux par entité)
- Total Hervé G., Total SAS AX, Total SAS LG, etc.
- Total consolidé en bas du tableau (ligne navy)

---

## Checklist de cohérence à valider

Avant toute livraison d'un reporting modifié, valider ces équations :

- [ ] **Brut total** = Liquidités + Immobilier + Financier coté + Non coté
- [ ] **Dettes** = somme de toutes les lignes du tableau Dettes (jamais ventilées par actif)
- [ ] **Net** = Brut − Dettes
- [ ] **Cards entités** (PP + Holdings) = cohérentes avec le tableau global
- [ ] **Hero KPIs** = cohérents avec les cards entités
- [ ] **Donuts** = pourcentages cohérents avec les valeurs des cards
- [ ] **Gain € YTD** = somme des Gain € YTD par entité
- [ ] **Géographie** : la somme des % par zone = 100% (uniquement sur Actions + PE)

---

## Cas spécifiques de propagation

**Modification d'une valeur de fonds** : impact sur le total de la poche → impact sur le total
du contrat → impact sur la catégorie Financier coté → impact sur l'entité → impact sur le total
global → impact sur les donuts d'allocation et de géographie.

**Ajout/suppression d'une ligne** : vérifier que tous les comptes de lignes dans les légendes
(ex: "Rhétorès · 4 poches") sont mis à jour.

**Changement de classification d'un fonds** : impact uniquement sur les donuts d'allocation
(et géographie si applicable), pas sur les totaux. Mais il faut absolument re-générer les donuts.

**Reclassification entité** (ex: déplacer un actif d'Hervé G. vers SAS AX) : impact sur les
totaux entité, mais le total consolidé reste inchangé.
