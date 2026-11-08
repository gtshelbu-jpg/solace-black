# Fresh Black installation

Read the embedded `/opt/solace/docs/ENCRYPTED_INSTALL.md` **before installing** if
you want LUKS and Secure Boot. It links the Surface installation guide and current
upstream references. The ISO is unsigned for firmware: Secure Boot must be disabled
to start it. Package signatures remain required; they are a different trust layer.

## Live stage, before reboot

Run `solace-install` and choose **Install Arch with Solace defaults**. Select the
intended disk/account, encrypted root, filesystem and password in archinstall.
Keep the systemd-boot/UKI defaults. Do not select an unrelated desktop profile;
the embedded Solace desktop is configured after first login.

The live wrapper performs early-input preparation and inspects the generated
target images **before** offering a reboot. A failure is a stop condition, not a
warning to ignore. You may also approve target-owned EFI key/signature preparation;
this still does **not** enroll firmware keys or enable Secure Boot.

First boot with Secure Boot disabled and confirm onboard-keyboard LUKS unlock.
Only later, after reviewing recovery and verifying the exact EFI signatures,
make the separate firmware enrollment/enablement decision. Keep a wired keyboard
and the USB available until both encrypted and Secure Boot cold boots succeed.

## Installed-system stage

Log in as the regular user and accept `solace-postinstall`. On a fresh interactive
home, Black offers optional groups before setup; nothing extra is selected silently:

- `assist`: checksum-verified pinned native source build of the offline explorer
  and interactive-helper prototype. Does not replace the selected shell.
- `wireless`, `network`, `frameworks`: the requested wireless tools, Wireshark GUI,
  Bettercap, Metasploit and RouterSploit; no capture services or group grants.
- Shared `apps`, `development`, `displaylink`, `sdr`, `gaming` are independent
  optional choices. DisplayLink's third-party kernel module needs separate Secure
  Boot/module-signing validation; do not assume EFI signing covers it.
- Black appearance is an explicit choice. Lid policy and tablet support are
  selected by the shared installer. No network credentials are embedded.

For explicit noninteractive selection, decline the automatic prompt and use, for
example, the following as your normal user (review the preview first):

```bash
solace-postinstall --dry-run --theme black --assist-source-build --with wireless --with network --with frameworks --lid-policy docked --no-tablet
# Repeat with --apply instead of --dry-run when the plan matches your choices.
```

Fresh homes receive reviewed, modular **native Lua** defaults, checked by the
installed compositor before login setup completes. Palette and toggle state stay
dynamic; config editor menus point to Lua files. Existing homes are not silently
migrated. A failed native check stops setup rather than marking it complete.

After setup, open the local Black Learn guide, reopen applications to pick up
themes, and run `sbtools sync` if you selected Assist. Uncheck **Reviewed guides**
and enable **Installed** for new tools that currently have metadata but no reviewed
command guide. Hardware feature availability is not implied by package installation.

The image's manifest/checksum identifies its source snapshot. An old ISO cannot
acquire later fixes by itself; physical keyboard, dock, firmware and clean-desktop
validation remain explicit checks rather than release guarantees.
