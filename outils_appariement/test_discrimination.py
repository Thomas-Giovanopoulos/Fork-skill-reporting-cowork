#!/usr/bin/env python3
"""Contrôles NÉGATIFS de l'appariement — ce que le harnais ne peut pas prouver.

Le harnais vérifie que chaque document trouve son profil. C'est nécessaire et insuffisant : un
matcher qui répondrait « oui » à tout le passerait aussi. Ce fichier vérifie l'inverse — que les
profils **se refusent** les documents qui ne sont pas les leurs.

Le contrôle central est le n°1, et il vise une faiblesse de la démonstration précédente. Sur le
Cardif de 2024, le profil v2 est écarté par sa **fenêtre de validité** : le verdict est juste, mais
c'est la date qui travaille, pas la signature. Or dans un run réel la date d'arrêté peut manquer —
et alors seules les ancres décident. On rejoue donc l'appariement **sans arrêté**, les deux fenêtres
éligibles, pour vérifier que les signatures suffisent à distinguer deux versions du même gabarit.

C'est la différence entre « le test passe » et « le test prouve quelque chose ».
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matcher_gabarit import apparier, charger_profils  # noqa: E402

ASSUREUR = Path("/sessions/epic-happy-ritchie/mnt/Données assureur")
PROFILS = charger_profils(Path(__file__).resolve().parent / "profils_corpus.json")

echecs: list[str] = []


def verifie(intitule: str, obtenu, attendu) -> None:
    ok = obtenu == attendu
    print(f"  {'OK   ' if ok else 'ÉCHEC'} {intitule}")
    if not ok:
        print(f"          obtenu  : {obtenu!r}")
        print(f"          attendu : {attendu!r}")
        echecs.append(intitule)


# D44 — les noms de fichiers PDF ci-dessous sont les CHEMINS RÉELS du corpus assureur, qui
# conserve ses noms d'origine : ce fichier lit ces PDF, les renommer casserait le contrôle. Le
# corpus est hors du paquet `skill/`, donc hors de ce qui est distribué aux CGP. En revanche les
# LIBELLÉS imprimés par ce script sont dé-identifiés : ils ne recopient plus le nom du client.
def apparie(nom: str, arrete: str | None):
    return apparier(ASSUREUR / nom, PROFILS, arrete)


print("1. Deux versions d'un même gabarit se distinguent PAR LEURS ANCRES, sans date d'arrêté")
print("   (si ce contrôle échoue, la fenêtre de validité masquait une signature indiscriminante)")

v24 = apparie("2024.12 relevé Cardif Elite Capi HANAMI.pdf", None)
verifie("Cardif 2024 sans arrêté → v1", (v24.gabarit, v24.valide_depuis),
        ("situation_contrat_capi_pm", "2024-01-01"))
verifie("Cardif 2024 sans arrêté : verdict non ambigu", v24.statut, "apparie")

v25 = apparie("2025.12 Relevé Cardif Elite Capi HANAMI.pdf", None)
verifie("Cardif 2025 sans arrêté → v2", (v25.gabarit, v25.valide_depuis),
        ("situation_contrat_capi_pm", "2025-12-31"))
verifie("Cardif 2025 sans arrêté : verdict non ambigu", v25.statut, "apparie")

print("\n2. La fenêtre de validité écarte bien la mauvaise version quand l'arrêté est connu")
v24b = apparie("2024.12 relevé Cardif Elite Capi HANAMI.pdf", "2024-12-31")
retenus = {(c["gabarit"], c["valide_depuis"]) for c in v24b.candidats}
verifie("v2 absent des candidats pour un arrêté de 2024",
        ("situation_contrat_capi_pm", "2025-12-31") in retenus, False)

print("\n3. Les deux gabarits Wealins ne se confondent pas")
print("   (piège : le mot « trimestre » est PLUS fréquent dans les annuels — 10 contre 3)")
wa = apparie("2025 Relevé annuel Wealins FC051727 HANAMI.pdf", None)
wt = apparie("Situation trimestrielle FC051727_31 03 26.pdf", None)
verifie("relevé annuel → releve_annuel_capi_lux", wa.gabarit, "releve_annuel_capi_lux")
verifie("situation trimestrielle → situation_trimestrielle_capi_lux", wt.gabarit,
        "situation_trimestrielle_capi_lux")
verifie("aucun des deux n'est ambigu", {wa.statut, wt.statut}, {"apparie"})

print("\n4. Un document ne s'apparie pas au profil d'un AUTRE émetteur")
print("   (le seul profil retenu doit être celui de son émetteur, pas seulement le mieux classé)")
for nom, emetteur, libelle in (
    ("2024.12 Relevé Himalia Capi HANAMI.pdf", "himalia_emetteur_a_confirmer",
     "relevé Himalia capi, arrêté 2024.12"),
    ("2026.06 relevé UAF Cerise.pdf", "spirica", "relevé UAF, arrêté 2026.06"),
    ("2025.12 Relevé Cardif Elite Capi HANAMI.pdf", "cardif",
     "relevé Cardif Elite capi, arrêté 2025.12"),
):
    v = apparie(nom, None)
    autres = {c["gabarit"] for c in v.candidats
              if c["gabarit"] != v.gabarit}
    verifie(f"{libelle:44s} → {emetteur}", v.emetteur_code, emetteur)
    verifie(f"{'':44s}   aucun profil d'un autre gabarit ne franchit la barrière", autres, set())

print("\n5. Un document hors corpus ne doit PAS être apparié de force")
print("   (un matcher qui répond toujours « oui » passerait tous les contrôles précédents)")
faux = Path("/tmp/_pas_un_releve.pdf")
if not faux.exists():
    import subprocess
    subprocess.run(["bash", "-c",
                    f"printf 'Ceci est un document quelconque, sans aucune ancre connue.\\n' "
                    f"| ps2pdf - {faux} 2>/dev/null || true"], check=False)
if faux.exists() and faux.stat().st_size > 0:
    vf = apparie(faux.name, None) if False else apparier(faux, PROFILS, None)
    verifie("document quelconque → aucun profil", vf.statut in ("aucun", "illisible"), True)
else:
    print("  —     (ps2pdf indisponible : contrôle sauté, à rejouer dans un environnement complet)")

print(f"\n{'ÉCHEC' if echecs else 'OK'} — {len(echecs)} échec(s)")
sys.exit(1 if echecs else 0)
