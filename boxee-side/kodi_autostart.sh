#!/bin/sh
# kodi_autostart.sh — Auto-start Kodi when SD card is detected at boot.
# Scans /tmp/mnt/ for kodi.bin; UUID-independent.
#
# Place this file on the Boxee Box at: /data/hack/kodi_autostart.sh
# Then add this line to /data/hack/boot.sh:
#   sh /data/hack/kodi_autostart.sh &

LOG=/tmp/kodi_autostart.log
echo "$(date): kodi_autostart.sh started" > $LOG

# Wait up to 60 seconds for the Kodi SD card to be automounted
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
    echo "$(date): kodi.bin not found in /tmp/mnt/ — Kodi SD card not present." >> $LOG
    exit 1
fi

echo "$(date): Found Kodi at $KODI_DIR" >> $LOG

# --- Kill Boxee and KEEP it dead -------------------------------------------
# A single killall loses the race: /opt/boxee/run_boxee.sh is a loop that
# respawns Boxee the instant it dies, so Boxee comes back alive and squats on
# the SMD hardware video decoder — which makes Kodi play no video even though
# its UI works. Fix: kill the RESPAWNER first (so no new Boxee is spawned),
# then kill Boxee itself.
kill_respawner() {
    # run_boxee.sh runs as "/bin/sh ...", so killall by name won't match it.
    # Find it by scanning /proc cmdlines and kill the loop.
    for p in /proc/[0-9]*; do
        if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q run_boxee.sh; then
            kill "${p#/proc/}" 2>/dev/null
        fi
    done
}

kill_respawner
killall Boxee BoxeeLauncher BoxeeHal BoxeeApplication 2>/dev/null

# Belt-and-suspenders reaper: keep killing the respawner + Boxee in the
# background for a short window, in case the loop spawned a new child mid-kill.
(
    n=0
    while [ "$n" -lt 20 ]; do
        kill_respawner
        killall Boxee BoxeeLauncher BoxeeHal BoxeeApplication 2>/dev/null
        n=$((n + 1))
        sleep 1
    done
) &

# Wait until Boxee is confirmed gone before launching Kodi, so the SMD decoder
# is actually free. Require 3 consecutive clear polls, up to ~30s.
clear_count=0
for i in $(seq 1 30); do
    if pidof Boxee >/dev/null 2>&1; then
        clear_count=0
    else
        clear_count=$((clear_count + 1))
        [ "$clear_count" -ge 3 ] && break
    fi
    sleep 1
done
echo "$(date): Boxee confirmed down after ${i}s — launching Kodi" >> $LOG

cd "$KODI_DIR" || exit 1

export HOME=/data
export KODI_HOME="$KODI_DIR"
export PYTHONHOME="$KODI_DIR/python2.7"
export PYTHONPATH="$KODI_DIR/python2.7:$KODI_DIR/python2.7/lib-dynload"
export LD_LIBRARY_PATH="$KODI_DIR/lib:$KODI_DIR:/opt/local/lib:/opt/boxee/lib:$LD_LIBRARY_PATH"

echo "$(date): Starting Kodi from $KODI_DIR (HOME=$HOME)" >> $LOG
exec ./kodi.bin >> $LOG 2>&1
