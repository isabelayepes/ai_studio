"""
MCP Speech Server — Kokoro-only (TTS) + Faster-Whisper (STT)

Env knobs (optional):
  KOKORO_LANG_CODE=a    # 'a' American English
  KOKORO_VOICE=af_heart # default voice
  TTS_DOWNLOAD_DIR=out  # where files are saved when save_path is used
  TTS_FILE_BASE_URL=    # e.g. http://localhost:8787 to expose downloads

Run:
  python mcp_speech_server.py
"""

from __future__ import annotations
import base64, io, os, sys, tempfile, contextlib
from dataclasses import dataclass
from typing import Optional, Tuple, List

import numpy as np
import soundfile as sf

# Optional .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ---------- Config ----------
KOKORO_LANG_CODE = os.getenv("KOKORO_LANG_CODE", "a")   # 'a' => American English
KOKORO_DEFAULT_VOICE = os.getenv("KOKORO_VOICE", "af_heart")
TTS_DOWNLOAD_DIR = os.getenv("TTS_DOWNLOAD_DIR", "out")
TTS_FILE_BASE_URL = os.getenv("TTS_FILE_BASE_URL")  # optional base URL for saved files

# lazy caches
_kokoro = None
_faster = None

# ---------- Quiet Kokoro's stdout to avoid corrupting JSON-RPC ----------
@contextlib.contextmanager
def _quiet_stdout_to_stderr():
    """
    Redirect sys.stdout to sys.stderr within the block so any progress logs
    (pip/spacy/hf) don't appear on MCP stdout.
    """
    old = sys.stdout
    try:
        sys.stdout = sys.stderr
        yield
    finally:
        sys.stdout = old

# ---------- MCP ----------
from mcp.server.fastmcp import FastMCP
app = FastMCP("speech-kokoro")

@dataclass
class TranscribeInput:
    audio_b64: Optional[str] = None
    audio_path: Optional[str] = None
    language: Optional[str] = None

@dataclass
class TranscribeOutput:
    text: str
    language: Optional[str] = None
    duration_sec: Optional[float] = None

@dataclass
class SynthesizeInput:
    text: str
    voice: Optional[str] = None
    rate: Optional[float] = None
    save_path: Optional[str] = None

@dataclass
class SynthesizeOutput:
    audio_b64_wav: str
    sample_rate: int
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None

# ---------- helpers ----------
def _safe_out_path(rel_path: str) -> str:
    base = os.path.abspath(TTS_DOWNLOAD_DIR)
    os.makedirs(base, exist_ok=True)
    rel_path = rel_path.lstrip("/\\")
    target = os.path.abspath(os.path.join(base, rel_path))
    if not (target == base or target.startswith(base + os.sep)):
        raise ValueError("save_path escapes TTS_DOWNLOAD_DIR")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    return target

def _wav_bytes_from_float32(audio: np.ndarray, sr: int) -> bytes:
    audio = np.clip(audio, -1.0, 1.0)
    bio = io.BytesIO()
    sf.write(bio, audio, sr, subtype="PCM_16", format="WAV")
    return bio.getvalue()

def _load_audio_from_input(inp: TranscribeInput) -> Tuple[np.ndarray, int]:
    if not inp.audio_b64 and not inp.audio_path:
        raise ValueError("Provide audio_b64 or audio_path")
    if inp.audio_b64:
        data = base64.b64decode(inp.audio_b64)
        bio = io.BytesIO(data)
        audio, sr = sf.read(bio, dtype="float32")
    else:
        audio, sr = sf.read(inp.audio_path, dtype="float32")
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    return audio, sr

# ---------- STT (faster-whisper) ----------
def _stt_with_faster_whisper(audio: np.ndarray, sr: int, language: Optional[str]) -> TranscribeOutput:
    global _faster
    if _faster is None:
        from faster_whisper import WhisperModel
        _faster = WhisperModel(os.getenv("FASTER_WHISPER_MODEL", "small"))
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        sf.write(tmp.name, audio, sr)
        segments, info = _faster.transcribe(tmp.name, language=language)
        text = " ".join(seg.text.strip() for seg in segments if seg.text)
        return TranscribeOutput(text=text.strip(), language=info.language, duration_sec=info.duration)

# ---------- TTS (kokoro) ----------
def _tts_with_kokoro(text: str, voice: Optional[str], rate: Optional[float]) -> SynthesizeOutput:
    """
    Uses kokoro.KPipeline(lang_code='a') and generates 24kHz audio.
    Quiet stdout during import/init/call to keep MCP stdout clean.
    """
    global _kokoro
    with _quiet_stdout_to_stderr():
        from kokoro import KPipeline  # import quietly
        if _kokoro is None:
            _kokoro = KPipeline(lang_code=KOKORO_LANG_CODE)  # 'a' American English

        v = voice or KOKORO_DEFAULT_VOICE
        speed = rate if (rate and rate > 0) else 1.0

        chunks: List[np.ndarray] = []
        for _, _, audio in _kokoro(text, voice=v, speed=speed, split_pattern=r"\n+"):
            chunks.append(np.asarray(audio, dtype=np.float32))

    if not chunks:
        raise RuntimeError("Kokoro returned no audio")

    audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sr = 24000  # kokoro default sample rate
    b = _wav_bytes_from_float32(audio, sr)
    return SynthesizeOutput(audio_b64_wav=base64.b64encode(b).decode("ascii"), sample_rate=sr)

# ---------- Tools ----------
@app.tool()
def transcribe_audio(payload: dict) -> dict:
    """Transcribe audio to text. payload: {audio_b64?, audio_path?, language?}"""
    inp = TranscribeInput(**payload)
    audio, sr = _load_audio_from_input(inp)
    out = _stt_with_faster_whisper(audio, sr, inp.language)
    return out.__dict__

@app.tool()
def synthesize_speech(payload: dict) -> dict:
    """Synthesize speech. payload: {text, voice?, rate?, save_path?}"""
    inp = SynthesizeInput(**payload)
    out = _tts_with_kokoro(inp.text, inp.voice, inp.rate)
    out_dict = out.__dict__.copy()

    if inp.save_path:
        target = _safe_out_path(inp.save_path)
        with open(target, "wb") as f:
            f.write(base64.b64decode(out.audio_b64_wav))
        out_dict["audio_path"] = target
        if TTS_FILE_BASE_URL:
            rel = os.path.relpath(target, start=os.path.abspath(TTS_DOWNLOAD_DIR)).replace(os.sep, "/")
            out_dict["audio_url"] = TTS_FILE_BASE_URL.rstrip("/") + "/" + rel

    return out_dict

@app.tool()
def list_voices(payload: dict) -> dict:
    """Return a small set of known Kokoro voices."""
    return {"backend": "kokoro", "voices": ["af_heart"], "lang_code": KOKORO_LANG_CODE}

if __name__ == "__main__":
    app.run()
