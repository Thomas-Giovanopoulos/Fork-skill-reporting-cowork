# Reporting Family Office Rhétorès Finance — VERSION ALTERNATIVE (pipeline déterministe)

> Skill de production de reportings patrimoniaux consolidés de type Family Office. Sa particularité :
> il sépare strictement la **structure** (figée, produite par code) des **données** (issues d'un Excel
> client) et du **contexte de marché** (produit une fois par période). Objectif : un reporting dont la
> structure ne « se tord » jamais quand les données changent — mêmes données → même reporting, toujours.

---

## 1. Ce que fait le skill

À partir d'un fichier **Excel source** rempli par le conseiller (CGP) et d'un **contexte de marché** de
période, le skill génère un **reporting HTML autonome** : Hero (chiffres clés), contexte de marché,
étude de performance, rendement annuel historique, répartition patrimoniale (tableau + donuts + cards),
et tableau patrimonial exhaustif. Tout le « contenant » est déterministe ; seules les valeurs varient.

Chaîne complète :

```
Excel client  ─(excel_to_manifest)→  manifest.json  ─(assemble = P1)→  squelette vide
                                                     ─(p2_fill   = P2)→  reporting rempli
contexte/<période>.json  ─────────────────────────────────────────────↗  (macro, faits, indices)
```

---

## 2. Principe — déterminisme par phases (P0 → P4)

| Phase | Régime | Sortie |
|---|---|---|
| **P0 Cadrage** | jugement humain | Excel source (onglet `Entités` rempli) |
| **P1 Structure** | déterministe, par code | squelette HTML vide (assembleur + banque de modules) |
| **P2 Remplissage** | automatisé (+ 1 îlot de jugement = la classification, saisie en amont) | reporting rempli |
| **P3 Cohérence** | vérification | auto-contrôle comptable (identités) |
| **P4 Polissage** | éditorial, additif | contexte de période (macro + faits), produit une fois |

**Règle de ré-entrée** : toute modification de données relance P2, jamais P1. La structure validée en
P1 est un invariant. C'est ce qui garantit que « les chiffres changent, la structure tient ».

---

## 3. Blocs du reporting

L'ordre est canonique et la **numérotation est calculée automatiquement** selon les blocs activés :

1. **Hero** — Actif brut, Dettes, Actif net, Gain € YTD (couleur au signe).
2. **Contexte de marché** — texte macro (5 §, gras/doré), faits marquants (5), **panorama technique
   des 8 indices** (variation en points/€ + % YTD, sans portefeuille). Vient du store de période.
3. **Étude de la performance (coté)** — 4 KPIs, **courbe poche financière vs équivalent benchmark**
   (benchmark du profil de risque rebasé sur la poche financière), + carte de comparaison au benchmark.
