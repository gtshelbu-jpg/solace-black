import gzip
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("assist_install", ROOT / "scripts/install-assist.py")
assist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assist)


class AssistInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="assist-install-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.lock = assist.load_lock()

    def test_preview_does_not_fetch_build_or_create_state(self):
        with patch.object(assist.subprocess, "run") as run, patch.object(assist.subprocess, "check_output") as output:
            assist.install(self.home)
        run.assert_not_called()
        output.assert_not_called()
        self.assertEqual(list(self.home.iterdir()), [])

    def test_local_policy_does_not_bypass_required_signatures_or_trust(self):
        assist.check_policy("PackageOptional\nPackageTrustedOnly\n")
        for policy in ("PackageRequired PackageTrustedOnly", "PackageOptional PackageTrustAll", "PackageNever"):
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                assist.check_policy(policy)

    def fake_git(self, source, *args):
        values = {
            ("rev-parse", "HEAD"): self.lock["commit"].encode(),
            ("status", "--porcelain"): b"",
            ("show", "HEAD:pyproject.toml"): f'[project]\nversion = "{self.lock["version"]}"\n'.encode(),
            ("show", "-s", "--format=%ct", "HEAD"): b"1234",
            ("archive", "--format=tar", f'--prefix=solace-assist-{self.lock["version"]}/', "HEAD"): b"fixture archive",
            ("show", "HEAD:packaging/arch/PKGBUILD.in"): b"pkgver=@VERSION@\nsha256sums=('@SHA256@')\n",
        }
        return values[args]

    def test_preparation_verifies_archive_before_writing_recipe(self):
        output = self.home / "package"
        with patch.object(assist, "git", side_effect=self.fake_git):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                assist.prepare(self.home, output, self.lock)
            self.assertFalse(output.exists())
            data = io.BytesIO()
            with gzip.GzipFile(fileobj=data, mode="wb", filename="", mtime=1234) as stream:
                stream.write(b"fixture archive")
            self.lock["source_sha256"] = hashlib.sha256(data.getvalue()).hexdigest()
            assist.prepare(self.home, output, self.lock)
        self.assertIn(self.lock["source_sha256"], (output / "PKGBUILD").read_text())
        self.assertEqual((output / "SOURCE_COMMIT").read_text().strip(), self.lock["commit"])

    def test_modified_or_wrong_revision_source_is_preserved(self):
        for output in (b"wrong revision", self.lock["commit"].encode()):
            with patch.object(assist, "git", side_effect=[output, b" M pyproject.toml"]):
                with self.assertRaises(ValueError):
                    assist.prepare(self.home, self.home / "package", self.lock)
        self.assertFalse((self.home / "package").exists())

    def test_strict_policy_stops_before_fetch_or_package_changes(self):
        with patch.object(assist.os, "geteuid", return_value=1000), \
             patch.object(assist.shutil, "which", return_value="/usr/bin/tool"), \
             patch.object(assist.subprocess, "check_output", return_value="PackageRequired PackageTrustedOnly"), \
             patch.object(assist.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                assist.install(self.home, apply=True)
        run.assert_not_called()
        self.assertEqual(list(self.home.iterdir()), [])

    def test_verified_local_source_build_uses_unprivileged_makepkg_with_tests(self):
        with patch.object(assist.os, "geteuid", return_value=1000), \
             patch.object(assist.shutil, "which", return_value="/usr/bin/tool"), \
             patch.object(assist.subprocess, "check_output", return_value="PackageOptional PackageTrustedOnly"), \
             patch.object(assist, "prepare", return_value=self.home / "package") as prepare, \
             patch.object(assist.subprocess, "run") as run:
            assist.install(self.home, apply=True, source=self.home)
        prepare.assert_called_once()
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0][:4], ["sudo", "pacman", "-S", "--needed"])
        self.assertIn("python-textual>=8.2.8", commands[0])
        self.assertEqual(commands[1], ["makepkg", "--syncdeps", "--install", "--noconfirm"])

    def test_tools_only_source_plan_skips_shared_and_bootstrap(self):
        result = subprocess.run(["bash", str(ROOT / "install.sh"), "--dry-run", "--tools-only", "--assist-source-build"],
                                env={**os.environ, "HOME": str(self.home)}, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("install-assist.py --apply", result.stderr)
        self.assertNotIn("blackarch-repo.sh", result.stderr)
        self.assertNotIn("/opt/solace/install.sh", result.stderr)
        self.assertNotIn("-- solace-assist", result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_desktop_only_rejects_source_build_instead_of_silently_ignoring(self):
        result = subprocess.run(["bash", str(ROOT / "install.sh"), "--dry-run", "--desktop-only", "--assist-source-build"], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be combined", result.stderr)


if __name__ == "__main__":
    unittest.main()
