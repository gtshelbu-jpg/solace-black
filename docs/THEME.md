# Solace Black theme

An optional charcoal, silver and muted-violet appearance. Warning/error red is
kept distinct. The original geometric wallpaper is static; the theme adds no
animations, blur effects, background services or keybindings.

## Register and select

Install the pinned shared Solace assets first, including native Lua palette
templates. Registration uses those templates and the Black palette rather than
shipping a duplicate Solace theme tree. ImageMagick renders the original SVG
wallpaper into a native-resolution-independent 3840×2160 PNG once at registration.

```bash
# Preview only: no writes or theme changes.
python3 scripts/theme.py

# Register only; leaves the current selection untouched.
python3 scripts/theme.py --apply

# Select through the normal shared theme system.
solace-theme-set --appearance-only solace-black

# Return to the standard named theme.
solace-theme-set --appearance-only solace
```

The desktop installer also supports `--theme black`; `--theme keep` remains the
default. An existing `~/.config/solace/themes/solace-black` is never overwritten by
registration. Keep personal theme adjustments there; review or rename an older
theme explicitly before rebuilding its generated assets.

## Coverage

- Shared terminal palettes (Alacritty, Foot, Kitty and Ghostty); Starship and tmux
  follow their ANSI colours without replacing shell configuration or keybindings.
- Waybar colours and active-workspace accents, retaining the user's bar layout.
- btop's generated `current` palette and Impala's application theme. Solace-launched
  Bluetui receives a terminal-local ANSI accent override; its upstream version
  does not expose a native theme configuration API. Warning/error colours remain
  distinct, and the palette override is restored when that dedicated TUI exits.
- Walker, Mako, swayosd, GTK CSS and shared editor/tool palette outputs.
- Hyprland active borders, lock-screen colours and a dedicated original wallpaper.

Only supported applications following the shared theme includes change. The
appearance-only marker avoids file-manager preference resets, editor extension
installation and privileged browser/peripheral integration. It does not install
applications or force all third-party applications to support the theme.

SDDM and boot visuals are separate, system-wide contexts: selecting a user theme
does not change them. Display scale, lock-logo dimensions, personal overrides and
shortcuts are not theme settings. A running locker keeps its already-loaded
appearance until the next lock; theme selection never terminates the locker.

## Hyprland configuration formats

Shared generation provides both `hyprland.conf` and `hyprland.lua` palette outputs.
Lua configurations must load the generated Lua file (and the generated
`gum.env.lua` environment include) on reload; freezing palette values in a
one-time conversion prevents later theme changes from working.

These palette templates do **not** migrate an entire legacy Hyprland configuration.
Hyprland 0.57+ requires a fully converted Lua configuration; renaming `.conf` or
installing a colour theme alone is not a compatibility repair. Full modular
configuration and runtime-helper migration remains a separate validation task.

## Checks

Tests cover palette semantics, shared-output regeneration, write-free previews,
preservation of existing themes and renderer-failure boundaries. Validate actual
generated Lua with the target compositor before selection, then check terminal,
bar, launcher and notification logs plus an actual desktop screenshot. Do not
infer graphical compatibility merely from a successful file copy.
