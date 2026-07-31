# Dashboard admin — source versionnée (D56)

> Décision de gouvernance de Thomas (31/07) : l'artefact Cowork n'est qu'un **déploiement** ;
> la SOURCE fait foi ici, dans le fork, versionnée avec le reste. « Un point de gouvernance
> devra s'appliquer dans la mesure où on portera le dashboard ailleurs UN JOUR. »

## Règles

1. **`dashboard_admin_artifact.html` est la source de vérité.** Toute évolution du dashboard
   se fait dans CE fichier, puis se déploie vers l'artefact Cowork (`update_artifact`,
   id `referentiels-admin-dashboard`). Jamais l'inverse — un artefact modifié sans sa source
   est une divergence.
2. **Le jour du portage** (webapp, autre hébergement) : ce HTML est le cahier des charges
   vivant — comportements, garde-fous et libellés y sont exécutables, pas seulement décrits.
3. **Garde-fous embarqués** (à préserver dans tout portage) :
   - heure de **dernière lecture** affichée + avertissement « pas du temps réel » (D34,
     RUNBOOK §0 — le cache des artefacts) ;
   - commentaire d'arbitrage **obligatoire** (qui décide dit pourquoi — la qualité du motif
     reste sous la responsabilité de l'arbitre, le garde ne juge pas le texte) ;
   - « Accepter » = confirmation explicite rappelant l'écriture canonique transactionnelle
     et la visibilité à tout CGP au prochain `ref_bundle` (D36) ;
   - provenance D44 affichée avec ses absences DITES (« empreinte absente »), jamais cachées.
4. **Périmètre de visibilité** (consigné le 31/07 en séance) : surface ADMIN. En remote, les
   CGP n'atteignent que `ref_bundle` (lecture) et `ref_propose` (écriture de propositions) ;
   `ref_arbitrer` et l'update du contexte de marché (D52) restent admin-only. Les stores
   clients ne transitent jamais par le MCP (D33/D35/D36).

## Validation du 31/07

Pipeline validé de bout en bout depuis l'artefact : proposition de démo
(`demo_dashboard_2026-07-31`) déposée par `ref_propose` → visible dans la file en_attente du
dashboard → **rejetée depuis l'artefact** par Thomas (13:36:28 UTC, tracée au Postgres,
répartition 7 rejetées / 1 acceptée). Le concept « artefact live comme dashboard » est acté.
