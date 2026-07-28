# Règles d'exposition géographique (référence skill — CDC chantier F)

## Principe

L'exposition géographique se détermine **par actif** (ligne), à l'ingestion, et se stocke
validée (`geography` dans `attributes.lines[]`, codes `reference_tables`). Le donut
« Exposition géographique » affiche le **% des actifs tagués** (dénominateur = somme des
lignes portant une géo), jamais un bucket « non spécifié ». La **couverture** doit être
affichée à côté du donut : « sur X % des encours cotés ».

## Hiérarchie de sources (fiabilité décroissante — on s'arrête à la première qui répond)

1. **Référentiel ISIN** (`skill_assets/isin_referentiel_v0.csv`) : si l'ISIN y figure avec
   un `geo_code`, c'est la réponse. Déterministe, validé.
2. **Titre vif** : pays du siège de l'émetteur (Microsoft → amerique_du_nord,
   LVMH → europe, TSMC (ADR compris) → asie_pacifique). L'ADR ne change pas l'exposition.
3. **ETF / fonds indiciel** : l'indice dans le nom fait foi —
   MSCI World / ACWI → monde ; S&P 500, Nasdaq, Russell → amerique_du_nord ;
   EuroStoxx, Stoxx 600, CAC, DAX → europe ; MSCI EM, « Emerging » → emergents ;
   Topix, Nikkei, « Asia » → asie_pacifique.
4. **Fonds actif** : ventilation géographique du reporting gestionnaire si disponible
   (zone dominante > 60 % → cette zone ; sinon monde) ; à défaut, zone explicite dans le
   nom du fonds (« Veritas Asian » → asie_pacifique, « Emerging Markets Corporate Bond »
   → emergents) ; thématiques mondiaux (énergie, robotique, biotech, société) → monde.
5. **Sinon : NON TAGUÉ.** Une géo absente est toujours préférable à une géo fausse.
   La ligne sort du donut, la couverture affichée baisse — c'est le signal voulu.

## Périmètre

- Toutes classes confondues (pas seulement les actions) : un fonds oblig émergents porte
  `emergents`, un fonds monétaire euro peut porter `europe` si on veut l'exposer — mais on
  ne force pas : monétaire/fonds euros sans géo est un choix acceptable.
- L'ISIN seul ne donne JAMAIS la géo (le préfixe = pays de domiciliation du véhicule,
  LU/IE ≠ exposition).

## V1 : une zone par ligne

Pas de look-through proportionnel (60 % US / 40 % EU) en v1. Le référentiel porte une
zone unique par ISIN. Extension future : colonne `geo_breakdown` (JSON) dans le
référentiel, agrégation pondérée dans le moteur — ne rien construire en v1 qui l'empêche.

## Ingestion & évolution

- Tout ISIN classé/localisé pendant un run et absent du référentiel sort en
  **proposition d'ajout** (diff à valider par Tristan) — jamais d'écriture directe.
- Conflit entre une source de rang n et le référentiel : le référentiel gagne,
  le conflit est loggé en `notes` du diff.
