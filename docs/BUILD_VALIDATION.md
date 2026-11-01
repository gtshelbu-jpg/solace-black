# Build validation status

- Shared interface 1 is published in Solace commit
  `b30f8172aa542b49df66c39ddf348891547744e5` and recorded in `upstream.lock.json`.
- Fetching that exact commit from the local Git repository succeeded; the staged
  dependency is a detached, clean checkout, not a copy of the running desktop.
- Both profile variants prepare without sudo. Tests check separation of build,
  live and target repository setup, signature policy, provenance, user-edited
  overlays, source pinning and write-free installation previews.
- The original checked-in Solace profile is unchanged by composition. Normal
  Solace retains its original Calamares package selection; Black uses archinstall.

**No actual ISO has been built or booted.** This workstation lacks mkarchiso,
rsync and QEMU. An isolated Arch builder/VM and dedicated populated build keyring
are required. Do not install privileged build tooling onto the daily-driver or
launch a privileged container implicitly to make a validation claim.

Next build gates: resolve/verify selected package artifacts and signing trust;
build both variants in the isolated environment; boot in a disposable UEFI VM;
validate target staging/first-login and rerun preservation. Actual cryptographic
verification is done by Pacman/GPG, not by mocked signature-presence tests.

Secure Boot live media, LUKS2 layout/unlock/recovery, signed UKI updates, module
policy and Surface hardware remain separately reviewed deployment milestones.
No disk, key enrollment, networking profile or live installation was changed.
