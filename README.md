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

## Quick setup

### 1. Install dependencies

```bash
pip install elevenlabs edge-tts imageio-ffmpeg
```

### 2. Clone the repo

```bash
git clone <repo-url> /path/to/codex-voice
cd /path/to/codex-voice
```

### 3. Set up ElevenLabs API key

Get a key from https://elevenlabs.io/app/settings/api-keys (Starter plan $5/mo required for voice cloning).

```bash
echo "ELEVENLABS_API_KEY=sk_your_key_here" > .env
```

### 4. Create voice clones

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

### 5. Hook into Codex CLI

Add to `~/.codex/config.toml`:

```toml
notify = ["python3", "/path/to/codex-voice/codex_hook.py"]
```

Done! Codex will now voice every Russian response.

## Agent setup (automated)

If you're an AI agent setting this up, run these commands:

```bash
# Install deps
pip install elevenlabs edge-tts imageio-ffmpeg

# Set API key
echo "ELEVENLABS_API_KEY=sk_xxx" > /path/to/codex-voice/.env

# Hook into Codex (add to first line of config)
# In ~/.codex/config.toml add:
# notify = ["python3", "/path/to/codex-voice/codex_hook.py"]
```

Voice samples and cloning must be done manually (requires human to select audio clips).

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
├── clone_voices.py    # Clone voices on ElevenLabs from samples/
├── ctl.py             # Voice control (stop/mute/unmute/status)
├── voices.json        # Voice IDs and context mapping (generated)
├── .env               # API key (not committed)
├── samples/           # Voice audio clips for cloning (not committed)
├── AGENTS.md          # Instructions for AI agents
└── README.md          # This file
```
