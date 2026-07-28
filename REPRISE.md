# Reprise — à lire en premier dans une nouvelle session

> Réécrit le 2026-07-28 (2ᵉ session). Tout l'état utile est sur disque : ce fichier suffit à repartir
> sans relire l'historique du chat.

## Amorçage

```bash
pip install -U jsonschema                          # T4 : Draft 2020-12 requis
cd FORK-Cowork && python3 regenerer_checksums.py --verifier
cd skill/p1_engine && python3 tests/run_tests.py   # attendu : 7/7, QC 9/9
```

**Depuis le sandbox de l'agent, la troisième ligne ne passe pas** (cf. pièges ci-dessous). Utiliser :

```bash
python3 run_une_fixture.py --reset fx_simple.xlsx fx_minimal.xlsx fx_no_portfolio.xlsx
python3 run_une_fixture.py fx_lignes_classes.xlsx fx_noncote.xlsx fx_limites.xlsx fx_multiholdings.xlsx
```

**La régression n'a pas besoin d'être rejouée en priorité cette fois** : elle a été rejouée en
environnement neuf le 28/07, **7/7, QC vert, déterminisme confirmé sur les sept** — y compris
`fx_simple`, le trou de la session d'avant. Aucune dégradation (5,6 à 8,1 s par fixture) : le
ralentissement observé alors était un état du sandbox, pas une régression du moteur. La rejouer reste un
bon réflexe avant de modifier `skill/`, mais elle ne bloque plus rien.

Ordre de lecture ensuite : `README.md` (organisation, boucle de travail) · `JOURNAL.md` (ce qui a été
fait, et pourquoi — l'entrée « 2026-07-28 (2) » est la plus récente) · `REGISTRE_ECARTS.md` (écarts de
schéma R1–R7) · `docs/roadmap_2026-07-27.md` (le plan en deux voies).

---

## Ce qui a changé — 2ᵉ session, 2ᵉ partie

