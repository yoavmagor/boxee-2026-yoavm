#!/bin/sh
# /data/hack/boot.sh — Boxee+Hacks boot script (modified to add Kodi autostart)
#
# This is the stock Boxee+Hacks boot.sh with one added line at the end:
#   sh /data/hack/kodi_autostart.sh &
#
# To apply: paste this over /data/hack/boot.sh on the Boxee Box via telnet.
# The /data partition is writable ext3 and survives reboots.

sh /data/hack/skin.sh &
sh /data/hack/splash.sh &
sh /data/hack/visualiser.sh &
sh /data/hack/subtitles.sh &
sh /data/hack/logo.sh &
sh /data/hack/apps.sh &
sh /data/hack/network.sh &
sh /data/hack/telnet.sh &
sh /data/hack/ftp.sh &
sh /data/hack/plugins.sh &
sh /data/hack/kodi_autostart.sh &
