# Spécification du tri — blocs, sous-sections et widgets

> **2026-07-27.** Réalise le livrable **J2** du CDC (« établir le tableau de faisabilité bloc par
> bloc »), étendu aux deux étages que la v4 ne couvrait pas. Arbitré en atelier (Thomas × Cowork).
> Amende le CDC v4 : décisions **D28–D31**, clôture **O8** et **T1**, élargit le chantier **J**.

---

## 1 — Le constat : trois étages de tri, un seul dans le manifeste

| Étage | Exemples | Gouverné aujourd'hui par | Dans le manifeste ? |
|---|---|---|---|
| **Bloc** | `historique`, `performance_nc` | `blocs_enabled`, littéral de dict dans `excel_to_manifest.py` | oui |
| **Sous-section** | « Fonds de private equity », « Titres non cotés » | `{% if pnc.detail %}` / `{% if pnc.detail_titres %}` | **non** |
| **Widget** | « Disponibilités par contrat », « Positions — Matières premières » | `{% if perf and (perf.dispo or perf.mp) %}` | **non** |

Le second mécanisme — **la truthiness d'une clé de données dans le template** — n'était pas documenté.
Il respecte D17 par accident (donnée absente → `None` → pas de rendu, jamais de squelette), mais :

- `store_to_manifest` (J) ne contrôlerait qu'**un tiers** du tri réel ;
- **l'intention est inexprimable** à ces étages : impossible de dire « la donnée est là, je ne veux pas
  l'afficher » — le défaut que §1.6 du CDC dénonce pour les blocs, reproduit un étage plus bas ;
- **aucune pertinence** : une ligne de matières premières à 0,1 % du patrimoine déclenche un tableau
  complet avec son chapeau.

**Décision D28** : le tri est à trois étages, et **les trois sont déclarés au manifeste**. Les
templates ne décident plus de ce qui s'affiche ; ils rendent ce qu'on leur déclare. Prolonge D12/D20
jusqu'au bout : le forme-store devient la source unique de *ce qui apparaît*, comme il l'est déjà de
*ce qui est écrit*.

---

## 2 — Étage 1 : les blocs

| Bloc | Nature | Règle d'apparition | Notes |
|---|---|---|---|
| `hero` | intention actée | toujours | identité client ; le `True` en dur devient explicite |
| `contexte` | intention + donnée externe | **store de période présent**, sinon désactivé | jamais de squelette (D17). Aucun logement au store → C6/O7 |
| `supervision` | faisabilité | valuations + classification présentes | porte le tableau *Historique du patrimoine* (≠ bloc `rendement_annuel`, cf. §5) |
| `performance` | faisabilité | ≥ 1 contrat coté avec lignes | hôte des widgets de l'étage 3 |
| `performance_nc` | faisabilité | ≥ 1 entrée `non_cote` — **jamais de seuil de pertinence** | titre et KPI **adaptatifs**, cf. §3. Voir D32 |
| `rendement_annuel` *(ex-`historique`)* | faisabilité | **≥ 2 points** d'historique | 1 seul point → candidat pertinence (§4), pas un tableau d'une ligne |
| `repartition` | intention (`mode`) | `mode != presentee` | inchangé |
| `exhaustif` | intention (`mode`) | `mode != presentee` | inchangé |
| `footer` | intention actée | toujours | |

**Décision D29a** : `rendement_annuel` est **automatique sur faisabilité** — si la donnée est là, il
s'affiche, sans question. (Réponse explicite de Thomas : « si la donnée est là afficher l'historique ».)

---

## 3 — Étage 2 : les sous-sections du non coté

Gating **data-driven propre**, dérivé de `attributes.instrument_type` (Fonds / Titre) :

| Sous-section | Règle |
|---|---|
| « Fonds de private equity — détail par véhicule » | ≥ 1 entrée `instrument_type = Fonds` |
| « Titres non cotés — détention directe ou via support » | ≥ 1 entrée `instrument_type = Titre` |

Ces deux règles sont de la **faisabilité pure** : automatiques, sans question.

**Défaut à corriger — le bloc peut s'afficher sans fonds.** `performance_nc` est gated par « une
entité a du non coté », mais les KPI **MOIC / TVPI sont recalculés sur les fonds seuls**. Un client
qui n'aurait que des titres (OCA, SOMNOO, co-investissements) verrait un bloc « performance non coté »
aux KPI vides. D'où deux règles d'adaptation :

