#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ${1:-} != "--apply" || $# != 1 ]]; then
  echo 'Preview: download the pinned official BlackArch bootstrap, verify SHA256, then execute its verified keyring setup.'
  echo 'To configure THIS target system explicitly: sudo bash bootstrap/blackarch-repo.sh --apply'
  exit 0
fi
(( EUID == 0 )) || { echo 'Run the explicit --apply action as root.' >&2; exit 1; }
[[ -f /etc/arch-release ]] || { echo 'Arch Linux is required.' >&2; exit 1; }
# Root-owned temporary directory; do not execute a mutable download from a user cache.
work="$(mktemp -d -t solace-black-bootstrap.XXXXXXXX)"
trap 'rm -rf -- "$work"' EXIT
curl --proto '=https' --tlsv1.2 --fail --location --output "$work/strap.sh" https://blackarch.org/strap.sh
expected="$(tr -d '\n' <"$ROOT/bootstrap/strap.sha256")"
[[ $expected =~ ^[a-f0-9]{64}$ ]] || { echo 'Invalid bootstrap checksum' >&2; exit 1; }
printf '%s  %s\n' "$expected" "$work/strap.sh" | sha256sum --check --status
source "$ROOT/bootstrap/repository-config.sh"
blackarch_repair_inherited_mirrorlist /etc/pacman.conf /etc/pacman.d/blackarch-mirrorlist
# The reviewed upstream script verifies the keyring package's signature against
# its pinned signer fingerprints. Never insert SigLevel=Never/TrustAll here.
bash "$work/strap.sh"
pacman-conf --repo-list | grep -qx blackarch
echo 'BlackArch setup completed. Review multilib selection before installing tools.'
