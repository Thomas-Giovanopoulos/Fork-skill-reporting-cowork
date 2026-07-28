# Classification des actifs

> Les 12 classes d'actifs Rhétorès, la méthode d'identification M1-M5, les règles de géographie,
> le scan portefeuille ligne par ligne. Référencé depuis le SKILL.md (Étape 4 du workflow).

---

## Les 12 classes d'actifs Rhétorès

La convention Rhétorès distingue 12 classes d'actifs distinctes :

```
1.  Actions                  — Actions cotées, ETF actions, fonds actions actifs
2.  Obligations              — État, corporate, green bonds, high yield, aggregate, émergents
3.  Produits structurés      — Tout PS quel que soit le sous-jacent
4.  Fonds euros              — Catégorie distincte des obligations (PB annuelle stable)
5.  Alternatifs              — Hedge funds, absolute return UNIQUEMENT
6.  Matières premières       — Or physique, métaux, énergie (via fonds dédié)
7.  Crypto                   — Bitcoin, Ethereum, fonds crypto (ligne distincte, plus dans Alternatifs)
8.  Monétaire                — Inclut liquidités investies (Money Market funds)
9.  Private Equity           — LBO, growth, co-invest, secondaire, fonds de fonds
10. Dette privée             — Direct lending, mezzanine, distressed debt
11. Immo non coté            — UNIQUEMENT investissement (exclure RP/RS/Usage)
12. Infrastructures          — Fonds d'infrastructure non cotés
```

