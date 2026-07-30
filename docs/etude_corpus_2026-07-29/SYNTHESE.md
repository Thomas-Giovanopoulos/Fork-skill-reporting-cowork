# Synthèse — extension du corpus au 2026-07-29

> Prolonge `docs/etude_signature_gabarits_2026-07-27.md`, qui portait sur **11 relevés** examinés à un
> instant donné. Cette extension ajoute **34 documents** couvrant quatre émetteurs sur **quatre ans**, et
> ouvre donc l'axe que l'étude d'origine ne pouvait pas voir : la **dérive dans le temps**.
>
> Quatre séries analysées en parallèle, une par émetteur — le regroupement est délibéré : la dérive ne se
> lit pas document par document, elle se lit en série chronologique. Détail dans `spirica_uaf_cerise.md`,
> `cardif.md`, `wealins.md`, `himalia.md`.

---

## 0 — Le corpus se scinde en deux, et il faut le savoir avant de lire quoi que ce soit

`pdfinfo` sur les 34 documents révèle que **la moitié sont des rééditions du 24/07/2026** — regénérées
depuis le système actuel de l'émetteur, avec l'arrêté d'époque mais le générateur d'aujourd'hui.

| | Rééditions du 24/07/2026 | Originaux exploitables |
|---|---|---|
| Spirica / UAF (Cerise + Pollux) | **12 sur 12** | aucun |
| Himalia | 3 | **2** (28/01/2025, 05/03/2026) |
| Cardif | 2 | **2** (28/01/2025, 23/01/2026) |
| Wealins | 0 | **7** |
| Nortia | — (aucune métadonnée) | 5, à qualifier |

**Conséquence méthodologique** : sur la série Spirica, toute dérive de générateur est **structurellement
invisible** — six PDF produits en quatre minutes le même jour ne peuvent pas témoigner de quatre ans
d'évolution. C'est un piège qui aurait pu passer pour un résultat (« aucune dérive chez Spirica ») et qui
n'est qu'un artefact de collecte. Il a été identifié avant de lancer les autres analyses, ce qui a permis
de les cibler sur les originaux.

**Ce qu'il faudrait pour compléter** : les PDF **d'archive** de Spirica, tels que reçus à l'époque.

---

## 1 — Le résultat principal : la dérive existe, et son amplitude varie du tout au rien

C'est le fait le plus important de cette extension, et il interdit toute règle globale.

| Émetteur | Écart | Amplitude de la dérive | Ancres survivantes |
|---|---|---|---|
| **Cardif** | 12 mois | **rupture** — polices, casse, nombre de colonnes, unité (`euros` → `€`), pagination apparue, section `Garanties au terme` ajoutée | **1 sur 11** |
| **Wealins** | 12 mois | mineure — un titre enrichi (« à la performance nette de frais »), une phrase supprimée | quasi toutes |
| **Himalia** | 13 mois | **nulle** — page 1 identique à l'octet hors date d'arrêté et montant ; coordonnées `bbox` des en-têtes identiques **au centième de point** | **30 sur 30** |
| Spirica | 4 ans | indéterminable (cf. §0) | — |

Deux conséquences qui se contredisent en apparence :

- **Un profil unique par émetteur ne suffit pas** : le profil B.7 tel qu'écrit **n'apparierait pas** le
  relevé Cardif de 2024. Il faut pouvoir versionner.
- **Versionner systématiquement serait une faute** : chez Himalia, cela fragmenterait en plusieurs
  profils un gabarit rigoureusement identique — du bruit pur, et autant d'adjudications inutiles.

**Donc le versionnement doit être une capacité du schéma, jamais une règle de conception.** Ce qui le
déclenche n'est pas une décision prise à l'avance mais la **détection d'un drift au runtime** — c'est-à-dire
le self-healing (jalon A5, N4/N5). Autrement dit : O15 ne se règle pas dans le DDL seul, il se règle dans
le DDL **plus** la boucle d'apprentissage. Un profil non versionné n'est pas un profil incomplet, c'est un
émetteur stable.

---

## 2 — Trois croyances de l'étude d'origine sont réfutées

### 2.1 — L'ID de template natif ne versionne pas le gabarit

Cardif expose `TYPE_MODELE=66`, présenté en A.4-1 comme une « signature parfaite » court-circuitant le
matching en couches. **Il vaut 66 avant et après la refonte de 2025** — donc à travers un changement de
gabarit si profond qu'une seule ancre sur onze y survit.

