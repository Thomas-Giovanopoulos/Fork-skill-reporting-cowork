# Runbook — mise en place du store des référentiels

> Ce que ce dossier peut et ne peut pas faire : il **contient** le DDL, le serveur MCP et ce runbook.
> L'agent qui a écrit le fork n'a aucun accès réseau et ne peut ni joindre Postgres, ni déployer, ni
> brancher un connecteur. Un agent local disposant d'un shell (Claude Code) peut en revanche piloter
> `docker exec` sans réseau : c'est ainsi que les étapes 2.1 à 2.3 ont été exécutées le 2026-07-29.

## État vérifié au 2026-07-29

| Étape                   | État | Preuve                                                                                                                                                  |
| ------------------------ | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 base`rhetores_ref` | ✅    | existe, UTF8, collation`en_US.utf8`                                                                                                                   |
| 2.2 DDL                  | ✅    | schéma`ref` : 6 tables, 6 types, 11 index, 4 triggers ; `schema_version` = `0.1-skill`                                                           |
| 2.3 rôles               | ✅    | `ref_app` / `ref_admin` NOLOGIN + `ref_mcp` LOGIN NOINHERIT ; séparation D34 **testée en base**                                           |
| 2.4 serveur MCP          | ✅    | bascule**uv** (écart R8) : `pyproject.toml` + `uv.lock`, 43 paquets, `server.py` importe, `/health` → `referentiels_configures: true` |
| 2.5 branchement Cowork   | ✅    | connecteur enregistré : le serveur **répond depuis une session** ; contrôles négatifs 401 / 403 passés avant branchement                            |
| 2.6 bout en bout         | ✅    | `ref_bundle` renvoie le bundle attendu, 4 outils exposés — chaîne client → MCP → Postgres prouvée                                          |
| 2.7 seed                 | ✅    | seed **chargé** : 17 acteurs, 2 successions, **9** gabarits, 261 ISIN ; Cardif en **deux fenêtres** de validité, Wealins en **deux gabarits**  |

> ⚠️ **Un état déclaré n'est pas un état vérifié.** `REPRISE.md` et l'encadré du §2 annonçaient les
> étapes 2.1–2.3 « faites sur sa machine ». Au matin du 29/07 c'était faux : la base `rhetores_ref`
> existait bien, mais le schéma `ref` était **absent** et **aucun rôle** n'avait été créé — seul le §2.1
> avait tourné. Le DDL a été joué ce jour-là. Moralité : le contrôle du §2.2 prend deux secondes, le
> faire avant de croire un tableau d'avancement, celui-ci compris.
>
> **Et c'est bien ce tableau-ci que l'avertissement vient d'attraper, dans l'autre sens.** Il portait
> encore ⛔ sur 2.5 et 2.7 alors que les deux étaient faits : le connecteur répond depuis une session et
> le seed est chargé. Un avancement périmé trompe autant en retard qu'en avance — il fait tenir pour
> bloqué un travail déjà livré, et détourne l'effort suivant. Corrigé le 29/07.

---

## 0 — Ce qui est mis en cache, et ce qui ne l'est pas

Question posée le 2026-07-29, après qu'un redémarrage de Cowork ait été nécessaire : *les CGP
devront-ils relancer l'application sans arrêt ?* **Non.** Mais il fallait séparer deux choses qui
s'étaient mélangées.

| | En cache ? | Change quand | Concerne un CGP ? |
|---|---|---|---|
| Le **schéma** des outils (liste, paramètres, description) | **oui**, jusqu'au redémarrage du client | quand **nous** modifions le code du serveur | seulement aux déploiements |
| Les **données** rendues par un appel | **non** — chaque appel touche Postgres | à chaque écriture en base | jamais de redémarrage |

**Preuve, observée dans une session unique et continue** : `ref_bundle` a rendu un bundle **vide** à
00 h 08, puis **17 acteurs / 2 successions / 9 gabarits / 261 ISIN** après le chargement du seed, **sans
aucun redémarrage** ; et l'adjudication acceptée à 09 h 02 était lisible aussitôt. Un gabarit canonisé
par l'admin est donc visible au `ref_bundle` suivant — c'est le test de réussite du projet, et il
n'exige rien de l'utilisateur.

### Trois conséquences d'architecture, à ne pas perdre

**1 — Le danger n'est pas le redémarrage, c'est la dégradation SILENCIEUSE.** Un client au schéma
périmé ne rejette pas un argument inconnu : il le **retire de l'appel sans un mot**. À l'échelle d'un
parc, des CGP en versions mêlées ignoreraient silencieusement un paramètre — bien pire qu'une erreur.
**Règle** : ne jamais rendre un nouveau paramètre porteur sans que le serveur puisse détecter le vieux
client. Le cas `sections` a été chanceux : le bundle complet dépassant la limite d'un résultat d'outil,
un vieux client échoue **franchement**. Si `sections` n'avait été qu'une optimisation, personne n'aurait
rien vu.

**1 bis — L'ORDRE entre migration et déploiement dépend du SENS du changement.** Constaté en vrai le
2026-07-29, migration 002 : elle a été jouée avant le redémarrage du serveur, et `ref_propose` s'est
mis à échouer sur `column "source_document" of relation "adjudications" does not exist` — le code
insérait encore dans une colonne que la base venait de perdre. L'outil était **cassé en service**.

