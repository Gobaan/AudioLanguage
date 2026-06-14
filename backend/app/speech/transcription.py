from pathlib import Path
import os

from app.speech.audio_io import convert_to_wav
from app.speech.display import learner_facing_transcript
from app.speech.similarity import normalize_for_match, text_similarity


WHISPER_MODEL = None
WHISPER_MODEL_AVAILABLE: bool | None = None


def transcribe_speech(
    audio_path: Path,
    *,
    language: str,
    expected_romanized: str,
) -> dict:
    model = get_whisper_model()
    if model is None:
        return unavailable_transcription("Install faster-whisper and a local model to enable speech interpretation.")

    wav_path: Path | None = None
    try:
        wav_path = convert_to_wav(audio_path)
        segments, info = model.transcribe(
            str(wav_path),
            language=language or None,
            task="transcribe",
            beam_size=1,
            vad_filter=False,
        )
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        romanized = learner_facing_transcript(
            transcript,
            language=language or "",
            target_romanized=expected_romanized,
        )
        score = text_similarity(
            normalize_for_match(romanized),
            normalize_for_match(expected_romanized),
        )

        return {
            "available": True,
            "transcript": transcript,
            "romanized": romanized,
            "score": round(score, 3),
            "language": getattr(info, "language", language),
            "language_probability": getattr(info, "language_probability", None),
            "feedback": "",
        }
    except Exception as error:  # pragma: no cover - depends on optional model/runtime
        return unavailable_transcription(f"Speech recognizer failed: {error}")
    finally:
        if wav_path:
            wav_path.unlink(missing_ok=True)


def get_whisper_model():
    global WHISPER_MODEL, WHISPER_MODEL_AVAILABLE

    if WHISPER_MODEL_AVAILABLE is False:
        return None
    if WHISPER_MODEL is not None:
        return WHISPER_MODEL

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        WHISPER_MODEL_AVAILABLE = False
        return None

    model_name = os.environ.get("AUDIO_LANGUAGE_WHISPER_MODEL", "tiny")
    device = os.environ.get("AUDIO_LANGUAGE_WHISPER_DEVICE", "cpu")
    compute_type = os.environ.get("AUDIO_LANGUAGE_WHISPER_COMPUTE_TYPE", "int8")
    try:
        WHISPER_MODEL = WhisperModel(model_name, device=device, compute_type=compute_type)
    except Exception:
        WHISPER_MODEL_AVAILABLE = False
        return None

    WHISPER_MODEL_AVAILABLE = True
    return WHISPER_MODEL


def unavailable_transcription(message: str) -> dict:
    return {
        "available": False,
        "transcript": "",
        "romanized": "",
        "score": 0.0,
        "language": None,
        "language_probability": None,
        "feedback": message,
    }
