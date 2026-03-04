# codex-voice

Auto-voices Russian-language [Codex CLI](https://github.com/openai/codex) responses using **"Древние русы против ящеров"** meme voices via ElevenLabs.

Each sentence is voiced by a different character based on context:

| Voice | Triggers on |
|---|---|
| **Радислав Багиров** | Default narrator — explanations, summaries |
| **Дрочеслав сын Сергея** | Destructive actions — delete, deploy, refactor, fix, merge |
| **Всеслав Чародей** | Wisdom — config, architecture, databases, Docker, types |
| **Хитрый Ящер** | Errors — bugs, crashes, exceptions, test failures |
| **Подлый Ящер** | Sneaky issues — warnings, deprecations, security, tech debt |

## Quick setup (automated)

```bash
git clone https://github.com/glazunovds/codex-voice.git
cd codex-voice
python setup.py
```

This will:
1. Install Python dependencies
2. Prompt for your ElevenLabs API key (optional — skips to free edge-tts fallback)
3. Auto-configure the `notify` hook in `~/.codex/config.toml`
4. Check for `voices.json` (cloned voices)
5. On Linux/macOS: check for an audio player (`mpv`, `ffplay`, or `paplay`)

To uninstall: `python setup.py --uninstall`

## Platform support

| Platform | Audio backend | Notes |
|---|---|---|
| **Windows** | MCI (built-in) | No extra software needed |
| **Linux** | mpv / ffplay / paplay | Install one: `sudo apt install mpv` |
| **macOS** | mpv / ffplay | Install via: `brew install mpv` |

## Manual setup

### 1. Create voice clones (optional)

Get a key from https://elevenlabs.io/app/settings/api-keys (Starter plan $5/mo required for voice cloning).

```bash
echo "ELEVENLABS_API_KEY=sk_your_key_here" > .env
```

You need ~30 second voice samples for each character. Get them from:
- [SteosVoice Telegram bot](https://cybervoice.io/ru/voices/rusy-protiv-yashcherov.html) — generate from text prompts
- YouTube — extract from original Багиров lectures
- The Steam game "Русы против ящеров"

Place samples in `samples/` directory:
```
samples/
├── bagirov.mp3           # Радислав Багиров (narrator)
├── droceslav.mp3         # Дрочеслав (warrior)
├── vseslav.mp3           # Всеслав Чародей (wizard)
├── podliy_yashcher.mp3   # Подлый Ящер (sneaky villain)
└── ящер.mp3              # Хитрый Ящер (main villain)
```

Clone them:
```bash
python clone_voices.py
```

This creates `voices.json` with ElevenLabs voice IDs.

### 2. Manual hook setup (if not using setup.py)

Add to `~/.codex/config.toml`:

```toml
notify = ["python3", "/path/to/codex-voice/codex_hook.py"]
```

Done! Codex will now voice every Russian response.

## Voice controls

From any terminal:

```bash
python ctl.py stop      # Kill current playback immediately
python ctl.py mute      # Mute all future voice output
python ctl.py unmute    # Re-enable voice output
python ctl.py status    # Show current state (MUTED/ACTIVE)
```

Inside Codex CLI, just say:
- **"замолчи"** / **"mute voice"** — mutes voice
- **"говори"** / **"unmute voice"** — unmutes voice
- **"стоп"** / **"stop"** — stops current playback

## Configuration

Environment variables (set in `.env` or system env):

| Variable | Default | Description |
|---|---|---|
| `ELEVENLABS_API_KEY` | — | Required for cloned voices |
| `CODEX_VOICE_VOLUME` | `0.1` | Playback volume (0.0–1.0) |
| `CODEX_VOICE_SPEED` | `0.75` | Playback speed (0.75 = 25% slower) |
| `CODEX_VOICE_ENGINE` | `auto` | Force `elevenlabs` or `edge` |

## Fallback

Without ElevenLabs (no API key / no `voices.json`), falls back to **edge-tts** with `ru-RU-DmitryNeural` voice. Free, no API key needed, but no meme voices.

## Files

```
codex-voice/
├── codex_hook.py      # Main Codex notify hook
├── setup.py           # One-command install/uninstall
├── clone_voices.py    # Clone voices on ElevenLabs from samples/
├── ctl.py             # Voice control (stop/mute/unmute/status)
├── voices.json        # Voice IDs and context mapping (generated)
├── .env               # API key (not committed)
├── samples/           # Voice audio clips for cloning (not committed)
├── AGENTS.md          # Instructions for AI agents
└── README.md          # This file
```