| Sens du changement | Ordre sûr | Pourquoi |
|---|---|---|
| **Ajouter** une colonne | migration **puis** code | le code ne peut pas écrire dans ce qui n'existe pas |
| **Retirer** une colonne | code **puis** migration | l'ancien code écrit encore dedans, et échoue dès qu'elle disparaît |

Une migration qui fait **les deux à la fois** — comme la 002, qui ajoute `source_empreinte` /
`source_gabarit` / `source_arrete` et retire `source_document` — n'a donc **aucun ordre sûr en un seul
temps**. Deux options : déployer d'abord le code qui écrit les nouvelles colonnes et n'écrit plus
l'ancienne, puis jouer la migration ; ou scinder la migration en deux (ajout maintenant, retrait après
déploiement). La seconde est plus sûre si le serveur ne peut pas être arrêté.

**2 — Un changement de signature est une release coordonnée.** Le garde-fou usuel est de **versionner le
nom de l'outil** (`ref_bundle_v2`), ce qui laisse cohabiter ancien et nouveau client le temps de la
bascule. À mettre en place avant qu'il y ait un parc, pas après.

**3 — Le dashboard admin (B5) est le seul endroit où le cache mordra un utilisateur.** Les artefacts
Cowork **mettent leurs lectures MCP en cache** (avec un bouton Recharger). Le dashboard d'adjudication
montrera donc un état daté. Ce n'est pas un défaut, mais il devra **afficher l'heure de sa dernière
lecture** plutôt que de se faire passer pour du temps réel : un dashboard qui mentirait sur sa fraîcheur
ferait arbitrer sur des données périmées.

---

## 1 — Le mécanisme : comment le skill parle à la base

C'est le point à comprendre avant tout le reste, parce qu'il détermine l'ordre des étapes.

**Le sandbox d'exécution du skill n'a aucun accès réseau.** Un script Python du pipeline ne peut donc
**pas** se connecter à Postgres. Seul le **client Claude** peut appeler un serveur MCP.

D'où la chaîne réelle :

```
Client Claude ──appelle──► MCP ref_bundle ──lit──► Postgres
      │
      └──écrit──► run/referentiels.json
                        │
                        └──lu par──► pipeline Python déterministe
```

**Le fichier est le contrat, pas la connexion.** Conséquences pratiques :

- Le côté consommateur (skill) se développe **dès maintenant** contre `seed/referentiels.json`, sans
  aucune infra. Le jour où la base existe, seule la *provenance* du fichier change — une instruction
  dans SKILL.md, pas une réécriture.
- Le même artefact sert **trois fois** : bundle du run, pièce du dossier archivé (D4), et repli
  hors-ligne quand le réseau ou le MCP est indisponible (D35).
- C'est **le même joint** que le futur `get_client()` du datahub : on ne construit pas un mécanisme
  jetable.

---

## 2 — Étape par étape

> **Avancement** : voir le tableau vérifié en tête de document. Au 2026-07-29, les étapes **2.1 à 2.7
> sont faites et contrôlées** — les blocs qui suivent servent donc à rejouer, à diagnostiquer et à
> reprendre sur une autre instance (§4), pas à avancer. Les deux verrous à connaître avant d'y toucher
> sont au §2.5 (relance de Cowork après un changement de signature) et au §3 (taille du bundle).

### 2.0 Protocole d'exécution sur la machine de Thomas — Windows, PowerShell, conda

Les blocs de ce runbook ont été écrits pour un shell POSIX. La machine cible est **Windows 11 +
PowerShell 7 + conda `base` activé en permanence** : quatre d'entre eux ne peuvent pas fonctionner tels
quels. Les pièges ci-dessous ont tous été rencontrés le 2026-07-29 ; ils coûtent une soirée si on ne
les connaît pas.

**1 — Ne jamais activer de venv. Appeler l'interpréteur par son chemin.**

