"""Install only Black-owned additions; preserve locally modified owned files."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def install(home, theme="keep", apply=False):
    target = home / ".config/hypr/derivative.conf"
    state = home / ".local/state/solace-black/managed-files.json"
    main = home / ".config/hypr/hyprland.conf"
    if not apply:
        print("Preview: install the Black include only if unchanged; preserve user overrides and current theme.")
        if theme == "black": print("Preview: register/select the optional inherited Black theme.")
        return
    if not main.is_file() or "source = ~/.config/hypr/derivative.conf" not in main.read_text():
        raise ValueError("The shared derivative/user include contract is missing. Review the upstream install; do not replace user Hyprland configuration automatically.")
    ledger = json.loads(state.read_text()) if state.exists() else {}
    key = ".config/hypr/derivative.conf"
    placeholder = b"# Reserved for an explicitly installed derivative. Empty in standard Solace.\n"
    if target.is_symlink():
        raise ValueError("Preserving a user-supplied derivative symlink; review integration manually")
    if target.exists() and target.read_bytes() != placeholder and digest(target.read_bytes()) != ledger.get(key):
        raise ValueError("Black include was locally customized; preserving it for manual review")
    data = (ROOT / "overlays/desktop/derivative.conf").read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    ledger[key] = digest(data)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(ledger, indent=2) + "\n")
    if theme == "keep": return

    base = home / ".local/share/solace/themes/solace"
    dest = home / ".config/solace/themes/solace-black"
    if not dest.exists():
        if not base.is_dir(): raise ValueError("Install shared Solace theme assets first")
        # Materialize inherited theme files at runtime, not a duplicate source tree.
        original = tomllib.loads((base / "colors.toml").read_text())
        palette = dict(original)
        palette.update(tomllib.loads((ROOT / "overlays/desktop/colors.toml").read_text()))
        aliases = {"bg": "background", "fg": "foreground", "light_fg": "foreground", "bright_fg": "foreground",
                   "selection": "selection_background", "dark_fg": "color8", "muted": "color8",
                   "red": "color1", "green": "color2", "yellow": "color3", "blue": "color4",
                   "magenta": "color5", "cyan": "color6", "bright_red": "color9", "bright_green": "color10",
                   "bright_yellow": "color11", "bright_blue": "color12", "bright_magenta": "color13", "bright_cyan": "color14"}
        for key, source in aliases.items(): palette[key] = palette[source]
        for key in ("lighter_bg", "dark_bg", "darker_bg"): palette[key] = palette["background"]
        replacements = {value.lower(): palette[key] for key, value in original.items()
                        if isinstance(value, str) and re.fullmatch(r"#[a-fA-F0-9]{6}", value) and key in palette}
        shutil.copytree(base, dest)
        for path in dest.rglob("*"):
            if not path.is_file() or path.is_symlink() or "backgrounds" in path.relative_to(dest).parts: continue
            try: text = path.read_text()
            except UnicodeError: continue
            path.write_text(re.sub(r"#[a-fA-F0-9]{6}", lambda m: replacements.get(m[0].lower(), m[0]), text))
        (dest / "colors.toml").write_text("\n".join(f"{key} = {json.dumps(value)}" for key, value in palette.items()) + "\n")
    # User explicitly requested selection. Ordinary reruns never select a theme.
    subprocess.run(["bash", str(home / ".local/share/solace/bin/solace-theme-set"), "solace-black"], check=True,
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
