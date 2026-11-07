import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("black_theme", ROOT / "scripts/theme.py")
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="black-theme-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        share = self.home / ".local/share/solace"
        self.base = share / "themes/solace"
        self.base.mkdir(parents=True)
        (self.base / "colors.toml").write_text('background = "#00020a"\nforeground = "#ffffff"\naccent = "#3b6aa5"\n')
        (self.base / "inherited.json").write_text('{"background":"#00020a","accent":"#3b6aa5"}')
        (self.base / "backgrounds").mkdir()
        (self.base / "backgrounds/old.png").write_bytes(b"old wallpaper")
        templates = share / "default/themed"
        templates.mkdir(parents=True)
        (templates / "hyprland.lua.tpl").write_text('hl.config({ general = { col = { active_border = "rgb({{ accent_strip }})" } } })\n')
        (templates / "alacritty.toml.tpl").write_text('background = "{{ background }}"\nforeground = "{{ foreground }}"\n')
        (templates / "waybar.css.tpl").write_text('@define-color background {{ background }};\n')

    def fake_magick(self, args, **kwargs):
        self.assertEqual(args[0], "magick")
        Path(args[-1]).write_bytes(b"rendered wallpaper")

    def test_preview_is_write_free(self):
        with patch.object(theme.subprocess, "run") as run:
            dest = theme.register(self.home)
        self.assertFalse(dest.exists())
        run.assert_not_called()

    def test_register_renders_palette_and_original_wallpaper_without_selecting(self):
        old = (self.base / "colors.toml").read_bytes()
        with patch.object(theme.subprocess, "run", side_effect=self.fake_magick):
            dest = theme.register(self.home, apply=True)
        self.assertEqual((self.base / "colors.toml").read_bytes(), old)
        self.assertIn('#101017', (dest / "alacritty.toml").read_text())
        self.assertIn('b4a1e8', (dest / "hyprland.lua").read_text())
        self.assertNotIn('{{', (dest / "hyprlock.conf").read_text())
        self.assertIn('180,161,232', (dest / "hyprlock.conf").read_text())
        self.assertEqual(json.loads((dest / "inherited.json").read_text())["accent"], "#b4a1e8")
        self.assertEqual([p.name for p in (dest / "backgrounds").iterdir()], ["solace-black.png"])
        self.assertTrue((dest / "appearance-only").is_file())
        self.assertFalse((self.home / ".config/solace/current").exists())

    def test_existing_theme_is_preserved(self):
        with patch.object(theme.subprocess, "run", side_effect=self.fake_magick):
            dest = theme.register(self.home, apply=True)
        (dest / "personal.txt").write_text("my tweaks")
        with self.assertRaises(ValueError):
            theme.register(self.home, apply=True)
        self.assertEqual((dest / "personal.txt").read_text(), "my tweaks")

    def test_failed_renderer_does_not_publish_partial_theme(self):
        with patch.object(theme.subprocess, "run", side_effect=OSError("missing renderer")):
            with self.assertRaises(OSError):
                theme.register(self.home, apply=True)
        self.assertFalse((self.home / ".config/solace/themes/solace-black").exists())

    def test_semantic_shades_remain_distinct(self):
        palette = theme.palette_for(self.base)
        self.assertEqual(palette["bg"], palette["background"])
        self.assertNotEqual(palette["lighter_bg"], palette["background"])
        self.assertNotEqual(palette["dark_bg"], palette["background"])