`source` n'existe pas en PowerShell (l'équivalent serait le *dot-sourcing* `. .\...`), et un venv
Windows place ses scripts dans `Scripts\`, jamais `bin/`. Un `source .venv/bin/activate` est donc faux
**deux fois**. Plutôt que de traduire la commande, on supprime le besoin — appeler l'interpréteur par
son chemin est plus court, insensible au shell, et immunisé contre le piège 3 :

```powershell
.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8001
```

> **Depuis la bascule uv du §2.4, ce piège ne concerne plus le serveur des référentiels** : `uv run`
> résout le `.venv` du projet tout seul, il n'y a plus de venv à activer ni de chemin à taper. Le piège
> reste documenté ici parce que le `README.md` de `mcp_referentiels/` et bien d'autres READMEs portent
> encore la séquence POSIX — et parce qu'un `pip` ponctuel dans un venv manuel arrive toujours.

**2 — `&&` ne se traduit PAS par `-and`.** C'est l'erreur qui fait perdre le plus de temps, parce
qu'elle ne produit aucun message d'erreur :

```powershell
(python3 -m venv .venv) -and (source .venv/bin/activate)   # ⛔ affiche : False
```

`-and` est un opérateur **booléen**, pas un enchaînement de commandes : PowerShell exécute la partie
gauche, échoue à droite, et **imprime le résultat de l'expression — `False`**. La commande de gauche a
pourtant bien tourné ; on croit à un échec total alors que le venv a été créé. En PowerShell 7, `&&`
fonctionne nativement ; sinon `;` enchaîne inconditionnellement.

**3 — conda pose `VIRTUAL_ENV` sur son propre prefix.** `base` étant toujours actif, `VIRTUAL_ENV` vaut
`…\anaconda3`, et tout outil qui s'y fie croit être dans le mauvais environnement (`uv` le signale par
un avertissement de mismatch). Si l'on doit malgré tout activer quelque chose :

```powershell
conda deactivate            # ou, plus chirurgical : $env:VIRTUAL_ENV = $null
```

Sur cette machine, l'activation de conda dans les terminaux ne vient **pas** d'un profil PowerShell
(il n'y en a aucun) mais de VS Code : réglages `python.terminal.activateEnvironment` et expérience
`pythonTerminalEnvVarActivation`, passés à `false` / `optOutFrom` le 2026-07-29.

**4 — `docker exec -it` meurt hors terminal interactif.** `-t` réclame un TTY : dans un script, un hook
ou un agent, la commande échoue sur `the input device is not a TTY`. Tous les `docker exec` de ce
runbook fonctionnent aussi bien **sans** `-it` et ont été récrits ainsi — les garder utilisables par un
agent est ce qui a permis de jouer le DDL sans intervention manuelle.

**5 — `cp .env.example .env` est silencieux ET destructeur.** `cp` est un alias de `Copy-Item`, **muet
en cas de succès** : « rien ne s'affiche » ne veut pas dire « rien ne s'est passé ». Et si un `.env`
renseigné existe déjà, la commande l'écrase par un gabarit aux valeurs vides, sans un mot. Elle ne sert
qu'au **premier** amorçage ; ensuite on **ajoute** les lignes manquantes en fin de fichier.

> Interpréteurs disponibles : `python` → `anaconda3\python.exe` (3.13.9) et `python3` → shim Store
> *PythonManager* (3.13.9 aussi). Les deux savent créer un venv. ⚠️ Le `.venv` actuel de
> `mcp_referentiels/` a été créé par le python du venv de `integration-O2s-api` (cf. son `pyvenv.cfg`,
> clé `executable`) : c'est un venv-de-venv, fonctionnel mais fragile — il casse si le venv parent
> bouge. Le recréer depuis `python` (anaconda) est préférable, et sans coût puisqu'il ne contient
> que pip.

### 2.1 Créer la base et les rôles

En dev local, le Postgres du `docker-compose.yml` de `fo-data-store` suffit (image `postgres:16`,
conteneur `rhetores-dev-db`, superutilisateur `rhetores`).

```powershell
docker compose up -d          # depuis fo-data-store, si ce n'est pas déjà lancé

# Contrôler d'abord : CREATE DATABASE n'est pas idempotent, il échoue si la base existe.
docker exec rhetores-dev-db psql -U rhetores -d postgres -tAc "SELECT datname FROM pg_database WHERE datname='rhetores_ref';"

# Base SÉPARÉE de la projection du datahub (D33) : on ne pollue pas ses tables.
docker exec rhetores-dev-db psql -U rhetores -d postgres -c "CREATE DATABASE rhetores_ref WITH ENCODING 'UTF8' TEMPLATE template0;"
```

> **Collation** : la commande ci-dessus ne fixe que l'encodage, la collation est donc héritée du
> cluster — `en_US.utf8` sur l'image `postgres:16`, et non le `fr_FR.UTF-8` que suggère le §0 commenté
> du DDL (locale absente de l'image). Sans conséquence ici : c'est **aussi** le défaut d'Azure Flexible
> Server, donc la parité visée au §4 est respectée. Seul effet : un `ORDER BY` sur des libellés
> accentués suit les règles en_US.

> Le nom `rhetores_ref` est celui supposé par le DDL. Pour en changer, adaptez-le ici **et** dans le
> DSN de l'étape 2.4 — le DDL lui-même n'y fait pas référence.

### 2.2 Exécuter le DDL

```powershell
docker cp ddl_referentiels_v0.sql rhetores-dev-db:/tmp/ddl.sql
docker exec rhetores-dev-db psql -U rhetores -d rhetores_ref -v ON_ERROR_STOP=1 -f /tmp/ddl.sql
```

`ON_ERROR_STOP=1` n'est pas décoratif : sans lui, psql poursuit après la première erreur et laisse un
schéma à moitié construit qu'aucun contrôle simple ne distingue d'un schéma complet.

Contrôle attendu — **le faire systématiquement**, c'est lui qui a révélé le 29/07 que le DDL n'avait
jamais tourné malgré un avancement déclaré :

```powershell
docker exec rhetores-dev-db psql -U rhetores -d rhetores_ref `
  -c "SELECT valeur FROM ref.ref_meta WHERE cle='schema_version';" `
  -c "SELECT table_name FROM information_schema.tables WHERE table_schema='ref' ORDER BY 1;"
