# Beelink — boot into Ubuntu by default (runbook)

**Problem.** The Beelink GTR9 Pro is dual-boot (Windows 11 / Ubuntu 24.04) and
lives in Ubuntu, but every unattended restart — a power cut, an
`unattended-upgrades` reboot, a kernel update — lands in Windows. Docker
Engine's collectors (`longseries/`) then sit off until someone walks over.

**Cause.** The UEFI firmware's boot order, not anything in Ubuntu. Check the
three places it can go wrong, in this order, from Ubuntu.

## 1. Firmware boot order (the usual culprit)

```bash
sudo efibootmgr
```

Read `BootOrder:` and the `Boot000X*` lines. If `Windows Boot Manager` comes
before `ubuntu`, GRUB never gets a turn. Rewrite the order with the IDs
*exactly as printed*, Ubuntu first:

```bash
sudo efibootmgr -o 0001,0000     # example: 0001 = ubuntu, 0000 = Windows Boot Manager
sudo efibootmgr                  # confirm
sudo reboot                      # test — it must come back in Ubuntu with nobody at the keyboard
```

If it still boots Windows, this firmware honours its own setup menu over NVRAM
edits: press **Del** at power-on → *Boot* → *Boot Option #1* = `ubuntu`.
(Beelink's AMI firmware usually offers a one-off boot menu on **F7**; the key
is printed on the POST screen.)

## 2. GRUB's default — only if the GRUB menu appears and picks Windows

In `/etc/default/grub`:

```
GRUB_DEFAULT=saved
GRUB_SAVEDEFAULT=true      # boots whatever was chosen last; or GRUB_DEFAULT=0 for "always the first entry"
GRUB_TIMEOUT=3
```

then `sudo update-grub`.

## 3. Windows putting itself back first

Feature updates, and some firmware after any Windows session, rewrite the
order. Two guards:

- In Windows: *Power Options → Choose what the power buttons do → Turn on fast
  startup* — **off**.
- From an admin PowerShell, make the firmware order prefer Ubuntu from the
  Windows side too:

  ```powershell
  bcdedit /enum firmware                                      # find the {GUID} of the "ubuntu" entry
  bcdedit /set "{fwbootmgr}" displayorder "{GUID}" /addfirst
  ```

## Booting Windows once, on purpose — over SSH/Tailscale, without touching the default

```bash
sudo efibootmgr -n 0000 && sudo reboot      # BootNext: one boot into Windows, then back to Ubuntu
```

## Two firmware settings a collector host needs

- **Restore on AC Power Loss → Power On.** After a power cut the machine
  otherwise stays off until someone presses the button. (Under *Advanced* /
  *Chipset* in the setup menu; the label varies.)
- **Fast Boot** must not skip USB, or the keyboard is dead when you need the
  boot menu.

## Why this matters for `longseries/`

Docker Engine is a system service on the Ubuntu boot, and every collector runs
under `restart: unless-stopped`, so a reboot with nobody logged in brings the
whole stack back — *if* the machine boots Ubuntu. Once it does, the Beelink is
a genuine always-on replica (ADR-001 Q1), not "a replica while it happens to
be up".

## Verify, once

```bash
sudo reboot                # from an SSH session; wait two minutes
ssh beelink docker ps      # the longseries-* containers are Up, and nobody touched the machine
```

*Written 2026-09-12. The efibootmgr IDs above are examples; use the ones your
firmware prints.*
