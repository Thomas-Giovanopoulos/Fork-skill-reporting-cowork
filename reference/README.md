# Référence de rendu sur client réel — Gronier T2 2026

> Importée le 2026-07-28 depuis la session « Reporting skill (Gronier) », qui contenait le seul
> forme-store **réel** produit à ce jour. C'est ce qui débloque **L1** et rend **L3b** possible : les
> 7 fixtures prouvent la fidélité du lecteur, seul un client réel mesure la perte de la projection Excel.

## Contenu

| Fichier | Rôle |
|---|---|
| `gronier_T2/client.store.json` | le forme-store — **migré** (poche unique matérialisée, A5) |
| `gronier_T2/client.store.json.bak` | l'original avant migration, à conserver |
| `gronier_T2/manifest.json` | le manifeste — **migré** (clé `blocs_enabled.historique` retirée) |
| `gronier_T2/manifest.json.bak` | l'original |
| `gronier_T2/Reporting_Gronier_T2_2026.xlsx` | le classeur de transition, 15 onglets |
| `gronier_T2/consolide_Gronier_T2_2026.html` | le HTML livré au client |
| `gronier_T2/contexte_T2 2026.json` | le contexte de marché du trimestre |
| `gronier_T2/cp_valos.json` | 9 séries de valorisation × 5 dates — **orphelines**, cf. M7 |
| `gronier_T2/rapport_apply.md` | le rapport de réconciliation, qui explique l'écart store ↔ classeur |

## Rejouer

```bash
cd /tmp && mkdir -p rejeu && cd rejeu          # PAS depuis skill/ : voir l'avertissement ci-dessous
python3 <fork>/skill/p1_engine/p2_fill.py \
    <fork>/reference/gronier_T2/Reporting_Gronier_T2_2026.xlsx \
    <fork>/reference/gronier_T2/manifest.json  sortie.html
```

Attendu : **contrôles comptables 9/9**, actif brut **4 608 966 €** (3 982 294,76 coté + 626 670,92 non
coté), dettes 0. Deux avertissements normaux et attendus : 13 lignes de détail sans performance, et le
placeholder P4 du commentaire de gestion.

**⚠ Ne pas lancer le rendu depuis `skill/`.** `p2_fill` écrit un snapshot dans `./snapshots/` relatif au
répertoire courant : rendre depuis `skill/` **ajoute un fichier au paquet**, ce qui fait échouer le
selfcheck au prochain contrôle d'intégrité (constaté — le paquet est passé à 117 fichiers). Rendre depuis
un répertoire de travail jetable.

## Ce que cette référence sait déjà nous dire

**Le store réel valide le schéma sans une erreur, et ce fait ne prouve rien.** Il passait parce que six
des dix tableaux du schéma sont absents — et facultatifs — et parce que `additionalProperties: true` ne
contraint rien sur les entrées. *Zéro erreur n'est pas zéro perte.*

**Le store et le classeur ne sont pas synchronisés**, et c'est un piège pour L3 : 6 471,21 € d'écart sur
le coté, 400 876 € sur le capital investi de FC051727. `rapport_apply.md` l'explique — le store est resté
sur les valorisations « Catégories & Perf » du 23/07 quand le classeur a été recalé le 24/07 sur les
relevés officiels. **Un contrôle « rendu Excel ≡ rendu store » sur ce couple mesurerait cette dérive, pas
la fidélité du lecteur.** Le premier travail de L3b est donc de régénérer le store depuis les relevés
officiels — pas de comparer en l'état.

Le détail des neuf manques, des deux manques supplémentaires révélés par ce run (M10, M11) et des cinq
ambiguïtés est au §7 de `docs/spec_lecteur_forme_store_2026-07-28.md`.

## Migrations appliquées

Par `migrer_reference.py` (à la racine du fork), idempotent, `.bak` conservés :

- **manifeste** : `blocs_enabled.historique` retiré (valait `false`). Le bloc *Rendement annuel* a été
  renommé puis **retiré** en session 1 (D31) — la clé n'a plus de destination, et `blocs_enabled` étant
  `additionalProperties: false`, sa présence faisait échouer la validation **avant même l'ouverture du
  classeur**.
- **store** : poche unique matérialisée sur les 5 contrats qui n'en avaient pas ; `custodian` et
  `invest_date` propagés du contrat vers les poches des 2 contrats qui en avaient déjà.

Ce qui n'a **pas** été comblé, délibérément : `capital_invested` et `value_jan1` sur les poches de
`tmp_fc_006` et `tmp_fc_007`. Ils sont propres à chaque poche et les répartir au prorata serait fabriquer
une donnée. La perf YTD par poche reste donc non calculable pour ces deux contrats — le manque doit rester
visible, et la migration le signale à chaque passage.
