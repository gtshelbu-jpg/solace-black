import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project = load("project", ROOT / "scripts/project.py")
desktop = load("desktop", ROOT / "scripts/install-desktop.py")


class FoundationTests(unittest.TestCase):
    def setUp(self):
        Path("/tmp/opencode").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="black-tests-", dir="/tmp/opencode")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "upstream"
        profile = self.source / "archiso/profile"
        profile.mkdir(parents=True)
        (self.source / "install.sh").write_text("#!/bin/bash\n")
        (self.source / "archiso/build.sh").write_text("#!/bin/bash\n")
        (self.source / "archiso/interface.json").write_text('{"version":1}')
        (profile / "profiledef.sh").write_text('iso_name="archlinux"\niso_publisher="Arch"\niso_application="Live"\n')
        (profile / "pacman.conf").write_text('[options]\nSigLevel = Required DatabaseOptional\nLocalFileSigLevel = Optional\n[core]\nInclude = /etc/pacman.d/mirrorlist\n[extra]\nInclude = /etc/pacman.d/mirrorlist\n')
        (profile / "packages.x86_64").write_text("base\narchinstall\ncalamares\ncage\nkcrash\n")
        unit = profile / "airootfs/etc/systemd/system/pacman-init.service"
        unit.parent.mkdir(parents=True)
        unit.write_text("[Service]\nExecStart=/usr/bin/pacman-key --populate\n")

    def test_black_profile_separates_build_live_and_target(self):
        before = (self.source / "archiso/profile/pacman.conf").read_bytes()
        dest = self.root / "black-profile"
        manifest = project.compose(self.source, dest, "solace-black", development=True)
        build = (dest / "pacman.conf").read_text()
        live = (dest / "airootfs/etc/pacman.conf").read_text()
        self.assertIn("Server = https://blackarch.org", build)
        self.assertIn("Include = /etc/pacman.d/blackarch-mirrorlist", live)
        self.assertNotIn("TrustAll", build + live)
        self.assertNotIn("LocalFileSigLevel = Optional", build + live)
        self.assertIn("[core]", live)
        self.assertIn("[extra]", live)
        self.assertIn("[multilib]", live)
        self.assertIn("blackarch-keyring", manifest["packages"])
        self.assertNotIn("calamares", manifest["packages"])
        self.assertNotIn("nmap", manifest["packages"])
        self.assertTrue(manifest["upstream"]["development"])
        self.assertTrue((dest / "airootfs/usr/share/solace/variant-stage-target").is_file())
        self.assertTrue((dest / "airootfs/usr/share/solace/build-manifest.json").is_file())
        self.assertIn("--populate archlinux blackarch", (dest / "airootfs/etc/systemd/system/pacman-init.service").read_text())
        self.assertEqual(before, (self.source / "archiso/profile/pacman.conf").read_bytes())

    def test_standard_variant_does_not_get_black_repository_or_hook(self):
        dest = self.root / "base-profile"
        manifest = project.compose(self.source, dest, "solace", development=True)
        self.assertIn("calamares", manifest["packages"])
        self.assertNotIn("blackarch-keyring", manifest["packages"])
        self.assertNotIn("[blackarch]", (dest / "pacman.conf").read_text())
        self.assertFalse((dest / "airootfs/usr/share/solace/variant-stage-target").exists())

    def test_existing_profile_output_is_preserved(self):
        dest = self.root / "existing"
        dest.mkdir(); (dest / "mine").write_text("user data")
        with self.assertRaises(ValueError): project.compose(self.source, dest, "solace-black", True)
        self.assertEqual((dest / "mine").read_text(), "user data")

    def test_unpublished_interface_and_unpinned_releases_fail_closed(self):
        with self.assertRaises(ValueError): project.validate_upstream(self.source)
        (self.source / "archiso/interface.json").unlink()
        with self.assertRaises(ValueError): project.validate_upstream(self.source, True)

    def test_implicit_local_package_repo_is_rejected(self):
        repo = self.source / "archiso/localrepo"
        repo.mkdir(); (repo / "untrusted.pkg.tar.zst").write_text("not a package")
        with self.assertRaises(ValueError): project.compose(self.source, self.root / "out", "solace-black", True)

    def test_desktop_include_preserves_user_edits_and_shortcuts(self):
        home = self.root / "home"
        config = home / ".config/hypr"
        config.mkdir(parents=True)
        main = config / "hyprland.conf"
        main.write_text("source = ~/.config/hypr/derivative.conf\nsource = ~/.config/hypr/user.conf\n")
        original = main.read_bytes()
        include = config / "derivative.conf"
        include.write_text("# Reserved for an explicitly installed derivative. Empty in standard Solace.\n")
        desktop.install(home, apply=True)
        desktop.install(home, apply=True)
        self.assertNotIn("bind", "\n".join(l for l in include.read_text().splitlines() if not l.startswith("#")))
        self.assertEqual(main.read_bytes(), original)
        include.write_text("# my customization\n")
        with self.assertRaises(ValueError): desktop.install(home, apply=True)
        self.assertEqual(include.read_text(), "# my customization\n")

    def test_desktop_preview_is_write_free(self):
        home = self.root / "empty-home"
        desktop.install(home)
        self.assertFalse(home.exists())

    def test_install_dry_run_never_executes_privileged_or_network_commands(self):
        home = self.root / "home"
        home.mkdir()
        stubs = self.root / "bin"
        stubs.mkdir()
        for cmd in ["sudo", "curl", "pacman"]:
            p = stubs / cmd
            p.write_text("#!/bin/bash\necho 'Unexpected real operation' >&2\nexit 99\n")
            p.chmod(0o755)
        env = {**os.environ, "HOME": str(home), "PATH": str(stubs) + ":" + os.environ["PATH"]}
        p = subprocess.run(["bash", str(ROOT / "install.sh"), "--dry-run", "--with", "web"], env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("blackarch-repo.sh", p.stderr)
        self.assertIn("ffuf", p.stderr)
        self.assertFalse(any(home.iterdir()))

    def test_bootstrap_default_is_a_preview(self):
        p = subprocess.run(["bash", str(ROOT / "bootstrap/blackarch-repo.sh")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn("Preview", p.stdout)
        checksum = (ROOT / "bootstrap/strap.sha256").read_text().strip()
        self.assertRegex(checksum, r"^[a-f0-9]{64}$")

    def test_local_fetch_resolves_source_before_git_changes_directory(self):
        pinned = json.loads((ROOT / "upstream.lock.json").read_text())
        (self.root / "upstream.lock.json").write_text(json.dumps(pinned))
        calls = []
        def fake_run(*args, **kwargs):
            calls.append(args)
            if args[:3] == ("git", "init", "-q"): Path(args[3]).mkdir()
        with patch.object(project, "ROOT", self.root), patch.object(project, "run", fake_run), \
             patch.object(project, "git_value", return_value=pinned["solace"]["commit"]), \
             patch("os.getcwd", return_value=str(self.root)):
            dest = project.fetch("upstream")
        fetch = next(args for args in calls if len(args) > 3 and args[3] == "fetch")
        self.assertEqual(fetch[5], str(self.source.resolve()))
        self.assertTrue(dest.is_dir())


if __name__ == "__main__": unittest.main()
