# Chantier UI — dossier de design (2026-07-31, 4ᵉ session)

> Discussion de design DÉDIÉE, décisions consignées AVANT toute ligne de template (REPRISE §4).
> Pièces : `reference/controles_epoque/` (A = INTERAGYR 23/07, B = Gronier 27/07),
> `runs/interagyr_2026-07/reporting_interagyr.html` (C = run moteur corrigé),
> `docs/revue_controle_interagyr_2026-07-30.md`, `docs/spec_tri_blocs_widgets_2026-07-27.md`
> (D28, D29b — cadre déjà arbitré). Inventaire complet réalisé le 30/07 (agent d'exploration,
> comparaison A/B/C bloc à bloc + banque de widgets).

## 0 — Constat de cadrage : il n'y a pas deux « styles » à unifier

L'inventaire tranche la question posée par la revue (§2, point 4) :

- **B (Gronier 27/07) est conforme au bit à la banque actuelle** — mêmes `th`, mêmes chapeaux,
  même ordre de widgets. **C = B moins ce que la donnée n'alimente pas.**
- **A (INTERAGYR 23/07) n'est conforme à rien** : ses en-têtes de tableaux et chapeaux
  n'existent nulle part dans `skill/p1_engine/bank/`. A est une composition d'époque hors
  moteur (ou banque antérieure).

Conséquence de méthode : « unifier les styles » = **décider, trait par trait, lesquels des
traits de A on porte dans la banque**. Il n'y a qu'un seul moteur ; A est un cahier d'intentions,
pas un concurrent. Chaque trait ci-dessous est une décision D-UI-n à arbitrer.

## 1 — D-UI-1 · Canvas PE (W2 graphe + W3 composition + pitch) — **FAIT le 31/07 (D53)**

> **Archéologie (31/07)** : les widgets 2 et 3 n'avaient pas « jamais existé » — ils ont été
> **supprimés le 23/07/2026 « à la demande du CGP »**, et `test_pnc.mjs` vérifiait leur ABSENCE.
> Rétablir n'était donc pas combler un trou mais **renverser une décision d'époque** — arbitré
> explicitement par Thomas le 31/07 (« Rétablir tout »), consigné en **D53** au registre, test
> retourné (absence → présence + bascule exercée), même mouvement que `verifier_pieges.py`.

Découverte confirmée et précisée : **tout est calculé, le CSS existe déjà, seul le markup Jinja
manque.** `performance_nc.html.j2` saute de Widget 1 à Widget 4 (les numéros 2 et 3 manquent
dans les commentaires mêmes).

Calculé par `p2_fill` (L1237–1543) et jamais dessiné :

| Clé | Contenu | Widget cible (existant dans A) |
|---|---|---|
| `bars.labels_js/data_js/line_js/unit/dec/ymin` | série trimestrielle + courbe pré-décalée (_lift 11 %) | W2 `perf_nc_bars` (barres + ligne) |
| `views_js` | N+1 vues (portefeuille + par fonds), KPI/barres par vue | bascule cliquable de A |
| `compo` | multiples MOIC/TVPI/cible + largeurs de barres + poids | W3 `.bench-card` composition |
| `pitch` | texte commercial déterministe (mot pour mot celui de A) | `.pnc-pitch` |
| `summary`, `schedules` | synthèse 11 col. + échéanciers | page « Détails » (option, cf. D-UI-1c) |

CSS déjà présent : `_styles.html:392` (`.pnc-pitch`), `:407-423` (composition), `:430` (page chart).
Le repli au coût existe à deux étages (`_nav_at` L1254 + repli L1327) : les deux barres au coût
d'INTERAGYR **doivent** se dessiner dès que W2 existe.

Proposition : **porter W2 + W3 + pitch + bascule views** dans `performance_nc.html.j2`,
gabarit = le markup de A (A:863-895). La page « Détails » (`summary`/`schedules`) en option
séparée (D-UI-1c), pas dans le premier lot.

