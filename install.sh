#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
shopt -s nullglob
installers=("$root"/*/install.sh)
if ((${#installers[@]} == 0)); then
    printf 'No utility installers found.\n' >&2
    exit 1
fi
if [[ ! -t 0 || ! -t 1 ]]; then
    printf 'The installer menu requires an interactive terminal. Run: bash install.sh\n' >&2
    exit 1
fi

selected=()
for i in "${!installers[@]}"; do selected[$i]=1; done
current=0
message=''
restore_terminal() { printf '\033[?25h\033[?1049l'; }
trap restore_terminal EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
printf '\033[?1049h\033[?25l'
while true; do
    printf '\033[H\033[2Jcachy-qol installers\n\n'
    for i in "${!installers[@]}"; do
        directory="${installers[$i]%/install.sh}"
        marker=' '; checkbox=' '
        if ((i == current)); then marker='>'; fi
        if [[ "${selected[$i]}" == 1 ]]; then checkbox='x'; fi
        printf ' %s [%s] %s\n' "$marker" "$checkbox" "${directory##*/}"
    done
    printf '\nUp/Down: move | Space: toggle | A: select all | Enter: install | Q: quit\n'
    printf '%s\n' "$message"
    key=''
    if ! IFS= read -r -s -n 1 key; then exit 0; fi
    case "$key" in
        $'\033')
            sequence=''
            IFS= read -r -s -n 2 -t 0.2 sequence || true
            case "$sequence" in
                '[A'|'OA') current=$(((current + ${#installers[@]} - 1) % ${#installers[@]})) ;;
                '[B'|'OB') current=$(((current + 1) % ${#installers[@]})) ;;
            esac
            ;;
        ' ') selected[$current]=$((1 - selected[current])); message='' ;;
        a|A) for i in "${!installers[@]}"; do selected[$i]=1; done; message='' ;;
        q|Q) exit 0 ;;
        '')
            count=0
            for i in "${!installers[@]}"; do count=$((count + selected[i])); done
            if ((count > 0)); then break; fi
            message='Select at least one utility, or press Q to quit.'
            ;;
    esac
done
restore_terminal
trap - EXIT INT TERM
for i in "${!installers[@]}"; do
    if [[ "${selected[$i]}" == 1 ]]; then
        directory="${installers[$i]%/install.sh}"
        printf '\nInstalling %s...\n' "${directory##*/}"
        (cd -- "$directory" && bash ./install.sh)
    fi
done
printf '\nSelected utilities installed.\n'
