# Cas particuliers et points d'attention récurrents

> Règles spécifiques rencontrées en pratique. Cas déjà rencontrés et tranchés.
> Référencé depuis le SKILL.md.

---

## Retraits et flux importants

Un retrait ou versement important (typiquement > 100 K€) doit apparaître **explicitement** :
- Avec une note explicative sous le tableau du Bloc 03
- La performance YTD doit être calculée selon Modified Dietz (voir `references/08-template-excel.md`,
  section "Onglet Mouvements") sur le capital pondéré, pas sur la valo globale

Exemple validé : retrait de −2 320 000 € sur la SAS Exemple le 10/01/2026 (poche FAS Rhétorès Wealins),
documenté dans l'onglet Mouvements du fichier Excel source.

---

## Catégorie "Autres investissements" UBS

UBS regroupe parfois des actifs de natures différentes sous la catégorie "Autres investissements"
dans ses relevés. **Toujours éclater cette catégorie** en appliquant la méthode M1-M5 par ligne
(voir `references/02-classification.md`).

Exemples d'éclatement validés :
- "Autre investissement / Or physique" → Matières premières
- "Autre investissement / Hedge Fund" → Alternatifs
- "Autre investissement / SCPI cotée" → Actions (REIT) ou Immo non coté selon liquidité

---

## GAMA vs DNCA — Disambiguation

Plusieurs fonds aux noms proches peuvent être confondus :

| Fonds | Classe Rhétorès | Justification |
|---|---|---|
| GAMA Global Bond Opportunities | **Alternatifs** | Pas de benchmark obligataire classique, gestion non contrainte, vol > 5% |
| GAMA Global Short-Dated | **Obligations** | Dette < 3 ans, vol < 3%, catégorie oblig. flexible |
| DNCA Alpha Bonds | **Alternatifs** | Benchmark €STR +2%, performance absolue |

---

## Indosuez Cap Émergents

Fonds mixte 50% actions / 50% obligations émergents. Décision validée :
- Pour la classification d'allocation : split 50/50 entre Actions Émergents et Obligations Émergents
- Pour la géographie : 100% Émergents (sur la part Actions uniquement)

---

## Saint Honoré Innovation

Relevé disponible uniquement au 17/04 (date différente des autres relevés au 30/04).
**Convention** : afficher la valeur avec un astérisque `984 023 €*` et une note de bas de tableau :
"* Valorisation au 17/04/2026, dernier relevé disponible."

---

## Reclassifications UBS systématiques

Vérifier systématiquement ces cas connus dans tous les relevés UBS :

| Position UBS | Classe UBS d'origine | Classe Rhétorès correcte |
|---|---|---|
| Tobam BTC-... (plusieurs fonds) | Monétaire ou Alternatifs | **Crypto** |
| iShares Bitcoin Trust ETF (IBIT) | Actions Monde | **Crypto** |
| WisdomTree Physical Gold | Actions | **Matières premières** |
| iShares Gold Trust (IAU) | Actions | **Matières premières** |
| Saint Honoré Innovation | Actions Monde | **Private Equity coté** → Actions International |

---

## EdR — Transferts internes

Les transferts internes EdR (entre comptes du même client) ne sont **PAS** des flux à comptabiliser
dans Modified Dietz. Convention : ces opérations apparaissent dans le relevé EdR mais ne doivent
pas figurer dans l'onglet Mouvements du fichier Excel source.

Exemple : transfert de fonds entre CTO EdR et FAS EdR au sein de la même AV Cardif Lux 2 de Client Exemple.

---

## Fonds euros — Valorisation hors PB

Les fonds euros sont revalorisés uniquement lors du versement annuel de la participation aux
bénéfices (généralement janvier/février N+1 pour l'année N).

**Conventions de valorisation au 31/03 ou 30/06** :
- Valeur affichée = dernière valeur post-PB connue (sans recalcul)
- Pas de signe "*" ni de note "valorisation indicative"
- Performance YTD = 0% jusqu'au prochain versement de PB

**Exception — Calcul prorata 2,5%** : si tu veux estimer une valeur intermédiaire (Cardif Lux),
appliquer un calcul ponctuel au prorata d'un rendement annuel hypothétique de 2,5%.
Formule type : `Valeur date = Valeur 01/01 × (1 + 2.5% × N_mois/12)`.

---

## Contrats sans valeur 01/01 (nouveaux contrats)

Pour un contrat souscrit dans l'année (ex: Lombard Utmost ouvert en avril 2026) :
- Pas de "Valeur 01/01" dans le fichier Excel
- Le "Gain % YTD" reste vide ou affiche `—`
- Seule la performance "depuis l'origine" (Gain € et Gain %) peut être calculée à partir du nominal

---

## Lombard / Crédit Lombard

Les prêts Lombard sont **toujours** classés en "In fine" (pas amortissable).
Le contrat servant de garantie doit avoir la mention "Nantissement = Oui".

Cas validés Client Exemple :
- Prêt Lombard UBS → garanti par les contrats Wealins Lux (toutes poches)
- Prêt Lombard Indosuez → garanti par Cardif Lux 1 uniquement (PAS Cardif Lux 2)
