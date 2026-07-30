# Filet A — appariement d'un document à son profil de gabarit

> Le filet qui manquait. Motif : la limite **L8** — les 7 fixtures de régression exercent le *rendu*
> (`p2_fill`), alors que signatures et pièges de parsing pilotent l'*extraction*. Tout ce que l'étude
> de corpus a établi était donc invérifiable jusqu'ici.
>
> Développé **hors de `skill/`** à dessein, pour ne pas régénérer les checksums à chaque itération.
> À promouvoir dans `skill/pipeline/` une fois la forme stabilisée.

## Pourquoi deux filets et non un

« Tester l'extraction » recouvre deux choses de nature opposée. Les confondre condamne soit à des
tests fragiles — comparer du texte produit par un LLM —, soit à n'en écrire aucun. C'est
vraisemblablement pourquoi il n'y en avait pas.

| | Objet | Nature | Assertion |
|---|---|---|---|
| **Filet A** *(ici)* | l'**appariement** document → profil | **déterministe** : du code sur du texte | **égalité exacte** |
| Filet B *(à venir)* | la **qualité de l'extraction** des valeurs | un subagent lit le document | invariants tolérants : `invariant_controle`, présence des champs de `champs_publies` |

## Contenu

| Fichier | Rôle |
|---|---|
| `matcher_gabarit.py` | l'algorithme. Lit un PDF, rend `(emetteur_code, gabarit, valide_depuis)` ou un verdict `ambigu` / `aucun` / `illisible` |
| `profils_corpus.json` | les **9 profils** à la forme cible, ancres extraites des études et vérifiées sur les PDF |
| `harnais_appariement.py` | rejoue les 37 documents contre la table de vérité |
| `test_discrimination.py` | contrôles **négatifs** — ce que le harnais ne peut pas prouver |

## Lancer

```bash
cd outils_appariement
python3 harnais_appariement.py                                   # tout le corpus
python3 harnais_appariement.py cardif wealins                    # par émetteur (limite de 45 s)
python3 harnais_appariement.py himalia_emetteur_a_confirmer      # ⚠ le code complet, pas « himalia »
python3 test_discrimination.py                                   # les contrôles négatifs
```

## État vérifié au 2026-07-29

**32/32 appariés** (scores 0,95 à 1,00) **et 5 Nortia signalés**, non comptés parce que leur profil n'est
pas établi. **15 contrôles négatifs** au vert.

> *Formulation corrigée le 29/07 : ce README annonçait « 37/37 » et « 12/12 ». C'était flatteur par
> arrondi — 37 est le nombre de documents du corpus, pas le nombre d'appariements vérifiés, et les
> 5 Nortia sont hors décompte par construction. Un compte rendu qui embellit de 5 unités est un compte
> rendu qu'on cessera de croire.*

Le contrôle qui compte est le premier de `test_discrimination.py`, et il corrige une faiblesse de la
première démonstration. Sur le Cardif de 2024, le profil v2 est écarté par sa **fenêtre de validité** :
le verdict est juste, mais c'est la date qui travaille, pas la signature. Or dans un run réel l'arrêté
peut manquer. Rejoué **sans date**, les deux fenêtres éligibles, les signatures suffisent : 2024 → v1,
2025 → v2, sans ambiguïté. C'est la différence entre « le test passe » et « le test prouve quelque
chose ».

Le dernier contrôle vise le biais symétrique : un document quelconque ne doit **pas** être apparié de
force, sans quoi un matcher répondant toujours « oui » passerait tout le reste.

## Quatre écarts avec l'étude d'origine, chacun motivé par une observation

**1 — La couche 1 ne peut que restreindre, jamais décider.** Chez Cardif, `Producer` et `Creator` sont
identiques de part et d'autre d'une refonte à laquelle une seule ancre sur onze survit ; et
`TYPE_MODELE=66` vaut la même chose avant et après. La couche 1 est un **pré-filtre d'émetteur** — les
deux profils Cardif ont donc, à dessein, une `couche1` **identique**.

