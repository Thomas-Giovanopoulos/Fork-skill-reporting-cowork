# Serveur MCP des référentiels du skill (D37)

> Serveur **autonome**. Il ne se greffe pas sur `mcp-o2s-server` — décision de Thomas du 2026-07-28,
> qui remplace la version initiale du RUNBOOK §2.4. Motifs : cycle de vie et déploiement indépendants,
> aucun risque de régression sur O2S, et au moment de la convergence datahub on débranche un serveur
> entier plutôt que de démêler un module.

Expose quatre outils sur la base `rhetores_ref` : `ref_bundle`, `ref_propose`, `ref_adjudications`,
`ref_arbitrer`. Le pas-à-pas de mise en service est dans [`../RUNBOOK.md`](../RUNBOOK.md) §2.4 à §2.7.

## Démarrer

Protocole **uv**, le même que `mcp-o2s-server` depuis le 2026-07-29 (écart R8 du registre ; l'ancienne
séquence `venv` + `pip` est décrite dans `requirements.txt`, conservé mais remplacé).

```powershell
cd infra/mcp_referentiels
$env:VIRTUAL_ENV = $null                  # si conda est actif : il pose sa propre valeur
uv sync                                   # crée le .venv et installe (lock : 45 paquets)
# le .env est livré = copie du .env.example → le REMPLIR, ne pas le recopier par-dessus
uv run uvicorn server:app --host 127.0.0.1 --port 8001
curl.exe -s http://localhost:8001/health
```

Aucune activation de venv : `uv run` résout l'interpréteur du projet seul — ce qui évite au passage
que `source .venv/bin/activate` (faux deux fois sous Windows) soit jamais nécessaire. Pas-à-pas complet
et pièges de configuration dans [`../RUNBOOK.md`](../RUNBOOK.md) §2.0 et §2.4.

`/health` est dispensé de JWT et répond
`{"status":"ok","service":"mcp-referentiels","referentiels_configures":true|false}`. Le serveur
**démarre même sans** `REFERENTIELS_DATABASE_URL` : l'import de psycopg est différé, le DSN n'est
résolu qu'à l'appel d'un outil. On préfère un serveur qui répond et échoue avec un message clair à un
serveur qui refuse de démarrer.

