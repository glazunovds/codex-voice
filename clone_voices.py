#!/usr/bin/env python3
"""Clone voices on ElevenLabs from local audio samples.

Prerequisites:
    export ELEVENLABS_API_KEY="your-key-here"
    pip install elevenlabs

Usage:
    python clone_voices.py

Reads .mp3 files from ./samples/ and creates instant voice clones.
Saves voice IDs to voices.json for use by the hook.
"""

import json
import os
import sys
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent / "samples"
VOICES_FILE = Path(__file__).parent / "voices.json"

# Voice metadata: filename (without .mp3) -> display name and context keywords
VOICE_CONFIG = {
    "bagirov": {
        "name": "Радислав Багиров",
        "context": "default",
    },
    "droceslav": {
        "name": "Дрочеслав сын Сергея",
        "context": "battle",
    },
    "vseslav": {
        "name": "Всеслав Чародей",
        "context": "magic",
    },
    "ящер": {
        "name": "Хитрый Ящер",
        "context": "error",
    },
    "podliy_yashcher": {
        "name": "Подлый Ящер",
        "context": "sneaky",
    },
}


def clone_voice(name: str, audio_path: str) -> str:
    """Create an instant voice clone on ElevenLabs, return voice_id."""
    from elevenlabs.client import ElevenLabs

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: set ELEVENLABS_API_KEY environment variable")
        sys.exit(1)

    client = ElevenLabs(api_key=api_key)

    with open(audio_path, "rb") as f:
        voice = client.voices.ivc.create(
            name=f"codex-voice-{name}",
            files=[f],
        )

    return voice.voice_id


def main():
    # Load existing voices
    voices = {}
    if VOICES_FILE.exists():
        voices = json.loads(VOICES_FILE.read_text())

    if not SAMPLES_DIR.exists() or not list(SAMPLES_DIR.glob("*.mp3")):
        print(f"No samples found in {SAMPLES_DIR}/")
        print("Place .mp3 voice samples there with names matching:")
        for key in VOICE_CONFIG:
            print(f"  {key}.mp3  ->  {VOICE_CONFIG[key]['name']}")
        print("\nYou can also run 'python extract_samples.py' to auto-download.")
        sys.exit(1)

    for mp3 in sorted(SAMPLES_DIR.glob("*.mp3")):
        key = mp3.stem
        if key in voices:
            print(f"  {key}: already cloned (voice_id: {voices[key]['voice_id']})")
            continue

        config = VOICE_CONFIG.get(key, {"name": key, "context": "default"})
        print(f"  Cloning: {config['name']} from {mp3.name}...")

        try:
            voice_id = clone_voice(key, str(mp3))
            voices[key] = {
                "voice_id": voice_id,
                "name": config["name"],
                "context": config["context"],
            }
            print(f"  -> voice_id: {voice_id}")
        except Exception as e:
            print(f"  Error cloning {key}: {e}")

    VOICES_FILE.write_text(json.dumps(voices, indent=2, ensure_ascii=False))
    print(f"\nVoices saved to {VOICES_FILE}")


if __name__ == "__main__":
    main()
