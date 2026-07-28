# Journal du fork

> Une ligne par intervention sur `skill/`. Complète `REGISTRE_ECARTS.md`, qui ne
> traite que les **écarts de schéma** ; ici on trace les **modifications de code**.
> Tenu au fil de l'eau, comme le registre.

---

## 2026-07-28 — Ouverture du fork

**Mise en place**

- Fork créé à partir du paquet `reporting-fo-rhetores-alt` installé (merge HANAMI du 27/07) :
  118 fichiers, caches Python exclus.
- `BASELINE_MD5.txt` enregistrée — état de référence à l'ouverture (M6).
- `verifier_empreinte.sh` — outil de comparaison baseline ↔ état courant, exclut les caches.
- `REGISTRE_ECARTS.md` ouvert avec 6 entrées déjà connues (R1–R6).
- Documents de conception versés dans `docs/`, livrables d'infra dans `infra/`.

**Environnement**

- `jsonschema` porté de 3.2.0 à 4.26.0 (`Draft202012Validator` requis par `store_builder.py`) —
  **T4 levé**. À refaire dans tout nouvel environnement : `pip install -U jsonschema`.
- `chmod -R u+w skill/` : la copie depuis le cache du skill installé hérite du mode lecture seule,
  ce qui bloque toute édition. À savoir si le fork est recréé.

**État de référence vérifié**

| Contrôle | Résultat |
|---|---|
| `p1_engine/selfcheck.py` | Self-check OK — paquet intègre, environnement prêt |
| `pipeline/test_store_builder.py` | Tous les tests passent (5 assertions) |
| `p1_engine/tests/run_tests.py` | **7/7 fixtures OK**, QC 9/9, rendus déterministes |

---

### T3 — `run_tests.py` : répertoire temporaire propre et erreurs visibles

**Fichier** : `skill/p1_engine/tests/run_tests.py` · **Chantier** : A2 (hygiène préalable)

**Symptôme rencontré en vrai, avant toute modification.** La régression échouait sur
`subprocess.CalledProcessError` nu, sans message. Diagnostic : `/tmp/_reg*` contenait des résidus
d'un run du 27/07 appartenant à `nobody`, donc l'écriture échouait en `PermissionError`. Exécutée à la
main vers un autre chemin, la même commande sortait en code 0. **Le symptôme ressemblait à une
régression moteur alors qu'il n'en était pas une** — c'est exactement ce que décrivait T3.

**Deux causes, deux correctifs.** Le chemin en dur n'était que la moitié du problème :

1. `TMP = Path(tempfile.mkdtemp(prefix="reg_"))` — un répertoire par run, plus aucune collision
   inter-utilisateurs. Nettoyé dans un `finally`, donc sans résidu pour le run suivant.
2. Nouvelle fonction `_run(argv, label)` — l'ancien `check=True` + `capture_output=True` **avalait
   stderr**. Un échec affiche désormais l'étape, le code de retour, stderr et stdout. Sans ce second
   correctif, le prochain vrai bug moteur coûterait le même temps de diagnostic.

**Vérification** : régression 7/7, QC 9/9, déterminisme confirmé, aucun résidu dans `/tmp`.
`verifier_empreinte.sh` ne signale que ce fichier comme modifié.

**Pas d'entrée au registre des écarts** : c'est un correctif de code, aucune forme de schéma touchée.

---

### O11 — documents composites : tranché empiriquement

**Question** : un PDF composite donne-t-il un profil, ou un profil par sous-template ?

**Méthode** : plutôt que de trancher en théorie, détection des frontières de segments sur les deux
exemplaires Wealins, volontairement dissemblables — 26 pages / 2 FID contre 15 pages / 1 FID.

**Résultat** — structure identique, frontières nettes sur les deux :

| Segment | Marqueur | FC051727 | FC055211 |
|---|---|---|---|
| Adresse | ni pagination ni pied de page légal | p1 | p1 |
| Corps réglementaire | pied de page fax-A + pagination locale `n/N` | p2–8 | p2–6 |
| Loi Pacte | **pied de page à fax différent, AUCUNE pagination** | p9 | p7 |
| Annexe booklet | `<booklet>` puis `Page n / M` | p10–26 | p8–15 |

**Décision** : **un profil composite, avec segments déclarés**, drift évalué **par segment**. Un seul
appariement, aucune couche de matching supplémentaire ; mais une évolution de la seule page Loi Pacte
— la plus susceptible de bouger, étant réglementaire — produit une proposition ciblée au lieu
d'invalider tout le profil. Le fait que cette page porte un **autre numéro de fax** prouve qu'elle est
produite par un autre générateur : les cycles de vie sont bien indépendants.

