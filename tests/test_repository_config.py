from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = '[blackarch]\nSigLevel = Required DatabaseOptional TrustedOnly\nInclude = /etc/pacman.d/blackarch-mirrorlist\n'


class RepositoryConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="black-repo-config-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "pacman.conf"
        self.mirrors = self.root / "blackarch-mirrorlist"

    def repair(self, content=CANONICAL):
        self.config.write_text(content)
        result = subprocess.run([
            "bash", "-euc", 'source "$1"; blackarch_repair_inherited_mirrorlist "$2" "$3"',
            "fixture", str(ROOT / "bootstrap/repository-config.sh"), str(self.config), str(self.mirrors),
        ], capture_output=True, text=True)
        self.assertEqual(self.config.read_text(), content)
        return result

    def test_inherited_include_is_repaired_without_altering_signature_policy(self):
        result = self.repair()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.mirrors.read_text(), 'Server = https://blackarch.org/blackarch/blackarch/os/$arch\n')
        self.assertEqual(self.mirrors.stat().st_mode & 0o777, 0o644)

    def test_existing_custom_mirrors_are_preserved(self):
        self.mirrors.write_text("# my custom mirror selection\nServer = https://mirror.example.test/$arch\n")
        before = self.mirrors.read_bytes()
        self.assertEqual(self.repair().returncode, 0)
        self.assertEqual(self.mirrors.read_bytes(), before)

    def test_inactive_foreign_and_custom_includes_are_not_adopted(self):
        for content in ('[core]\n', '#[blackarch]\n#Include = /etc/pacman.d/blackarch-mirrorlist\n',
                        '[other]\nInclude = /etc/pacman.d/blackarch-mirrorlist\n',
                        '[blackarch]\nInclude = /custom/mirrors\n'):
            with self.subTest(content=content):
                self.assertEqual(self.repair(content).returncode, 0)
                self.assertFalse(self.mirrors.exists())

    def test_empty_existing_file_is_not_overwritten(self):
        self.mirrors.touch()
        self.assertNotEqual(self.repair().returncode, 0)
        self.assertEqual(self.mirrors.read_bytes(), b"")

    def test_symlink_is_refused_and_its_target_preserved(self):
        target = self.root / "user-file"
        target.write_text("preserve me")
        self.mirrors.symlink_to(target)
        self.assertNotEqual(self.repair().returncode, 0)
        self.assertEqual(target.read_text(), "preserve me")


if __name__ == "__main__":
    unittest.main()
