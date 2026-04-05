# boxee-2026-yoavm

Run **Kodi 14.2 (Helix)** on a Boxee Box (D-Link DSM-380, Intel CE4100) in 2026 — with full Plex integration via PlexBMC and 5.1 audio passthrough over optical.

This repository contains everything needed to reproduce the setup: a flashable disk image, scripts, patches, and a complete setup guide. All release files are in the [v1.0.0 release](https://github.com/yoavmagor/boxee-2026-yoavm/releases/tag/v1.0.0).

---

## What's in this release

| File | Description |
|------|-------------|
| [`boxeehacks-kodi.zip`](https://github.com/yoavmagor/boxee-2026-yoavm/releases/download/v1.0.0/boxeehacks-kodi.zip) | Boxee+Hacks installer with Kodi autostart pre-bundled |
| [`kodi-boxee-box.img.gz`](https://github.com/yoavmagor/boxee-2026-yoavm/releases/download/v1.0.0/kodi-boxee-box.img.gz) | Kodi 14.2 disk image — flash to USB stick or SD card (512 MB+) |
| [`start_kodi.py`](https://github.com/yoavmagor/boxee-2026-yoavm/releases/download/v1.0.0/start_kodi.py) | Python script to start/restart Kodi from your computer via telnet |
| [`patch_plexbmc.py`](https://github.com/yoavmagor/boxee-2026-yoavm/releases/download/v1.0.0/patch_plexbmc.py) | Script to apply Plex 1.43+ compatibility patches via telnet |
| [`script.module.requests-2.9.1.zip`](https://github.com/yoavmagor/boxee-2026-yoavm/releases/download/v1.0.0/script.module.requests-2.9.1.zip) | Python requests module (required by PlexBMC) |
| [`plexbmc-v3.6.1.zip`](https://github.com/yoavmagor/boxee-2026-yoavm/releases/download/v1.0.0/plexbmc-v3.6.1.zip) | PlexBMC Plex client addon for Kodi 14 |

The Kodi binary (`kodi/kodi.bin`) and all 68 required shared libraries (`kodi/lib/`) are also tracked individually in this repository.

---

## Setup

See **[KODI-ON-BOXEE-BOX.md](KODI-ON-BOXEE-BOX.md)** for the full step-by-step setup guide covering:

- Installing Boxee+Hacks (modified installer included in the release)
- Flashing the Kodi disk image
- DNS fix for the dead `boxee.tv` domain
- Autostart configuration
- Installing and configuring PlexBMC
- Applying the Plex 1.43+ compatibility patches

---

## Background

For the full story of how this came together — the hardware archaeology, the missing libraries, the PlexBMC debugging, and how the whole thing was done with Claude Code — see **[BOXEE-KODI-PLEX-2026.md](BOXEE-KODI-PLEX-2026.md)**.

---

## Related repositories

| Repository | Description |
|------------|-------------|
| [yoavmagor/boxeehack](https://github.com/yoavmagor/boxeehack) | Fork of Boxee+Hacks with Kodi autostart script |
| [yoavmagor/plugin.video.plexbmc](https://github.com/yoavmagor/plugin.video.plexbmc) | Fork of PlexBMC with Plex 1.43+ and offline-mode patches |

---

## Tested on

| Component | Version |
|-----------|---------|
| Hardware | Boxee Box (D-Link DSM-380, Intel CE4100, i686) |
| Kodi | 14.2 (Helix), CE4100 build |
| PlexBMC | 3.6.1 |
| Plex Media Server | 1.43.0 |