- **KPI MOIC/TVPI rendus uniquement si la sous-section Fonds existe.** Sinon ils sont retirés, pas
  affichés à `—` (D17).
- **Titre du bloc adapté** quand une seule sous-section est présente, pour ne pas annoncer une
  grammaire (engagé/appelé/MOIC) qui ne s'applique pas.

---

## 4 — Étage 3 : les widgets, et la pertinence

### a. Disponibilités par contrat + Matières premières

**Contrainte de mise en page, actée** : les deux widgets partagent une rangée
(`grid-template-columns: 1fr 1fr` si les deux, `1fr` si une seule). Ils forment donc une **paire
liée** — une décision sur l'un affecte le rendu de l'autre. Le template gère déjà les deux cas ; c'est
la *question* qui doit être posée pour la paire, pas widget par widget.

**Décision D29b** : ces deux widgets relèvent de l'**intention**, pas de la faisabilité. Ils
**dupliquent** une information déjà présente au tableau exhaustif ; leur raison d'être est un focus
voulu. Ils ne s'affichent donc **jamais automatiquement** : la donnée présente en fait des
**candidats**, l'affichage est décidé par AskUser (§4c).

> Historique : `p2_fill` les commente comme « demandes client ». Nées client-spécifiques, elles
> étaient devenues de facto standard pour tout le monde dès que la donnée existait. D29b clôt cette
> dérive.

### b. Trois défauts à corriger dans le calcul des disponibilités

1. **`Court terme` est exclu à tort.** Le calcul retient `cls == "Monétaire"` ou un libellé préfixé
   liquid/compte courant/espèces/cash. Or `CLASS_COLORS` et les poids de tri traitent `"Court terme"`
   et `"Monétaire"` comme **équivalents** (même couleur `#D8C6A0`, même poids 1). Une ligne classée
   Court terme est donc du monétaire partout **sauf** dans les disponibilités.
2. **Le matching par préfixe de libellé est fragile** : « Trésorerie » n'est pas capté ; « Solde en
   espèces » non plus (le préfixe testé est `espèces`). Un libellé de relevé légèrement différent
   disparaît **silencieusement** du widget. À remplacer par une règle de classe, le libellé n'étant
   au mieux qu'un repli — et tout repli par libellé doit être **tracé**, pas silencieux.
3. **Définition à arrêter** : un fonds euros est-il une « disponibilité » ? Rachetable, mais pas du
   cash. Aujourd'hui exclu (implicitement). À expliciter dans la règle plutôt qu'à laisser au hasard
   du code.

### c. Le protocole d'AskUser de tri — un seul, batché, persisté

**Décision D30** : la pertinence et l'intention d'étage 3 passent par **une question unique et
groupée**, posée une fois au run, dont la **réponse est persistée**.

```
Au run, après l'apply et avant store_to_manifest :
  1. Calculer la FAISABILITÉ de tous les étages depuis le forme-store (déterministe).
  2. Constituer la liste des CANDIDATS :
       • la paire dispo/MP, si la donnée existe (D29b) ;
       • tout bloc faisable mais sous seuil de pertinence
         (ex. PE à faible part du patrimoine, rendement_annuel à 1 point,
          matières premières à part marginale).
  3. Si la liste est vide  → aucune question, on continue.
     Si elle est non vide  → UN SEUL AskUser, tous les candidats en une fois.
  4. PERSISTER les réponses dans le manifeste (`tri_decisions`), avec provenance
     et date, et les archiver au dossier de run (D4).
  5. Au run suivant du même client : les décisions persistées sont RÉUTILISÉES.
     Aucune nouvelle question, sauf candidat nouveau ou demande explicite de révision.
```

**Pourquoi la persistance est non négociable** : sans elle, deux runs du même client produisent des
reportings différents selon l'humeur du répondant. Avec elle, le tri devient une **donnée du run**,
reproductible et auditable — cohérent avec I1 (« toute évolution se définit d'abord comme une forme
dans le dict ») et avec l'objectif de rigidité. C'est aussi ce qui rend la question compatible avec le
full-auto en un seul run : on ne paie la pause qu'une fois par client.

**Ce que D30 clôt** : le point ouvert **O8** du CDC. Les seuils ne sont plus à coder en dur — ils
servent seulement à **déclencher la question**, pas à décider seuls. Un seuil mal réglé coûte alors
une question de trop, jamais un reporting faux.

