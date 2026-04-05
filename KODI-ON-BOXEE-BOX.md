# Kodi on Boxee Box — Setup Guide

Run Kodi 14 (Helix) on a Boxee Box, replacing the Boxee UI entirely. Kodi starts automatically at boot from a USB stick or SD card and connects to a Plex Media Server via the PlexBMC addon.

---

## Downloads

All files needed for this setup are in the [v1.0.0 release](https://github.com/yoavmagor/boxee-2026-yoavm/releases/tag/v1.0.0):

| File | Used in | Description |
|------|---------|-------------|
| `boxeehacks-kodi.zip` | Part A | Boxee+Hacks installer with Kodi autostart pre-bundled |
| `kodi-boxee-box.img.gz` | Part C | Kodi 14.2 disk image — flash to USB stick or SD card |
| `start_kodi.py` | Part E | Python script to start/restart Kodi from your computer |
| `script.module.requests-2.9.1.zip` | Part F | Python requests module (PlexBMC dependency) |
| `plexbmc-v3.6.1.zip` | Part F | PlexBMC Plex client addon for Kodi 14 |
| `patch_plexbmc.py` | Part G | Script to apply Plex 1.43+ compatibility patches via telnet |

---

## What You Need

- Boxee Box (D-Link DSM-380)
- Two USB sticks (or one USB stick + one SD card):
  - One for the Boxee+Hacks installer (any size, FAT32)
  - One for the Kodi image, **512 MB or larger**
- A computer on the same LAN as the Boxee Box
- A Plex Media Server on your LAN (for PlexBMC playback)

---

## Part A — Boxee+Hacks Installation

Boxee+Hacks is community firmware that adds telnet, FTP, and a boot hook to the stock Boxee firmware. Without it, you cannot install or run Kodi.

### A1 — Download Boxee+Hacks

Download **`boxeehacks-kodi.zip`** from the [release page](https://github.com/yoavmagor/boxee-2026-yoavm/releases/tag/v1.0.0).

This is a modified version of Boxee+Hacks that includes the Kodi autostart script pre-bundled — the installer will place it on your Boxee Box automatically, so you will not need to copy it manually later.

### A2 — Prepare the USB installer stick

Format a USB stick as **FAT32** and name it `BOXEE`. Extract `boxeehacks-kodi.zip` and copy the contents of the `boxeehacks-kodi/` folder into the **root** of the stick:

```
install.sh
debug.sh
uninstall.sh
support/        (entire folder)
hack/           (entire folder — contains kodi_autostart.sh and boot.sh)
```

If any of these are missing or placed in a subdirectory, the installer will silently fail.

### A3 — Install via the hostname trick

On the Boxee Box, go to **Settings → Network → Servers** and find the **Host Name** field. Enter:

```
boxeebox; sh /media/BOXEE/install.sh
```

Back out of the settings menu. The Boxee logo will turn **red** — installation is running. Do not interrupt power. The UI will restart automatically when complete. This takes about 1 minute.

If it fails (logo does not turn red, or UI restarts without changes), verify the USB stick layout and try again. The install has no side effects if it fails — you can retry without factory-resetting.

### A4 — Verify installation

Telnet into the box:

```bash
telnet YOUR_BOXEE_IP 2323
# Default password: secret
```

If you get a shell prompt, Boxee+Hacks is installed.

> **Change the default password.** The default telnet password is `secret`. Change it immediately after installation with `passwd`.

Verify the autostart script was installed:

```sh
ls /data/hack/kodi_autostart.sh && grep kodi_autostart /data/hack/boot.sh
```

Both should return output. If either is missing, see Part D to add them manually.

---

## Part B — DNS Fix for boxee.tv (Required)

Boxee+Hacks checks `boxee.tv` on every boot to verify license status. The domain is dead. Without a fix, the boot process stalls for ~2 minutes on every startup.

**Fix:** Add a local DNS entry pointing `boxee.tv` to any HTTP server on your LAN that returns a 200 response. A Pi running a minimal web server works. Add the DNS entry to your router's local DNS overrides, or to the `/etc/hosts` file on the Boxee Box itself:

```sh
# On the Boxee Box via telnet:
echo "127.0.0.1 boxee.tv" >> /etc/hosts
echo "127.0.0.1 api.boxee.tv" >> /etc/hosts
```

> If your router supports local DNS entries (pfSense, Pi-hole, dd-wrt, etc.), adding it there is cleaner and persists across Boxee Box reboots.

---

## Part C — Flash the Kodi Storage Media

Download **`kodi-boxee-box.img.gz`** from the [release page](https://github.com/yoavmagor/boxee-2026-yoavm/releases/tag/v1.0.0) and flash it to a USB stick or SD card using [balenaEtcher](https://etcher.balena.io/) (Windows/Mac/Linux) or `dd`.

**With balenaEtcher:**
1. Open balenaEtcher → Flash from file → select `kodi-boxee-box.img.gz`
2. Select your USB stick or SD card as target
3. Flash

**With `dd` (Mac/Linux):**
```bash
# Find your disk (e.g. /dev/disk4 on Mac, /dev/sdb on Linux)
diskutil list          # Mac
lsblk                  # Linux

# Flash (replace diskN with your disk, NOT a partition like disk4s1)
gunzip -c kodi-boxee-box.img.gz | sudo dd of=/dev/rdiskN bs=4m
```

> **SD card note:** The SD slot uses an internal USB card reader IC — Kodi must be started *after* the card is mounted. The autostart script handles this automatically. **Insert the SD card before booting.** Hot-plug after boot does not work.

---

## Part D — Reboot into Kodi

Insert the Kodi SD card or USB stick **before** rebooting. If you installed from `boxeehacks-kodi.zip` (Part A), the autostart script is already in place — just reboot:

```sh
reboot
```

Kodi will start automatically. From cold power-on, expect ~60–90 seconds total. The Boxee splash screen appears first, then Kodi takes over.

**If you used the original Boxee+Hacks instead of `boxeehacks-kodi.zip`**, you need to add the autostart script manually. Connect via telnet and run:

<details>
<summary>Manual autostart setup (only needed if you didn't use boxeehacks-kodi.zip)</summary>

```sh
cat > /data/hack/kodi_autostart.sh << 'EOF'
#!/bin/sh
LOG=/tmp/kodi_autostart.log
echo "$(date): kodi_autostart.sh started" > $LOG

KODI_DIR=""
for i in $(seq 1 60); do
    for dir in /tmp/mnt/*/; do
        if [ -x "${dir}kodi.bin" ]; then
            KODI_DIR="${dir%/}"
            break 2
        fi
    done
    sleep 1
done

if [ -z "$KODI_DIR" ]; then
    echo "$(date): kodi.bin not found — SD/USB card not present." >> $LOG
    exit 1
fi

echo "$(date): Found Kodi at $KODI_DIR" >> $LOG
sleep 3
killall Boxee BoxeeLauncher BoxeeHal 2>/dev/null
sleep 2
cd "$KODI_DIR" || exit 1

export HOME=/data
export KODI_HOME="$KODI_DIR"
export PYTHONHOME="$KODI_DIR/python2.7"
export PYTHONPATH="$KODI_DIR/python2.7:$KODI_DIR/python2.7/lib-dynload"
export LD_LIBRARY_PATH="$KODI_DIR/lib:$KODI_DIR:/opt/local/lib:/opt/boxee/lib:$LD_LIBRARY_PATH"

echo "$(date): Starting Kodi from $KODI_DIR" >> $LOG
exec ./kodi.bin >> $LOG 2>&1
EOF
chmod +x /data/hack/kodi_autostart.sh
grep -q kodi_autostart /data/hack/boot.sh || echo 'sh /data/hack/kodi_autostart.sh &' >> /data/hack/boot.sh
reboot
```

</details>

---

## Part E — Set Up the `start_kodi.py` Script (optional, recommended)

Download **`start_kodi.py`** from the [release page](https://github.com/yoavmagor/boxee-2026-yoavm/releases/tag/v1.0.0). This script lets you start or restart Kodi from your Mac/Linux machine without needing to manually telnet in. `patch_plexbmc.py` (Part G) also imports it, so you need it regardless.

**Before first use, edit these four variables at the top of the file:**

| Variable | What to set | How to find it |
|----------|-------------|----------------|
| `HOST` | IP address of your Boxee Box | Check your router's DHCP table |
| `PORT` | `2323` | Always 2323 for Boxee+Hacks |
| `PASSWORD` | Your telnet password | Whatever you set after `passwd` (default: `secret`) |
| `USB_PATH` | Mount path of Kodi media | Telnet in and run `ls /tmp/mnt/` — it looks like `/tmp/mnt/69C4-44AF` |

```bash
# Start Kodi (Boxee already booted):
python3 start_kodi.py

# Reboot Boxee Box, then auto-start Kodi after it comes back up:
python3 start_kodi.py --reboot-first
```

---

## Part F — Install PlexBMC

PlexBMC is a Kodi 14 compatible Plex client addon. Install it from inside Kodi.

Download **`script.module.requests-2.9.1.zip`** and **`plexbmc-v3.6.1.zip`** from the [release page](https://github.com/yoavmagor/boxee-2026-yoavm/releases/tag/v1.0.0) and copy them to your Kodi USB stick or SD card so Kodi can reach them.

### F1 — Get your Plex token

You need a Plex authentication token. The easiest way:

1. Open Plex Web UI in a browser while logged in
2. Browse to any media item, click the three-dot menu, then **Get Info**
3. At the bottom of the info panel, click **View XML**
4. In the URL, copy the value of `X-Plex-Token=` — that is your token

The token is a 20-character alphanumeric string like `y5zPxk8EBx2Whtp6QkBm`.

### F2 — Install from zip in Kodi

In the Kodi UI on the Boxee Box:

1. **Settings → Add-ons → Install from zip file**
2. Navigate to the Kodi SD card root (it should appear in the file browser as the storage source)
3. Install **`script.module.requests-2.9.1.zip`** first — PlexBMC requires this
4. Then install **`plexbmc-v3.6.1.zip`**

> The order matters. PlexBMC will fail to load if `requests` is not installed first.

### F3 — Configure PlexBMC

In Kodi: **Add-ons → Video add-ons → PleXBMC → Configure** (or press C on the addon to open settings).

Set these fields:

| Setting | Value |
|---------|-------|
| **Connection → IP Address** | IP of your Plex Media Server |
| **Connection → Port** | `32400` |
| **Connection → Authentication token** | `YOUR_PLEX_USERNAME\|YOUR_PLEX_TOKEN` (format: `username\|token`) |
| **Playback → Transcoding** | Enabled |
| **Playback → Transcode type** | Universal |
| **Playback → Quality** | `1920x1080, 8Mbps` (or lower if your network is slow) |
| **Advanced → Manual server mode** | Enabled |
| **Advanced → Discovery** | Disabled |

> The token field format is `username|token`, e.g. `john|y5zPxk8EBx2Whtp6QkBm`. The username can be any string if using a Plex token directly.

---

## Part G — Apply PlexBMC Patches

Two Python patches are required to make PlexBMC work with Plex 1.43+ and without internet access. These fix:

1. **`plex.py`** — crash when plex.tv is unreachable (UnboundLocalError); token not found in manual mode
2. **`plexserver.py`** — Kodi 14 cannot handle Plex 1.43's two-level HLS master playlists; this resolves them before handing the URL to Kodi

Download **`patch_plexbmc.py`** from the [release page](https://github.com/yoavmagor/boxee-2026-yoavm/releases/tag/v1.0.0) and place it in the same directory as `start_kodi.py`.

**Before running, ensure:**
- `start_kodi.py` has the correct `HOST`, `PORT`, and `PASSWORD` for your Boxee Box
- Kodi is running on the Boxee Box
- PlexBMC is installed and configured (Part F)
- PlexBMC has been opened at least once (so backup files exist)

```bash
python3 patch_plexbmc.py
```

The script connects via telnet, reads the original backup files, applies the patches, and verifies the result. It is safe to re-run — it always patches from the `.bak` backup, never from a previously patched file.

**After patching, restart Kodi:**

```bash
python3 start_kodi.py --reboot-first
```

---

## Checking the Autostart Log

```sh
cat /tmp/kodi_autostart.log
```

Example of a successful boot:
```
Thu Apr  2 10:01:05 IST 2026: kodi_autostart.sh started
Thu Apr  2 10:01:07 IST 2026: Found Kodi at /tmp/mnt/69C4-44AF
Thu Apr  2 10:01:12 IST 2026: Starting Kodi from /tmp/mnt/69C4-44AF
```

---

## Troubleshooting

**Kodi doesn't start after reboot**
- Check the log: `cat /tmp/kodi_autostart.log`
- Verify the media is mounted: `ls /tmp/mnt/`
- Verify `boot.sh` has the autostart line: `grep kodi_autostart /data/hack/boot.sh`

**Log says "kodi.bin not found"**
- The media wasn't mounted within 60 seconds. Try reinserting (for USB) or rebooting with the SD card already in.
- Run manually: `sh /data/hack/kodi_autostart.sh`

**Kodi crashes immediately**
- Check the full log for error lines
- Ensure `/opt/local/lib/libgpg-error.so.0` exists on the Boxee Box (it's part of Boxee+Hacks)

**SD card not visible in Kodi after Kodi starts**
- Insert the SD card *before* booting — hot-plug after Kodi starts won't work without BoxeeHal running

**PlexBMC shows empty library / "Server offline"**
- Verify the patches were applied: `grep 'manual_token' /data/.kodi/addons/plugin.video.plexbmc-3.6.1/resources/lib/plex.py`
- Check that the `myplex_token` setting is set in the format `username|token`
- Restart Kodi after applying patches

**Playback fails with "Playback failed" error**
- Verify the plexserver.py patch is applied: `grep 'inner_url' /data/.kodi/addons/plugin.video.plexbmc-3.6.1/resources/lib/plexserver.py`
- Verify Plex server is reachable from the Boxee Box: telnet in and run `wget -q -O- http://YOUR_PLEX_IP:32400/identity`
- Check Kodi log: `tail -50 /data/.kodi/temp/kodi.log`

**Boot stalls for ~2 minutes every time**
- The boxee.tv DNS fix (Part B) was not applied. The box is trying to reach the dead boxee.tv domain.

**autostart script or boot.sh not present after install**
- You may have used the original Boxee+Hacks zip instead of `boxeehacks-kodi.zip`. Follow the manual setup steps in the Part D details block.

---

## How It Works

### Why not native SD card detection?

The Boxee Box SD slot is **not** a native SDHCI controller — it's wired through an internal USB card reader IC (Alcor Micro, USB ID `058f:6366`). A custom kernel module (`card_detector.ko`) polls this via SCSI and fires udev events on insertion.

When Boxee+Hacks' `BoxeeHal` is running, it receives mount notifications via `curl http://127.0.0.1:5700/storage.OnMount` and tells the UI about new storage. Since we kill BoxeeHal to start Kodi, hot-plug notifications are lost. The solution: **insert media before booting** so it's already mounted when Kodi starts.

### The autostart script (`kodi_autostart.sh`)

- Runs at boot via `/data/hack/boot.sh`
- Polls `/tmp/mnt/*/` for up to 60 seconds waiting for udev to mount the media
- UUID-independent — works regardless of which slot or what filesystem UUID the media has
- Kills Boxee, BoxeeLauncher, and BoxeeHal before starting Kodi
- Sets required environment:
  - `HOME=/data` — Kodi user data goes to `/data/.kodi/` (persistent, writable ext3)
  - `KODI_HOME` — tells Kodi where its application files are
  - `PYTHONHOME` / `PYTHONPATH` — bundled Python 2.7 (system Python is too old)
  - `LD_LIBRARY_PATH` — bundled libs first, then `/opt/local/lib` for system libs

### Why PlexBMC needs patches

Plex Media Server 1.43+ changed two things that break PlexBMC 3.6.1:

1. **Removed direct file serving** (`/library/parts/ID/HASH/file.ext`). All playback now goes through HLS transcoding.
2. **Changed HLS structure** to a two-level master playlist (`start.m3u8` → `session/UUID/base/index.m3u8`). Kodi 14's HLS demuxer only handles flat segment playlists, not master playlists.

Additionally, PlexBMC assumes internet access to plex.tv for authentication. Without it, a Python exception causes the server discovery to fail before loading any library.

The `patch_plexbmc.py` script fixes all three issues.

### Library notes

The Kodi build ships most of its dependencies as bundled `.so` files in the `lib/` directory on the media. A few libraries are sourced from the Boxee+Hacks system (`/opt/local/lib`):

| Library | Source |
|---------|--------|
| `libgpg-error.so.0` | `/opt/local/lib` (Boxee+Hacks) |
| All others | bundled in `lib/` on the media |

---

## File Layout on the Media

```
/                          ← root of USB stick / SD card
├── kodi.bin               ← Kodi 14 (Helix) binary for Intel CE4100
├── start-kodi.sh          ← manual launch helper (run from telnet)
├── lib/                   ← bundled shared libraries
├── addons/                ← Kodi addons
├── python2.7/             ← bundled Python 2.7 runtime
├── system/                ← Kodi system resources
├── userdata/              ← default userdata (profiles, sources)
├── language/              ← UI language files
├── sounds/                ← UI sounds
├── media/                 ← UI media assets
└── gconv/                 ← character encoding tables
```

Kodi's **user data** (settings, library databases, installed addons) is stored at `/data/.kodi/` on the Boxee Box's internal writable partition — not on the media. This persists across reboots and media swaps.

---

## Tested Environment

| Component | Details |
|-----------|---------|
| Hardware | Boxee Box (D-Link DSM-380, Intel CE4100, i686) |
| Firmware | Boxee+Hacks (modified — `boxeehacks-kodi.zip`) |
| Kodi version | 14.2 (Helix) |
| PlexBMC | 3.6.1 |
| Plex Media Server | 1.43.0 |
| Media tested | USB stick (FAT32, 8 GB), SD card (FAT32, 16 GB) |
| Host for scripts | macOS (Python 3.6+) |
