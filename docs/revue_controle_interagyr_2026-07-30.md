# Revue du run INTERAGYR contre le contrôle (`consolide_Interagyr.html` du 23/07)

> 2026-07-30. Thomas a fourni le reporting produit « à l'époque » avec les mêmes documents — le
> contrôle — et cinq points de revue. Ce document trace chaque point à sa CAUSE. Verdict
> d'ensemble : les cinq points se répartissent en **trois familles** qui n'appellent pas le même
> traitement — un **bug du run** (la jointure nature), des **données absentes des entrées**, et
> des **écarts de style moteur vs contrôle**. Presque rien n'est du code perdu.
>
> Au positif, mesuré : pipeline de bout en bout en **11 minutes contre ~25** à l'époque — la
> vitesse est un effet de bord de la structure (parallélisme réel + priming), pas un objectif.

## 0 — La cause racine du point 2 (et d'une partie du 4) : LA JOINTURE NATURE S'EST CASSÉE

Diagnostic établi sur le code (p2_fill L614-627) : le moteur joint les lignes classées à leur
contrat par `norm("{nature} — {banque}")`. Or la nature a fait un aller-retour destructeur :

```
structure : « Compte Titres »  →  ancre : envelope_type = cto  →  lecteur : « CTO »
Fin coté (façade)  : clé « CTO — UBS (De Pury Pictet) »
Lignes  (subagent) : clé « Compte Titres — UBS (De Pury Pictet) »   →  AUCUN HIT
```

Conséquence en cascade, silencieuse : `_geo_from_lines` reste False, les **53 lignes classées
n'alimentent ni le donut Classes, ni la géo, ni le SRI pondéré** — le moteur retombe sur la
« Classe dominante » de la ligne Fin coté (absente des ancres) et sur les replis par classe.
C'est exactement les symptômes du point 2 (donuts, « aucune action en direct ») et une partie du
point 4 (colonnes vides). **Pourquoi L3a ne l'a pas vu** : les fixtures écrivent des natures
(`CTO`, `AV`) qui survivent à l'aller-retour code→affichage. « Compte Titres » ne survit pas —
le hasard de vocabulaire de l'A2, matérialisé.

**Correctif** : champ `nature` VERBATIM optionnel sur `financierCoteEntry` (et l'ancre/l'apply le
portent) ; le lecteur émet la nature verbatim quand elle existe, le code d'enveloppe sinon.
Entrée au registre au moment de la pose. Re-run : donuts, géo et pondération SRI doivent revenir.

## 1 — Les cinq points, un par un

