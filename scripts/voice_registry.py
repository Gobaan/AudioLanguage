"""Hard-coded voice profiles for dialogue character consistency."""

from __future__ import annotations

from typing import Any


DEFAULT_PROVIDER = "edge_tts"


CHARACTER_VOICE_PROFILES: dict[str, dict[str, dict[str, str]]] = {
    "en": {
        "learner": {"provider_voice": "en-US-JennyNeural", "rate": "+0%", "pitch": "+0Hz"},
        "friend": {"provider_voice": "en-US-EricNeural", "rate": "+2%", "pitch": "+0Hz"},
        "staff": {"provider_voice": "en-US-BrianNeural", "rate": "+0%", "pitch": "-2Hz"},
        "local_helper": {"provider_voice": "en-US-ChristopherNeural", "rate": "-1%", "pitch": "+0Hz"},
        "vendor": {"provider_voice": "en-US-AriaNeural", "rate": "+4%", "pitch": "+0Hz"},
        "pharmacist": {"provider_voice": "en-US-RogerNeural", "rate": "-3%", "pitch": "-2Hz"},
        "default": {"provider_voice": "en-US-GuyNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
    "ta": {
        "learner": {"provider_voice": "ta-IN-PallaviNeural", "rate": "+0%", "pitch": "+0Hz"},
        "friend": {"provider_voice": "ta-IN-ValluvarNeural", "rate": "+3%", "pitch": "+0Hz"},
        "staff": {"provider_voice": "ta-IN-ValluvarNeural", "rate": "+0%", "pitch": "-1Hz"},
        "local_helper": {"provider_voice": "ta-IN-ValluvarNeural", "rate": "-1%", "pitch": "+1Hz"},
        "vendor": {"provider_voice": "ta-IN-PallaviNeural", "rate": "+4%", "pitch": "+1Hz"},
        "pharmacist": {"provider_voice": "ta-IN-ValluvarNeural", "rate": "-4%", "pitch": "-2Hz"},
        "default": {"provider_voice": "ta-IN-ValluvarNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
    "ja": {
        "learner": {"provider_voice": "ja-JP-NanamiNeural", "rate": "+0%", "pitch": "+0Hz"},
        "friend": {"provider_voice": "ja-JP-KeitaNeural", "rate": "+2%", "pitch": "+0Hz"},
        "staff": {"provider_voice": "ja-JP-KeitaNeural", "rate": "+0%", "pitch": "-2Hz"},
        "local_helper": {"provider_voice": "ja-JP-KeitaNeural", "rate": "-1%", "pitch": "+0Hz"},
        "vendor": {"provider_voice": "ja-JP-NanamiNeural", "rate": "+3%", "pitch": "+0Hz"},
        "pharmacist": {"provider_voice": "ja-JP-KeitaNeural", "rate": "-3%", "pitch": "-1Hz"},
        "default": {"provider_voice": "ja-JP-NanamiNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
    "yue": {
        "learner": {"provider_voice": "zh-HK-HiuGaaiNeural", "rate": "+0%", "pitch": "+0Hz"},
        "friend": {"provider_voice": "zh-HK-WanLungNeural", "rate": "+2%", "pitch": "+0Hz"},
        "staff": {"provider_voice": "zh-HK-WanLungNeural", "rate": "+0%", "pitch": "-2Hz"},
        "local_helper": {"provider_voice": "zh-HK-WanLungNeural", "rate": "-1%", "pitch": "+1Hz"},
        "vendor": {"provider_voice": "zh-HK-WanLungNeural", "rate": "+3%", "pitch": "-1Hz"},
        "pharmacist": {"provider_voice": "zh-HK-WanLungNeural", "rate": "-3%", "pitch": "-2Hz"},
        "default": {"provider_voice": "zh-HK-WanLungNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
    "zh": {
        "learner": {"provider_voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%", "pitch": "+0Hz"},
        "friend": {"provider_voice": "zh-CN-YunxiNeural", "rate": "+2%", "pitch": "+0Hz"},
        "staff": {"provider_voice": "zh-CN-YunyangNeural", "rate": "+0%", "pitch": "-2Hz"},
        "local_helper": {"provider_voice": "zh-CN-YunyangNeural", "rate": "-1%", "pitch": "+0Hz"},
        "vendor": {"provider_voice": "zh-CN-YunxiNeural", "rate": "+3%", "pitch": "-1Hz"},
        "pharmacist": {"provider_voice": "zh-CN-YunyangNeural", "rate": "-3%", "pitch": "-2Hz"},
        "default": {"provider_voice": "zh-CN-YunyangNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
    "ar": {
        "learner": {"provider_voice": "ar-SA-ZariyahNeural", "rate": "+0%", "pitch": "+0Hz"},
        "friend": {"provider_voice": "ar-SA-HamedNeural", "rate": "+2%", "pitch": "+0Hz"},
        "staff": {"provider_voice": "ar-SA-HamedNeural", "rate": "+0%", "pitch": "-2Hz"},
        "local_helper": {"provider_voice": "ar-SA-HamedNeural", "rate": "-1%", "pitch": "+0Hz"},
        "vendor": {"provider_voice": "ar-SA-ZariyahNeural", "rate": "+3%", "pitch": "+0Hz"},
        "pharmacist": {"provider_voice": "ar-SA-HamedNeural", "rate": "-3%", "pitch": "-1Hz"},
        "default": {"provider_voice": "ar-SA-HamedNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
}


VOICE_PROFILES: dict[str, dict[str, dict[str, str]]] = {
    "en": {
        "learner": {
            "provider_voice": "en-US-JennyNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
        "friend": {
            "provider_voice": "en-US-DavisNeural",
            "rate": "+2%",
            "pitch": "+0Hz",
        },
        "neighbor": {
            "provider_voice": "en-US-MichelleNeural",
            "rate": "-2%",
            "pitch": "-2Hz",
        },
        "classmate": {
            "provider_voice": "en-US-DavisNeural",
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
            "provider_voice": "en-US-AriaNeural",
            "rate": "+3%",
            "pitch": "+0Hz",
        },
        "server": {
            "provider_voice": "en-US-AriaNeural",
            "rate": "+5%",
            "pitch": "+0Hz",
        },
        "pharmacist": {
            "provider_voice": "en-US-RogerNeural",
            "rate": "-3%",
            "pitch": "-2Hz",
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
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "+3%",
            "pitch": "+0Hz",
        },
        "neighbor": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "-3%",
            "pitch": "-3Hz",
        },
        "classmate": {
            "provider_voice": "ta-IN-ValluvarNeural",
            "rate": "+5%",
            "pitch": "+1Hz",
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
            "provider_voice": "ta-IN-PallaviNeural",
            "rate": "+4%",
            "pitch": "+0Hz",
        },
        "server": {
            "provider_voice": "ta-IN-PallaviNeural",
            "rate": "+4%",
            "pitch": "+1Hz",
        },
        "pharmacist": {
            "provider_voice": "ta-IN-ValluvarNeural",
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
    "ja": {
        "learner": {
            "provider_voice": "ja-JP-NanamiNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
        "friend": {
            "provider_voice": "ja-JP-KeitaNeural",
            "rate": "+2%",
            "pitch": "+0Hz",
        },
        "classmate": {
            "provider_voice": "ja-JP-KeitaNeural",
            "rate": "+4%",
            "pitch": "+1Hz",
        },
        "staff": {
            "provider_voice": "ja-JP-KeitaNeural",
            "rate": "+0%",
            "pitch": "-2Hz",
        },
        "local": {
            "provider_voice": "ja-JP-KeitaNeural",
            "rate": "-1%",
            "pitch": "+0Hz",
        },
        "server": {
            "provider_voice": "ja-JP-NanamiNeural",
            "rate": "+3%",
            "pitch": "+0Hz",
        },
        "vendor": {
            "provider_voice": "ja-JP-NanamiNeural",
            "rate": "+3%",
            "pitch": "+0Hz",
        },
        "pharmacist": {
            "provider_voice": "ja-JP-KeitaNeural",
            "rate": "-3%",
            "pitch": "-1Hz",
        },
        "default": {
            "provider_voice": "ja-JP-NanamiNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
    },
    "yue": {
        "learner": {
            "provider_voice": "zh-HK-HiuGaaiNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
        "friend": {
            "provider_voice": "zh-HK-WanLungNeural",
            "rate": "+2%",
            "pitch": "+0Hz",
        },
        "classmate": {
            "provider_voice": "zh-HK-WanLungNeural",
            "rate": "+4%",
            "pitch": "+1Hz",
        },
        "staff": {
            "provider_voice": "zh-HK-WanLungNeural",
            "rate": "+0%",
            "pitch": "-2Hz",
        },
        "server": {
            "provider_voice": "zh-HK-WanLungNeural",
            "rate": "+3%",
            "pitch": "-1Hz",
        },
        "default": {
            "provider_voice": "zh-HK-WanLungNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
    },
    "zh": {
        "learner": {
            "provider_voice": "zh-CN-XiaoxiaoNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
        "friend": {
            "provider_voice": "zh-CN-YunxiNeural",
            "rate": "+2%",
            "pitch": "+0Hz",
        },
        "classmate": {
            "provider_voice": "zh-CN-YunxiNeural",
            "rate": "+4%",
            "pitch": "+1Hz",
        },
        "staff": {
            "provider_voice": "zh-CN-YunyangNeural",
            "rate": "+0%",
            "pitch": "-2Hz",
        },
        "server": {
            "provider_voice": "zh-CN-YunxiNeural",
            "rate": "+3%",
            "pitch": "-1Hz",
        },
        "default": {
            "provider_voice": "zh-CN-YunyangNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
    },
    "ar": {
        "learner": {
            "provider_voice": "ar-SA-ZariyahNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
        "friend": {
            "provider_voice": "ar-SA-HamedNeural",
            "rate": "+2%",
            "pitch": "+0Hz",
        },
        "classmate": {
            "provider_voice": "ar-SA-HamedNeural",
            "rate": "+4%",
            "pitch": "+1Hz",
        },
        "staff": {
            "provider_voice": "ar-SA-HamedNeural",
            "rate": "+0%",
            "pitch": "-2Hz",
        },
        "local": {
            "provider_voice": "ar-SA-HamedNeural",
            "rate": "-1%",
            "pitch": "+0Hz",
        },
        "server": {
            "provider_voice": "ar-SA-ZariyahNeural",
            "rate": "+3%",
            "pitch": "+0Hz",
        },
        "vendor": {
            "provider_voice": "ar-SA-ZariyahNeural",
            "rate": "+3%",
            "pitch": "+0Hz",
        },
        "pharmacist": {
            "provider_voice": "ar-SA-HamedNeural",
            "rate": "-3%",
            "pitch": "-1Hz",
        },
        "default": {
            "provider_voice": "ar-SA-HamedNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        },
    },
}


def character_voice_profile_for(language: str, character_id: str, speaker_role: str = "") -> dict[str, Any]:
    language_profiles = CHARACTER_VOICE_PROFILES.get(language, CHARACTER_VOICE_PROFILES["en"])
    profile = dict(language_profiles.get(character_id) or language_profiles["default"])
    profile_id = f"{language}-{character_id or 'default'}"
    profile.update(
        {
            "id": profile_id,
            "provider": DEFAULT_PROVIDER,
            "character_id": character_id,
            "speaker_role": speaker_role,
        }
    )
    return profile


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