**Une référence de rendu sur client réel est entrée dans le fork** : `reference/gronier_T2/`. Store,
manifeste, classeur, HTML livré, contexte, `cp_valos.json`, rapport de réconciliation. Rejoue en **QC 9/9,
actif brut 4 608 966 €**. Lire `reference/README.md` avant de s'en servir — notamment le fait que **store
et classeur ne sont pas synchronisés** (6 471 € d'écart), ce qui piège L3.

**Invariant A5 posé dans le schéma** : `attributes.pockets` est désormais **requis et non vide** sur
`financierCoteEntry`, et `pocket` gagne `type`, `custodian`, `value_jan1`, `invest_date`, `pledged`. Un
contrat sans poche réelle en déclare une qui le décrit lui-même — un seul chemin de code pour le lecteur.
Trois tests l'ancrent dans `test_store_builder.py` (8/8).

**`migrer_reference.py`** (racine) migre manifeste et store vers l'état courant, idempotent, `.bak`
conservés. Il **refuse** de combler `capital_invested` / `value_jan1` sur les poches multi — les répartir
serait fabriquer une donnée — et le signale à chaque passage.

**A2/T1 était déjà fait** : le bloc a été renommé puis retiré en session 1, il y a huit blocs.
`blocs_enabled` n'accepte plus ni `historique` ni `rendement_annuel` : les vieux manifestes se **migrent**,
ils ne se renomment pas.

**Un snapshot de client réel a été retiré du paquet livré.** `snapshots/tmp_ent_001_T2 2026.json` figurait
dans `BASELINE_MD5.txt` — donc présent à l'ouverture du fork, laissé par un rendu de session 1 depuis
`skill/`, et validé comme légitime par tous les contrôles depuis. Paquet à **115 fichiers**. La baseline
n'est pas régénérée, le retrait apparaît en `SUPPRIMÉS` : c'est voulu.

**État vérifié en fin de session** : checksums à jour (115), selfcheck OK, `test_store_builder` 8/8,
régression **7/7** QC vert et déterministe.

---

## Ce qui a changé depuis la dernière reprise

### D37 — le serveur MCP dédié est ÉCRIT

`infra/mcp_referentiels/` existe : `server.py`, `jwt_auth.py`, `user_store.py`, `logging_config.py`,
`tools/{__init__,_logging,referentiels}.py`, `requirements.txt`, `.env.example`, plus deux scripts de
vérification. Syntaxe vérifiée, **14 contrôles de portage au vert**, écart de code vis-à-vis du module
d'origine conforme aux deux correctifs annoncés (0 ligne inattendue).

Détail des choix dans `infra/mcp_referentiels/README.md`, pas-à-pas de mise en service dans
`infra/RUNBOOK.md` §2.4 (réécrit).

Le choix structurant : **`rhetores_authz` est importé, pas recopié** — le fix S11 y vit, en dupliquer le
code donnerait deux implémentations de validation de token à faire diverger. Idem `user_store` : un seul
registre, donc une seule vérité sur qui est administrateur.

Deux défauts trouvés en portant `referentiels_skill.py`, corrigés :

1. `_identity()` lisait `claims["role"]` au singulier — clé que le middleware ne produit **jamais** (il
   écrit `{"roles": [user.role]}`). Le prédicat retombait donc sur le registre utilisateurs à *chaque
   appel d'outil*.
2. La fuite de compteurs globaux de `ref_adjudications` (RUNBOOK §6) est refermée.

**O5 reste clos** (ids provisoires attribués à Gronier) : le jalon A1 est ordonnançable. Convention en
place et testée dans `pipeline/store_builder.py` — préfixes `tmp_fc_`, `tmp_nc_`, `tmp_mv_`…,
numérotation séquentielle, `_provisional_ids: true` dans le meta. **Le skill ne stampe jamais d'id
définitif.**

---

## État de l'infra chez Thomas

Étapes **2.1 à 2.3 du RUNBOOK faites** sur sa machine : base `rhetores_ref` créée, DDL exécuté, rôles
`ref_app` / `ref_admin` / `ref_mcp` en place.

Reste, côté voie B — et **c'est maintenant purement de l'exécution**, le code est écrit :

1. `pip install -r requirements.txt` dans `infra/mcp_referentiels/` (⚠ lire la note sur le chemin
   relatif de `rhetores_authz`), remplir le `.env` ;
2. `uvicorn server:app --port 8001`, vérifier `/health` ;
3. brancher le MCP dans Cowork (§2.5), appeler `ref_bundle` — **un bundle vide est le succès attendu** ;
4. charger `seed/seed.sql` (§2.7, jalon B4).

**Le piège de configuration à connaître avant de remplir le `.env`** : `REFERENTIELS_DATABASE_URL`
désigne les référentiels, `DATABASE_URL` désigne le **registre utilisateurs** (sa seule présence fait
basculer `rhetores_authz` sur Postgres). Si `DATABASE_URL` est vide *et* que `users.json` manque, tout
appel authentifié répond **403 « Utilisateur non référencé »** avec un token pourtant valide — le
symptôme ressemble à un défaut d'auth, c'est un fichier absent. Ne pas « corriger » en pointant
`DATABASE_URL` sur `rhetores_ref` : la séparation des deux bases est D33.

---

## Où reprendre, par ordre d'utilité

1. **Écrire le lecteur de forme-store (L2)**, maintenant que le joint est cartographié et que A1/A4/A5
   sont tranchés. Règle de conduite, non négociable : **échouer bruyamment sur chaque manque** plutôt que
   combler par un défaut. Un manque silencieusement comblé est un manque qu'on ne corrigera jamais.
   Tout est dans `docs/spec_lecteur_forme_store_2026-07-28.md` — §1 le joint, §3 l'ordre canonique des
   sept onglets sans `colmap`, §7 la confrontation au réel.
2. **L3a — fidélité du lecteur**, sur les 7 fixtures. Réalise aussi **L4**. Prouvable sans donnée client.
3. **L3b — perte de la projection Excel**, sur Gronier. **Prérequis** : régénérer
   `reference/gronier_T2/client.store.json` depuis les relevés officiels, sinon on mesure la dérive des
   deux artefacts au lieu de la perte de projection.
4. **A3 — tri à trois étages**, spec écrite (`docs/spec_tri_blocs_widgets_2026-07-27.md`). O7 est orienté
   (la donnée du Contexte vit au store), la **forme** du logement reste à discuter.
5. **A4 — seed des référentiels**, désormais sous D38 : **un profil par template**. Trancher **O15** avant
   (l'unicité `(emetteur_code, gabarit, periodicite)` suppose que `gabarit` nomme le template, pas sa
   fonction).

**CORRECTION IMPORTANTE — « côté voie B il n'y a plus qu'à exécuter » est FAUX.** Je l'ai écrit deux fois,
c'était une erreur, relevée par l'audit du 28/07. Il reste **deux briques de code, et elles sont dans
`skill/`** :

- **le client de lecture au store** : appeler `ref_bundle` en début de run, se replier sur la copie
  vendorée si le réseau manque (D35), et faire des 7 profils / 261 ISIN un *snapshot* au lieu d'une source
  de vérité (D36). `grep -rn 'ref_bundle' skill/` ne rend **rien** aujourd'hui ;
- **le producteur de propositions** : sans identification par signature (B10/N4) et self-healing (N5), il
  n'existe jamais de gabarit à adjuger, et **le test de réussite n'a pas de sujet**.

Ces deux briques sont écrivables **tout de suite**, sans attendre l'infra — c'est le meilleur usage du
temps d'agent, puisque l'exécution du serveur est chez Thomas.

**Autre nuance à ne pas répéter** : « O5 est clos » n'est vrai que **pour Gronier**. C4 nomme Gronier *et*
INTERAGYR, et il n'existe aucun store INTERAGYR. A1 est ordonnançable ; **A9 ne l'est pas**.

**Les manques restants sont au registre**, M1 à M11. Les traiter **un par un, validés par leur propre
usage** — jamais par anticipation. Le plus lourd reste **M1** (assureur/intermédiaire) : c'est la clé de
jointure des lignes et des mouvements, et le store l'a fusionnée irréversiblement dans `label`.

---

## Dettes de pilotage relevées par l'audit du 28/07

- **Le CDC v4 n'est plus un instrument de suivi** : 3 cases cochées sur 82, alors que **20 sont réellement
  faites**. Il est daté du 27/07 et n'a jamais été mis à jour. Le suivi réel vit ici et dans `JOURNAL.md`.
- **N3 est une dette ACTIVE, pas une tâche en attente** : les pièges de parsing sont désormais
  **dupliqués** — dans `seed/gabarits.json` *et* toujours dans `skill/SKILL.md` §2.b. Deux vérités qui vont
  diverger. À solder en premier si le fork devait s'arrêter.
- **Le dépôt n'est pas versionné** (pas de `.git`). M2 (« registre dès le premier commit ») et M7 (« un
  passage, un bump ») n'ont pas de support. La traçabilité tient sur `BASELINE_MD5.txt` + `JOURNAL.md` +
  `CHECKSUMS.json` — ça fonctionne, mais ce n'est pas ce que le CDC décrit.
