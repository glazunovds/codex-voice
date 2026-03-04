#!/usr/bin/env python3
"""codex-voice control: stop, mute, unmute, status.

Usage:
    python ctl.py stop    — kill current playback
    python ctl.py mute    — mute all future voice
    python ctl.py unmute  — unmute voice
    python ctl.py status  — show current state
"""

import os
import sys
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
PID_FILE = BASE / "voice.pid"
STOP_FILE = BASE / "voice.stop"
MUTE_FILE = BASE / "voice.mute"


def stop():
    STOP_FILE.touch()
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               capture_output=True, check=False)
            else:
                import signal
                os.kill(pid, signal.SIGTERM)
            PID_FILE.unlink(missing_ok=True)
        except (ValueError, ProcessLookupError, OSError):
            pass
    print("Stopped.")


def mute():
    stop()
    MUTE_FILE.touch()
    print("Muted.")


def unmute():
    MUTE_FILE.unlink(missing_ok=True)
    print("Unmuted.")


def status():
    muted = MUTE_FILE.exists()
    playing = PID_FILE.exists()
    pid = ""
    if playing:
        try:
            pid = PID_FILE.read_text().strip()
        except OSError:
            pass
    print(f"Voice: {'MUTED' if muted else 'ACTIVE'}")
    print(f"Playing: {'yes (PID ' + pid + ')' if playing else 'no'}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"stop": stop, "mute": mute, "unmute": unmute, "status": status}.get(cmd, status)()