`TYPE_MODELE` identifie une **famille de document**, pas un gabarit. C'est un excellent **pré-filtre**, et
un raccourci trompeur. À reclasser comme tel dans R4 et dans le profil B.7.

### 2.2 — La périodicité n'est pas lisible dans le document — et cela touche la clé d'unicité

Quatre émetteurs, quatre échecs ou faux amis, un seul cas fiable :

| Émetteur | Token candidat | Verdict |
|---|---|---|
| Spirica | « trimestriels » | **faux ami** — désigne une offre commerciale, identique sur des arrêtés annuels |
| Cardif | « pour l'année » | **faux ami** — fenêtre de cumul YTD, inchangée sur des arrêtés au 30/03 et au 30/06 |
| Himalia | « 8 années » | **faux ami** — durée du contrat. Aucun token de périodicité, nulle part |
| Wealins | `^INFORMATION\s+(ANNUELLE\|TRIMESTRIELLE)\s*:` en en-tête d'annexe | **fiable** — label de nature, sur 100 % des pages d'annexe |

L'affirmation d'origine — « périodicité discriminée par un token de libellé » — **ne se généralise pas** :
elle tient chez un émetteur sur quatre.

**Et la conséquence dépasse la documentation.** La table `gabarits` est unique sur
`(emetteur_code, gabarit, periodicite)` (R4, DDL §5). Si la périodicité n'est pas déterminable à la lecture
du document dans trois cas sur quatre, alors **elle ne peut pas faire partie de la clé d'appariement** —
au mieux d'une clé de stockage renseignée par ailleurs (date d'arrêté, contexte du run, saisie du CGP).
C'est un point à trancher **avant le premier `INSERT`**, et il rejoint O15 par un autre chemin que celui
qu'on avait identifié.

### 2.3 — Les polices discriminent les émetteurs, pas les gabarits

Chez Cardif, la liste des polices sépare parfaitement deux gabarits que `Producer` et `Creator` ne
séparaient pas — d'où l'idée d'une « couche 1bis ». Mais chez Himalia elle est identique sur les cinq
documents : `{Helvetica, Helvetica-Bold}` partout. **Le résultat Cardif ne se généralise pas.**

En revanche, au niveau **émetteur**, les polices sont discriminantes et utiles : Spirica vaut
`{Times-Roman, Helvetica, Times-Bold}` / OpenPDF / PDF 1.5, Himalia `{Helvetica, Helvetica-Bold}` /
iText 2.1.7 / PDF 1.4. Et la collision « JasperReports apparaît aussi chez Spirica », signalée comme
piège en B.5, **tombe** : c'est une collision de *mot*, pas de *chaîne* — le `Creator` complet diffère.

---

## 3 — Le correctif de schéma le plus rentable : sections requises vs optionnelles

Confirmé indépendamment sur **trois émetteurs sur quatre** :

- **Spirica** — la section `PRM` est absente au 31/12/2022 (aucune UC ce jour-là) et présente ensuite ;
  `DÉTAIL DES OPÉRATIONS` apparaît en 2026.03. Trois « configurations » qui ressemblaient à trois
  gabarits n'en sont qu'un.
- **Himalia** — la section `Fonds Euro` est absente de 3 documents sur 5.
- **Wealins** — `Arbitrages` n'apparaît que dans 1 document sur 7, `Aperçu des fonds` dans 3 sur 7
  (dès 2 FID).

Ces sections sont **pilotées par la donnée**, pas par le gabarit : elles apparaissent quand le portefeuille
les justifie. Or le profil déclare aujourd'hui une liste `sections_ordonnees` **à plat**. Un matcher qui
exige toutes les sections déclarées échoue sur un portefeuille plus simple ; un matcher qui n'en exige
aucune n'apparie plus rien.

**Correctif** : scinder en `sections_requises` et `sections_optionnelles`. C'est ce qui distingue un
gabarit à géométrie variable d'un nouveau gabarit — sans quoi on fabriquerait des profils versionnés pour
des portefeuilles qui évoluent, ce qui est précisément le bruit dont il faut se garder.

---

## 4 — Wealins : deux gabarits, et le nom de fichier se trompe une fois sur deux

Sept documents, trois intitulés commerciaux, **deux gabarits réels** :

- **G1 — information annuelle** : les 2 relevés annuels 2025 **et** `Information annuelle FC055211_31 12 24`
- **G2 — situation de contrat trimestrielle** : les 2 `Situation trimestrielle` **et** les 2 `FC…-20260630`

**Le nom de fichier se trompe 2 fois sur 4** sur les documents où il prétend dire quelque chose. Confirmation
éclatante de la décision A.1-3 de l'étude : l'identification se fait sur le contenu, **jamais** sur le nom.