- **Arbitrage 1a — ARBITRÉ (31/07, « Rétablir tout ») et FAIT** : W2+W3+pitch+bascule views
  portés dans `performance_nc.html.j2`, gabarit du contrôle A.
- **Arbitrage 1b — FAIT** : `p2_fill` expose désormais la **provenance** de chaque série
  (`cout` par fonds, `cout_note` par vue) ; le titre du graphe dit « · au coût (capital
  appelé) » quand la série est un proxy d'appels — « tout ou partie au coût » si mixte —
  et la note suit la bascule de vue. Vérifié sur le re-run INTERAGYR.
- **Arbitrage 1c — OUVERT** : page « Détails » PE (summary + échéanciers) — hors premier lot,
  à arbitrer plus tard.

## 2 — D-UI-2 · Colonne cible PE + micro-nettoyages du bloc 03 — **FAIT le 31/07**

- **Colonne supprimée** : « Cible (MOIC/TRI) » retirée du tableau fonds (retour aux 8 colonnes
  du contrôle A), la cible vit dans le sous-texte `.cdet`. Le tableau *titres* garde sa
  « Cible (TRI) » — pas de redondance là-bas. Gardé par test_pnc (« colonne Cible absente »,
  « la cible vit dans le sous-texte »).
- **`.cdet` réparé à la racine** : le store était SAIN (`duration_target: 7`, numérique) —
  c'est le lecteur qui n'apposait pas le suffixe. `_duree()` posé dans `lecteur_store.py`,
  même contrat que `_moic()` (« le formatage préserve la valeur ») : `7 → « 7y »`,
  `7.5 → « 7,5y »`, chaîne déjà formatée verbatim. Vérifié : « Cible 2,0x · 7y » au re-run.
- **Chapeau W4 adaptatif** : `p2_fill` calcule `detail_title` depuis les classes réellement
  présentes parmi les fonds (hors titres directs) — « Fonds de private equity » (INTERAGYR),
  « Fonds non cotés » si mélange (fx_simple : PE + dette privée), élision d'/de gérée.
  Gardé par test_pnc (chapeau conforme au motif).

## 3 — D-UI-3 · Colonnes adaptatives par disponibilité de données (principe de Thomas)

État : les 10 colonnes du tableau détail sont **en dur** dans `performance.html.j2:87`
(+1 seule conditionnelle `show_ps_corrige`), le `colspan` calculé à la main à 3 emplacements,
le sous-tableau `acc-lines` **répété 3 fois à l'identique**. Le PE est symétrique (9 en dur).
À l'inverse, le bloc `exhaustif` a le seul mécanisme déclaratif du moteur :
`{% include "columns/cols_" ~ cat %}` + `COLSPANS`/libellés dans `assemble.py:31-33`.

