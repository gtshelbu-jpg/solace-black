# Surface hardware deployment gate

No kernel, ACPI parameter, disk or firmware policy is applied by this profile.
Test current stock Arch keyboard, touchpad, touch, graphics, audio, camera, Wi-Fi,
battery, shutdown and suspend before selecting any linux-surface components.
Documented ACPI workarounds require observed symptoms, not automatic application.

Candidate deployment: GPT ESP + LUKS2 root/home, systemd-boot + signed UKIs,
separate reviewed signing/update/recovery procedure. Encryption, firmware trust,
kernel/module signing and live-media Secure Boot are separate controls. Preserve
OEM firmware recovery options and keep recovery material/private keys outside Git.
The desktop installer does not partition, enroll keys or rebuild boot artifacts.
