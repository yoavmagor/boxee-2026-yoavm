#!/usr/bin/env python3
"""
Boxee Box Kodi Starter
Connects to Boxee Box via telnet, kills Boxee/BoxeeHal, starts Kodi.
Usage: python3 start_kodi.py [--wait-for-boot]

CONFIGURATION — edit the four variables below before first use:
  HOST      IP address of your Boxee Box (check your router's DHCP table)
  PORT      Telnet port — always 2323 for Boxee+Hacks
  PASSWORD  Boxee+Hacks telnet password (default is "secret" on a fresh install)
  USB_PATH  Mount path of the Kodi SD card or USB stick on the Boxee Box.
            Find it by telnetting in and running: ls /tmp/mnt/
            It will look like /tmp/mnt/XXXX-XXXX (the UUID of your storage media).
"""

import socket
import time
import sys
import argparse

HOST = "192.168.1.X"        # <-- SET THIS: your Boxee Box IP address
PORT = 2323                  # telnet port, do not change
PASSWORD = "secret"          # <-- SET THIS: your Boxee+Hacks password
USB_PATH = "/tmp/mnt/XXXX-XXXX"  # <-- SET THIS: run `ls /tmp/mnt/` on the box to find it

IAC  = bytes([255])
DONT = bytes([254])
DO   = bytes([253])
WONT = bytes([252])
WILL = bytes([251])
SB   = bytes([250])
SE   = bytes([240])


def negotiate(data):
    responses = b""
    out = b""
    i = 0
    while i < len(data):
        if data[i:i+1] == IAC:
            cmd = data[i+1:i+2]
            if cmd in (DO, DONT, WILL, WONT):
                opt = data[i+2:i+3]
                if cmd == DO:
                    responses += IAC + WONT + opt
                elif cmd == WILL:
                    responses += IAC + DONT + opt
                i += 3
            elif cmd == SB:
                end = data.find(IAC + SE, i + 2)
                i = end + 2 if end != -1 else len(data)
            else:
                i += 2
        else:
            out += data[i:i+1]
            i += 1
    return out, responses


class BoxeeSession:
    def __init__(self, host, port, timeout=20):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(timeout)
        self.s.connect((host, port))
        self.buf = b""

    def _recv(self, t=3):
        self.s.settimeout(t)
        try:
            chunk = self.s.recv(4096)
            if chunk:
                cleaned, responses = negotiate(chunk)
                if responses:
                    self.s.sendall(responses)
                self.buf += cleaned
        except socket.timeout:
            pass

    def read_until(self, *markers, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            for m in markers:
                if m.encode() in self.buf:
                    data = self.buf
                    self.buf = b""
                    return data.decode("utf-8", "replace")
            self._recv(min(1, deadline - time.time()))
        data = self.buf
        self.buf = b""
        return data.decode("utf-8", "replace")

    def send(self, text):
        self.s.sendall(text.encode())

    def run(self, cmd, timeout=15):
        self.send(cmd + "\n")
        time.sleep(0.5)
        return self.read_until("BOXEE# ", timeout=timeout)

    def login(self, password):
        self.read_until("assword:", "ogin:", timeout=10)
        self.send(password + "\n")
        self.read_until("#", "$", timeout=10)
        self.send("PS1='BOXEE# '\n")
        time.sleep(1)
        self.read_until("BOXEE# ", timeout=5)

    def close(self):
        self.s.close()


def wait_for_boxee(host, port, timeout=120):
    print(f"Waiting for Boxee Box to come back online", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.socket()
            s.settimeout(3)
            s.connect((host, port))
            s.close()
            print(" connected!")
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            print(".", end="", flush=True)
            time.sleep(3)
    print(" TIMED OUT")
    return False


def start_kodi(wait_for_boot=False):
    if wait_for_boot:
        time.sleep(5)  # Give it a moment after reboot signal
        if not wait_for_boxee(HOST, PORT):
            print("ERROR: Boxee Box did not come back online.")
            sys.exit(1)
        time.sleep(5)  # Let boot settle (udev/automount needs to finish)
        print("Boot settled. Connecting...")

    print(f"Connecting to {HOST}:{PORT}...")
    try:
        sess = BoxeeSession(HOST, PORT)
    except Exception as e:
        print(f"ERROR: Cannot connect: {e}")
        sys.exit(1)

    print("Logging in...")
    sess.login(PASSWORD)
    print("Logged in.")

    # Kill Boxee stack (Boxee, BoxeeLauncher, BoxeeHal)
    print("Stopping Boxee...")
    sess.run("killall Boxee BoxeeLauncher BoxeeHal 2>/dev/null; sleep 2")

    # Check that USB stick with Kodi is mounted
    out = sess.run(f"ls {USB_PATH}/kodi.bin 2>/dev/null && echo KODI_FOUND || echo KODI_MISSING")
    if "KODI_MISSING" in out:
        print(f"ERROR: kodi.bin not found at {USB_PATH}/kodi.bin")
        print("Is the USB stick mounted? Check /tmp/mnt/ contents:")
        print(sess.run("ls /tmp/mnt/"))
        sess.close()
        sys.exit(1)

    # Show mounted storage before starting Kodi
    print("\nMounted storage at startup:")
    mounts = sess.run("mount | grep '/tmp/mnt' | grep -v 'upnp'")
    print(mounts)

    # Set up environment and launch Kodi in a background screen-like session
    # Using nohup + setsid so it survives telnet disconnect
    print("Starting Kodi...")
    setup_cmds = (
        f"cd {USB_PATH} && "
        f"export KODI_HOME={USB_PATH} && "
        f"export PYTHONHOME={USB_PATH}/python2.7 && "
        f"export PYTHONPATH={USB_PATH}/python2.7 && "
        f"export LD_LIBRARY_PATH={USB_PATH}/lib:{USB_PATH}:$LD_LIBRARY_PATH && "
        f"nohup ./kodi.bin > /tmp/kodi.log 2>&1 &"
    )
    sess.run(setup_cmds, timeout=5)
    time.sleep(2)

    # Confirm Kodi is running
    out = sess.run("sleep 2 && pidof kodi.bin && echo KODI_RUNNING || echo KODI_NOT_RUNNING")
    if "KODI_RUNNING" in out:
        print("Kodi is running!")
    else:
        print("Warning: kodi.bin PID not found yet (may still be starting)")
        print(out)

    # Show what storage Kodi can see
    print("\nStorage visible at Kodi start:")
    print(sess.run("ls /tmp/mnt/"))

    sess.close()
    print("Done. Kodi started on Boxee Box.")


def reboot_boxee():
    print(f"Connecting to {HOST}:{PORT} to reboot...")
    sess = BoxeeSession(HOST, PORT)
    sess.login(PASSWORD)
    print("Sending reboot command...")
    sess.send("reboot\n")
    time.sleep(1)
    sess.close()
    print("Reboot command sent.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Kodi on Boxee Box")
    parser.add_argument("--reboot-first", action="store_true",
                        help="Reboot Boxee Box first, then start Kodi after boot")
    args = parser.parse_args()

    if args.reboot_first:
        reboot_boxee()
        start_kodi(wait_for_boot=True)
    else:
        start_kodi(wait_for_boot=False)
