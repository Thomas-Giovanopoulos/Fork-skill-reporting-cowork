# Run INTERAGYR — 2026-07-30 (B-iv, premier run réel du chantier B)

Mode **AGRÉGATION** : Excel de structure (ancres) + 4 PDFs → identification → 4 subagents primés
→ diffs → apply → store 2.1-skill → rendu direct. Décisions CGP du run (AskUser batché) :
**comptes séparés** (4 CTO UBS, banque désambiguïsée) ; **arrêté 15/07/2026** (date des relevés).

## Rejouer

```
# 1. Référentiels : ref_bundle (MCP vivant — provenance de CE run) → referentiels.json
# 2. Identification (déterministe) :
python3 skill/pipeline/matcher_gabarit.py … → identification.json (4/4 appariés, 0.96–1.00)
# 3. Extraction : 4 subagents primés par les profils du bundle (non déterministe — filet B)
# 4. Chaîne déterministe :
python3 skill/pipeline/valider_diff.py runs/interagyr_2026-07/diff_*.json
python3 skill/pipeline/appliquer_diffs.py runs/interagyr_2026-07/ancres.store.json \
    runs/interagyr_2026-07/client.store.json runs/interagyr_2026-07/diff_*.json \
    --arrete 2026-07-15 --referentiels runs/interagyr_2026-07/referentiels.json \
    --documents runs/interagyr_2026-07/contexte_docs.json \
    --rapport runs/interagyr_2026-07/rapport_apply.json
python3 outils_extraction/harnais_extraction.py runs/interagyr_2026-07/client.store.json \
    "Interagyr.pdf" "Releve╠ü - INTERAGYR Offensif 6.pdf"
cd skill && python3 p1_engine/store_to_manifest.py ../runs/interagyr_2026-07/client.store.json \
    ../runs/interagyr_2026-07/manifest.json --period-long "T3 2026" --period-short "T3-26" \
    --date 2026-07-15 --date-display "15 juillet 2026"
python3 p1_engine/p2_fill.py ../runs/interagyr_2026-07/client.store.json \
    ../runs/interagyr_2026-07/manifest.json ../runs/interagyr_2026-07/reporting_interagyr.html
```

## Résultats

| Contrôle | Verdict |
|---|---|
| Identification | 4/4 appariés (PPT 1.00, Dauphine 0.98/0.98/0.96), profils du store VIVANT |
| Validation des diffs | 4/4 après correction de 2 `unrecognized_data` mal formés (le valideur a mordu, les subagents ont corrigé leur propre fichier) |
| Apply | 4 changements, **0 conflit** (les old_value = ancres, exactes), provenance D49 posée |
| Harnais d'extraction | **7/7 points** sur les 2 documents établis (PPT + Dauphine Offensif) |
| Contrôles comptables | **7/7 OK**, rendu déterministe, actif brut 4 723 156 € |

## Écarts et questions pour le CGP (réconciliation B3 — à présenter, pas à trancher seul)

1. **Valeurs ancres vs relevés** (appliquées, à confirmer) : PPT 1 982 034 → 1 982 033,79 ;
   Dauphine Équilibré 1 501 734 → 1 502 062 ; Prudent 501 321 → 501 163 ; Offensif 500 456 →
   **497 897** (−2 559 €, le plus gros écart).
2. **Profil PPT** : le relevé dit « Croissance », la structure dit « Dynamique ». Non modifié —
   qualification CGP requise.
3. **Dates** : relevés Dauphine « au 16/07 » (semaine 13–16/07), PPT « au 15/07 » — l'arrêté du
   run est 15/07 ; écart d'un jour à assumer ou documenter.
4. **Mouvement détecté hors périmètre du diff** : achat LBPAM +25 116 € (Tresorerie 2, semaine du
   relevé) → `unrecognized_data`, à qualifier.
5. **4 acteurs non résolus** (attendu) : les banques désambiguïsées « UBS (…) » ne sont pas des
   alias du référentiel — c'est la contrepartie du choix « comptes séparés » ; question de
   modélisation à instruire (le discriminant de mandat pourrait vivre ailleurs que dans
   `assureur`).
6. **Commentaire de gestion absent** (P4) et contexte de marché T3-26 non fourni — éditorial,
   avant livraison.

## Leçons du run (détail au JOURNAL, entrée du 30/07)

Le valideur a attrapé de la variance réelle de subagents dès le premier lot ; le harnais était
plus strict que la règle qu'il vérifie (liquidités exemptées de perf_pct — corrigé) ; et le
priming a visiblement travaillé : filigrane filtré, U+2212, monétaire PPT reclassé, double
convention numérique gérée, « — » ≠ 0.