Proposition : **généraliser le mécanisme déclaratif d'`exhaustif`** aux blocs 02/03 — le jeu
de colonnes devient une donnée du manifeste (calculée par p2_fill selon la disponibilité :
une colonne dont toutes les valeurs sont `—` ne s'imprime pas), le template ne décide plus
(droite ligne de D28). Cas nommés par Thomas : « Versements/Retraits/Perf YTD » vides sur
INTERAGYR ; « perf origine » sans sens à deux mois d'historique.

- **Arbitrage 3a+3b — ARBITRÉS le 31/07 (Thomas : « Profils adaptatifs »)** : union des
  colonnes A∪B/C déclarée au manifeste, une colonne 100 % vide ne s'imprime pas — INTERAGYR et
  Gronier gardent chacun leur jeu naturel, par la donnée, pas par le template. Tension E1 du
  Gronier corrigé (colonnes stables + « — ») tranchée en faveur de l'adaptivité.
  **Implémentation : FAITE le 31/07** — `perf["cote_cols"]` calculé par p2_fill (union de
  12 colonnes candidates, `_col_vivante()` : une colonne dont toutes les cellules sont vides
  ne s'imprime pas ; « Valeur » pivot toujours présente ; « Valeur projetée » sur
  `show_ps_corrige`). Template déclaratif : thead en boucle, cellules par macro `cote_cells`,
  sous-tableau ISIN dé-triplé en macro unique `acc_lines_tbl`, colspan dérivé. **Prouvé dans
  les deux sens** : INTERAGYR tombe à 6 colonnes (Date d'inv., Capital investi, Valeur,
  Perf €/% origine — Versements/Retraits/YTD/Nant./ann. disparus d'eux-mêmes, le point 4 de
  la revue est soldé), fx_simple garde ses 8 (YTD vivants). Le jeu de colonnes de CHAQUE
  fixture est gravé au golden (`cote_cols`) : un jeu qui change sans décision est une
  régression.
- **D-UI-9 (arbitrage Thomas 31/07, résolution de la tension E2) — FAIT** : le détail ligne à
  ligne RESTE (« le cœur du reporting ») dans les deux modes, mais **« garder les lignes et
  caviarder les valeurs aberrantes »** — une perf de ligne au-delà de ±100 %
  (`PERF_LIGNE_MAX_PCT`, ajustable) est réputée calculée sur données assureur manquantes
  (les +350 % de Gronier) : elle s'affiche « — », la ligne reste, le run signale ⚠ avec les
  valeurs écartées. Le vrai remède nommé par Thomas : **Modified Dietz sur mouvements datés**
  — chantier de données, lié au contrat Valorisations+Mouvements de E7.

## 4 — D-UI-4 · Double donut coté/non coté

Correction d'inventaire : **le double donut existe déjà et C le dessine** (`donuts_sup`,
arcs Coté 95 % / Non coté 5 % + classes en anneau intérieur — même forme que A). Le grief
résiduel du point 2b de la revue est donc réduit à la taxonomie de l'anneau intérieur
(« Court terme » fourre-tout → D-UI-5) et aux enveloppes (corrigées le 30/07). **Proposition :
clore 2b sans travail de template**, sauf objection sur pièce.

## 5 — D-UI-5 · Dépliage « Court terme » (G6) — **FAIT le 31/07 (option 1)**