```

Attendu : `0.1-skill`, puis les **six** tables `acteur_successions`, `acteurs`, `adjudications`,
`gabarits`, `isin`, `ref_meta`. Le backtick est la continuation de ligne en PowerShell — pas
l'antislash.

### 2.3 Créer le rôle de connexion

Les rôles `ref_app` et `ref_admin` sont créés par le DDL. Le rôle de **connexion** est laissé en
commentaire à dessein : il porte un mot de passe.

```powershell
docker exec rhetores-dev-db psql -U rhetores -d rhetores_ref -c `
 "CREATE ROLE ref_mcp LOGIN NOINHERIT PASSWORD 'CHOISIR_UN_MOT_DE_PASSE';
  GRANT ref_app, ref_admin TO ref_mcp;"
```

> **Mot de passe retenu en dev local : `dev`**, par parité avec le superutilisateur `rhetores`/`dev` du
> `docker-compose.yml`. C'est un secret de dév sans valeur, et un mot de passe fort n'apporterait rien
> sur un Postgres en conteneur dont le compte admin est déjà `dev`. La bascule managée (§4) impose
> évidemment un vrai secret, injecté par `REFERENTIELS_DATABASE_URL`.

`NOINHERIT` est le point clé : `ref_mcp` est membre des deux groupes mais n'en exerce **aucun** sans
`SET ROLE` explicite. C'est ce qui fait qu'un bug applicatif ne peut pas canoniser à la place d'un CGP
— la séparation « proposer ≠ canoniser » est portée par la base, pas par une convention.

**Vérifier que la permission tient vraiment.** D34 exigeait que la séparation soit une permission et non
une convention : cela se démontre, cela ne se suppose pas. Les cinq contrôles suivants ont été passés
avec succès le 2026-07-29 — deux doivent **échouer**, c'est le but.

```powershell
$e = "-e","PGPASSWORD=dev"
# 1. sans SET ROLE  -> ATTENDU : permission denied for schema ref
docker exec @e rhetores-dev-db psql -U ref_mcp -d rhetores_ref -tAc "SELECT count(*) FROM ref.acteurs;"
# 2. SET ROLE ref_app -> lecture du canonique OK
docker exec @e rhetores-dev-db psql -U ref_mcp -d rhetores_ref -tAc "SET ROLE ref_app; SELECT count(*) FROM ref.acteurs;"
# 3. ref_app tente de canoniser -> ATTENDU : permission denied for table acteurs
docker exec @e rhetores-dev-db psql -U ref_mcp -d rhetores_ref -tAc "SET ROLE ref_app; INSERT INTO ref.acteurs (code,nom,role,provenance,confiance) VALUES ('x','X','assureur','seed','low');"
# 4. ref_app PROPOSE dans la file -> doit passer
docker exec @e rhetores-dev-db psql -U ref_mcp -d rhetores_ref -tAc "BEGIN; SET LOCAL ROLE ref_app; INSERT INTO ref.adjudications (cible,nature,cle,proposition,propose_par) VALUES ('acteur','nouvel_acteur','{}','{}','test'); ROLLBACK;"
# 5. ref_admin canonise -> doit passer
docker exec @e rhetores-dev-db psql -U ref_mcp -d rhetores_ref -tAc "BEGIN; SET LOCAL ROLE ref_admin; INSERT INTO ref.acteurs (code,nom,role,provenance,confiance) VALUES ('x','X','assureur','seed','low'); ROLLBACK;"
```

Les contrôles 4 et 5 écrivent dans une transaction annulée : ils prouvent le droit sans laisser de
ligne. Si le contrôle 1 **réussit**, le `NOINHERIT` a été perdu (rôle recréé sans l'option, ou `GRANT`
rejoué autrement) et toute la garantie D34 est tombée en silence.

### 2.4 Monter un serveur MCP DÉDIÉ — *révisé (D37)*

> **Cette étape a changé.** La version initiale greffait un module `tools/` sur `mcp-o2s-server`.
> **Décision de Thomas : on ne surcharge pas le serveur O2S.** On monte un serveur MCP **autonome**, en
> reprenant le petit framework Starlette de `mcp-o2s-server`, qui fonctionne bien.
>
> Motifs : cycle de vie et déploiement indépendants, aucun risque de régression sur O2S, et au moment de
> la convergence datahub on débranche un serveur entier plutôt que de démêler un module.

> **ÉCRIT au 2026-07-28** — `infra/mcp_referentiels/` existe, syntaxe vérifiée, 14 contrôles de portage
> au vert. Reste à l'**exécuter** chez Thomas (aucun accès réseau depuis l'agent). Détail des choix et
> des trois écarts assumés : [`mcp_referentiels/README.md`](mcp_referentiels/README.md).

Arborescence produite (`infra/mcp_referentiels/`) :

```
server.py                Starlette + FastMCP + JWTAuthMiddleware, calqué sur mcp-o2s-server/server.py
jwt_auth.py              middleware repris ; validation du token DÉLÉGUÉE à rhetores_authz (fix S11)
user_store.py            adaptateur rhetores_authz — MÊME registre utilisateurs que O2S
logging_config.py        logging JSON, repris verbatim (mêmes lignes dans le même agrégateur)
tools/referentiels.py    ← referentiels_skill.py, + les deux correctifs ci-dessous
tools/_logging.py        décorateur @logged (reprise, allowlist d'audit étendue)
tests/test_portage.py    14 contrôles sans réseau ni base
tests/verifier_diff.py   garde-fou : n'accepte que les deux écarts de code voulus
requirements.txt         mcp, starlette, uvicorn, psycopg[binary], pyjwt[crypto], python-dotenv, rhetores_authz
.env.example             les deux DSN à ne pas confondre, auth, ALLOWED_ORIGINS, PORT
```

