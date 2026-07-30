# Chantier UI — dossier de design (2026-07-30, 4ᵉ session)

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

## 1 — D-UI-1 · Canvas PE (W2 graphe + W3 composition + pitch) — premier candidat confirmé

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

- **Arbitrage 1a** : W2+W3+pitch+views — go ?
- **Arbitrage 1b** : titre du graphe. A : « Valorisation trimestrielle du non coté — depuis
  T2-26 ». En mode repli au coût, le titre DIT « au coût » (cohérence 2-ter §2 : jamais faire
  passer un cumul d'appels pour une valorisation).
- **Arbitrage 1c** : page « Détails » PE (summary + échéanciers) — maintenant, plus tard, jamais ?

## 2 — D-UI-2 · Colonne cible PE + micro-nettoyages du bloc 03

- La cible apparaît **deux fois** en B/C : colonne dédiée « Cible (MOIC/TRI) » ET sous-texte
  `.cdet` (« … · Cible 2,0x · 7y »). A n'a que le sous-texte. Proposition : **supprimer la
  colonne**, garder le sous-texte (retour à 8 colonnes, aligné sur A).
- Bug amont repéré au passage : le `.cdet` de C est tronqué (« · 7 » au lieu de « · 7y ») —
  la durée perd son unité entre store et rendu (le template ne formate pas, L1482-84 : valeurs
  pré-formatées attendues). À corriger côté lecteur/store, hors template.
- Chapeau W4 : B/C disent « Fonds de private equity — détail par véhicule » même si le
  portefeuille porte de la dette privée ; le `pitch` sait déjà nommer les 4 classes (`_LBLNC`
  L1429). Proposition : titre adaptatif sur le modèle du seul précédent existant (`geo_title`,
  L751-52).

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

- **Arbitrage 3a** : règle de masquage — mécanique pure (colonne 100 % vide → masquée) ou
  seuils métier (ex. « perf origine » exige ≥ N mois d'historique) ? Recommandation : mécanique
  pure d'abord (zéro faux jugement), seuils métier en second temps si besoin.
- **Arbitrage 3b** : A porte 3 colonnes que B/C n'ont pas (Nant., Perf %, Perf % ann.) et B/C
  en portent 4 que A n'a pas (Versements, Retraits, Perf YTD ×2). Jeu canonique = union avec
  masquage adaptatif, ou jeu B/C conservé + masquage ? Recommandation : union — c'est
  l'adaptivité qui fait le tri, pas le template.

## 4 — D-UI-4 · Double donut coté/non coté

Correction d'inventaire : **le double donut existe déjà et C le dessine** (`donuts_sup`,
arcs Coté 95 % / Non coté 5 % + classes en anneau intérieur — même forme que A). Le grief
résiduel du point 2b de la revue est donc réduit à la taxonomie de l'anneau intérieur
(« Court terme » fourre-tout → D-UI-5) et aux enveloppes (corrigées le 30/07). **Proposition :
clore 2b sans travail de template**, sauf objection sur pièce.

## 5 — D-UI-5 · Dépliage « Court terme » (G6)

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

## 6 — D-UI-6 · Repli enveloppe bruyant

`envelope()` (p2_fill.py:76-85) : cascade en `if` littéraux, **repli final silencieux vers
« Assurance-vie FR/LU »** — le vice qui a menti au donut jusqu'au 30/07. Proposition :

- nature non reconnue → catégorie visible **« Autre (à qualifier) »** au donut + signalement
  K3 au rapport de run (échec bruyant L5, jamais de défaut silencieux) ;
- externaliser la cascade en table (la fonction + `ENV_COLORS` doivent s'éditer ensemble
  aujourd'hui — PER/PEE/Nominatif administré coûteront une ligne au lieu d'un patch).

## 7 — D-UI-7 · Bloc 02 : courbe « 2 points » nouveau client (à valider — revue §2-quater 3)

Pour un client sans historique D50 : courbe dégradée à 2 points (capital investi à la date
d'invest → valeur à l'arrêté), **affichée comme telle** (« depuis l'investissement », pas de
prétention d'historique) — même philosophie que le PE au coût. Le canal éditorial (commentaire
de gestion) reste un chantier séparé (spec courte à venir, hors UI).

## 8 — D-UI-8 · Conventions d'affichage (zéro/quasi-zéro code)

- **Chapeaux du bloc 00** : seul endroit où « T3-26 » subsiste (les titres de section disent
  déjà « Reporting au 15 juillet 2026 » partout). Trois conventions coexistent dans les pièces :
  A « S29 2026 », B « T2 2026 », C « T3-26 ». À arrêter : recommandation **« T3 2026 »**
  (forme longue de B), soit `period_short` reformatté.
- **Libellés partenaires** : A « UBS (Dauphine — Équilibré) » vs C « UBS (Dauphine AM — … ) » —
  nommage du store, à trancher une fois et consigner.

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

> Statut : PROPOSÉ — en attente d'arbitrage de Thomas, décision par décision. Rien n'est
> implémenté à la date de ce document.
