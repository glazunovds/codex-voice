#!/usr/bin/env python3
"""Codex CLI notify hook: voice Russian text using Древние Русы voices.

Uses ElevenLabs cloned voices if available (voices.json), falls back to edge-tts.
Splits text into sentences for fast streaming playback.

Setup: add to ~/.codex/config.toml:
    notify = ["python3", "D:/work/ideas/codex-voice/codex_hook.py"]

Env vars:
    ELEVENLABS_API_KEY  - required for cloned voices
    CODEX_VOICE_VOLUME  - playback volume 0.0-1.0 (default 0.5)
    CODEX_VOICE_ENGINE  - "elevenlabs" or "edge" (default: auto-detect)
"""

import asyncio
import json
import os
import re
import sys
import tempfile
import subprocess
from pathlib import Path

# Load .env from script directory
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().strip().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

EDGE_VOICE = "ru-RU-DmitryNeural"
PID_FILE = Path(__file__).parent / "voice.pid"
STOP_FILE = Path(__file__).parent / "voice.stop"
MUTE_FILE = Path(__file__).parent / "voice.mute"
VOLUME = float(os.environ.get("CODEX_VOICE_VOLUME", "0.1"))
SPEED = float(os.environ.get("CODEX_VOICE_SPEED", "0.75"))  # 0.75 = 25% slower
VOICES_FILE = Path(__file__).parent / "voices.json"

# ffmpeg from imageio_ffmpeg (already installed)
try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = None

