# Serveur MCP des référentiels du skill (D37)

> Serveur **autonome**. Il ne se greffe pas sur `mcp-o2s-server` — décision de Thomas du 2026-07-28,
> qui remplace la version initiale du RUNBOOK §2.4. Motifs : cycle de vie et déploiement indépendants,
> aucun risque de régression sur O2S, et au moment de la convergence datahub on débranche un serveur
> entier plutôt que de démêler un module.

Expose quatre outils sur la base `rhetores_ref` : `ref_bundle`, `ref_propose`, `ref_adjudications`,
`ref_arbitrer`. Le pas-à-pas de mise en service est dans [`../RUNBOOK.md`](../RUNBOOK.md) §2.4 à §2.7.

## Démarrer

```bash
cd infra/mcp_referentiels
python3 -m venv .venv && source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt                        # ⚠ lire la note rhetores_authz du fichier
cp .env.example .env                                   # puis remplir
uvicorn server:app --host 0.0.0.0 --port 8001
curl http://localhost:8001/health
```

`/health` est dispensé de JWT et répond `{"status":"ok","referentiels_configures":true|false}`. Le
serveur **démarre même sans** `REFERENTIELS_DATABASE_URL` : l'import de psycopg est différé, le DSN
n'est résolu qu'à l'appel d'un outil. On préfère un serveur qui répond et échoue avec un message clair
à un serveur qui refuse de démarrer.

## Les deux variables qu'il ne faut pas confondre

C'est le piège de configuration de ce serveur, et il produit un symptôme trompeur.

| Variable | Désigne | Effet de son absence |
|---|---|---|
| `REFERENTIELS_DATABASE_URL` | la base des **référentiels** (`rhetores_ref`) | les outils `ref_*` échouent avec un message explicite |
| `DATABASE_URL` | le **registre utilisateurs** — qui est admin | bascule sur `users.json` / `USERS_JSON` |

Elles ne pointent pas la même base, et cette séparation **est** D33. Conséquence pratique : si
`DATABASE_URL` est vide *et* que `users.json` manque, tout appel authentifié répond
**403 « Utilisateur non référencé »** alors que le token est parfaitement valide. Le symptôme ressemble
à un problème d'authentification ; c'est un fichier absent. Ne pas « corriger » en pointant
`DATABASE_URL` sur `rhetores_ref`.

## Ce qui est repris, et ce qui a changé

Le framework est calqué sur `mcp-o2s-server` : Starlette + FastMCP en streamable HTTP, `JWTAuthMiddleware`,
sonde `/health`, logging JSON. `logging_config.py` est repris verbatim — les deux serveurs doivent
produire des lignes de même forme pour être lisibles dans le même agrégateur.

**`rhetores_authz` est importé, pas recopié.** Le fix S11 (`aud` *et* `iss` vérifiés en HS256 comme en
RS256) y vit. En dupliquer le code créerait une seconde implémentation de validation de token,
condamnée à diverger : au prochain correctif du paquet partagé, ce serveur resterait vulnérable sans
que rien ne le signale. Un serveur MCP autonome ne veut pas dire une pile d'authentification autonome.
Même raisonnement pour `user_store` : **un seul** registre pour les deux serveurs, donc une seule
vérité sur qui est administrateur.

Trois écarts assumés par rapport au module d'origine `../referentiels_skill.py` :

**1 — `_identity()` lit `roles` (liste), non `role` (singulier).** Le middleware écrit
`{"roles": [user.role]}` et **ignore délibérément** tout rôle porté par le token. Le module d'origine
lisait `claims["role"]`, clé jamais produite : il retombait donc systématiquement sur
`user_store.get_user(oid)`, soit un accès au registre — lecture disque ou requête — à *chaque appel
d'outil*, alors que l'information était déjà en contexte. Les replis (singulier, puis registre) restent
en place pour des claims d'une autre provenance, mais ne sont plus le chemin normal.

**2 — `ref_adjudications` calcule sa répartition sur le périmètre de l'appelant.** Elle portait sur
toute la table même pour un non-admin dont la liste est filtrée : un CGP apprenait le volume global de
propositions de ses confrères. Fuite modeste, mais gratuite. Point ouvert du RUNBOOK §6, refermé ici.

**3 — l'allowlist d'audit gagne quatre clés** : `cible`, `nature`, `decision`, `statut`. Ce sont des
énumérations fermées, validées avant usage, qui ne peuvent porter aucune donnée client. Les rédiger
aurait rendu la piste d'audit de l'arbitrage inutilisable — « qui a accepté quoi » est précisément ce
qu'on doit pouvoir relire, et c'est la contrepartie du privilège admin (D34). `cle`, `proposition`,
`motif`, `commentaire`, `source_document` et `run_id` restent rédigés.

Aucun autre écart : `python3 tests/verifier_diff.py` compare les deux modules **hors docstrings et
commentaires** et n'accepte que ces deux correctifs de code.

## Vérifier sans infra

```bash
python3 tests/test_portage.py     # 14 contrôles — logique pure, ni réseau ni base
python3 tests/verifier_diff.py    # écart de code vis-à-vis du module d'origine
```

Les deux correctifs portent sur de la logique pure, donc testables avec des bouchons. Le premier se
mesure en **comptant les accès au registre** : le comportement observable est inchangé, seul le nombre
d'accès diffère — un test de valeur de retour ne l'aurait pas attrapé.

Tout ce qui touche la base (`_tx`, l'UPSERT canonique, l'atomicité de l'arbitrage) reste hors portée
ici et se vérifie au RUNBOOK §2.6 : appeler `ref_bundle` sur une base neuve, où **un bundle vide est le
succès attendu**.

## Points ouverts

- Une **connexion par appel d'outil**, pas de pool : simple et sûr, à remplacer si le dashboard
  d'adjudication rafraîchit souvent.
- `requirements.txt` installe `rhetores_authz` par **chemin relatif** (`../../../rhetores_authz`). À
  corriger le jour où ce dossier devient son propre dépôt — ou installer le paquet dans le venv une
  fois pour toutes.
- Les dossiers `__pycache__` de ce répertoire ont été produits par la vérification de syntaxe et n'ont
  pas pu être supprimés depuis l'agent (autorisation par dossier). Sans effet, `.gitignore` les couvre.
