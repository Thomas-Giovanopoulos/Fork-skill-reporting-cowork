# Fork — Référentiels & consommation du forme-store

> **Nouvelle session ? Commencez par [`REPRISE.md`](REPRISE.md).** Il contient l'amorçage, l'état vérifié
> de l'infra, où reprendre, et les pièges d'environnement à ne pas redécouvrir.

> **Sujet du fork** : sortir les référentiels du paquet vendoré vers un store partagé, et faire lire
> le forme-store au moteur de rendu. *Nommé par son sujet, pas par un client* (M1) — le dossier
> conteneur s'appelle `FORK-Cowork` pour des raisons d'outillage, mais le sujet est celui-ci.
>
> Ouvert le 2026-07-28. Base : le paquet `reporting-fo-rhetores-alt` installé (merge HANAMI du 27/07).

---

## Pourquoi ce fork existe

Le skill de reporting est né avant le datahub. Il devrait être un **consommateur** (lire des données
consolidées, produire un reporting) ; faute d'infra, il fait aussi l'**agrégation**. Deux
conséquences qu'on traite ici :

1. **Le moteur lit un classeur, pas le pivot.** Tant que `p2_fill` consomme un Excel, toute extension
   de schéma se décide à l'aveugle. D'où D20 : un lecteur de forme-store en premier livrable, pour que
   chaque forme soit validée par son propre usage.
2. **Les référentiels sont vendorés dans le paquet**, donc figés à l'installation. Quand un CGP
   rencontre un nouveau format, l'apprentissage meurt avec son run. D'où D36 : les référentiels vivent
   dans un store partagé, lu à chaque run.

**Le test de réussite**, formulé simplement : *un nouveau gabarit validé est visible au run suivant
d'un autre CGP, sans réinstallation.*

## Ce que le fork parie, et ce qu'il ne parie pas

Le fork développe ses extensions de schéma **unilatéralement** (D18) : on ne touche pas à
`validation_app` dans ce cycle, et le retour vers Code se fait **en une fois**, quand les formes
auront été éprouvées sur un run réel.

- `reference_tables` est **déjà nommé** dans `clients.meta` côté infra : le fork ne fabrique pas un
  concept, il rattrape un concept déclaré, et ne devine que la forme d'une ligne.
- Pour les **inventions réelles** (identifiant stable de poche, logement du bloc Contexte,
  `tri_decisions`), le pari est plus large — d'où le registre.

**Deux règles non négociables**

- **`REGISTRE_ECARTS.md` se tient au fil de l'eau** (D21). Aucune clé posée sans son entrée dans le
  même mouvement. Le registre *est* l'addendum du jour du retour. Tenu régulièrement il ne coûte
  presque rien ; laissé s'accumuler, il redevient une session perdue (leçon HANAMI).
- **Le contrat de diff reste intact** (B7). C'est le point de contact avec `validation_app` : les
  enrichissements vont dans le forme-store, jamais dans le contrat.

## Organisation

```
FORK-Cowork/
├── README.md                 ce fichier — point d'entrée et reprise
├── JOURNAL.md                une entrée par intervention sur skill/
├── REGISTRE_ECARTS.md        M2/M3 — une entrée par décision de schéma unilatérale
├── BASELINE_MD5.txt          empreinte du paquet à l'ouverture du fork (M6)
├── verifier_empreinte.sh     ce qui a bougé depuis la baseline
├── regenerer_checksums.py    À LANCER APRÈS TOUTE MODIFICATION DE skill/
├── run_une_fixture.py        régression découpée — indispensable dans le sandbox de l'agent
├── skill/                    la branche de travail (117 fichiers + CHECKSUMS)
├── infra/                    référentiels : DDL, RUNBOOK, serveur MCP dédié (mcp_referentiels/)
├── seed/                     amorçage des référentiels + script d'assemblage
└── docs/                     CDC, spécifications, étude de signature, roadmap
```

## Boucle de travail — trois commandes, dans cet ordre

```bash
python3 regenerer_checksums.py            # sinon le selfcheck du skill échoue
python3 skill/p1_engine/selfcheck.py      # intégrité du paquet + environnement
cd skill/p1_engine && python3 tests/run_tests.py   # régression 7/7, le filet
```

La première n'est pas optionnelle. `selfcheck.py` compare taille et md5 de chaque fichier à
`CHECKSUMS.json`, et l'étape 0 du protocole du skill impose **STOP** en cas d'échec : une modification
légitime rend donc le skill inutilisable jusqu'à régénération. Le message d'erreur parle de
« troncature probable » et oriente vers une réinstallation — ne pas s'y fier, c'est simplement le
manifeste qui est en retard.

Puis `bash verifier_empreinte.sh` pour voir ce qui a bougé, et une entrée dans `JOURNAL.md`.

**Depuis le sandbox de l'agent, la troisième commande ne passe pas.** Chaque appel shell y est coupé à
45 s et n'y survit pas en arrière-plan (namespace PID isolé) ; `run_tests.py` n'imprimant qu'à la fin,
il dépasse la limite sans rien afficher. Utiliser alors `run_une_fixture.py`, qui découpe le même
verdict — il importe `run_tests.py` et appelle son `measure()` tel quel, sans réécrire de logique :