- **`docs/spec_tri_blocs_widgets_2026-07-27.md` est partiellement périmée** : elle décrit le bloc
  `rendement_annuel`, supprimé depuis.
- **6 des 17 lignes de « À inscrire dès qu'on y touche »** du registre sont périmées — déjà posées, et
  vraisemblablement **héritées de HANAMI** avant le fork (`store_builder.py` est inchangé vs baseline).
- **R1 et R6 décrivent au présent des positions qui n'existent pas** : `meta.reference_tables` (le schéma
  n'a aucun objet `meta`) et `tri_decisions` au manifeste (absent). Ce sont des positions *souhaitées*.
- **O9, le critère d'arrêt du fork, n'est toujours pas défini** — et son candidat (b) (« retour dès qu'une
  extension touche le contrat de diff ») est **inopérant**, puisque B7 l'interdit déjà : il ne se
  déclenchera jamais. Reste le candidat (a), un seuil sur le nombre d'entrées du registre. Repère :
  **7 entrées posées, 11 dettes réelles décidées non posées**. Un seuil sur « posé + décidé » est déjà
  dépassé.

## Ce qui attend une réponse de Thomas

| Sujet | Nature |
|---|---|
| **K7** — Banque Thaler et CA Indosuez : même entité, ou deux repreneurs de la poche ex-Intesa ? | AskUser au CGP |
| **Émetteur du contrat HIMALIA CAPITALISATION** | AskUser au CGP — un nom plausible circule, volontairement **non** inscrit |
| **Dates d'effet** des deux successions Wealins | AskUser au CGP — laissées à `null` plutôt que devinées |
| **8ᵉ fixture avec onglet Historique** | arbitrage : couvrirait un trou réel, mais **déplace le golden** |
| **O12** — comblement par O2S quand la source ne publie pas de perf par ligne | arbitrage produit |
| **R2** — portée de `reference_tables` (global vs par client) | à arbitrer avec Code |
| **O11 rouvert** — D38 dit « un profil par template » (Wealins = 4), mais R7 et le seed livré font l'inverse (1 profil à 4 segments) | **contradiction à lever avant de charger le seed** |
| **O15** — `gabarit` nomme-t-il le template ou sa fonction ? | **avant le premier `INSERT`**, sinon la clé `(emetteur_code, gabarit, periodicite)` est instable |
| **O9** — le seuil du critère d'arrêt du fork | ton garde-fou, et il n'existe pas |
| **O5/C4 pour INTERAGYR** — aucun store INTERAGYR | bloque A9, pas A1 |