# Context keywords for voice selection
# Багиров = default narrator (explanations, general dev talk, summaries)
# Дрочеслав = aggressive actions (delete, refactor, deploy, build, destroy, fix, victory)
# Всеслав Чародей = wisdom/config (architecture, config, types, design, infra, databases, deep knowledge)
# Хитрый Ящер = errors/failures (bugs, exceptions, crashes, broken things)
# Подлый Ящер = sneaky issues (warnings, deprecations, security, tech debt, hidden problems)
CONTEXT_KEYWORDS = {
    "error": [
        # Errors & crashes
        "ошибк", "error", "fail", "bug", "exception", "traceback", "не удалось", "проблем",
        "crash", "broken", "сломан", "падени", "panic", "fatal", "critical", "абенд",
        "cannot", "undefined", "null pointer", "segfault", "reject", "timeout", "timed out",
        # HTTP errors
        "500", "502", "503", "404", "403", "401",
        # Runtime errors
        "typeerror", "referenceerror", "syntaxerror", "nullpointerexception",
        "stackoverflow", "outofmemory", "heap", "core dump",
        # Build failures
        "compilation error", "ошибка компиляц", "не компилир", "build fail",
        "cannot find module", "module not found", "не найден модуль",
        # Test failures
        "тест упал", "тесты упали", "test failed", "assert", "expect",
        "красные тесты", "failed to", "не прошёл", "не прошел",
        # DB errors
        "deadlock", "connection refused", "connection reset", "сonnection lost",
    ],
    "battle": [
        # Destructive actions
        "удалил", "удали", "удаляю", "уничтож", "очисти", "зачист", "стёр", "снёс",
        "drop", "rm ", "rm -rf", "truncate", "purge", "wipe", "nuke",
        # Refactoring & rewrites
        "рефакторинг", "refactor", "переписал", "rewrite", "перенёс", "переделал",
        "разделил", "split", "extract", "вынес", "decompos",
        # Deployment & ops
        "deploy", "деплой", "деплоим", "выкатил", "выкатыва", "релиз", "release",
        "rollback", "откатил", "откатыва",
        # Build & compile
        "build", "сборк", "собрал", "собираю", "компиляц", "скомпилир",
        # Migrations
        "миграц", "migrat", "migrate",
        # Process management
        "kill", "restart", "перезапус", "стопнул", "остановил", "запустил", "start",
        # Git battle
        "force push", "merge", "мерж", "rebase", "cherry-pick", "squash",
        "resolved", "conflict", "конфликт",
        # Fixes & victories
        "fixed", "исправил", "починил", "пофиксил", "решил", "разобрался",
        "готово", "сделано", "done", "complete", "завершён", "успешно",
        "работает", "заработало", "прошли", "зелёные",
    ],
    "magic": [
        # Configuration
        "config", "конфиг", "настро", "setting", "переменн", "env", ".env",
        "toml", "yaml", "yml", "json config", "dotenv",
        # Architecture & patterns
        "архитектур", "design", "pattern", "паттерн", "принцип", "solid",
        "абстракц", "abstract", "наследован", "inherit", "полиморф", "инкапсуляц",
        "декоратор", "decorator", "фабрик", "factory", "singleton", "observer",
        "стратеги", "strategy", "adapter", "facade", "фасад",
        # Types & interfaces
        "тип", "type", "interface", "интерфейс", "generic", "дженерик",
        "schema", "схем", "enum", "model", "модел", "entity", "dto",
        # Infrastructure & DevOps
        "kafka", "clickhouse", "elasticsearch", "rabbitmq", "celery",
        "docker", "dockerfile", "compose", "kubernetes", "k8s", "helm",
        "terraform", "ansible", "ci/cd", "pipeline", "jenkins", "github actions",
        "infra", "инфраструктур", "nginx", "apache", "caddy", "traefik",
        "redis", "memcached", "кэш", "cache",
        # Databases
        "database", "базы данных", "бд", "postgres", "mysql", "mongo", "sqlite",
        "orm", "prisma", "typeorm", "sequelize", "drizzle", "knex",
        "индекс", "index", "партицион", "partition", "репликац", "шардир",
        "запрос", "query", "sql", "nosql", "миграц схем",
        # Languages & frameworks
        "go ", "golang", "java", "spring", "boot", "kotlin",
        "angular", "react", "vue", "svelte", "next", "nuxt", "nest",
        "ngrx", "redux", "store", "стор", "reducer", "action", "effect", "selector",
        "rxjs", "observable", "subscribe", "pipe",
        # Styling
        "style", "стил", "css", "scss", "sass", "less", "tailwind", "bootstrap",
        "тем", "theme", "palette", "цвет", "color", "шрифт", "font", "layout",
        # Networking & API
        "api", "rest", "graphql", "grpc", "websocket", "endpoint", "эндпоинт",
        "роут", "route", "маршрут", "middleware", "перехватчик", "interceptor",
        "авториз", "auth", "jwt", "oauth", "token", "сессия", "session",
    ],
    "sneaky": [
        # Warnings & deprecations
        "warning", "предупрежд", "deprecated", "устарел", "устаревш",
        "will be removed", "будет удалён", "не рекомендуется",
        # Security
        "vulnerab", "уязвим", "security", "безопасност", "xss", "csrf", "injection",
        "инъекц", "exploit", "атак", "breach", "утечк", "leak", "exposure",
        # Technical debt & hacks
        "debt", "долг", "техдолг", "tech debt",
        "todo", "fixme", "xxx", "hack", "хак", "workaround", "обходн",
        "костыл", "crutch", "временно", "temporary", "потом", "later",
        # Legacy & smell
        "legacy", "устаревш", "старый код", "код пахнет", "code smell",
        "антипаттерн", "anti-pattern", "spaghetti", "спагетти",
        "god object", "god class", "монолит",
        # Hidden problems
        "подозритель", "suspicious", "weird", "странн", "непонятн",
        "неочевидн", "неявн", "implicit", "side effect", "побочн",
        "race condition", "гонк", "утечка памяти", "memory leak",
        # Lint & quality
        "lint", "eslint", "prettier", "sonar", "complexity", "сложност",
        "тест не", "test fail", "flaky", "нестабильн", "coverage", "покрыти",
        # Performance
        "медленн", "slow", "performance", "производительн", "оптимиз",
        "bottleneck", "узкое место", "n+1", "лишн", "redundant", "избыточн",
    ],
}


def has_russian(text: str) -> bool:
    return bool(re.search("[а-яА-ЯёЁ]", text))


def load_voices() -> dict | None:
    """Load cloned voice config from voices.json."""
    if not VOICES_FILE.exists():
        return None
    try:
        voices = json.loads(VOICES_FILE.read_text(encoding="utf-8"))
        if not voices:
            return None
        return voices
    except (json.JSONDecodeError, OSError):
        return None


def pick_voice(text: str, voices: dict) -> tuple[str, str]:
    """Pick voice_id and name based on text context. Returns (voice_id, name)."""
    text_lower = text.lower()

    # Check context keywords against voice configs
    for key, voice in voices.items():
        context = voice.get("context", "")
        if context == "default":
            continue
        for ctx_category in context.split(","):
            ctx_category = ctx_category.strip()
            keywords = CONTEXT_KEYWORDS.get(ctx_category, [ctx_category])
            if any(kw in text_lower for kw in keywords):
                return voice["voice_id"], voice["name"]

    # Fall back to default voice
    for key, voice in voices.items():
        if voice.get("context") == "default":
            return voice["voice_id"], voice["name"]

    # Just use the first voice
    first = next(iter(voices.values()))
    return first["voice_id"], first["name"]