**Coût structurel : nul.** `extraction_hints` est déjà une colonne JSONB — les segments sont des
données, pas un changement de schéma. Cf. registre R7.

**Piège découvert en cours de route** : mon premier détecteur attrapait des **dates** (`27/01`,
`31/12`, `13/03`) avant la vraie pagination — dans ce document, `\d+/\d+` est ambigu. Consigné dans
les `extraction_hints` du profil Wealins : ancrer la pagination du corps sur un dénominateur petit et
constant, et celle de l'annexe sur le préfixe littéral « Page ».

---

### A4 — seed des référentiels produit

**Fichiers** : `seed/acteurs.json`, `seed/successions.json`, `seed/gabarits.json`,
`seed/construire_bundle.py` · **Chantier** : A4

Un script rejouable, deux sorties depuis une source unique :

- `seed/referentiels.json` — le bundle au format du contrat, **utilisable immédiatement par le skill**,
  sans aucune infra. C'est le substitut fidèle de l'appel MCP `ref_bundle` (D35/D36).
- `seed/seed.sql` — 287 `INSERT` idempotents (`ON CONFLICT DO UPDATE`) pour le chargement en base (B4).

**Contenu** : 17 acteurs, 2 successions datées, 7 profils de gabarit, 261 ISIN promus de l'asset v0.

**Contrôles d'intégrité avant écriture** (rien ne sort si ça échoue) : unicité des codes d'acteur,
unicité du couple (émetteur × gabarit × périodicité), et toute référence d'acteur résolue — la clé
étrangère est ce qui chaîne les deux tables (D22).

**Vérifications faites** : bundle conforme au contrat, 40 blobs JSONB tous valides après passage en
SQL, segments Wealins préservés, apostrophes équilibrées sur toutes les lignes exécutables.

**Deux règles que je me suis imposées sur les acteurs** :

- **Aucune identité devinée.** Nortia et l'émetteur Himalia ne sont pas lisibles en texte (logo
  image). Nortia est nommé par une source fiable ; l'émetteur Himalia reçoit le code explicite
  `himalia_emetteur_a_confirmer`, en confiance `low`, avec la question ouverte inscrite dans son
  payload. Un nom plausible circule : il n'est **pas** inscrit.
- **`domiciliation` à null quand elle n'est pas établie.** Sept acteurs sur dix-sept sont dans ce cas.
  Mieux vaut un trou visible qu'une valeur inventée qui basculerait un contrat en FR ou LU.

**Correction d'une donnée du salvage** : le référentiel ISIN compte **44** entrées sans géographie, pas
212 — la validation CGP du 24/07 en avait déjà complété 173. E6 est donc bien plus petit qu'annoncé.

---

### Outillage — `regenerer_checksums.py` (le maillon qui manquait)

**Découverte, en constatant l'effet de ma propre modification.** `p1_engine/selfcheck.py` contrôle la
taille et le md5 de chaque fichier contre `CHECKSUMS.json`. Après le correctif T3, le selfcheck
échouait avec :

```
✗ p1_engine/tests/run_tests.py : taille 4786 != 3596 attendue (troncature probable)
```

Deux problèmes dans ce seul message. D'abord l'étape 0 du protocole du skill impose **STOP** si le
selfcheck échoue : **toute modification légitime rend donc le skill inutilisable**. Ensuite le message
oriente vers un faux diagnostic — « troncature probable » suggère un paquet corrompu et une
réinstallation, alors que le fichier est parfaitement valide.

Aucun générateur de `CHECKSUMS.json` n'existait dans le paquet. `regenerer_checksums.py` comble ce
trou, avec un mode `--verifier` qui n'écrit rien.

**Nouvelle règle de travail du fork** : après toute modification de `skill/`, lancer
`python3 regenerer_checksums.py` puis `python3 skill/p1_engine/selfcheck.py`. C'est désormais dans le
README.

---

### A2 — hygiène préalable : renommage D31 et correction T2

