"""Source locking and Archiso composition, without configuring the build host."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MIRROR = "https://blackarch.org/blackarch/blackarch/os/$arch"


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def git_value(source, *args):
    p = subprocess.run(["git", "-C", str(source), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def lock():
    data = json.loads((ROOT / "upstream.lock.json").read_text())
    if data.get("schema") != 1 or not re.fullmatch(r"[a-f0-9]{40}", data["solace"]["commit"]):
        raise ValueError("Invalid upstream lock")
    return data["solace"]


def fetch(source=None):
    pinned = lock()
    fetch_source = str(Path(source).expanduser().resolve(strict=True)) if source else pinned["repository"]
    dest = ROOT / ".deps/solace"
    if dest.exists():
        if git_value(dest, "rev-parse", "HEAD") != pinned["commit"] or git_value(dest, "status", "--porcelain"):
            raise ValueError("Existing dependency differs or is modified; preserve/review it manually")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fetch-", dir=dest.parent) as work:
        checkout = Path(work) / "solace"
        run("git", "init", "-q", checkout)
        run("git", "-C", checkout, "remote", "add", "origin", pinned["repository"])
        run("git", "-C", checkout, "fetch", "--depth=1", fetch_source, pinned["commit"])
        run("git", "-C", checkout, "checkout", "--detach", "FETCH_HEAD")
        if git_value(checkout, "rev-parse", "HEAD") != pinned["commit"]:
            raise ValueError("Fetched source does not match the lock")
        checkout.rename(dest)
    return dest


def validate_upstream(source, development=False):
    interface = source / "archiso/interface.json"
    if not interface.is_file():
        raise ValueError("Pinned Solace lacks interface 1. Publish/re-pin the reviewed upstream changes; use --upstream PATH --development only for local testing.")
    if json.loads(interface.read_text()).get("version") != lock()["interface"]:
        raise ValueError("Unsupported Solace derivative interface")
    if not (source / "install.sh").is_file() or not (source / "archiso/build.sh").is_file():
        raise ValueError("Missing upstream entry points")
    commit = git_value(source, "rev-parse", "HEAD")
    dirty = git_value(source, "status", "--porcelain")
    if not development and (commit != lock()["commit"] or dirty is None or dirty):
        raise ValueError("Release composition requires a clean checkout at the locked revision")
    if not development and (git_value(ROOT, "rev-parse", "HEAD") is None or git_value(ROOT, "status", "--porcelain")):
        raise ValueError("Release composition also requires committed, clean Black sources")
    return {"commit": commit, "development": development, "dirty": bool(dirty) or commit is None}


def package_lines(path):
    names = []
    for raw in path.read_text().splitlines():
        name = raw.split("#", 1)[0].strip()
        if not name:
            continue
        if not re.fullmatch(r"[a-z0-9@_+.-]+", name):
            raise ValueError(f"Invalid package name in {path.name}")
        if name not in names:
            names.append(name)
    return names


def own_input_digest():
    result = hashlib.sha256()
    for name in ["upstream.lock.json", "assist.lock.json", "install.sh", "scripts", "bootstrap", "packages", "overlays", "profiles", "docs/learn"]:
        root = ROOT / name
        paths = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in paths:
            if not path.is_file() or "__pycache__" in path.parts: continue
            result.update(str(path.relative_to(ROOT)).encode() + b"\0" + path.read_bytes())
    return result.hexdigest()


def blackarch_conf(base, live=False):
    # Build artifacts require signatures. The live configuration can be inherited
    # by archinstall targets, which must support normal unsigned local AUR builds.
    lines = []
    for line in base.splitlines():
        if re.match(r"\s*(SigLevel|LocalFileSigLevel|GPGDir)\s*=", line):
            continue
        lines.append(line)
        if line.strip() == "[options]":
            local_policy = "Optional TrustedOnly" if live else "Required TrustedOnly"
            lines += ["SigLevel = Required DatabaseOptional TrustedOnly", f"LocalFileSigLevel = {local_policy}"]
    if not any(line.strip() == "[multilib]" for line in lines):
        lines += ["", "[multilib]", "Include = /etc/pacman.d/mirrorlist"]
    lines += ["", "[blackarch]", "SigLevel = Required DatabaseOptional TrustedOnly"]
    lines.append("Include = /etc/pacman.d/blackarch-mirrorlist" if live else f"Server = {MIRROR}")
    return "\n".join(lines) + "\n"


def compose(source, dest, variant, development=False):
    provenance = validate_upstream(source, development)
    if dest.exists():
        raise ValueError("Profile output already exists; refusing to overwrite it")
    # Legacy automatic local repos must never introduce an unsigned build path.
    if any((source / "archiso/localrepo").glob("*.pkg.tar.*")):
        raise ValueError("Move local package artifacts out of upstream; use the explicitly trusted build repository workflow")
    shutil.copytree(source / "archiso/profile", dest, symlinks=True)
    definition = dest / "profiledef.sh"
    text = definition.read_text()
    for key, value in [("iso_name", variant), ("iso_publisher", "Solace"), ("iso_application", f"{variant} installation environment")]:
        text, count = re.subn(rf'^{key}=.*$', f'{key}="{value}"', text, flags=re.M)
        if count != 1:
            raise ValueError(f"Unexpected upstream profile: {key}")
    definition.write_text(text)
    if variant == "solace-black":
        shutil.copytree(ROOT / "overlays/archiso/airootfs", dest / "airootfs", dirs_exist_ok=True, symlinks=True)
        packages = package_lines(dest / "packages.x86_64")
        # Black uses archinstall, not the experimental Calamares dependency chain.
        packages = [p for p in packages if p not in {"calamares", "cage", "kcrash"}]
        for package in package_lines(ROOT / "packages/live.txt"):
            if package not in packages:
                packages.append(package)
        (dest / "packages.x86_64").write_text("\n".join(packages) + "\n")
        base = (dest / "pacman.conf").read_text()
        (dest / "pacman.conf").write_text(blackarch_conf(base))
        live_etc = dest / "airootfs/etc"
        (live_etc / "pacman.conf").write_text(blackarch_conf(base, live=True))
        mirrors = live_etc / "pacman.d/blackarch-mirrorlist"
        mirrors.parent.mkdir(parents=True, exist_ok=True)
        mirrors.write_text(f"Server = {MIRROR}\n")
        # Both installed keyring packages are populated by the existing live service.
        unit = live_etc / "systemd/system/pacman-init.service"
        content = unit.read_text().replace("--populate\n", "--populate archlinux blackarch\n")
        unit.write_text(content)
    manifest = {"schema": 1, "variant": variant, "upstream": provenance,
                "black": {"commit": git_value(ROOT, "rev-parse", "HEAD"), "inputs_sha256": own_input_digest()},
                "packages": package_lines(dest / "packages.x86_64"),
                "black_bootstrap_sha256": (ROOT / "bootstrap/strap.sha256").read_text().strip() if variant == "solace-black" else None}
    metadata = json.dumps(manifest, indent=2) + "\n"
    (dest / "solace-build-manifest.json").write_text(metadata)
    shipped_metadata = dest / "airootfs/usr/share/solace/build-manifest.json"
    shipped_metadata.parent.mkdir(parents=True, exist_ok=True)
    shipped_metadata.write_text(metadata)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    get = commands.add_parser("fetch", help="Explicitly fetch the locked source; never run its installer")
    get.add_argument("--source", help="Optional local Git repository containing the locked commit")
    iso = commands.add_parser("iso", help="Compose or build through upstream mkarchiso infrastructure")
    iso.add_argument("variant", choices=["solace", "solace-black"])
    iso.add_argument("--upstream", type=Path, default=ROOT / ".deps/solace")
    iso.add_argument("--development", action="store_true", help="Allow an uncommitted/alternate upstream; NOT a release build")
    iso.add_argument("--prepare-only", action="store_true", help="Write staged files only; no root, package operations or mkarchiso")
    iso.add_argument("--profile-output", type=Path)
    iso.add_argument("--gpg-dir", type=Path, help="Dedicated pre-populated build keyring trusting Arch and BlackArch")
    iso.add_argument("--local-repo", type=Path, help="Explicit signed local package repository for an actual build")
    args = parser.parse_args()
    if args.command == "fetch":
        print(fetch(args.source)); return
    source = args.upstream.resolve()
    # A real build needs explicit build trust, never silently the host keyring.
    if not args.prepare_only and args.variant == "solace-black" and args.gpg_dir is None:
        raise ValueError("Black builds require --gpg-dir; prepare-only is unprivileged")
    if args.profile_output:
        dest = args.profile_output.resolve()
    else:
        parent = ROOT / ".work/profiles"
        parent.mkdir(parents=True, exist_ok=True)
        dest = Path(tempfile.mkdtemp(prefix=args.variant + "-", dir=parent)) / "profile"
    manifest = compose(source, dest, args.variant, args.development)
    print(json.dumps({"profile": str(dest), **manifest}, indent=2))
    if args.prepare_only:
        return
    work_parent = ROOT / ".work/mkarchiso" / args.variant
    work_parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="build-", dir=work_parent))
    # Never reuse mkarchiso step caches across changed profiles or overwrite an
    # earlier image from another build merely because its ISO version is equal.
    cmd = ["bash", source / "archiso/build.sh", "--profile", dest,
           "--embed-source", source, "--work", work,
           "--out", ROOT / "out" / args.variant / work.name]
    if args.gpg_dir:
        cmd += ["--gpg-dir", args.gpg_dir.resolve()]
    if args.local_repo:
        cmd += ["--local-repo", args.local_repo.resolve()]
    if args.variant == "solace-black":
        cmd += ["--extra-source", "solace-black", ROOT]
    if args.development:
        cmd += ["--allow-dirty-sources"]
    env = os.environ.copy()
    epoch = git_value(source, "show", "-s", "--format=%ct", "HEAD")
    if epoch and "SOURCE_DATE_EPOCH" not in env: env["SOURCE_DATE_EPOCH"] = epoch
    run(*cmd, env=env)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
