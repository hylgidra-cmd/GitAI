"""Provider interfaces for AI (Embedder, LLM, STT, TTS, Vision+OCR).
Local deterministic adapters run in dev/CI; production providers (Gemini, Whisper, ElevenLabs)
implement the same protocols without touching business logic."""
import hashlib
import math
import re
from dataclasses import dataclass
from typing import Protocol

from app.models.types import EMBEDDING_DIM

_WORD = re.compile(r"\w+", re.UNICODE)

STOPWORDS = {
    # en
    "the", "and", "was", "were", "who", "what", "when", "where", "why", "how", "which", "that",
    "this", "these", "those", "with", "from", "for", "are", "is", "its", "has", "have", "had",
    "does", "did", "can", "about", "into", "than", "then", "there", "their", "they", "you",
    "your", "tell", "please",
    # ru
    "что", "как", "это", "кто", "где", "когда", "почему", "для", "или", "его", "она", "они",
    "был", "была", "было", "были", "есть", "при", "про", "над", "под", "мне", "нам",
    # uz / kaa (latin)
    "bu", "va", "bilan", "uchun", "nima", "qachon", "qayer", "qanday", "kim", "men", "sen",
    "ham", "yoki", "edi", "bolgan", "boldi",
}


def tokenize(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if len(w) > 2 and w not in STOPWORDS]


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class HashEmbedder:
    """Deterministic bag-of-words hashing embedder (dev/test; language-agnostic)."""

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * EMBEDDING_DIM
        for tok in tokenize(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % EMBEDDING_DIM] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class LLM(Protocol):
    def answer(self, question: str, passages: list[str], lang: str) -> tuple[str, float]:
        """Return (answer_text, cost_usd)."""
        ...


class ExtractiveLLM:
    """Builds the answer only from supplied passages (cannot invent facts)."""

    def answer(self, question: str, passages: list[str], lang: str) -> tuple[str, float]:
        return " ".join(passages[:2]), 0.0


class STTProvider(Protocol):
    def transcribe(self, audio_bytes: bytes, lang: str, hint_text: str = "") -> str: ...


class LocalSTT:
    """Deterministic STT adapter for dev/tests."""

    def transcribe(self, audio_bytes: bytes, lang: str, hint_text: str = "") -> str:
        if hint_text.strip():
            return hint_text.strip()
        try:
            decoded = audio_bytes.decode("utf-8").strip()
            if decoded:
                return decoded
        except UnicodeDecodeError:
            pass
        return f"audio_query_{len(audio_bytes)}"


class TTSProvider(Protocol):
    def synthesize(self, text: str, lang: str) -> str: ...


class LocalTTS:
    """Deterministic TTS adapter returning a CDN-style Opus URL."""

    def synthesize(self, text: str, lang: str) -> str:
        digest = hashlib.sha256(f"{lang}:{text}".encode()).hexdigest()[:16]
        return f"https://cdn.audioguide.uz/tts/{lang}/{digest}.opus"


@dataclass
class VisionResult:
    ocr_text: str
    detected_label: str
    exif_stripped: bool


class VisionOCRProvider(Protocol):
    def analyze(self, image_bytes: bytes, hint_text: str = "") -> VisionResult: ...


def strip_exif_bytes(image_bytes: bytes) -> bytes:
    """Strip JPEG APP1 (EXIF/GPS) segments if present."""
    if not image_bytes.startswith(b"\xff\xd8"):
        return image_bytes
    out = bytearray(b"\xff\xd8")
    i = 2
    n = len(image_bytes)
    while i + 4 <= n and image_bytes[i] == 0xFF:
        marker = image_bytes[i + 1]
        if marker in (0xDA, 0xD9):  # SOS or EOI
            out.extend(image_bytes[i:])
            break
        seg_len = int.from_bytes(image_bytes[i + 2 : i + 4], "big")
        if marker != 0xE1:  # skip APP1 (EXIF/GPS)
            out.extend(image_bytes[i : i + 2 + seg_len])
        i += 2 + seg_len
    return bytes(out)


class LocalVisionOCR:
    """Deterministic Vision + OCR adapter (Arabic, Latin, Cyrillic text extraction)."""

    def analyze(self, image_bytes: bytes, hint_text: str = "") -> VisionResult:
        _ = strip_exif_bytes(image_bytes)
        ocr = hint_text.strip()
        if not ocr:
            try:
                ocr = image_bytes.decode("utf-8").strip()
            except UnicodeDecodeError:
                ocr = "museum artifact inscription"
        return VisionResult(ocr_text=ocr, detected_label=ocr[:120], exif_stripped=True)


embedder: Embedder = HashEmbedder()
llm: LLM = ExtractiveLLM()
stt_provider: STTProvider = LocalSTT()
tts_provider: TTSProvider = LocalTTS()
vision_provider: VisionOCRProvider = LocalVisionOCR()