**Attention** : "Alternatifs" ≠ tout ce qui est complexe. Seuls hedge funds et absolute return.
Un fonds obligataire flexible n'est PAS un alternatif. La crypto n'est PLUS dans Alternatifs —
elle a sa propre classe (#7).

**Obligations** : toutes les sous-catégories (État, corporate, green bonds, high yield, aggregate,
émergents) doivent être identifiées fonds par fonds dans la classification fine.

**Fonds euros — valorisation** : revalorisé une seule fois par an, lors du versement de la
participation aux bénéfices (généralement janvier/février N+1 pour l'année N). Conséquence :
au 31/03/N ou 30/06/N, la valeur reste celle du 31/12/N-1 (valeur dernier PB connu). Pas d'asterisk
ou de note "valorisation indicative". Performance YTD = 0% jusqu'au prochain versement de PB.

**Immo non coté** : applique uniquement aux investissements (locatif, SCPI, OPCI, SCI de rendement).
Exclure résidence principale, résidence secondaire, biens d'usage personnel. Ces derniers apparaissent
dans le patrimoine immobilier mais pas dans l'allocation d'actifs.

**Infrastructure** : applique uniquement aux fonds non cotés. Un fonds thématique d'infrastructure
coté (ex: ETF Global Infrastructure) reste classé en Actions International.

---

## Méthode d'identification M1-M5

Pour chaque position d'un portefeuille, appliquer la méthode dans cet ordre de priorité :

### M1 — Morningstar
Consulter la fiche Morningstar du fonds (https://www.morningstar.fr).
Lire la classification Morningstar Global Category et l'allocation par classe d'actifs.

### M2 — Benchmark de référence
Si M1 incomplet, regarder le benchmark de référence du fonds dans son prospectus ou DICI.
Un benchmark "MSCI World" → Actions. "Bloomberg Global Aggregate" → Obligations. Etc.

### M3 — Prospectus / DICI
Lire le document d'information du fonds (objectif, stratégie, allocation cible).

### M4 — Analyse du nom du fonds
Lecture sémantique du libellé :
- "Money Market" / "Monétaire" → Monétaire
- "Bond" / "Obligations" / "Fixed Income" / "Aggregate" / "Credit" → Obligations
- "Equity" / "Actions" / "Stocks" → Actions
- "Gold" / "Or" / "Physical Metals" → Matières premières
- "Bitcoin" / "BTC" / "Crypto" / "Blockchain" → Crypto
- "Real Estate" / "Property" → Immo non coté (si non coté) ou Actions (si REIT coté)
- ⚠ Les libellés "Tobam BTC-..." sont des fonds **crypto**, même si UBS les classe en Monétaire/Alternatifs
- ⚠ "iShares Bitcoin Trust ETF" est **crypto**, même si UBS le classe en Actions Monde

### M5 — Flag "International ⚠"
En dernier recours, classer comme "International" et flagger pour validation Tristan.

---

## Règles de géographie

### Périmètre de la géographie

La géographie ne s'applique **que** sur :
- **Actions** : par fonds, selon la concentration géographique du portefeuille
- **Produits structurés** : selon le sous-jacent du produit (PAS l'émetteur)
- **Private Equity** : selon la cible d'investissement du fonds

### Classes sans géographie

Pour les autres classes (Obligations, Monétaire, Fonds euros, Matières premières, Crypto,
Alternatifs, Dette privée, Immo non coté, Infrastructures), la géographie n'est PAS calculée.
Ces classes apparaissent dans le donut "Allocation classes d'actifs" mais pas dans le donut
"Géographie".

### Règle pour les fonds Actions — Règle des 60%

Si un fonds Actions a une concentration géographique > 60% sur une zone, classer entièrement
sur cette zone. Sinon → "International / Monde".

Exemples validés :
- Franklin Technology Fund (95% US) → US
- DPAM World Sustainable (40% US, 25% Europe, 35% reste) → International / Monde
- CPR Gold Miners (40% US, 30% Canada, 20% Australie) → International / Monde

### Règle pour les Produits structurés

Géographie selon le sous-jacent du produit, PAS selon l'émetteur.
Exemples :
- Barclays structuré sur CSI 300 → Émergents (Chine)
- JPMorgan structuré sur iTraxx Europe → Europe
- BNP Paribas structuré sur S&P 500 → US

Hiérarchie de recherche du sous-jacent :
1. Lire le nom du produit (suffixes connus : SHSZ300 = Chine ; iTraxx = Europe ; COIN-MSTR = US ; etc.)
2. ISIN sur le site de l'émetteur
3. Term sheet du produit
4. Sinon → "International ⚠"

### Note sur la Suisse

La Suisse est traitée comme **zone géographique distincte** ("Europe hors UE" — Suisse spécifiquement).
Ne pas la regrouper avec "Europe" qui désigne la zone Euro.

---

## Outil — Scan portefeuille ligne par ligne

### Quand l'utiliser
Pour produire la classification fine d'une poche (ex: poche FID Dauphine AM, FAS Rhétorès, etc.)
lors de la production d'un nouveau reporting ou lors d'une revue d'allocation.

### Format obligatoire : tableau HTML visuel

Colonnes : `# | Libellé | ISIN | Classe UBS | Classe Rhétorès (badge coloré) | Géo | Montant € | Note/Raisonnement`

- Sections par catégorie UBS dans l'ordre (Actions / Obligations / PS / etc.)
- Ligne navy "TOTAL" avec montant et variance vs relevé
- Reclassifications ⚠ surlignées en jaune avec badge rouge "⚠ UBS mal classé"

### Raisonnement à fournir par ligne

Pour chaque position, indiquer dans la colonne "Note" :
- Méthode utilisée (M1, M2, M3, M4, M5)
- Si reclassement par rapport à la classification UBS, justifier

### Alertes systématiques

Toujours vérifier ces cas connus :
- Fonds "Tobam BTC-..." → Crypto (UBS les classe parfois en Monétaire ou Alternatifs)
- iShares Bitcoin Trust ETF → Crypto (UBS le classe en Actions Monde)
- ETF or physique → Matières premières (UBS les classe parfois en Actions)
- REITs cotés → Actions (et non Immo non coté)
- Fonds thématiques cotés → Actions International (et non Infrastructure / Matières premières)

---

## Sources de référence externes

Pour vérifier une classification, consulter dans cet ordre :
1. **Morningstar** (https://www.morningstar.fr) — fiche fonds et allocation
2. **Quantalys** (https://www.quantalys.com) — vue agrégée et benchmark
3. **Boursorama** (https://www.boursorama.com) — fiche fonds rapide
4. **Site de l'émetteur** — prospectus, DICI, document de référence
5. **Bloomberg / Refinitiv** — pour les positions complexes (PS, obligations)
