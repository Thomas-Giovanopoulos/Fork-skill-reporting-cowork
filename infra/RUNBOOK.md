# Runbook — mise en place du store des référentiels

> Ce que ce dossier peut et ne peut pas faire : il **contient** le DDL, le module MCP et ce runbook.
> Il ne **crée** rien. Les commandes ci-dessous sont à exécuter par Thomas ; l'agent n'a aucun accès
> réseau et ne peut ni joindre Postgres, ni déployer, ni brancher un connecteur.

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

> **Avancement au 2026-07-28** : les étapes **2.1 à 2.3 sont FAITES** sur la machine de Thomas — base
> `rhetores_ref` créée, DDL exécuté, rôles `ref_app` / `ref_admin` / `ref_mcp` en place. Reprendre
> directement à **2.4**, dans sa version révisée (serveur MCP dédié, D37).

### 2.1 Créer la base et les rôles

En dev local, le Postgres du `docker-compose.yml` de `fo-data-store` suffit (image `postgres:16`,
conteneur `rhetores-dev-db`, superutilisateur `rhetores`).

```bash
docker compose up -d          # depuis fo-data-store, si ce n'est pas déjà lancé

# Base SÉPARÉE de la projection du datahub (D33) : on ne pollue pas ses tables.
docker exec -it rhetores-dev-db psql -U rhetores -d postgres -c "CREATE DATABASE rhetores_ref WITH ENCODING 'UTF8' TEMPLATE template0;"
```

> Le nom `rhetores_ref` est celui supposé par le DDL. Pour en changer, adaptez-le ici **et** dans le
> DSN de l'étape 2.4 — le DDL lui-même n'y fait pas référence.

### 2.2 Exécuter le DDL

```bash
docker cp ddl_referentiels_v0.sql rhetores-dev-db:/tmp/ddl.sql
docker exec -it rhetores-dev-db psql -U rhetores -d rhetores_ref -v ON_ERROR_STOP=1 -f /tmp/ddl.sql
```

Contrôle attendu :

```bash
docker exec -it rhetores-dev-db psql -U rhetores -d rhetores_ref \
  -c "SELECT valeur FROM ref.ref_meta WHERE cle='schema_version';"   # -> 0.1-skill
```

### 2.3 Créer le rôle de connexion

Les rôles `ref_app` et `ref_admin` sont créés par le DDL. Le rôle de **connexion** est laissé en
commentaire à dessein : il porte un mot de passe.

```bash
docker exec -it rhetores-dev-db psql -U rhetores -d rhetores_ref -c \
 "CREATE ROLE ref_mcp LOGIN NOINHERIT PASSWORD 'CHOISIR_UN_MOT_DE_PASSE';
  GRANT ref_app, ref_admin TO ref_mcp;"
```

`NOINHERIT` est le point clé : `ref_mcp` est membre des deux groupes mais n'en exerce **aucun** sans
`SET ROLE` explicite. C'est ce qui fait qu'un bug applicatif ne peut pas canoniser à la place d'un CGP
— la séparation « proposer ≠ canoniser » est portée par la base, pas par une convention.

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

Lancement :

```bash
cd infra/mcp_referentiels
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # ⚠ lire la note rhetores_authz (chemin relatif)
cp .env.example .env                 # puis remplir — cf. les DEUX DSN ci-dessous
uvicorn server:app --host 0.0.0.0 --port 8001
curl http://localhost:8001/health    # dispensé de JWT
```

**Le piège de configuration de ce serveur.** Deux variables, deux bases, à ne pas confondre :
`REFERENTIELS_DATABASE_URL` désigne les référentiels ; **`DATABASE_URL`** désigne le registre
utilisateurs (sa seule présence fait basculer `rhetores_authz` sur Postgres). Si `DATABASE_URL` est
vide *et* que `users.json` manque, tout appel authentifié répond **403 « Utilisateur non référencé »**
avec un token pourtant valide : le symptôme ressemble à un défaut d'auth, c'est un fichier absent. Ne
pas « corriger » en pointant `DATABASE_URL` sur `rhetores_ref` — la séparation des deux bases est D33.

Et la variable d'environnement, **délibérément distincte** de `DATABASE_URL` (c'est elle qui
garantit la séparation D33) :

```
REFERENTIELS_DATABASE_URL=postgresql://ref_mcp:MOT_DE_PASSE@localhost:5432/rhetores_ref
```

