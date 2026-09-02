from __future__ import annotations

from backend.api_service import qwen_agent, qwen_tts, voice


def test_qwen_legacy_environment_names_are_supported(monkeypatch) -> None:
    monkeypatch.delenv("WAREHOUSE_QWEN_API_KEY", raising=False)
    monkeypatch.delenv("WAREHOUSE_QWEN_MODEL", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("QWEN_API_KEY", "legacy-key")
    monkeypatch.setenv("QWEN_MODEL", "qwen-plus")

    assert qwen_agent.api_key() == "legacy-key"
    assert qwen_agent.model_name() == "qwen-plus"


def test_tts_audio_content_type_detection() -> None:
    assert qwen_tts._content_type(b"RIFF\x00\x00\x00\x00WAVE") == "audio/wav"
    assert qwen_tts._content_type(b"ID3audio") == "audio/mpeg"
    assert qwen_tts._content_type(b"OggSaudio") == "audio/ogg"
    assert qwen_tts._content_type(b"\x00\x00\x00\x18ftypM4A ") == "audio/mp4"
    assert qwen_tts._content_type(b"unknown") == "application/octet-stream"


def test_voice_router_contract() -> None:
    paths = {route.path for route in voice.router.routes}

    assert paths == {
        "/api/voice/test",
        "/api/voice/status",
        "/api/voice/transcribe",
        "/api/voice/chat",
        "/api/voice/synthesize",
    }


def test_invalid_explicit_ffmpeg_path_is_not_reported_ready(monkeypatch, tmp_path) -> None:
    missing = tmp_path / "missing-ffmpeg.exe"
    monkeypatch.setenv("WAREHOUSE_FFMPEG_PATH", str(missing))

    assert voice._ffmpeg_path() is None
    assert voice._ffmpeg_status()["ready"] is False