---

## Pièges d'environnement à ne pas redécouvrir

- **`regenerer_checksums.py` après TOUTE modification de `skill/`**, sinon le selfcheck échoue et son
  message (« troncature probable ») fait croire à un paquet corrompu.
- La copie du paquet depuis le cache du skill installé arrive en **lecture seule** : `chmod -R u+w skill`.
- Le sandbox de l'agent n'a **aucun egress réseau** — ni Postgres, ni déploiement, ni test contre un
  service vivant. Ports 443, 53 et 5432 bloqués, DNS non résolu.
- **Chaque appel shell est coupé à 45 s**, et **exécuté dans un namespace PID isolé** : toute tâche de
  fond est tuée au retour de l'appel. Un `nohup … &` suivi de sondages ne marche pas — et le sondage
  lui-même trompe, `pgrep -f run_tests.py` s'appariant à la ligne de commande du shell qui le contient
  (faux « encore en cours » indéfiniment ; écrire `pgrep -f "[r]un_tests"`). `run_tests.py` est donc
  **inexécutable d'un seul trait** ici, indépendamment de la lenteur : c'est structurel, pas une
  dégradation. Utiliser `run_une_fixture.py`.
- La suppression de fichiers exige une autorisation par dossier : éviter de créer des fichiers
  temporaires dans les dépôts. Les `__pycache__` de `infra/mcp_referentiels/` en sont un résidu — sans
  effet, couverts par le `.gitignore` local, à supprimer à la main si cela gêne.
- Les dossiers de Thomas sont **synchronisés OneDrive** : un fichier « cloud-only » fait échouer une
  commande shell mais se télécharge par une simple lecture.
- `mcp-o2s-server` doit être monté **en lecture seule** pour servir de gabarit : ne rien y écrire.
- **Aucune des 7 fixtures n'a d'onglet Historique** : tout ce chemin est hors couverture, y compris les
  lignes annuelles du tableau de supervision, qui restent en production.
