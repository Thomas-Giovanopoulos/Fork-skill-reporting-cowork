#!/usr/bin/env python3
"""Régénère skill/CHECKSUMS.json — À LANCER APRÈS TOUTE MODIFICATION DU SKILL.

    python3 regenerer_checksums.py            met à jour et affiche le delta
    python3 regenerer_checksums.py --verifier n'écrit rien, liste les écarts

Pourquoi ce script existe
-------------------------
`p1_engine/selfcheck.py` contrôle la taille et le md5 de chaque fichier contre
`CHECKSUMS.json`. Or l'étape 0 du protocole du skill impose : **si le self-check
échoue, STOP**. Une modification légitime fait donc échouer le selfcheck, et son
message oriente vers un faux diagnostic — « troncature probable », donc « paquet
corrompu, réinstallez ». Sans ce script, chaque édition du fork casse le skill de
façon trompeuse.

`CHECKSUMS.json` est exclu de son propre manifeste (il ne peut pas contenir son
propre md5). Les caches Python le sont aussi : ce n'est pas de la source.

Garde-fou D44 — pourquoi ICI et pas dans selfcheck.py
-----------------------------------------------------
`selfcheck.py` tourne à CHAQUE run de CHAQUE CGP : c'est le chemin chaud, il doit
rester à ~1 s et ne rien découvrir de neuf. Le paquet, lui, n'est scellé qu'ici, par
nous, et une seule fois par modification. Le contrôle d'identifiants clients a donc
sa place au **scellement** : c'est le dernier point où l'on peut encore refuser
d'expédier. Chez le CGP, il serait trop tard — le fichier est déjà installé.

Le contrôle BLOQUE l'écriture, il n'avertit pas : un manifeste régénéré est une
autorisation de diffusion. Il a été vérifié en injectant un faux identifiant dans un
fichier du paquet et en constatant le refus nominatif (fichier + ligne).
Même barrière, mêmes conventions que `seed/construire_bundle.py` (garde-fou D44 côté
seed) et `infra/migration_002_purge_identifiants_clients.sql` (côté base).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
SKILL = ICI / "skill"
MANIFESTE = SKILL / "CHECKSUMS.json"

EXCLUS_NOMS = {"CHECKSUMS.json"}
EXCLUS_MOTIFS = ("__pycache__",)

# --------------------------------------------------------------------------------------------
# Garde-fou D44 : aucun identifiant client dans le paquet distribué
# --------------------------------------------------------------------------------------------
# Noms de clients et d'entités clientes connus du corpus, en minuscules. LISTE PAR NATURE
# INCOMPLÈTE : elle attrape les clients DÉJÀ connus, jamais un nouveau. Elle ne remplace donc pas
# la relecture — elle empêche seulement une régression sur ce qui a déjà fuité une fois.
# À ÉTENDRE à chaque nouveau client dont un document entre dans le corpus.
#   - `interagyr` est le piège : ce n'est ni un partenaire ni un émetteur, c'est un CLIENT
#     (découverte A.1-1 de l'étude de signature) ; il se purge au même titre que `gronier` ;
#   - `cerise` / `pollux` sont deux contrats clients du corpus Spirica ;
#   - `herve` / `sas ax` / `sas lg` étaient l'exemple courant de la documentation, remplacé par
#     les placeholders non ambigus « Client Exemple » / « SAS Exemple » (D44).
# Les deux graphies de `herve` sont listées : la purge doit résister à l'accent perdu.
NOMS_CLIENTS = (
    "hanami", "shida", "matsu", "gronier", "interagyr", "cerise", "pollux",
    "herve", "hervé", "herve_g", "sas ax", "sas_ax", "sas lg", "sas_lg",
)

# Forme des références de contrat rencontrées chez Wealins et Quintet : deux lettres suivies de
# cinq à huit chiffres (forme synthétique 'AB1234567'). Les valeurs réelles ne sont volontairement
# PAS citées ici — documenter une fuite en la recopiant la laisse ouverte.
MOTIF_REFERENCE_CONTRAT = re.compile(r"[A-Z]{2}[0-9]{5,8}")

# Un ISIN est un code de MARCHÉ, pas un identifiant client — et il contient exactement la forme
# d'une référence de contrat : `DK0062498333` (Novo Nordisk) contient « K0062498 ». On SOUSTRAIT
# donc les ISIN bien formés AVANT de chercher. Sans cette soustraction, le contrôle hurle sur les
# 261 lignes légitimes de assets/isin_referentiel_v0.csv ; plus personne ne le croit, quelqu'un le
# commente « en attendant », et il est désarmé. C'est le mode de défaillance d'un garde-fou trop
# bavard : il ne meurt pas d'être faux, il meurt d'être ignoré.
MOTIF_ISIN = re.compile(r"\b[A-Z]{2}[0-9A-Z]{9}[0-9]\b")

# Préfixe réservé aux références MANIFESTEMENT FICTIVES qui illustrent la forme dans la doc
# (`XX000001`). Elles ont la forme d'une référence de contrat — c'est le but — donc on les exempte
# explicitement plutôt que d'assouplir le motif.
PREFIXE_REFERENCE_FICTIVE = "XX"

# Binaires du paquet : illisibles en texte, et de toute façon pas de la doc rédigée. Le reste est
# décodé en utf-8 strict ; ce qui ne se décode pas est signalé et sauté, pas ignoré en silence.
SUFFIXES_BINAIRES = {".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg", ".zip", ".pyc", ".ico"}


def pertinent(p: Path) -> bool:
    if p.name in EXCLUS_NOMS or p.suffix == ".pyc":
        return False
    return not any(m in p.parts for m in EXCLUS_MOTIFS)


def identifiants_dans(texte: str) -> list[str]:
    """Rend la liste de ce qui a été reconnu dans une ligne (vide si elle est propre)."""
    trouves: list[str] = []
    reste = MOTIF_ISIN.sub(" ", texte)  # cf. MOTIF_ISIN : la soustraction est le cœur du contrôle
    for m in MOTIF_REFERENCE_CONTRAT.finditer(reste):
        if m.group(0).startswith(PREFIXE_REFERENCE_FICTIVE):
            continue
        trouves.append(f"référence de contrat {m.group(0)!r}")
    bas = texte.lower()
    for nom in NOMS_CLIENTS:
        if nom in bas:
            trouves.append(f"nom de client {nom!r}")
    return trouves


def auditer() -> list[tuple[str, str, str]]:
    """Parcourt le paquet. Rend la liste des (fichier, ligne, ce qui a été reconnu).

    Les NOMS DE FICHIERS sont audités au même titre que leur contenu : un snapshot de run client
    porte le nom du client dans son nom de fichier et rien dans son contenu.
    """
    fuites: list[tuple[str, str, str]] = []
    for p in sorted(SKILL.rglob("*")):
        if not p.is_file() or not pertinent(p):
            continue
        rel = p.relative_to(SKILL).as_posix()
        for quoi in identifiants_dans(rel):
            fuites.append((rel, "nom de fichier", quoi))
        if p.suffix.lower() in SUFFIXES_BINAIRES:
            continue
        try:
            texte = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"  ! {rel} : non décodable en utf-8, non audité (binaire ?)", file=sys.stderr)
            continue
        for n, ligne in enumerate(texte.splitlines(), start=1):
            for quoi in identifiants_dans(ligne):
                fuites.append((rel, f"ligne {n}", quoi))
    return fuites


def calculer() -> dict[str, dict]:
    out = {}
    for p in sorted(SKILL.rglob("*")):
        if not p.is_file() or not pertinent(p):
            continue
        data = p.read_bytes()
        rel = p.relative_to(SKILL).as_posix()
        out[rel] = {"size": len(data), "md5": hashlib.md5(data).hexdigest()}
    return out


def main() -> int:
    if not SKILL.is_dir():
        print(f"Dossier introuvable : {SKILL}", file=sys.stderr)
        return 2

    # Garde-fou D44 AVANT tout : régénérer le manifeste, c'est autoriser la diffusion du paquet
    # chez chaque CGP. On refuse de sceller ce qu'on ne peut pas expédier.
    fuites = auditer()
    if fuites:
        print("IDENTIFIANT CLIENT DÉTECTÉ — le manifeste n'a PAS été régénéré (D44) :",
              file=sys.stderr)
        vus = set()
        for fichier, ou, quoi in fuites:
            if (fichier, ou, quoi) in vus:
                continue
            vus.add((fichier, ou, quoi))
            print(f"  - {fichier} ({ou}) : {quoi}", file=sys.stderr)
        print("\n  Le paquet `skill/` s'installe chez CHAQUE CGP : un identifiant client qui entre\n"
              "  ici est distribué à tous les confrères. Ne supprimez pas la provenance,\n"
              "  DÉ-IDENTIFIEZ-la — gardez le type de document et le nombre de réplicats, retirez\n"
              "  le client. Exemples :\n"
              "    « relevé <Client>.pdf »        -> « relevé <émetteur>, arrêté <période> »\n"
              "    « contrat AB123456 (Client X) » -> « contrat XX000001 (Client Exemple) »\n"
              "  Un snapshot de run client réel ne se dé-identifie pas : il se supprime.\n"
              "  Cf. seed/construire_bundle.py (même garde-fou côté seed).", file=sys.stderr)
        return 1

    print(f"Garde-fou D44 OK — aucun identifiant client dans le paquet (référence de contrat "
          f"{MOTIF_REFERENCE_CONTRAT.pattern}, ni l'un des {len(NOMS_CLIENTS)} noms de clients "
          f"connus), noms de fichiers compris. Les ISIN bien formés sont soustraits avant "
          f"recherche : DK0062498333 n'est pas une référence de contrat.")

    neuf = calculer()
    ancien = json.loads(MANIFESTE.read_text(encoding="utf-8")) if MANIFESTE.exists() else {}

    modifies = sorted(k for k in neuf if k in ancien and neuf[k] != ancien[k])
    ajoutes = sorted(set(neuf) - set(ancien))
    retires = sorted(set(ancien) - set(neuf))

    for titre, lot in (("MODIFIÉS", modifies), ("AJOUTÉS", ajoutes), ("RETIRÉS", retires)):
        if lot:
            print(f"{titre} :")
            for k in lot:
                print(f"    {k}")

    if not (modifies or ajoutes or retires):
        print(f"Aucun écart — le manifeste est à jour ({len(neuf)} fichiers).")
        return 0

    if "--verifier" in sys.argv:
        print("\nMode vérification : rien n'a été écrit.")
        return 1

    MANIFESTE.write_text(json.dumps(neuf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nManifeste régénéré : {len(neuf)} fichiers.")
    print("Relancez `python3 skill/p1_engine/selfcheck.py` pour confirmer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
