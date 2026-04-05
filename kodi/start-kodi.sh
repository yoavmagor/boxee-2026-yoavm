#!/bin/sh
# start-kodi.sh - Manually launch Kodi on Boxee Box.
# Run this from the Boxee telnet shell if Kodi doesn't auto-start.
# Uses the directory this script lives in, so works from any mount path.

KODI_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$KODI_DIR" || exit 1

killall Boxee BoxeeLauncher BoxeeHal 2>/dev/null
sleep 2

export HOME=/data
export KODI_HOME="$KODI_DIR"
export PYTHONHOME="$KODI_DIR/python2.7"
export PYTHONPATH="$KODI_DIR/python2.7:$KODI_DIR/python2.7/lib-dynload"
export LD_LIBRARY_PATH="$KODI_DIR/lib:$KODI_DIR:/opt/local/lib:/opt/boxee/lib:$LD_LIBRARY_PATH"

exec ./kodi.bin