**`rhetores_authz` est importé, pas recopié.** Le fix S11 y vit ; le dupliquer créerait une seconde
implémentation de validation de token, condamnée à diverger. Autonomie de déploiement ne veut pas dire
pile d'authentification autonome. Même raisonnement pour `user_store` : un seul registre, donc une
seule vérité sur qui est administrateur.

Le code des quatre outils est inchangé, à **deux correctifs** près, relevés au portage :

1. `_identity()` lit `claims["roles"]` (**liste**) et non `claims["role"]`. Le middleware écrit
   `{"roles": [user.role]}` et ignore délibérément le rôle porté par le token ; la clé au singulier
   n'existe donc jamais. Le module d'origine retombait de ce fait sur `user_store.get_user(oid)` à
   **chaque appel d'outil**, alors que l'information était déjà en contexte.
2. Dans `ref_adjudications`, la répartition par statut suit désormais le périmètre de la liste — elle
   portait sur toute la table même pour un non-admin filtré (§6, point refermé).

#### Mise en service — protocole `uv`, identique à `mcp-o2s-server`

> **Bascule du 2026-07-29 : `pip` + venv manuel → `uv`.** Décision de Thomas. Ce serveur adopte le
> protocole de `mcp-o2s-server` au lieu d'en avoir un propre. Un `pyproject.toml` et un `uv.lock`
> remplacent `requirements.txt` (conservé, marqué remplacé, parce que son commentaire sur le chemin
> relatif reste l'explication du choix). Écart consigné au registre — **R8**.
>
> Trois raisons, dont une qui s'est vérifiée dans l'heure :
>
> 1. **uv crée et gère le `.venv` lui-même**, donc plus d'activation : les pièges 1 et 2 du §2.0
>    disparaissent pour ce serveur au lieu d'être documentés.
> 2. **Un seul protocole pour les deux serveurs** — plus de « lequel est en pip, lequel est en uv ».
> 3. **Le lock rend l'alignement des versions vérifiable.** `requirements.txt` ne portait que des
>    `>=` : il *affirmait* aligner les versions sur `mcp-o2s-server` sans rien garantir. Le premier
>    `uv lock` a résolu **`mcp` 2.0.0**, version qui a **supprimé `mcp.server.fastmcp`** — `server.py`
>    ne s'importait plus du tout. C'est exactement la divergence que le fichier disait vouloir éviter,
>    restée invisible tant qu'aucun lock ne l'exposait.

```powershell
Set-Location "FORK-Cowork\infra\mcp_referentiels"
$env:VIRTUAL_ENV = $null        # §2.0 piège 3 : conda pose sa propre valeur

uv lock                         # résout et verrouille (45 paquets)
uv sync                         # crée le .venv et installe
uv run python -c "import server; print('server importe OK')"
```

Aucune activation, aucun chemin d'interpréteur à taper : `uv run` résout le `.venv` du projet seul.

**Puis remplir le `.env`** — il existe DÉJÀ (livré avec le fork, copie conforme du `.env.example` :
MD5 identique, vérifié). **Ne pas refaire `cp .env.example .env`**, cf. §2.0 piège 5. Trois clés :

```
JWT_SECRET=<le secret partagé>                                                  # recette HS256
REFERENTIELS_DATABASE_URL=postgresql://ref_mcp:dev@localhost:5432/rhetores_ref
USERS_FILE=../../../mcp-o2s-server/users.json
```

> ⚠️ **ET COMMENTER `JWT_AUDIENCE=` ET `JWT_ISSUER=`.** C'est le piège le plus vicieux de la chaîne,
> parce qu'il fait échouer **tous** les tokens en donnant l'impression d'un problème de signature.
> `rhetores_authz/token.py` lit ces variables ainsi :
>
> ```python
> _JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", _AZURE_AUDIENCE)
> _JWT_ISSUER   = os.environ.get("JWT_ISSUER", "rhetores-finance")
> ```
>
> `os.environ.get` ne rend son défaut que si la clé est **absente**. Or le `.env.example` livre ces
> deux lignes **présentes et vides** : l'audience et l'issuer attendus valent donc `""`, et aucun token
> réaliste ne peut valider. Symptôme constaté le 29/07 : `401 Token invalide : Invalid issuer` avec un
> secret parfaitement bon. Les défauts documentés (`api://mcp-rhetores`, `rhetores-finance`) ne
> s'appliquent que si les lignes sont **commentées**. Le même piège vaut pour le `.env.example` de
> `mcp-o2s-server`. Correctif de fond souhaitable dans le paquet partagé :
> `os.environ.get("JWT_ISSUER") or "rhetores-finance"` — à arbitrer, il touche trois consommateurs.

> **`USERS_FILE` n'est pas optionnel ici.** `users.json` **n'existe pas** dans `mcp_referentiels/` — il
> ne vit que dans `mcp-o2s-server/`. Sans `DATABASE_URL` et sans ce fichier, tout appel authentifié
> répond **403 « Utilisateur non référencé »** avec un token valide : le symptôme ressemble à un défaut
> d'auth, c'est un fichier absent. Le pointer sur le registre d'O2S **est** la bonne réponse — c'est
> l'intention « un seul registre pour les deux serveurs ». Ne pas confondre avec `USERS_JSON`, qui
> attend le **contenu JSON brut**, pas un chemin. Le champ d'identité y est nommé **`azure_oid`**
> (forme `{"users": [{azure_oid, email, role, cabinet_id, agence_id, active}]}`), et c'est lui que le
> middleware compare au claim `oid`/`sub` du token.

> **Ne pas confondre les deux DSN.** `REFERENTIELS_DATABASE_URL` désigne les référentiels ;
> `DATABASE_URL` désigne le **registre utilisateurs** (sa seule présence fait basculer `rhetores_authz`
> sur Postgres). On laisse `DATABASE_URL` **vide** en dev — c'est une configuration valide. Ne jamais
> la « corriger » en la pointant sur `rhetores_ref` : la séparation des deux bases **est** D33, et
> `server.py` journalise une erreur `dsn_confondus` si les deux se valent.

Démarrage et contrôle :

```powershell
uv run uvicorn server:app --host 127.0.0.1 --port 8001
```

```powershell
curl.exe -s http://localhost:8001/health      # second terminal — dispensé de JWT
```

Attendu : `{"status":"ok","service":"mcp-referentiels","referentiels_configures":true}`. Le drapeau à
`false` signifie que `REFERENTIELS_DATABASE_URL` manque — le serveur démarre quand même, l'import de
psycopg étant différé et le DSN n'étant résolu qu'à l'appel d'un outil. On préfère un serveur qui
répond et échoue avec un message clair à un serveur qui refuse de démarrer.

> **Port 8001, pas 8000.** 8000 est celui de `mcp-o2s-server`, 8080 celui d'Adminer : les trois
> tournent ensemble sans conflit, à condition de ne pas les confondre. (La version précédente de ce
> bloc interrogeait `/health` sur 8000 — elle testait donc l'autre serveur.)

Vérifications hors infra :

```powershell
uv run python tests\test_portage.py     # 14 contrôles, ni réseau ni base
uv run python tests\verifier_diff.py    # écart de code vs le module d'origine
```

> **Dérive de versions à connaître.** `mcp` est verrouillé à **1.29.0** ici et à **1.27.2** dans
> `mcp-o2s-server` — même majeure, API intacte, écart toléré. En revanche `mcp-o2s-server` porte
> toujours `mcp[cli]>=1.0` sans borne haute : seul son lock le protège aujourd'hui, et le prochain
> `uv lock --upgrade` y sautera en 2.0.0 avec la même panne d'import. **Y poser `<2` avant que ça
> arrive.**

> Les `tools\__pycache__\*.cpython-310.pyc` du dépôt viennent d'une vérification de syntaxe en Python
> 3.10 alors que le venv est en 3.13. Sans effet (les balises de version coexistent) et couverts par
> `.gitignore` — supprimables sans risque.

### 2.5 Brancher le MCP dans Cowork

Action d'interface, impossible depuis l'agent. Le serveur expose du streamable HTTP derrière le
middleware JWT. Vérifier que `ALLOWED_ORIGINS` couvre bien le client — le défaut est
`https://claude.ai`.

> ⚠️ **L'endpoint MCP est `/mcp`, pas `/`.** `server.py` monte `mcp.streamable_http_app()` sur `/`,
> mais ce sous-app place sa route sur `streamable_http_path` — **`/mcp` par défaut**. Un POST JSON-RPC
> sur `/` répond donc `404 Not Found`. Ce qui masque l'erreur : le middleware s'exécute **avant** le
> routage, si bien qu'un appel non authentifié sur `/` renvoie bien 401 et donne l'illusion que le
> chemin existe. Constaté le 2026-07-29 en passant du 401 au 404 dès le token valide.

Deux contrôles négatifs à passer **avant** de brancher quoi que ce soit : ils confirment que le
middleware travaille, et évitent de prendre plus tard un refus légitime pour une panne.

```powershell
# appel MCP sans token -> ATTENDU 401
curl.exe -s -o NUL -w "%{http_code}`n" -X POST http://localhost:8001/ -H "Content-Type: application/json" -d "{}"
# Origin hors allowlist -> ATTENDU 403, avec une ligne `origin_rejected` dans les logs
curl.exe -s -o NUL -w "%{http_code}`n" -X POST http://localhost:8001/ -H "Origin: https://evil.example" -d "{}"
```

> `127.0.0.1:8001` n'est **pas** joignable depuis claude.ai : le branchement suppose une exposition
> (tunnel ou déploiement). Tant qu'on reste en local, le §2.6 se vérifie avec un client MCP local
> plutôt qu'avec Cowork.

> ⛔ **Verrou : changer la signature d'un outil exige de relancer Cowork, pas seulement le serveur.**
> Le client **met le schéma des outils en cache** au moment de l'enregistrement du connecteur. Relancer
> uvicorn ne le rafraîchit pas : la session continue d'appeler l'ancienne signature. Et le mode d'échec
> est le pire qui soit — le client ne se plaint de rien, il **retire silencieusement** l'argument qu'il ne
> connaît pas, l'appel part sans lui, et l'outil répond correctement à une question qu'on ne lui a pas
> posée. Constaté le 2026-07-29 sur le paramètre `sections` de `ref_bundle` : le serveur le déclarait,
> chaque appel renvoyait le bundle entier, aucune erreur nulle part. Un paramètre sans effet est le
> symptôme le plus trompeur de la chaîne, parce qu'il ressemble à un bug de l'outil et qu'il est en
> réalité un état du client. **Après toute modification de signature : réenregistrer le connecteur et
> relancer Cowork**, puis vérifier par `tools/list` que le schéma reçu porte bien le nouvel argument.

### 2.6 Vérifier de bout en bout

Appeler `ref_bundle` depuis une session. Attendu sur une base neuve :

```json
{"schema_version": "0.1-skill", "acteurs": [], "successions": [], "gabarits": [], "isin": [],
 "compte": {"acteurs": 0, "successions": 0, "gabarits": 0, "isin": 0}}
```

Un bundle vide **est** le succès à cette étape : la chaîne client → MCP → Postgres fonctionne.

> ✅ **PASSÉ le 2026-07-29**, sans attendre le branchement Cowork. Réponse obtenue mot pour mot, plus
> `tools/list` renvoyant les quatre outils `ref_adjudications`, `ref_arbitrer`, `ref_bundle`,
> `ref_propose`. La chaîne est donc prouvée jusqu'à Postgres, y compris l'auth.

**Comment le rejouer sans Cowork.** Utile parce que `127.0.0.1:8001` n'est pas joignable depuis
claude.ai : on forge un token de recette et on parle au serveur directement.

1. Lire `JWT_SECRET` depuis le `.env`, et prendre un `azure_oid` **réel** du registre
   `mcp-o2s-server/users.json` (le middleware refuse en 403 un oid inconnu).
2. Signer en HS256 avec `aud = api://mcp-rhetores`, `iss = rhetores-finance`, `sub` **et** `oid` = cet
   azure_oid, plus `exp`. `sub` est exigé : absent **ou `None`**, PyJWT lève
   `Token is missing the "sub" claim` — son contrôle `require` teste `payload.get(c) is None`, donc une
   valeur nulle compte comme manquante.
3. POSTer sur **`/mcp`** (cf. §2.5) : `initialize`, puis `tools/list`, puis
   `tools/call` avec `{"name": "ref_bundle", "arguments": {}}`.

> Si `load_dotenv()` est appelé depuis un script vivant **hors** du dossier du projet, il ne trouve
> rien : sans argument, il remonte depuis le dossier **du script**, pas depuis le répertoire courant.
> Passer `dotenv_path` explicitement. `server.py` n'a pas ce souci, il vit dans le dossier du projet.

### 2.7 Charger le seed

Une fois le bundle vide obtenu, charger `seed/` — acteurs Gronier, successions datées, profils de
gabarit, promotion de l'ISIN v0. C'est le jalon **B4** de la roadmap, et c'est lui qui rend le test
suivant possible.

> ✅ **FAIT le 2026-07-29.** En base : **17 acteurs, 2 successions, 9 gabarits, 261 ISIN**. Deux points
> à ne pas relire de travers — **Cardif occupe deux lignes**, qui sont le même gabarit dans **deux
> fenêtres de validité** (D42), et **Wealins occupe deux lignes**, qui sont **deux gabarits distincts**
> (annuel et trimestriel). Neuf lignes ne veulent donc pas dire neuf templates. Le compte de « 7 profils »
> qui figurait ici datait d'avant le corpus étendu.

**Le test de réussite du projet**, à faire tourner à ce moment : un gabarit validé par un CGP est
visible au run suivant d'un **autre** CGP, **sans réinstallation du skill**.

---

## 3 — Le contrat du bundle

C'est la forme sur laquelle le skill se développe, indépendamment de la provenance du fichier.

```json
{
  "schema_version": "0.1-skill",
  "acteurs":     [ { "code": "...", "nom": "...", "role": "assureur|depositaire|gerant|plateforme",
                     "domiciliation": "FR|LU|CH|null", "est_depositaire_tiers": true,
                     "alias": ["..."], "payload": {} } ],
  "successions": [ { "predecesseur_code": "...", "successeur_code": "...",
                     "date_effet": "AAAA-MM-JJ", "date_cloture": null, "contexte": "..." } ],
  "gabarits":    [ { "emetteur_code": "...", "gabarit": "...",
                     "valide_depuis": "AAAA-MM-JJ", "valide_jusqu_a": null,
                     "periodicite": "...", "template_id_natif": null,
                     "signature": {}, "extraction_hints": {},
                     "champs_publies": {}, "invariant_controle": "...",
                     "emetteur_lisible": true } ],
  "isin":        [ { "isin": "...", "label": "...", "class_code": "...", "geo_code": null,
                     "sri": 4, "source": "..." } ],
  "compte": { "acteurs": 0, "successions": 0, "gabarits": 0, "isin": 0 }
}
```

> **Mis à jour le 2026-07-29 (D42).** La clé d'unicité d'un gabarit est
> `(emetteur_code, gabarit, valide_depuis)` : `valide_depuis` et `valide_jusqu_a` **font partie du
> contrat**, ils manquaient ici. `periodicite` reste dans le bundle mais n'est plus qu'une colonne
> **informative** — le matcher ne s'en sert pas, elle est renseignée par le contexte (date d'arrêté, run,
> saisie CGP). Un consommateur qui apparierait sur la périodicité travaillerait sur une valeur que le
> document ne porte pas.

**Ce document ne se lit plus systématiquement en entier.** La version précédente de ce §3 affirmait que
« les référentiels sont petits, il n'y a ni pagination ni requête par ligne ». **Mesuré le 29/07, c'est
faux** : le bundle complet fait **185 ko pour 4 936 lignes**, au-delà de ce qu'un résultat d'outil MCP
peut porter — les **261 ISIN en représentent environ 70 %** à eux seuls. Un run qui n'a besoin que des
acteurs et des gabarits n'a donc aucune raison de payer les ISIN.

D'où le paramètre **`sections`** de `ref_bundle` : un sous-ensemble de `acteurs` | `successions` |
`gabarits` | `isin`, la réponse portant `sections_retournees` pour qu'on sache ce qu'on a demandé. Sans
argument, le comportement d'origine est conservé — le bundle entier. Le fichier reste un substitut fidèle
de l'appel MCP, mais la fidélité porte désormais sur la **forme** d'une section, pas sur le fait de tout
recevoir d'un coup. *Voir le verrou du §2.5 : un `sections` déclaré côté serveur reste sans effet tant que
Cowork n'a pas été relancé, et c'est exactement ainsi que ce paramètre a paru ne rien faire.*

---

## 4 — Bascule dev → managé

La topologie retenue est un Postgres 16 managé joignable par le MCP déjà déployé — le docker local
reste la boucle de dev. Le `docker-compose.yml` le dit lui-même : cet échafaudage n'est **jamais**
déployé en prod, la cible étant Azure Database for PostgreSQL Flexible Server.

Rejouer 2.1 à 2.3 sur l'instance managée, puis changer le seul `REFERENTIELS_DATABASE_URL`. Aucun
code ne bouge — c'est l'intérêt d'avoir tout paramétré par DSN.

> **Trois adaptations sur l'instance managée.** Les blocs 2.1 à 2.3 passent par `docker exec`, qui
> n'existe pas là-bas : on attaque l'hôte directement en `psql "host=… sslmode=require"`. Le mot de
> passe `dev` de `ref_mcp` (§2.3) devient un vrai secret, à injecter par variable d'environnement et
> non à écrire dans un fichier. Et le `TEMPLATE template0` du 2.1 est inutile : Azure fournit déjà des
> bases en UTF8 / `en_US.utf8` — c'est ce qui rend la collation du dev local (§2.1) fidèle à la cible.

Tant que la base vit en local, le partage entre CGP n'est pas prouvé : c'est précisément ce que la
bascule débloque.

---

## 5 — Défaire

```powershell
# Dans la base : le schéma emporte tables, types, triggers et index.
docker exec rhetores-dev-db psql -U rhetores -d rhetores_ref -c "DROP SCHEMA ref CASCADE;"
docker exec rhetores-dev-db psql -U rhetores -d rhetores_ref -c "DROP ROLE IF EXISTS ref_mcp; DROP ROLE IF EXISTS ref_app; DROP ROLE IF EXISTS ref_admin;"
```

⚠️ Les rôles sont des objets **de cluster**, pas de base : les `DROP ROLE` ci-dessus les retirent pour
tout le serveur Postgres, `rhetores` (la projection du datahub) incluse. Sans effet aujourd'hui —
aucun objet de cette base ne leur appartient — mais à savoir avant de les rejouer.

Côté MCP : il n'y a **rien à défaire dans le code**. Le serveur étant autonome depuis D37, il suffit
d'arrêter le processus ; aucun enregistrement à retirer d'un `server.py` partagé, aucune régression
possible sur O2S. C'est exactement le bénéfice attendu de la décision du 2026-07-28. Pour neutraliser
sans arrêter, vider `REFERENTIELS_DATABASE_URL` : le serveur démarre toujours et `/health` renvoie
`referentiels_configures: false`.

---

## 6 — Points ouverts sur ce chantier

| #             | Sujet                                                                                                                                                                                                                        |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **O14** | Tranché : module co-écrit ici, déployé par Thomas.                                                                                                                                                                       |
| **R2**  | La portée de`reference_tables` (global vs par client) reste à arbitrer avec Code — cf. `REGISTRE_ECARTS.md`.                                                                                                          |
| —            | Une**connexion par appel d'outil** (pas de pool) : simple et sûr, à remplacer par un pool si le dashboard rafraîchit souvent.                                                                                       |
| ~~—~~       | ~~Fuite de compteurs globaux dans`ref_adjudications`~~ — **corrigé** au portage (2026-07-28) : la répartition suit le périmètre de la liste.                                                                   |
| —            | `requirements.txt` installe `rhetores_authz` par **chemin relatif** (`../../../rhetores_authz`) : à corriger le jour où ce serveur devient son propre dépôt.                                                 |
| —            | Le module d'origine`referentiels_skill.py` est **conservé** tant que le serveur n'a pas tourné pour de vrai ; `tests/verifier_diff.py` signale toute correction appliquée d'un seul côté. Le retirer ensuite. |
