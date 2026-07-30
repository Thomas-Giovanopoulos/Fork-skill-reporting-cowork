# Reprise — à lire en premier dans une nouvelle session

> Réécrit le 2026-07-30 (fin de la 3ᵉ session). Tout l'état utile est sur disque : ce fichier
> suffit à repartir sans relire l'historique du chat. Détail : `JOURNAL.md` (entrées datées, la
> section « À faire ensuite » est À JOUR) ; décisions D32–D52 : `docs/roadmap_2026-07-27.md`,
> D45–D49 : `docs/CDC_v5_2026-07-29.md`, D50–D51 : `docs/spec_historique_arretes_2026-07-30.md` ;
> registre des écarts : R1–R11.

## Amorçage

```bash
pip install -U jsonschema                          # T4 : Draft 2020-12 requis
cd FORK-Cowork && python3 verifier_pieges.py       # garde N3 (retournée le 30/07)
cd skill && python3 p1_engine/selfcheck.py         # paquet intègre (132 fichiers)
python3 p1_engine/tests/test_l3a.py fx_simple      # lecteur vivant (sous-ensemble, timeout 45s)
```

## Où on en est, en cinq lignes

1. **Chantier L (lecteur de forme-store) : FAIT.** Format convergé `2.1-skill` (D48), lecteur en
   façade (`p1_engine/lecteur_store.py`), preuve L3a chaîne complète **7/7 à l'octet près**
   (manifeste + HTML), bascule ⑤ : le store est le chemin nominal (SKILL.md §2.e,
   `store_to_manifest.py`). Coupure du chemin Excel différée, prérequis nommés (JOURNAL 30/07-4).
2. **Chantier B : B-i → B-iv FAITS.** Priming des subagents par profil (N3 soldé), outillage
   `valider_diff.py`/`appliquer_diffs.py` (20 tests, 5 refus prouvés), table de vérité
   d'extraction (`outils_extraction/`, autotest deux sens), et **premier run réel INTERAGYR
   validé** (`runs/interagyr_2026-07/`, rejouable) : MCP vivant (D36), 4 subagents primés en
   parallèle, QC **9/9** dont le nouveau **QC de traversée** (Σ lignes rendues = Σ lignes store),
   SRI 4/7 du contrôle d'époque retrouvé par la mécanique, **11 min vs 25** (O10 chiffré).
3. **Deux passes de revue de Thomas** contre le contrôle d'époque, tout diagnostiqué :
   `docs/revue_controle_interagyr_2026-07-30.md` (§0 cause racine, §2-bis/§2-ter/§2-quater).
   Deux bugs corrigés le jour même : la **jointure `nature` verbatim** (53 lignes perdues en
   silence — R11) et `envelope()` (formes longues).
4. **PROCHAIN GROS MORCEAU : le CHANTIER UI** — discussion de design DÉDIÉE, avant toute ligne
   de template. Pièces : `reference/controles_epoque/` (2 rendus d'époque + README avec les
   réserves de Thomas) et la revue. Périmètre listé au JOURNAL « À faire ensuite » ; premier
   candidat : le **canvas PE** (p2_fill calcule séries/barres, le template ne dessine pas).
5. **Base saine** : paquet scellé 132 fichiers, selfcheck OK, golden 7/7, toutes suites vertes,
   garde D44 éprouvée (5 morsures cette session, toutes traitées).

## Les réflexes constants

- **Ne jamais faire régresser le skill** : golden (2 moitiés, timeout 45 s) + L3a + QC avant/après.
- Table-de-vérité-d'abord ; un invariant non testé n'est qu'un commentaire ; échec bruyant (L5),
  jamais de défaut silencieux ; ambiguïté signalée, jamais tranchée seule.
- Trouvaille hors chemin → liste ; fuite client ou régression → interruption. **Resceller après
  tout changement de `skill/`** (`regenerer_checksums.py`), et rendre les clients réels depuis un
  **répertoire jetable** — `snapshots/` écrit dans le cwd et a encore mordu cette session.
- Le pipeline écrit des fichiers, l'AGENT parle au MCP (symétrie D35/D36). Bash sandbox : 45 s
  max, pas de tâches de fond. Le venv fatigue → on coupe, le dossier porte tout.
