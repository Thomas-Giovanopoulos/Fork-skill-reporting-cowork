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

## 2026-07-29 — Assainissement avant la session d'avancement

Rien de `skill/` n'a été modifié : l'empreinte est inchangée, aucune régénération de checksums nécessaire.

**Quatre décisions actées** (roadmap §« Décisions du jour ») :

- **D39 / O7 clos** — le contexte de marché vit dans une **table séparée, par période**, partagée par tous
  les clients. C'est un fait de marché, pas un fait client : le loger par client dupliquerait le même
  texte autant de fois qu'il y a de clients. Les `contexte/*.json` deviennent le snapshot de secours.
  **A3 est débloqué.**
- **D40 / O12 clos** — le comblement de la perf par ligne via O2S est acté, mais la librairie est hors
  service : il passe par un **export O2S (PDF ou Excel)**. Conséquence qui simplifie plutôt qu'elle
  complique — un export O2S est **une source documentaire comme une autre**, avec son `source_document`,
  sa `provenance` et son profil de gabarit. Aucun cas particulier dans le moteur ; le retour de l'API ne
  changera que la provenance.
- **D41 / O9 clos** — cible : traiter **tous les points du CDC**. J'avais objecté qu'une cible n'est pas
  un critère (elle ne peut pas se déclencher avant la fin), Thomas m'a rejoint : s'y ajoutent **deux fils
  de détente** provoquant un retour anticipé — *(a)* Code touche `store_client.schema.json` ou
  `validation_app`, ce qui rendrait la divergence bilatérale donc irréconciliable par le registre seul ;
  *(b)* les dettes « décidées non posées » croissent sans qu'aucune ne soit posée, mode de défaillance
  HANAMI exact. Repère : 7 posées, 11 en attente.