**Chantier** : A2 · **Clôt** : T1, T2 (T3 et T4 déjà réglés à l'ouverture)

**D31 — `historique` → `rendement_annuel`.** La clé désignait le bloc *Rendement annuel*, alors que le
tableau *Historique du patrimoine* vit dans le bloc `supervision`. Deux objets, un seul mot : quiconque
écrirait le mapping store→manifeste se tromperait naturellement. Le template portait d'ailleurs déjà
le commentaire « BLOC — RENDEMENT ANNUEL », ce qui confirmait le diagnostic.

Douze remplacements sur sept fichiers, plus le renommage du template
(`blocs/historique.html.j2` → `blocs/rendement_annuel.html.j2`). Appliqués par script avec
**assertion du nombre d'occurrences attendu pour chacun** — aucun remplacement partiel toléré, le
script échoue en bloc plutôt que de laisser le paquet à moitié migré. La clé de données
`data.historique` a été renommée aussi : la laisser alimenter `rendement_annuel` aurait perpétué
exactement la confusion que D31 vient lever.

`historique_annuel` (catégorie du store) et « Historique du patrimoine » (tableau de supervision)
sont **intacts** — vérifié explicitement.

**T2 — description périmée.** `manifest.schema.json` annonçait « ordre canonique figé » sur **sept**
blocs, alors que `BLOCK_ORDER` en compte **neuf** (`performance_nc` et `rendement_annuel` intercalés
après `performance`). Corrigé, avec la mention explicite que la source de vérité est `BLOCK_ORDER`.
Contrôle croisé ajouté à la volée : les neuf noms du schéma et ceux de `BLOCK_ORDER` coïncident
exactement, dans les deux sens.

**Vérification** : selfcheck OK · régression **7/7, QC 9/9, déterministe** — donc un renommage à
comportement strictement identique.

---

### Point à trancher — le bloc `rendement_annuel` est-il vraiment affiché ?

Trouvé en lisant `base.html.j2` pour le renommage, et **non modifié** à dessein :

```jinja
{% if blocs_enabled.rendement_annuel and reporting.mode != 'presentee' %}
```

Deux conditions, à deux endroits différents. `blocs_enabled` porte la **faisabilité** (le client a un
historique) tandis que le template ajoute une **intention** (`mode != 'presentee'`) qui n'est déclarée
nulle part dans le manifeste. C'est précisément le défaut que §1.6 du CDC dénonce pour les blocs, et
que D28 veut supprimer.

Conséquence concrète : en mode `presentee` — le mode principal, celui qui part chez le client — ce bloc
**ne s'affiche jamais**, quelle que soit la donnée. Or D29a a acté « si la donnée est là, on affiche
l'historique, sans question ».

Il y a donc une contradiction entre le comportement actuel et la décision prise. Je ne l'ai pas
tranchée seule : l'activer changerait le rendu de **tous** les clients en version présentée et ferait
bouger le golden des fixtures. À arbitrer avec Thomas avant A3.

---

### Suppression du bloc Rendement annuel, avec relocalisation de la synthèse annualisée

**Décision Thomas** : le bloc est déprécié au profit du tableau *Historique du patrimoine*, donc à
supprimer — mais en re-logeant l'annualisé.

**Vérification faite avant de supprimer.** Les deux objets lisent le même onglet Historique, mais le
tableau en fait bien plus : il porte la performance annuelle **et** valeur coté, non coté, patrimoine,
allocation, flux nets, perf en €, perf cumulée. Aucune donnée brute ne disparaît.

**Ce que la lecture du code a révélé, et qui a changé le geste.** Le bloc ne contenait pas « un chiffre
annualisé » mais un **tableau synthétique complet** : YTD, 3, 5, 10 ans et depuis lancement, ventilés
poche cotée / poche non cotée / global, avec pondération. Rien de tout cela n'existe ailleurs — le
tableau Historique donne des performances **par période**, pas des annualisés **par horizon**. La
relocalisation était donc plus qu'un ornement.

**Geste retenu, choisi pour le risque minimal** : le calcul de `H` reste intégralement en place (le
retirer aurait été un risque sans gain) ; seule la clé exposée change —
`data["rendement_annuel"]=H` devient `data["annualise"]=H.get("synth")` — et le widget est rendu
**sous** le tableau Historique, en pleine largeur. Le reste de `H` (graphe, repères, texte de marché)
n'est plus consommé : dette assumée et notée, à nettoyer plus tard.

Retraits : entrée de `BLOCK_ORDER`, propriété du schéma, clé de l'exemple, inclusion dans
`base.html.j2`, émission dans `excel_to_manifest.py`, variable `_has_hist` devenue inutile, et le
fichier `blocs/rendement_annuel.html.j2`. **Huit blocs** désormais, au lieu de neuf.

**Un oubli rattrapé par mon propre correctif T3.** Le premier essai a échoué sur
`Manifeste invalide : Additional properties are not allowed ('rendement_annuel' was unexpected)` :
j'avais retiré la propriété du schéma mais pas son émission. Sans la remontée de `stderr` ajoutée à
l'ouverture du fork, ce serait remonté en `CalledProcessError` nu — le correctif s'est payé le jour
même.

**Deux problèmes trouvés au passage, corrigés**

1. **Fuite de commentaire interne dans le document client.** Mon commentaire de relocalisation était en
   `<!-- -->`, donc **émis dans le HTML livré** — un deck client contenait les mots « bloc supprimé » et
   « déprécié ». Converti en commentaire Jinja `{# #}`, qui n'est pas rendu. Le commentaire voisin
   préexistant, qui décrivait l'implémentation du tableau, a été assaini de la même façon.
2. **Ma formulation « à côté du tableau » était trompeuse** (relevé par Thomas) : le tableau Historique
   occupe toute la largeur, rien ne tient à côté. Le widget est bien **sous** lui. Corrigé dans les
   commentaires du code.

### Trou de couverture à signaler — l'onglet Historique n'est testé par AUCUNE fixture

Constaté en cherchant à vérifier le widget : **aucune des 7 fixtures ne possède d'onglet Historique.**

Conséquences :

- le bloc supprimé n'était **jamais** exercé par la régression — d'où son passage à 7/7 sans broncher ;
- les **lignes annuelles du tableau Historique du patrimoine** ne sont pas testées non plus, alors
  qu'elles restent en production ;
- la synthèse annualisée, son calcul géométrique et sa pondération inter-poches sont hors couverture.

**Vérification menée malgré tout**, avec une fixture jetable créée dans `/tmp` (hors du fork, pour ne
pas déplacer le golden) : `fx_noncote` enrichie de 7 années d'historique. Résultat — widget présent,
3 lignes (coté / non coté / global), horizons **YTD · 3 ans · 5 ans** (le « 10 ans » absent à juste
titre, l'historique n'ayant que 7 années), pondération 59 % / 41 %, identités comptables **9/9**, et
aucune fuite de commentaire.

**Recommandation** : ajouter une 8ᵉ fixture avec onglet Historique. Elle couvrirait d'un coup les
lignes annuelles du tableau et la synthèse annualisée. Cela **fera bouger le golden** (une entrée de
plus), donc c'est une décision à prendre, pas un geste à glisser.

### État de la vérification après suppression

| Fixture | Valeurs vs golden | QC | Déterminisme |
|---|---|---|---|
| fx_lignes_classes | conforme | 9/9 | oui |
| fx_limites | conforme | 9/9 | oui |
| fx_minimal | conforme | 9/9 | oui |
| fx_multiholdings | conforme | 9/9 | oui |
| fx_no_portfolio | conforme | 4/4 | oui |
| fx_noncote | conforme | 9/9 | oui |
| fx_simple | conforme (2 929 000 € / 0 € / 2 929 000 €) | 9/9 | **non rejoué** |

Six fixtures sur sept vérifiées en passe complète. Pour `fx_simple`, les trois valeurs et le QC ont
été confirmés par un rendu isolé, mais le second rendu de contrôle du déterminisme n'a pas pu être
rejoué : le sandbox s'est fortement dégradé en fin de session (un rendu passé de ~2 s à ~20 s), au
point que la régression complète dépasse la limite d'un appel. À rejouer d'un bloc au prochain
démarrage :

```bash
cd skill/p1_engine && python3 tests/run_tests.py
```

Rien n'indique un problème de déterminisme : mon changement n'introduit aucune source de variabilité,
et les six autres fixtures le confirment.

**Note d'environnement** : le script de régression n'imprime qu'à la fin (le dict de résultats est
construit avant tout affichage). Sur un sandbox lent, on ne distingue donc pas un run long d'un blocage
— j'ai perdu du temps là-dessus. Un affichage incrémental par fixture serait un petit gain réel.