| # | Constat de Thomas | Cause | Famille | Traitement |
|---|---|---|---|---|
| 1a | « Reporting au DATE » redevenu « T3 2026 » | Les en-têtes composent `— {{period_long}}` : le contrôle passait simplement `period_long = "Reporting au 16 juillet 2026"`. | argument de run | Zéro code — convention d'affichage à fixer (CGP) et à documenter dans SKILL.md. |
| 1b | Textes/macros Dauphine absents | Le contrôle injectait les sections ACTUALITÉS des relevés Dauphine comme commentaire. Le moteur n'a **jamais** eu ce canal — c'est l'éditorial (P4), fait main à l'époque. | canal éditorial manquant | Petit chantier : les subagents captent DÉJÀ ces sections (`unrecognized_data`) — il manque le logement (commentaire de gestion du run) et l'injection P4. À spécifier, lien I3 (veille documentaire). |
| 2a | SRI 4 → 6 | Double cause : la jointure cassée (§0 — le SRI pondéré par ligne n'a jamais tourné) ET **aucune ligne extraite ne porte `sri`** (les subagents ont résolu class/geo au référentiel, pas sri) → repli par classe, Actions=6. | bug + donnée | §0 + **enrichissement déterministe à l'apply** : sri/class/geo complétés depuis `isin_referentiel_v0.csv` quand absents — la « priorité absolue » du référentiel est déjà la règle, l'apply peut l'appliquer mécaniquement (responsabilité (e), à ajouter à `appliquer_diffs`). |
| 2b | Donut Classes confond coté/non coté | Deux choses : la jointure (§0) appauvrit le donut ; ET le moteur Gronier a un donut UNIQUE où le non coté entre par classes (L642), là où le contrôle a un **double donut à arcs Coté/Non coté** — une forme que le moteur n'a jamais eue. | bug + style | §0 d'abord, puis décision de design : porter le double donut au moteur (chantier UI, avec le point 4). |
| 2c | Géo « aucune action en direct » | La jointure (§0). Les 43 lignes avec géographie n'ont jamais atteint `agg_geo`. Le libellé même (« Géographie — Actions » vs « Exposition géographique ») bascule avec `_geo_from_lines`. | bug | §0. Re-run attendu : « Exposition géographique » alimentée. |
| 3 | Courbe 02 vide, pas de commentaire | La courbe lit `courbe_performance` (Valorisations) : la structure n'en fournit pas, le run n'en a pas — c'est le vide de l'HISTORIQUE (D50) : au premier run d'un client, il n'y a pas de passé. Le commentaire = 1b. | donnée | Court terme : point de valorisation initial dérivable des invest_dates + arrêté (2 points minimum). Vrai remède : les arrêtés D50 — chaque run nourrit la courbe du suivant. |
| 4 | Tableau détail orienté Gronier, colonnes vides | Colonnes vides : en partie §0 (lignes non jointes). Style : le moteur EST le style Gronier ; le contrôle a des colonnes différentes (sous-tableaux par contrat, % alloc., Perf € par ligne). | bug + style | §0 pour les vides ; puis LA discussion de design : unifier les deux styles (lien D5 — tiers de service ; peut-être un mode par client). À traiter comme un chantier UI dédié, pas au fil de l'eau. |
| 5 | Graphiques PE disparus + colonne cible redondante | **RIEN N'EST PERDU** — et correction du 30/07 (Thomas) : la courbe PE consomme des **VALORISATIONS À DATE**, jamais des mouvements (`_nav_at` : dernière Valorisation ≤ date ; appels = simple proxy au coût ; les flux ne servent qu'à l'échéancier). Le contrôle le confirme : `perf_nc_bars` = deux barres de valorisation (05/26, 07/26). La première rédaction de cette ligne disait « pilotée par les flux » — abus de langage venu du nom de l'onglet « NC Flux », qui mélange deux natures ; le store convergé les sépare déjà (`valuations[]` pour les VL, `mouvements` pour les flux). Le run était muet parce qu'il n'avait AUCUNE valorisation NC, ni datée ni courante (rapports PE hors périmètre §2.b, structure sans VL). | donnée | Décisions : source des VL non cotées (saisie CGP de la dernière NAV, et/ou ouverture du périmètre aux rapports trimestriels PE — à trancher) ; au minimum, le run doit dessiner les deux barres AU COÛT comme le contrôle — vérifier au re-run qu'aucun verrou de template ne l'empêche. Colonne « cible » redondante : micro-décision UI avec le point 4. D50 fera le reste : chaque run nourrit la courbe du suivant. |

## 2 — Ce que ça dit du fond (la lecture de Thomas, précisée)

« On paie le port rapide de la session Gronier » — oui, mais pas où on croyait. Le moteur n'a
rien perdu de ce qu'il avait (le PE en est la preuve) ; ce qui manque est ce que le moteur n'a
**jamais eu** : le contrôle du 23/07 était en partie composé par l'agent (éditorial, double
donut, en-têtes datés), et le moteur déterministe a un périmètre plus étroit. Le fork a protégé
« ne pas régresser LE MOTEUR » (golden, L3a) ; la référence UX du CGP est le rendu d'époque.
**Il manque un troisième juge : la parité de blocs contre un contrôle d'époque** — ce document
en est le premier exemplaire, à systématiser quand le style sera unifié (point 4).

## 2-bis — Observation aggravante de Thomas (30/07, soir) : le détail ligne à ligne ABSENT

**53 lignes au store, zéro au rendu** — vérifié (LVMH, IVO, LU1940199711, Compte Courant :
introuvables dans l'HTML). Le widget « tableau exhaustif + accordéon lignes » (p2_fill L1067)
joint par la même clé `norm("{nature} — {banque}")` que les donuts : même cause racine (§0), même
correctif. MAIS la leçon dépasse le bug : **les QC ont dit 7/7 pendant que le cœur du reporting
manquait** — aucune couche du filet ne surveille la traversée store → HTML au niveau des lignes
(le harnais juge le store, les QC jugent les totaux — qui viennent des poches). Trou structurel.

**Décision induite : un CONTRÔLE DE TRAVERSÉE** — `Σ lignes rendues = Σ lignes du store`, par
contrat, intégré aux contrôles comptables de p2_fill (QC n°10). Un reporting qui perd une ligne
entre le store et l'HTML échoue bruyamment, il ne s'imprime pas amputé. C'est L5 appliqué au
rendu, et le juge qui aurait attrapé ce bug à la première seconde.

## 2-ter — PE : les trois étages ARBITRÉS par Thomas (30/07, soir)

Validés « au global très bonnes solutions », avec deux réalités de terrain :

1. **Étages 1 et 2 dormants faute de documents** : Thomas n'a pas de documents de fonds PE sous
   la main « et n'en aura pas comme ça ». La consigne (situations d'associé/avis) et le ciblage
   par segments restent la **doctrine** — leurs gabarits se construiront organiquement par le
   self-healing le jour où de tels documents arriveront (D38). Rien à construire en avance.
