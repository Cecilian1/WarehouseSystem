"""Qwen3-TTS non-realtime speech synthesis through DashScope."""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from backend.api_service.qwen_agent import api_key


DEFAULT_TTS_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MAX_AUDIO_BYTES = 12 * 1024 * 1024


class QwenTTSUnavailableError(RuntimeError):
    pass


class QwenTTSRequestError(RuntimeError):
    pass


def status() -> dict[str, Any]:
    return {
        "configured": bool(api_key()),
        "model": os.environ.get("WAREHOUSE_TTS_MODEL", "qwen3-tts-flash"),
        "voice": os.environ.get("WAREHOUSE_TTS_VOICE", "Cherry"),
        "provider": "DashScope",
    }


def _download_audio(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not (
        hostname == "aliyuncs.com" or hostname.endswith(".aliyuncs.com")
    ):
        raise QwenTTSRequestError("TTS返回了不受信任的音频地址")
    with urllib.request.urlopen(url, timeout=45) as response:
        audio = response.read(MAX_AUDIO_BYTES + 1)
    if len(audio) > MAX_AUDIO_BYTES:
        raise QwenTTSRequestError("TTS返回的音频文件过大")
    return audio


def _content_type(audio: bytes) -> str:
    if audio.startswith(b"RIFF") and audio[8:12] == b"WAVE":
        return "audio/wav"
    if audio.startswith((b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        return "audio/mpeg"
    if audio.startswith(b"OggS"):
        return "audio/ogg"
    if len(audio) >= 12 and audio[4:8] == b"ftyp":
        return "audio/mp4"
    return "application/octet-stream"


def synthesize(text: str) -> tuple[bytes, str]:
    key = api_key()
    if not key:
        raise QwenTTSUnavailableError("尚未配置Qwen API Key")
    normalized = re.sub(r"[*_`#]", "", text).strip()
    normalized = re.sub(r"(?m)^\s*[-•]+\s*", "", normalized)
    normalized = re.sub(r"\s*\n+\s*", "；", normalized)
    if not normalized:
        raise QwenTTSRequestError("待合成文本不能为空")

    payload = json.dumps(
        {
            "model": os.environ.get("WAREHOUSE_TTS_MODEL", "qwen3-tts-flash"),
            "input": {
                "text": normalized[:800],
                "voice": os.environ.get("WAREHOUSE_TTS_VOICE", "Cherry"),
                "language_type": "Chinese",
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        os.environ.get("WAREHOUSE_TTS_BASE_URL", DEFAULT_TTS_URL),
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-1000:]
        raise QwenTTSRequestError(f"TTS接口返回HTTP {exc.code}：{detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise QwenTTSRequestError(f"无法连接TTS接口：{exc}") from exc

    audio_info = ((result.get("output") or {}).get("audio") or {})
    encoded = audio_info.get("data") or ""
    if encoded:
        try:
            audio = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise QwenTTSRequestError("TTS返回的音频编码无效") from exc
    else:
        audio_url = str(audio_info.get("url") or "")
        if not audio_url:
            raise QwenTTSRequestError("TTS没有返回音频")
        audio = _download_audio(audio_url)
    if not audio:
        raise QwenTTSRequestError("TTS返回了空音频")
    return audio, _content_type(audio)
