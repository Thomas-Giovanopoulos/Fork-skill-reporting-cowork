# Le reporting consolidé avec Claude — guide du conseiller

> Rhétorès Finance · version du 31 juillet 2026 · à destination des CGP
> Ce guide explique simplement comment produire un reporting patrimonial consolidé pour un
> client à partir de ses relevés. Aucune connaissance technique n'est nécessaire.

## C'est quoi ?

Un assistant qui fabrique le **reporting patrimonial consolidé** d'un client — le document HTML
avec le contexte de marché, les indicateurs, les graphiques d'allocation, le détail par contrat
et le suivi du non coté — à partir de deux choses que vous lui donnez : les **relevés officiels**
du client et votre **Excel de structure**. Il lit, vérifie, assemble, se contrôle, et vous pose
des questions quand quelque chose n'est pas clair. Il ne devine jamais à votre place.

## Ce qu'il vous faut avant de commencer

1. **L'Excel de structure du client** — la liste de ses contrats et investissements (un modèle
   vierge est fourni avec l'outil si c'est un nouveau client).
2. **Les relevés officiels en PDF** — relevés bancaires, situations de contrats d'assurance-vie
   ou de capitalisation, relevés de mandats. Les vrais documents des établissements, pas des
   récapitulatifs maison.
3. Dix minutes de disponibilité vers la fin : c'est là qu'il vous posera ses questions.

## Comment lancer

Ouvrez une conversation avec Claude, déposez vos fichiers (l'Excel + les PDF), et écrivez
simplement quelque chose comme :

> « Prépare le reporting consolidé de [Client] au [date d'arrêté] avec ces documents. »

C'est tout. Le reste se déroule tout seul, et dure en général une dizaine de minutes.

## Ce qui se passe pendant qu'il travaille

- Il **identifie chaque document** : quel établissement, quel type de relevé. S'il ne reconnaît
  pas un document, il vous le dira au lieu de faire semblant.
- Il **lit chaque relevé et se vérifie contre les totaux imprimés** dessus : si sa lecture ne
  retombe pas sur le total du document, il recommence ou vous le signale.
- Il **assemble** le tout dans le reporting, puis passe une batterie de contrôles comptables
  (les totaux doivent se recouper entre eux, ligne à ligne, contrat par contrat).
- Un reporting qui ne passe pas ses contrôles **ne vous est pas livré** — c'est voulu.

## Les questions qu'il vous posera

Elles arrivent groupées, en une fois, vers la fin. Typiquement :

- **Un écart** entre un relevé et votre Excel de structure → il vous montre les deux valeurs et
  vous demande laquelle fait foi. Il ne corrige jamais en silence.
- **Une donnée absente** — par exemple la valeur d'un fonds de private equity sans document
  récent → il vous demande la dernière valeur connue, ou votre accord pour afficher le montant
  investi « au coût » (et le reporting le dira explicitement).
- **Un établissement ou un document inconnu** → il vous demande de le nommer.

Répondez simplement ; vos réponses sont retenues pour les fois suivantes.

## Ce que vous recevez

- **Le reporting HTML** — le document à présenter au client. Il s'ouvre dans n'importe quel
  navigateur et s'imprime proprement.
- Sur demande, le **dossier complet du run** : tout ce qui a servi à produire le reporting,
  archivé et rejouable (utile en cas de question ultérieure).

Le reporting s'adapte de lui-même au client : un nouveau client sans historique n'aura pas de
colonnes vides « performance depuis l'origine », un client suivi depuis des années aura tout.
Quand une valeur est estimée plutôt que constatée, **le document le dit** (« au coût »,
« courbe simplifiée ») — jamais une estimation déguisée en certitude.

## Les bons documents à donner (et ceux à éviter)

| Donnez | Évitez |
|---|---|
| Relevés et situations **officiels** des établissements | Récapitulatifs faits main, captures d'écran |
| Pour le private equity : la **situation d'associé** (1-2 pages) ou les **avis d'appel/distribution** | Le rapport trimestriel de 80 pages du fonds |
| Des PDF nets, texte lisible | Scans penchés ou photos — si c'est illisible, il vous le dira |

## Ce que l'outil ne fera jamais

- Inventer une valeur manquante, ou en corriger une en silence.
- Faire passer un montant investi pour une valorisation.
- Livrer un reporting dont les contrôles comptables échouent.
- Modifier les référentiels partagés du cabinet de sa propre initiative : quand il découvre un
  nouvel établissement ou un nouveau type de document, il en fait la **proposition**, et c'est
  l'administrateur qui valide.

## Si quelque chose cloche

- **« Le paquet installé est corrompu » au démarrage** → réinstallez le skill (ou relancez
  l'application). N'essayez pas de réparer à la main.
- **« Référentiels lus depuis le snapshot embarqué »** → l'outil a travaillé avec sa copie
  locale car le service partagé n'était pas joignable. Le reporting est valable ; mentionnez-le
  simplement à l'administrateur pour que les dernières validations vous parviennent.
- **Une valeur du reporting vous semble fausse** → dites-le dans la conversation : il vous
  montrera d'où elle vient (quel document, quelle page) et corrigera avec vous.

## Confidentialité

Les documents de vos clients restent dans votre environnement de travail. Ce qui remonte au
cabinet quand vous validez un nouveau type de document, ce sont des **modèles anonymisés** —
jamais un nom de client, jamais un numéro de contrat, jamais un fichier client.
