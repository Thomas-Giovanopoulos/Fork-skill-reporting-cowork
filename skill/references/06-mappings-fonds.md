# Mappings de fonds validés — Spécifique client Hervé G.

> Tables de fonds identifiés et classifiés pour chaque poche du client Hervé G.
> Ce fichier est **spécifique-client** : à dupliquer / adapter pour chaque nouveau client.
> Référencé depuis le SKILL.md.

---

## Note sur la nature de ce fichier

À la différence des autres fichiers `references/` qui contiennent des règles **génériques**,
ce fichier contient des **données client spécifiques** : mappings de fonds réels avec leur ISIN.
C'est le seul fichier à dupliquer pour démocratiser le skill à un autre client.

**Logique d'enrichissement** : à chaque nouveau scan portefeuille ligne par ligne validé,
ajouter les fonds dans ce fichier pour ne plus avoir à les reclasser à la prochaine session.

---

## Poche PPT De Pury — Wealins Hervé G. (compte UBS 5159306)

| ISIN | Libellé | Classe Rhétorès | Géographie | Source de la classification |
|---|---|---|---|---|
| LU1481584016 | Flossbach Von Storch Bond Opport-IT | Obligations | — | M1 Morningstar |
| LU1331972494 | Eleva Absolute Return Europe | Alternatifs | — | M1 Morningstar |
| LU1103307663 | Goldman Sachs AB Return Tracker | Alternatifs | — | M1 Morningstar |
| XS3015338299 | JPM/Markit iTraxx Europe | Produits structurés | Europe | M4 nom sous-jacent |
| XS3209178162 | BNPPI/SHSZ300 | Produits structurés | Émergents (Chine) | M4 nom sous-jacent |
| LU1111643042 | Eleva European Selection | Actions | Europe | M1 Morningstar |
| IE00BKBF6H24 | iShares Core MSCI World ETF | Actions | International/Monde | M1 Morningstar |
| IE00BDBRDM35 | iShares Core Global Agg Bond ETF | Obligations | — | M1 Morningstar (⚠ mal classé "Zone Euro" par UBS) |
| IE00B3ZW0K18 | iShares S&P 500 EUR Hedged ETF | Actions | US | M1 Morningstar |
| IE00BF1B7389 | SSGA SPDR MSCI ACWI ETF | Actions | International/Monde | M1 Morningstar |
| CH1466881666 | Helevia Swiss Dividend Fund | Actions | Europe (Suisse rattachée) | M1 Morningstar |
| CH1137723925 | Swiss Physical Gold | Matières premières | — | M4 nom (⚠ mal classé "Actions" par UBS) |
| LU1870289573 | White Fleet IV Secular Trends | Actions | International/Monde | M1 Morningstar |
| LU0835721324 | RAM Systematic EM Equities | Actions | Émergents | M1 Morningstar |
| CH0140909257 | UBS Money Market EUR | Monétaire | — | M1 Morningstar |
| LU1280945632 | GAMA Global Bond Opportunities | Alternatifs | — | Validation Tristan |
| LU2092460075 | GAMA Short-Dated Opportunities | Obligations | — | Validation Tristan |
| LU2385154757 | White Fleet IV Enetia Energy | Actions | International/Monde | Validation Tristan |

---

## Poche FAS Rhétorès — Wealins Hervé G. (compte UBS 5159308)

| ISIN | Libellé | Classe UBS | Classe Rhétorès | Note |
|---|---|---|---|---|
| FR0010389254 | CM-CIC Moneplus FCP | Monétaires | Monétaire | ✅ conforme |
| FR0014002IJ4 | TOBAM BTC-Equity Fund | Monétaires | **Crypto** | ⚠ mal classé par UBS — BTC = crypto |
| FR0014002IG0 | TOBAM BTC-Linked and Blockchain | Monétaires | **Crypto** | ⚠ mal classé par UBS |
| XS3052630798 | Barclays/AWCDSD1 | Produits Structurés | Produits structurés | ✅ |
| XS3033792071 | Goldman Sachs/SGTED316 | Produits Structurés | Produits structurés | ✅ |
| FRSG000176H0 | SG Issuer/3M Euribor | Produits Structurés | Produits structurés | ✅ |
| FR0013293859 | TOBAM Bitcoin FPS -A1- | Alternatifs | **Crypto** | ⚠ mal classé par UBS |
| FR0014002H35 | TOBAM Bitcoin FPS -R1- | Alternatifs | **Crypto** | ⚠ mal classé par UBS |

---

## Autres poches — À enrichir au fil des sessions

Pour chaque nouvelle poche scannée ligne par ligne, ajouter ici une section :

```
## Poche [Nom] — [Contrat] [Entité] (compte [N°])

| ISIN | Libellé | Classe Rhétorès | Géographie | Source |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |
```

Poches à scanner pour compléter le mapping Hervé G. :
- FID Dauphine AM Hervé G. (UBS 5159312)
- FID UBS Hervé G. (UBS 5159534)
- FID Indosuez Hervé G. (Cardif Lux 1)
- FAS EdR + FID EdR Hervé G. (Cardif Lux 2)
- FID Dauphine AM SAS AX (UBS 5159538)
- FID De Pury Pictet SAS AX (UBS 5159542)
- FAS Rhétorès SAS AX (UBS 5159540)
- CTO EdR SAS AX
- CTO Tilvest SAS AX

---

## Règles transverses validées

### Règle TOBAM BTC
Tous les fonds TOBAM avec "BTC", "Bitcoin", "Blockchain" dans le nom → **Crypto**,
quelle que soit la classification UBS (Monétaire ou Alternatifs).

### Règle Infrastructure
La classe Infrastructure s'applique uniquement aux fonds **non cotés** d'infrastructure.
Les fonds **cotés** thématiques énergie/infrastructure (ex: White Fleet Enetia Energy)
sont classés en **Actions** avec géographie International/Monde.

### Règle géographie produits structurés
Ne pas calculer la géographie des produits structurés au niveau du donut Géographie
(trop complexe sans les term sheets). Le PS reste dans le donut Classes d'actifs uniquement.

### Alertes UBS récurrentes
UBS classe parfois des fonds selon leur **domiciliation** (Ireland, Luxembourg) plutôt que
leur **géographie réelle**. Toujours vérifier :
- Un fonds "Zone Euro" domicilié en Irlande peut être un ETF mondial → vérifier M1
- Un fonds "Actions" peut être de l'or physique ou un obligataire → vérifier M4
