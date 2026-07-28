# Étude empirique — Signatures de gabarit des relevés partenaires

> **2026-07-27.** Suite du checkpoint `checkpoint_store_partenaire_2026-07-25.md` (§9, point parqué n°1).
> Corpus : 11 relevés réels analysés par 11 sous-agents en parallèle (1/document, lecture seule).
> Les empreintes de la partie B sont le **seed v0** du store de couples.
> Tout le corpus est en **texte natif propre** (zéro OCR) — confirmé sur les 11 documents.

---

## Partie A — Enseignements transverses

### A.1 — Le modèle de clé change : émetteur ≠ partenaire ≠ nom de fichier

Constats du corpus :

- Les 4 fichiers « Interagyr » ne désignent **pas un partenaire** : « Interagyr » est un **client**.
  Ils recouvrent **2 émetteurs distincts** — `Interagyr.pdf` est un relevé **de Pury Pictet
  Turrettini** (mandat coté, moteur SSRS) ; les 3 `Relevé - INTERAGYR …` sont des reportings
  hebdo **Dauphine AM** (moteur Word).
- « UAF » est un **distributeur** : le document est émis par **Spirica** (assureur).
- « Nortia » : l'émetteur n'apparaît **nulle part dans le texte** (identité portée par un logo
  image non-OCR). Idem Himalia (produit « HIMALIA CAPITALISATION », assureur non nommé en texte).

**Décisions induites :**

