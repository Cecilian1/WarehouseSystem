"""Voice assistant transport and local transcription endpoints."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.api_service.helpers import ok
from backend.api_service.sensevoice import (
    SenseVoiceTranscriptionError,
    SenseVoiceUnavailableError,
    status as sensevoice_status,
    transcribe_wav,
)
from backend.api_service.qwen_agent import (
    QwenRequestError,
    QwenUnavailableError,
    chat as qwen_chat,
    status as qwen_status,
)
from backend.api_service.qwen_tts import (
    QwenTTSRequestError,
    QwenTTSUnavailableError,
    status as tts_status,
    synthesize,
)

router = APIRouter(prefix="/api/voice", tags=["voice"])
MAX_AUDIO_BYTES = 10 * 1024 * 1024
SUPPORTED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/mpeg",
    "audio/mp3", "audio/aac", "application/octet-stream",
}


def _ffmpeg_path() -> str | None:
    configured = os.environ.get("WAREHOUSE_FFMPEG_PATH", "").strip()
    if configured:
        resolved = shutil.which(configured)
        if resolved:
            return resolved
        candidate = Path(configured).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        return None
    return shutil.which("ffmpeg")


def _ffmpeg_status() -> dict[str, Any]:
    configured = os.environ.get("WAREHOUSE_FFMPEG_PATH", "").strip()
    resolved = _ffmpeg_path()
    return {
        "ready": bool(resolved),
        "path": resolved or configured or "ffmpeg",
    }


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class VoiceChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    history: list[ChatHistoryItem] = Field(default_factory=list)


class VoiceSynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


async def _read_audio(request: Request, supported_types: set[str]) -> tuple[bytes, str]:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type not in supported_types:
        raise HTTPException(status_code=415, detail="不支持的音频格式")
    declared_size = request.headers.get("content-length")
    if declared_size:
        try:
            if int(declared_size) > MAX_AUDIO_BYTES:
                raise HTTPException(status_code=413, detail="音频不能超过10MB")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="音频长度格式无效") from exc
    audio = await request.body()
    if not audio:
        raise HTTPException(status_code=400, detail="没有收到音频数据")
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="音频不能超过10MB")
    return audio, content_type


@router.post("/test")
async def test_audio_upload(request: Request) -> dict[str, Any]:
    audio, content_type = await _read_audio(request, SUPPORTED_AUDIO_TYPES)
    return ok({
        "received": True,
        "bytes": len(audio),
        "contentType": content_type,
        "receivedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "message": "电脑后端已收到录音，基础语音链路正常。",
    })


@router.get("/status")
async def get_voice_status() -> dict[str, Any]:
    return ok({
        "sensevoice": sensevoice_status(),
        "ffmpeg": _ffmpeg_status(),
        "qwen": qwen_status(),
        "tts": tts_status(),
    })


@router.post("/transcribe")
async def transcribe_audio(request: Request) -> dict[str, Any]:
    audio, content_type = await _read_audio(request, SUPPORTED_AUDIO_TYPES)
    if content_type not in {"audio/wav", "audio/x-wav"}:
        ffmpeg = _ffmpeg_path()
        if not ffmpeg:
            raise HTTPException(status_code=503, detail="服务器缺少 ffmpeg，暂时无法转换小程序录音")
        source_path = None
        wav_path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="warehouse-voice-", suffix=".input", delete=False) as source:
                source.write(audio)
                source_path = source.name
            wav_path = f"{source_path}.wav"
            completed = await asyncio.to_thread(subprocess.run, [ffmpeg, "-y", "-i", source_path, "-ar", "16000", "-ac", "1", wav_path], capture_output=True, timeout=30)
            if completed.returncode != 0:
                raise HTTPException(status_code=400, detail="小程序录音格式转换失败")
            audio = await asyncio.to_thread(Path(wav_path).read_bytes)
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(status_code=504, detail="音频格式转换超时") from exc
        finally:
            for path in (source_path, wav_path):
                if path:
                    try:
                        Path(path).unlink(missing_ok=True)
                    except OSError:
                        pass
    if len(audio) < 44 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        raise HTTPException(status_code=400, detail="音频不是有效的WAV文件")
    try:
        result = await asyncio.to_thread(transcribe_wav, audio)
    except SenseVoiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SenseVoiceTranscriptionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ok(result)


@router.post("/chat")
async def chat_with_assistant(payload: VoiceChatRequest) -> dict[str, Any]:
    history = [{"role": item.role, "content": item.content} for item in payload.history]
    try:
        result = await asyncio.to_thread(qwen_chat, payload.text.strip(), history)
    except QwenUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except QwenRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ok(result)


@router.post("/synthesize")
async def synthesize_answer(payload: VoiceSynthesisRequest) -> Response:
    try:
        audio, content_type = await asyncio.to_thread(synthesize, payload.text)
    except QwenTTSUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except QwenTTSRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    extension = {
        "audio/wav": "wav",
        "audio/mpeg": "mp3",
        "audio/ogg": "ogg",
        "audio/mp4": "m4a",
    }.get(content_type, "audio")
    return Response(
        content=audio,
        media_type=content_type,
        headers={"Cache-Control": "no-store", "Content-Disposition": f"inline; filename=assistant.{extension}"},
    )