2. **Nouvel AskUser du run (proposition Thomas)** : « fonds de PE sans document — comment fait-on ? »
   Quand le run porte un fonds non coté sans AUCUNE source de valorisation (ni document, ni VL
   déclarée fraîche), la question entre dans le **lot batché B3/D30** : le CGP donne une VL datée
   (provenance `declare_cgp`), ou choisit l'affichage **au coût** — et le rendu DIT « au coût »,
   il ne fait pas passer un cumul d'appels pour une valorisation. Réponse persistée, pas reposée.
3. **Étage 3 acté** : colonnes « Dernière VL connue » + « Date de VL » dans l'Excel de structure
   (chantier A), l'ancre du non coté. Actif dès le prochain tour de structure.

## 2-quater — Deuxième passe de Thomas (post-correctifs) : six points, diagnostic et sort

| # | Constat | Diagnostic | Sort |
|---|---|---|---|
| 1 | Bloc 00 (contexte) toujours vide | Donnée de PÉRIODE absente : `contexte/T3-26.json` n'existe pas — c'est la table D39 (contexte de marché par trimestre, partagée). Le mécanisme fonctionne (les fixtures ont T2-26). | **TRANCHÉ — D52** : mise à jour par le **dashboard admin** (drag & drop « update contexte de marché » → Postgres, table par période côté référentiels), écriture admin-only — « je suis contre donner ce pouvoir aux CGP ». Lecture au run via le bundle, snapshots vendorés en secours (D35). Au backlog du dashboard D34/B5. |
| 2a | « Court terme » = fourre-tout à déplier | Le moteur classe les liquidités de contrats en « Court terme » (G6 de la roadmap l'avait noté). Taxonomie d'affichage à décider : Monétaire vs Liquidités vs dépliage. | Chantier UI (avec G6). |
| 2b | Enveloppes : AV au lieu de Compte Titres | **BUG, corrigé le jour même** : `envelope()` ne connaissait que les formes courtes ('cto') — la nature verbatim « Compte Titres » tombait dans le repli Assurance-vie EN SILENCE. Reconnaissance des formes longues ajoutée ; donut vérifié (« Compte Titres » ×10, zéro AV). Le repli silencieux vers AV reste un vice de conception à revoir au chantier UI (un inconnu devrait se voir). | Corrigé + point UI (repli à rendre bruyant). |
| 3 | 02 : graphique et texte vides | Courbe = vide de l'HISTORIQUE (D50) ; texte = canal éditorial (jamais existé au moteur). **Idée à valider** : courbe dégradée à 2 points pour un nouveau client (capital investi à la date d'invest → valeur à l'arrêté), même philosophie que le PE au coût — affichée comme telle. | D50 + canal éditorial + option « courbe 2 points » au chantier UI. |
| 4 | Colonnes sans données à masquer ; « perf origine » awkward sur nouveau client | Perspective nouvelle consignée : **l'adaptivité des colonnes par disponibilité de données** — le jeu de colonnes doit se plier à ce que le client A, pas l'inverse. Rejoint l'unification des styles (contrôles d'époque). | Chantier UI (principe directeur ajouté). |
| 5 | Dispos pleine largeur ✓ | Débat interne résolu par le rendu ; les matières premières reviennent en petit bloc quand présentes (`_mp` séparé au moteur). | Acquis. |
| 6 | PE bon, graphiques manquants | **Découverte** : le canvas PE n'a JAMAIS existé dans la banque du moteur — `p2_fill` calcule les séries (`views`/`bars` prêtes, y compris le repli au coût), le template `performance_nc` ne les dessine pas. La plomberie est là, le dessin manque. | Chantier UI — coût faible (données déjà branchées), fort rendement. |

## 3 — Plan proposé (ordre de traitement)

0. **QC de traversée des lignes** (§2-bis) — à poser AVANT le correctif, pour le voir échouer
   sur le run actuel puis passer après correctif : le contrôle négatif gratuit.
1. **Correctif jointure `nature`** (bug, prioritaire) + re-run INTERAGYR → re-juger les points
   2a/2b/2c/4-vides ET le détail ligne à ligne sur pièces.
2. **Enrichissement référentiel à l'apply** (sri/class/geo par ISIN quand absents) → SRI attendu
   proche du contrôle (4).
3. **`period_long` daté** (décision d'affichage, zéro code) + note SKILL.md.
4. **Canal éditorial** : logement du commentaire de gestion + injection des ACTUALITÉS Dauphine
   captées (spec courte avant code).
5. **Chantier UI dédié** : unification du style (tableau détail, double donut, SRI coté affiché,
   colonne cible PE, blocs explicatifs PE) — discussion de design avec le contrôle comme pièce,
   décisions consignées, PUIS implémentation. Ne pas le faire au fil de l'eau.
6. **Données du prochain run** : flux PE (périmètre à trancher) ; la courbe se nourrira des
   arrêtés D50.