1. La clé du store n'est pas `partenaire × gabarit` mais **`émetteur-du-document × gabarit
   (× périodicité)`**.
2. Le « partenaire » commercial (UAF, Nortia, courtier…) est une **dimension séparée**, avec un
   mapping `distributeur ↔ émetteur` à part.
3. L'identification d'un document se fait **sur le contenu** (signature), **jamais** sur le nom de
   fichier.
4. Quand l'émetteur est absent du texte (logo seul), le **seed est nommé par un humain une fois** ;
   au runtime l'identification passe par la signature, pas par la lecture d'un nom.

### A.2 — La signature est en couches pondérées, pas un hash unique

Preuve par les réplicats intra-émetteur :

| Émetteur | Réplicats corpus | Couches STABLES | Volatils (à exclure) |
|---|---|---|---|
| Dauphine AM | 3 (E4 / Offensif / Trésorerie) | boilerplate légal, en-têtes colonnes, filigrane 9 tokens, agrément AMF | **pages 3→6**, libellés poches KPI, section actualités présente/absente |
| Spirica (via UAF) | 2 (Cerise / Pollux) | metadata JasperReports+OpenPDF, phrases légales SPIRICA, colonnes tableau | montants, nb lignes supports, civilité |
| Wealins | 2 (FC051727 / FC055211) | titres de sections ordonnés, footer RCS Luxembourg, double pagination | **pages 15↔26**, nb de FID, nb lignes OPC |

**Architecture de signature retenue** (du moins cher au plus discriminant) :

| Couche | Source | Coût | Rôle | Limite |
|---|---|---|---|---|
| 1. Metadata PDF | `pdfinfo` (Creator/Producer) | quasi gratuit | pré-filtre | **sous-discrimine** : JasperReports chez Spirica ET Himalia → jamais suffisante seule |
| 2. Ancres boilerplate | chaînes verbatim stables (mentions légales, footers, taglines) | faible | **cœur discriminant** | tolérance requise aux dates embarquées dans les libellés |
| 3. Structure | titres de sections ordonnés + en-têtes de colonnes exacts | moyen | confirmation + base d'ancrage extraction | wrapping multi-lignes des en-têtes |

Verdict : **match** = concordance suffisante des couches ; **drift** = divergence. Les valeurs
(montants, dates, nb pages, nb lignes, libellés de poches) ne touchent aucune couche → le biais
paranoïaque est structurellement non-bruyant.

Stack des moteurs de génération observés (couche 1) :

| Émetteur | Creator / Producer |
|---|---|
| de Pury Pictet Turrettini | Microsoft Reporting Services (SSRS) 2019.11.0.0 |
| Dauphine AM | Microsoft Word / 365 (tagged PDF) |
| Spirica | JasperReports Library / OpenPDF |
| Himalia (assureur non nommé) | JasperReports / iText 2.1.7 |
| Cardif | BdocPDF V7.0 / Apache FOP 2.2 |
| Nortia (plateforme) | polices standard non embarquées, tag technique `^{PSTOCK=paper_0}` |
| Wealins | (voir empreintes ; double pagination = marqueur fort) |

### A.3 — À EXCLURE formellement de toute signature

- **Le nombre de pages** — prouvé mortel : Dauphine 3-6 pages, Wealins 15-26 pages pour le même
  gabarit. Utilisable au mieux comme plage indicative large, jamais comme critère de match.
- Les dates (arrêté, édition — parfois séparées de 4 ans : réédition Spirica 2026 d'un arrêté 2022).
- Les libellés contenant une date embarquée (« Valeur atteinte au 31/12/2022 en euros ») → matcher
  par pattern tolérant, pas par chaîne exacte.
- Les libellés de poches/KPI dépendant du mandat (POCHE ACTIONS vs POCHE OBLIGATIONS chez Dauphine).
- La composition de benchmark (dépend du profil client — apparence boilerplate, réalité volatile).
- Le nom du signataire (la fonction « Directrice Générale de Spirica » est stable, la personne non).

### A.4 — Trois aubaines pour le full-auto

1. **ID de template littéral (Cardif)** : `<MODELE>Relevé situation front-office</MODELE>` +
   `<TYPE_MODELE>66</TYPE_MODELE>` embarqués dans le PDF. Signature parfaite quand elle existe —
   à exploiter opportunistement (champ optionnel `template_id_natif` du profil).
2. **Discriminant de périodicité = libellé, pas date** : la date d'arrêté ne discrimine PAS (un
   trimestriel peut tomber au 31/12). Le token discriminant Cardif : « Cumul des opérations pour
   l'**année** » (→ « pour le mois » / « pour le trimestre »). La granularité
   émetteur × gabarit × périodicité est validée, discriminée par tokens précis.
3. **Checksums intégrés = auto-validation sans humain** : plusieurs relevés n'impriment PAS de
   ligne total (Himalia, Dauphine) → le moteur recalcule et croise. Vérifié : Σ des 9 lignes
   Himalia = « Épargne atteinte » au centime ; Σ des 4 sous-totaux Dauphine = Total portefeuille.
   Chaque profil stocke son **invariant de contrôle** → extraction auto-validée → moins de pauses.
   Rigidité gratuite, cœur du projet.

### A.5 — Problèmes soulevés, à traiter avant le dashboard admin

1. **Modèle de clé et natures de proposition** : l'admin arbitrera 3 natures différentes —
   nouvel émetteur / nouveau gabarit d'un émetteur connu / variante de périodicité. Le schéma du
   store et le contrat de proposition doivent les distinguer. **[le plus structurant]**
2. **Émetteur absent du texte** (Nortia, Himalia) : nommage humain au seed, identification par
   signature au runtime. Prévoir le cas « signature reconnue, émetteur non lisible » dans le flux.
3. **Documents composites** (Wealins = courrier + relevé réglementaire + page Loi Pacte + annexe
   booklet, chacun sa pagination locale, footer fax différent sur la page Loi Pacte) : un PDF =
   plusieurs sous-templates. À trancher : profil composite unique vs profil par sous-template.

---

## Partie B — Les 11 empreintes (seed v0 du store)

Convention : chaque empreinte suit le même schéma JSON. `ancres_texte` = couche 2 ;
`marqueurs_structure` = couches 1+3 ; `pieges_parsing` = à migrer vers les hints d'extraction du
profil (remplace les pièges codés en dur au §2.b du SKILL.md).

### B.1 — de Pury Pictet Turrettini · mandat coté · à la demande/mensuel

```json
{
  "file": "Interagyr.pdf",
  "emetteur": "de Pury Pictet Turrettini (Belgique)",
  "distributeur_ou_contexte": "client final : Interagyr ; dépositaire : UBS (champ 'Banque Dépositaire')",
  "type_releve": "Évaluation de portefeuille — gestion discrétionnaire (mandat coté)",
  "periodicite": "probable mensuel/à la demande (arrêté mi-mois 15/07, historique mensuel glissant)",
  "pages_observees": 11,
  "sections_ordonnees": [
    "Page de garde (Evaluation du Portefeuille / Point de Contact)",
    "Résumé",
    "Matrice allocation actifs et devises",
    "Evolution des actifs par groupe d'évaluation",
    "Performance historique en EUR",
    "Détail des Positions - Liquidités",
    "Détail des Positions - Obligations",
    "Détail des Positions - Actions",
    "Liste des transactions",
    "Dividendes, intérêts et autres paiements",
    "Adéquation du profil",
    "DISCLAIMER"
  ],
  "tableaux_cles": [
    {"titre": "Détail des Positions (Obligations/Actions)", "colonnes": ["DESIGNATION / ISIN", "QUANTITE", "COURS / Prix Achat Moyen", "DEVISE", "EVALUATION (Devise)", "EVALUATION (EUR)", "Intérêts Courus", "RESULTAT Devise", "RESULTAT EUR", "YTD", "POIDS %"]},
    {"titre": "Liste des transactions", "colonnes": ["Date", "Instrument", "ISIN", "Nombre", "Prix", "Devise", "Montant Devise", "% du portefeuille"]},
    {"titre": "Performance historique en EUR", "colonnes": ["[mois glissants]", "Evaluation de début", "Evaluation de fin", "Flux espèces", "Flux titres", "Gain/perte en capital", "Rendement du portefeuille", "Rendement benchmark *", "cumuls"]}
  ],
  "signature": {
    "metadata_pdf": "Creator/Producer = Microsoft Reporting Services 2019.11.0.0 (SSRS)",
    "ancres_texte": [
      "de Pury Pictet Turrettini (Belgique)",
      "Aperçu du Portefeuille",
      "Point de Contact",
      "Matrice allocation actifs et devises",
      "Détail des Positions - Liquidités",
      "Liste des transactions",
      "Dividendes, intérêts et autres paiements",
      "Adéquation du profil",
      "En cas de divergence avec l'estimation produite par la banque dépositaire, les indications de cette dernière prévaudront"
    ],
    "marqueurs_structure": [
      "Séquence fixe des 12 titres de section",
      "Footer chaque page : émetteur + 'Situation au DD/MM/YYYY' + 'Page X/N'",
      "En-têtes tableaux positions sur 2 lignes, sous-colonnes Devise/EUR sous RESULTAT et EVALUATION",
      "Motif 'Total : [sous-catégorie]' après chaque groupe d'instruments",
      "Page de garde 2 colonnes à labels fixes (Compte/Devise/Situation au/Etablie au/Banque Dépositaire/Profil/Mode de détention | Gérant/Tél/E-mail)"
    ],
    "n_pages_indicatif": "9-14"
  },
  "pieges_parsing": [
    "DEUX conventions numériques dans le MÊME PDF : bloc Résumé en anglo-saxon (1,925,477 / 97.15%) vs reste en franco-suisse (1 134 708,36 / 25,19%) — caractéristique stable du gabarit, utilisable comme marqueur",
    "Chaque position sur 2 lignes physiques (ligne 1 = valeurs, ligne 2 = ISIN + PAM + 2e %) — recoupler avant parsing",
    "RESULTAT YTD : deux % empilés, le bon est la 2e ligne (résultat depuis achat) [déjà connu §2.b]",
    "Fonds monétaires classés à tort 'Obligations' → reclasser monetaire [déjà connu §2.b]",
    "Deux niveaux de totaux (section vs sous-catégorie 'Total :') — risque de double comptage",
    "Sections purement graphiques sans texte (Evolution des actifs, Exposition actions) — pas une erreur d'extraction",
    "Benchmark 'Rendement benchmark *' : symbole % seul sans chiffre pour mois sans historique",
    "'Situation au' (arrêté) ≠ 'Etablie au' (édition), écart ~5 jours",
    "Composition du benchmark = volatile (dépend du profil), pas boilerplate",
    "Pas de filets de tableau — pdftotext -layout impératif"
  ],
  "invariant_controle": "Σ sous-totaux 'Total :' par catégorie = total de section ; Σ sections = total portefeuille",
  "texte_natif": true
}
```

### B.2 — Dauphine AM · reporting hebdo mandat · hebdomadaire (3 réplicats)

Consolidé des 3 réplicats (E 4 - ETF · Offensif 6 · Trésorerie 2). **Même gabarit confirmé** ;
divergences volatiles : nb pages (3/4/6), libellés de poches KPI selon mandat, section ACTUALITÉS
présente uniquement si valeurs commentées, section Mouvements vide ou remplie.

```json
{
  "files": ["Relevé - INTERAGYR E 4 - ETF.pdf", "Relevé - INTERAGYR Offensif 6.pdf", "Relevé - INTERAGYR Tresorerie 2.pdf"],
  "emetteur": "Dauphine AM (filiale de Rhétorès Groupe), agrément AMF n°GP-17000033",
  "distributeur_ou_contexte": "reporting de gestion interne conseillers — PAS un relevé de dépositaire ; clients = mandats INTERAGYR",
  "type_releve": "Reporting hebdomadaire de gestion sous mandat (composition + mouvements [+ actualités])",
  "periodicite": "hebdomadaire",
  "pages_observees": "3 à 6 selon mandat",
  "sections_ordonnees": [
    "Bandeau légal 3 lignes (couverture uniquement)",
    "Titre 'Reporting hebdomadaire' + sous-titre 'Composition du portefeuille & mouvements de la semaine'",
    "Bloc identité : CLIENT / SEMAINE DU / VALORISATION AU",
    "Composition du portefeuille (bloc KPI)",
    "Détail des positions (tableau groupé par classe, sous-totaux, Total portefeuille)",
    "Mouvements de la semaine (résumé + liste, ou 'Aucun mouvement sur la semaine.')",
    "ACTUALITÉS — L'actualité sur les valeurs détenues (optionnelle, disclaimer IA + puces)"
  ],
  "tableaux_cles": [
    {"titre": "Détail des positions", "colonnes": ["ISIN", "SUPPORT", "VALEUR", "+/- VALUE", "+/- %", "POIDS"]},
    {"titre": "Bloc KPI", "colonnes": ["VALORISATION TOTALE", "PERFORMANCE YTD", "POCHE [variable selon mandat]", "LIQUIDITÉS", "NOMBRE DE LIGNES"]},
    {"titre": "Mouvements", "colonnes": ["Type (ACHAT/VENTE)", "Support", "Montant", "ISIN", "Date"]}
  ],
  "signature": {
    "metadata_pdf": "Creator/Producer = Microsoft Word pour Microsoft 365 (tagged PDF)",
    "ancres_texte": [
      "Reporting hebdomadaire",
      "Composition du portefeuille & mouvements de la semaine",
      "Détail des positions",
      "Mouvements de la semaine",
      "Dauphine AM, filiale de Rhétorès Groupe",
      "agrément AMF n°GP-17000033",
      "Des convictions au service de la gestion de vos actifs",
      "Une allocation diversifiée, fidèle à l'orientation du mandat.",
      "COMMUNICATION À CARACTÈRE NON COMMERCIAL",
      "NE PEUT ÊTRE TRANSMIS À DES CLIENTS FINAUX"
    ],
    "marqueurs_structure": [
      "En-tête colonnes exact : ISIN SUPPORT VALEUR +/- VALUE +/- % POIDS",
      "En-tête courant 'Reporting hebdomadaire — Semaine du … au …' pages 2+",
      "Footer 'Document à caractère non commercial — non contractuel · Dauphine AM · agrément AMF n°GP-17000033' + 'Page N' (absent page 1)",
      "Filigrane fragmenté en 9 tokens identiques et ordonnés sur chaque page ('U clu','sa s','ex','ge ive','in e','te n','rn t','m','e') — parasite ET ancre fiable",
      "Structure catégorie > lignes > sous-total > 'Total portefeuille'",
      "Disclaimer IA fixe après 'L'actualité sur les valeurs détenues' (si section présente)"
    ],
    "n_pages_indicatif": "3-6+ (couverture + composition + mouvements [+ actualités])"
  },
  "pieges_parsing": [
    "Filigrane diagonal fragmenté pollue l'extraction -layout — filtre regex des 9 tokens AVANT tout parsing [généralise le piège 'filigrane' déjà connu §2.b]",
    "+/- % = variation DE LA SEMAINE, PAS un YTD [déjà connu §2.b] — PERFORMANCE YTD n'existe que dans le bloc KPI",
    "Noms de SUPPORT wrappés sur 2 lignes, valeurs sur la 1re — désalignement si parsing naïf",
    "Sous-totaux de classe sans ISIN/SUPPORT (4 champs au lieu de 6) — distinguer par absence d'ISIN",
    "Ligne LIQUIDITÉS : tiret cadratin '—' pour +/- VALUE et +/- % = non applicable, pas zéro",
    "Signe moins Unicode U+2212 (pas ASCII '-') dans les négatifs",
    "Espace insécable = séparateur de milliers, virgule décimale",
    "Tableau positions scindé entre 2 pages SANS ré-émission d'en-tête",
    "Valorisation apparaît 2 fois (page de garde 'VALORISATION AU' + KPI 'VALORISATION TOTALE') — dédupliquer",
    "Libellés de poches KPI variables selon mandat (ACTIONS vs OBLIGATIONS/MONÉTAIRE) — volatil, pas drift",
    "Section Mouvements : cas dégénéré 'Aucun mouvement sur la semaine.'",
    "Noms de fichiers en Unicode NFD (accent combiné) — résoudre par glob, jamais retaper",
    "Convention d'inclusion des liquidités dans le KPI 'NOMBRE DE LIGNES' non garantie"
  ],
  "invariant_controle": "Σ sous-totaux de classes = 'Total portefeuille' (vérifié au € près sur E4) ; KPI 'NOMBRE DE LIGNES' ≈ compte des lignes extraites (convention liquidités à confirmer)",
  "texte_natif": true
}
```

### B.3 — Spirica (distribué UAF Life Patrimoine) · relevé de situation AV · sur demande (2 réplicats)

Consolidé des 2 réplicats (Cerise / Pollux). **Même gabarit confirmé** — divergences purement
volatiles (client, montants, civilité).

```json
{
  "files": ["2022.12 relevé UAF Cerise.pdf", "2022.12 relevé UAF Pollux.pdf"],
  "emetteur": "SPIRICA (assureur)",
  "distributeur_ou_contexte": "conseiller EMERAUDE GESTION PRIVEE 'en partenariat avec UAF LIFE PATRIMOINE' — UAF = distributeur, PAS l'émetteur",
  "type_releve": "Relevé de Situation — assurance vie 'Version Absolue 2' (courrier + tableau supports)",
  "periodicite": "sur demande (trimestriels disponibles sur demande) — attention : date d'édition peut être des ANNÉES après l'arrêté (réédition 07/2026 d'un arrêté 12/2022)",
  "pages_observees": 2,
  "sections_ordonnees": [
    "Bloc adresse destinataire",
    "Bloc identification contrat (produit, n°, date d'effet, cadre fiscal)",
    "Lieu + date d'émission",
    "Objet : Relevé de Situation + paragraphe introductif",
    "Bandeau centré 'SITUATION AU [date]'",
    "Sous-titre mode de gestion ('Gestion libre')",
    "Tableau des supports + ligne 'Montant de la valeur atteinte au [date]' + 'Valeur de rachat*'",
    "Notes de bas de page rachat (3 §)",
    "Page 2 : 'Contrat n° [n°]' + clôture + signature + 'Vos interlocuteurs à votre service :'"
  ],
  "tableaux_cles": [
    {"titre": "Supports (par mode de gestion)", "colonnes": ["Support", "Valeur de la part en euros", "Date de valeur", "Nombre de parts au [date]", "Valeur atteinte au [date] en euros", "%"]}
  ],
  "signature": {
    "metadata_pdf": "Creator = JasperReports Library ; Producer = OpenPDF — ATTENTION : JasperReports aussi chez Himalia, jamais suffisant seul",
    "ancres_texte": [
      "Objet : Relevé de Situation",
      "SITUATION AU",
      "Montant de la valeur atteinte au",
      "Valeur de rachat*",
      "Le Relevé de Situation n'engage en rien la responsabilité de SPIRICA.",
      "Ce document n'a pas de valeur contractuelle.",
      "Vos interlocuteurs à votre service :",
      "Directrice Générale de Spirica",
      "Le rachat est l'opération par laquelle vous demandez"
    ],
    "marqueurs_structure": [
      "Bandeau titre centré 'SITUATION AU [date]' séparant courrier et tableau",
      "En-tête page 2 = 'Contrat n° [n°]' seul",
      "Footer chaque page : 'Page X / Y' + 3 lignes disclaimer SPIRICA",
      "Colonnes tableau fixes (dont 2 libellés à date embarquée → matcher par pattern)",
      "Bloc final 3 paires label:valeur (Votre conseiller / Adresse / Téléphone)"
    ],
    "n_pages_indicatif": "≥2 (2 en mono-support, croît avec supports/poches)"
  },
  "pieges_parsing": [
    "Sans -layout, le flux réordonne en-têtes et valeurs (tous les en-têtes, puis toutes les valeurs) — extraction par coordonnées impérative",
    "Libellés de colonnes à DATE EMBARQUÉE ('Nombre de parts au 31/12/2022') — pattern tolérant, jamais match exact",
    "Deux dates très éloignées : arrêté (SITUATION AU) vs édition du courrier (réédition possible à +4 ans) — seule SITUATION AU fait foi",
    "Cellule 'Nombre de parts' VIDE pour fonds euros = normal, pas un décalage de colonne",
    "'Valeur atteinte' = 'Valeur de rachat' ici, mais peuvent diverger (pénalités) — ne pas assumer l'égalité",
    "Pas d'ISIN — identification supports par libellé seul → référentiel externe nom→ISIN",
    "Civilité variable modifie les accords des phrases boilerplate — normaliser avant ancrage",
    "Bloc conseiller en 2 colonnes juxtaposées — fusion/désordre en extraction plane",
    "Mono-support ici (1 ligne, 100%) — le profil doit rester valide 0..N lignes et autres modes de gestion (pilotée…)",
    "N° contrat sous 2 formats ('Votre numéro de contrat :' p.1 vs 'Contrat n°' p.2)"
  ],
  "invariant_controle": "Σ colonne % = 100 ; Σ valeurs atteintes lignes = 'Montant de la valeur atteinte'",
  "texte_natif": true
}
```

### B.4 — Nortia (plateforme, non nommée en texte) · relevé compte-titres · mensuel probable

```json
{
  "file": "Relevé Nortia 30 06 26.pdf",
  "emetteur": "NON IDENTIFIABLE EN TEXTE — aucune occurrence de 'Nortia' ; identité = logo image (non-OCR). Nommage humain requis au seed.",
  "distributeur_ou_contexte": "conseiller 'EMERAUDE GESTION PRI' ; plateforme de tenue de compte présumée Nortia (nom de fichier)",
  "type_releve": "Relevé de portefeuille compte-titres (situation + encadré fiscal YTD)",
  "periodicite": "mensuelle probable (édité le 7 du mois suivant l'arrêté)",
  "pages_observees": 2,
  "sections_ordonnees": [
    "'RELEVE PORTEFEUILLE AU [date]' + date d'édition + pagination n/N",
    "Bloc adresse client + 'Votre conseiller :'",
    "'VOTRE COMPTE TITRES N° [n°]' + titulaire",
    "'Madame, Monsieur,' + paragraphe introductif",
    "'VALORISATION EN : EUR' + tableau positions",
    "Macro-zones ordonnées : TITRES - EUROPE > TITRES - INTERNATIONAL > TITRES - AUTRES > LIQUIDITES",
    "'Total du portefeuille'",
    "'INFORMATIONS FISCALES SUR VOTRE PORTEFEUILLE DEPUIS le 1er Janvier [année]'",
    "Légende (*) MIF / PMA / E + clôture 'Bien à vous,'"
  ],
  "tableaux_cles": [
    {"titre": "Positions", "colonnes": ["Code et désignation valeur", "MIF (*)", "Quantité", "Cours", "Valorisation", "Prix moyen d'acquisition (PMA)", "Plus ou moins value latente"]},
    {"titre": "Informations fiscales", "colonnes": ["Libellé (Revenus encaissés / Total des cessions / PMV réalisées)", "Montant EUR"]}
  ],
  "signature": {
    "metadata_pdf": "polices standard non embarquées (Courier/Helvetica) ; tag technique '^{PSTOCK=paper_0}' en tête de CHAQUE page (invisible à l'écran, très fiable)",
    "ancres_texte": [
      "RELEVE PORTEFEUILLE AU",
      "VOTRE COMPTE TITRES",
      "VALORISATION EN : EUR",
      "Code et désignation valeur",
      "Prix moyen d'acquisition (PMA)",
      "TITRES - EUROPE",
      "Total du portefeuille",
      "INFORMATIONS FISCALES SUR VOTRE PORTEFEUILLE DEPUIS le 1er Janvier",
      "Instrument financier éligible à la règlementation MIF",
      "PMA : La validité de cette information est sous votre responsabilité",
      "E Dépôt à l'étranger"
    ],
    "marqueurs_structure": [
      "En-tête complet répété sur chaque page (titre + édition + pagination + adresse + conseiller + n° compte)",
      "En-tête tableau 7 colonnes réparti sur 2-3 lignes physiques, répété chaque page",
      "Macro-zones dans l'ordre fixe TITRES-EUROPE / INTERNATIONAL / AUTRES / LIQUIDITES",
      "Dernière page contient toujours 'Total du portefeuille' + bloc fiscal",
      "Tag '^{PSTOCK=paper_0}' première ligne de chaque page"
    ],
    "n_pages_indicatif": "variable selon positions (2 ici)"
  },
  "pieges_parsing": [
    "Flag 'E' (dépôt étranger) = colonne fantôme sans X fixe — se retrouve décalé loin de sa ligne en extraction (reading-order)",
    "Sous-totaux de catégorie à 3 champs (catégorie/% /montant) vs 7 pour les lignes titres",
    "Négatifs écrits '- 29 220,00' avec ESPACE après le signe — risque de split en 2 tokens",
    "'EUR' accolé uniquement à la colonne Cours, implicite ailleurs",
    "Précision décimale de Quantité variable (0 à 4 déc.) selon la nature du titre — pas un discriminant de colonne",
    "Page 2 ré-affiche tout l'en-tête + en-tête tableau mais ne contient QUE 'Total du portefeuille'",
    "Sous-totaux ≠ total consolidé (unique, dernière page) — double comptage si sommation naïve des lignes à '%'",
    "Σ % des sections = 100 seulement EN INCLUANT LIQUIDITES (43,62% ici)",
    "Tag ^{PSTOCK} pollue le texte extrait — filtrer avant matching",
    "Pas de filets — regroupement par indentation et présence/absence de '%' uniquement"
  ],
  "invariant_controle": "Σ % sections (liquidités incluses) = 100,00 ; Σ valorisations = 'Total du portefeuille'",
  "texte_natif": true
}
```

### B.5 — Himalia (assureur non nommé en texte, prob. Generali) · relevé de situation capi · annuel probable

```json
{
  "file": "2023.12 Relevé Himalia Capi HANAMI.pdf",
  "emetteur": "NON IDENTIFIABLE EN TEXTE — produit 'HIMALIA CAPITALISATION' (gamme Generali présumée), logo image only. Nommage humain requis au seed.",
  "distributeur_ou_contexte": "souscripteur personne morale HANAMI INVESTISSEMENTS",
  "type_releve": "Relevé de situation — contrat de capitalisation (UC)",
  "periodicite": "indéterminée sur 1 spécimen (arrêté 31/12 → annuel probable)",
  "pages_observees": 3,
  "sections_ordonnees": [
    "'Relevé de situation au JJ/MM/AAAA' + disclaimer 'Ce document n'est pas assimilable à un état de situation.'",
    "Bloc identité souscripteur",
    "Bloc contractuel (Souscripteur / Nom du produit / N° du contrat / Durée / Dates d'effet / Option Fiscale / Profil de gestion / Option de prévoyance)",
    "Bloc totaux (Total versé / Total investi* / Total racheté / Epargne atteinte au [date])",
    "Section 'Répartition' (titre récurrent pages tableau)",
    "Tableau 'Répartition de l'investissement' / 'Plus/moins-values***' par catégorie ('Fonds UC' [, 'Fonds Euros'])",
    "Notes (*)(**)(***) + 'Point d'attention :'"
  ],
  "tableaux_cles": [
    {"titre": "Répartition / PMV (2 groupes de colonnes HOMONYMES)", "colonnes": ["Support(s)", "Nb de parts", "Date de valeur", "Valeur de part(€)", "Montant(€) [groupe Répartition]", "%** [groupe Répartition]", "Prix d'Achat Moyen", "Montant(€) [groupe PMV]", "%** [groupe PMV]"]}
  ],
  "signature": {
    "metadata_pdf": "Producer = iText 2.1.7 by 1T3XT ; Creator = JasperReports — ATTENTION : JasperReports aussi chez Spirica, jamais suffisant seul",
    "ancres_texte": [
      "Relevé de situation au",
      "Ce document n'est pas assimilable à un état de situation.",
      "Total versé depuis l'origine",
      "Total investi depuis l'origine",
      "Epargne atteinte au",
      "Répartition de l'investissement",
      "Plus/moins-values***",
      "Prix d'Achat Moyen",
      "Le montant de l'épargne atteinte est obtenu à partir des dernières valeurs connues.",
      "Point d'attention :"
    ],
    "marqueurs_structure": [
      "Titre de page répété 'Répartition' sur chaque page du tableau",
      "DEUX groupes de colonnes aux libellés homonymes Montant(€)/%** — désambiguïser par groupe parent",
      "Absence de ligne Total dans le tableau (total uniquement en bloc d'en-tête p.1)",
      "Bloc 3 notes (*)(**)(***) + 'Point d'attention :'"
    ],
    "n_pages_indicatif": "1 page synthèse + N pages tableau (3 ici pour 9 supports)"
  },
  "pieges_parsing": [
    "Colonnes HOMONYMES ('Montant(€)', '%**') sous 2 groupes parents différents — lecture par nom de colonne seule = ambiguë",
    "Sans -layout : réordonnancement total par colonnes (valeur isolée '-0,16' atterrit APRÈS les notes de bas de page) — -layout impératif",
    "Colonne %** PMV VIDE quand PAM = 0,00 € — parseur à nb de tokens fixe échoue",
    "AUCUNE ligne Total dans le tableau — recalcul obligatoire (Σ 9 lignes = Epargne atteinte, vérifié au centime)",
    "Catégorie 'Fonds UC' affichée UNE fois (p.2), non répétée p.3 — perte de contexte en page-par-page",
    "Noms de supports wrappés sur 2 lignes — fusion avant association aux valeurs",
    "'€' explicite dans les cellules PAM, implicite dans Montant(€)",
    "Pas d'ISIN — référentiel externe nom→ISIN requis",
    "Aucune pagination texte ('Page X/Y' absent) — position par pdfinfo uniquement",
    "Σ %** ≈ 99,99 (arrondis) — jamais exiger 100,00 strict"
  ],
  "invariant_controle": "Σ Montant(€) lignes = 'Epargne atteinte au [date]' (bloc p.1) — vérifié exact sur le spécimen",
  "texte_natif": true
}
```

### B.6 — Wealins · relevé annuel capi Luxembourg · annuel (2 réplicats)

Consolidé des 2 réplicats (FC051727, 26 p., 2 FID / FC055211, 15 p., 1 FID). **Même gabarit
confirmé** — le nombre de pages varie du simple au double avec le nombre de FID : preuve définitive
que le nb de pages est hors signature. **Document composite** : 4 sous-templates concaténés.

```json
{
  "files": ["2025 Relevé annuel Wealins FC051727 HANAMI.pdf", "2025 Relevé annuel Wealins FC055211 HANAMI.pdf"],
  "emetteur": "WEALINS S.A. (assureur luxembourgeois, R.C.S. Luxembourg B 53682)",
  "distributeur_ou_contexte": "dépositaires MULTIPLES par fonds dédié (Banque Thaler, Quintet) — pas un dépositaire unique par contrat",
  "type_releve": "Relevé annuel 'Wealins Capi France' — COMPOSITE de 4 sous-templates : (1) courrier, (2) information annuelle réglementaire, (3) page Loi Pacte, (4) annexe booklet look-through par FID",
  "periodicite": "annuel",
  "pages_observees": "15 (1 FID) et 26 (2 FID)",
  "sections_ordonnees": [
    "[Sous-doc 1] Page adresse (sans footer) + courrier 'Information annuelle [année]' signé COO/CEO",
    "[Sous-doc 2] Caractéristiques du contrat > Information sur l'évolution du contrat (primes/rachats depuis origine) > Situation au 31/12/N-1 > Situation au 31/12/N > Valeur de rachat au 01/01/N+1 > Services/opérations/coûts année N (primes, allocations, rachats, arbitrages, frais) > Frais de gestion administrative > Informations relatives aux unités de compte > Autres informations > signature",
    "[Sous-doc 3] Tableau réglementaire Loi Pacte (page SANS pagination, footer fax DIFFÉRENT)",
    "[Sous-doc 4] Annexe booklet : 'Aperçu des fonds' consolidé, puis PAR FID : Profil d'investissement > Type d'Actifs + donut > Rendement trimestriel > Frais spécifiques > tableau croisé Type/Devise/Catégories > Fonds (détail ISIN, multi-pages) > Fonds alternatifs non UCITS > Liquidités > Valeur totale du fonds"
  ],
  "tableaux_cles": [
    {"titre": "Situation au [date] (x2 : N-1 et N)", "colonnes": ["Fonds", "Nombre d'unités de compte", "Valeur de l'unité de compte", "Date valeur", "Montant total devise du fonds", "Montant total devise du contrat", "%"]},
    {"titre": "Loi Pacte", "colonnes": ["Nom du fonds", "Société de gestion", "SRI", "Perf brute (A)", "Frais UC (B)", "Perf nette (A-B)", "Frais admin (C)", "Frais totaux (B+C)", "Perf finale (A-B-C)"]},
    {"titre": "Détail Fonds / Fonds alternatifs (annexe)", "colonnes": ["Nom", "ISIN", "Quantité", "Devise", "Prix", "Total en devise", "Taux de change", "Total en EUR"]},
    {"titre": "Liquidités (annexe)", "colonnes": ["Nom", "Quantité", "Intérêts courus", "Devise", "Taux de change", "Total en EUR"]},
    {"titre": "Rendement [année]", "colonnes": ["1er trimestre", "2e trimestre", "3e trimestre", "4e trimestre", "Année"]}
  ],
  "signature": {
    "metadata_pdf": "(voir empreintes) — le marqueur fort est structurel : DOUBLE pagination",
    "ancres_texte": [
      "Wealins Capi France",
      "Contrat de capitalisation",
      "Caractéristiques du contrat",
      "Information sur l'évolution du contrat",
      "Arbitrages et/ou changement de banque dépositaire",
      "Informations relatives aux unités de compte",
      "Loi Pacte",
      "Aperçu des fonds",
      "Profil d'investissement",
      "Valeur totale du fonds au",
      "R.C.S.: Luxembourg B 53682",
      "TVA Intra-com.: LU 166 094 20",
      "wealins.com"
    ],
    "marqueurs_structure": [
      "PAGINATIONS LOCALES multiples et non contiguës : 'n/1' (courrier) → 'n/4 ou n/6' (corps) → page SANS compteur (Loi Pacte) → 'Page n/M' (annexe) — aucune pagination globale n'existe",
      "Footer fax DIFFÉRENT sur la page Loi Pacte (26 43 12 74 vs 42 88 84) = marqueur de sous-template",
      "Footer légal WEALINS identique au caractère près sur presque toutes les pages",
      "Bloc structurel répété PAR FID dans l'annexe (Type d'Actifs → Rendement → Frais → croisé → Fonds → alternatifs → Liquidités → Valeur totale)",
      "En-tête annexe 'INFORMATION ANNUELLE : [date] - [contrat]' + 'Fonds : [nom]'"
    ],
    "n_pages_indicatif": "bloc fixe ~9 pages + annexe proportionnelle au nb de FID/lignes (15-26 observés)"
  },
  "pieges_parsing": [
    "COMPOSITE : 4 sous-docs à paginations propres — ne jamais segmenter par pagination globale",
    "Le mot 'Fonds' a 3 sens : FID/enveloppe, catégorie d'actif, titre de sous-tableau OPC — grep naïf interdit",
    "Deux tableaux 'Situation au' identiques (N-1 / N) — capturer la date DU TITRE avec le tableau",
    "'Type d'Actifs' apparaît 2 fois avec contenus différents (simple p.1 annexe vs croisé p.3) — désambiguïser par contexte",
    "Détail 'Fonds' multi-pages sans sous-total intermédiaire — concaténer avant d'agréger",
    "3 niveaux de totaux par FID (sous-totaux Fonds/alternatifs/Liquidités + Valeur totale) — hiérarchiser",
    "Séparateur de milliers INCOHÉRENT entre corps (points : 1.014.646,31) et annexe (espaces : 545 975,50) — dans le même PDF",
    "Colonne Rendement 'Année' ≠ somme des trimestres (composition) — jamais valider par addition",
    "Loi Pacte : perf souvent 'non disponible' avec frais renseignés — cellules vides légitimes",
    "'Open Cost Order' négatif dans Liquidités = débit en attente, pas un actif",
    "Nom du FID ≈ nom de la banque dépositaire ('540709 Banque Thaler SA') — confusion produit/tiers",
    "Artefact '<booklet>' en texte brut en tête d'annexe (balise template visible) — à filtrer",
    "En-têtes empilés sur 2-3 lignes au-dessus de valeurs plus basses — désalignement vertical -layout",
    "Code agence 'LEU.326' en p.1 — ne pas le prendre pour un n° de contrat",
    "Noms fonds/gestionnaires wrappés sur 2 lignes"
  ],
  "invariant_controle": "Par FID : Σ sous-totaux (Fonds + alternatifs + Liquidités) = 'Valeur totale du fonds' ; Σ FID = valeur du contrat",
  "texte_natif": true
}
```

### B.7 — Cardif (BNP Paribas Cardif) · situation de contrat capi PM · annuel

```json
{
  "file": "2025.12 Relevé Cardif Elite Capi HANAMI.pdf",
  "emetteur": "Cardif Assurance Vie (BNP Paribas Cardif)",
  "distributeur_ou_contexte": "CGP EMERAUDE GESTION PRIVEE ; réseau balisé '<RESEAU>DIRECT-CGPI</RESEAU>' ; souscripteur PM HANAMI INVESTISSEMENTS",
  "type_releve": "Situation de contrat — Cardif Elite Capitalisation Personnes Morales (variante Personnes Physiques existe et peut différer)",
  "periodicite": "annuelle — DISCRIMINANT = libellé 'Cumul des opérations pour l'année' (attendu : 'pour le mois'/'pour le trimestre' dans les variantes), PAS la date d'arrêté",
  "pages_observees": 3,
  "sections_ordonnees": [
    "En-tête : 'Cardif Elite Capitalisation Personnes Morales' + 'Situation du contrat N° … au JJ/MM/AAAA' + bandeau 'Contrat de capitalisation'",
    "Informations relatives au contrat > Références (n° contrat/client, dates) + Votre Conseil en Gestion de Patrimoine",
    "Souscripteur",
    "Cumul des opérations > 'Cumul des opérations pour l'année'",
    "P.2 : 'Situation du contrat au [date EN LETTRES]' (tableau supports, groupe 'Gestion libre') + '(1) Net de frais de gestion.' + paragraphes légaux",
    "P.3 : 'Garanties au terme du contrat' (tableau nb UC garanti) + clôture légale"
  ],
  "tableaux_cles": [
    {"titre": "Cumul des opérations pour l'année", "colonnes": ["Montant brut des versements", "Montant net des versements", "Montant brut des rachats"]},
    {"titre": "Situation du contrat", "colonnes": ["Support", "Code ISIN", "Répartition", "Nombre d'unités de compte", "Valeur de l'unité de compte", "Valorisation"]},
    {"titre": "Garanties au terme", "colonnes": ["Support", "Nombre d'unités de compte"]}
  ],
  "signature": {
    "metadata_pdf": "Producer = Apache FOP 2.2 ; Creator = BdocPDF V7.0",
    "template_id_natif": "<MODELE>Relevé situation front-office</MODELE> + <TYPE_MODELE>66</TYPE_MODELE> — ID de gabarit LITTÉRAL embarqué dans le PDF, signature parfaite",
    "ancres_texte": [
      "Cardif Elite Capitalisation Personnes Morales",
      "Contrat de capitalisation",
      "Cumul des opérations pour l'année",
      "Situation du contrat au",
      "Garanties au terme du contrat",
      "Valeur du contrat au",
      "(1) Net de frais de gestion."
    ],
    "marqueurs_structure": [
      "Bloc technique XML-like (<PAPIER>/<TYPE_ENVOI>/<MODELE>/<TYPE_MODELE>/<RESEAU>) répété identique en bas de CHAQUE page",
      "Pagination 'n/3'",
      "En-tête colonnes Support | Code ISIN | Répartition | Nombre d'unités de compte | Valeur de l'unité de compte | Valorisation",
      "Sous-titre de groupe 'Gestion libre' portant le total du groupe sur sa propre ligne",
      "Ligne 'FONDS GENERAL (1)' avec footnote",
      "Date d'arrêté doublée : numérique (p.1) + en toutes lettres (p.2) — contrôle de cohérence interne"
    ],
    "n_pages_indicatif": "3 (structure fixe), croît si nombreux supports"
  },
  "pieges_parsing": [
    "Mise en page FOP en positionnement absolu → espacements extrêmes en -layout ; préférer extraction par positions (bbox/pdfplumber) au découpage par largeur",
    "Ligne 'FONDS GENERAL (1)' : '--' à la place des valeurs numériques mais Valorisation présente — cas particulier",
    "Noms de supports wrappés sur 2 lignes, ISIN et chiffres sur la 1re",
    "'Gestion libre' porte le total du groupe SUR la ligne du libellé de groupe — pas une ligne de support",
    "En-têtes empilés sur 2 lignes ('Montant brut' / 'des versements') — reconstruire",
    "Ligne total 'Valeur du contrat au [date] [montant]' sans séparateur net — détecter comme total",
    "Bloc XML technique : une balise peut se COUPER en fin de ligne physique — parseur de tags naïf cassé ; à filtrer du contenu, à GARDER pour la signature",
    "Artefact d'encodage ponctuel ('sociét�') — prévoir remplacement UTF-8",
    "Tableau Garanties (p.3) = mêmes supports, jeu de colonnes réduit — ne pas confondre avec le tableau Situation",
    "Variante Personnes Physiques du même produit = bloc Souscripteur différent — ne pas présumer l'identité des variantes"
  ],
  "invariant_controle": "Σ Valorisations lignes (+ FONDS GENERAL) = 'Valeur du contrat au [date]' ; cohérence date numérique (p.1) / date en lettres (p.2)",
  "texte_natif": true
}
```

---

## Partie C — Vers le store de couples

### C.1 — Schéma de profil qui se dégage des empreintes

```
profil := {
  emetteur:            { nom, alias[], nomme_par: "texte" | "humain (logo only)" },
  distributeurs:       [ ... ]                     // dimension séparée, mapping distributeur↔émetteur
  gabarit:             { type_releve, sous_templates[]? },   // composite → cf. problème ouvert n°3
  periodicite:         { valeur, token_discriminant },       // ex. Cardif "pour l'année"
  signature: {
    metadata_pdf:      { creator, producer },       // couche 1 — pré-filtre, jamais suffisante
    template_id_natif: str?,                        // ex. Cardif TYPE_MODELE 66 — court-circuit si présent
    ancres_texte:      [ ... ],                     // couche 2 — cœur discriminant
    marqueurs_structure:[ ... ],                    // couche 3 — sections ordonnées + colonnes
    n_pages_indicatif: "plage large, HORS matching"
  },
  extraction_hints: {
    pieges:            [ ... ],                     // migration §2.b SKILL.md → data
    ancrage_tableaux:  [ ... ],                     // où sont les tableaux, colonnes multi-lignes, etc.
    format_numerique:  { separateurs, negatifs, devises }
  },
  invariant_controle:  str,                         // checksum d'auto-validation full-auto
  gouvernance:         { version, provenance: "seed"|"auto-derive"|"valide_admin", confiance }
}
```

### C.2 — Récap seed v0 (7 profils, 11 documents)

| # | Émetteur | Gabarit | Périodicité | Réplicats | Particularités |
|---|---|---|---|---|---|
| B.1 | de Pury Pictet Turrettini | évaluation mandat coté | à la demande/mensuel | 1 | SSRS ; double convention numérique interne |
| B.2 | Dauphine AM | reporting hebdo mandat | hebdo | **3** | filigrane 9 tokens = parasite ET ancre |
| B.3 | Spirica (dist. UAF) | relevé situation AV | sur demande | **2** | rééditions à +4 ans ; dates embarquées dans colonnes |
| B.4 | [Nortia — logo only] | relevé compte-titres | mensuel prob. | 1 | émetteur non lisible ; tag ^{PSTOCK} |
| B.5 | [Himalia — logo only] | relevé situation capi | annuel prob. | 1 | colonnes homonymes ; pas de ligne total |
| B.6 | Wealins | relevé annuel capi Lux | annuel | **2** | COMPOSITE 4 sous-templates ; 15↔26 pages |
| B.7 | Cardif | situation capi PM | annuel | 1 | **template_id natif** ; discriminant périodicité identifié |

### C.3 — Problèmes ouverts (ordre de traitement proposé)

1. **Modèle de clé & natures de proposition** — 3 natures d'arbitrage admin : nouvel émetteur /
   nouveau gabarit d'un émetteur connu / variante de périodicité. Conditionne le schéma du store
   ET le dashboard admin. **[à traiter en premier]**
2. **Émetteur absent du texte** — flux « signature reconnue, émetteur non lisible » ; nommage
   humain une fois au seed.
3. **Documents composites** (Wealins) — profil composite unique vs profil par sous-template ;
   impacte le schéma `gabarit.sous_templates` et la logique de match par segments.

---

*Sources : 11 analyses sous-agents (2026-07-27, lecture seule, un agent par document) ; checkpoint
`checkpoint_store_partenaire_2026-07-25.md` ; SKILL.md `reporting-fo-rhetores-alt` §2.b.*
