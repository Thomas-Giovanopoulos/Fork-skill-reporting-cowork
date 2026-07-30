# POC étape 2 — Banque de modules + assembleur P1

Preuve de concept : transformer la phase **P1 (Structure)** en génération **par assemblage de
modules** plutôt que par rédaction libre du HTML. Extraite de `consolide_client_exemple_v15.html` (la cible la
plus proche fournie par Tristan).

## Comment ça marche

```
manifest.example.json  ──>  assemble.py  ──>  build/skeleton_client_exemple.html
   (leviers variables)      (code, banque bank/)     (squelette vide)
```

```bash
python3 assemble.py manifest.example.json build/skeleton_client_exemple.html
```

L'assembleur : valide le manifeste (schéma + règles métier), applique les **ordres canoniques figés
dans le code**, puis assemble les modules Jinja2 de `bank/`. Le LLM ne produit aucun HTML.

## Arborescence de la banque

```
bank/
  base.html.j2                  assemble les blocs dans l'ordre canonique
  partials/
    head.html.j2                <head>, polices, Chart.js, body
    _styles.html                TOUTE la CSS, extraite verbatim de v15 (figée)
    foot.html.j2                footer + fermeture
  blocs/
    hero.html.j2                Hero — structure figée, valeurs = data-slot (remplies en P2)
    exhaustif.html.j2           Bloc 02 — boucle sur les entités
  fragments/
    entity_section.html.j2      1 entité : boucle ses catégories en ORDRE CANONIQUE
  columns/                      LES 5 JEUX DE COLONNES (cœur paramétrique)
    cols_liquidites.html.j2     2 colonnes
    cols_immobilier.html.j2     7 colonnes
    cols_financier_cote.html.j2 8 colonnes
    cols_non_cote.html.j2       7 colonnes
    cols_dettes.html.j2         8 colonnes
```

## Ce que le POC prouve

1. **Déterminisme strict** — deux rendus du même manifeste donnent un fichier au **hash identique**.
2. **Structure non tordable par les données** — le manifeste ne porte pas de valeurs ; mélanger
   l'ordre des catégories dans le manifeste ne change rien : l'assembleur impose l'ordre canonique
   (Liquidités → Immobilier → Financier coté → Non coté → Dettes).
3. **Fidélité à v15** — le squelette reproduit exactement les sections par entité de l'original :
   - Client Exemple : Liquidités, Immobilier, Financier coté, Dettes
   - SAS Exemple : Liquidités, Financier coté, Financier non coté
   - SAS Exemple 2 : Liquidités, Immobilier
4. **Pas de trou silencieux** — Jinja est en `StrictUndefined` : toute variable manquante lève une
   erreur au lieu de produire un HTML incomplet.

## Frontière P1 / P2 matérialisée

Le squelette s'arrête où commence le remplissage. Les points que P2 viendra remplir sont marqués par
des attributs `data-slot` (ex : `data-slot="subtotal"`, `data-slot="entity_total"`, KPIs du Hero) et
par un commentaire `<!-- data-slot:rows ... -->` à l'emplacement des lignes de chaque catégorie.

## Divergences relevées entre v15 et les fichiers de référence (à arbitrer avec Tristan)

Le HTML cible diffère des `references/` sur trois points structurels. J'ai suivi **le HTML** :

1. **Numérotation des blocs.** v15 = 00 Contexte · 01 Répartition · 02 Exhaustif. Les références
   prévoient 01 Performance · 02 Répartition · 03 Exhaustif. v15 n'a pas de bloc Performance.
2. **Colonnes Liquidités.** v15 = 2 colonnes (Intitulé du compte · Solde). La référence en prévoit 4.
3. **Colonnes Immobilier.** v15 = 7 colonnes, dont « Loyer ann. » et « Date acq. » que la référence
   disait explicitement **ne pas afficher**. Idem Non coté (MOIC, Non appelé estimé) et Dettes
   (Taux, Échéance, Périodicité, Garantie) plus riches que la référence.

> Décision à prendre : la référence fait-elle foi (et v15 est en avance), ou v15 fait-elle foi (et il
> faut mettre à jour les références) ? Tant que ce n'est pas tranché, les modules `columns/` collent à v15.

## Limites du POC (volontaires)

- Couvre Hero + Bloc 02 Exhaustif + Footer. Bloc 00 (contexte) et Bloc 01 (répartition : tableau
  global, 4 donuts, cards entités) sont à ajouter comme modules sur le même patron — les donuts et le
  tableau global sont des modules **fixes**, les cards entités un **fragment paramétrique** (1 par entité).
- La logique multi-poches du Financier coté relève du remplissage P2 (nombre de poches = donnée), pas
  de la structure P1. Le module ne fige que l'en-tête de colonnes.

---

## Installation & exécution

L'assembleur a besoin de Python 3.9+ et de deux paquets.

```bash
# 1. installer les dépendances (une seule fois)
pip install -r p1_engine/requirements.txt
#   (en environnement sandbox géré, ajouter si besoin : --break-system-packages)

# 2. générer le squelette à partir d'un manifeste
python3 p1_engine/assemble.py mon_manifeste.json consolide_Client_squelette.html
```

Vérifier le déterminisme (optionnel) : générer deux fois et comparer les empreintes —
elles doivent être identiques.

```bash
python3 p1_engine/assemble.py m.json a.html && python3 p1_engine/assemble.py m.json b.html
sha256sum a.html b.html   # les deux hash doivent être égaux
```

En cas d'erreur « Manifeste invalide », l'assembleur indique précisément le champ fautif
(schéma) ou la règle métier violée (1 seule PP en tête, id d'entité uniques).