```bash
python3 run_une_fixture.py --reset fx_simple.xlsx fx_minimal.xlsx fx_no_portfolio.xlsx
python3 run_une_fixture.py fx_lignes_classes.xlsx fx_noncote.xlsx fx_limites.xlsx fx_multiholdings.xlsx
```

Hors sandbox (machine de Thomas), `run_tests.py` reste la commande de référence.

## Où en est-on

Le plan complet est dans `docs/roadmap_2026-07-27.md`, en deux voies : le **skill** (séquentielle) et
l'**infra référentiels** (parallèle, dépendance externe). Rien dans la voie skill n'attend l'infra,
grâce à D35 — seed vendoré d'abord, promotion ensuite.

**Aucun point n'est plus strictement bloquant.** O5/C4 est clos **pour Gronier** — donc A1 est
ordonnançable, mais A9 (banc d'essai INTERAGYR) ne l'est pas, faute de store INTERAGYR.

État des livrables, au 2026-07-29. *Ce tableau est daté à dessein : un état non daté finit par mentir.*

| Livrable | Où | État |
|---|---|---|
| Étude de signature (11 relevés) | `docs/etude_signature_gabarits_2026-07-27.md` | fait — seed v0 des gabarits |
| **Étude de corpus (34 documents, 4 ans)** | `docs/etude_corpus_2026-07-29/` | fait — 4 études d'émetteur, synthèse, **8 limites du système (LIM1–LIM8)**, table de vérité |
| CDC v4 | `docs/CDC_v4_2026-07-27.md` | recoché le 29/07 — **20 cases sur 82**, 7 annotées « à moitié » |
| Spécification du tri à trois étages | `docs/spec_tri_blocs_widgets_2026-07-27.md` | fait (réalise J2), **partiellement périmée** — décrit un bloc supprimé depuis |
| DDL + migration 001 (D42) | `infra/ddl_referentiels_v0.sql`, `infra/migration_001_d42_fenetre_validite.sql` | **joués en base** le 29/07 |
| **Serveur MCP dédié** (D37) | `infra/mcp_referentiels/` | **en service** — 4 outils, 15 contrôles de portage, séparation D34 démontrée en base |
| Seed des référentiels | `seed/` | **chargé en base** — 17 acteurs, 2 successions, **9 gabarits**, 261 ISIN |
| **Filet A — appariement** | `outils_appariement/` | **fait et exercé** — matcher, 32 appariés + 5 signalés, 15 contrôles négatifs |
| Référence de rendu client réel | `reference/gronier_T2/` | produite — rejoue en QC 9/9, 4 608 966 € |
| Spécification du lecteur de forme-store | `docs/spec_lecteur_forme_store_2026-07-28.md` | écrite — manques MQ1–MQ11, ambiguïtés A1–A5 |
| **Lecteur de forme-store** (A1/L2) | — | **AUCUNE LIGNE DE CODE.** Le vide central du fork : la « colonne vertébrale » de D20 n'existe qu'en spécification |
| **Client de lecture du bundle + producteur de propositions** | — | **AUCUNE LIGNE DE CODE**, et `grep -rn 'ref_bundle' skill/` le confirme. Ce sont les deux briques qui manquent au test de réussite |

## Protocole de merge (M6) — écrit avant d'en avoir besoin

Tiré de l'expérience HANAMI, où le merge n'a été sûr que grâce à un registre rédigé *à la fin*, au
prix d'une session perdue par saturation de contexte. Un fork de schéma présente le même risque à un
niveau où les md5 ne suffisent pas, puisque la divergence y est **sémantique**.

1. `BASELINE_MD5.txt` fixe l'état du paquet à l'ouverture. Au moment du merge, recalculer et comparer
   pour isoler **exactement** les fichiers touchés.
2. Écrire par **copie de fichier**, jamais par édition partielle d'un fichier de la cible.
3. **Vérifier après chaque écriture** (taille + md5), pas à la fin du lot.
4. Auditer le paquet **fichier par fichier** avant de le sceller.
5. La divergence sémantique se lit dans `REGISTRE_ECARTS.md`, pas dans les md5.

Régénérer l'empreinte à tout moment :

```bash
cd skill && find . -type f -print0 | sort -z | xargs -0 md5sum > ../BASELINE_MD5.txt
```

## Contraintes d'environnement (à connaître avant de reprendre)

- L'**agent n'a aucun accès réseau** : pas de connexion à Postgres, pas de déploiement, pas de test
  contre un service vivant. Les livrables d'infra sont des **fichiers à exécuter** côté Thomas.
- La suppression de fichiers exige une autorisation explicite par dossier — éviter de créer des
  fichiers temporaires dans les dépôts.
- `jsonschema` doit être en ≥ 4.x (`Draft202012Validator`) : `pip install -U jsonschema` dans tout
  nouvel environnement, sinon `selfcheck` le signale (T4).