Discriminant : le label d'en-tête d'annexe en capitales (§2.2 ci-dessus), doublé d'un marqueur structurel —
**4 blocs pour G1** (avec la page Loi Pacte) contre **3 pour G2**.

### Et les sous-templates ne circulent pas en autonomie

C'était l'hypothèse à tester, et elle est **réfutée**. `Information annuelle FC055211_31 12 24.pdf` n'est
pas le sous-template n°2 extrait seul : c'est le composite complet à 4 blocs, 11 pages. **7 documents sur 7
sont composites.**

Conséquence directe : **un profil composite unique à segmentation interne**, et non un profil par enfant.
C'est la forme retenue par **R7 dans sa rédaction d'origine** — la « résolution » proposée le 28/07
(« sous-templates déclarés comme enfants de plein droit ») est infirmée par la donnée. Les segments restent
des segments ; ils ne sont pas des documents.

Trois corrections à B.6 par la même occasion : le « pied de page au numéro de fax différent sur la page Loi
Pacte », interprété comme la preuve d'un générateur distinct, est en réalité le **fossile d'un changement de
numéro non propagé** (en janvier 2025, toutes les pages portaient le même) ; `Arbitrages` et `Aperçu des
fonds` doivent être rétrogradées en ancres conditionnelles ; et « double pagination » sous-estime — il y a
3 ou 4 blocs paginés.

---

## 5 — Ce que le corpus dit de D38 (« un assureur peut avoir 50 templates »)

La prémisse **n'est pas observée** : le maximum constaté est de **deux gabarits par émetteur**, et jamais
cinquante. Mais la décision reste juste, pour une raison différente de celle invoquée :

- **la variété simultanée est faible** — Wealins expose 2 gabarits, les autres 1 ;
- **la variété temporelle est réelle** — Cardif a produit un second gabarit en douze mois.

Autrement dit, ce qui fait grossir le catalogue n'est pas la largeur de l'offre d'un assureur mais le
**temps**. La conclusion pratique est la même — il faut pouvoir en héberger beaucoup, et le self-healing les
fait arriver un par un — mais le mécanisme est autre, et cela change ce qu'on doit surveiller : non pas
« a-t-on tous les templates de cet assureur ? » mais « ce template a-t-il bougé depuis le dernier run ? ».

---

## 6 — Les limites du système, telles que ce corpus les révèle

Le corpus n'a pas seulement produit des empreintes : il a délimité ce que l'approche par signature **peut**
et **ne peut pas** faire. Ces limites-là sont l'apport le plus durable de l'étude, parce qu'une empreinte
se refait et qu'une limite mal comprise se paie longtemps. Elles sont classées ci-dessous en **inhérentes**
(à contourner par conception) et **réductibles** (à traiter).

> **Renumérotées de `L1`…`L8` en `LIM1`…`LIM8` le 2026-07-29.** Le préfixe `L` désignait déjà le **chantier L**
> du CDC et de la roadmap — les cinq tâches `L1`–`L5` du lecteur de forme-store. « L2 » valait donc à la
> fois « le store ne peut pas être exhaustif » et « écrire le lecteur », et « L5 » à la fois « les
> profils ne pourront pas être supprimés » et « chaque extension est livrée lecteur d'abord ». Une
> collision de préfixe rend la référence ambiguë sans qu'on puisse le détecter à la lecture. Les numéros
> sont conservés, seul le préfixe change ; les `L1`–`L5` du chantier restent inchangés.

### Inhérentes — aucune version du système ne les lèvera

**LIM1 — Un document ne dit pas ce qu'il est.** C'est la limite la plus profonde, et elle contredit une
prémisse du dispositif. La périodicité n'est inscrite nulle part chez trois émetteurs sur quatre, et les
tokens qui semblent la dire sont des faux amis (offre commerciale, fenêtre de cumul, durée de contrat).
Or la décision A.1-3 pose que l'identification se fait « sur le contenu, **jamais** sur le nom de
fichier ». Pour la périodicité, le contenu est **muet** — et le contexte (date d'arrêté, run, saisie du
CGP) est tout ce qui reste. Il faut donc admettre que l'identification est **mixte** : le gabarit vient du
contenu, la périodicité vient d'ailleurs. Le nier conduirait à chercher indéfiniment un token qui n'existe
pas.

