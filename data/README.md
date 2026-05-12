# Data Content Graph

This directory describes the generated learning content independently from the runtime code.

The goal is to make the curriculum inspectable before wiring it into the app.

## Layout

Split data into language-independent curriculum and language-specific realizations.

```text
data/
  curriculum/
    functions.json
    scenes.json
    review_modes.json
    card_templates.json
  languages/
    en/
      targets.json
      dialogues.json
      practice_cards.json
      visual_beats.json
      audio_assets.json
      visual_prompts.json
```

Future languages should add their own folder:

```text
data/languages/es/
data/languages/ta/
data/languages/ru/
```

Current language folders:

- `en`: English seed content used to validate the graph shape.
- `ta`: Tamil seed content for testing a language the builder does not understand; marked `needs_native_review`.

## Core Relationships

```text
Function
  -> language-specific Target
  -> language-specific Dialogue
       -> universal or localized Scene
       -> DialogueLine
            -> language-specific VisualBeat
```

Do not generate every function in every scene. The graph should be sparse and intentional:

- Each function has one anchor dialogue.
- Each function can have one or two extensions.
- Each function can have two or three transfer dialogues.
- Each dialogue line can have one visual beat.

## Universal vs Language-Specific

Universal curriculum:

- communicative function
- meaning units
- learning goal
- gesture grammar
- abstract or reusable scene context
- review mode definitions

Language-specific content:

- canonical phrase
- script and transliteration, when helpful
- accepted variants
- valid but off-target variants
- script and transliteration
- register/formality notes
- dialogue lines
- practice cards, distractors, and session ordering
- audio paths
- visual beat prompts and assets

## Asset Pipeline

The app should treat audio and visuals as generated assets attached to the content graph, not as hand-coded UI assumptions.

Audio manifests:

- `data/languages/{language}/audio_assets.json`
- Generated with `python scripts/build_audio_manifest.py`
- One entry per spoken dialogue line.
- Each speaker role gets a hard-coded, stable `voice_profile` from `scripts/voice_registry.py`.
- Silent setup beats are skipped and listed under `skipped_empty_text`.
- `audio_path` points to an existing file when possible, otherwise to `audio/generated/{language}/{dialogue_id}/line-{index}.mp3`.

Visual prompt manifests:

- `data/languages/{language}/visual_prompts.json`
- Generated with `python scripts/build_visual_prompt_manifest.py`
- One entry per dialogue line, including silent visual setup beats.
- Each entry keeps both a `shared_prompt` and a `localized_prompt`.
- `image_path` points to `visuals/generated/{language}/{dialogue_id}/frame-{index}.png`.

Useful commands:

```powershell
python scripts/build_audio_manifest.py
python scripts/build_visual_prompt_manifest.py
python scripts/export_visual_prompt_files.py --language ta
python scripts/validate_asset_manifests.py
```

To generate MP3 files from the manifest when `edge-tts` is installed and network access is available:

```powershell
python scripts/generate_tts_from_manifest.py --language ta --limit 3
```

The visual prompt exporter writes prompt text files under `visuals/generated/{language}/{dialogue_id}/prompts/` so image and video tools can be driven from the same source data.

## Practice Card Principle

The default new-card template is `guided-speaking-scene-v1` in `data/curriculum/card_templates.json`.

It uses the working first-card loop:

1. Audio prompt: "They say" while showing frame 0.
2. Scene partner line plays while showing frame 0.
3. Audio prompt: "You say" while switching to frame 1.
4. Learner model line plays while showing frame 1.
5. Audio prompt: "Now you try" while staying on frame 1.
6. Mic records and verifies against target script plus transliteration.
7. Failure shows heard pronunciation, expected pronunciation, and Try Again.

Frame 2 / final partner response is optional and should be reserved for full-dialogue review or post-success confirmation. It is not part of the default speaking practice loop.

The MVP should not only ask the learner to repeat one phrase across many scenes.

Practice cards should test:

- whether the learner can infer the learner-character's intention from the scene
- whether the learner can choose between plausible but different functions
- whether the learner can produce the phrase after the model audio is removed
- whether the learner can transfer a known function to a new scene
- whether the learner can survive a constrained AI roleplay using repair phrases

Use scene visuals to teach meaning, but use retrieval and contrast to prevent shallow memorization.

Do not make English the master and translate it. The function is the master; each language realizes that function naturally.

## MVP Scenario Priorities

The MVP focuses on the first situations a new language learner needs to survive and feel socially safe:

- greeting and asking wellbeing
- introducing yourself
- asking for repetition or slower speech
- saying you do not understand
- asking for help
- asking where something is
- ordering or requesting a basic item
- asking the price
- paying
- thanking and closing politely

The source app still has `audio_sources/dialogues.json`; this directory is the emerging richer graph for the MVP curriculum.
