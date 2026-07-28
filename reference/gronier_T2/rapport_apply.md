# Rapport d'apply — run Gronier T2 2026 (30/06/2026)

## Sources & hiérarchie
- **Catégories et Perf HANAMI_T2 2026.xlsx** : source de vérité des valorisations (décision CGP).
- **PDF Wealins FC051727 / FC055211** : structure des poches + détail lignes (2 subagents parallèles, diffs validés au schéma).
- **État de comptes O2S 30/06** : bouche-trou uniquement (détail lignes des contrats non couverts par les PDF ; perfs par ligne "+/-Value %" = depuis achat).
- Excel de structure Gronier (7 contrats, 4 entités) : ancres de réconciliation.

## Décisions CGP (AskUser)
1. Valorisations Wealins = Catégories & Perf ; écarts vs Σ lignes PDF absorbés sur lignes Liquidités documentées : FC051727 +3 217,24 €, FC055211 +1 542,32 € (frais d'assurance + dates VL).
2. Bloc 00 : store de période T2 2026 produit via recherche web (6 indices sourcés au 30/06 ; Brent et EUR/USD écartés faute de source fiable). Vendoré dans le skill.
3. Wealins = 2 contrats distincts (clés désambiguïsées "Wealins (FC0512727)" / "Wealins (FC055211)").
4. (Structure) Altaroc : engagé = appelé ; cible 1,8x · 10y ; capital investi = versements nets.

## Mouvements
- Rachat 100 000 € CTO Nortia (S1 2026, date conventionnelle 31/03 — date exacte non publiée).
- Correctif moteur appliqué pendant le run : le KPI YTD intègre désormais les flux (périmètre constant) → +1,52 % au lieu de −0,96 %.

## QC
- Contrôles comptables : 9/9 OK. Total brut 4 615 437 € (coté 3 988 766 + non coté 626 671).
- QC éditorial : 42 lignes sans perf (39 Wealins — les relevés ne publient pas de perf par ligne, documenté ; 3 O2S "(nc)").
- Réconciliation O2S HANAMI : 4 560 478,20 € retrouvés au centime (coté + NC en VL, hors SHIDA/MATSU).

## Propositions référentiel ISIN (à valider par Tristan — jamais écrites au CSV)
- 12 propositions (5 classements par nom + compléments) : voir propositions_referentiel.json.

## Correctif FC051727 (post-livraison v1)
- La « perf louche » (+38,9 % depuis origine) venait d'une erreur de consolidation : le versement de
  200 000 € reçu par la poche FID en 2025 avait été manqué. Capital externe réel : 951 627 €
  (FID 250 000 + 200 000, FAS Thaler 250 000 + 251 627). FID clôturé à 468 018 (+4,0 % sur 450 000
  investis — banal), recyclé en FAS Quintet 413 227 (flux interne). Perf depuis origine : +13,3 %
  en Dietz modifié (+9,7 % cash-on-cash). Store, Excel de transition et Excel de structure corrigés.

## Anomalie de doc corrigée
- SKILL.md §2.b indiquait des noms de champs de ligne (value_eur/class_code/geo_code) non conformes au schéma réel ($defs.line : value/class/geography) — corrigé ; les diffs de ce run ont été normalisés à l'apply.

## Enrichissement géo (24/07/2026, validé CGP)
- 183 propositions géo par classification de nom (subagent, GEO_RULES) : 143 high + 40 medium,
  49 ISIN laissés sans zone (nom insuffisant). Validées high+medium par le CGP.
- Référentiel : 177 geo_code complétés + 6 ISIN ajoutés (261 entrées). 60 lignes du run taguées.
- Donut « Exposition géographique » : de 2 lignes (23 K€) à Europe 32 % / Monde 31 % / Émergents 31 % / Asie-Pac 5 %.
- Lisibilité des flux : colonne « Flux nets » dans l'Historique du patrimoine + mention « après
  retraits nets de 100 000 € » sous la Valeur en fin de période (le 4,03M − 100k + 61k = 3,99M se lit désormais).

## Run historique (24/07/2026) — 31 relevés assureurs + 1 Excel Positions Overview
- 31 subagents parallèles (3 vagues : UAF ×12, Himalia/Cardif ×9, Nortia/Wealins ×10). 31/31 extraits.
- **Décision CGP : les relevés officiels priment désormais partout** (C&P = contrôle croisé). Coté 30/06
  officiel : 3 982 294,76 € (Wealins en valeur de rachat). Lignes 30/06 des 5 contrats non-Wealins
  remplacées par le détail officiel (perf par ligne PRM pour UAF/Himalia ; Cardif/Nortia publient en €, pas en %).
- **FC051727 corrigé par le relevé annuel 2025** : poches réelles Intesa/CIC/Thaler/Quintet ; versements
  2025 datés : 250 000 (13/03) + 200 000 (07/05), frais 1 750 + 1 500 ; clôture CIC→Quintet le 30/12/2025.
  Le « versement 251 627 » de C&P n'existe pas dans l'officiel. Base Dietz origine = valeur au
  31/12/2024 (550 750,75 €, décision CGP — relevé annuel 2024 manquant). Perf depuis base : +4,74 %.
- Historique : 12 points 2022-2024 nouveaux ; Valorisations recalée sur l'officiel (courbe depuis
  31/12/2024 : 3 319 671,53 €) ; **perf annuelle 2025 = +6,34 %** (Dietz, périmètre complet) dans l'onglet Historique.