> Réalisation : `classe_liquidite()` posée comme **règle unique** — donut Classes
> (« Monétaire » / « Liquidités », « Court terme » disparaît de l'affichage) et widget
> Disponibilités (Monétaire quasi-liquide + Liquidités) consomment la même fonction. Trous de
> la spec §4.b comblés au passage : lignes « Court terme » réintégrées au widget, préfixes
> « Trésorerie » / « Solde en espèces » captés. SRI et couleur « Liquidités » ajoutés.
> Vérifié au re-run INTERAGYR : zéro « Court terme » au rendu, Liquidités + Monétaire vivants.

Mécanique actuelle (`p2_fill.py:1798-1801`) : l'anneau Classes fusionne « Monétaire » DANS
« Court terme » et y AJOUTE la catégorie patrimoniale `liquidites` (comptes hors contrat).
Trois options :

1. **Dépliage à deux entrées** : « Monétaire » (fonds monétaires) / « Liquidités » (espèces,
   comptes courants, liquidités de contrats) — « Court terme » disparaît.
2. Dépliage à trois (Monétaire / Liquidités de contrats / Comptes courants) — granularité
  maximale, risque de miettes au donut.
3. Statu quo légendé (infobulle).

Recommandation : option 1 — deux mots que le client comprend, zéro fourre-tout.
**Incohérence liée à corriger dans le même geste** (spec_tri_blocs §4.b, déjà écrit) : le
widget Disponibilités teste `cls == "Monétaire"` + préfixes de libellé et **exclut à tort les
lignes classées « Court terme »** ; « Trésorerie »/« Solde en espèces » non captés. La taxonomie
décidée ici doit être LA règle unique, partagée donut/Disponibilités (une fonction, deux
consommateurs).

## 6 — D-UI-6 · Repli enveloppe bruyant — **FAIT le 31/07**

> Réalisation : cascade externalisée en table `ENV_TABLE` (formes exactes + préfixes ; ajouter
> une enveloppe = une ligne + sa couleur). **Découverte en passant : l'assurance-vie vivait du
> repli** — aucune forme « av »/« assurance vie » n'était reconnue ; elle est désormais NOMMÉE.
> L'inconnu va en « Autre (à qualifier) » (bordeaux au donut) + ⚠ au rapport de run listant
> les natures verbatim. Contrôle négatif exercé (« Plan Épargne Logement » → Autre + signalé).

`envelope()` (p2_fill.py:76-85) : cascade en `if` littéraux, **repli final silencieux vers
« Assurance-vie FR/LU »** — le vice qui a menti au donut jusqu'au 30/07. Proposition :

- nature non reconnue → catégorie visible **« Autre (à qualifier) »** au donut + signalement
  K3 au rapport de run (échec bruyant L5, jamais de défaut silencieux) ;
- externaliser la cascade en table (la fonction + `ENV_COLORS` doivent s'éditer ensemble
  aujourd'hui — PER/PEE/Nominatif administré coûteront une ligne au lieu d'un patch).

## 7 — D-UI-7 · Bloc 02 : courbe « 2 points » nouveau client — **VALIDÉ et FAIT le 31/07**

Pour un client sans historique D50 : courbe dégradée à 2 points (capital investi à la date
d'invest → valeur à l'arrêté), **affichée comme telle** (« depuis l'investissement », pas de
prétention d'historique) — même philosophie que le PE au coût. Le canal éditorial (commentaire
de gestion) reste un chantier séparé (spec courte à venir, hors UI).

**Réalisation (31/07)** — précision d'inventaire : le template ne dessine QUE `fin_line_js`
(« Poche financière ») ; `data_js` (patrimoine global) est calculé et jamais dessiné. Le repli
alimente donc la poche cotée : sans AUCUNE Valorisation, 2 points `[capital investi coté,
valeur à l'arrêté]` aux mois du premier investissement et de l'arrêté (2 mois distincts
minimum), `degraded=True`, note de sincérité sous le canvas (« Courbe simplifiée — deux
points… s'enrichira à chaque arrêté »), garde d'échelle ±2,5 % réutilisée. `curve_end_eur`
volontairement NON posé (le QC « courbe ≈ actif net » juge le patrimoine global, pas la poche).
Filet : **fixture `fx_courbe2pts`** créée (fx_simple sans Valorisations — aucune fixture
n'exerçait le repli), golden étendu d'une clé `curve_degraded` jugée sur CHAQUE fixture (un
repli qui cesse de s'annoncer est une régression muette), store de vérité dérivé (D47,
`validation_app/ingest` remonté en lecture seule), golden 8/8, **L3a 8/8 à l'octet**.
Vérifié sur le re-run INTERAGYR : 05/26 → 07/26, 4,50 → 4,48 M€, échelle figée (variation
−0,4 % < 2 %), QC 9/9, actif brut inchangé.

## 8 — D-UI-8 · Conventions d'affichage — **ARBITRÉ et FAIT le 31/07**

- **Chapeaux du bloc 00 — arbitrage Thomas : « Reporting au [date] »** (pas « T3 2026 »).
  FAIT : `contexte.html.j2` compose « Reporting au {{ date_display }} - Faits marquants » /
  « … - Performance des indices ». Les trois conventions d'époque (S29 2026 / T2 2026 / T3-26)
  sont mortes.
- **Libellés partenaires — arbitrage Thomas : la forme du STORE fait foi** (« UBS (Dauphine
  AM — Équilibré) »), jugée plus esthétique que la forme d'époque. Zéro code — convention
  consignée, le store est déjà la source. L'agrégation E6b du donut (parenthèse à chiffre =
  contrat) reste compatible : les mandats à texte restent distincts.

## 9 — Ordre de réalisation proposé

1. **D-UI-1** canvas PE (W2+W3+pitch+views) — plomberie prête, CSS prêt, gabarit dans A.
2. **D-UI-2** colonne cible + chapeau adaptatif + fix `.cdet` amont.
3. **D-UI-5 + D-UI-6** taxonomie Court terme (règle unique donut/Disponibilités) + enveloppe
   bruyante — même zone de code.
4. **D-UI-3** colonnes adaptatives (le plus gros morceau — refactor déclaratif des blocs 02/03,
   dé-triplication d'`acc-lines`).
5. **D-UI-7** courbe 2 points (si validée) + **D-UI-8** conventions.
6. Re-run INTERAGYR + confrontation aux deux contrôles d'époque (le « troisième juge ») après
   chaque lot ; golden/L3a/QC avant-après à chaque étape (réflexes constants).

> Statut initial : PROPOSÉ. Mise à jour 31/07 : blocs 1–4 FAITS (D-UI-1/D53, D-UI-7, D-UI-2,
> D-UI-5/6) ; restent D-UI-3, D-UI-8, arbitrage 1c.

## 10 — Enseignements du Gronier corrigé (31/07, pièce archivée — E1–E8)

> Thomas a fourni un Gronier **corrigé forme + fond** (« plus qualitatif ») avec la doctrine :
> la structure du contrôle INTERAGYR « met tout le monde d'accord », le style Gronier est
> hyperspécifique. Diff complet D↔B dépouillé (196 lignes, 14 hunks — révision chirurgicale,
> aucun bloc créé/renommé). Pièce : `reference/controles_epoque/Reporting_NicolasG_T2_2026_corrige_2026-07-31.html`.

- **E1 (pèse sur D-UI-3)** : le Gronier corrigé garde les 10 colonnes À L'IDENTIQUE et dégrade
  les CELLULES (« — » sur l'origine des poches FAS) — sa doctrine implicite est « colonnes
  stables, cellules dégradables », PAS le masquage. Tension ouverte avec la demande de revue de
  Thomas (« supprimer les colonnes sans données ») → arbitrage nécessaire avant D-UI-3.
- **E2** : la simplification n'est pas structurelle mais de PROFONDEUR — 100 % des blocs et
  colonnes gardés, mais les 13 sous-tableaux ISIN et les `cdet` de mandat retirés. Tension avec
  le « détail ligne à ligne = cœur du reporting » (revue INTERAGYR) → arbitrage par MODE ?
- **E3** : un widget vide se SUPPRIME (« Arbitrages de la période » retiré au lieu du
  placeholder « Aucun arbitrage ») ; une glose ne décrit jamais une interaction absente.
- **E4** : toute métrique à périmètre ambigu porte son périmètre en sous-titre — « SRI 4/7 ·
  moyen pondéré **(coté + non coté)** » vs « SRI 4/7 · **portefeuille coté seul** ». Absent de
  la banque, transposable immédiatement.
- **E5** : une colonne constante par support n'informe pas — Matières premières « Perf % »
  (répétée) → « **% Contrat** » (poids). Banque à corriger.
- **E6** : hiérarchie contrat → poche rendue dans les TABLEAUX (lignes ↳ indentées dans
  Disponibilités, sous-total recomposable à l'œil) ; AGRÉGATION par partenaire dans les DONUTS
  (les deux Wealins fusionnés à 45 %). Deux évolutions de banque.
- **E7** : courbe coté par MORCEAUX à sauts de flux (segments pointillés atténués, montant du
  flux sous le segment, % au-dessus) — seul apport de forme neuf, coûteux, exige le contrat de
  données Valorisations + Mouvements datés (lien D50). Chantier dédié.
- **E8 — défauts de la pièce** (consignés au README des contrôles) : écart 300 000 € donut
  vs Historique (926 671 € vs 626 671 €, hérité de B, non corrigé) ; colonne « Cible
  (MOIC/TRI) » conservée contre D-UI-2 (le `cdet` porte pourtant déjà la cible — la banque a
  raison sur le fond) ; W2/W3 PE absents (la banque est en avance, D53 — ne pas régresser) ;
  « Court terme » conservé au donut (D-UI-5 assumé comme divergence d'affichage du moteur,
  validée par Thomas en séance).