Dépendance : `psycopg` (v3), déjà utilisée par `DatahubStore`. L'import est différé dans le module,
donc le serveur démarre même si les référentiels ne sont pas configurés.

### 2.5 Brancher le MCP dans Cowork

Action d'interface, impossible depuis l'agent. Le serveur expose du streamable HTTP à la racine, avec
le middleware JWT. Vérifier que `ALLOWED_ORIGINS` couvre bien le client.

### 2.6 Vérifier de bout en bout

Appeler `ref_bundle` depuis une session. Attendu sur une base neuve :

```json
{"schema_version": "0.1-skill", "acteurs": [], "successions": [], "gabarits": [], "isin": [],
 "compte": {"acteurs": 0, "successions": 0, "gabarits": 0, "isin": 0}}
```

Un bundle vide **est** le succès à cette étape : la chaîne client → MCP → Postgres fonctionne.

### 2.7 Charger le seed

Une fois le bundle vide obtenu, charger `seed/` (7 profils de gabarit, acteurs Gronier, successions
datées, promotion de l'ISIN v0). C'est le jalon **B4** de la roadmap, et c'est lui qui rend le test
suivant possible.

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
  "gabarits":    [ { "emetteur_code": "...", "gabarit": "...", "periodicite": "...",
                     "template_id_natif": null, "signature": {}, "extraction_hints": {},
                     "champs_publies": {}, "invariant_controle": "...",
                     "emetteur_lisible": true } ],
  "isin":        [ { "isin": "...", "label": "...", "class_code": "...", "geo_code": null,
                     "sri": 4, "source": "..." } ],
  "compte": { "acteurs": 0, "successions": 0, "gabarits": 0, "isin": 0 }
}
```

Le skill lit ce document **en entier** : les référentiels sont petits, il n'y a ni pagination ni
requête par ligne. C'est ce qui permet au fichier d'être un substitut fidèle de l'appel MCP.

---

## 4 — Bascule dev → managé

La topologie retenue est un Postgres 16 managé joignable par le MCP déjà déployé — le docker local
reste la boucle de dev. Le `docker-compose.yml` le dit lui-même : cet échafaudage n'est **jamais**
déployé en prod, la cible étant Azure Database for PostgreSQL Flexible Server.

Rejouer 2.1 à 2.3 sur l'instance managée, puis changer le seul `REFERENTIELS_DATABASE_URL`. Aucun
code ne bouge — c'est l'intérêt d'avoir tout paramétré par DSN.

Tant que la base vit en local, le partage entre CGP n'est pas prouvé : c'est précisément ce que la
bascule débloque.

---

## 5 — Défaire

```bash
# Dans la base : le schéma emporte tables, types, triggers et index.
docker exec -it rhetores-dev-db psql -U rhetores -d rhetores_ref \
  -c "DROP SCHEMA ref CASCADE;"
docker exec -it rhetores-dev-db psql -U rhetores -d rhetores_ref \
  -c "DROP ROLE IF EXISTS ref_mcp; DROP ROLE IF EXISTS ref_app; DROP ROLE IF EXISTS ref_admin;"
```

Côté MCP : retirer l'enregistrement dans `server.py` et la variable d'environnement. Le module peut
rester en place, il ne s'active pas sans DSN.

---

## 6 — Points ouverts sur ce chantier

| #             | Sujet                                                                                                                                                                                           |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **O14** | Tranché : module co-écrit ici, déployé par Thomas.                                                                                                                                          |
| **R2**  | La portée de`reference_tables` (global vs par client) reste à arbitrer avec Code — cf. `REGISTRE_ECARTS.md`.                                                                             |
| —            | Une**connexion par appel d'outil** (pas de pool) : simple et sûr, à remplacer par un pool si le dashboard rafraîchit souvent.                                                          |
| ~~—~~     | ~~Fuite de compteurs globaux dans`ref_adjudications`~~ — **corrigé** au portage (2026-07-28) : la répartition suit le périmètre de la liste.                                        |
| —            | `requirements.txt` installe `rhetores_authz` par **chemin relatif** (`../../../rhetores_authz`) : à corriger le jour où ce serveur devient son propre dépôt.                       |
| —            | Le module d'origine`referentiels_skill.py` est **conservé** tant que le serveur n'a pas tourné pour de vrai ; `tests/verifier_diff.py` signale toute correction appliquée d'un seul côté. Le retirer ensuite. |