**LIM2 — Le store ne peut pas être exhaustif, par construction.** Il n'apprend que des documents qui passent
la porte d'un CGP. La question « avons-nous tous les gabarits de cet assureur ? » est donc **sans réponse
possible** — et c'est pourquoi la seule question tractable est temporelle : « celui-ci a-t-il bougé depuis
le dernier run ? ». Corollaire pratique : aucun indicateur de couverture ne sera jamais honnête. Mieux vaut
ne pas en construire que d'en afficher un faux.

**LIM3 — La frontière entre « variante » et « nouveau gabarit » est un jugement, pas un calcul.** Chez
Spirica, trois configurations de sections ne font qu'un gabarit ; chez Cardif, un changement de polices et
de colonnes en fait deux. Entre les deux, il n'existe **aucun critère formel** — seulement un seuil, et
tout seuil est arbitraire. Le système devra donc trancher par **délégation** : détecter, proposer, et laisser
l'humain décider. C'est précisément la raison d'être de la file d'adjudication, et cela mérite d'être dit
comme un choix assumé plutôt que subi.

**LIM4 — Un détecteur de drift ne sait pas si un changement est bénin ou cassant.** Wealins a déplacé une
ancre, Cardif en a cassé dix sur onze. Un détecteur voit « des ancres ont bougé » dans les deux cas. La
gravité n'est lisible qu'après coup, en regardant si l'extraction a échoué — donc trop tard pour
l'empêcher. Conséquence : le drift ne doit **jamais** déclencher une correction automatique, seulement une
proposition. Contourné par conception (D34), pas résolu.

**LIM5 — Les profils ne pourront pas être supprimés.** Le run Gronier lit des relevés remontant à **2022**.
Si les gabarits sont versionnés à mesure que les émetteurs changent de maquette, les anciens profils
doivent **rester vivants** pour rester capables de lire les archives. Le store croît donc de façon
monotone, et rien n'y est jamais périmé — seulement inactif. Personne ne l'avait prévu, et cela change ce
qu'on attend d'une « fenêtre de validité » : elle sert à choisir, pas à retirer.

### Réductibles — à traiter

**LIM6 — La couche 1 (métadonnées) porte beaucoup moins qu'annoncé.** Elle ne discrimine pas les gabarits
(Cardif : `Producer` et `Creator` identiques de part et d'autre d'une rupture), l'ID de template natif ne
versionne pas, et les polices discriminent les émetteurs sans discriminer les gabarits. L'identification
repose donc **presque entièrement sur les couches 2 et 3** — une base plus étroite que la conception ne le
supposait. À corriger dans la pondération : la couche 1 est un **pré-filtre d'émetteur**, pas un élément de
signature de gabarit.

**LIM7 — Le corpus disponible est lui-même biaisé.** La moitié des PDF sont des rééditions récentes (§0), ce
qui rend la dérive de Spirica inconnaissable. Réductible : il suffit d'archiver les PDF **tels que reçus**.
À défaut, toute étude ultérieure butera sur le même mur, et pourra même conclure à tort à une stabilité.

**LIM8 — Et la plus importante : la partie du système que cette étude concerne n'a aucun filet.** Les 7
fixtures de régression exercent le **rendu** (`p2_fill`). Les signatures, les pièges de parsing et les
`extraction_hints` pilotent l'**extraction**, faite par des subagents. Rien ne teste ce chemin. Autrement
dit : tout ce que ce corpus établit est, aujourd'hui, **invérifiable par la régression** — un profil faux
ou un piège périmé ne se manifesterait qu'à la lecture du reporting produit. C'est la limite qui devrait
peser le plus sur l'ordre des travaux, et c'est déjà la raison pour laquelle la migration N3 a été
suspendue plutôt que faite à l'aveugle.

---

## 7 — Ce qui reste à établir

- **Nortia** : cinq documents, **aucune métadonnée PDF** — donc couche 1 vide. À qualifier, et à confirmer
  qu'il s'agit bien d'originaux : sans `CreationDate`, la distinction original / réédition du §0 n'est pas
  vérifiable par ce moyen.
- **Spirica sur archives réelles** : la dérive de cet émetteur reste inconnue.
- **`Positions Overview (1).xlsx`** : non analysé. À rapprocher de D40 (export O2S comme source
  documentaire) s'il s'agit d'un export de dépositaire.
- **La convention de nommage de `gabarit`** (O15) : le corpus donne enfin de quoi la formuler, mais elle
  n'est pas écrite. Elle doit répondre à trois cas maintenant documentés — deux gabarits simultanés
  (Wealins), deux gabarits successifs (Cardif), un gabarit stable sur treize mois (Himalia).
