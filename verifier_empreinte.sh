#!/usr/bin/env bash
# Protocole de merge (M6) — isole EXACTEMENT les fichiers touchés par le fork.
#
#   ./verifier_empreinte.sh            compare l'état courant à la baseline
#   ./verifier_empreinte.sh --record   (ré)enregistre la baseline  [ouverture du fork uniquement]
#
# La baseline fixe l'état du paquet à l'OUVERTURE du fork. Ne la régénérez pas
# après une modification : elle perdrait sa raison d'être, qui est de dire ce qui
# a bougé depuis. Les caches Python sont exclus — ce n'est pas de la source.
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$ICI/skill"
BASE="$ICI/BASELINE_MD5.txt"

empreinte() {
    cd "$SKILL"
    find . -type f \
        -not -path '*/__pycache__/*' -not -name '*.pyc' \
        -print0 | sort -z | xargs -0 md5sum
}

if [[ "${1:-}" == "--record" ]]; then
    empreinte > "$BASE"
    echo "Baseline enregistrée : $(wc -l < "$BASE") fichiers."
    exit 0
fi

if [[ ! -f "$BASE" ]]; then
    echo "Aucune baseline. Lancez : $0 --record" >&2
    exit 2
fi

TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
empreinte > "$TMP"

# Comparaison par nom de fichier : modifiés, ajoutés, supprimés.
MODIFIES=$(join -j 2 -o 1.1,2.1,0 \
    <(sort -k2 "$BASE" | grep -v '__pycache__') \
    <(sort -k2 "$TMP") 2>/dev/null | awk '$1!=$2 {print $3}')
AJOUTES=$(comm -13 <(awk '{print $2}' "$BASE" | sort) <(awk '{print $2}' "$TMP" | sort))
SUPPRIMES=$(comm -23 <(awk '{print $2}' "$BASE" | sort) <(awk '{print $2}' "$TMP" | sort))

afficher() { [[ -n "$2" ]] && { echo "$1"; echo "$2" | sed 's/^/    /'; } || true; }

afficher "MODIFIÉS :"  "$MODIFIES"
afficher "AJOUTÉS :"   "$AJOUTES"
afficher "SUPPRIMÉS :" "$SUPPRIMES"

if [[ -z "$MODIFIES$AJOUTES$SUPPRIMES" ]]; then
    echo "Aucun écart : le fork est identique à sa baseline."
fi

echo
echo "Rappel : la divergence SÉMANTIQUE ne se lit pas ici mais dans REGISTRE_ECARTS.md."
