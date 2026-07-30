# Chantier B — extraction & réconciliation : roadmap déballée et vérifiée

> 2026-07-30. Demande de Thomas : « on déballe la roadmap du chantier B, on repasse dessus pour
> vérifier que tout est cohérent face à la vision + les chantiers réalisés, puis on exécute. »
> Ce document EST cette passe — il ne code rien. Sources : CDC v4 §B, roadmap (jalon A7),
> décisions D40–D51, chantier L clos (30/07), SKILL.md §2, seed des gabarits, contrat de diff.

---

## 1 — Ce qu'est le chantier B, et ce qu'il n'est pas

B est le **producteur nominal du store** : PDFs de relevés → un subagent par document → contrats
de diff → réconciliation → apply → forme-store 2.1 → rendu (chemin prouvé par le chantier L).
C'est le **filet B** de la distinction fondatrice : l'extraction est faite par un LLM, elle ne se
vérifie pas à l'égalité exacte (ça, c'est le filet A — matcher, lecteur, moteur) mais par
**invariants tolérants**. B lève la limite LIM8 (« extraction sans filet ») constatée par l'étude
du corpus.

Ce que B n'est **pas** : l'ingestion de l'Excel de structure (chantier A, convertisseur D45),
ni le tri des blocs (A3/J), ni l'écriture des arrêtés au datahub (D50, attend le schéma SQL).

## 2 — B1–B10 revisités, tâche par tâche

| # | Tâche (v4) | État au 30/07 et amendements |
|---|---|---|
| B10 | Identification préalable par signature | **FAIT** — `matcher_gabarit.py`, 3 couches, table de vérité 37 docs, discrimination prouvée. Verdicts `ambigu`/`aucun` → `producteur_propositions.py` (fait aussi) → file d'adjudication. |
| B4 | Pièges encodés dans le profil, pas le prompt | **DÉBLOQUÉ = première brique.** N3 était suspendu « faute de filet d'extraction » ; B est ce filet. Migrer les pièges du SKILL.md §2.b vers `extraction_hints` des 9 profils ; le prompt subagent se **prime** depuis le profil apparié. |
| B1 | Un subagent par PDF, sortie = contrat de diff validé jsonschema | Tient. Manque l'outil : **aucun valideur de diff exécutable** n'existe (le schéma oui, `diff_contract.schema.json` — inchangé, md5 = baseline). À écrire (léger). |
| B2 | Profil de diff : `old_value`, `source_page`, `unrecognized_data` | Tient, vérifié : le contrat porte déjà tout (`path/old_value/new_value/source_page`, `confidence`, `notes`, `unrecognized_data` requis). **Les clés du format convergé voyagent dans `path` sans amendement — B7 tient sans rien toucher.** `old_value` dépend du mode : cf. §4, décision de séquencement. |
| B3 | Réconciliation : écart ou low → AskUser, décision tracée | Tient. S'aligne sur D30 (AskUser **batché**, réponses persistées) — cohérent avec la correction D51 du 30/07 : les questions d'un run se posent en un lot, jamais en rafale. |
| B5 | Capter la référence de rattachement énoncée par le relevé (D14) | Tient. S'enrichit du format convergé : le rattachement rejoint `assureur`/`intermediaire` (MQ1) et `pocket.id` (C7) — cf. §3, deux règles d'apply à fixer. |
| B6 | `confidence` cotée depuis K et N, pas au jugement | Tient, et l'infra est là : les référentiels arrivent au run par `referentiels.json` (étape 0-bis, D36). Couple exact = high, alias = medium, inconnu = low + proposition K3. Rien à inventer, à outiller dans l'apply. |
| B7 | Ne pas déformer le contrat de diff | **Vérifié le 30/07** : contrat intact depuis l'ouverture du fork. La provenance D49 n'y entre PAS — elle est **calculée à l'apply** (empreinte du document, gabarit du verdict matcher, arrêté du contexte de run), le contrat reste le point de contact avec validation_app. |
| B8 | Vérifier l'invariant de contrôle avant d'émettre le diff (D25) | Tient, et **le seed est prêt** : vérifié le 30/07, les 9 profils portent `invariant_controle`. Invariant en échec = signal, jamais correction. |
| B9 | Lire `champs_publies` du profil | Tient, seed prêt (9/9). Règle MQ11 en découle : `moic_realise` & co. se REMPLISSENT quand la source les publie — le défaut « logement déclaré jamais rempli » était un défaut de constructeur, l'apply en devient responsable. D40 s'y raccorde : l'export O2S est une source documentaire ordinaire (son gabarit arrivera par le self-healing). |

