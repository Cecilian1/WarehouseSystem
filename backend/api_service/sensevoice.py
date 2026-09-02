"""Local SenseVoice transcription through the standalone FunASR runtime."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNTIME_DIR = PROJECT_ROOT / "bin" / "funasr-llamacpp"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "sensevoice" / "sensevoice-small-q8.gguf"
RUNTIME_NAMES = ("llama-funasr-sensevoice.exe", "llama-funasr-sensevoice")


class SenseVoiceUnavailableError(RuntimeError):
    pass


class SenseVoiceTranscriptionError(RuntimeError):
    pass


def _configured_path(name: str) -> Path | None:
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser().resolve() if value else None


def runtime_path() -> Path:
    configured = _configured_path("WAREHOUSE_SENSEVOICE_BIN")
    if configured:
        return configured
    for name in RUNTIME_NAMES:
        matches = list(DEFAULT_RUNTIME_DIR.rglob(name)) if DEFAULT_RUNTIME_DIR.exists() else []
        if matches:
            return matches[0]
    return DEFAULT_RUNTIME_DIR / RUNTIME_NAMES[0]


def model_path() -> Path:
    return _configured_path("WAREHOUSE_SENSEVOICE_MODEL") or DEFAULT_MODEL_PATH


def status() -> dict[str, Any]:
    binary = runtime_path()
    model = model_path()
    return {
        "ready": binary.is_file() and model.is_file(),
        "runtimePath": str(binary),
        "runtimeExists": binary.is_file(),
        "modelPath": str(model),
        "modelExists": model.is_file(),
        "model": "SenseVoiceSmall Q8 GGUF",
    }


def _extract_transcript(output: str) -> str:
    lines = [line.strip() for line in output.replace("\r", "\n").split("\n") if line.strip()]
    timestamped: list[str] = []
    for line in lines:
        match = re.match(r"^\[[^]]+\]\s*(.+)$", line)
        if match and "-->" in line:
            text = match.group(1)
            text = text.split("]", 1)[-1].strip() if "]" in text else text
            if text:
                timestamped.append(text)
    if timestamped:
        return "".join(timestamped).strip(" \t\r\n，。！？、,.!?;；:：")

    ignored_prefixes = (
        "system_info:", "main:", "sensevoice", "[sensevoice]", "ggml_", "llama_", "load ", "sampling ",
    )
    candidates = [
        line for line in lines
        if not line.lower().startswith(ignored_prefixes)
        and not re.match(r"^[a-z_]+:\s", line.lower())
    ]
    if not candidates:
        raise SenseVoiceTranscriptionError("SenseVoice 未返回可识别的文字")
    return candidates[-1].strip(" \t\r\n，。！？、,.!?;；:：")


def transcribe_wav(audio: bytes, timeout_seconds: int = 60) -> dict[str, Any]:
    binary = runtime_path()
    model = model_path()
    if not binary.is_file() or not model.is_file():
        missing = "运行时" if not binary.is_file() else "模型"
        raise SenseVoiceUnavailableError(f"SenseVoice{missing}尚未安装")

    temporary_path: Path | None = None
    started_at = time.perf_counter()
    try:
        with tempfile.NamedTemporaryFile(prefix="warehouse-voice-", suffix=".wav", delete=False) as handle:
            handle.write(audio)
            temporary_path = Path(handle.name)

        model_argument = os.path.relpath(model, binary.parent)
        result = subprocess.run(
            [str(binary), "-m", model_argument, "-a", str(temporary_path)],
            cwd=str(binary.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        if result.returncode != 0:
            detail = output[-800:] if output else f"退出码 {result.returncode}"
            raise SenseVoiceTranscriptionError(f"SenseVoice 识别失败：{detail}")

        return {
            "transcript": _extract_transcript(output),
            "language": "auto",
            "durationMs": round((time.perf_counter() - started_at) * 1000),
            "model": "SenseVoiceSmall Q8 GGUF",
        }
    except subprocess.TimeoutExpired as exc:
        raise SenseVoiceTranscriptionError("SenseVoice 识别超时，请缩短录音后重试") from exc
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)
