# Pont Excel → P2 (remplissage)

Chaîne complète : **Excel source → manifeste → squelette (P1) → reporting rempli (P2)**.

```bash
# 1) Excel -> manifeste (lit l'onglet "Entités" + scanne les onglets catégorie)
python3 excel_to_manifest.py source.xlsx manifest.json \
        --period-long "T2 2026" --period-short "T2-26" \
        --date 2026-06-30 --date-display "30 juin 2026" --version v1

# 2) Excel + manifeste -> reporting rempli (réutilise la MÊME banque que P1)
python3 p2_fill.py source.xlsx manifest.json reporting_rempli.html
```

## Convention source : l'onglet « Entités »

Les libellés et types d'entités ne sont pas déductibles des seuls onglets (un onglet « PP »
ne dit pas « Camille D. »). Le fichier source doit donc comporter un onglet **`Entités`** :

| id | label | type (pp/holding) | onglet (suffixe) |
|----|-------|-------------------|------------------|
| client_exemple | Client Exemple | pp | PP |
| sas_exemple | SAS Exemple | holding | SAS Exemple |

Les onglets catégorie sont nommés `[Catégorie] — [suffixe]` (ex. `Fin coté — SAS Exemple`).

## Principe : structure figée, données injectées

P2 ne régénère pas la structure : il rend la **même banque que P1** en lui passant un jeu de
données. Les templates bouclent sur les données si elles existent, sinon restent en mode squelette.
La structure reste donc déterministe ; seules les valeurs varient.

## Rempli automatiquement (mécanique)

- **Hero** : actif brut, dettes, actif net, Gain € YTD (calculé sur les poches disposant d'une valeur 01/01).
- **Bloc Exhaustif** : lignes de détail par catégorie, avec **regroupement multi-poches** (ligne mère
  consolidée + lignes poches `↳`), sous-totaux par catégorie, total par entité.
- **Bloc Répartition** : tableau global consolidé + cards par entité (brut/dettes/net).
- Calculs : Gain € / Gain % / Gain % YTD (financier coté), Non appelé réel (non coté), agrégations.

## Laissé vide volontairement (jugement ou données externes)

- **Donuts d'allocation** (4) : nécessitent la classification fine en 12 classes Rhétorès (méthode
  M1-M5) — c'est l'îlot de jugement de P2, pas encore outillé.
- **Bloc Contexte** (texte macro, faits marquants, 8 indices) : données externes (web, document UBS).
- **Bloc Performance** (courbe d'évolution, comparaison indices) : séries temporelles + indices externes.

## Simplifications connues de cette v1

- **Allocation des dettes** : les dettes ne sont pas réparties dans la colonne « Dettes » de chaque
  catégorie ; elles figurent uniquement dans la ligne « Dettes » (total) et minorent l'actif net.
  v15 les répartit (immo / financier). Règle de répartition à ajouter ensuite.
- **Valorisation non coté** : série trimestrielle par fonds construite depuis l'onglet `NC Flux`
  (Valorisations en palier, à défaut cumul des appels) ; repli sur l'onglet `Non coté` (VL, sinon
  capital appelé) si aucun flux saisi. Le bloc 02 est interactif : bascule portefeuille ↔ fonds,
  pagination Graphique · Détails (synthèse PE / échéancier de flux daté). TRI saisi (colonne
  `TRI (%)`), jamais calculé.
- Aucune donnée client réelle : testé sur 5 profils fictifs (voir `test_excels/`).

## Mise à jour — Donuts du consolidé (rempli)

Les 4 donuts d'allocation sont désormais calculés mécaniquement au niveau consolidé :
- **Classes d'actifs** : agrégation financier coté + non coté par classe Rhétorès.
- **Géographie** : sur les lignes classées « Actions » disposant d'une géographie.
- **Dépositaires** : agrégation par dépositaire (colonne existante).
- **Enveloppes** : AV/Capi (LU vs FR via dépositaire NC) + Compte Titres.

La classification fine (12 classes + géo) est saisie dans 2 colonnes du Financier coté
(`Classe Rhétorès`, `Géographie`) — le jugement M1-M5 se fait à la saisie, l'agrégation reste
déterministe. Reste à outiller : Bloc Contexte et Bloc Performance (données externes).

## Mise à jour — Bloc Performance (rempli)

- **KPIs** : performance YTD %, gain € YTD, performance depuis origine, valeur du portefeuille — calculés depuis l'Excel.
- **Courbe d'évolution** : onglet `Valorisations` (dates bi-mensuelles ; valeur coté à chaque point ;
  valeur non coté **ponctuelle, maintenue en palier** entre deux réévaluations — gestion correcte du PE).
- **Comparaison vs indices** : onglet `Indices` (8 indices figés + YTD %). Le portefeuille est comparé aux benchmarks.

### Alimentation automatique des indices — `fetch_indices.py`
```bash
python3 fetch_indices.py source.xlsx --year 2026   # nécessite yfinance + accès réseau
```
Récupère les YTD des 8 indices via Yahoo Finance et écrit l'onglet `Indices`. À lancer sur un poste
disposant d'un accès internet (le bac à sable de génération peut le bloquer).