- **O15 tranché sur le fond** — `gabarit` porte l'identité du **template**. Le cas qui mord n'est pas deux
  formats contemporains (rare, et c'est un défaut d'organisation de l'émetteur, comme le dit Thomas) mais
  le **changement de template dans le temps** : avec la clé actuelle le nouveau format écrase l'ancien et
  rend les relevés archivés inparsables — or le run Gronier lit des relevés jusqu'à **2022**. Restent à
  écrire la convention de nommage et une fenêtre de validité.

**O11 résolu, et la contradiction était de mon fait.** J'avais inscrit D38 sans vérifier le seed livré,
créant deux décisions opposées. Vérification faite dans l'étude de signature §B.6 : **Wealins n'est pas
quatre documents mais un seul PDF composite** (courrier + information réglementaire + page Loi Pacte +
annexe booklet). Or le matcher apparie un *document*. D38 vaut pleinement pour « 50 relevés distincts →
50 profils » ; les **sections d'un composite ne sont pas des templates**, elles n'ont pas de signature au
niveau document. Forme retenue : un profil par document identifiable, **sous-templates déclarés comme
enfants de plein droit** (chacun ses `extraction_hints`, son invariant) au lieu du `segments.liste`
informel — ce qui répond au refus de Thomas de réduire le store de schémas à « un bout d'infra inutile ».
R7 amendé en conséquence, la décision d'origine tient, seule sa forme change.

**Recochage du CDC** : de 3 cases sur 82 à **20**, chacune avec sa preuve datée ; 7 tâches à moitié
annotées sans être cochées (C4, E3, E5, E6, I1, J5, K7) ; encadré en tête disant que le CDC a cessé
d'être l'instrument de suivi. Cinq des 20 sont cochées **avec réserve inscrite** — dont **H1, acquise
avant le fork** (`SKILL.md` inchangé depuis la baseline) et **I2, qui ne repose que sur une preuve
négative**.

**Registre assaini** : les 6 lignes périmées de « À inscrire dès qu'on y touche » déplacées dans « Déjà
posées — inscrites à tort comme à venir », avec leur position réelle. Quatre étaient **héritées de
HANAMI** : le registre avait donc inscrit comme « à poser » des clés déjà là. Reste **11 lignes à venir**,
ce qui recolle exactement au repère de D41. `C7` vérifié toujours absent. Les champs « Position » de
**R1 et R6** reformulés en position *visée* — ils décrivaient au présent des chemins qui n'existent pas,
et pour R1 la clé serait même **refusée** (`additionalProperties: false` à la racine).

**Spec de tri** marquée partiellement périmée : elle décrit le bloc `rendement_annuel`, supprimé depuis.

### N3 — la dette est plus subtile que « une duplication », et elle rétrécit

Diagnostic revu. `SKILL.md` §2.b et `seed/gabarits.json` ne portent pas deux copies du même texte mais
**deux corpus partiellement disjoints** : le seed couvre 7 émetteurs en détail, `SKILL.md` en couvre 3 plus
sommairement. Rien ne garantissait qu'une correction de l'un parvienne à l'autre.

Mais trois pièges de `SKILL.md` sont absents du seed **à juste titre** : ils ne portent pas sur un relevé
d'émetteur mais sur les **entrées propres au skill** — charger le classeur du CGP en `data_only`, ignorer
les lignes de légende, absorber l'écart de ±1 € sur les liquidités. Un piège de gabarit décrit un document
reçu d'un tiers ; ceux-là décrivent la mécanique interne du pipeline. **N3 ne s'applique pas à eux.** La
section n'est donc pas à supprimer, elle est à **scinder**.

**Et je ne l'ai pas scindée aujourd'hui, délibérément.** Deux raisons, la seconde plus sérieuse : le skill
ne peut pas encore lire les profils (`seed/` vit hors du paquet, le client de lecture n'existe pas), et
surtout **la régression ne couvre pas ce chemin** — les 7 fixtures exercent le *rendu*, les pièges pilotent
l'*extraction* faite par les subagents. Modifier cette section changerait le comportement d'agents que
rien dans le filet n'observe. Quand la consigne constante est « ne pas faire régresser le skill », c'est
exactement le changement qu'on ne fait pas à l'aveugle.

Livré à la place : `verifier_pieges.py`, qui rend la divergence **détectable** sans rien changer au
comportement. Il ne compare pas des textes — ils sont rédigés différemment à dessein — mais la présence
des marqueurs discriminants de chaque piège d'émetteur. **4/4 au vert.** La duplication subsiste ; elle
se soldera d'un geste mécanique le jour où le bundle est lisible.

### Extension du corpus — 34 documents, quatre ans, quatre émetteurs

Thomas a ouvert deux dossiers de relevés. Correction d'un chiffre au passage : l'étude d'origine porte sur
**11 relevés**, pas « une trentaine » — les 31 étaient le volume *traité* par le run Gronier, pas le corpus
*disséqué*. Le nouveau corpus en apporte 34, et surtout il ouvre l'axe que l'étude ne pouvait pas voir : le
**temps**. Quatre séries confiées à quatre agents, une par émetteur — regroupement délibéré, la dérive ne se
lit pas document par document mais en série chronologique. Synthèse dans
`docs/etude_corpus_2026-07-29/SYNTHESE.md`, détail dans quatre fichiers frères.

**Un piège de collecte évité de justesse.** `pdfinfo` sur les 34 documents montre que **la moitié sont des
rééditions du 24/07/2026** — arrêté d'époque, générateur d'aujourd'hui. Les six PDF Spirica ont été produits
en quatre minutes le même jour : toute dérive de générateur y est **structurellement invisible**. Le premier
agent l'a signalé de lui-même, ce qui a permis de cibler les trois suivants sur les seuls originaux. Sans ce
contrôle, « aucune dérive chez Spirica » aurait été rapporté comme un résultat alors que c'est un artefact.

**Le résultat principal : la dérive existe, et son amplitude va du tout au rien.**

| Émetteur | Écart | Amplitude | Ancres survivantes |
|---|---|---|---|
| **Cardif** | 12 mois | **rupture** — polices, casse, colonnes, `euros`→`€`, section ajoutée | **1 / 11** |
| **Wealins** | 12 mois | mineure — un titre enrichi, une phrase retirée | quasi toutes |
| **Himalia** | 13 mois | **nulle** — `bbox` des en-têtes identiques au **centième de point** | **30 / 30** |

D'où la conclusion qui interdit toute règle globale : le profil B.7 **n'apparierait pas** le Cardif de 2024,
donc il faut pouvoir versionner ; mais versionner systématiquement fragmenterait Himalia pour rien. **Le
versionnement est une capacité du schéma, jamais une règle de conception** — ce qui le déclenche est la
détection de drift au runtime, c'est-à-dire le self-healing (A5/N5). O15 ne se règle donc pas dans le DDL
seul, mais dans le DDL *plus* la boucle d'apprentissage.

**Trois croyances de l'étude d'origine sont réfutées.**

1. **L'ID de template natif ne versionne pas.** `TYPE_MODELE=66` chez Cardif vaut **avant et après** la
   refonte. Présenté en A.4-1 comme une « signature parfaite », c'est un identifiant de **famille de
   document** — bon pré-filtre, raccourci trompeur, incapable de court-circuiter les couches 2 et 3.
2. **La périodicité n'est pas lisible dans le document**, et cela **touche la clé d'unicité**. Trois faux
   amis sur quatre émetteurs : « trimestriels » chez Spirica est une offre commerciale, « pour l'année »
   chez Cardif une fenêtre YTD, « 8 années » chez Himalia la durée du contrat. Seul Wealins porte un token
   fiable. Or `gabarits` est unique sur `(emetteur_code, gabarit, periodicite)` : une clé d'appariement ne
   peut pas reposer sur une valeur indéterminable à la lecture. **Nouveau point ouvert O16**, bloquant pour
   le chargement du seed.
3. **Les polices discriminent les émetteurs, pas les gabarits.** Chez Cardif elles séparent parfaitement
   deux gabarits que `Producer` et `Creator` ne séparent pas — d'où l'idée d'une « couche 1bis ». Mais chez
   Himalia elles sont identiques sur les cinq documents. Le résultat ne se généralise pas. Au niveau
   émetteur, en revanche, elles sont utiles — et la collision « JasperReports apparaît aussi chez Spirica »
   signalée en B.5 **tombe** : collision de *mot*, pas de *chaîne*.

**Le correctif de schéma le plus rentable, confirmé indépendamment sur trois émetteurs** : distinguer
`sections_requises` de `sections_optionnelles`. `PRM` et `DÉTAIL DES OPÉRATIONS` chez Spirica, `Fonds Euro`
chez Himalia (absent 3 fois sur 5), `Arbitrages` et `Aperçu des fonds` chez Wealins — toutes **pilotées par
la donnée**, elles apparaissent quand le portefeuille les justifie. Avec la liste `sections_ordonnees` à
plat, un gabarit à géométrie variable se fait passer pour plusieurs gabarits, et on versionne pour rien.
C'est exactement le bruit qu'il faut éviter.

**Wealins : deux gabarits, pas quatre — et j'avais tort.** Sept documents, trois intitulés commerciaux,
deux gabarits réels (information annuelle / situation trimestrielle). **Le nom de fichier se trompe deux
fois sur quatre**, confirmation éclatante de A.1-3. Surtout : `Information annuelle FC055211_31 12 24.pdf`
n'est **pas** le sous-template n°2 circulant seul, c'est le composite complet à 4 blocs — **7 documents sur
7 sont composites**. Les sous-templates ne circulent **jamais** en autonomie. Ma « résolution » du 28/07
(« sous-templates déclarés comme enfants de plein droit ») est donc **infirmée par la donnée**, et R7 dans
sa rédaction d'origine avait raison : un profil composite unique à segmentation interne. Les segments sont
des segments, pas des documents. R7 amendé en conséquence, l'amendement fautif conservé pour la trace.

**Et D38 ?** Sa prémisse — « un assureur peut avoir 50 templates » — **n'est pas observée** : le maximum
constaté est de deux par émetteur. Mais la décision reste juste pour une autre raison que celle invoquée :
ce qui fait grossir le catalogue n'est pas la largeur de l'offre, c'est le **temps**. La conclusion pratique
ne change pas, le mécanisme si — et donc ce qu'on surveille : non pas « a-t-on tous les templates de cet
assureur ? » mais « ce template a-t-il bougé depuis le dernier run ? ».

**Reste à établir** : Nortia (cinq documents, **aucune métadonnée PDF**, donc couche 1 vide — et la
distinction original/réédition n'y est pas vérifiable), Spirica sur archives réelles, et
`Positions Overview (1).xlsx` à rapprocher de D40.

---

## 2026-07-29 (2) — Voie B en service : la chaîne client → MCP → Postgres est prouvée

Le serveur des référentiels **répond et sert la base**. `ref_bundle` renvoie le bundle vide attendu,
les quatre outils sont exposés, l'auth fonctionne de bout en bout. C'est le franchissement du RUNBOOK
§2.6, et il débloque **B4 / A4** : le chargement du seed est désormais purement de l'exécution.

### Ce qui n'était pas fait alors qu'on le croyait fait

`REPRISE.md` et l'encadré du RUNBOOK §2 annonçaient les étapes 2.1 à 2.3 « faites sur sa machine ».
Contrôle : la base `rhetores_ref` existait, mais **le schéma `ref` était absent et aucun rôle créé**.
Seul le §2.1 avait tourné. Le DDL a été joué ce jour-là, avec `ON_ERROR_STOP=1`.

L'enseignement mérite d'être noté parce qu'il se répétera : **un état déclaré n'est pas un état
vérifié**, et le contrôle du §2.2 coûte deux secondes. Les tableaux d'avancement de ce fork — celui-ci
compris — doivent être lus comme des intentions jusqu'à preuve.

La séparation D34 a été **démontrée** plutôt que supposée : cinq contrôles, dont deux qui doivent
échouer (`ref_mcp` sans `SET ROLE` → `permission denied for schema ref` ; `ref_app` → `INSERT INTO
acteurs` refusé). C'est consigné en R3 et rejouable au §2.3. Tant que ces deux-là échouent, la garantie
« proposer ≠ canoniser » est portée par la base et non par une convention.

### Bascule d'outillage : `pip` → `uv` (écart R8)

Décision de Thomas : **un seul protocole pour les deux serveurs MCP**. `pyproject.toml` + `uv.lock`
remplacent `requirements.txt` (conservé, marqué remplacé). Bénéfice immédiat : `uv` gérant le `.venv`,
les pièges Windows d'activation cessent de s'appliquer au lieu d'être documentés.

Le motif décisif n'était pas le confort. `requirements.txt` *affirmait* aligner ses versions sur
`mcp-o2s-server` avec des `>=` qui ne garantissaient rien — et le premier `uv lock` a résolu **`mcp`
2.0.0**, version qui a **supprimé `mcp.server.fastmcp`** : `server.py` ne s'importait plus. La
divergence que le fichier disait vouloir éviter était donc déjà là, invisible faute de lock. Corrigé
par `mcp[cli]>=1.27.2,<2`.

**Conséquence pour l'infra, pas pour le fork** : `mcp-o2s-server` porte la même dépendance non bornée
(`mcp[cli]>=1.0`). Seul son lock le protège aujourd'hui ; son prochain `uv lock --upgrade` produira la
même panne. Y poser `<2` avant que ça arrive.

### Trois défauts de configuration trouvés en montant la chaîne

Aucun n'est spécifique au fork : les trois valent pour tout consommateur de `rhetores_authz`.

1. **`JWT_AUDIENCE=` / `JWT_ISSUER=` vides interdisent toute authentification.**
   `token.py` fait `os.environ.get("JWT_ISSUER", "rhetores-finance")`, or `.get` ne rend son défaut que
   si la clé est **absente**. Les `.env.example` des deux serveurs livrent ces lignes présentes et
   vides : l'audience et l'issuer attendus valent `""`, et **aucun token réaliste ne valide**. Symptôme
   trompeur au possible — `401 Invalid issuer` avec un secret parfaitement bon. Contourné en commentant
   les lignes ; le correctif de fond est `os.environ.get(...) or "défaut"` dans le paquet partagé, à
   arbitrer puisqu'il touche trois consommateurs.
2. **L'endpoint MCP est `/mcp`, pas `/`.** Le mount est bien à la racine, mais
   `streamable_http_app()` place sa route sur `streamable_http_path` (défaut `/mcp`). Ce qui masque
   l'erreur : le middleware s'exécutant **avant** le routage, un POST non authentifié sur `/` renvoie
   401 et non 404 — on croit le chemin bon. Le RUNBOOK §2.5 et le README du serveur disaient tous deux
   « à la racine » ; corrigé.
3. **`users.json` ne vit que dans `mcp-o2s-server/`**, et son champ d'identité est `azure_oid`. Sans
   `USERS_FILE` pointé dessus, tout appel authentifié répond `403 Utilisateur non référencé` avec un
   token valide. Le pointer sur le registre d'O2S est la bonne réponse, pas un pis-aller : c'est
   l'intention « un seul registre pour les deux serveurs », donc une seule vérité sur qui est admin.

### État

Base `rhetores_ref` peuplée du schéma seul, serveur sur 8001, `/health` à
`referentiels_configures: true`, contrôles négatifs 401 / 403 passés, `ref_bundle` → bundle vide.
Reste le §2.5 (branchement Cowork, action d'interface, et `127.0.0.1` n'est pas joignable depuis
claude.ai) puis le §2.7, chargement du seed.

---

## 2026-07-29 (2) — Filet A : l'appariement est enfin vérifiable

`skill/` **inchangé** (115 fichiers, selfcheck OK) : tout est développé dans `outils_appariement/`, à
promouvoir dans `skill/pipeline/` une fois la forme stabilisée. Détail dans son `README.md`.

**Une distinction qui débloque le problème.** « Tester l'extraction » recouvre deux choses de nature
opposée : l'**appariement** d'un document à son profil est du code déterministe sur du texte, donc
testable à l'égalité exacte ; la **qualité de l'extraction** des valeurs est faite par un subagent et ne
se vérifie que par invariants. Les confondre condamne soit à des tests fragiles — comparer du texte
produit par un LLM —, soit à n'en écrire aucun. C'est vraisemblablement pourquoi il n'y en avait pas.
Le filet A est construit ; le filet B suivra, et n'assertera jamais d'égalité de chaînes.

**Trois décisions actées avant de coder** : D42 (clé `(emetteur_code, gabarit, valide_depuis)`,
périodicité informative hors matching — clôt O16 et complète O15), la résolution d'O11 par la donnée, et
le périmètre de session arbitré par Thomas (filet d'abord).

**Livré, dans l'ordre où il fallait le faire.**

*La table de vérité, avant le code qu'elle vérifie* — 37 documents, 9 gabarits attendus, vérifiée dans
les deux sens (aucun document manquant, aucun PDF hors table, aucun gabarit cité sans déclaration ni
déclaré sans être exercé). Son apport le plus utile est le champ `certitude` : **15 `etabli`** sur
originaux contemporains, **17 `presume_reedition`**, **5 `a_etablir`**. Sans lui, la stabilité apparente
des douze Spirica aurait passé pour une preuve alors que ce sont douze rééditions du même jour.

*Le matcher*, écrit d'après ce que le corpus a établi et non d'après ce que l'étude supposait : couche 1
en **pré-filtre d'émetteur** seulement, couches 2 et 3 porteuses, `sections_requises` en barrière et
`sections_optionnelles` non pénalisantes, choix de version par date d'arrêté, pages hors matching.

*Le harnais* — **32/32 appariés** (scores 0,95 à 1,00) **et 5 Nortia signalés**, hors décompte parce que
leur profil n'est pas établi.

*Les contrôles négatifs* — **15 assertions**, et c'est elles qui donnent sa valeur au reste.

> *Chiffres corrigés le 29/07 : j'avais écrit « 37/37 » et « 12/12 ». Flatteur par arrondi — 37 est la
> taille du corpus, pas le nombre d'appariements vérifiés. Relevé par l'audit, et c'est exactement le
> travers que je reproche aux tableaux d'avancement des autres documents.*

**Le contrôle qui compte, et pourquoi la première démonstration ne prouvait pas ce qu'elle semblait
prouver.** Sur le Cardif de 2024, v2 est écarté par sa **fenêtre de validité** : verdict juste, mais
c'est la date qui travaille, pas la signature. Or dans un run réel l'arrêté peut manquer. Rejoué **sans
date**, les deux fenêtres éligibles, les ancres suffisent : 2024 → v1, 2025 → v2, sans ambiguïté. C'est
la différence entre « le test passe » et « le test prouve quelque chose ». Un dernier contrôle vise le
biais symétrique — un document quelconque ne doit **pas** être apparié de force, sans quoi un matcher
répondant toujours « oui » passerait tout le reste.

**Cinq pièges rencontrés, tous inscrits.** `^INFORMATION\s+ANNUELLE\s*:` ne matche rien parce que
`pdftotext -layout` **indente** l'en-tête d'annexe. `Fonds Euro` matche 5/5 en sous-chaîne chez Himalia à
cause d'une note « ( ex fonds euros) » — piège absent de l'étude d'origine ; en regex ancrée, 2/5, donc
optionnelle. L'apostrophe typographique U+2019 casse trois ancres. `Prix moyen d'acquisition (PMA)`
**n'existe pas** dans le texte Nortia, l'en-tête étant coupé sur trois lignes entrelacées. Et trois
fichiers portent un nom **mojibake** : je m'y suis cogné deux fois avant de comprendre qu'aucune
normalisation Unicode ne peut les réconcilier — le mojibake conserve la lettre de base et ajoute deux
caractères, le nom propre fond l'accent dans un seul. Le harnais prend le nom **tel quel**.

**Et ce que ces 37/37 ne prouvent pas**, écrit noir sur blanc dans le README plutôt que laissé à
l'optimisme : rien sur la stabilité temporelle chez Spirica (rééditions) ; Nortia non validé (couche 1
vide, ancres d'un seul document) ; **Cardif v1 et de_pury_pictet reposent chacun sur UN document**, donc
une ancre propre à ce document et non au gabarit ne se verrait pas ; et plusieurs ancres sont classées
optionnelles **par prudence** malgré 100 % d'occurrence, le corpus ne permettant pas de trancher entre
« propre à la version » et « bloc conditionnel ».

**Reste de la session** : le seed corrigé (Wealins scindé en deux profils, ancres conditionnelles,
fenêtres de validité), puis le producteur de propositions. **Le seed n'est toujours pas chargé** — et
c'est maintenant `profils_corpus.json` qui en est le brouillon vérifié.

---

## 2026-07-29 (3) — Le seed passe à la forme vérifiée, et D42 devient une migration

`skill/` **inchangé** (115 fichiers, selfcheck OK). Le seed est **prêt à charger** — c'est le premier
moment où je peux le dire, et voir plus bas pourquoi il faut jouer une migration d'abord.

**D42 ne se joue plus dans le DDL : la base est en service.** Le DDL a été exécuté chez Thomas le 29/07 ;
changer la clé d'unicité demande donc un `ALTER`, pas une réécriture.
`infra/migration_001_d42_fenetre_validite.sql` est rejouable, gardée par des tests d'existence, avec sa
section « défaire ». Le DDL a été aligné en parallèle pour les installations neuves, et l'équivalence des
deux **vérifiée par script** (colonnes, `DEFAULT`, nullabilité de `periodicite`, les deux contraintes,
disparition de l'ancienne) plutôt qu'à la relecture.

**Un défaut trouvé en écrivant la migration, et il aurait été silencieux.** La tentation était de laisser
`valide_depuis` nullable, `NULL` valant « depuis toujours ». C'est faux pour une raison qui ne se voit
qu'à l'exécution : **en SQL, deux NULL sont distincts dans une contrainte d'unicité.** Deux profils
`(cardif, situation_contrat_capi_pm, NULL)` auraient donc été acceptés tous les deux. Et pire, `ref_arbitrer`
écrit par `INSERT … ON CONFLICT (clé) DO UPDATE` : une cible de conflit contenant un NULL ne matche jamais,
donc **chaque adjudication acceptée aurait inséré un doublon** au lieu de mettre à jour, sans un mot, et
`ref_bundle` aurait rendu plusieurs profils pour le même gabarit. D'où `valide_depuis NOT NULL DEFAULT
'0001-01-01'` — préféré à `UNIQUE NULLS NOT DISTINCT` (PostgreSQL 15+) parce qu'une convention de date ne
dépend d'aucune version et se lit dans les données.

**Le MCP suit** : la clé de conflit de `_SPECS["gabarit"]` devient `(emetteur_code, gabarit,
valide_depuis)`, et `periodicite` cesse d'être requise — l'exiger obligerait l'appelant à inventer une
valeur que le document ne porte pas. ⚠️ **Le serveur doit être redémarré** pour que ce changement prenne.

### Mon propre garde-fou m'a menti, et c'était le grain qui était faux

`tests/verifier_diff.py` a **validé le changement de clé D42 sans le signaler**. La raison est instructive :
`ast.unparse` écrase tout le dictionnaire `_SPECS` sur **une seule ligne**, laquelle contient `'role'` —
fragment alors présent dans la liste des écarts admis pour une raison sans aucun rapport (la spec `acteur`
a un champ requis nommé `role`). Le garde-fou a donc approuvé une modification de schéma par **coïncidence
de sous-chaîne**. Un contrôle qui passe à tort est pire qu'aucun contrôle : il donne une confiance fausse.

Première correction, insuffisante : imprimer le motif d'admission de chaque ligne. La coïncidence devenait
visible, mais il fallait alors justifier des lignes comme `else:` — trop générique pour être un marqueur sûr.
Le problème n'était pas la liste, c'était le **grain**.

Version retenue : on ne compare plus des lignes mais des **définitions de premier niveau**. Un écart se lit
« la définition `_identity` a changé », et seules trois définitions sont déclarées modifiables (`_identity`,
`register`, `_SPECS`), chacune avec son motif. Aucune coïncidence de texte n'est possible, les lignes de
structure ne demandent plus de justification, et un écart déclaré qui ne se produit plus est signalé comme
du bruit à retirer — c'est exactement ce qui avait permis au faux négatif d'arriver.

**Vérifié dans les deux sens**, parce qu'un garde-fou ne se croit pas : sur une copie fidèle il rend 0 ; sur
une copie où j'ai glissé un rôle Postgres supplémentaire dans `_tx` — modification non déclarée — il rend 1
et affiche le diff exact.

### Le seed

**9 profils** au lieu de 7, à la forme validée par le corpus : `couche1` séparée en pré-filtre d'émetteur,
`signature` scindée en `sections_requises` / `sections_optionnelles` / `discriminants`, fenêtres de validité.
Wealins est scindé en deux (`releve_annuel_capi_lux` et le nouveau `situation_trimestrielle_capi_lux`), et
Cardif porte ses deux versions.

Rien n'est supprimé en silence : `token_periodicite` est conservé sous `_token_periodicite_refute` **avec sa
réfutation**, et les marqueurs de structure sous `_marqueurs_structure_observes` — le matcher ne les consomme
pas encore, mais l'information est chère à reconstituer.

`construire_bundle.py` refuse désormais un `valide_depuis` absent, un triplet en doublon et une fenêtre
incohérente ; les trois refus ont été éprouvés par injection.

**Le contrôle qui prouve la conversion** : le harnais a gagné une option `--profils`, et les 37 documents
sont rejoués **en lisant le seed** et non le brouillon — **32 appariés + 5 Nortia signalés**, plus les 12
contrôles négatifs. Une conversion ne se croit pas, elle se rejoue.

Trois valeurs de `periodicite` changent (Cardif, Himalia, Nortia passent à `a_la_demande`) : conséquence
directe de D40/D42 — là où aucun token fiable n'existe, on cesse d'affirmer une périodicité.

---

## 2026-07-29 (4) — Seed en base, UPSERT prouvé, et le bundle ne tient plus

`skill/` inchangé. Thomas a joué la migration 001, redémarré le serveur et chargé le seed.

**B4 est atteint au chargement** : `ref_bundle` rend **17 acteurs, 2 successions, 9 gabarits, 261 ISIN**,
avec Cardif en deux versions (`2024-01-01→2025-12-31` et `2025-12-31→null`), Wealins en deux gabarits, et
les sept autres à `0001-01-01`.

**L'UPSERT est prouvé, et il valide le raisonnement de la migration.** Test choisi pour être sans risque :
renvoyer `wealins/situation_trimestrielle_capi_lux` **à l'identique**, clés de documentation incluses — un
envoi tronqué aurait écrasé les ancres vérifiées. Résultat : `version` passe de 1 à **2**, `created_at`
inchangé et `updated_at` neuf (donc la **même ligne**), et les colonnes non envoyées — `extraction_hints`,
`champs_publies`, `periodicite`, `invariant_controle` — intactes : le `DO UPDATE` ne touche que ce qu'on
lui donne.

Le raisonnement se referme : la contrainte `UNIQUE` étant désormais **effective** grâce au `NOT NULL`, un
doublon est impossible par construction. Avec `valide_depuis` nullable, cette même contrainte n'aurait rien
attrapé — deux NULL étant distincts — et l'insertion aurait passé en silence. Le `NOT NULL` est ce qui rend
la contrainte utile, pas un détail de style.

### Une affirmation du design est tombée au premier chargement réel

`ref_bundle` documentait : « les référentiels sont petits et lus en entier : pas de pagination, pas de
requête par ligne ». Vrai sur une base vide. Au premier chargement : **185 ko, 4 936 lignes — au-delà de ce
qu'un résultat d'outil MCP peut porter.** Le bundle n'est pas revenu.

Deux causes mesurées : **1 732 lignes sur 4 936 (35 %) sont des champs de pure traçabilité** que le skill
ne lit jamais, et les **261 ISIN pèsent près de 70 %** du total à eux seuls — alors que l'essentiel des
besoins d'un run ne porte que sur les gabarits.

Corrigé sur les deux fronts : `ref_bundle(sections=[...])`, et `created_at` / `updated_at` / `version` /
`validated_by` retirés du payload (ils restent en base). `provenance` et `confiance` sont **conservés** :
enums courts, et la confiance est une information métier que le skill peut légitimement pondérer (B9). Le
`compte` porte **toujours** sur les quatre tables, même quand une seule est demandée — sans quoi un appel
partiel se lirait comme une base à moitié vide.

### Le garde-fou de diff a menti une seconde fois, et c'était encore le grain

Après le faux négatif de la veille, corrigé en passant au grain de la **définition**, il a laissé passer la
réécriture de `ref_bundle` : celle-ci vit dans `register`, déjà déclarée modifiable pour
`ref_adjudications`. **Une seule autorisation couvrait les quatre outils MCP.**

Troisième version : les fonctions imbriquées sont extraites sous `parent.enfant` et remplacées par un
marqueur dans le corps du parent — 17 définitions comparées au lieu de 10, et `register.ref_bundle` est un
écart distinct de `register.ref_adjudications`, chacun avec son motif. Les définitions **ajoutées** doivent
être déclarées elles aussi, et un écart déclaré qui ne se produit plus est signalé comme du bruit à
retirer : c'est exactement ce qui avait permis au premier faux négatif d'arriver.

Vérifié dans les deux sens, comme les fois précédentes : vert sur copie fidèle, et sur une copie où l'on
glisse une décision `peut_etre` dans `ref_arbitrer`, il désigne **`register.ref_arbitrer`** nommément — là
où la version 2 aurait dit « register » et se serait tue.

Deux mensonges de ce garde-fou en deux jours, tous deux dus au grain et non à la liste. La leçon vaut
au-delà de ce fichier : un contrôle doit être vérifié **par un échec provoqué**, sinon on ne sait pas ce
qu'il regarde.

---

## 2026-07-29 (5) — Audit du CDC, et une purge de la documentation de pilotage

`skill/` inchangé (115 fichiers, selfcheck OK). Aucun code métier écrit : cette entrée ne parle que de
véracité des documents, ce qui est précisément l'objet du fork.

**Ce qui a bougé en deux jours** : la voie B est passée d'« écrite » à **« en service »** — DDL et
migration 001 joués, 4 outils MCP répondant depuis une session, seed chargé (17/2/**9**/261), UPSERT
prouvé. Et le **filet A** existe : c'est le premier filet du fork sur le chemin de l'extraction, donc un
comblement partiel de LIM8. La voie A, elle, n'a **pas** bougé : A1 n'a toujours aucune ligne de code, et
les deux briques `skill/` du test de réussite non plus — `grep -rn 'ref_bundle' skill/` ne rend rien.

**Mes propres chiffres étaient flatteurs.** J'annonçais « 37/37 appariés » et « 12/12 contrôles
négatifs » : le harnais imprime **32/32 appariés · 5 signalés**, et `test_discrimination.py` produit **15**
assertions. 37 est la taille du corpus, pas le nombre d'appariements vérifiés, et les 5 Nortia sont hors
décompte par construction. Corrigé partout, avec la mention du correctif — un compte rendu qui embellit de
cinq unités est un compte rendu qu'on cessera de croire, et je passe mon temps à reprocher ce travers aux
autres documents.

**Deux collisions de numérotation, de mon fait, et c'est l'erreur exacte que T1 documentait pour
`historique`.** J'ai appelé `M1–M11` les manques du forme-store alors que `M1–M7` est le chantier M du CDC,
et `L1–L8` les limites du système alors que `L1–L5` sont les tâches du chantier L. Renommés en **`MQ1–MQ11`**
et **`LIM1–LIM8`** dans tout le dépôt, avec une note de renommage à chaque source.

**La table des points ouverts de la roadmap se contredisait**, parce que je l'avais alimentée en ajoutant
des lignes sans retirer les anciennes : O7 deux fois, O9 deux fois, O12 deux fois, **O15 trois fois**, O16
deux fois — dont une qui affirmait encore « bloque le chargement du seed » alors qu'il est chargé, et une
qui donnait pour « résolution retenue » l'amendement O11 **infirmé le même jour**. Fusionnée à une ligne
par point.

**Le tableau « État vérifié » du RUNBOOK était périmé** — ⛔ sur §2.5 et §2.7, tous deux faits. Le tableau
qui met en garde contre les tableaux d'avancement s'est fait attraper par son propre avertissement, dans
l'autre sens : il annonçait moins que la réalité. Corrigé, et l'ironie notée sur place.

**Autres corrections** : le repère de D41 disait « 7 entrées posées », il y en a **8** (R8 posé le même
jour) ; `REGISTRE_ECARTS` disait que la donnée du bloc Contexte « vit dans le store » alors que **D39 dit
l'inverse** ; le titre de R4 portait encore l'ancienne clé ; R7 situait `segments` dans `extraction_hints`
alors qu'il est au premier niveau du profil et n'y atterrit qu'après `construire_bundle.py` ; le CDC disait
« jusqu'à D41 » ; `REPRISE.md` avait six passages faux, dont « le dépôt n'est pas versionné » et « 3 cases
cochées sur 82 » ; et le plan de session annonçait « 38 documents » pour 37 PDF.

**Un défaut de portabilité corrigé** : `harnais_appariement.py` codait en dur les chemins du corpus sur le
montage de sandbox du jour. Un filet qui ne se rejoue pas ailleurs n'est pas un filet — désormais réglable
par `--corpus` ou variable d'environnement, avec un échec précoce nommant les chemins essayés. Sans cela,
un dossier mal monté aurait produit 37 échecs d'appariement : le diagnostic exactement inverse du vrai.

**Deux constats que je n'ai pas corrigés, et qu'il faut savoir.** Le fil de détente (a) de D41 — « Code
touche `store_client.schema.json` ou `validation_app` » — **n'a pas de capteur** : le dépôt de Code n'est
pas accessible, donc ce fil ne se déclenchera que si quelqu'un va regarder. Et l'« équivalence DDL /
migration vérifiée par script » du 29/07 a été vérifiée par un script **jetable**, non conservé : la
formulation du journal laisse croire qu'on peut la rejouer, on ne peut pas.

Enfin, un point de discipline : `ref_adjudications` montre **un accepté et un rejeté**. Les deux sont
tracés, mais le fil de l'eau (D21) veut qu'un arbitrage laisse une entrée — le rejet du test de mise en
service figure au RUNBOOK §2.6, pas ici. À l'avenir, les deux.

---

## 2026-07-29 (6) — D43/D44 : hébergement tranché, et une fuite de données clients dans le paquet livré

Parti d'une question d'hébergement, arrivé à un incident. Le paquet passe de **115 à 113 fichiers**,
régression **7/7** QC pleins et déterministe, selfcheck OK.

**D43 — MCP et Postgres sur Railway, colocalisés.** Azure Flexible Server reste la cible de production
(RUNBOOK §4), mais on ne l'attend pas. Trois motifs : le MCP y est une **recopie** (`mcp-o2s-server` y est
déjà, avec `railway.toml` et `nixpacks.toml`, et notre serveur a la même forme) ; colocaliser supprime
toute question d'egress ; et surtout **la base est reconstructible** — `seed.sql` la rejoue en une
commande, donc perdre l'instance coûte les adjudications du jour, pas le référentiel. La durabilité pèse
ici beaucoup moins que pour le datahub, ce qui autorise un hébergement léger — et débloque la
démonstration du test de réussite, qui exige une base *joignable*, pas *définitive*.

### D44 — et la question d'hébergement masquait plus grave qu'elle

En cherchant ce qui, dans cette base, justifierait des précautions de conformité, le constat s'est
retourné. **`ref_bundle` rend le store en entier à CHAQUE CGP** — c'est l'objet de D36. Donc tout
identifiant client qui y entre est visible de tous. Ce n'est pas un risque de prestataire d'hébergement :
c'est une **divulgation entre confrères**, et elle était déjà opérante en local.

Les deux successions du seed portaient `contexte = "Wealins FC051727 — poche FAS"`, soit un numéro de
contrat réel. La distinction qui tranche : une succession est un **fait de marché** — « la poche
ex-Intesa a été reprise par CA Indosuez ». Le numéro de contrat n'est pas le fait, c'est **l'endroit où
on l'a observé**, et sa place est le dossier de run du client.

**Ma première purge était trop étroite, et le détail est instructif.** J'ai corrigé les deux `contexte`
et déclaré l'affaire close. Restaient : `acteurs[].payload.source` = « relevés annuels FC051727 et
FC055211 » (même fuite, autre colonne), des notes nommant le client, et surtout — que je n'avais pas vu —
**la colonne `source` des 261 ISIN**, qui partait en base avec des étiquettes `gronier_*` /
`interagyr_*`. La plus grosse fuite en volume, invisible à qui cherche des numéros de contrat.

### Le paquet livré contenait les données de clients tiers

Le balayage systématique des 115 fichiers de `skill/` a donné **16 fichiers**. Ce paquet s'installe chez
**chaque** CGP :

- `references/03-tableau-exhaustif.md` : « Wealins **FR056470** (**Hervé G.**) » et « Wealins
  **FC056913** (**SAS AX**) » — numéros de contrat **avec le porteur nommé** ;
- `snapshots/hanami_T2-26.json` et `snapshots/pp_gronier_T2-26.json` — données de deux clients réels ;
- `06-mappings-fonds.md` : sept **numéros de compte UBS** réels ;
- `07-cas-particuliers.md` : le montant et la date d'une opération réelle ;
- et `Hervé G.` / `SAS AX` dans **dix** fichiers — le client de démonstration des documents de référence.

Deux natures, deux gestes. Le résidu se retire ; l'exemple courant de la documentation se **remplace**,
et de façon rigoureusement cohérente sous peine de rendre les documents incompréhensibles. Retenu :
`Client Exemple` / `SAS Exemple`, placeholders **non ambigus** — tout le problème étant qu'un nom
réaliste était un nom réel.

**Et je dois reconnaître la même erreur trois fois.** Le 29/07 au matin j'ai retiré
`snapshots/tmp_ent_001` en écrivant que c'était « une fuite, pas du désordre » — puis j'ai refermé le
sujet **sans regarder les 41 autres fichiers du même dossier**, où dormaient deux snapshots de clients
réels. Purge partielle sur le seed, purge partielle sur les snapshots, et la même leçon à chaque fois :
un constat de fuite oblige à balayer la **catégorie**, pas l'occurrence.

### Le garde-fou, et où il ne doit PAS être

Décision de conception : le contrôle va dans **`regenerer_checksums.py`**, pas dans `selfcheck.py`. Le
selfcheck tourne à chaque run de chaque CGP ; sceller le paquet, c'est nous. Un audit d'identifiants a sa
place au **scellement** — régénérer, c'est autoriser la diffusion —, pas dans le chemin chaud.

Un piège qui aurait désarmé le contrôle : le motif `[A-Z]{2}[0-9]{5,8}` **matche l'intérieur d'un ISIN**
(`DK0062498333` contient `K0062498`). Sans soustraire les ISIN bien formés, il crie sur 261 lignes
légitimes du CSV — et un garde-fou qui crie au loup finit désactivé. C'est écrit en commentaire, parce que
la prochaine personne aura la tentation de « simplifier » la soustraction.

**Vérifié en le faisant échouer**, comme les précédents : injection de `HANAMI` + `AB123456` dans
`skill/README.md` → refus nominatif avec fichier et ligne, plus un message qui dit **comment**
dé-identifier au lieu de seulement interdire. Injection retirée, retour au vert.

La liste des noms est **incomplète par nature** — elle attrape les clients connus, jamais un nouveau. Le
garde-fou réduit le risque, il ne le supprime pas.

**Reste, et c'est délibéré** : `test_discrimination.py` conserve les vrais noms dans ses **chemins** de
PDF — le corpus assureur garde ses noms d'origine, il est hors du paquet, et les renommer casserait le
contrôle. Seuls ses libellés imprimés sont dé-identifiés. Et `docs/` porte encore une centaine
d'occurrences : ce sont des documents de travail internes, non distribués — à traiter, mais pas au même
titre.

---

## 2026-07-29 (7) — Le branchement commence : le pipeline lit enfin les référentiels

Paquet de 113 à **117 fichiers**, régression **7/7**, `test_store_builder` 8/8, selfcheck OK.

**Le diagnostic qui a réorienté la session.** Reporté sur l'architecture cible du CDC (§1.3), l'état
réel donne une image nette : **la colonne de droite est en service, la colonne du milieu est vide.** Les
référentiels tournent, le matcher est écrit et éprouvé — et *rien ne les appelle*. La « couture » que le
CDC désigne lui-même, le dict forme-store, est précisément ce que rien ne consomme.

C'est aussi la cause du drift ressenti : chaque détour de la journée était réel — la fuite de données,
le garde-fou menteur — mais tous **périphériques**. Deux jours sans toucher la colonne vertébrale,
pendant que les actifs s'accumulaient débranchés. Chemin retenu par Thomas : **brancher l'existant
d'abord**. Règle anti-drift adoptée : tout va dans une liste, sauf une fuite de données clients ou une
régression du skill.

**Une précision demandée par Thomas, et elle mérite d'être écrite.** « On ne peut pas appeler un outil
MCP dans un skill ? » — si, mais il faut distinguer deux acteurs. **L'agent peut** : `ref_bundle` est
dans ses outils, et les instructions du skill peuvent lui demander de l'appeler puis d'écrire le
résultat. **Le pipeline ne peut pas** : son sandbox est lancé en `--unshare-net`. Vérifié sur place —
`gaierror` sur le DNS, port 53 injoignable, 443 aussi.

Et c'est un **avantage**, pas seulement une contrainte : un pipeline qui est une fonction pure de ses
fichiers est **reproductible**. Deux runs du même client rendent le même HTML, et le bundle devient une
pièce du dossier archivé (D4). Si le code appelait le réseau, deux runs pourraient différer sans que
rien ne le signale — et le déterminisme que la régression vérifie à chaque fixture ne voudrait plus
rien dire.

**Livré** — `skill/pipeline/referentiels.py` : résout la source dans l'ordre de fraîcheur décroissante
(chemin explicite → variable d'environnement → dossier de run → répertoire courant → snapshot vendoré),
valide la forme, et expose les accès par code, par **alias** (K1) et par **succession** (K5). Plus
`skill/pipeline/matcher_gabarit.py`, promu depuis `outils_appariement/`.

**Le snapshot vendoré est produit par `construire_bundle.py`**, pas à la main — un snapshot fabriqué
séparément divergerait du bundle au premier changement et personne ne s'en apercevrait. Il **exclut les
ISIN** à dessein : ils vivent déjà dans le paquet sous `assets/isin_referentiel_v0.csv`, qui est
d'ailleurs la *source* de la section `isin` du bundle. Les vendorer deux fois mettrait 261 lignes en
double, avec deux copies à faire diverger.

**Une découverte qui a changé la conception** : *aucun code* ne lit le CSV ISIN. Il n'est cité qu'en
prose — `SKILL.md`, `GEO_RULES.md`. Le référentiel ISIN est donc consommé par **l'agent qui lit des
instructions**, pas par du code. Le lecteur a deux clientèles, et je n'ai touché qu'à la première : la
seconde relève de N3, qui modifie le chemin d'extraction — lequel n'a **aucun filet** (LIM8).

### Le test a trouvé un défaut de la nature exacte que le module doit prévenir

`test_referentiels.py` (17 contrôles) a échoué au premier essai sur la provenance. La cause : je la
déduisais de **la façon dont le chemin était fourni** — tout chemin explicite était étiqueté « run » —
et non de **ce qu'il désigne**. Conséquence : pointer volontairement le snapshot vendoré, cas
parfaitement légitime pour forcer le mode hors ligne, le faisait passer pour un bundle frais et
**supprimait l'avertissement**. C'était le repli silencieux que ce module existe pour empêcher, logé
dans le module lui-même.

Corrigé en comparant le chemin **résolu** au snapshot. La leçon est celle de la journée, une fois de
plus : la provenance est une propriété de la source, jamais de l'intention de l'appelant.

**Étape 0-bis ajoutée à `SKILL.md`** — la moitié agent du branchement, autorisée par Thomas. Elle
demande à l'agent d'appeler `ref_bundle(sections=["gabarits","acteurs","successions"])` et d'écrire la
réponse dans `referentiels.json` à la racine du dossier de run. Trois choix y sont explicités :

- **demander les sections**, jamais tout : le bundle complet dépasse la taille d'un résultat d'outil,
  les ISIN en faisant 70 % ;
- **ne pas bloquer** si le connecteur manque — le repli vendoré existe —, mais **le dire au CGP** en une
  phrase. Tout l'objet de D36 est qu'un gabarit validé soit visible au run suivant d'un autre CGP sans
  réinstallation : un repli silencieux annulerait ce bénéfice sans que personne ne le sache. Le module
  signale la provenance de son côté ; l'agent la relaie ;
- **les ISIN restent hors du bundle**, l'agent continue de lire le CSV comme avant.

**Chaîne vérifiée de bout en bout**, en simulant ce que l'agent écrit : bundle de run déposé dans un
dossier → `charger(dossier_run='.')` rend `provenance: run`, les deux fenêtres Cardif dans l'ordre, et
l'acteur retrouvé par l'alias `WEALINS`. Paquet à **117 fichiers**, régression **7/7**,
`test_referentiels` 17/17, `test_store_builder` 8/8, selfcheck OK.

**Reste du branchement** : le producteur de propositions, qui refermera la boucle de drift.

---

## 2026-07-29 (8) — Vague de test : le moteur est confirmé, le MCP révèle deux pièges de déploiement

**Le moteur est confirmé.** Neuf contrôles, tous verts.

| | Résultat |
|---|---|
| Intégrité du paquet | 117 fichiers, manifeste à jour, selfcheck OK, garde-fou D44 vert |
| Régression | **7/7**, QC pleins, déterministe sur les sept |
| `test_store_builder` | 8/8 |
| `test_referentiels` | 17/17 |
| Filet A — appariement | **32/32 appariés · 5 signalés** sur 37 documents |
| Contrôles négatifs | 15, aucun échec |
| Le seed porte les ancres vérifiées | 11/11 en lisant `seed/gabarits.json` |
| **Référence client réel** | **QC 9/9**, actif brut **4 608 966 €** |
| **Déterminisme sur client réel** | deux rendus, **même md5** |

### Un écart de 73 lignes qui n'était pas une régression

La comparaison au HTML livré donnait d'abord **73 lignes** contre les 9 annoncées la veille. Cause : mon
appel omettait le **4ᵉ argument** de `p2_fill`, le fichier de contexte de marché — sans lui, le bloc
Contexte reste en placeholder et les faits marquants disparaissent. Et **la commande de rejeu que
j'avais moi-même documentée** dans `reference/README.md` omettait ce même argument : le piège était
inscrit dans ma documentation. Corrigé, avec la mention du symptôme.

Avec le contexte : **7 lignes**, toutes expliquées — et **deux sont des améliorations** :

1. Un commentaire CSS portait « Hervé G. ». La purge D44 l'a retiré, et le constat va plus loin que le
   paquet : **le HTML remis au client contenait le nom d'un AUTRE client dans le commentaire de sa
   feuille de style.** Une troisième surface de fuite, que je n'avais pas anticipée.
2. Le commentaire HTML « Widget — Historique du patrimoine » n'est plus émis : c'est le correctif de
   fuite de commentaire de la session 1 devenu visible.
3. Le commentaire de gestion P4, rédigé après génération. Attendu.

### Deux pièges de déploiement, dont un qui a cassé un outil en service

**L'ordre migration / déploiement dépend du SENS du changement.** La migration 002 a été jouée avant le
redémarrage du serveur, et `ref_propose` s'est mis à échouer sur `column "source_document" ... does not
exist` : le code écrivait encore dans une colonne que la base venait de perdre. **Ajouter** une colonne →
migration puis code. **Retirer** une colonne → code puis migration. La 002 fait les deux, elle n'a donc
**aucun ordre sûr en un seul temps** — il faut déployer le code d'abord, ou scinder la migration.
Inscrit au RUNBOOK §0.

**Et le retrait silencieux d'argument a mordu une seconde fois, en pire.** Après redémarrage du serveur,
`ref_propose` accepte la proposition — mais les trois colonnes `source_empreinte` / `source_gabarit` /
`source_arrete` arrivent à **`null`** alors que je les avais passées. Le schéma d'outil en cache côté
client porte encore `source_document` : mes arguments ont été **retirés en route**. Le serveur a le
nouveau contrat, le client l'ancien.

C'est pire qu'une erreur : la file d'adjudication contient désormais une proposition dont la provenance
paraît **vide par choix de l'appelant**. Un arbitre n'aurait aucun moyen de savoir qu'elle a été perdue
en transport. C'est exactement le mode de défaillance que le RUNBOOK §0 annonçait — et le constater deux
fois en une journée en fait une priorité, pas une remarque.

**Correctif à faire** : donner au serveur le moyen de **détecter un vieux client**, plutôt que d'espérer
que les schémas soient à jour. Un argument de version que le nouveau client envoie toujours, et dont
l'absence fait dire au serveur « votre client est en retard » au lieu d'écrire des `null`.

**Une observation de conception au passage** : `ref_propose` accepte une proposition **incomplète** — il
ne valide que la cible, les champs obligatoires étant contrôlés à l'arbitrage par `_upsert_canonique`.
Défendable (un run ne doit pas être empêché de signaler quelque chose de partiel), mais l'erreur remonte
alors à l'admin plutôt qu'au run. À arbitrer.

Les deux propositions de test sont **rejetées et tracées**, avec le résultat du test dans leur
commentaire d'arbitrage — c'est le bon endroit pour cette information.

---

## 2026-07-29 (9) — Le retrait silencieux d'arguments, et pourquoi la solution évidente était mauvaise

`skill/` inchangé. Modification de `infra/mcp_referentiels/` seule — **aucune signature touchée**, donc
un redémarrage du serveur suffit, sans relancer Cowork.

**Le problème, constaté deux fois dans la journée.** Le client MCP met le schéma des outils en cache.
Quand le serveur gagne un paramètre, un client au schéma périmé **retire l'argument de l'appel sans
aucune erreur**. Première occurrence : `sections` ignoré, tout le bundle revenu. Seconde, plus grave :
une proposition enregistrée avec ses trois champs de provenance à `null` alors qu'ils avaient été passés
— une provenance qui **paraissait vide par choix de l'appelant** quand elle avait été perdue en
transport. Aucun moyen, pour un arbitre, de faire la différence.

**Thomas a posé la bonne objection**, et elle a disqualifié ma première idée. Je voulais faire déclarer
sa version au client. Mais alors un appelant parfaitement à jour qui ne remplirait pas ce champ serait
accusé d'être en retard : on échangerait un faux négatif silencieux contre un **faux positif bruyant**.
Et un contrôle qui accuse à tort est un contrôle qu'on apprend à ignorer — c'est exactement ce qui est
arrivé au garde-fou de diff deux fois aujourd'hui.

**Le raisonnement qui sort de l'impasse** : on ne peut pas savoir de façon fiable ce que le client *est*,
mais on sait exactement ce que le serveur *a reçu*. Le signal doit donc être **descriptif, jamais
accusatoire**.

- Le serveur annonce **son** contrat (`contrat_outil`) dans chaque réponse — à l'appelant de comparer.
- Chaque écriture **renvoie ce qu'elle a reçu** : `provenance_recue`, `sections_recues`.
- Quand c'est ambigu — provenance vide, `sections` absent — la réponse énonce **les deux lectures
  possibles** et dit quoi faire, sans en choisir une.

Deux propriétés qui valaient le détour : **aucun faux positif n'est possible**, puisque la réponse
énonce des faits ; et le mécanisme couvre **tout** argument perdu, pas seulement ceux qu'on avait
anticipés — alors qu'un contrôle par champ n'aurait attrapé que les cas prévus.

**Neuf contrôles l'ancrent** dans `test_portage.py`, testables **sans base** : la logique
d'avertissement est du calcul sur les arguments reçus. C'est délibéré — un mécanisme de détection qui
exigerait Postgres pour être éprouvé ne le serait qu'en production, c'est-à-dire jamais. L'un des
contrôles vérifie qu'**aucun libellé n'affirme que le client est périmé** : le libellé compte autant que
le déclenchement.

---

## 2026-07-29 (10) — Le mécanisme fonctionne, et il a immédiatement révélé une troisième purge partielle

**Le correctif du retrait silencieux est vérifié en réel** : `ref_bundle` renvoie
`contrat_outil: "2026-07-29.d44"` et `sections_recues: ["successions"]` — l'écho confirme que
l'argument est arrivé. Le mécanisme fait exactement ce qu'on lui demande : énoncer des faits.

**Et c'est en le lisant que j'ai vu autre chose.** Le `payload.note` d'une succession portait encore
« du run Gronier ». Vérification étendue aux acteurs : la base sert **en ce moment, à chaque CGP**, un
numéro de contrat client dans **cinq** payloads (`banque_thaler`, `ca_indosuez`, `cic`,
`intesa_sanpaolo`, `quintet`), un second chez `wealins`, et quatre noms de clients dans des notes de
provenance (`altaroc`, `dauphine_am`, `de_pury_pictet`, `spirica`).

La cause : la migration 002 ne traitait que `contexte` et `source_document` — les seules fuites connues
à l'heure où je l'ai écrite. Les fuites de `payload` ont été trouvées **après**, et corrigées **dans le
seed seulement**. La base avait été chargée avant. **Source propre, donnée déployée sale.**

**Troisième purge partielle en deux jours, et le motif se répète.** La première a fixé deux `contexte`
en laissant les payloads. La deuxième a retiré un snapshot en laissant les 41 autres fichiers du même
dossier. Celle-ci a corrigé le fichier source en laissant la copie déployée. À chaque fois : je corrige
**ce que j'ai trouvé** et je déclare l'affaire close.

**La règle que j'en tire, et qu'il faut appliquer littéralement.** Un constat de fuite oblige à balayer
les **couches**, pas l'occurrence — et il y en a cinq :

1. le **fichier source** (`seed/*.json`) ;
2. l'**artefact généré** (`referentiels.json`, `seed.sql`, le snapshot vendoré) ;
3. la **donnée déployée** en base — celle que j'ai oubliée aujourd'hui ;
4. le **paquet livré** (`skill/`) — oublié hier ;
5. la **sortie remise au client** (le HTML) — trouvée par accident dans la vague de test, où un
   commentaire CSS portait le nom d'un autre client.

**`infra/migration_003_purge_payloads.sql`** — 19 `UPDATE` idempotents. Deux choix à noter :

- **Générés depuis le seed purgé**, pas écrits à la main. Recopier des JSON de plusieurs lignes est
  précisément le geste qui fait diverger la base de sa source.
- **Des `UPDATE` et non un rechargement de `seed.sql`** : celui-ci est idempotent pour les acteurs, les
  gabarits et les ISIN, mais **pas pour les successions** — leur `INSERT` n'a aucune cible de conflit,
  faute de clé naturelle. Un rechargement complet créerait des successions en double.

La migration porte aussi ses propres requêtes de contrôle, et l'avertissement qu'elle écrase `payload`
en entier — sans conséquence aujourd'hui, la seule adjudication acceptée ayant porté sur `gabarits`.

---

## 2026-07-29 (11) — Migration 003 jouée, provenance vérifiée dans les deux sens

**La base est propre.** Relecture d'un `ref_bundle` réel, section par section : les 17 acteurs ne portent
plus ni numéro de contrat ni nom de client, et les deux successions non plus. Les dé-identifications
**préservent l'information** au lieu de la supprimer — « deux relevés annuels du même émetteur », « un
contrat Wealins observé au corpus », « une note intermédiaire d'un run réel ». Un arbitre garde de quoi
juger la provenance d'une ancre sans savoir de qui elle vient.

Le contrôle qui compte n'était pas le `SELECT` de la migration mais **la relecture du bundle** : c'est ce
que voit un CGP, donc le seul point de vue qui prouve quelque chose.

**La provenance D44 est vérifiée dans les deux sens** — et un mécanisme de détection dont on n'a vu qu'une
moitié ne prouve rien :

| Cas | Résultat |
|---|---|
| Provenance passée | `provenance_recue` renvoie les **trois** valeurs · **aucun** avertissement |
| Provenance absente | les trois à `null` · avertissement émis, énonçant **les deux lectures possibles** sans accuser le client, et disant quoi faire |

Il se déclenche donc quand il doit et **se tait quand il ne doit pas**. C'est cette seconde moitié qui
manquait à ma première idée — celle qui aurait accusé un appelant à jour de n'avoir pas rempli un champ.

**État général** : paquet à 117 fichiers, manifeste à jour, selfcheck OK, `test_portage` au vert,
garde-fou de diff sans écart non déclaré, seed et base alignés à 17 acteurs.

Les quatre propositions de test de la journée sont **rejetées et tracées**, chacune portant son résultat
dans son commentaire d'arbitrage. La file d'adjudication est ainsi devenue le journal de ces
vérifications — c'est le bon endroit : elle survit à la session.

---

## 2026-07-29 (12) — Le producteur de propositions : la boucle est refermée

`skill/pipeline/producteur_propositions.py` écrit, testé, promu. Paquet à **119 fichiers**, régression
**7/7**, `test_store_builder` 8/8, `test_referentiels` 17/17, `test_producteur` au vert, selfcheck OK.
C'est la dernière brique du chemin choisi : le matcher **détecte**, le producteur **rédige**, l'agent
**relaie**, l'admin **arbitre**. La colonne du milieu du schéma n'est plus vide.

**Trois principes de conception, chacun hérité d'une leçon de la semaine.**

- **Le producteur ne fabrique aucune signature.** La frontière variante/nouveau gabarit est un jugement
  (LIM3), un détecteur ne sait pas si un drift est bénin ou cassant (LIM4) : il signale et fournit la
  matière, il ne devine pas. Une proposition est une *demande de travail*, pas un gabarit prêt — et
  `ref_arbitrer` refuse d'ailleurs d'écrire un gabarit sans `signature`. Sur `aucun`, il ne tranche même
  pas nouvel_emetteur/nouveau_gabarit : `nature_a_confirmer`.
- **Aucune donnée client dans la proposition (D44).** Le texte d'un relevé regorge d'identifiants ; la
  file est partagée. La proposition ne porte que l'empreinte, l'émetteur candidat, les scores. Le texte
  reste dans le dossier de run. C'est la même règle que `source_document` retiré en D44, appliquée en
  amont cette fois.
- **Le pipeline écrit un fichier, l'agent parle au MCP.** Même symétrie que le lecteur : sandbox sans
  réseau, donc `propositions.json` en sortie, relais par l'agent (étape finale ajoutée à SKILL.md). Le
  run reste une fonction pure de ses fichiers, donc reproductible.

**Le garde-fou D44 m'a arrêté sur mon propre test**, et c'est un bon signe. La sentinelle `ZZ99887766`
du test — un faux numéro de contrat destiné à prouver la non-fuite — a été refusée au scellement : le
motif `[A-Z]{2}[0-9]{5,8}` ne distingue pas un faux d'un vrai. Corrigé avec le préfixe **`XX`**, réservé
aux références fictives et exempté par le garde-fou. Le test reste probant (il cherche la sentinelle par
sous-chaîne, hors garde-fou). Un contrôle qui attrape jusqu'aux fixtures fait exactement son travail.

**Boucle démontrée de bout en bout**, sur un run mixte (un relevé Cardif connu + un émetteur inconnu) :
le connu s'apparie sans bruit, l'inconnu produit une proposition, `propositions.json` ne contient que ce
qui est à relayer. La proposition passée à `ref_propose` revient avec `provenance_recue` portant
l'empreinte calculée par le pipeline et `source_gabarit: null` cohérent — puis rejetée (démo). Le
document réel n'a jamais quitté le dossier de run.

**Ce que cela débloque** : le *test de réussite du projet* est désormais exécutable de bout en bout — un
gabarit proposé par le run d'un CGP, arbitré par l'admin, devient visible au `ref_bundle` du run suivant
d'un autre. Il ne manque plus que l'hébergement hors du poste (D43) pour que « un autre CGP » soit
littéral, et le dashboard admin (D34) pour que l'arbitrage ait une surface.

---

## 2026-07-29 (13) — L'alignement du lecteur, consigné en CDC v5

Discussion d'alignement (28–29/07) close et consignée : `docs/CDC_v5_2026-07-29.md`, **D45–D49**,
O3 clos, O17–O18 ouverts. Aucune ligne de code — c'est un tour de conception, à la demande de Thomas
(« une fois l'alignement terminé, note le tout dans le cahier des charges »).

**Ce que la lecture de `validation_app` (montée en lecture seule ce jour) a changé.**

- **`excel_to_store` existe déjà** — `validation_app/ingest/excel_to_store.py`, 626 lignes, extrait de
  la racine de fo-data-store le 29/07. La brique que le plan du chantier L me faisait écrire en premier
  est écrite. On la **réemploie** (D47) : migration one-shot + dérivation des stores de vérité.
- **MQ1 et MQ6 étaient déjà résolus en face** : `assureur`/`intermediaire` au contrat, catégories
  liq/immo/dettes typées. La convergence (D48) les rapatrie au lieu de les inventer.
- **Correction d'une affirmation de la veille** : les deux schémas ne divergent pas par la langue des
  clés (le fork a le même sommet français), mais **structurellement et dans les deux sens** — le fork
  porte des amendements postérieurs (poches A5, `lines[]`, `ps`) que validation_app n'a pas, et
  inversement (`blocs_enabled`, catégories typées, verrou optimiste). D'où la règle de D48 :
  confrontation champ à champ, l'antériorité ne vaut pas canonicité.
- **L'Excel de transition meurt** comme surface de rectification (D46, constat d'usage de Thomas :
  aucun CGP ne modifie un classeur de détail ; le README de validation_app actait déjà le remplacement
  du GUI Excel). La question du rond-trip store→excel→store, ouverte la veille, **se dissout**. Le
  chantier D est abandonné comme feature produit ; D4 (dossier de run rejouable) survit.
- **Incohérence relevée en passant** (liste, pas d'interruption) : `excel_to_store` émet
  `schema_version: "1.0"` là où sa doc parle du template v2.0 → O18, et le lecteur n'en fait pas un
  discriminant.

**Décision de méthode reconduite** : on ne coupe pas le chemin Excel→HTML avant la preuve L3a — le
filet de régression actuel ne protège que ce chemin (D45, discipline de bascule).

**Note d'environnement** (consigne Thomas) : si le venv de cette session faiblit, on coupe et on
change de chat — le dossier physique porte tout, rien ne vit dans la session.

---

## 2026-07-29 (14) — Étape ① du chantier L : la confrontation des stores est à TROIS colonnes

`docs/confrontation_stores_2026-07-29.md` écrit — le **format convergé** est défini, écart par
écart, chacun arbitré avec son motif. Méthode : le module validation_app a été lu **et exécuté**
(`excel_to_store.py` sur `imports/reporting_durand_01.xlsx`, dans le sandbox, dépôt intouché) — le
store émis fait foi, pas le docstring.

**La découverte qui recadre tout** : la confrontation n'était pas bilatérale. Le classeur du skill
porte des onglets que `excel_to_store` **ne lit pas** (`Lignes`, `Mouvements`, `NC Flux`, `PS`,
`Cours PS`, `Indices`, `Arbitrages`) — exactement MQ3/MQ5/MQ8 et les lignes classées. Le
sur-ensemble de vérité est le **classeur** (spec §3, normative), pas l'une des deux branches.
L'avertissement de Thomas (« l'antériorité ne vaut pas canonicité ») est confirmé dans les deux
sens : validation_app a aussi ses **pertes silencieuses** — `ownership_pct: 100` codé en dur
(colonne démembrement ignorée), dettes sans date de souscription ni montant initial, non coté lu
jusqu'à la colonne 10 : **MQ4 (TRI) n'est résolu nulle part**.

**Arbitrages saillants** (le détail est dans le document) :

- `pocket.id` existe côté validation_app et sert déjà de `position_id` aux valuations — **C7/D16
  (identifiant stable de poche) est résolu par rapatriement**, la jointure par libellé meurt.
- MQ2 se résout **par la poche** (une ligne classeur = une poche, A5), pas au niveau contrat.
- `blocs_enabled` dans le store validation_app **contredit MQ9** (spec §7.8) : les commutateurs
  restent au manifeste ; ce calcul de faisabilité est le travail de `store_to_manifest` (J1).
  **CDC v5 §2.2 corrigée** — ma phrase « le manifeste et le store convergent d'eux-mêmes » était
  une erreur d'appréciation, consignée comme telle.
- `reference_tables` embarqué (validation_app) est un legacy pré-MCP : D36 tranche, pas de
  référentiels dans le store client. C5 caduc dans sa lettre.
- Règle de nommage proposée : concepts métier en français (`assureur`, `nantissement`…), champs
  techniques inchangés (`value_current`…). Trois questions résiduelles posées à Thomas (nommage,
  assureur en code d'acteur, envelope_type en codes normés) — **non bloquantes**, défauts annoncés.

Prochaine étape : ② dériver les 7 stores de vérité des fixtures — `excel_to_store` exécuté puis
sortie **complétée** des onglets qu'il ne lit pas, au format convergé ; les amendements de schéma
se posent à ce moment-là, chacun avec son entrée au registre (M3).

---

## 2026-07-30 (1) — Étape ② : le format convergé est posé, les 7 stores de vérité dérivés

**Le schéma d'abord.** `store_client.schema.json` réécrit en **`2.1-skill`** — l'amendement
d'ensemble R10 (MQ1–MQ8, MQ10, C7/D16, A4, D49, `nantissement`) : les stores 2.0 ne valident plus,
échec bruyant voulu. `test_store_builder.py` passe de 8 à **15 contrôles**, dont 5 refus prouvés
(sans assureur, poche sans id, montant négatif, dette sans capital restant, + les deux refus A5).
Le registre est à jour dans le même mouvement (M3) : **R10 posée, le compteur du fil de détente
D41-b passe de 11 dettes décidées non posées à 1** (la forme d'une ligne de la table de contexte).

**Le dérivateur ensuite** — `outils_lecteur/deriver_stores.py`. D47 respecté à la lettre :
l'`excel_to_store` de validation_app est **importé depuis le dépôt monté et exécuté**, sa sortie est
la base ; le script la complète (onglets non lus, colonnes perdues) et la converge. Règle de
conduite héritée de la spec §7.4 : **aucune lecture positionnelle sans vérification d'en-têtes**,
un écart est fatal, jamais toléré. Résultat : **7/7 stores dérivés et valides**, écrits dans
`skill/p1_engine/tests/fixtures/stores/`.

**Deux vérités indépendantes les confirment.** *(a)* Les totaux des stores tombent **à l'euro
près** sur l'`actif_brut` du golden de la régression, 7/7 — un juge que le dérivateur ne connaît
pas. *(b)* La régression complète rejouée (en deux passes, limite 45 s du sandbox) : QC verts
(9/9 partout, 4/4 sur no_portfolio), déterminisme, actif brut = golden, 7/7 — le moteur n'a pas
bougé, le contrat « ne jamais faire régresser » tient.

**Trois découvertes en chemin, chacune par un garde-fou :**

- **`Valorisation`, cinquième type de NC Flux** — attrapé par l'échec bruyant du dérivateur sur
  `fx_simple`. Ce n'est pas un flux : c'est un **point de VL par fonds**, et son logement convergé
  existait déjà — `valuations[]` avec `position_id` = l'entrée non coté. MQ3 se scinde en deux
  logements existants, aucune forme nouvelle. `FLUX_TYPES` du moteur (p2_fill L339) fait foi.
- **L'onglet `Indices` n'a aucun consommateur** : aucun `read_sheet("Indices")` ; le
  `store.get("indices")` de p2_fill L905 lit le **contexte de marché** (la table D39,
  `contexte/{période}.json`), pas le classeur. L'onglet ne rentre donc pas au store — même
  catégorie que la colonne 2 des Dettes.
- **Les dates du classeur sont parfois du verbatim** (« Févr. 2024 »), affiché tel quel par le
  moteur : `invest_date` (contrat et poche) et `date_souscription` perdent leur `format: date` —
  ISO quand connue, verbatim sinon. Un format strict aurait refusé ce que le rendu exige.

Et le défaut silencieux de validation_app confirmé une fois de plus : son
`LABEL_TO_CLASS.get(x, "actions")` transforme une cellule vide en « Actions » — le dérivateur
applique ABSENCE ≠ NULL (classe vide → champ absent), et **exige** la classe sur les lignes, où
elle est requise.

Prochaine étape : ③ le lecteur (`store → listes canoniques de read_sheet`), puis ④ le harnais L3a.

---

## 2026-07-30 (2) — Étapes ③ et ④ : le lecteur est écrit, et L3a est PROUVÉE — 7/7 à l'octet près

**La colonne vertébrale (D20/L2) existe.** `skill/p1_engine/lecteur_store.py` : une **façade** qui
présente un store 2.1-skill sous l'interface classeur que le moteur consomme déjà (`sheetnames`,
`iter_rows`, ligne 3 d'en-têtes vide → repli « indices canoniques » de `read_sheet`, qui est
exactement notre contrat). **Le moteur ne change pas** — la substitution tient en un point :
quatre lignes dans `main()` de `p2_fill.py` (un `.json` est un store, tout le reste est inchangé).
C'est la promesse de L2 tenue littéralement.

**L3a : rendu depuis le store ≡ rendu depuis l'Excel, hash SHA-256 identique, 7 fixtures sur 7.**
Harnais rejouable : `p1_engine/tests/test_l3a.py` (accepte un sous-ensemble de fixtures, utile
sous timeout). Pas une tolérance, pas un « écart explicable » : l'octet près.

**Le lecteur est la position canonique des tables d'affichage (A2/A3)**, et cette position a été
gagnée par l'erreur : codes → libellés (`actions` → « Actions »), enveloppes → natures (`av_lu` →
« AV »), booléens → « Oui »/« — », ISO → jj/mm/aaaa, MOIC nombre → texte français. Le premier
smoke test a échoué sur **un** chiffre : mon `.1f` arrondissait `1,06x` en `1,1x` — le formatage
doit préserver la valeur, jamais la résumer (A3 en action). Trois autres corrections tirées des
sondes de types AVANT l'écriture : `taux` verbatim sur les dettes (« SOFR+0,9% » n'a pas de
nombre), `balance` optionnelle (cellule vide → « — » au rendu, pas « 0 € » — le `or 0.0` de
validation_app était un défaut silencieux de plus), motif d'id d'entité assoupli (le manifeste
reprend les ids de l'onglet Entités : `tmp_ent_NNN` cassait la correspondance).

**Ce que le lecteur REFUSE, et le dit** (L5) : les produits structurés (`attributes.ps`) — leur
forme au store est incomplète (pas de logement nominal/valeur-si-cassé, MQ5 à finir) et aucune
fixture ne les exerce ; un store qui en porte lève une erreur explicite plutôt qu'un rendu amputé.
Idem code d'enveloppe inconnu, poche non résolue, type de flux hors vocabulaire.

**Le garde-fou D44 m'a encore attrapé** : « Gronier » écrit dans deux fichiers vendorés (docstring
de test_l3a, description du schéma). Dé-identifié (« le client de référence »), paquet rescellé —
**128 fichiers**, selfcheck OK. Suites : test_store_builder 15/15, test_referentiels 17/17,
test_producteur OK, régression moteur 7/7 (rejouée à l'étape ②).

**Précision de Thomas (mid-run), consignée en CDC v5 §1.3** : il y a DEUX Excel. L'Excel de
**structure** (3 feuilles) est l'entrée de production — c'est lui que la conversion one-shot D45
vise, avec son propre petit convertisseur à venir. Le format **riche** (transition) ne sert plus
qu'aux fixtures, à la reprise de l'existant, et à un éventuel export (écarté par D46). Ne pas
dimensionner le convertisseur de production sur un format que les CGP ne rempliront jamais.

**Reste du chantier L** : l'étape ⑤ (bascule puis coupure) attend son heure — le SKILL.md doit
brancher le mode (b) de D6 (`{client}.json` direct) sur ce chemin, et la régression basculer sur
les fixtures-store. Et L3b attend toujours le store du client de référence régénéré depuis les
relevés officiels.

---

## 2026-07-30 (3) — Sidetrack historique : l'arrêté devient un objet de première classe (D50/D51)

Demande de Thomas, avec sa boussole (`CAHIER_DES_CHARGES.md` plateforme, v. 06/07) en pièce
jointe : des **shards par année** dans la base pour que les reportings consultent un historique,
au lieu du tableau « reconstruit comme on peut ». La reconnaissance dans le skill a montré pire
que « comme on peut » — **quatre sources, trois fragiles, une orpheline** :

- l'onglet `Historique` porte des perfs annuelles **déclarées par le CGP, jamais recalculées** ;
- `snapshots/{client}_{période}.json` (comparaison N-1 + gel des coupons PS) est écrit par le
  moteur **en local, relatif au cwd** : un autre CGP, une autre machine → le N-1 disparaît
  **silencieusement**. La famille de bugs que D36 a tuée pour les référentiels, toujours vivante
  pour l'historique — et la source de la fuite `tmp_ent_001` et de la pollution du cwd ;
- `cp_valos.json` du run de référence : le grain exact de `valuations[]`, jamais entré au store.

**Posé dans `docs/spec_historique_arretes_2026-07-30.md`** : le grain logique est l'**arrêté**
(l'année seule détruirait les lignes trimestrielles du tableau), la partition physique est
l'**année** — la demande est satisfaite par le partitionnement, pas par le grain. Colonnes
dépliées (invariant §8 de la boussole), provenance D49/audit par ligne, immuabilité (correction =
nouvelle version), rendu en **projections dérivées** relayées par l'agent (même symétrie que les
référentiels), perfs annuelles **recalculées**. Vit dans le **datahub client** (D6, permissions
D2), jamais dans la base des référentiels (D33/D44 — l'historique est un fait client, pas un fait
de marché). `snapshots/` meurt **après** double lecture, pas avant (discipline D45). C'est la
part *reporting-grade* de R3 — le wayback complet reste en vague 4.

**UX (D51)** : les relevés historiques passent par le pipeline NORMAL — la fenêtre de validité
D42/LIM5 existe précisément pour lire les archives, un relevé 2023 produit un arrêté rétroactif.
Le skill **détecte** l'historique manquant et le **demande** par AskUser ; le geste est le drag &
drop du chat, qui existe déjà. Disponibilités/matières premières : des relevés désormais,
l'AskUser d'origine rétrogradé en repli.

Aucun code — les formes SQL et méthodes `Store` se posent avec le datahub (entrée au registre à
ce moment-là, M3) ; les projections dérivées arrivent après la bascule ⑤, avec le chantier B.

**Correction de Thomas dans la foulée, D51 amendée** : pour disponibilités/matières premières, la
présence de la donnée dans les relevés ne dit pas que le CGP **veut** la section. La donnée entre
au store inconditionnellement ; l'AskUser porte sur l'**intention** d'afficher, ne se pose que si
la faisabilité existe, et se persiste via `tri_decisions` (D30) — c'est la séparation MQ9 (« le
store répond peut-on, le manifeste répond veut-on ») appliquée à la collecte. Ma première
rédaction en faisait un repli de collecte : corrigée. Le grain arrêté/partition-année est validé.

---

## 2026-07-30 (4) — Bascule ⑤ : le store est le chemin nominal, prouvé sur la chaîne COMPLÈTE

**La bascule exigeait une brique que le plan n'avait pas nommée** : en mode store pur, le
manifeste n'avait pas de source (`excel_to_manifest` lit le classeur). Écrit :
`p1_engine/store_to_manifest.py` (**J1**, version minimale) — miroir exact d'`excel_to_manifest`,
même CLI, `entities[].categories` **dérivé** du store (le fait, pas le choix — MQ9), les
commutateurs de rendu restant des arguments. C'est le point de rencontre exact du « peut-on »
(store) et du « veut-on » (manifeste).

**La preuve s'est étendue à la chaîne complète** : `test_l3a.py` génère désormais LES DEUX
manifestes (égalité JSON exigée) puis rend chaque chemin avec le sien — **7/7 identiques**,
manifeste et HTML. Et la preuve a immédiatement payé : premier run, 2 manifestes sur 4
divergents. Cause : validation_app **devine** le profil client depuis la colonne 7 du premier
contrat, là où le moteur lit la cellule « Profil » de l'onglet Entités (défaut Équilibré). Deux
heuristiques pour la même donnée — le dérivateur reproduit désormais celle du moteur, c'est elle
que le golden protège. Une divergence de plus au compte de la confrontation à trois colonnes.

**SKILL.md basculé** : l'Egress §2.e ne passe plus par le writer (« projeter vers l'Excel de
transition » — mort avec D46) mais rend **directement depuis le store**
(`store_to_manifest.py` + `p2_fill.py {client}.json`). Le mode CONSOMMATION (D6-b) pointe sur ce
chemin. L'ancien chemin Excel reste documenté pour la seule **reprise de classeurs historiques**.

**La COUPURE (retrait du chemin Excel du moteur) est différée, avec prérequis nommés** — on ne
coupe pas un chemin encore nourri : *(a)* le convertisseur de production Excel de structure
3 feuilles → store d'ancres (CDC v5 §1.3) n'existe pas encore ; *(b)* le chantier B (extraction
PDF → diffs → apply) est le producteur nominal du store et n'est pas construit ; *(c)* la reprise
des classeurs riches historiques passe encore par lui. Quand (a) et (b) existent, le chemin Excel
du moteur devient du code mort et se retire — avec bascule du golden sur les fixtures-store.

Filet complet rejoué après la bascule : régression golden 7/7 (les DEUX moitiés), test_l3a 7/7
chaîne complète, suites pipeline vertes, paquet rescellé à **129 fichiers**, selfcheck OK.

---

## 2026-07-30 (5) — Chantier B : la roadmap déballée, vérifiée, pas encore exécutée

`docs/roadmap_chantier_B_2026-07-30.md` — la passe de cohérence demandée par Thomas avant toute
exécution. B1–B10 revisités un par un face à D40–D51 et au chantier L clos. L'essentiel :

- **Trois vérifications positives** : les 9 profils du seed portent tous `invariant_controle` et
  `champs_publies` (B8/B9 nourris) ; le contrat de diff est intact ET suffisant — les clés du
  format convergé voyagent dans `path`, B7 tient sans amendement ; la provenance D49 se calcule à
  l'apply, elle n'entre pas dans le contrat.
- **Le chaînon manquant est l'APPLY** : SKILL.md §2.d dit « consolider via store_builder » — un
  geste d'agent, pas un outil. `appliquer_diffs.py` à écrire, avec quatre responsabilités : la
  provenance D49, les `pocket.id` déterministes (C7), la résolution assureur → code acteur (K3),
  le remplissage piloté par `champs_publies` (MQ11).
- **Le filet B a cinq couches nommées** : jsonschema → invariant du gabarit (D25) →
  réconciliation (B3/D30 batché) → QC comptables → verbatim source_page. Aucune n'est l'égalité
  exacte ; chacune attrape sa classe d'erreur. LIM8 se lève par empilement, pas par un miracle.
- **Périmé attrapé** : A8 (writer & feuilles v5) contredisait D46 — ligne barrée à la roadmap.
- **Décision de séquencement proposée** : B v1 en mode **ré-entrée** (le `{client}.json` existant
  est la base old) — le convertisseur structure 3 feuilles reste à A6, B ne l'attend pas.
- **Plan en cinq jalons** : B-i priming par profil (N3 débloqué — c'était « suspendu faute de
  filet », B EST le filet) ; B-ii outillage (valideur + apply) ; B-iii table de vérité
  d'extraction (la méthode qui a sauvé le matcher, appliquée une 3ᵉ fois — points de contrôle
  discriminants, pas extraction de référence complète) ; B-iv premier run réel + mesure O10 ;
  B-v réconciliation batchée + banc INTERAGYR (A9).

Trois questions posées à Thomas avant B-i : mode ré-entrée d'abord ; tolérance des invariants
portée par le profil (« au centime sauf déclaration contraire ») ; B-iv sur corpus ou INTERAGYR.

**Tranchées le jour même** (roadmap B §6 mise à jour) : ré-entrée OUI ; tolérance au profil OUI ;
B-iv sur **INTERAGYR d'abord puis le client de référence** — gradient de complexité croissante.
La réflexion de Thomas sur un « Excel de données complet qui bypasserait l'extraction » est
consignée avec sa réponse déjà en place : ce bypass existe avec la garantie (mode CONSOMMATION,
provenance D49) ; la variante Excel serait le même geste moins la provenance — le motif exact de
D46. Prérequis logistique noté pour B-iv : la base de ré-entrée INTERAGYR devra être fournie au
fork (aucun store INTERAGYR ici, constat C4).

---

## 2026-07-30 (6) — B-i : le priming par profil est câblé, N3 soldé, le chien de garde retourné

**Bonne surprise en ouverture** : B-i n'exige NI régénération de seed NI rejeu en base. Vérifié
avant de toucher quoi que ce soit — les 9 gabarits du bundle **et** du snapshot portent déjà
`extraction_hints` (pièges, ancrage, format numérique), `champs_publies` et `invariant_controle`,
et les profils sont un **sur-ensemble strict** des pièges en dur du SKILL.md (Dauphine : 12 pièges
au profil contre 3 sommaires en dur). Le travail était un recâblage pur.

**SKILL.md §2.b recâblé** :

- **L'identification entre dans le protocole** (étape 2, avant tout dispatch) : chaque PDF passe
  au matcher (profils du `referentiels.json` du run, arrêté du contexte). `apparie` → subagent
  primé ; `ambigu`/`aucun` → extraction **quand même**, en prompt générique, signalée dans
  `notes` + proposition (boucle N5) ; `illisible` → OCR, signalé au CGP, pas de dispatch.
- **Les pièges d'émetteur en dur sont RETIRÉS** : le point 4 dit désormais de copier **verbatim**
  depuis le profil apparié — `extraction_hints.*`, `champs_publies` (avec la règle MQ11 : on
  remplit ce que la source publie, on n'invente pas ce qu'elle tait, D40 pour le comblement),
  `invariant_controle` (vérifié avant d'émettre, au centime sauf tolérance déclarée DANS
  l'invariant — décision Thomas du 30/07). Mettre à jour un piège = mettre à jour le **profil**,
  jamais le SKILL.md : un piège appris par un CGP profite au suivant — c'est N3 réalisé, et c'est
  le même mouvement que D36 pour les référentiels.
- Restent en dur, à bon droit : les pièges « entrées du skill » (Excel CGP `data_only`, légendes)
  et les règles génériques (ISIN, GEO_RULES, codes, Σ±1 €, noms canoniques, multi-mandats).

**`verifier_pieges.py` retourné** : sa raison d'être (rendre la duplication détectable en
attendant D36) s'est réalisée — il garde désormais l'invariant **inverse** : aucun nom d'émetteur
ne doit revenir dans le §2.b. Et il a mordu **immédiatement** : trois marqueurs restants… dans
l'exemple de désambiguïsation multi-mandats (« UBS (Dauphine — Offensif) »). Pas un piège — mais
l'exemple n'avait pas besoin de noms réels : neutralisé en « Gérant A / Gérant B » plutôt que
d'affaiblir le garde par une liste blanche. Un chien de garde qu'on dresse à tolérer des
exceptions finit par ne plus garder grand-chose.

Suites vertes, paquet rescellé (129 fichiers), selfcheck OK. **Prochain jalon : B-ii** —
l'outillage déterministe (`valider_diff.py` + `appliquer_diffs.py` et ses quatre
responsabilités : provenance D49, pocket.id C7, résolution acteurs K3, remplissage MQ11).

---

## 2026-07-30 (7) — B-ii : l'apply cesse d'être un geste, il devient un outil

`skill/pipeline/valider_diff.py` et `appliquer_diffs.py` écrits, testés (`test_apply.py`,
**20 contrôles**, dont 5 refus prouvés), branchés au SKILL.md §2.d. Paquet rescellé à
**132 fichiers**, selfcheck OK, garde N3 au vert, toutes suites vertes.

**Le valideur** (première couche du filet B) : jsonschema + trois règles que le schéma ne sait
pas dire — `update` sans `entry_id` refusé (ne vise personne), montant de mouvement négatif
refusé (A4, à l'entrée, pas à l'apply), et le vocabulaire des lignes à deux niveaux : les
variantes **connues** des runs réels (`value_eur`, `class_code`, `geo_code`…) passent en
avertissement et se normalisent à l'apply, une clé **inconnue** est une erreur — un champ qu'on
ne reconnaît pas est une donnée qui se perdrait en silence.

**L'apply** et ses quatre responsabilités (roadmap B §3.1), chacune testée aussi par le refus :
provenance **D49** posée depuis le contexte d'identification (§2.b étape 2) ; **`pocket.id`**
attribués en séquence globale + `lines[].pocket` résolus du libellé vers l'id (C7 — la jointure
par texte meurt à l'entrée) + poche 0 auto (A5) ; **`assureur` → code acteur** par alias, non
résolu = verbatim + signalement K3, jamais de code inventé ; contrôle **MQ11** quand
`champs_publies` promet la perf par ligne. Règle dure héritée de D4 plateforme : `old_value` ≠
store = **CONFLIT**, champ non appliqué, rapporté pour B3 — jamais de last-write-wins. Et un
diff invalide dans un lot ne bloque pas les autres, il est rapporté.

**Le test s'est trompé avant l'outil, et c'est instructif** : le contrôle MQ11 ne se déclenchait
pas parce que j'avais primé le test avec le gabarit Wealins — qui publie la perf **par poche**,
pas par ligne. La matrice `champs_publies` a corrigé mon intuition, exactement le service qu'on
attend d'elle au runtime.

**Reste de B** : B-iii (table de vérité d'extraction sur le corpus — points de contrôle
discriminants, à écrire AVANT tout prompt), puis B-iv (premier run réel : INTERAGYR — Thomas
fournira la base de ré-entrée), puis B-v (réconciliation batchée + A9).

---

## 2026-07-30 (8) — B-iii : la table de vérité d'extraction, relevée dans les documents réels

`outils_extraction/` (hors paquet, comme `outils_appariement/` — le corpus reste hors
distribution, D44) : `table_verite_extraction.json` + `harnais_extraction.py`, autotest au vert
dans les deux sens. Troisième application de la méthode table-de-vérité-d'abord — écrite AVANT
tout prompt de subagent.

**La méthode** : des POINTS DE CONTRÔLE, pas des extractions de référence — chaque valeur a été
**relevée dans le PDF réel** (pdftotext + lecture) le 30/07, jamais déduite. 8 documents établis
couvrant 6 gabarits sur 9 (Himalia, Cardif v1 ET v2, Spirica, Wealins annuel ET trimestriel,
PPT, Dauphine), 4 documents `a_etablir` que le harnais SIGNALE sans les faire échouer (même
convention que la table d'appariement). Nortia reste sans document dans les monts — a_etablir
de fait.

**Ce que le dépouillement a montré en passant** :

- **Le piège de double convention PPT, vu en direct** : « Valeur totale 1,982,034 » (bloc Résumé,
  anglo-saxon, euros ronds) contre « Total : 1 134 708,36 » (détail franco-suisse) dans le même
  document — le piège du profil n'est pas théorique, la table l'exerce (tolérances distinctes).
- **La jointure temporelle passe par l'ISIN, jamais le libellé** : LU1940199711 s'appelle
  « LYXOR MSCI EUROPE » en 2024 et « AMUNDI MSCI EUROPE » en 2025 — même support, gérant
  renommé. Consigné comme note du point de contrôle Cardif v2.
- **La succession K5 est visible dans les poches** : la FAS de FC051727 est « Banque Thaler
  (540709) » au 31/12/2025 et « CA Indosuez (1719249) » au 30/06/2026 — numéro ET teneur
  changent, seule la nature FAS survit. Le point de contrôle porte la note.
- **Interagyr.pdf EST le relevé PPT** (SSRS, compte 5045739001, dépositaire UBS Fr) — le mont
  15.7.26 couvre donc PPT + Dauphine ×3, pas seulement Dauphine.

**Le harnais sait refuser** (contrôle négatif intégré `--autotest`) : un store conforme passe
5/5, le même store avec UNE valeur corrompue de 100 € tombe sur DEUX points (la ligne et
l'invariant D25) — deux couches indépendantes qui attrapent la même faute, c'est le filet B en
miniature. Portes : contrat, ligne, poche, invariant, agregat, champ_promis (MQ11), info.

**Reste de B** : B-iv — premier run réel sur INTERAGYR (Thomas fournit la base de ré-entrée),
puis Gronier en complexité croissante ; B-v — réconciliation batchée + A9.

---

## 2026-07-30 (9) — B-iv : le premier run réel, de bout en bout, et la boucle entière a travaillé

`runs/interagyr_2026-07/` — mode **AGRÉGATION** (Thomas a fourni l'Excel de STRUCTURE, pas la
ré-entrée prévue : le flux nominal complet a donc été exercé). Décisions CGP par AskUser batché :
comptes séparés (le cas multi-mandats du §2.b, en vrai — 4 CTO UBS), arrêté 15/07/2026.

**Chaque brique construite cette semaine a servi, dans l'ordre :**

- **ref_bundle sur le MCP VIVANT** (D36) — 17 acteurs/2 successions/9 gabarits, contrat d'outil
  échoïsé. Premier run dont les référentiels viennent du store partagé, pas du snapshot.
- **Identification** (B10) : 4/4 appariés, scores 0,96–1,00 — y compris les noms mojibake.
- **Ancres** depuis la structure (store 2.1 valide), poches pck_001..004, ids déterministes.
- **4 subagents primés** (B-i), dispatchés en un message, ~100 s en parallèle réel. Le priming a
  visiblement travaillé : filigrane filtré, U+2212, monétaire PPT reclassé, double convention
  numérique gérée, sous-totaux non double-comptés, « — » ≠ 0.
- **Le valideur (B-ii) a mordu au premier lot** : 2 diffs avec `unrecognized_data` mal formé
  (clés inventées `type`, `content`/`section`). Renvoyés à leurs subagents avec les erreurs
  exactes — corrigés sans perte (replié dans description/raw). Le filet B couche 1 fait son
  travail : la variance est attrapée à l'entrée, pas découverte au rendu.
- **Apply (B-ii)** : 4 changements, **0 conflit** (old_value = ancres), provenance D49 posée
  partout, 4 acteurs non résolus (attendu — contrepartie du choix comptes séparés, consigné
  comme question de modélisation).
- **Harnais (B-iii) : 7/7 points** sur PPT + Dauphine Offensif — après DEUX corrections du
  harnais lui-même révélées par le run : le scope par contrat (juger un store multi-contrats
  mélangeait les lignes) et l'exemption liquidités sur `champ_promis` (le harnais était plus
  strict que la règle qu'il vérifie — l'extraction avait raison, le juge avait tort).
- **Rendu direct depuis le store** (bascule ⑤) : store_to_manifest + p2_fill, **QC 7/7**,
  déterministe, actif brut 4 723 156 €, HTML dans le dossier de run.

**Écarts pour la réconciliation CGP** (README du run, §Écarts) : ancres vs relevés (Offensif
−2 559 €, le plus gros), profil PPT « Croissance » vs « Dynamique » structure, dates 15 vs 16/07,
un achat LBPAM +25 116 € en unrecognized_data. Rien tranché en silence.

**B-iv est fait pour INTERAGYR.** Suite : les écarts au CGP (B-v, avec le banc A9), puis le
client de référence en complexité croissante. Et deux corrections d'outils à retenir : le harnais
a maintenant `scope` par document et l'exemption liquidités — l'autotest reste vert.

---

## 2026-07-30 (10) — Revue contre le contrôle d'époque : un bug de jointure, pas du code perdu

Thomas a fourni `consolide_Interagyr.html` (23/07, mêmes documents) comme contrôle, avec cinq
points de revue. Diagnostic complet : `docs/revue_controle_interagyr_2026-07-30.md`. Trois
familles de causes, presque rien de perdu :

- **LA cause racine (points 2 et 4-vides) : la jointure nature s'est cassée.** « Compte Titres »
  (structure) → `cto` (ancre) → « CTO » (lecteur) : le moteur joint les lignes par
  `norm("{nature} — {banque}")`, aucun hit — les 53 lignes classées n'ont alimenté ni donuts, ni
  géo, ni SRI pondéré, **silencieusement**. L3a ne pouvait pas le voir : les fixtures écrivent
  des natures qui survivent à l'aller-retour code→affichage. C'est le hasard de vocabulaire A2
  matérialisé. Correctif décidé : `nature` VERBATIM optionnelle au store, lecteur la préfère.
- **Données absentes des entrées** : sri jamais émis par les subagents (repli par classe → SRI 6
  au lieu de 4 ; remède : enrichissement DÉTERMINISTE sri/class/geo par le référentiel ISIN à
  l'apply — la « priorité absolue » devient mécanique) ; ni flux PE ni valorisations dans la
  structure → courbe vide et **graphiques PE muets — rien n'est perdu, `fx_simple` les rend**,
  ils sont pilotés par les flux ; le vide de la courbe est le vide de l'historique (D50) : au
  premier run, il n'y a pas de passé.
- **Style moteur vs contrôle d'époque** : l'en-tête « Reporting au DATE » est un simple
  `period_long` (zéro code) ; le double donut coté/non coté, les sous-tableaux par contrat, le
  SRI coté affiché, les blocs explicatifs PE — le contrôle était en partie composé par l'agent,
  le moteur ne les a JAMAIS eus. À traiter en **chantier UI dédié**, pas au fil de l'eau.

**Leçon de méthode** : le fork protège « ne pas régresser le moteur » (golden, L3a) — la
référence UX du CGP est le rendu d'époque. Il manque un troisième juge : la **parité de blocs
contre un contrôle d'époque**. Cette revue en est le premier exemplaire.

**Mesure O10 au passage** : pipeline complet en **11 minutes contre ~25** à l'époque.

**Correction de Thomas dans la foulée, vérifiée au code et au contrôle** : la courbe PE consomme
des **valorisations à date**, jamais des mouvements — `_nav_at` prend la dernière Valorisation ≤
date (les appels ne sont qu'un proxy au coût, les flux ne servent qu'à l'échéancier), et le
contrôle le montre (`perf_nc_bars` : deux barres de VL, 05/26 et 07/26). Ma formulation « pilotée
par les flux » venait du nom trompeur de l'onglet « NC Flux », qui mélange deux natures que le
store convergé sépare déjà (`valuations[]` vs `mouvements`). Le run était muet faute de TOUTE
valorisation NC — rapports PE hors périmètre §2.b et structure sans VL. Deux décisions ouvertes :
la source des VL non cotées (saisie CGP et/ou rapports trimestriels PE), et vérifier au re-run
que les deux barres AU COÛT se dessinent au minimum, comme le contrôle. Revue corrigée (§5).

---

## 2026-07-30 (11) — PE arbitré, détail ligne à ligne diagnostiqué, contrôles d'époque archivés

Trois mouvements dans la discussion du soir, tous consignés dans la revue
(`docs/revue_controle_interagyr_2026-07-30.md` §2-bis, §2-ter) :

- **L'observation « beaucoup plus grave » de Thomas — le détail ligne à ligne absent** : vérifié,
  53 lignes au store, ZÉRO au rendu, même cause racine que les donuts (la jointure nature,
  L1067). Mais la leçon dépasse le bug : les QC ont dit 7/7 pendant que le cœur du reporting
  manquait — AUCUNE couche ne surveille la traversée store → HTML. Décision : **QC de traversée**
  (Σ lignes rendues = Σ lignes du store, par contrat, QC n°10 de p2_fill), posé AVANT le
  correctif pour le voir échouer sur le run actuel — contrôle négatif gratuit.
- **PE arbitré** : étages 1-2 (situations d'associé, ciblage par segments) = doctrine dormante
  faute de documents — leurs gabarits naîtront par self-healing quand les docs arriveront ;
  **AskUser « fonds PE sans document » proposé par Thomas** — batché B3/D30, VL datée déclarée ou
  affichage AU COÛT qui se dit tel ; étage 3 acté (colonnes VL/Date de VL dans la structure).
- **`reference/controles_epoque/`** créé : le contrôle INTERAGYR (23/07) et le **Reporting
  Gronier T2 pré-compilation** (27/07) fournis par Thomas — avec son avertissement en README :
  « il a de nombreux défauts ». Règle d'usage écrite : un contrôle d'époque se confronte, il ne
  se recopie pas ; un défaut du contrôle est une quatrième issue possible d'un écart.

---

## 2026-07-30 (12) — Correctifs de la revue : le run INTERAGYR retrouve son cœur, et les valeurs du contrôle

Séquence exécutée dans l'ordre annoncé, chaque garde vu refuser avant de passer (R11 au registre) :

1. **QC n°10 « traversée »** posé AVANT correctif → **échec prouvé 0/53** sur le run fautif. Le
   juge qui manquait existe : un reporting qui perd une ligne entre le store et l'HTML échoue.
2. **Correctif `nature` verbatim** (schéma + lecteur + ancres + dérivateur) : le mot du client
   fait les clés de jointure — le code d'enveloppe reste la donnée normée. + `GEO_VERS_LIBELLE`
   au lecteur (les codes géo s'affichaient en snake_case).
3. **Enrichissement référentiel à l'apply** : class/geography/sri des lignes complétés/corrigés
   par `isin_referentiel_v0.csv`, priorité absolue mécanique. Constat honnête : la colonne `sri`
   du référentiel est **vide sur 261 lignes** — le SRI 4 du contrôle d'époque ne venait d'aucune
   source traçable ; le remplir est un chantier de DONNÉE (à ordonnancer).
4. **Re-run INTERAGYR** : QC **9/9** (traversée 53/53), **SRI 4/7 pondéré et SRI coté 3/7 — les
   valeurs exactes du contrôle, retrouvées par la mécanique** dès que les lignes joignent (la
   pondération par classes réelles fait le travail, sans aucun SRI de ligne) ; « Exposition
   géographique » alimentée ; LVMH et le détail ligne à ligne au rendu ; en-tête « Reporting au
   15 juillet 2026 » (simple period_long) ; actif brut inchangé 4 723 156 €.
5. **Filet complet** : golden 7/7 (10/10 QC sur fx_lignes_classes — le QC de traversée vit),
   L3a 7/7, test_apply/test_store_builder verts, paquet rescellé 132 fichiers, selfcheck OK.

**Et D44 a encore mordu, trois fois** : « INTERAGYR » dans deux commentaires vendorés
(dé-identifiés), et — récidive structurelle — **p2_fill a écrit `snapshots/interagyr_T3-26.json`
DANS le paquet** pendant mes rendus (cwd = skill/). Supprimé. C'est la troisième fois que le
répertoire snapshots/ fait parler de lui : l'argument vivant pour D50, et un rappel de discipline
— les rendus de clients réels se font depuis un répertoire jetable, jamais depuis skill/.

**Reste de la revue** (points de style, chantier UI dédié) : double donut coté/non coté,
sous-tableaux par contrat, blocs explicatifs PE, colonne cible — sur pièces, avec les deux
contrôles d'époque. Et le canal éditorial (commentaire de gestion/ACTUALITÉS) à spécifier.

---

## 2026-07-30 (13) — Deuxième passe de revue : un bug corrigé (enveloppes), une découverte (le canvas PE n'a jamais existé)

Six points de Thomas sur le run corrigé, tous diagnostiqués et consignés (revue §2-quater) :

- **BUG corrigé dans l'heure** : `envelope()` ne connaissait que les formes courtes ('cto') — la
  nature verbatim « Compte Titres » tombait dans le **repli Assurance-vie en silence**, le donut
  Enveloppes mentait. Formes longues reconnues, donut vérifié (« Compte Titres » ×10). Le repli
  silencieux vers AV reste un vice à rendre bruyant (chantier UI). Filet rejoué : golden 7/7,
  L3a échantillon vert, paquet rescellé, selfcheck OK — et rendu depuis un répertoire jetable
  cette fois (leçon snapshots appliquée).
- **DÉCOUVERTE point 6** : le canvas PE n'a **jamais existé dans la banque du moteur** —
  `p2_fill` calcule les séries (views/bars, repli au coût compris), le template
  `performance_nc` ne les dessine pas. Plomberie prête, dessin manquant : coût faible au
  chantier UI.
- Le reste trié : contexte 00 = table D39 sans entrée T3-26 (processus de rédaction trimestriel
  à trancher) ; « Court terme » à déplier (G6, taxonomie d'affichage) ; 02 = D50 + éditorial,
  avec l'idée « courbe 2 points » pour nouveaux clients (à valider) ; colonnes adaptatives par
  disponibilité de données (principe directeur du chantier UI, perspective de Thomas) ; dispos
  pleine largeur acquis, MP en petit bloc confirmé.

Le chantier UI a maintenant son périmètre complet, ses pièces (deux contrôles d'époque) et ses
principes. C'est la prochaine grande discussion de design.

---

## 2026-07-31 (14) — Chantier UI ouvert : dossier de design, et bloc 1 (canvas PE) soldé en renversant une décision d'époque

4ᵉ session, contexte frais sur `REPRISE.md` (amorçage vert). Le chantier UI s'est ouvert
par l'**instruction sur pièces** — comparaison bloc à bloc des trois rendus (contrôles A/B + run
C) et inventaire de la banque — consignée dans `docs/chantier_ui_design_2026-07-31.md`
(8 décisions D-UI-1…8). Trois recadrages issus de l'instruction :

- **Il n'y a pas deux styles à unifier** : B (Gronier) est conforme au bit à la banque actuelle,
  C = B moins la donnée absente ; A (INTERAGYR 23/07) n'est conforme à rien — composition
  d'époque hors moteur. « Unifier » = décider trait par trait ce qu'on porte de A vers la banque.
- **Le double donut coté/non coté existe déjà** (donuts_sup, arcs + classes) — le point 2b de la
  revue se réduit à la taxonomie « Court terme » (D-UI-5).
- **Archéologie du canvas PE** : W2/W3 n'avaient pas « jamais existé » — **supprimés le
  23/07/2026 « à la demande du CGP »**, `test_pnc.mjs` vérifiait leur ABSENCE. Signalé à Thomas
  avant toute ligne ; arbitrage explicite : **« Rétablir tout » → D53**.

**Bloc 1 FAIT (D-UI-1/D53)** : W2 (barres + ligne, plugin segPct) + W3 (composition MOIC/TVPI/
cible) + pitch + bascule par fonds portés dans `performance_nc.html.j2` depuis le gabarit A —
le CSS était déjà dans `_styles.html`, la plomberie `p2_fill` n'avait jamais cessé de calculer.
S'y ajoute la **règle de sincérité** (revue §2-ter) : `p2_fill` expose la provenance de la série
(`cout` par fonds, `cout_note` par vue), le titre du graphe dit « · au coût (capital appelé) »
quand la NAV est un proxy d'appels, et la note suit la bascule de vue.

**Le test retourné a tout jugé** : `test_pnc.mjs` (qui était RASSIS — pas dans la suite courante,
écrit avant le fork presentee/envoyee) vérifie désormais la PRÉSENCE de W2/W3, exerce la bascule
(update du chart, surbrillance, restauration KPI), s'adapte au mode en le DISANT
(`[presentee]`/`[envoyee]`), et sort par `process.exit` (les timers décoratifs le faisaient
pendre sous jsdom). Vert dans les deux modes.

**Filet complet** : golden 7/7 (QC de traversée vivant), L3a 7/7 à l'octet, re-run INTERAGYR
depuis le store en répertoire jetable — QC 9/9, actif brut inchangé 4 723 156 €, déterministe,
**les deux barres au coût se dessinent** (240/200/40 K€, paliers T2→T3) avec le titre sincère.
Paquet rescellé 132 fichiers, selfcheck OK, garde N3 verte.

**Et D44 a encore mordu — un faux positif instructif** : un `npm i` interrompu (lenteur OneDrive)
avait laissé `node_modules/` DANS le paquet ; le garde a refusé de resceller sur des noms de
clients fictifs (hanami/shida/matsu) trouvés dans... les tables tldts vendorées. Nettoyé,
leçon prise : les dépendances de test s'installent hors paquet (sandbox), jamais dans `skill/`.

Bloc suivant du chantier : **D-UI-2** (colonne cible PE + chapeau adaptatif + fix `.cdet` amont),
puis D-UI-5/6 (taxonomie Court terme + enveloppe bruyante), puis D-UI-3 (colonnes adaptatives).

---

## 2026-07-31 (15) — Bloc 2 : la courbe coté vit (D-UI-7), et le filet s'est enrichi d'une fixture et d'une clé

Thomas a validé D-UI-7 en séance (« Ok on peut avancer ») après avoir lui-même éclairé la
généalogie : le graphe coté de Gronier remontait parce que Gronier avait l'onglet Historique —
le skill en découle, INTERAGYR n'en a pas. Pas un bug de dessin : le vide D50.

**Fait** : repli à 2 points dans `p2_fill` — sans aucune Valorisation, la « Poche financière »
(la SEULE série que le template dessine — `data_js` global est calculé et jamais dessiné,
un cousin du canvas PE) se trace du capital investi coté (mois du premier investissement) à la
valeur à l'arrêté, `degraded=True`, **note de sincérité** sous le canvas, garde d'échelle
±2,5 % réutilisée. `curve_end_eur` non posé — le QC « courbe ≈ actif net » juge le patrimoine
global, pas la poche cotée.

**La leçon de filet** : AUCUNE fixture n'exerçait le repli (toutes celles qui ont du coté ont
des Valorisations) — un invariant non testé n'est qu'un commentaire. Créé `fx_courbe2pts`
(fx_simple moins Valorisations), enseigné au harnais la clé `curve_degraded` (jugée sur CHAQUE
fixture : un repli qui cesse de s'annoncer est une régression muette), golden ré-enregistré
**avec diff prouvé** (7 fixtures inchangées au centime ; le « 9/9 » de fx_lignes_classes au
golden était rassis d'avant le QC de traversée, remis à 10/10 réel). Store de vérité dérivé
via D47 — `validation_app/ingest` remonté par Thomas en **lecture seule** (le montage de
l'ancienne session n'existait plus ; `DEFAUT_VALIDATION_APP` dans `deriver_stores.py` pointe
un chemin de session mort, à paramétrer au prochain passage). Golden 8/8, **L3a 8/8 à
l'octet**, re-run INTERAGYR QC 9/9 (05/26 → 07/26, 4,50 → 4,48 M€, échelle figée), actif brut
inchangé, paquet rescellé **134 fichiers**, selfcheck OK, N3 verte.

---

## 2026-07-31 (16) — Bloc 3 : D-UI-2 soldé — la cible à sa place, le chapeau qui dit vrai, la durée réparée à la racine

Trois gestes, trois familles différentes — et c'est la leçon du bloc :

- **Décision de style** : colonne « Cible (MOIC/TRI) » supprimée du tableau fonds (retour aux
  8 colonnes du contrôle A) — la cible vit dans le sous-texte. Le tableau titres garde la
  sienne (pas de redondance là-bas). La décision est un invariant : test_pnc la garde.
- **Bug amont, réparé à la racine** : le `.cdet` tronqué (« · 7 ») n'était PAS un défaut du
  store — le store porte le nombre sémantique (`duration_target: 7`), c'est le **lecteur** qui
  n'apposait pas le suffixe attendu par le template (« valeurs pré-formatées »). `_duree()`
  posé dans lecteur_store.py, même contrat que `_moic()` : préserver la valeur, jamais la
  résumer. « Cible 2,0x · 7y » de retour au re-run.
- **Adaptivité** : chapeau W4 calculé des classes réellement présentes (fonds hors titres) —
  « Fonds de private equity » pour INTERAGYR, « Fonds non cotés » pour fx_simple (PE + dette
  privée). Deuxième titre adaptatif du moteur après geo_title.

Filet : test_pnc vert deux modes (dont un sélecteur corrigé — il jugeait le chapeau du bloc
CÔTÉ, premier `.cote-exh-hd` du document : scoper au conteneur), golden 8/8, L3a 8/8 à
l'octet, re-run INTERAGYR QC 9/9 déterministe, paquet rescellé 134 fichiers, selfcheck OK.

---

## 2026-07-31 (17) — Bloc 4 : « Court terme » déplié, l'enveloppe ne ment plus — et l'AV vivait du repli

**D-UI-5 (option 1, validée en séance)** : le fourre-tout « Court terme » disparaît de
l'affichage — « Monétaire » (fonds monétaires) et « Liquidités » (liquidités de contrats G6 +
comptes hors contrat) le remplacent. La pièce maîtresse est `classe_liquidite()`, **règle
unique à deux consommateurs** (donut Classes, widget Disponibilités) : l'incohérence documentée
par spec_tri_blocs §4.b est soldée — les lignes « Court terme » réintègrent le widget,
« Trésorerie » et « Solde en espèces » sont captés.

**D-UI-6** : `envelope()` externalisée en table `ENV_TABLE` (ajouter une enveloppe = une ligne
+ une couleur, plus jamais un patch de fonction). **La trouvaille qui justifie tout le geste** :
l'assurance-vie n'était RECONNUE nulle part — elle vivait du repli silencieux. Elle est nommée
(« av », « assurance vie », préfixe « assurance »), et l'inconnu va en **« Autre (à
qualifier) »** (bordeaux) + ⚠ au rapport listant les natures verbatim. Contrôle négatif exercé
à l'unité (« Plan Épargne Logement » → Autre + signalé) ; formes AV/CTO/PEA/Capi vérifiées une
à une.

Filet : golden 8/8, L3a 8/8 à l'octet, re-run INTERAGYR QC 9/9 déterministe (zéro « Court
terme », Liquidités + Monétaire au donut, Compte Titres ×10 inchangé, zéro « Autre »), paquet
rescellé 134 fichiers, selfcheck OK, N3 verte.

---

## 2026-07-31 (18) — Recadrage de Thomas : le fork est le PoC (D54), l'hébergement est son Docker local (D55)

Deux décisions de scope posées en séance, consignées au registre :

- **D54** : le merge fork → main cesse d'être l'objectif — irréaliste en temps, dit
  explicitement. Le fork est le **véhicule du PoC** ; on avance au maximum quand même. Le
  registre des écarts change de titre sans changer de contenu : de plan de réconciliation à
  **spécification documentée** de ce que main devrait apprendre du fork. La discipline du
  filet ne bouge pas : elle protège désormais le PoC pour lui-même.
- **D55** : aucun accès Railway — le pipeline réaliste est **MCP local + Docker local de
  Thomas**. Les livrables d'hébergement deviennent des artefacts exécutables chez lui
  (docker-compose Postgres + MCP, migrations dont `contexte_marche` D52, runbook), et le
  dashboard admin D34/D52 se construira contre ce Docker.

La cible concrète reformulée : **un PoC fonctionnel de bout en bout** — pipeline d'extraction
(prouvé), rendu (chantier UI aux 4/5), référentiels + contexte sur Postgres local, dashboard
admin en artefact live, deux clients réels (INTERAGYR fait, Gronier en B-v).

---

## 2026-07-31 (19) — Le Gronier corrigé instruit (E1–E8), trois arbitrages, bloc 5 livré

Thomas a fourni le **Gronier corrigé** (archivé, 3ᵉ contrôle d'époque) avec la doctrine : la
structure INTERAGYR « met tout le monde d'accord », Gronier est hyperspécifique. Dépouillé en
E1–E8 (dossier UI §10). Trois arbitrages en séance :

- **D-UI-3 : « Profils adaptatifs »** — union A∪B/C au manifeste, colonne 100 % vide masquée.
  La tension E1 (le Gronier corrigé garde ses 10 colonnes avec « — ») est tranchée en faveur
  de l'adaptivité. Implémentation à venir (prochain bloc).
- **D-UI-9 : « garder les lignes et caviarder les valeurs aberrantes »** — résolution de la
  tension E2 (le Gronier corrigé supprimait les sous-tableaux ISIN ; or les +350 % venaient de
  perfs CALCULÉES sur données assureur manquantes). FAIT : borne ±100 % (`PERF_LIGNE_MAX_PCT`),
  la ligne reste, la perf aberrante s'affiche « — », ⚠ au run. Remède de fond nommé : Modified
  Dietz sur mouvements datés (lié au contrat de données de la courbe à sauts E7).
- **Quick wins « oui, les cinq »** — FAITS : E3 widget Arbitrages supprimé quand vide (plus de
  placeholder) ; E4 SRI porte son périmètre (« coté + non coté » / « portefeuille coté seul ») ;
  E5 MP « Perf % » → « % Contrat » (poids, discriminant) ; E6a poches ↳ indentées aux
  Disponibilités (si ≥ 2 poches liquides) ; E6b donut Partenaires agrégé par partenaire
  (parenthèse À CHIFFRE = contrat → fusion ; sans chiffre = mandat → distinct — testé sur les
  deux pièces).

**Défauts de la pièce consignés au README des contrôles** : écart 300 000 € donut vs
Historique (hérité, non corrigé) ; colonne Cible conservée contre D-UI-2 (suppression
maintenue) ; W2/W3 PE absents (la banque est en avance, D53 — ne pas régresser).

**D44 a mordu deux fois au rescellement — sur MES commentaires** : « Gronier » et une vraie
référence de contrat étaient entrés dans le paquet par les commentaires de code ; puis sur
l'exemple générique « AB123456 » lui-même (motif trop plausible). Dé-identifié en formes non
appariables. Le garde protège aussi contre la documentation.

Filet : golden 8/8, L3a 8/8, test_pnc OK, re-run INTERAGYR QC 9/9 déterministe (placeholder
Arbitrages disparu, SRI suffixés), paquet rescellé 134 fichiers.

Restent au chantier UI : **D-UI-3 implémentation** (profils adaptatifs — gros refactor),
**D-UI-8** (conventions), arbitrage 1c (page Détails PE), et les chantiers E7 (courbe à sauts
de flux — exige Valorisations+Mouvements datés, lien D50) et E6/dispo-poches côté données.

---

## 2026-07-31 (20) — Bloc 6 : les colonnes adaptatives vivent (D-UI-3 soldé)

Le gros refactor du chantier UI, plus court que craint parce que les DONNÉES portaient déjà
l'union : `_cmetrics` émettait `nant` et `gpct_ann` (à « — ») depuis toujours. Fait :

- `perf["cote_cols"]` — le jeu de colonnes est une DONNÉE calculée (union A∪B/C, 12
  candidates) ; `_col_vivante()` masque toute colonne dont toutes les cellules sont vides ;
  « Valeur » est pivot (toujours là) ; « Valeur projetée » reste sur `show_ps_corrige`.
- Template déclaratif (D28 honoré) : thead en boucle, cellules par macro `cote_cells` (gras
  du pivot et padding du dernier th dérivés), **sous-tableau ISIN dé-triplé** en macro unique
  `acc_lines_tbl`, colspan dérivé de la longueur du jeu.
- **Prouvé dans les deux sens** : INTERAGYR passe de 10 colonnes (dont 4 vides) à **6
  colonnes naturelles** — le point 4 de la revue du 30/07 est soldé — et fx_simple garde ses
  8 avec YTD vivants. Le jeu de chaque fixture est gravé au **golden** (`cote_cols`), diff de
  ré-enregistrement prouvé (8 fixtures inchangées sur les valeurs).

Filet : golden 8/8, L3a 8/8 à l'octet, test_pnc OK, re-run INTERAGYR QC 9/9 déterministe,
paquet rescellé 134 fichiers, selfcheck OK, N3 verte.

Le chantier UI n'a plus qu'un point ouvert de design : **D-UI-8** (conventions des chapeaux
bloc 00, libellés partenaires — quasi zéro code) et l'arbitrage 1c (page Détails PE). Les
chantiers de données (courbe à sauts E7, Modified Dietz D-UI-9, VL non cotées D51-3) suivent.

---

## 2026-07-31 (21) — Bloc 7 : D-UI-8 soldé, et une leçon de livraison

**D-UI-8 arbitré et fait** : les chapeaux du bloc 00 disent « Reporting au [date] » (les trois
conventions d'époque sont mortes), et la forme du STORE fait foi pour les libellés partenaires
(« UBS (Dauphine AM — …) », plus esthétique aux yeux de Thomas — zéro code, convention
consignée).

**La leçon** : Thomas a vu 10 colonnes dont 4 vides là où j'annonçais 6 — le rendu D-UI-3
n'avait JAMAIS été livré. La commande composée du bloc 6 avait expiré APRÈS la copie du golden
mais AVANT celle du rendu, et j'avais « vérifié » la livraison à la taille du fichier (102 ko ≈
102 ko) au lieu du contenu. Règle prise : **une livraison se vérifie au CONTENU du fichier
livré** (thead extrait, chapeau grep-é), jamais à sa taille ni au succès apparent d'un cp.
OneDrive était innocent (tué depuis un mois côté Thomas).

Filet : golden 8/8, L3a 8/8, re-run QC 9/9, rendu livré et vérifié au contenu (6 colonnes,
chapeau daté), paquet rescellé 134 fichiers.

**LE CHANTIER UI EST SOLDÉ — 8 décisions sur 8** (D-UI-1/D53, 2, 3, 5, 6, 7, 8, 9). Reste
ouvert : arbitrage 1c (page Détails PE), et les chantiers de DONNÉES nés du chantier :
courbe à sauts de flux (E7), Modified Dietz lignes (D-UI-9), VL non cotées (D51-3),
Disponibilités par poche côté données. Prochains fronts : canal éditorial, D50 arrêtés,
B-v Gronier, dashboard admin sur Docker local (D55).

---

## 2026-07-31 (22) — Le dashboard admin VIT : artefact live validé en conditions réelles (D34/D52/D55/D56)

Premier front post-chantier-UI, choisi par Thomas pour « valider le pipeline de validation +
le concept d'artefact live comme dashboard ». Fait dans l'heure, MCP local vivant :

- **Sondé avant de construire** : formes réelles de `ref_adjudications` (répartition incluse),
  `ref_bundle` (compte des 4 tables — 17 acteurs / 2 successions / 9 gabarits / 261 ISIN).
- **Pipeline validé de bout en bout DEPUIS la surface admin** : proposition de démo déposée
  par `ref_propose` → visible en file dans l'artefact → **rejetée par Thomas depuis le
  dashboard** (13:36:28 UTC, tracée au Postgres, 7 rejetées / 1 acceptée / 0 en attente).
  Constat au passage : le garde du commentaire obligatoire ne juge pas le TEXTE (« Lorem
  ipsum dolor » passe) — tracé qui/quand mécanique, pourquoi sous responsabilité de l'arbitre.
- **L'artefact** (`referentiels-admin-dashboard`) : compteurs du canonique, onglets par statut,
  cartes avec clé/proposition/motif/provenance D44 (absences DITES), arbitrage avec
  commentaire obligatoire et confirmation d'écriture canonique, **heure de dernière lecture**
  affichée avec l'avertissement « pas du temps réel » (D34/RUNBOOK §0).
- **Sémantique de visibilité posée en séance** (question de Thomas sur le remote futur) :
  aujourd'hui local = surface admin par construction ; demain remote = les CGP n'atteignent
  que `ref_bundle` + `ref_propose`, l'arbitrage et le contexte D52 restent admin-only, les
  stores clients ne transitent jamais (D33/D35/D36) ; seul chantier neuf au portage : l'auth.
- **D56 (gouvernance, point de Thomas)** : la source versionnée fait foi —
  `dashboard/dashboard_admin_artifact.html` + `dashboard/README.md` (règles, garde-fous à
  préserver dans tout portage) ; l'artefact Cowork n'est qu'un déploiement.

Verdict de Thomas : « le rendu est très satisfaisant ». Prochains fronts dans l'ordre proposé :
**contexte de marché T3-26** (dernier bloc vide du reporting), spec courte du canal éditorial,
B-v Gronier (dès dépôt des pièces), D50 arrêtés.

---

## À faire ensuite

> Réécrit le 2026-07-29 au soir, après la CDC v5. La brique « producteur de propositions » de la
> version précédente de ce bloc est **faite** (entrée 12) ; la boucle référentiels est refermée et le
> test de réussite exécutable, à un hébergement près (D43).

**Le chantier L est FAIT** (① à ⑤, coupure différée avec prérequis nommés) et **le chantier B a
son premier run réel VALIDÉ** : INTERAGYR de bout en bout, corrigé après deux passes de revue de
Thomas contre le contrôle d'époque (QC 9/9 dont traversée, SRI du contrôle retrouvé par la
mécanique, enveloppes justes, 11 min vs 25).

**Chantier UI : blocs 1–4 FAITS le 31/07** (dossier `docs/chantier_ui_design_2026-07-31.md`,
JOURNAL 14–17) : canvas PE rétabli (**D53**, renversement arbitré + provenance « au coût »),
courbe coté 2 points (D-UI-7, fixture + clé golden), colonne cible/chapeau/durée (D-UI-2),
Monétaire/Liquidités + enveloppe bruyante (D-UI-5/6, l'AV est nommée). **Reste du chantier :
D-UI-3, les colonnes adaptatives** — le gros refactor déclaratif des blocs 02/03 (modèle :
mécanisme d'`exhaustif`), deux arbitrages ouverts (masquage mécanique vs seuils métier ; union
A∪B/C vs B/C) — puis **D-UI-8** (chapeaux bloc 00, libellés partenaires) et l'arbitrage 1c
(page « Détails » PE). Le double donut existait déjà (2b clos sans template).

**En parallèle / ensuite, par ordre d'utilité :**

- **Canal éditorial** (commentaire de gestion + ACTUALITÉS Dauphine captées) — spec courte.
- **Dashboard admin (D34/B5)** — backlog enrichi : arbitrage des propositions, heure de dernière
  lecture, et **D52 : drag & drop « update contexte de marché »** (admin-only, table par période
  côté référentiels — les CGP n'écrivent jamais le contexte).
- **SRI du référentiel ISIN** : colonne vide sur 261 lignes — chantier de DONNÉE (DIC/PRIIPs).
- **B-v** : réconciliation batchée + run Gronier (complexité croissante) — le contrôle d'époque
  est déjà archivé. Puis les questions CGP pendantes (K7, Himalia, Wealins).
- **Hébergement D55** (amende D43) : **Docker local de Thomas**, pas Railway (aucun accès).
  Livrables à produire : docker-compose (Postgres + MCP référentiels), migrations (dont
  `contexte_marche`, D52), runbook — Thomas exécute chez lui.
- Structure : colonnes « Dernière VL / Date de VL » (PE, D51 étage 3) + AskUser « fonds PE sans
  document » au lot batché.
- **La 8ᵉ fixture Historique** (validée par Thomas) : couvre les lignes annuelles du tableau de
  supervision, aujourd'hui en production sans aucun test. Déplace le golden.
- **INTERAGYR comme second client réel** : `Reporting_INTERAGYR_v4.xlsx` existe dans la session Gronier —
  en tirer un store rendrait A9 ordonnançable et donnerait un second point de comparaison à L3b.
- ~~Hébergement (D43) : Railway~~ — **remplacé par D55** (Docker local, cf. ci-dessus).
- **Dashboard admin en artefact live (D34 / B5)** — rappelé par Thomas le 2026-07-29. La file
  d'adjudication a besoin d'une surface où l'admin voit les propositions, arbitre, et suit les drifts.
  C'est un live artifact (il lit le MCP, écrit via `ref_arbitrer`), et il devra **afficher l'heure de sa
  dernière lecture** plutôt que se faire passer pour du temps réel (cf. RUNBOOK §0, le cache des
  artefacts). Le producteur de propositions ci-dessus est son fournisseur amont : il n'a de sens qu'une
  fois qu'il y a des propositions à afficher.

**Questions au CGP en attente** (ne bloquent que la canonisation des acteurs concernés) : K7
(Thaler/Indosuez), émetteur HIMALIA, dates d'effet Wealins.
