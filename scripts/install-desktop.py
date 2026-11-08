"""Install only Black-owned additions; preserve locally modified owned files."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def install(home, theme="keep", apply=False):
    native = (home / ".config/hypr/hyprland.lua").is_file()
    extension = "lua" if native else "conf"
    target = home / (".config/hypr/derivative." + extension)
    state = home / ".local/state/solace-black/managed-files.json"
    main = home / (".config/hypr/hyprland." + extension)
    if not apply:
        print("Preview: install the Black include only if unchanged; preserve user overrides and current theme.")
        if theme == "black": print("Preview: register/select the optional inherited Black theme.")
        return
    contract = ('dofile(os.getenv("HOME") .. "/.config/hypr/derivative.lua")' if native
                else "source = ~/.config/hypr/derivative.conf")
    if not main.is_file() or contract not in main.read_text():
        raise ValueError("The shared derivative/user include contract is missing. Review the upstream install; do not replace user Hyprland configuration automatically.")
    ledger = json.loads(state.read_text()) if state.exists() else {}
    key = ".config/hypr/derivative." + extension
    placeholder = ("--" if native else "#").encode() + b" Reserved for an explicitly installed derivative. Empty in standard Solace.\n"
    if target.is_symlink():
        raise ValueError("Preserving a user-supplied derivative symlink; review integration manually")
    if target.exists() and target.read_bytes() != placeholder and digest(target.read_bytes()) != ledger.get(key):
        raise ValueError("Black include was locally customized; preserving it for manual review")
    data = (ROOT / ("overlays/desktop/derivative." + extension)).read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    ledger[key] = digest(data)
    guide = home / ".local/share/solace/learn/solace-black.md"
    guide_key = ".local/share/solace/learn/solace-black.md"
    guide_data = (ROOT / "docs/learn/solace-black.md").read_bytes()
    if guide.is_symlink() or (guide.exists() and digest(guide.read_bytes()) != ledger.get(guide_key)):
        print("Preserving locally customized Black Learn guide.", file=sys.stderr)
    else:
        guide.parent.mkdir(parents=True, exist_ok=True)
        guide.write_bytes(guide_data)
        ledger[guide_key] = digest(guide_data)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(ledger, indent=2) + "\n")
    if theme == "keep": return

    dest = home / ".config/solace/themes/solace-black"
    if not dest.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/theme.py"), "--apply"], check=True,
                       env={**os.environ, "HOME": str(home)})
    # User explicitly requested selection. Ordinary reruns never select a theme.
    subprocess.run(["bash", str(home / ".local/share/solace/bin/solace-theme-set"), "--appearance-only", "solace-black"], check=True,
                   env={**os.environ, "HOME": str(home), "SOLACE_PATH": str(home / ".local/share/solace")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--apply", action="store_true")
    actions.add_argument("--dry-run", action="store_true")
    parser.add_argument("--theme", choices=["keep", "black"], default="keep")
    args = parser.parse_args()
    try: install(Path.home(), args.theme, args.apply)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr); sys.exit(1)
