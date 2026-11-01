# Build and release validation

Profile preparation is not an ISO build or a boot test. Do not use a prepared
profile or passing unit tests as evidence that installation media is ready.

## Build environment

Use a disposable Arch Linux VM with Archiso, rsync, Git and Python 3.11+.
Provision a dedicated Pacman keyring with reviewed Arch and BlackArch trust;
keep build-time, live-environment and installed-target repository setup separate.
Never weaken signature verification to resolve a missing package or signing key.

The source revision and interface are specified in `upstream.lock.json`.
Release composition requires clean, pinned source trees. Standard Solace retains
its signed local Calamares dependency; Black uses the shared archinstall path.

## Required checks

1. Run `python3 -m unittest discover -s tests -v`.
2. Prepare both variants and inspect their package/configuration manifests.
3. Resolve all package artifacts and validate signatures using Pacman/GPG.
4. Build each variant in separate work/output directories.
5. Boot each image in a disposable UEFI VM; check networking, repository trust,
   installer entry points and embedded source provenance.
6. Test installation only to a disposable virtual disk. Verify target staging,
   first-login setup, lid-policy selection and preservation across reruns.
7. Generate checksums and publish precise compatibility limitations with images.

Unit tests use fixtures and mocked privileged commands. They do not validate
cryptographic trust, tool binaries, bootability or hardware compatibility.

## Boot and hardware limitations

No released, hardware-validated ISO is provided by this source repository.
Live-media Secure Boot, LUKS2 recovery, signed UKI updates and kernel-module
policy require separate validation. A successful VM boot does not establish
physical hardware compatibility or authorize firmware/disk changes.