def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    parts = re.split(r"(?<=[.!?»…])\s+", text.strip())
    sentences = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if sentences and len(sentences[-1]) < 40:
            sentences[-1] += " " + part
        else:
            sentences.append(part)
    return [s for s in sentences if s.strip()]


# --- ElevenLabs TTS ---

def synth_elevenlabs(text: str, voice_id: str) -> str:
    """Synthesize using ElevenLabs API, return path to mp3."""
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

    audio_iter = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    for chunk in audio_iter:
        tmp.write(chunk)
    tmp.close()
    return tmp.name


# --- Audio post-processing ---

def post_process(path: str) -> str:
    """Slow down and normalize volume via ffmpeg."""
    if not FFMPEG:
        return path
    out = path + ".processed.mp3"
    # atempo for speed, loudnorm for consistent volume across voices
    subprocess.run([
        FFMPEG, "-y", "-i", path,
        "-filter:a", f"atempo={SPEED},loudnorm=I=-16:TP=-1.5:LRA=11",
        "-q:a", "2", out,
    ], check=True, capture_output=True)
    os.unlink(path)
    return out


# --- Playback ---

def play_audio(path: str):
    if sys.platform == "win32":
        import ctypes
        winmm = ctypes.windll.winmm
        # Use Windows MCI — no window, background playback, volume control
        abs_path = os.path.abspath(path).replace("\\", "/")
        alias = f"cv{id(path)}"
        winmm.mciSendStringW(f'open "{abs_path}" type mpegvideo alias {alias}', None, 0, 0)
        vol = int(VOLUME * 1000)  # MCI volume: 0-1000
        winmm.mciSendStringW(f'setaudio {alias} volume to {vol}', None, 0, 0)
        winmm.mciSendStringW(f'play {alias} wait', None, 0, 0)
        winmm.mciSendStringW(f'close {alias}', None, 0, 0)
    else:
        for player in ["mpv --no-video", "ffplay -nodisp -autoexit", "aplay"]:
            cmd = player.split() + [path]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue


# --- Main pipeline ---

def speak_sequential(text: str):
    """Split into sentences, synthesize and play each one sequentially."""
    sentences = split_sentences(text)
    if not sentences:
        return

    voices = load_voices()
    use_elevenlabs = (
        voices
        and os.environ.get("ELEVENLABS_API_KEY")
        and os.environ.get("CODEX_VOICE_ENGINE", "auto") != "edge"
    )

    # Kill previous voice process if still running
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            if old_pid != os.getpid():
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/PID", str(old_pid), "/T", "/F"],
                                   capture_output=True, check=False)
                else:
                    import signal
                    os.kill(old_pid, signal.SIGTERM)
        except (ValueError, ProcessLookupError, OSError):
            pass

    PID_FILE.write_text(str(os.getpid()))
    STOP_FILE.unlink(missing_ok=True)

    for sentence in sentences:
        # Check for graceful stop signal between sentences
        if STOP_FILE.exists():
            STOP_FILE.unlink(missing_ok=True)
            break
        if use_elevenlabs:
            voice_id, _ = pick_voice(sentence, voices)
            path = synth_elevenlabs(sentence, voice_id)
        else:
            import edge_tts
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.close()
            asyncio.run(edge_tts.Communicate(sentence, EDGE_VOICE).save(tmp.name))
            path = tmp.name
        path = post_process(path)
        play_audio(path)
        os.unlink(path)

    PID_FILE.unlink(missing_ok=True)
    STOP_FILE.unlink(missing_ok=True)


def main():
    if len(sys.argv) < 2:
        return

    try:
        data = json.loads(sys.argv[1])
    except (json.JSONDecodeError, IndexError):
        return

    if data.get("type") != "agent-turn-complete":
        return

    # Muted — skip entirely
    if MUTE_FILE.exists():
        return

    text = data.get("last-assistant-message", "")
    if not text or not has_russian(text):
        return

    if len(text) > 5000:
        text = text[:5000]

    speak_sequential(text)


if __name__ == "__main__":
    main()
