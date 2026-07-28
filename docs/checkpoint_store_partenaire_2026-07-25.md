# Note de conception — Store partenaire & pipeline d'agrégation self-healing

> **Checkpoint** — 2026-07-25. Consolide la réflexion menée à partir des réponses de Thomas
> aux 6 questions du chat « Alternative reporting skill », et de l'examen du dossier
> `validation_app` + des relevés réels (Interagyr/PPT, Wealins, Cardif, Nortia, UAF, Himalia).
> Rien n'a été modifié dans `validation_app` ni dans le skill : ce document est un point d'étape,
> pas un livrable technique.

---

## 1. Contexte & objectif

Le pipeline de reporting FO (skill `reporting-fo-rhetores-alt`) prend **~23 min de bout en bout**.
Répartition estimée (à re-mesurer sur un run réel) :

| Étape | Durée | Nature |
|---|---|---|
| Lecture Excel de structure + réconciliation | ~5 min | prépa/jugement, pas du temps machine pur |
| Lecture des PDF + agrégation dans l'Excel de transition | ~15 min | **goulot** — extraction LLM |
| Génération du reporting (P1/P2 + HTML, tests) | ~3-4 min | rapide, pas le goulot |

**La cible « 5 min » est un objectif de Tristan (CGP), aspirationnel**, jugé irréaliste en l'état
de la techno et raisonnable seulement le jour du tout-API. **Le vrai objectif du projet n'est pas la
vitesse mais la rigidité** (moins de reprises). Le gain de temps est un *side effect*, pas le cœur.

---

## 2. Décision structurante

**Deux produits séparés, pensés pour une liaison future.**

- Le **skill** reste un « papier cadeau » pour les CGP : full-auto, sans plomberie visible.
- **`validation_app`** reste le hub de validation humaine / lifeline.
- **Pivot commun : le contrat de diff.** Toute source (PDF, Excel, PENELOP XML, demain API partenaire)
  émet le même contrat → même boucle revue/apply/audit.

`validation_app` est déjà, à ~80 %, ce que décrit la cible : hub d'ingestion multi-source fonctionnel
(137 tests, auth JWT, dashboard de consultation, interface `Store` abstraite pour le datahub).
Manquent surtout le bouton « générer reporting » et la remontée datahub.

**Friction connue à réconcilier** : périmètre d'extraction inversé entre les deux.
Le skill extrait le **coté** des PDF (PE depuis la feuille Excel). `validation_app` extrait le
**non-O2S** (PE/dette/immo/liquidités) des PDF (coté depuis le MCP O2S). Même pivot, domaines opposés.
**O2S est rétrogradé en bouche-trou** (données les moins qualitatives) → le store partenaire devient
la source primaire, y compris pour le coté.

---

## 3. Le store partenaire

### Nature
**Référentiel-données** (option B), pas une bibliothèque de parsers regex/positionnels (option A).
Il **amorce** l'extraction LLM au lieu de la remplacer : par gabarit, il fournit à Haiku les indices
qui le rendent plus rapide et surtout plus fiable.

> Rejet de l'option A pure : plus on se spécialise sur la structure, plus on devient dépendant du
> gabarit → des dizaines de correctifs par semaine dès qu'un partenaire change un mini-aspect.
> Inefficace. La détermination doit se limiter à l'**ancrage** (voir §4).

### Granularité
**Un profil = un couple partenaire × gabarit.** Raison décisive : un même partenaire (ex. Cardif)
peut émettre des relevés mensuels *et* trimestriels, deux mises en page. Une clé « par partenaire »
n'aurait pas la finesse nécessaire. La **signature de gabarit** (§6) identifie nativement le template,
donc un partenaire à N gabarits = N profils, sans effort de clé.

### Contenu d'un profil (esquisse)
- Identité partenaire + alias + dépositaire.
- **Signature de gabarit** (voir §6).
- **Indices d'ancrage** : où est le tableau des positions, quelle colonne = perf/YTD, etc.
- **Pièges connus** migrés depuis §2.b du skill (ex. PPT « RÉSULTAT YTD = 2ᵉ ligne » ;
  Dauphine « +/- % hebdomadaire, pas YTD »).
- Défauts de classe/géo, mappings de champs.
- Version + provenance (auto-dérivé vs validé admin) + confiance.

### Amorçage (anti cold-start)
Un store vide crée des frictions inutiles avec les CGP (chaque 1ʳᵉ rencontre = voie lente). Donc :
- **Pré-semer le v0** avec les partenaires déjà sous la main dans les PJ (PPT, Wealins, Cardif,
  Nortia, UAF, Himalia).
- **Migrer les pièges §2.b** aujourd'hui codés en dur dans le SKILL.md vers des entrées de profil
  → dédoublonne et rend §2.b piloté par la donnée.

---

## 4. Extraction

- **Frontière du déterminisme : l'ancrage/structure uniquement.** Le déterministe localise (*où* est
  la donnée) ; **Haiku lit et interprète les valeurs** (*quoi*). La structure bouge peu ; les valeurs
  demandent de la robustesse LLM.
