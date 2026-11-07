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

The explorer now starts with **Reviewed guides**, not an alphabetical dump of
package metadata. Uncheck that filter when you want the full imported catalog.
**Start a task / Ctrl+T** offers guided starting points. **Build command / Ctrl+P**
opens a typed form with option explanations, explicit arguments and a preview.

Press **Ctrl+R** in the explorer (or run `sbtools sync`) to import existing local
Pacman caches and installed metadata. It does not download anything or refresh
package databases. Installed status is a snapshot, not a live guarantee.
**Enter** focuses results/opens details, **Tab** moves focus, **F** toggles a
favorite when results are focused, **Esc** returns and **Ctrl+Q** quits.
Browsing and selection never execute the described security tools.
The explorer follows the active Solace palette, including changes while it is
open. After upgrading an older Assist version, reopen it once to load this support.

### Search from the desktop

Open **Solace Assist Search** in the normal application launcher, or run
`sbtools launch`. Describe a task, choose a result, and its guide opens in the
terminal explorer. `sbtools launch enumerate smb` starts with that task directly.
This optional adapter needs Walker and the normal terminal launcher. Selecting a
result never starts the security tool, and cancelling does nothing.

### Preview a reviewed command

`sbtools templates` lists available typed previews. For example:

```bash
sbtools preview readelf-header --arg 'file=a sample.elf' --shell bash
```

Nothing is run, inserted, copied or submitted. Without a supported shell choice,
the default preview is structured arguments rather than guessed quoting. Read the
corresponding tool guide and check the installed version before manually using
any command. Network-probe previews take a single IP/explicit port list, without
an acknowledgment checkbox or flag; they do not broaden scope automatically.

Assist remains independently usable and optional. The Black installer can use a
trusted native package (`--with assist`) or an explicit pinned local source build
(`--assist-source-build`). The latter verifies the locked commit/source checksum,
runs native tests and respects normal Pacman local-package trust; it does not
silently relax signatures. An unselected Assist installation is not implied.

## Try the interactive helper prototype

Open **Solace Assist Helper (Prototype)** from the application launcher, or run
`sbtools shell` in a normal terminal. The left pane is a real shell on a private
tmux PTY; the right pane is the offline helper. Your ordinary terminal and tmux
bindings do not change.

A safe first try:

1. In the Bash pane, type `readelf` without Enter, then **Ctrl+G** for its guide.
2. **Ctrl+B, Right** switches to the helper. Use **Ctrl+P** to build a command,
   choose the ELF-header template, and enter `/usr/bin/ls` as the file to inspect.
3. The first argument is focused. **Enter** previews; **Ctrl+Enter** stages
   directly from the current fields. Buttons remain available. Nothing inserts
   or runs yet, and there is no extra acknowledgment step.
4. **Ctrl+B, Left** returns to the shell. Clear the old input yourself. At an
   **empty prompt**, **Ctrl+X then Ctrl+I** inserts the reviewed Bash preview.
5. Review/edit the line and press Enter yourself only if you want to execute it.
   This example reads an ELF header; it does not execute the inspected program.
6. `exit` or Ctrl+D closes the disposable helper and its jobs.

Only an explicit key shares a conservative executable hint; no terminal-output
scraping or raw command/credential history is stored by the helper. Bash insertion
uses native Readline, refuses nonempty buffers and never appends Enter. Other
shells keep their original executable and get read-only guidance, not a silent
switch or an invented editing adapter. This is an opt-in prototype, not finished
cross-shell assistance or an AI command agent. Terminal close/detach ends its
private session; do not use it for irreplaceable long-running jobs.

There is still no automatic generated-command execution or replacement launcher
shortcut. Your normal tmux binding is intentional.

## Troubleshooting the appearance

Open a **new** terminal after enabling Bash defaults. `ls` uses eza when available;
Starship supplies the prompt. btop's Solace theme is named `current`. Impala uses
an application palette, while Bluetui's fixed ANSI accents are styled in its
dedicated terminal by the Solace launch helper. Existing windows may need reopening.