---

## 5 — La collision de noms (T1), tranchée

**Décision D31** : `blocs_enabled.historique` est **renommé `rendement_annuel`** avant l'écriture de
`store_to_manifest`.

Rappel du piège : la clé `historique` désigne le bloc *Rendement annuel*, alors que le tableau
*Historique du patrimoine* vit dans le bloc `supervision`. Deux objets distincts, un seul mot —
quiconque écrit le mapping store→manifeste se tromperait naturellement. Le renommage est un prérequis
de J, pas un nettoyage cosmétique (déjà prévu en G3).

Portée du renommage : `BLOCK_ORDER` (`assemble.py`), `excel_to_manifest.py` (legacy),
`manifest.schema.json`, `manifest.example.json`, le template `blocs/historique.html.j2` et les
fixtures de régression. À faire d'un bloc, avec la régression 7/7 comme filet.

---

## 6 — Récapitulatif des décisions

| # | Décision |
|---|---|
| **D28** | Le tri est à **trois étages** (bloc / sous-section / widget) et les trois sont **déclarés au manifeste**. Les templates ne décident plus de ce qui s'affiche. J couvre 100 % du tri. |
| **D29a** | `rendement_annuel` est **automatique sur faisabilité** (≥ 2 points). Aucune question. |
| **D29b** | `dispo` et `matières premières` relèvent de l'**intention** : jamais automatiques, décidés par AskUser, et traités comme une **paire liée** (contrainte de mise en page : une rangée partagée). |
| **D30** | Pertinence et intention d'étage 3 → **un seul AskUser batché au run**, réponses **persistées au manifeste** (`tri_decisions`) et archivées au dossier de run. Réutilisées aux runs suivants. **Clôt O8.** |
| **D31** | `blocs_enabled.historique` → **`rendement_annuel`**, avant J. **Clôt T1.** |
| **D32** | **Le bloc PE n'a jamais de seuil de pertinence** : il s'affiche dès qu'il existe du non coté. Motif métier : le PE représente **peu d'actifs à forte importance individuelle**, et l'entrée en portefeuille suit souvent un événement où le client a été invité. La part du patrimoine est donc la **mauvaise métrique** pour ce bloc. |

### Seuils de déclenchement retenus (clôt O13)

| Candidat | Seuil | Statut |
|---|---|---|
| Bloc PE (`performance_nc`) | **aucun** — toujours affiché s'il existe | D32 |
| `rendement_annuel` | exactement **1 point** | D29a (≥ 2 = auto) |
| Matières premières | part **< 1 %** du patrimoine net OU une seule ligne | candidat |
| Disponibilités | **toujours candidat** | intention, D29b |

Garde-fous : les parts se calculent sur le **patrimoine net**, même base que les KPI. **Aucun seuil sur
les sous-sections Fonds/Titres** — elles restent en faisabilité pure (§3), la cohérence primant.

## 7 — Ce que ça change au CDC v4

- **Chantier J élargi** : J1 déclare les trois étages ; J2 est réalisé par ce document ; J3 (séparer
  l'intention) s'étend aux widgets ; **J7 nouveau** — porter le tri d'étage 2 et 3 dans le manifeste
  et retirer les conditions correspondantes des templates.
- **Chantier G** : G3 inclut le renommage D31. **G6 nouveau** — corriger le calcul des disponibilités
  (`Court terme`, matching par libellé, définition du fonds euros).
- **Chantier C** : le manifeste gagne `tri_decisions` — à inscrire au **registre des écarts** (M2/M3),
  statut « invention réelle ».
- **O8 clôturé** par D30. **T1 clôturé** par D31.
- **Nouveau O13** : les valeurs de seuil de déclenchement restent à proposer (je peux les dériver de
  Gronier et INTERAGYR, où les cas limites réels sont observables). Non bloquant : un seuil mal réglé
  ne coûte qu'une question de trop.

---

*Sources : `CDC_v4_2026-07-27.md` ; inspection du skill `reporting-fo-rhetores-alt`
(`p1_engine/assemble.py` BLOCK_ORDER, `excel_to_manifest.py` blocs_enabled, `p2_fill.py` construction
dispo/mp, `bank/blocs/performance.html.j2` et `performance_nc.html.j2`) ; arbitrages Thomas du 27/07.*