- **Levier vitesse = Haiku + parallélisme** (async). Le bulk de `validation_app` est déjà parallèle
  (`asyncio.as_completed`). L'extraction en simultané fait tomber les ~15 min vers **la durée du doc
  le plus lent** (~1-2 min), pas leur somme.
- **Le store partenaire n'est PAS un accélérateur.** Son rôle est la **fiabilité** : moins de valeurs
  fausses → moins de pauses → moins de reprises. Vitesse et fiabilité sont deux leviers distincts qui
  se complètent.
- Coût négligeable : Haiku ~0,012 $/doc (~720 $/an catalogue, ~200-250 avec Batch API). Le coût réel
  reste le temps CGP.
- Tous les relevés testés sont en **texte natif** (aucun OCR). Mais la diversité de mise en page est
  réelle et significative (PPT ~800 car/page tableaux clairsemés ; Cardif 3 pages denses ;
  Wealins 26 pages / 38k car) → justifie le store, invalide une bibliothèque de parsers figés.

---

## 5. Full-auto & pauses de validation

- **Full-auto = un seul run/message**, PAS « zéro humain ».
- **Les pauses AskUser sont conservées** — elles *font gagner* du temps (une question à 10 s évite un
  HTML faux régénéré). Objectif : **minimiser et regrouper** (idéalement un seul AskUser batché plutôt
  que 5 dispersés).
- Les 5 min (aspirationnelles) comptent le **temps machine**, pas la latence des réponses humaines.
- **La validation profonde est reléguée au post-HTML** dans `validation_app` — couche *séparée*, pas
  un remplacement des gates du run.

---

## 6. Self-healing & gouvernance

**Mécanisme.** Chaque profil porte une **signature de gabarit** (anatomie du relevé : titres de
sections, position des tableaux, en-têtes de colonnes). À chaque run, contrôle bon marché :

- **Match** → voie rapide primée (déterministe sur l'ancrage, Haiku sur les valeurs).
- **Drift détecté** → repli analyse LLM complète, profil re-dérivé, message CGP « nouveau gabarit,
  un peu plus long ».

**Biais paranoïaque obligatoire.** Asymétrie des coûts : une ré-analyse ne coûte que du temps Haiku
(quasi rien) ; un drift raté produit une extraction **fausse et silencieuse** que personne ne rattrape
avant le post-HTML (full-auto). Donc en cas de doute, la signature **penche vers « signaler le drift »**
— sans pour autant sonner le clairon pour un rien.

**Gouvernance.** Un profil re-dérivé est **appliqué à ce run seulement**, puis **proposé** (jamais écrit
d'autorité dans le store partagé) à un **dashboard admin « affaires courantes »** (visible admin
uniquement — Thomas aujourd'hui, d'autres ingés demain), qui arbitre avant que le profil devienne
canonique. Même logique que les ISIN inconnus validés par Tristan.

---

## 7. Trajectoire

1. **Phase îlot (maintenant)** : store partenaire + pipeline de mise à jour **dans le skill**.
   Le pipeline est construit *pour* `validation_app`, puis **copié/greffé** sur le skill, de sorte à
   pouvoir l'en **détacher** une fois la liaison établie.
2. **Liaison** : le skill devient consommateur pur ; le store est promu vers un emplacement partagé /
   table datahub ; `validation_app` possède la curation.
3. **API partenaires (≥ 3 mois : août + délais usuels)** : nouveau **3ᵉ producteur** du même contrat,
   diffs **pré-labellisés** `validated_by: partenaire` (auto-validés). Le store reste en **lifeline**
   si le flux partenaire casse. Le champ de provenance du contrat doit accepter une valeur
   « source autoritaire » en plus d'un email CGP.

---

## 8. Recalibrages / ce qui n'est pas retenu

- **Pas de bibliothèque de parsers déterministes purs** (option A). Trop fragile, dette jetable,
  maintenance hebdomadaire. Remplacée par le store-données + ancrage déterministe borné.
- **La reco initiale « pas de parsers » supposait une API proche.** L'API étant à ≥ 3 mois, le store
  partenaire redevient impératif — d'où l'option B et son volet self-healing.

---

## 9. Points parqués (à traiter un par un)

1. **Étude de la signature de gabarit** — le point de rupture technique. Étude empirique dédiée sur les
   vrais relevés : deux Cardif trimestriels de clients différents donnent-ils la même signature ? un
   mensuel vs un trimestriel se distinguent-ils ? Calibrer le seuil et les taux faux-positif/négatif.
2. **Routage des propositions en phase-îlot** — tant que le skill est séparé de `validation_app`, où
   atterrissent ses propositions de profil (drift). Piste privilégiée : **live artifact**. À cadrer
   spécifiquement (« ça remonte des faits très intéressants »).

---

## 10. Provenance

Sources : chat « Alternative reporting skill » (6 questions/réponses de cadrage), SKILL.md
`reporting-fo-rhetores-alt` (§2.b pièges de parsing, contrat de diff, pipeline P0-P4),
dossier `validation_app` (`HANDOFF.md`, `ingest/pdf_agent.py`, `api.py` bulk parallèle),
relevés réels fournis en PJ.
