#!/usr/bin/env python3
"""
Patch PlexBMC plex.py on Boxee Box.
Reads backup, applies two patches, writes patched file back.

Patch 1: talk_to_myplex() — return early on ConnectionError/ReadTimeout
          (prevents UnboundLocalError when plex.tv is unreachable)
Patch 2: discover_all_servers() manual mode — extract token from settings
          when self.myplex_token is None
"""

import sys
import time

# Import connection settings from start_kodi.py (must be in the same directory).
# Edit HOST, PORT, and PASSWORD in start_kodi.py before running this script.
sys.path.insert(0, '.')
from start_kodi import BoxeeSession, HOST, PORT, PASSWORD

PLEX_PY = "/data/.kodi/addons/plugin.video.plexbmc-3.6.1/resources/lib/plex.py"
BACKUP  = PLEX_PY + ".bak"

RETURN_LINE = "            return '<?xml version=\"1.0\" encoding=\"UTF-8\"?><message status=\"offline\"></message>'"

def apply_patches(content):
    lines = content.splitlines(keepends=True)
    out = []
    i = 0
    patched = {"conn_error": False, "read_timeout": False, "local_server": False}

    while i < len(lines):
        line = lines[i]

        # Patch 1a — after ConnectionError printDebug.error, insert return
        if ('printDebug.error' in line and
                'offline or uncontactable' in line and
                not patched["conn_error"]):
            out.append(line)
            # Only insert if next line is NOT already a return
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if 'return' not in next_line:
                out.append(RETURN_LINE + '\n')
                patched["conn_error"] = True
            i += 1
            continue

        # Patch 1b — after ReadTimeout printDebug.info, insert return
        if ('printDebug.info' in line and
                'read timeout for' in line and
                not patched["read_timeout"]):
            out.append(line)
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if 'return' not in next_line:
                out.append(RETURN_LINE + '\n')
                patched["read_timeout"] = True
            i += 1
            continue

        # Patch 2 — replace local_server=PlexMediaServer(...token=self.myplex_token)
        if ('local_server=PlexMediaServer' in line and
                'token=self.myplex_token' in line and
                not patched["local_server"]):
            # Detect indentation
            indent = len(line) - len(line.lstrip())
            sp = ' ' * indent
            out.append(sp + 'manual_token = self.myplex_token\n')
            out.append(sp + 'if manual_token is None:\n')
            out.append(sp + "    stored = settings.get_setting('myplex_token')\n")
            out.append(sp + "    if stored and '|' in stored:\n")
            out.append(sp + "        manual_token = stored.split('|', 1)[1]\n")
            out.append(line.replace('token=self.myplex_token', 'token=manual_token'))
            patched["local_server"] = True
            i += 1
            continue

        out.append(line)
        i += 1

    return ''.join(out), patched


def read_file_via_telnet(sess, path):
    """Read a file from the Boxee Box using marker-delimited cat."""
    START = "BOXEE_FILE_START_4729"
    END   = "BOXEE_FILE_END_4729"
    raw = sess.run(f"printf '%s\\n' {START} && cat {path} && printf '%s\\n' {END}", timeout=60)
    s = raw.find(START)
    e = raw.find(END)
    if s == -1 or e == -1:
        raise RuntimeError(f"Markers not found in output. Got: {repr(raw[:300])}")
    # Skip the marker line itself (+ newline)
    content = raw[s + len(START):]
    content = content.lstrip('\r\n')
    end_pos = content.find(END)
    content = content[:end_pos].rstrip('\r\n')
    return content


def write_file_via_heredoc(sess, path, content):
    """Write content to a file on Boxee Box using a shell heredoc."""
    MARKER = "__PLEXPY_HEREDOC_EOF__"
    # Verify content doesn't contain our marker
    if MARKER in content:
        raise RuntimeError("Content contains heredoc marker — choose different marker")

    # Send the heredoc command then the content
    sess.send(f"cat > {path} << '{MARKER}'\n")
    time.sleep(0.2)

    # Send content in chunks to avoid buffer issues
    chunk_size = 1024
    for offset in range(0, len(content), chunk_size):
        chunk = content[offset:offset + chunk_size]
        sess.send(chunk)
        time.sleep(0.05)

    # Close heredoc
    sess.send(f"\n{MARKER}\n")
    time.sleep(1)
    # Drain prompt
    sess.read_until("BOXEE# ", timeout=10)


def main():
    print(f"Connecting to {HOST}:{PORT}...")
    sess = BoxeeSession(HOST, PORT)
    sess.login(PASSWORD)
    print("Connected.\n")

    # Step 1: read the backup
    print(f"Reading {BACKUP} ...")
    content = read_file_via_telnet(sess, BACKUP)
    print(f"  Read {len(content)} bytes, {content.count(chr(10))} lines")

    # Quick sanity check
    if 'talk_to_myplex' not in content or 'discover_all_servers' not in content:
        print("ERROR: backup doesn't look like plex.py — aborting")
        sess.close()
        sys.exit(1)

    # Step 2: apply patches
    patched_content, applied = apply_patches(content)
    print(f"Patches applied: {applied}")
    if not all(applied.values()):
        print("WARNING: not all patches were applied — check output above")

    # Verify the patches look correct
    if 'manual_token' not in patched_content:
        print("ERROR: patch 2 not in output")
        sess.close()
        sys.exit(1)

    # Step 3: write patched file
    print(f"\nWriting patched file to {PLEX_PY} ...")
    write_file_via_heredoc(sess, PLEX_PY, patched_content)

    # Step 4: verify
    size = sess.run(f"wc -c < {PLEX_PY}").strip()
    print(f"  Written file size: {size} bytes (original backup: {len(content.encode())} bytes)")

    print("\nVerification:")
    print(sess.run(f"grep -n 'status=.offline' {PLEX_PY}"))
    print(sess.run(f"grep -n 'manual_token' {PLEX_PY}"))

    # Check for obvious syntax errors (unmatched indentation near our patches)
    print("\nContext around talk_to_myplex patch:")
    print(sess.run(f"grep -n -A2 -B2 'offline or uncontactable' {PLEX_PY}"))

    print("\nContext around discover_all_servers patch:")
    print(sess.run(f"grep -n -A2 -B2 'manual_token' {PLEX_PY}"))

    sess.close()
    print("\nDone. Restart Kodi to apply changes.")


if __name__ == "__main__":
    main()
