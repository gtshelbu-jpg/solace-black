# Installed-desktop readiness

A working migration/test session is not proof that the installer reproduces it.
Do not describe Black as install-ready until the gates below pass against the
same pinned sources and final image. Keep machine logs, screenshots, credentials
and personal configuration outside the repositories.

## Source coverage versus remaining validation

| Area | Reusable implementation | Remaining gate |
| --- | --- | --- |
| Shared Bash defaults | Stock-startup detection, explicit opt-in for custom startup, backups and tests | Verify new terminals after a clean first-login install |
| Linked TUI appearance | btop reconciliation, Impala palette and Bluetui terminal adapter | Verify real graphical launch/focus paths after clean install and theme changes |
| Black wallpaper | Original text-free SVG, installer rendering and no-branding regression test | Check unlocked desktop at the display's actual aspect ratio |
| Black Learn page | Managed page, shared topic discovery, customization-preservation test | Open through both first-login and menu paths |
| DisplayLink | Optional package group, matching-header selection and service lifecycle | Actual dock hotplug, output, unplug/replug and reboot testing; software readiness is not hardware proof |
| Core native tools | Explicit native package group and repository setup | Safe CLI smoke checks, availability and signature checks on the installed target |
| Native Lua desktop | Shared reversible modular staging helper, live palette bridges, toggle-state mapping and isolated compositor verification; legacy configuration remains in the installer | Real modular-session testing, runtime helpers and regular installer promotion |
| Solace Assist | Offline CLI/TUI catalog; exact source lock/checksum, explicit native build/install path and standard application-menu entry | Clean-install validation and production signed binary distribution |
| Security launcher | Optional Walker task-search adapter uses shared catalog ranking and opens documentation only; native menu entry | Real graphical selection/cancel validation; normal launcher bindings remain unchanged |
| Command previews | Initial typed, reviewed templates; supported-shell renderers and structured-only generic fallback | Expand curated coverage; validate additional shell versions without treating previews as execution |
| Assisted shell | Internal real-PTY transport with resize, Ctrl+C, cleanup and explicit-Enter tests; no public shell UI | Editable-buffer adapters, terminal UI and complete cross-shell/fallback validation; never auto-submit generated commands |

Do not install a shortcut that points to an unimplemented interface. The normal
terminal and tmux bindings must remain usable independently of Black or Assist.
Browsing tool documentation must not execute tools or install packages.

## Promotion sequence

1. Implement every portable fix in its owning repository: desktop/install engine
   in Solace, Black integration in Black, catalog/shell interfaces in Assist.
   Add regression tests and update pinned dependencies after publication.
2. Deploy those same source files to the test machine with backups. Record local
   exceptions privately; do not treat hand-edited staging files as installer work.
3. Complete native Lua session parity, including startup, bindings, theme changes,
   toggles, monitors, lock/unlock and restart behavior. Preserve the fallback
   session until the regular installed session passes; do not upgrade the daily
   driver just because the snapshot session starts.
4. Validate the selected Black tools and integrations through their actual user
   entry points. Use offline/help/version checks and controlled fixtures, not
   scans of third-party networks or privileged packet captures.
5. Build from clean, pinned sources. Boot and install to a disposable virtual
   disk, then verify that first login reproduces the desktop without manually
   copying a snapshot or repair files. Check a second installer run preserves
   personal choices. Test the regular session, not a special staging entry.
6. Finish physical hardware checks and publish the exact image checksum, source
   revisions and explicit limitations. An older delivered ISO does not acquire
   later source fixes automatically.

The target result is reproducible **portable defaults and selected features**,
not copying a developer's credentials, saved networks, machine-specific monitor
rules, personal shell choice or complete application inventory. Optional groups
remain optional. See [build validation](BUILD_VALIDATION.md) for trust and media
checks.
