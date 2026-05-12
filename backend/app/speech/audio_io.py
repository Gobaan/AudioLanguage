from pathlib import Path
import subprocess
import tempfile


def convert_to_wav(audio_path: Path) -> Path:
    """Convert browser-recorded audio to mono 16k WAV for local STT engines."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
        wav_path = Path(wav_file.name)

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(audio_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-y",
        str(wav_path),
    ]
    subprocess.run(command, capture_output=True, check=True)
    return wav_path