4. **Performance non coté (Private Equity)** *(conditionnel — seulement si non coté)* — barres
   trimestrielles dès **T4-25** (décalage d'un trimestre du PE) + ligne **benchmark de pairs** MSCI
   Private Capital, pondéré par l'allocation ; sleeve PE décomposé par stratégie (Buyout/Growth/Venture)
   selon le profil de risque. Étiquettes +% par segment.
5. **Rendement annuel** *(conditionnel — seulement si historique)* — performance par année depuis
   l'entrée en relation. Rendu **adaptatif** : ≤ 5 années → cartes annuelles ; > 5 → bar chart +
   encart meilleure/pire année avec contexte.
5. **Répartition patrimoniale** — tableau global consolidé (dettes réparties par catégorie), 4 donuts
   (classes, géographie, dépositaires, enveloppes), cards par entité (montants en unité adaptative).
6. **Tableau exhaustif** — détail ligne à ligne par entité, avec regroupement multi-poches.
7. **Footer**.

---

## 4. Fichier Excel source — conventions

- **Onglet `Entités`** : `id` · `label` · `type (pp/holding)` · `onglet (suffixe)`. Une seule PP, en tête.
- **Onglets catégorie** : nommés `[Catégorie] — [suffixe]` (`Liq`, `Immo`, `Fin coté`, `Non coté`, `Dettes`).
  - *Financier coté* porte aussi `Classe Rhétorès` (12 classes) et `Géographie` (Actions).
  - *Non coté* porte `Classe Rhétorès` (PE / Dette privée / Immo non coté / Infrastructures).
  - *Dettes* porte `Adossement (catégorie)` (à quelle catégorie la dette se rattache).
- **Onglet `Valorisations`** : valeur du financier coté à dates bi-mensuelles ; valeur non coté
  **ponctuelle** (saisie aux dates de réévaluation, maintenue en palier — gestion du PE).
- **Onglet `Historique`** *(optionnel)* : `Année` · `Rendement YTD (%)` · `Commentaire` (années
  notables). Sa présence active le bloc Rendement annuel.

La classification (12 classes, géo) et l'adossement des dettes sont **saisis dans l'Excel** : le seul
jugement (méthode M1-M5) est ainsi capturé en donnée, et l'agrégation reste déterministe.

---

## 5. Contexte de marché — store par période

Le macro, les faits marquants et les indices ne dépendent pas du client : ils sont produits **une
fois par trimestre** dans `contexte/<période>.json` (ex. `contexte/T2-26.json`) et **réutilisés pour
tous les clients** de la période. Gain de calcul + cohérence entre clients. Format des indices :
`{name, var, ytd}`. Texte macro : balises `<strong>` (terme clé, navy) et `<em>` (chiffre, doré).

---

## 6. Commandes

```bash
pip install -r p1_engine/requirements.txt            # jinja2, jsonschema, openpyxl, yfinance

python3 p1_engine/lint.py            source.xlsx                          # contrôle de saisie (pré-vol)
python3 p1_engine/fetch_indices.py   contexte/T2-26.json --year 2026      # indices via yfinance (réseau requis)
python3 p1_engine/excel_to_manifest.py source.xlsx manifest.json \
        --period-long "T2 2026" --period-short "T2-26" --date 2026-06-30 --date-display "30 juin 2026"
python3 p1_engine/p2_fill.py         source.xlsx manifest.json consolide_[Client].html
```

`p2_fill` lance automatiquement le lint en pré-vol et l'auto-contrôle comptable en fin.

---

## 7. Règles déterministes notables

- **Numérotation des blocs** : calculée par position ; activer/retirer un bloc renumérote tout seul.
- **Unité adaptative** (cards + courbe) : K€ si patrimoine < 1 M€, sinon M€ (2 décimales).
- **Répartition des dettes** : chaque dette est ventilée dans sa catégorie d'`Adossement` (tableau global).
- **Courbe** : patrimoine global = financier (série Valorisations) + actif non-financier net constant.
- **Donut géographie** : si aucune action en direct, état « Non applicable » (pas d'anneau vide).
- **Comparaison Performance** : Portefeuille vs **benchmark du profil de risque** du client (Prudent / Équilibré / Dynamique — pondérations MSCI World / Obligations / Monétaire figées par profil), avec détail des composantes (pastille + barre) et texte explicatif. Profil saisi dans l'onglet `Entités` (repli `--profile`, défaut Équilibré). Échelle absolue (40 % = barre pleine).
- **Format Rendement annuel** : `HIST_CARDS_MAX = 5` (constante dans `p1_engine/p2_fill.py`) — ≤ 5
  années affichées (historique + année courante) → cartes ; au-delà → bar chart. Purement déterministe.

---

## 8. Contrôles qualité

- **Lint (`lint.py`)** — avant génération : 1 PP en tête, id uniques, colonnes numériques, classes/géo/
  adossement dans les valeurs autorisées (détection de typo), dépositaires. Erreurs bloquantes + avertissements.
- **Auto-contrôle comptable (dans `p2_fill`)** — après génération : Σ brut catégories = actif brut,
  Σ dettes réparties = dette totale, Σ nets entités = actif net, donut classes = financier, donuts ≈ 100 %.
  Résultat affiché + tracé dans le HTML (`<!-- QC: … -->`).

---

## 9. Arborescence

```
reporting-fo-rhetores-alt/
├── SKILL.md
├── README.md                      (ce fichier)
├── assets/Reporting_data_template.xlsx   (template source à dupliquer par client)
├── contexte/T2-26.json            (exemple de store de période)
├── references/                    (9 fichiers de règles métier, contenu d'origine)
└── p1_engine/
    ├── assemble.py                (P1 — manifeste → squelette)
    ├── excel_to_manifest.py       (Excel → manifeste)
    ├── p2_fill.py                 (P2 — Excel → reporting rempli + auto-contrôle)
    ├── lint.py                    (contrôle de saisie)
    ├── fetch_indices.py           (indices via yfinance → store)
    ├── manifest.schema.json       (contrat du manifeste)
    ├── bank/                      (banque de modules HTML/Jinja : base, blocs, fragments, colonnes, CSS)
    └── README.md, README-pont-P2.md
```

---

## 10. Ce qui reste manuel (P4, éditorial)

- Le **store de période** : texte macro (5 §) et faits marquants (5), rédigés une fois par trimestre
  (recherche web). Les indices peuvent être automatisés via `fetch_indices.py`.
- La **classification** des fonds (12 classes + géo), l'**adossement** des dettes et les **commentaires**
  d'années notables : saisis dans l'Excel. C'est l'unique jugement humain ; tout le reste est mécanique.

---

## Crédits

Version alternative (pipeline déterministe) réalisée par **Thomas Giovanopoulos**, en prenant pour
base les travaux de **Tristan** (règles métier validées, structure du reporting, template de collecte).
