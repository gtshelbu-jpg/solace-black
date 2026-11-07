# Solace Black

Solace Black keeps Solace's familiar desktop and adds an explicitly configured
BlackArch repository, a small native toolkit and an optional coordinated theme.
It is not a different shell, and it does not automatically start security tools.

## Start with the normal shortcuts

- **Super + Enter:** terminal.
- **Super + Alt + Enter:** ordinary tmux terminal; no AI or assisted shell.
- **Super + Space:** normal application launcher.
- **Super + Alt + Space:** Solace menu; **Learn > Solace** reopens this guide.
- **Super + K:** discover the existing keybindings.

## Choose the Black appearance

If registered, select **Solace Black** in the normal theme menu, or run:

```bash
solace-theme-set --appearance-only solace-black
```

The theme coordinates the wallpaper, terminal ANSI colours, bar, supported TUI
apps, launcher, notifications, GTK and lock colours. A running locker keeps the
appearance it already loaded until the next lock. Scale, lock-logo dimensions,
SDDM, boot visuals and personal keybindings are separate settings.

Return to the standard named theme with:

```bash
solace-theme-set --appearance-only solace
```

## What the core toolkit includes

- **nmap:** network discovery and port/service inspection.
- **tcpdump:** command-line packet capture.
- **Wireshark CLI tools** (including tshark): packet/protocol analysis.
- **ripgrep:** searching local text and source trees.

For a safe first step, read the installed tools' manuals, such as `man nmap` or
`man tcpdump`. Only inspect networks, systems and traffic you are authorized to
access. Packet capture permissions are not granted automatically to every user.

Arch repositories keep priority. Packages still require the configured trusted
repository signatures; BlackArch is an additional source, not a replacement for
the Arch base. Review third-party/AUR build recipes before installing them.

## Optional groups and hardware

The Black installer offers separately selected web/wireless/native tool groups.
Shared Solace applications, development, SDR, gaming and DisplayLink remain
explicit options. DisplayLink requires matching kernel headers, a successful
EVDI DKMS build and its service; the bar indicator reports readiness, not proof
that an attached dock/display works. No saved network credentials are included.

## Solace Assist: offline tool explorer

If selected at install, open **Solace Assist** from **Super + Space**, or run
`sbtools` in a terminal. It searches tools by purpose, shows categories and
source-reviewed guides, and keeps notes, tags and favorites locally. Examples:

```bash
sbtools search enumerate smb
sbtools show nmap
sbtools installed
```

Press **Ctrl+R** in the explorer (or run `sbtools sync`) to import existing local
Pacman caches and installed metadata. It does not download anything or refresh
package databases. Installed status is a snapshot, not a live guarantee.
**Enter** focuses results/opens details, **Tab** moves focus, **F** toggles a
favorite when results are focused, **Esc** returns and **Ctrl+Q** quits.
Browsing and selection never execute the described security tools.
The explorer follows the active Solace palette, including changes while it is
open. After upgrading an older Assist version, reopen it once to load this support.

Assist remains independently usable and optional. The Black installer can use a
trusted native package (`--with assist`) or an explicit pinned local source build
(`--assist-source-build`). The latter verifies the locked commit/source checksum,
runs native tests and respects normal Pacman local-package trust; it does not
silently relax signatures. An unselected Assist installation is not implied.

## Still not enabled

There is no enabled assisted shell, automatic generated-command execution or
replacement launcher shortcut. The normal tmux binding is intentional.

## Troubleshooting the appearance

Open a **new** terminal after enabling Bash defaults. `ls` uses eza when available;
Starship supplies the prompt. btop's Solace theme is named `current`. Impala uses
an application palette, while Bluetui's fixed ANSI accents are styled in its
dedicated terminal by the Solace launch helper. Existing windows may need reopening.