---

## 2026-07-28 (2) — Régression rejouée · serveur MCP dédié écrit (D37)

Session en environnement neuf. **Aucune modification de `skill/`** : l'empreinte est inchangée
(9 fichiers modifiés + 1 supprimé, exactement ceux de la session précédente), donc pas de régénération
de checksums nécessaire.

**Régression — le trou de la session précédente est refermé**

`fx_simple` n'avait pas pu être rejouée pour le contrôle de déterminisme (6/7 vérifiées). C'est fait :
**7/7, QC vert partout, déterminisme confirmé sur les sept**. Aucune dégradation — 5,6 à 8,1 s par
fixture, loin des ~20 s observés en fin de session précédente : le ralentissement était bien un état du
sandbox, pas une régression du moteur. `selfcheck.py` OK, manifeste à jour (116 fichiers, aucun écart).

**Deux pièges d'environnement, dont un mal diagnostiqué la fois précédente**

Le sandbox coupe chaque appel bash à **45 s** *et* exécute chaque appel dans un **namespace PID isolé** :
toute tâche de fond est tuée au retour de l'appel. Un `nohup … &` suivi de sondages ne fonctionne donc
pas — et le sondage lui-même trompe, `pgrep -f run_tests.py` s'appariant à la ligne de commande du shell
qui le contient (faux « encore en cours » indéfiniment). `run_tests.py` est de ce fait **inexécutable
d'un seul trait** ici, indépendamment de la lenteur : la note de la session précédente attribuait à la
dégradation du sandbox ce qui est une limite structurelle.

