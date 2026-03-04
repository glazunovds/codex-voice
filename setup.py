#!/usr/bin/env python3
"""One-command setup for codex-voice.

Usage:
    python setup.py              # install deps + configure hook
    python setup.py --uninstall  # remove hook from codex config
"""

import os
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent / "codex_hook.py"
CODEX_CONFIG = Path.home() / ".codex" / "config.toml"
NOTIFY_LINE = f'notify = ["python3", "{HOOK_SCRIPT.as_posix()}"]'


def install():
    print("1. Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r",
                    str(Path(__file__).parent / "requirements.txt")],
                   check=True)

    print("\n2. Checking .env...")
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        try:
            key = input("   Enter your ElevenLabs API key (or press Enter to skip): ").strip()
        except EOFError:
            key = ""
        if key:
            env_file.write_text(f"ELEVENLABS_API_KEY={key}\n")
            print("   Saved to .env")
        else:
            print("   Skipped. Voice will use free edge-tts fallback.")
            print("   To add later: echo ELEVENLABS_API_KEY=sk_xxx > .env")

    print("\n3. Configuring Codex CLI hook...")
    CODEX_CONFIG.parent.mkdir(parents=True, exist_ok=True)

    if CODEX_CONFIG.exists():
        content = CODEX_CONFIG.read_text(encoding="utf-8")
        if "codex_hook.py" in content:
            print("   Hook already configured.")
        elif any(line.strip().startswith("notify") for line in content.splitlines()):
            print("   WARNING: Codex already has a notify hook.")
            print(f"   Add manually: {NOTIFY_LINE}")
        else:
            # Prepend notify line
            CODEX_CONFIG.write_text(NOTIFY_LINE + "\n" + content, encoding="utf-8")
            print("   Added notify hook to config.toml")
    else:
        CODEX_CONFIG.write_text(NOTIFY_LINE + "\n", encoding="utf-8")
        print("   Created config.toml with notify hook")

    print("\n4. Checking voices.json...")
    voices_file = Path(__file__).parent / "voices.json"
    if voices_file.exists():
        print("   Voice clones found.")
    else:
        print("   No voices.json — using edge-tts fallback.")
        print("   To set up cloned voices: add samples/ and run python clone_voices.py")

    print("\nDone! Restart Codex CLI to activate voice.")


def uninstall():
    print("Removing codex-voice hook...")
    if CODEX_CONFIG.exists():
        lines = CODEX_CONFIG.read_text(encoding="utf-8").splitlines()
        lines = [l for l in lines if "codex_hook.py" not in l]
        CODEX_CONFIG.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("Hook removed from config.toml")
    else:
        print("No config.toml found.")
    print("Done. Dependencies not removed (run pip uninstall manually if needed).")


if __name__ == "__main__":
    if "--uninstall" in sys.argv:
        uninstall()
    else:
        install()
