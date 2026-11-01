#!/bin/bash
# Sourced helper; no actions merely from loading this file.

blackarch_repair_inherited_mirrorlist() {
  local config="$1" mirrors="$2"
  [[ -f "$config" ]] || { echo 'Missing Pacman configuration; review it manually.' >&2; return 1; }
  if [[ -e "$mirrors" || -L "$mirrors" ]]; then
    [[ -f "$mirrors" && ! -L "$mirrors" && -r "$mirrors" && -s "$mirrors" ]] || {
      echo 'Existing BlackArch mirror list is empty, unreadable or not a regular file; preserving it for review.' >&2
      return 1
    }
    return 0
  fi
  # Repair only our canonical active Include, not arbitrary custom repository paths.
  if awk '
    /^[[:space:]]*\[/ { black = ($0 ~ /^[[:space:]]*\[blackarch\][[:space:]]*(#.*)?$/) }
    black && /^[[:space:]]*Include[[:space:]]*=[[:space:]]*\/etc\/pacman\.d\/blackarch-mirrorlist[[:space:]]*(#.*)?$/ { found = 1 }
    END { exit !found }
  ' "$config"; then
    # Never overwrite a file created concurrently. The parent must already exist.
    (set -o noclobber; umask 022
      printf '%s\n' 'Server = https://blackarch.org/blackarch/blackarch/os/$arch' > "$mirrors"
    ) || return 1
    echo 'Restored the missing mirror list referenced by the inherited BlackArch configuration.'
  fi
}