## 3 — Ce que les chantiers réalisés ajoutent à B (absent de la v4)

1. **L'apply est le chaînon manquant.** SKILL.md §2.d dit « consolider via `store_builder` » — un
   geste d'agent, pas un outil. Il faut `appliquer_diffs.py` (déterministe, testable) : diffs
   validés → entrées 2.1-skill via `store_builder`, avec quatre responsabilités nouvelles :
   *(a)* provenance **D49** sur chaque entrée (empreinte/gabarit/arrêté du run) ;
   *(b)* attribution **déterministe** des `pocket.id` (C7) — pck_NNN dans l'ordre du document ;
   *(c)* résolution `assureur` → **code acteur** par les alias du référentiel (verbatim +
   proposition K3 si inconnu) ;
   *(d)* remplissage piloté par `champs_publies` (MQ11).
2. **Le filet B a cinq couches, nommées** : jsonschema du diff (forme) → invariant de contrôle du
   gabarit (D25, cohérence interne du document) → réconciliation vs ancres (B3, cohérence externe)
   → contrôles comptables du moteur (9 QC, cohérence du store rendu) → verbatim `source_page`/
   ancrage (auditabilité humaine). Aucune couche n'est de l'égalité exacte ; chacune attrape une
   classe d'erreur différente.
3. **La méthode table-de-vérité-d'abord s'applique une 3ᵉ fois.** Avant tout prompt : une **table
   de vérité d'extraction** sur le corpus assureur réel — par document : les invariants attendus,
   les totaux imprimés, les champs que `champs_publies` promet, 2-3 valeurs de lignes choisies.
   Pas une extraction de référence complète (c'est le travail du filet, pas du harnais) : des
   **points de contrôle** choisis pour être discriminants. Elle a sauvé le matcher deux fois.
4. **La bascule ⑤ change la sortie de B** : l'apply produit un store 2.1 qui se rend
   **directement** (`store_to_manifest` + `p2_fill`). Plus d'Excel de transition à générer nulle
   part — le §2.e du SKILL.md est déjà à jour.
5. **D50 en attente d'infra** : B produit des entrées datées avec provenance — suffisant pour que
   les arrêtés se peuplent le jour où le schéma SQL existe. Rien à faire de plus dans B v1.

## 4 — Les incohérences et décisions relevées par la passe

| # | Constat | Proposition |
|---|---|---|
| a | **`old_value` a deux sources selon le mode.** Mode ré-entrée : le `{client}.json` existant (disponible AUJOURD'HUI). Mode AGRÉGATION nouveau client : le store d'ancres issu de l'Excel de structure 3 feuilles — dont le **convertisseur n'existe pas** (CDC v5 §1.3) et dont le format même attend A6/J. | **B v1 s'exécute en mode ré-entrée** (client existant). Le convertisseur structure suit avec A6 — B ne l'attend pas. |
| b | **A8 de la roadmap est périmé** : « Writer & feuilles v5 (D1-D2) » — le writer est **abandonné** depuis D46. | Ligne corrigée à la roadmap (ce jour). |
| c | **Tolérance des invariants non spécifiée.** L'étude a prouvé des invariants au centime (Σ lignes Himalia = épargne atteinte). Mais un PDF peut porter des arrondis d'affichage. | Défaut proposé : **au centime** quand le gabarit le dit (c'est une propriété du profil, pas une constante globale) ; sinon tolérance déclarée DANS `invariant_controle`. Jamais de tolérance implicite. |
| d | **O10 (plafond de parallélisme) n'a jamais été mesuré.** | Instrumenter le premier run réel de B : taille de vague, latence, coût. Mesurer, pas supposer. |
| e | **Questions CGP pendantes** (K7 Thaler/Indosuez, émetteur Himalia, dates d'effet Wealins) : elles ne bloquent pas l'extraction, mais plafonnent la `confidence` des acteurs concernés à medium/low. | Les poser au premier run réel avec CGP — B3 les portera naturellement dans son AskUser batché. |
| f | **La vérité d'extraction n'a pas de logement décidé** (docs/ ? outils ?). | `outils_extraction/table_verite_extraction.json` + harnais, hors paquet skill/ (comme `outils_appariement/`) — le corpus assureur reste hors distribution (D44). |

## 5 — Plan d'exécution proposé (après validation de cette passe)

| Jalon | Contenu | Preuve de fait |
|---|---|---|
| **B-i — Priming par profil (N3)** | Pièges du SKILL.md §2.b migrés dans `extraction_hints` des 9 profils (base + snapshot + seed) ; SKILL.md amendé : le prompt subagent se construit depuis le profil apparié. | Le SKILL.md ne contient plus un piège en dur ; un profil modifié change le prompt sans toucher au skill. |
| **B-ii — Outillage déterministe** | `valider_diff.py` (jsonschema + règles : `amount ≥ 0`, refs) et `appliquer_diffs.py` (§3.1, quatre responsabilités) + tests sentinelles (style D44 : rien ne fuit, rien ne s'invente). | Suites vertes ; un diff mal formé est refusé avec le chemin exact ; l'apply produit un store qui valide ET se rend. |
| **B-iii — Table de vérité d'extraction** | Points de contrôle par document du corpus (38 docs) : invariants, totaux, champs promis, valeurs discriminantes. Écrite AVANT tout prompt. | Le harnais échoue si on lui ment (contrôle négatif inclus, comme `test_discrimination`). |
| **B-iv — Premier run réel (mode ré-entrée)** | Sous-ensemble du corpus → subagents primés (B-i) → diffs (B-ii) → invariants (B8) → apply → rendu. Mesure O10. | Points de contrôle B-iii au vert ; QC 9/9 ; O10 chiffré. |
| **B-v — Réconciliation & banc complet** | AskUser batché (B3/D30) branché ; run INTERAGYR de bout en bout (A9) ; questions CGP posées (e). | A9 : trois versions de vérité concordent ; un run sans écart ne pose aucune question. |

## 6 — Questions ouvertes — TRANCHÉES par Thomas le 30/07

1. **Mode ré-entrée d'abord : OUI** (tolérable en l'état). *Réflexion ouverte de Thomas, à
   approfondir, consignée ici pour ne pas la perdre* : un export Excel de données complet
   permettrait de bypasser toute extraction pour régénérer un reporting — mais « on perd de facto
   la garantie derrière la data ». Note du fork : ce bypass-là **existe déjà, avec la garantie**
   — c'est le mode CONSOMMATION sur le `{client}.json` (provenance D49 par ligne, rendu direct
   depuis la bascule ⑤). La variante Excel serait le même geste **moins** la provenance, ce qui
   est précisément le motif de D46. Si le besoin réel est « régénérer sans ré-extraire », le
   store le couvre ; si c'est « une surface Excel consultable », c'est l'onglet de consultation
   validation_app. À rediscuter si un troisième besoin émerge.
2. **Tolérance des invariants : OUI** — au centime sauf déclaration contraire dans le profil.
3. **B-iv : INTERAGYR d'abord** (client simple), **puis le client de référence** (complexe) —
   gradient de complexité croissante, « ce qui révélera, peut-être, nos impairs ». Prérequis
   logistique : la base de ré-entrée INTERAGYR (`Reporting_INTERAGYR_v4.xlsx`, vu dans la session
   du client de référence) devra être fournie au fork au moment de B-iv — aucun store INTERAGYR
   n'existe ici (constat C4).
