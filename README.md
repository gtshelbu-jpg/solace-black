# Solace Black

An independently maintained overlay on a pinned Solace desktop, not a full fork.
Solace owns the shared desktop/installer/Archiso engine. Black owns repository
integration, optional native tool selections, a small desktop include and optional
palette, and explicit security/hardware deployment policy. Assist is a separate
offline CLI/TUI MVP, not a boot dependency. Its shell and Elephant adapter remain
later milestones; no unfinished launcher or assisted-shell shortcut is enabled.

## Source lock and build requirements

This is **not a released or hardware-validated ISO**. `upstream.lock.json` records
the exact interface-1 Solace revision. Modified or unpinned dependency
trees are rejected by release composition.
Development preparation is explicit and labels its build manifest accordingly.

```bash
# Explicit network fetch, or use --source /path/to/local/Solace to fetch the pin locally.
bash scripts/fetch-upstream.sh

# Prepare pinned profiles without sudo, package operations, or mkarchiso.
bash scripts/build-iso.sh solace-black --prepare-only
bash scripts/build-iso.sh solace --prepare-only
```

Build only in a disposable Arch environment with the required package artifacts
and signing trust. See [build and release validation](docs/BUILD_VALIDATION.md).

```bash
bash scripts/build-iso.sh solace --gpg-dir /path/to/dedicated/build-keyring --local-repo /path/to/signed-local-repository
bash scripts/build-iso.sh solace-black --gpg-dir /path/to/dedicated/build-keyring
```

The build machine needs Arch, Archiso/mkarchiso, rsync, Git and Python 3.11+.
Neither this project nor its tests install these prerequisites. Each flavor has
separate `.work/mkarchiso` and `out` directories. Archiso emits versioned ISO names;
there is no claim of a new image being built merely because a profile was prepared.
Generated profiles, dependency clones and image outputs are ignored by Git.

Black removes the experimental Calamares/Cage/KCrash dependency from its live
package list and retains the shared archinstall path. Normal Solace composition
retains its original package selection, including its separately prepared signed
Calamares requirement. No shared profile is edited in place.

## Optional appearance

For the optional coordinated charcoal/violet appearance, see the
[Solace Black theme](docs/THEME.md). Selecting it keeps the familiar desktop
layout and shortcuts; normal Solace remains available in the theme selector.
The shared first-login/Learn guide gains a **Solace Black** topic explaining the
current toolkit, theme and optional groups without advertising unfinished shell
or Assist integration. Locally edited guide pages are preserved on reinstall.
See [installed-desktop readiness](docs/RELEASE_READINESS.md) for the distinction
between tested staging fixes and a reproducible, install-ready release.

## Signing and repository contexts

1. **Build:** dedicated keyring already trusting Arch and BlackArch; strict package
   verification. Provision this trust in a disposable build VM/container using the
   reviewed official bootstrap, not by modifying the daily-driver host keyring.
2. **Live:** separate Pacman config/mirror list plus the verified blackarch-keyring
   package. The shared live `pacman-init` service populates both keyrings.
3. **Target:** after base installation, Black explicitly runs the pinned official
     bootstrap on the target before selecting/installing native tools.

Repository packages require trusted signatures in all three contexts. Build-time
local packages also require trusted signatures. Live/installed systems instead use
`LocalFileSigLevel = Optional TrustedOnly`, matching normal Arch AUR workflows:
unsigned local builds are allowed, but present signatures must validate against a
trusted key. The live configuration may be inherited by archinstall; it must not
carry the build-only local-signature requirement into the installed system.
Existing installations are not changed automatically by rebuilding an ISO.

Target repository setup runs before the shared desktop package stage. If
archinstall inherited Black's canonical repository Include but omitted its mirror
list, the bootstrap restores that missing file before invoking Pacman. Existing
custom mirror files and signature policy are not overwritten by that repair.

`bootstrap/blackarch-repo.sh` is preview-only without `--apply`. Applying requires
root, downloads into a root-owned temporary directory, checks the recorded SHA256,
then runs the reviewed upstream bootstrap (which verifies the keyring signature).
A changed download fails closed. Review the source and fingerprint changes before
updating that pin; a checksum from an untrusted source is not independent trust.
Reference: https://blackarch.org/downloads.html#install-repo

Standard Arch repositories retain precedence. The Black profile also enables
multilib for the live environment; installed-system multilib remains an explicit
base-install/admin choice. No SigLevel=Never/TrustAll or blanket --overwrite is used.
There is no automatic host pacman -Sy, package installation, trust enrollment or
repository change while composing a profile. Build keys are not embedded in ISOs.

Local packages must be signed and their signing keys trusted by the dedicated
build keyring; the upstream builder verifies through Pacman. This foundation does
not yet provide a binary Assist repository or a key-distribution service.
Pass their directory explicitly with `--local-repo`; profile preparation does not
import packages or trust keys. Standard Solace requires a signed Calamares package
in that repository. Do not put package artifacts in the pinned source checkout.

## Target desktop installation