- Écarts C&P vs officiel documentés (max : Cardif 31/12/25 +6 225 € ; Nortia 31/03/26 −4 298 €).
- Rachat Cardif 2025 précisé : 200 633,23 € (cumul annuel officiel, date conventionnelle mi-année).
- KPI 30/06 : YTD +1,23 % (+49 099 €), départ 4 033 196 €, fin 3 982 295 € après 100 000 € de retraits.

## Lignes annuelles 2024/2025 (complément)
- Année 2025 : valeur 4 033 195,69 € + flux nets +484 367 € + perf +6,34 % (Dietz complet).
- Année 2024 : +4,08 % en PÉRIMÈTRE PARTIEL (UAF ×2, Himalia, Cardif, FC055211 = 57 % du coté fin 2024,
  base 31/12/2023 officielle + primes datées 500 000 @23/10 et 1 000 000 @11/11). Exclus faute de source :
  Nortia (aucune valeur 31/12/2023 dans les relevés ni C&P) et FC051727 (primes 2024 non sourcées).
  Étiquetée « (périmètre partiel) » dans le rendu. Pour compléter : relevé Nortia 31/12/2023 + relevé annuel Wealins FC051727 2024.

## Corrections lisibilité (suite remarques CGP)
- Tableau historique : ordre inversé, du plus récent au plus ancien (T2 → T1 → 2025 → 2024).
- Perf par ligne restaurée : Nortia = plus-values latentes officielles du relevé (9 lignes, % dérivé
  gain/PMA) ; Cardif et Wealins = perfs O2S en bouche-trou par ISIN (41 lignes, horizon depuis achat) —
  les relevés Cardif/Wealins ne publient pas de perf par ligne. 13 lignes restent sans perf (fonds euros, liquidités).
- Moteur : les poches d'un contrat se rendent désormais aussi depuis les étiquettes de poche de
  l'onglet Lignes (FC051727 : 2 poches FAS — CA Indosuez / Quintet), pas seulement depuis Fin coté.

## Historique du patrimoine enrichi (24/07)
- Nouvelles colonnes : Non coté (forward-fill des points Valorisations ; 31/12/2024 = capital appelé
  Altaroc 70 000 €, proxy documenté faute de VL), Patrimoine, Allocation coté/NC (format « 86/14 »),
  Perf € période (gain Dietz en €, réconciliable : valeur N = valeur N−1 + perf € + flux).
- NC 31/12/2025 = 607 316,23 € (OCA + SOMNOO ×3 + Altaroc VL C&P + Stés hôtelières).

## Backburner (décision à venir — ne rien changer pour l'instant)
- Séparer le traitement des PARTS NON COTÉES DÉTENUES EN DIRECT / via supports (ex. OCA, obligations
  hôtelières SOMNOO, co-investissements) des ALLOCATIONS À DES FONDS DE PE (Altaroc…) : classes/rendus
  distincts à concevoir (le schéma store a déjà actions_non_cotees vs private_equity comme point d'appui).

## Détail par poche FC051727 (24/07)
- Bascule sur le modèle natif 2 lignes Fin coté (une par poche), lignées reconstituées depuis le
  relevé annuel Wealins 2025 + C&P : Intesa→Thaler/CA Indosuez (base 302 317,66 au 31/12/24 + 250 000
  versés 13/03/25, frais 1 750) et CIC→Quintet (base 248 433,09 + 200 000 versés 07/05/25, frais 1 500).
  v01 par poche (C&P) : 545 975 / 468 670. Contrôle : Σ gains poches YTD (+14 241 +12 127) = gain
  contrat (+26 369) ✓ ; capital contrat inchangé (997 501).
- Moteur : libellé de poche prioritaire comme titre de ligne (au lieu du mode de gestion) ; sous-titre
  = dépositaire · mode · profil. En-têtes Versements/Retraits/Frais ajoutés au Fin coté (colmap les
  connaissait) : flux saisissables par poche, l'injection Mouvements ne s'applique qu'en repli.

## Type Fonds/Titre (24/07, 4 décisions CGP)
- Colonne « Type (Fonds/Titre) » ajoutée : Excel de structure (template asset + Gronier, déroulant Réf),
  transition v5 (colmap/NCANON étendus), schéma store (attributes.instrument_type).
- Rendu en deux sous-sections : « Fonds de private equity » (engagé/appelé/non appelé/MOIC/Cible/Valeur)
  et « Titres non cotés » (nominal/TRI cible/valeur). Colonne Cible (MOIC/TRI) à droite de MOIC.
- KPIs MOIC/TVPI recalculés sur les FONDS SEULS : 1,53× / 1,52× (vs ~1,0× dilué par les titres au nominal).
- Gronier : 2 fonds (Altaroc, 107 K€) / 6 titres (520 K€ au nominal, TRI cibles 7-10 %).