Contournement : `run_one.py`, **hors `skill/`** pour ne pas déclencher la régénération des checksums. Il
importe `run_tests.py` et réutilise `measure()` **tel quel** — aucune logique de contrôle réécrite, donc
aucun risque de divergence avec le golden —, traite les fixtures nommées en argument et écrit son cumul
sur disque. Règle accessoirement le grief « affichage incrémental ».

**D37 — `infra/mcp_referentiels/` écrit**

Serveur MCP autonome, framework calqué sur `mcp-o2s-server` (monté en lecture seule pour l'occasion).
Sept modules + deux scripts de vérification ; détail dans `infra/mcp_referentiels/README.md`, RUNBOOK
§2.4 réécrit.

Le choix structurant : **`rhetores_authz` est importé, pas recopié.** Le fix S11 (`aud` *et* `iss`
vérifiés en HS256 comme en RS256) y vit ; en dupliquer le code donnerait deux implémentations de
validation de token, et ce serveur resterait vulnérable au prochain correctif du paquet partagé sans que
rien ne le signale. Autonomie de déploiement ≠ pile d'authentification autonome. Idem `user_store` : un
seul registre pour les deux serveurs, donc une seule vérité sur qui est administrateur.

**Deux défauts trouvés dans `referentiels_skill.py` en le portant**

1. `_identity()` lisait `claims["role"]` au **singulier**. Le middleware écrit `{"roles": [user.role]}`
   et ignore délibérément le rôle porté par le token : la clé au singulier n'existe **jamais**. Le
   prédicat retombait donc systématiquement sur `user_store.get_user(oid)` — lecture disque ou requête —
   à **chaque appel d'outil**, alors que l'information était déjà en contexte. Le commentaire « le rôle
   est lu des claims s'il y figure déjà » décrivait un chemin mort. Corrigé ; les replis sont conservés
   pour des claims d'une autre provenance.
2. La fuite de compteurs de `ref_adjudications` (RUNBOOK §6) est refermée : la répartition par statut
   suit le périmètre de la liste retournée.

Un troisième écart, assumé : l'allowlist d'audit gagne `cible`, `nature`, `decision`, `statut` — des
énumérations fermées, sans donnée client. Les rédiger rendait la piste d'audit de l'arbitrage
inutilisable, alors que « qui a accepté quoi » est la contrepartie du privilège admin (D34).

**Vérification, sans réseau ni base**

- `tests/test_portage.py` — 14 contrôles, tous verts. Le correctif n°1 est vérifié en **comptant les
  accès au registre** : le comportement observable est inchangé, seul le nombre d'accès diffère, donc un
  test de valeur de retour ne l'aurait pas attrapé.
- `tests/verifier_diff.py` — compare les deux modules **hors docstrings et commentaires** (AST) et
  n'accepte que les deux correctifs : 17 lignes d'écart, 0 inattendue. Transforme « j'ai recopié
  fidèlement 400 lignes » en assertion vérifiable, et signalera ensuite toute correction appliquée d'un
  seul côté.

Ce qui reste hors portée ici et ne peut pas l'être autrement : tout ce qui touche Postgres. Se vérifie
au RUNBOOK §2.6, où **un bundle vide est le succès attendu**.

**Résidu** : les `__pycache__` produits par la vérification de syntaxe n'ont pas pu être supprimés
(autorisation par dossier). Sans effet, couverts par le `.gitignore` ajouté.

**Arbitrages de Thomas en fin de session**

- **D38 — un profil de gabarit par template**, jamais un profil fonctionnel qui en encapsule plusieurs.
  Un assureur peut avoir 50 templates : il nous faut les 50. Cycler sur 50 signatures est plus simple que
  maintenir un schéma unique qui ne reflète pas la réalité, et le self-healing les fait arriver
  **organiquement** au lieu d'exiger un catalogue exhaustif au seed. **Clôt O11.** Wealins = 4 profils.
  Fait apparaître **O15** : l'unicité `(emetteur_code, gabarit, periodicite)` du DDL suppose désormais que
  `gabarit` nomme le *template* et non sa *fonction*.
- **O7 orienté** : la donnée du bloc Contexte vit **dans le store** (précédent INTERAGYR). La forme du
  logement reste à discuter — c'est elle, et non le principe, qui conditionne A3.

**A1 — l'inventaire avant le code**

Le joint de L2 est plus étroit qu'attendu : **tout** ce que le moteur lit du classeur passe par
`read_sheet(wb, prefix, suffix)`, qui rend des listes positionnelles en ordre canonique. Le moteur n'a
donc pas à changer — la substitution se fait en un point.

Mais la mise en regard du store et des 22 + 16 + 9 + 5 + 7 colonnes canoniques donne le résultat que D20
prévoyait : **le forme-store, en l'état, ne permet pas de reproduire le rendu.** Neuf manques bloquants,
cinq ambiguïtés, consignés dans `docs/spec_lecteur_forme_store_2026-07-28.md` et inscrits au registre.

Le plus lourd est **M1** : le store n'a ni assureur ni intermédiaire, seulement un `label` en texte libre.
Ce n'est pas une colonne d'affichage — c'est la **clé de jointure** des lignes et des mouvements vers leur
contrat. Le plus révélateur est **M6** : liquidités, immobilier et dettes reposent sur `genericEntry`, qui
ne déclare **aucune colonne de valeur**. Ces trois catégories fonctionnent parce que
`additionalProperties: true` laisse tout passer — elles ne sont pas modélisées, elles sont tolérées. Deux
d'entre elles entrent dans les contrôles comptables.

Lecture d'ensemble : le pivot a modélisé les **positions** et sous-modélisé la **provenance**. Tous les
manques sont de même nature — les informations d'origine documentaire que le CGP recopie d'un relevé
(assureur, intermédiaire, TRI communiqué, appels et distributions, adossement d'une dette).

**Le critère L3 doit être scindé**, et c'est une correction du plan, pas un détail. Fabriquer les
forme-stores *à partir des* classeurs de fixtures rend l'équivalence partiellement **tautologique** : ce
que l'Excel perd, le store le perd aussi. D'où deux contrôles à nommer séparément — **L3a**, fidélité du
lecteur, prouvable ici sur les 7 fixtures et qui réalise aussi L4 ; **L3b**, perte réelle de la projection
Excel, qui exige un store construit depuis une vérité plus riche, donc les données réconciliées de
Gronier. **Elles ne sont pas dans le fork** : L1 n'est pas exécutable en l'état, faute de données, alors
que O5 le croyait débloqué.

**Rien n'a été codé.** Écrire le lecteur avant cet inventaire aurait été inventer neuf extensions de
schéma au fil du clavier — l'inverse de D20 et de L5. Prochaine étape : trancher A1–A5, puis écrire le
lecteur en le faisant **échouer bruyamment** sur chaque manque plutôt que combler par un défaut. Un manque
silencieusement comblé est un manque qu'on ne corrigera jamais.

**Le run Gronier réel retrouvé — et il corrige l'analyse**

Sur indication de Thomas, la session « Reporting skill (Gronier) » a été criblée. Elle contient
`run_gronier_T2/` avec un **forme-store réel** (`client.store.json`), son manifeste, son classeur de
transition, son HTML et `cp_valos.json`. L1/L3b cessent d'être bloqués par l'absence de données. Détail
complet au §7 de `docs/spec_lecteur_forme_store_2026-07-28.md`. Les points qui changent quelque chose :

- **Le store réel valide le schéma sans une erreur — et ce fait ne prouve rien.** Il passe parce que
  **six des dix tableaux sont absents** (et facultatifs) et parce que `additionalProperties: true` ne
  contraint rien. *Zéro erreur n'est pas zéro perte* : c'est l'argument de D20 sous sa forme la plus nue.
- **Le run est rejouable**, et il bute sur `blocs_enabled.historique` — soit T1/D31 exactement, déjà au
  registre. La clé retirée, la chaîne repasse : **QC 9/9, actif brut 4 608 966 €**, diff de 9 lignes avec
  le HTML livré. Cela **déplace A2** : le renommage n'est plus de l'hygiène, c'est le prérequis
  d'exécution de la référence L3.
- **Le store réel est périmé par rapport au classeur** : 6 471,21 € d'écart sur le coté, 400 876 € sur le
  capital investi de FC051727. `rapport_apply.md` l'explique — le store est resté sur « Catégories & Perf »
  du 23/07, le classeur a été recalé le 24/07 sur les relevés officiels. **Piège pour L3** : sur ce couple,
  on mesurerait la dérive de deux artefacts désynchronisés, pas la fidélité du lecteur. Le §5 avait vu le
  risque de tautologie ; voici son symétrique. L3b exige un store et un classeur issus du **même** recalage.
- **A1 tranché** : `Type poche` (index 3) et `Profil` (index 7) sont bien **deux colonnes distinctes**,
  mais du seul **Excel de transition** (gabarit canonique) — l'Excel de structure n'a que `Profil` et un
  compteur `Nb poches attendu`. Décision : `pocket.type` → 3, `pocket.profile` → 7, sans détourner
  `profile`. *Désagréable au passage : le classeur réellement produit pour Gronier ne porte ni `Type
  poche`, ni `Intermédiaire`, ni `Géographie`, ni `SRI` — variante réduite absorbée silencieusement par la
  projection d'en-têtes de `colmap`, et le rendu s'affiche amputé sans que rien ne le signale.*
- **A2 revu à la baisse** : le store réel emploie `AV`/`Capi`/`CTO` et `Dette privée`/`Private Equity`,
  déjà compatibles avec le moteur. La fixture de `test_store_builder.py` était l'exception. Normalisation
  requise seulement pour `lines[].class` et `lines[].geography`, en snake_case.
- **A4 confirmé par la donnée** : `amount` est toujours positif dans le store réel. Convention figée à
  `amount ≥ 0`, le sens venant de `type`. C'est la fixture au retrait négatif qui est fautive.
- **A5** : le modèle voulu par Thomas est **celui du classeur**, et le store en est loin — `pockets` est
  absent 5 fois sur 7, et une poche n'y porte que 3 champs quand la ligne-poche du classeur porte tout le
  jeu contrat (capital investi, valeur 01/01, versements, frais, dépositaire, date, nantissement).
- **Deux manques que l'analyse de schéma n'avait pas vus.** **M10** : `invest_date` du non coté n'est pas
  déclaré, et le store réel a rangé la date **dans le texte de `validation_note`** — une date métier
  réfugiée dans un commentaire. **M11** : `moic_realise` est déclaré et **jamais rempli** alors que le
  classeur porte les valeurs — défaut du constructeur, pas du schéma.
- **M4 et M7 sont des pertes prouvées, plus des hypothèses.** Le TRI (10 % et 7 %) est au classeur et
  nulle part au store. Et `cp_valos.json` porte 9 séries × 5 dates au **grain exact** de `valuations[]`,
  **hors** du forme-store : la donnée existe, le logement existe, ils ne se sont pas rencontrés.
- **Une erreur de ma spec rectifiée** : `Fin coté` index 2 « Intermédiaire » *a* un consommateur —
  troisième terme de la clé de regroupement de `rows_financier_cote`. La moitié « intermédiaire » de M1
  est donc plus sévère qu'écrit : deux contrats du même assureur via des intermédiaires différents
  seraient **fusionnés**.

### Implémentation — invariant A5, migration, et la référence entre dans le fork

**A2/T1 n'était pas à faire : il était fait.** En cherchant à renommer `blocs_enabled.historique` →
`rendement_annuel`, constat que la session 1 a fait mieux — le bloc a été renommé **puis retiré**, son
tableau synthétique relocalisé sous le tableau Historique, `BLOCK_ORDER` passé de neuf à huit. Le
manifeste Gronier ne porte donc pas une clé *mal nommée* mais une clé **obsolète, sans destination**.
Ce n'était pas un renommage qu'il fallait, c'était une migration. Une heure économisée par cinq minutes
de lecture du journal.

**Schéma amendé (A5)** — `skill/pipeline/store_client.schema.json` :

- `pocket` gagne `type` (FID/FAS/FE/mono, colonne 3), `custodian`, `value_jan1`, `invest_date`,
  `pledged` ; `profile` reste la colonne 7. La distinction `type` / `profile` est celle tranchée au §7.4 —
  les confondre décalait deux colonnes sans rien casser visiblement.
- `attributes.pockets` devient **requis et non vide** sur `financierCoteEntry` (`minItems: 1`), et
  `attributes` devient requis. C'est la règle de Thomas : toujours au moins une poche, celle d'indice 0
  décrivant le contrat quand il n'y en a pas. Elle supprime le **second chemin de code** du lecteur et
  rend le compte de poches exact par construction.

Ce choix **invalide volontairement** le store réel tel qu'il existait — 5 contrats sur 7 n'avaient pas de
poche. C'est assumé : un invariant qui épargne les données existantes n'est pas un invariant.

**`migrer_reference.py`** (racine du fork, hors `skill/`) applique les deux migrations, idempotent, `.bak`
conservés. Sur le store Gronier : 5 poches uniques matérialisées, `custodian` et `invest_date` propagés
sur les 2 contrats multi-poches, **validation 0 erreur** après migration.

Ce qu'elle refuse de faire, et le dit à chaque passage : combler `capital_invested` et `value_jan1` sur
les poches de `tmp_fc_006`/`tmp_fc_007`. Ces valeurs sont propres à chaque poche ; les répartir au prorata
serait fabriquer une donnée. La perf YTD par poche reste donc non calculable pour ces deux contrats — le
manque doit rester **visible**, c'est tout l'objet de L5.

**Un défaut d'idempotence attrapé en le testant.** La seconde passe annonçait « 2 changements » alors
qu'elle n'avait plus rien à faire : les remarques (« manques non comblés ») étaient comptées comme des
modifications, donc le fichier aurait été réécrit indéfiniment. Séparation `changements` / `remarques` —
seuls les premiers justifient une écriture. Vérifié dans les deux sens : seconde passe muette, et rejeu
depuis le `.bak` qui refait bien les 7 changements.

**La référence est dans le fork** : `reference/gronier_T2/` — store migré, manifeste migré, classeur,
HTML livré, contexte, `cp_valos.json`, rapport de réconciliation, avec les `.bak`. Rejoue en **QC 9/9**,
actif brut **4 608 966 €**. `reference/README.md` documente le rejeu et les pièges.

**Un snapshot de client réel dormait dans le paquet livré**

`p2_fill` écrit son snapshot dans `./snapshots/` relatif au **répertoire courant**. Rendre depuis `skill/`
ajoute donc un fichier au paquet. En rejouant la référence je l'ai constaté sur moi-même — paquet passé à
117 fichiers, selfcheck en échec au contrôle suivant.

Mais en réconciliant le compte (115 au lieu des 116 attendus), découverte moins anodine :
**`snapshots/tmp_ent_001_T2 2026.json` figurait déjà dans `BASELINE_MD5.txt`.** Ce n'était donc pas mon
résidu : la session 1 avait déjà rendu Gronier depuis `skill/`, et le snapshot a été **figé dans
l'empreinte d'ouverture du fork** — puis compté comme légitime par tous les contrôles d'intégrité
suivants. Un fichier de résidu qui devient une référence parce qu'il était là au moment de la photo.

**Retiré, délibérément.** `snapshots/` porte des snapshots de clients de démonstration (`anne_d`,
`pp_*`, `carla_m`…) : c'est un jeu de données d'exemple, il a sa place dans le paquet. Un snapshot en
`tmp_ent_001` est autre chose — un id **provisoire** issu d'un run sur un **client réel**. Le livrer,
c'est expédier un fragment de données Gronier dans l'installation de chaque CGP. Ce n'est pas du désordre,
c'est une fuite. Paquet à **115 fichiers**, checksums régénérés, selfcheck OK.

La baseline n'est **pas** régénérée : elle doit rester la photo de l'ouverture (M6). Le retrait apparaît
donc en `SUPPRIMÉS` dans `verifier_empreinte.sh`, ce qui est exactement ce qu'on veut lire.

Deux notes au passage :

- `verifier_empreinte.sh` **tronque les noms de fichiers contenant une espace** (`tmp_ent_001_T2` au lieu
  de `tmp_ent_001_T2 2026.json`). Cinq fichiers du paquet en contiennent. Cosmétique, mais c'est ce qui
  m'a fait chercher le mauvais fichier pendant un moment.
- **Fausse alerte que je me suis faite à moi-même** : trois snapshots portaient une date de modification
  du jour, j'y ai vu une dérive du paquet à chaque régression. Leurs md5 sont **identiques à la
  baseline** — `p2_fill` les réécrit avec un contenu inchangé. Le paquet ne dérive pas ; seul un
  **nouvel** identifiant client crée un fichier. Vérifié avant de l'écrire, et heureusement.

**Trois tests ajoutés à `test_store_builder.py`**, qui passe de 5 à 8 contrôles :

- un contrat **sans** `pockets` est refusé ;
- une liste de poches **vide** est refusée (`minItems: 1`) ;
- les cinq nouveaux champs de `pocket` sont **acceptés** — `pocket` étant `additionalProperties: false`,
  un oubli d'amendement se verrait ici.

Sans ces tests l'invariant A5 ne serait qu'un commentaire : rien n'empêcherait un futur constructeur de
réintroduire des contrats sans poche, et le lecteur retomberait silencieusement sur deux chemins.

**Régression après modification de `skill/`** : checksums régénérés (116 fichiers), selfcheck OK,
`test_store_builder` **8/8**, régression **7/7** avec QC vert et déterminisme sur les sept.

---

## À faire ensuite

Ordre issu de `docs/roadmap_2026-07-27.md` :

- **A2 (suite)** — T1 : renommer `blocs_enabled.historique` → `rendement_annuel` (D31), avec la
  régression comme filet. T2 : corriger `manifest.schema.json`, qui annonce 7 blocs « en ordre
  canonique figé » alors que `BLOCK_ORDER` en compte 9.
- **A4** — produire le seed des référentiels dans `seed/` (7 profils de gabarit, acteurs Gronier,
  successions datées, promotion de l'ISIN v0).
- **O11** — trancher les documents composites (Wealins = 4 sous-templates) : conditionne la forme des
  profils qu'on va seeder, donc à faire **avant** A4.
- **A1** — le lecteur de forme-store, bloqué par **O5/C4** (ids provisoires Gronier), seul point
  bloquant du plan.