> ⚠️ **Changer la SIGNATURE d'un outil demande de relancer Cowork, pas seulement le serveur.** Le
> client met le schéma des outils en **cache** : après un simple redémarrage d'`uvicorn`, le nouveau
> *code* tourne bien, mais un argument que le schéma en cache ne déclare pas est **silencieusement
> retiré de l'appel**. Constaté le 2026-07-29 sur `ref_bundle(sections=[...])` : le corps de réponse
> prouvait le nouveau code (`sections_retournees` présent, champs d'audit élagués) tandis que le
> paramètre était ignoré — donc un comportement de « paramètre sans effet », le plus trompeur qui soit.
> Modifier le corps d'un outil : redémarrer le serveur suffit. Modifier sa signature : relancer Cowork.

> ⚠️ Deux points vérifiés à la première mise en service, qui coûtent une heure chacun :
> **l'endpoint MCP est `/mcp`**, pas `/` (le mount est à la racine, mais `streamable_http_app()` place
> sa route sur `streamable_http_path`, défaut `/mcp` — et un POST non authentifié sur `/` renvoie 401,
> pas 404, ce qui masque l'erreur) ; et **`JWT_AUDIENCE=` / `JWT_ISSUER=` vides dans le `.env` doivent
> être commentées**, sinon `token.py` prend `""` pour valeur attendue au lieu de son défaut et **tout**
> token est rejeté en `Invalid issuer`.

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

**4 — `ref_bundle` prend un paramètre `sections`, et le payload perd ses champs d'audit.** La version
initiale affirmait « les référentiels sont petits et lus en entier : pas de pagination ». C'était vrai
sur une base vide, et faux au **premier chargement réel** : 185 ko sur 4 936 lignes, **au-delà de ce
qu'un résultat d'outil MCP peut porter**. Les 261 ISIN en font près de 70 % à eux seuls, alors que la
plupart des besoins d'un run ne portent que sur les gabarits. `created_at`, `updated_at`, `version` et
`validated_by` sortent du bundle — ils restent en base ; `provenance` et `confiance` sont conservés,
étant des enums courts et de l'information métier (B9). Le `compte` porte **toujours** sur les quatre
tables, même quand une seule est demandée : sans quoi un appel partiel se lirait comme une base à moitié
vide.

**5 — D42 : la clé de conflit des gabarits devient `(emetteur_code, gabarit, valide_depuis)`.** Cf.
`../migration_001_d42_fenetre_validite.sql`. `periodicite` cesse d'être requise — l'exiger obligerait
l'appelant à inventer une valeur que le document ne porte pas chez trois émetteurs sur quatre.

**6 — Le serveur annonce son contrat et RENVOIE ce qu'il a reçu.** Correctif du retrait silencieux
d'arguments, constaté **deux fois** le 2026-07-29 : le client MCP met le schéma des outils en cache, et
un client périmé **retire de l'appel un argument qu'il ne connaît pas, sans aucune erreur**. La première
fois, `sections` a été ignoré et tout le bundle est revenu. La seconde, plus grave, une proposition a
été enregistrée avec ses trois champs de provenance à `null` alors qu'ils avaient été passés — donc une
provenance qui **paraissait vide par choix de l'appelant** quand elle avait été perdue en transport. Un
arbitre n'avait aucun moyen de le savoir.

**La fausse bonne idée, écartée.** Faire déclarer sa version au client : alors un appelant parfaitement
à jour qui ne remplirait pas ce champ serait accusé d'être en retard. On échangerait un faux négatif
silencieux contre un faux positif bruyant — et un contrôle qui accuse à tort est un contrôle qu'on
apprend à ignorer.

**Ce qui a été retenu**, en partant de ce qu'on peut savoir avec certitude : non pas ce que le client
*est*, mais ce que le serveur *a reçu*.

- Le serveur annonce **son** contrat (`contrat_outil`, valeur `2026-07-29.d44`) dans chaque réponse.
- Chaque écriture **renvoie ce qu'elle a reçu** : `provenance_recue` pour `ref_propose`,
  `sections_recues` pour `ref_bundle`. Un argument retiré en route se voit **immédiatement**.
- Quand le résultat est ambigu — provenance vide, ou `sections` absent — la réponse énonce **les deux
  lectures possibles** et dit quoi faire, sans en choisir une.

C'est descriptif, donc **sans faux positif possible**, et cela couvre **tout** argument perdu, pas
seulement ceux qu'on avait anticipés. Neuf contrôles l'ancrent dans `tests/test_portage.py`, dont un qui
vérifie qu'aucun libellé n'affirme que le client est périmé.

> **Corollaire opérationnel** : ce correctif ne change **aucune signature**, seulement des valeurs de
> retour. Un **redémarrage du serveur suffit**, sans relancer Cowork. C'est la règle du RUNBOOK §0 dans
> le bon sens : corps d'outil → serveur ; signature → serveur *et* client.

### Le garde-fou de diff a menti deux fois, et c'était le grain à chaque fois

`tests/verifier_diff.py` compare les deux modules hors docstrings et commentaires. Son histoire vaut
d'être connue, parce qu'un contrôle qui passe à tort est pire qu'aucun contrôle.

**Version 1, ligne à ligne avec des fragments admis.** Elle a validé le changement de clé D42 **sans le
signaler** : `ast.unparse` écrase tout `_SPECS` sur une seule ligne, laquelle contient `'role'` —
fragment admis pour une raison sans rapport (la spec `acteur` a un champ requis nommé `role`). Une
modification de schéma approuvée par coïncidence de sous-chaîne.

**Version 2, au grain de la définition.** Correcte sur `_SPECS`, mais elle a laissé passer la réécriture
de `ref_bundle` : celle-ci vit dans `register`, déjà déclarée modifiable pour `ref_adjudications`. Une
seule autorisation couvrait les quatre outils.

**Version 3, définitions imbriquées comprises.** Les fonctions internes sont extraites sous `parent.enfant`
et remplacées par un marqueur dans le corps du parent. `register.ref_bundle` et
`register.ref_adjudications` sont donc deux écarts distincts, chacun avec son motif. Vérifié dans les deux
sens : vert sur copie fidèle, et sur une copie où l'on glisse une décision `peut_etre` dans `ref_arbitrer`,
il désigne **`register.ref_arbitrer`** nommément.

Les définitions **ajoutées** doivent être déclarées elles aussi, et un écart déclaré qui ne se produit
plus est signalé comme du bruit à retirer — c'est précisément ce qui avait permis au faux négatif de la
version 1 d'arriver.

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
