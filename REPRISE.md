# Reprise — à lire en premier dans une nouvelle session

> Réécrit le 2026-07-31 au soir (fin de la 4ᵉ session — la plus dense : JOURNAL 14–22).
> Tout l'état utile est sur disque : ce fichier suffit à repartir sans relire le chat.
> Détail : `JOURNAL.md` (« À faire ensuite » À JOUR) ; **architecture complète** :
> `docs/architecture_skill_fork_2026-07-31.md` (le .skill + le fork, à jour) ; guide CGP
> distribuable : `docs/guide_cgp_skill_reporting.md` ; chantier UI :
> `docs/chantier_ui_design_2026-07-31.md` (SOLDÉ, E1–E8) ; décisions D32–D56 :
> `docs/roadmap_2026-07-27.md` ; D45–D49 : `docs/CDC_v5_2026-07-29.md` ; D50–D51 :
> `docs/spec_historique_arretes_2026-07-30.md` ; écarts : R1–R11.

## Amorçage

```bash
pip install -U jsonschema                          # T4 : Draft 2020-12 requis
cd FORK-Cowork && python3 verifier_pieges.py       # garde N3
cd skill && python3 p1_engine/selfcheck.py         # paquet intègre (134 fichiers)
python3 p1_engine/tests/test_l3a.py fx_simple      # lecteur vivant (timeout 45s)
```

Montages : le fork (obligatoire) ; `fo-data-store/validation_app/ingest` en LECTURE SEULE pour
re-dériver des stores (D47 — `outils_lecteur/deriver_stores.py --validation-app <racine>` où
`<racine>/ingest/` = ce montage ; le défaut du script pointe un montage MORT). Un pont
`mkdir /tmp/va && ln -s <mont ingest> /tmp/va/ingest` suffit. Node/jsdom : HORS paquet
(sandbox /tmp), jamais dans `skill/`.

## Où on en est, en cinq lignes

1. **Chantiers L et B : FAITS** (3ᵉ session). **CHANTIER UI : SOLDÉ 8/8** (4ᵉ session,
   JOURNAL 14–21, dossier UI à jour) : canvas PE rétabli avec provenance « au coût » (**D53**,
   renversement d'une suppression CGP du 23/07, test_pnc retourné) ; courbe coté 2 points
   sincère (D-UI-7) ; colonne cible/chapeau/durée « 7y » (D-UI-2, `_duree()` au lecteur) ;
   Monétaire/Liquidités + `envelope()` en table, AV nommée, inconnu « Autre (à qualifier) » +
   ⚠ (D-UI-5/6, `classe_liquidite()` règle unique) ; **colonnes adaptatives** (D-UI-3 :
   `perf["cote_cols"]`, union A∪B/C, colonne vide non imprimée — INTERAGYR 6 col., fx_simple
   8, jeux gravés au golden) ; caviardage des perfs de ligne aberrantes ±100 % (**D-UI-9** :
   « garder les lignes, caviarder les valeurs », remède de fond = Modified Dietz) ; quick wins
   du Gronier corrigé (E3 widget vide supprimé, E4 SRI avec périmètre, E5 « % Contrat » MP,
   E6 poches ↳ Disponibilités + donut Partenaires agrégé) ; chapeaux 00 « Reporting au
   [date] », partenaires = forme du store (D-UI-8).
2. **Scope recadré (Thomas)** : **D54** — le merge fork→main n'est plus l'objectif, le fork
   EST le PoC (registre des écarts = spécification documentée) ; **D55** — hébergement =
   **Docker local de Thomas** (un conteneur tourne DÉJÀ, exposé par le MCP référentiels
   local — pas Railway, aucun accès). Cible : PoC démontrable de bout en bout.
3. **Pièces** : 3 contrôles d'époque (`reference/controles_epoque/` + README à jour) — le
   **Gronier corrigé du 31/07** remplace celui du 27/07 (défauts connus consignés : écart
   300 k€ donut/Historique, colonne cible conservée à tort, W2/W3 absents — la banque est en
   avance, ne pas régresser). Doctrine : structure INTERAGYR = consensus, Gronier =
   hyperspécifique. Enseignements E1–E8 au dossier UI §10 ; **E7 (courbe à sauts de flux)**
   est le seul apport de forme non porté — exige Valorisations+Mouvements datés (lien D50).
4. **Filet** : golden 8 fixtures (clés `curve_degraded` + `cote_cols` — golden déplacé = diff
   PROUVÉ), L3a 8/8 à l'octet, `test_pnc.mjs` retourné/bi-mode (HORS suite courante — le
   lancer à la main si le bloc PE bouge), QC 9/9 sur INTERAGYR, actif brut 4 723 156 €
   inchangé toute la session. Paquet scellé 134 fichiers ; D44 a mordu 3× (node_modules,
   mes commentaires « Gronier », l'exemple « AB123456 » lui-même).
5. **Dashboard admin : FAIT et VALIDÉ** (JOURNAL 22) — artefact live
   `referentiels-admin-dashboard`, pipeline propose→file→arbitrage exercé en réel (rejet de
   Thomas tracé au Postgres). **D56** : la source versionnée fait foi
   (`dashboard/dashboard_admin_artifact.html` + README), l'artefact n'est qu'un déploiement.
   **File des fronts** (détail au JOURNAL) : contexte T3-26 à produire (bloc 00 vide, D39/D52),
   canal éditorial (spec courte), D50 arrêtés, **B-v run Gronier** (contrôle archivé, attend
   les pièces), chantiers de données (courbe à sauts E7, Dietz lignes, VL non cotées D51-3,
   SRI référentiel vide sur 261 lignes). Arbitrage 1c (page Détails PE) ouvert.

## Les réflexes constants

- **Ne jamais faire régresser le skill** : golden + L3a + QC avant/après ; test_pnc à la main
  si le PE bouge. **Une LIVRAISON se vérifie au CONTENU du fichier livré** (thead/chapeau
  extraits), jamais à la taille ni au succès apparent d'un cp — leçon du 31/07 (JOURNAL 21).
- Table-de-vérité-d'abord ; un invariant non testé n'est qu'un commentaire ; échec bruyant
  (L5) ; ambiguïté signalée, jamais tranchée seule — un renversement d'époque s'arbitre et se
  consigne (D53) ; une décision d'affichage devient un invariant gardé (golden/test).
- Resceller après tout changement de `skill/` (`regenerer_checksums.py` à la RACINE) ; rendus
  clients réels depuis un répertoire JETABLE ; dé-identifier, ne pas supprimer (D44 mord
  aussi les commentaires et la doc).
- Bash sandbox 45 s max, pas de tâches de fond ; le mont est LENT — travailler sur copie
  `/tmp/skillrun`, livrer sur le mont, VÉRIFIER au contenu. Le venv fatigue → on coupe, le
  dossier porte tout.