The ISO's generic target-staging hook copies the Black source beside Solace and
selects the Black first-login entry point. It refuses existing add-on sources or
bootstrap selections rather than overwriting them. Disk selection/formatting stays
inside the explicitly confirmed archinstall workflow.

```bash
# Always inspect the plan first. These examples are NOT instructions to rerun on
# the working source laptop.
bash install.sh --dry-run --base-path /opt/solace
bash install.sh --apply --lid-policy docked --no-tablet
# Optional additional packages:
bash install.sh --apply --with web --with wireless --lid-policy awake --no-tablet
# Select a signed native Assist package from a trusted repository:
bash install.sh --dry-run --with assist --lid-policy docked --no-tablet
# Or explicitly build the exact locked Assist source as a native local package:
bash install.sh --dry-run --assist-source-build --lid-policy docked --no-tablet
# Add selected tools to an existing Black desktop without rerunning shared setup:
bash install.sh --dry-run --tools-only --assist-source-build
# Add only desktop files to a prepared, compatible desktop:
bash install.sh --dry-run --desktop-only
```

The shared installer handles lid selection, keyring/PAM preservation, and user
preferences. Black defaults to preserving the current theme. `--theme black` is an
explicit opt-in: materialize the optional palette using shared theme assets, then
select it through Solace. Black supplies its own original static SVG wallpaper;
the artwork has no text or branding. Existing user themes and wallpaper selections are preserved by
default; registering a theme is separate from selecting it.

### Offline tool explorer

An installed Assist package provides **Solace Assist** in the normal application
launcher (**Super + Space**) and the `sbtools` command. It browses tool purposes,
categories, eight source-reviewed guides and personal notes/favorites. Search by
task, for example `sbtools search enumerate smb`. Run `sbtools sync` (or Ctrl+R in
the explorer) to explicitly read local Pacman caches and installed-file metadata;
this does not download data or refresh Pacman's databases. Browsing never runs a
security tool. There is no assisted shell or generated-command execution yet.
The explorer follows Solace's active palette and updates when the system theme
changes, without requiring a separate Assist theme setting.
The optional **Solace Assist Search** application entry uses Walker to ask for a
task, then presents shared-catalog ranked results. Selection opens a tool's
documentation in the explorer, never its executable. `sbtools launch enumerate
smb` skips the first prompt. It does not change normal launcher/terminal bindings
or install an independent Elephant catalog.

`sbtools templates` lists the initial reviewed, typed command previews. For
example, `sbtools preview readelf-header --arg 'file=a sample.elf' --shell bash`
prints a reviewable command without running, copying, inserting or submitting it.
Unknown-shell/generic mode returns structured arguments. PTY transport foundations
are tested separately; no public assisted-shell interface is enabled yet.

`--with assist` still expects a package in an explicitly trusted repository.
`--assist-source-build` is a separate opt-in for installations without that binary
distribution: fetch the commit in `assist.lock.json`, verify the deterministic
source archive SHA256, install signed build/TUI dependencies, then run unprivileged
`makepkg` with tests and normal Pacman installation. No global pip or signature
override is used. This local source-build mode requires the normal Arch
`Optional TrustedOnly` local-file policy and refuses stricter or untrusted policy;
it never changes trust. It is not a production signed binary repository.

To install only the catalog on an already prepared desktop, preview with
`python3 scripts/install-assist.py`, then explicitly apply with `--apply`.
`--source /path/to/solace-assist` can use a clean checkout at the exact pin; modified
or mismatched source fails closed. Build sources/artifacts are retained under
`~/.local/state/solace-black/assist-builds/`. Network access is required for initial
source/dependency acquisition; the installed explorer remains offline-capable.
`--tools-only` uses existing repository configuration and skips both shared setup
and repository bootstrapping; it is for an already configured Black installation.

Black tracks its owned include's hash. If edited locally, it is preserved and the
installer requests manual review. Missing shared derivative/user include support
also fails rather than rewriting a customized Hyprland configuration.
SUPER+Enter is unchanged. The approved security-launcher shortcut is reserved for
the launcher milestone; SUPER+ALT+Enter is not changed until real assisted-shell
mode passes cross-shell and terminal tests. The normal Solace bindings stay intact.

## Security boundaries

No disks, encryption settings, boot files, firmware keys, networking profiles,
firewall rules or SSH services are configured here. A security tool package is not
automatically a hardened workstation. See `profiles/hardware/surface`.
Live-media Secure Boot, target signed UKIs, kernel module enforcement/signing and
LUKS2 recovery require a separately reviewed and tested deployment procedure.

Online package availability and AUR/source revisions change. Source locks and
build manifests do not pin every binary dependency or guarantee bit-for-bit image
reproducibility. Verify actual package signatures and test the exact generated
image; unit tests and successful builds do not establish installation, hardware,
suspend or hotplug compatibility. See the validation guide for release gates.

```bash
python3 -m unittest discover -s tests -v
```

Tests use temporary fixtures and mocked privileged commands. No binary public
release is created automatically. Original overlay code and documentation are MIT
licensed; see LICENSE and NOTICE. Upstream code/assets and packages retain their
own licenses and notices.
