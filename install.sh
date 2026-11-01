#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${SOLACE_BASE:-/opt/solace}"
DRY=0
APPLY=0
DESKTOP_ONLY=0
THEME=keep
GROUPS_SELECTED=(core)
BASE_ARGS=()
usage() {
  cat <<'EOF'
Usage: bash install.sh [--dry-run|--apply] [options]
  --base-path PATH       Embedded/pinned Solace source (default /opt/solace)
  --with core|web|wireless|assist  Optional native groups (core selected initially)
  --desktop-only         Register Black desktop additions; no base/packages/repos
  --theme keep|black     Keep current selection by default; black is explicit
  --lid-policy POLICY   Pass the chosen policy to the shared Solace installer
  --no-tablet           Pass through the shared installer's tablet choice

Without --apply, a real install requires an interactive confirmation. --dry-run
never invokes sudo, downloads a bootstrap or changes desktop configuration.
No disk partitioning, Secure Boot enrollment or network profiles are configured.
EOF
}
while (( $# )); do
  case "$1" in
    --dry-run) DRY=1; shift;;
    --apply) APPLY=1; shift;;
    --desktop-only) DESKTOP_ONLY=1; shift;;
    --base-path|--theme|--with|--lid-policy)
      (( $# >= 2 )) || { echo "$1 needs a value" >&2; exit 1; }
      case "$1" in
        --base-path) BASE="$2";;
        --theme) case "$2" in keep|black) THEME="$2";; *) exit 1;; esac;;
        --with) case "$2" in core|web|wireless|assist) GROUPS_SELECTED+=("$2");; *) echo 'Unknown tool group' >&2; exit 1;; esac;;
        --lid-policy) case "$2" in docked|suspend|awake|keep) BASE_ARGS+=(--lid-policy "$2");; *) exit 1;; esac;;
      esac
      shift 2;;
    --no-tablet) BASE_ARGS+=(--no-tablet); shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done
if (( ! DRY )); then
  (( EUID != 0 )) || { echo 'Run as the target desktop user, not root.' >&2; exit 1; }
  if (( ! APPLY )); then
    [[ -t 0 ]] || { echo 'Non-interactive installs require --apply.' >&2; exit 1; }
    echo 'This installs the Solace desktop, enables BlackArch, and installs the selected native tools.'
    read -r -p 'Type INSTALL to continue: ' confirmation
    [[ $confirmation == INSTALL ]] || exit 1
  fi
  [[ -f "$BASE/archiso/interface.json" ]] || { echo 'Solace derivative interface 1 is required; review/publish/pin the upstream changes first.' >&2; exit 1; }
fi
step() {
  printf 'Plan:' >&2
  printf ' %q' "$@" >&2
  printf '\n' >&2
  if (( ! DRY )); then "$@"; fi
}
if (( ! DESKTOP_ONLY )); then
  step bash "$BASE/install.sh" "${BASE_ARGS[@]}"
  step sudo bash "$ROOT/bootstrap/blackarch-repo.sh" --apply
  mapfile -t packages < <(python3 - "$ROOT" "${GROUPS_SELECTED[@]}" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1]); sys.path.insert(0, str(root / "scripts"))
from project import package_lines
packages = set()
for group in sys.argv[2:]:
    packages.update(package_lines(root / "packages/target" / (group + ".txt")))
print("\n".join(sorted(packages)))
PY
  )
  # Availability is checked before requesting a package transaction. No --overwrite.
  step pacman -Si -- "${packages[@]}"
  step sudo pacman -Syu --needed -- "${packages[@]}"
fi
desktop_args=(--theme "$THEME")
if (( DRY )); then desktop_args+=(--dry-run); else desktop_args+=(--apply); fi
step python3 "$ROOT/scripts/install-desktop.py" "${desktop_args[@]}"
echo 'Black foundation finished. No launcher/assisted-shell shortcuts are enabled. Assist requires an explicitly selected, available signed package.'
