"""Register Black's optional theme from shared templates, never user dotfiles."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def palette_for(base):
    palette = tomllib.loads((base / "colors.toml").read_text())
    palette.update(tomllib.loads((ROOT / "overlays/desktop/colors.toml").read_text()))
    aliases = {"bg": "background", "fg": "foreground", "light_fg": "foreground",
               "bright_fg": "color15", "selection": "selection_background",
               "red": "color1", "green": "color2", "yellow": "color3", "blue": "color4",
               "magenta": "color5", "cyan": "color6", "bright_red": "color9",
               "bright_green": "color10", "bright_yellow": "color11", "bright_blue": "color12",
               "bright_magenta": "color13", "bright_cyan": "color14"}
    for key, value in aliases.items():
        palette[key] = palette[value]
    for key, value in palette.items():
        if key != "mode" and not re.fullmatch(r"#[a-fA-F0-9]{6}", value):
            raise ValueError(f"Invalid palette color: {key}")
    return palette


def render(text, palette):
    values = dict(palette)
    for key, value in palette.items():
        if not value.startswith("#"):
            continue
        values[key + "_strip"] = value[1:]
        values[key + "_rgb"] = ",".join(str(int(value[i:i+2], 16)) for i in (1, 3, 5))
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: values[m[1]], text)


def register(home, apply=False):
    share = home / ".local/share/solace"
    base = share / "themes/solace"
    templates = share / "default/themed"
    dest = home / ".config/solace/themes/solace-black"
    if not apply:
        print("Preview: register Solace Black palette, shared theme outputs and static wallpaper; do not select it.")
        return dest
    if dest.exists() or dest.is_symlink():
        raise ValueError("Existing Solace Black theme is preserved; review it before re-registering")
    if not base.is_dir() or not templates.is_dir():
        raise ValueError("Install shared Solace themes/templates first")
    if not (templates / "hyprland.lua.tpl").is_file():
        raise ValueError("Update shared Solace templates for Lua palette support first")
    palette = palette_for(base)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Render in a fresh sibling; partial output is never offered as a theme.
    with tempfile.TemporaryDirectory(prefix=".solace-black-", dir=dest.parent) as temp:
        staged = Path(temp) / "theme"
        shutil.copytree(base, staged, symlinks=False)
        original = tomllib.loads((base / "colors.toml").read_text())
        replacements = {value.lower(): palette[key] for key, value in original.items()
                        if isinstance(value, str) and re.fullmatch(r"#[a-fA-F0-9]{6}", value) and key in palette}
        for key in ("background", "foreground", "accent"):
            replacements[original[key].lower()] = palette[key]
        for path in staged.rglob("*"):
            if not path.is_file() or "backgrounds" in path.relative_to(staged).parts:
                continue
            try:
                text = path.read_text()
            except UnicodeError:
                continue
            path.write_text(re.sub(r"#[a-fA-F0-9]{6}", lambda m: replacements.get(m[0].lower(), m[0]), text))
        # Backgrounds are a Black-owned original, not inherited copies.
        backgrounds = staged / "backgrounds"
        if backgrounds.exists():
            shutil.rmtree(backgrounds)
        backgrounds.mkdir()
        (staged / "colors.toml").write_text("\n".join(f"{k} = {json.dumps(v)}" for k, v in palette.items()) + "\n")
        # Regenerate ALL shared outputs: textual replacement misses rgba/ANSI
        # forms and duplicate semantic colors in inherited Aether files.
        for template in sorted(templates.glob("*.tpl")):
            (staged / template.name.removesuffix(".tpl")).write_text(render(template.read_text(), palette))
        (staged / "icons.theme").write_text("Adwaita\n")
        (staged / "appearance-only").write_text("Select palette/CSS without resetting unrelated application preferences.\n")
        # Theme-specific widget accents, without changing the user's bar layout.
        with (staged / "waybar.css").open("a") as handle:
            handle.write(render('\n@define-color accent {{ accent }};\n#workspaces button.active { color: @accent; }\n#custom-solace { color: @accent; }\n', palette))
        # Lock layout/logo dimensions remain user-owned; only colors change.
        (staged / "hyprlock.conf").write_text(render(
            '$color = rgba({{ background_rgb }}, 1)\n$inner_color = rgba({{ background_rgb }}, 0.8)\n'
            '$outer_color = rgba({{ accent_rgb }}, 1)\n$font_color = rgba({{ foreground_rgb }}, 1)\n'
            '$muted_color = rgba({{ foreground_rgb }}, 0.72)\n$check_color = rgba({{ green_rgb }}, 1)\n'
            '$fail_color = rgba({{ red_rgb }}, 1)\n', palette))
        subprocess.run(["magick", "-background", "none", str(ROOT / "overlays/desktop/wallpaper.svg"),
                        str(backgrounds / "solace-black.png")], check=True)
        staged.rename(dest)
    return dest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Register files only; theme selection is separate")
    args = parser.parse_args()
    try:
        print(register(Path.home(), args.apply))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"ERROR: {error}\n")
