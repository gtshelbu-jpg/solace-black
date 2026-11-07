"""Explicit native source-build path for Assist; never changes Pacman trust."""

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = ["base-devel", "python-build", "python-installer", "python-setuptools", "python-wheel", "python-textual>=8.2.8", "tmux"]


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args])


def load_lock():
    lock = json.loads((ROOT / "assist.lock.json").read_text())
    if (lock.get("repository") != "https://github.com/gtshelbu-jpg/solace-assist.git"
            or not re.fullmatch(r"[a-f0-9]{40}", lock.get("commit", ""))
            or not re.fullmatch(r"[0-9][A-Za-z0-9.]*", lock.get("version", ""))
            or not re.fullmatch(r"[a-f0-9]{64}", lock.get("source_sha256", ""))):
        raise ValueError("Invalid Assist source lock")
    return lock


def check_policy(policy):
    # Do not silently weaken a signed-local-only installation or TrustAll setup.
    tokens = policy.split()
    if "PackageOptional" not in tokens or "PackageTrustedOnly" not in tokens or "PackageRequired" in tokens:
        raise ValueError("Source-built local package requires Arch's Optional TrustedOnly local-file policy. No trust policy was changed; use your signed-package distribution path instead.")


def prepare(source, output, lock):
    if git(source, "rev-parse", "HEAD").decode().strip() != lock["commit"]:
        raise ValueError("Assist source does not match the pinned commit")
    if git(source, "status", "--porcelain").strip():
        raise ValueError("Assist source is modified; preserve/review it before building")
    version = lock["version"]
    project = tomllib.loads(git(source, "show", "HEAD:pyproject.toml").decode())
    if project["project"]["version"] != version:
        raise ValueError("Assist source version does not match the lock")
    archive = git(source, "archive", "--format=tar", f"--prefix=solace-assist-{version}/", "HEAD")
    epoch = int(git(source, "show", "-s", "--format=%ct", "HEAD"))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=epoch) as stream:
        stream.write(archive)
    data = compressed.getvalue()
    if hashlib.sha256(data).hexdigest() != lock["source_sha256"]:
        raise ValueError("Assist source archive checksum mismatch; no build or install performed")
    recipe = git(source, "show", "HEAD:packaging/arch/PKGBUILD.in").decode()
    recipe = recipe.replace("@VERSION@", version).replace("@SHA256@", lock["source_sha256"])
    output.mkdir()  # Never reuse/overwrite a previous build directory.
    (output / f"solace-assist-{version}.tar.gz").write_bytes(data)
    (output / "PKGBUILD").write_text(recipe)
    (output / "SOURCE_COMMIT").write_text(lock["commit"] + "\n")
    return output


def install(home, apply=False, source=None):
    lock = load_lock()
    if not apply:
        print(f"Preview: build Assist {lock['version']} from pinned commit {lock['commit']}; verify source SHA256, run native tests, install through normal Pacman policy. No commands executed.")
        return
    if os.geteuid() == 0:
        raise ValueError("Run as the target desktop user, not root")
    for command in ("git", "makepkg", "pacman-conf", "sudo"):
        if not shutil.which(command):
            raise ValueError(f"Required command missing: {command}. Install the shared desktop/build prerequisites first.")
    policy = subprocess.check_output(["pacman-conf", "LocalFileSigLevel"], text=True)
    check_policy(policy)
    builds = home / ".local/state/solace-black/assist-builds"
    builds.mkdir(parents=True, exist_ok=True, mode=0o700)
    work = Path(tempfile.mkdtemp(prefix=lock["version"] + "-", dir=builds))
    print(f"Retaining build sources and artifacts at {work}", flush=True)
    if source is None:
        source = work / "source"
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "fetch", "--depth=1", lock["repository"], lock["commit"]], check=True)
        subprocess.run(["git", "-C", str(source), "checkout", "--detach", "FETCH_HEAD"], check=True)
    else:
        source = source.resolve()
    output = prepare(source, work / "package", lock)
    # These are normal signed repository dependencies. No pip, key import,
    # signature override, package database refresh or source execution as root.
    subprocess.run(["sudo", "pacman", "-S", "--needed", "--noconfirm", "--", *DEPENDENCIES], check=True)
    subprocess.run(["makepkg", "--syncdeps", "--install", "--noconfirm"], cwd=output, check=True)
    print("Assist installed. Open Solace Assist from the application menu or run sbtools. Browsing never executes tools.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--source", type=Path, help="Use an existing clean checkout at the exact pin instead of fetching")
    args = parser.parse_args()
    try:
        install(Path.home(), args.apply, args.source)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"ERROR: {error}")