**2 — Les polices discriminent les émetteurs, pas les gabarits.** Elles séparent parfaitement les deux
Cardif mais sont identiques sur les cinq Himalia. Le résultat Cardif ne se généralise pas.

**3 — Sections requises et optionnelles sont deux choses.** Les requises sont une **barrière** (toutes
présentes ou rejet), les optionnelles n'ajoutent que de la confiance. Sans cette distinction, un
gabarit à géométrie variable se fait passer pour plusieurs — et on versionne pour rien. Confirmé
indépendamment sur trois émetteurs : `PRM` chez Spirica, `Fonds Euro` chez Himalia (3 documents sur 5
ne l'ont pas), `Arbitrages` chez Wealins (1 sur 7).

**4 — La version se choisit par date d'arrêté, pas par périodicité** (D42). La périodicité n'est pas
lisible dans le document chez trois émetteurs sur quatre : elle ne peut pas servir au matching.

Et un acquis confirmé : **le nombre de pages reste hors matching.** Dauphine va de 3 à 6 pages,
Wealins de 15 à 26, pour le même gabarit.

## Une règle de conduite plutôt qu'un algorithme

**L'ambiguïté est signalée, jamais tranchée en silence.** La frontière entre « variante » et « nouveau
gabarit » est un jugement (limite L3) : aucun critère formel ne la trace. Deux profils à moins de 0,15
d'écart rendent un verdict `ambigu`, à porter en adjudication. Un matcher qui devine à la place de
l'humain fabrique des erreurs invisibles.

## Pièges rencontrés, à ne pas redécouvrir

- **`^INFORMATION\s+ANNUELLE\s*:` ne matche rien.** `pdftotext -layout` **indente** l'en-tête
  d'annexe : il faut `^\s*INFORMATION…`. Discriminant Wealins, 3/3 contre 0/4 dans un sens, 0/4 contre
  4/4 dans l'autre.
- **`Fonds Euro` matche 5/5 en sous-chaîne** chez Himalia, à cause d'une note « ( ex fonds euros) » —
  piège absent de l'étude d'origine. En regex ancrée `^\s*Fonds Euro\s*$` : 2/5, donc optionnelle.
- **L'apostrophe typographique U+2019** casse `Type d'Actifs`, `Information sur l'évolution du contrat`
  et la clause « En cas de divergence avec l'estimation… ». Toutes reprises en `['’]`.
- **`Prix moyen d'acquisition (PMA)` n'existe pas** dans le texte Nortia : l'en-tête est coupé sur
  trois lignes entrelacées. Scindé en `Prix moyen` + `(PMA)`.
- **Trois fichiers portent un nom mojibake** (accent combinant UTF-8 relu en CP437). Aucune
  normalisation Unicode ne les réconcilie — le harnais prend le nom **tel quel** dans la table de
  vérité, jamais reconstruit.

## Ce que ces résultats ne prouvent PAS

- **Rien sur la stabilité dans le temps chez Spirica** : ses 12 documents sont des rééditions du
  24/07/2026. Le harnais le rappelle dans son verdict, pour qu'on ne lise pas « 12/12 » comme une
  preuve de stabilité sur quatre ans.
- **Nortia n'est pas validé** : profil `a_etablir`, couche 1 vide (aucune métadonnée PDF), ancres
  reprises de l'étude d'origine sur un seul document.
- **Cardif v1 et de_pury_pictet reposent chacun sur UN seul document.** Une ancre qui s'y révélerait
  propre à ce document et non au gabarit ne se verrait pas ici.
- Plusieurs ancres sont classées **optionnelles par prudence** malgré 100 % d'occurrence observée
  (`Garanties au terme du contrat` chez Cardif v2, 3/3) : le corpus ne permet pas de trancher entre
  « propre à la version » et « bloc conditionnel ».
