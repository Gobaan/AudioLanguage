# Audio Sources

This directory is the text source of truth for generated audio.

- `dialogues.json`: scene cards and dialogue lines. Each line generates `audio/<sceneId>-<lineIndex>.mp3`.
- `prompts.json`: reusable app prompt text. Each key generates `audio/prompts/<key>.mp3`.

The generated MP3 files can be recreated from these JSON files, so edit the JSON first and regenerate audio from it.

## Regenerate Dialogue Audio

```powershell
python scripts\generate_audio_mp3.py
```

Use `--force` to overwrite existing dialogue MP3 files:

```powershell
python scripts\generate_audio_mp3.py --force
```

Optional voices:

```powershell
python scripts\generate_audio_mp3.py --feminine-voice en-US-JennyNeural --masculine-voice en-US-GuyNeural
```

## Regenerate Prompt Audio

```powershell
python scripts\generate_prompt_audio_mp3.py
```

Use `--force` to overwrite existing prompt MP3 files:

```powershell
python scripts\generate_prompt_audio_mp3.py --force
```

Optional prompt voice:

```powershell
python scripts\generate_prompt_audio_mp3.py --voice en-US-JennyNeural
```

## Verify Audio Coverage

```powershell
python scripts\verify_audio.py
```

The generation scripts use Edge TTS through the `edge-tts` Python package. If it is missing, install it in your environment before regenerating audio.
