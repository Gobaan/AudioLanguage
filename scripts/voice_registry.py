"""Hard-coded voice profiles for dialogue role consistency."""

from __future__ import annotations

from typing import Any


DEFAULT_PROVIDER = "edge_tts"


VOICE_PROFILES: dict[str, dict[str, dict[str, str]]] = {
    "en": {
        "learner": {
            "provider_voice": "en-US-JennyNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
        "friend": {
            "provider_voice": "en-US-AriaNeural",
            "rate": "+2%",
            "pitch": "+0Hz",
        },
        "neighbor": {
            "provider_voice": "en-US-MichelleNeural",
            "rate": "-2%",
            "pitch": "-2Hz",
        },
        "classmate": {
            "provider_voice": "en-US-AnaNeural",
            "rate": "+4%",
            "pitch": "+2Hz",
        },
        "staff": {
            "provider_voice": "en-US-BrianNeural",
            "rate": "+0%",
            "pitch": "-2Hz",
        },
        "local": {
            "provider_voice": "en-US-ChristopherNeural",
            "rate": "-1%",
            "pitch": "+0Hz",
        },
        "shopkeeper": {
            "provider_voice": "en-US-GuyNeural",
            "rate": "+1%",
            "pitch": "-3Hz",
        },
        "vendor": {
            "provider_voice": "en-US-RogerNeural",
            "rate": "+3%",
            "pitch": "-4Hz",
        },
        "server": {
            "provider_voice": "en-US-JasonNeural",
            "rate": "+5%",
            "pitch": "+0Hz",
        },
        "pharmacist": {
            "provider_voice": "en-US-SaraNeural",
            "rate": "-3%",
            "pitch": "+0Hz",
        },
        "receptionist": {
            "provider_voice": "en-US-NancyNeural",
            "rate": "+0%",
            "pitch": "+1Hz",
        },
        "conversation_partner": {
            "provider_voice": "en-US-DavisNeural",
            "rate": "-1%",
            "pitch": "-1Hz",
        },
        "default": {
            "provider_voice": "en-US-GuyNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
    },
    "ta": {
        "learner": {
            "provider_voice": "ta-IN-PallaviNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
        "friend": {
            "provider_voice": "ta-IN-PallaviNeural",
            "rate": "+3%",
            "pitch": "+2Hz",
        },
        "neighbor": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "-3%",
            "pitch": "-3Hz",
        },
        "classmate": {
            "provider_voice": "ta-IN-PallaviNeural",
            "rate": "+5%",
            "pitch": "+4Hz",
        },
        "staff": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "+0%",
            "pitch": "-1Hz",
        },
        "local": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "-1%",
            "pitch": "+1Hz",
        },
        "shopkeeper": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "+2%",
            "pitch": "-4Hz",
        },
        "vendor": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "+4%",
            "pitch": "-6Hz",
        },
        "server": {
            "provider_voice": "ta-IN-PallaviNeural",
            "rate": "+4%",
            "pitch": "+1Hz",
        },
        "pharmacist": {
            "provider_voice": "ta-IN-PallaviNeural",
            "rate": "-4%",
            "pitch": "-2Hz",
        },
        "receptionist": {
            "provider_voice": "ta-IN-PallaviNeural",
            "rate": "-1%",
            "pitch": "+3Hz",
        },
        "conversation_partner": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "-2%",
            "pitch": "+0Hz",
        },
        "default": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
    },
}


def voice_profile_for(language: str, speaker_role: str) -> dict[str, Any]:
    language_profiles = VOICE_PROFILES.get(language, VOICE_PROFILES["en"])
    profile = dict(language_profiles.get(speaker_role) or language_profiles["default"])
    profile_id = f"{language}-{speaker_role or 'default'}"
    profile.update(
        {
            "id": profile_id,
            "provider": DEFAULT_PROVIDER,
            "speaker_role": speaker_role,
        }
    )
    return profile
