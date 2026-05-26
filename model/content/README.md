# Data Content Graph

This directory describes the generated learning content independently from the runtime code.

The goal is to make the curriculum inspectable before wiring it into the app.

## Layout

Split data into language-independent curriculum and language-specific realizations.

```text
model/content/
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
    ja/
      targets.json
      dialogues.json
      practice_cards.json
      visual_beats.json
      audio_assets.json
```

Future languages should add their own folder:

```text
model/content/languages/es/
model/content/languages/ta/
model/content/languages/ru/
```

Current language folders:

- `en`: English seed content used to validate the graph shape.
- `ja`: Japanese MVP content for testing the language-picker flow and AI-guided card loop; marked `needs_native_review`.
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

- `model/content/languages/{language}/audio_assets.json`
- Generated with `python scripts/build_audio_manifest.py`
- One entry per spoken dialogue line.
- Each speaker role gets a hard-coded, stable `voice_profile` from `scripts/voice_registry.py`.
- Silent setup beats are skipped and listed under `skipped_empty_text`.
- `audio_path` points to an existing file when possible, otherwise to `audio/generated/{language}/{dialogue_id}/line-{index}.mp3`.

Visual prompt manifests:

- `model/content/languages/{language}/visual_prompts.json`
- Generated with `python scripts/build_visual_prompt_manifest.py`
- One entry per dialogue line, including silent visual setup beats.
- Each entry keeps both a `shared_prompt` and a `localized_prompt`.
- `image_path` points to `visuals/generated/{language}/{dialogue_id}/frame-{index}.png`.
- Image generation defaults to draft output under `model/assets/visuals/Drafts/{dialogue_id}/frame-{index}.png`.
- Draft output is only for prototype images: `gpt-image-1-mini` with `--quality low`.
- Medium-quality, high-quality, or full `gpt-image-1` good copies must use `--output-mode production`; the generator refuses to write those assets into `model/assets/visuals/Drafts`.
- Before generating frame 1 or frame 2 as a good copy, make sure the previous frame reference is also an accepted production/good-copy asset. Do not accidentally anchor medium frame 1 art to a low-quality draft frame 0.

Useful commands:

```powershell
python scripts/build_audio_manifest.py
python scripts/build_visual_prompt_manifest.py
python scripts/export_visual_prompt_files.py --language ta
python scripts/generate_images_from_manifest.py --language ja --prompt-id ja-first-hi-response-frame-0
python scripts/generate_images_from_manifest.py --language ja --prompt-id ja-first-hi-response-frame-0 --output-mode production --model gpt-image-1 --quality medium
python scripts/validate_asset_manifests.py
```

To generate MP3 files from the manifest when `edge-tts` is installed and network access is available:

```powershell
python scripts/generate_tts_from_manifest.py --language ta --limit 3
python scripts/generate_tts_from_manifest.py --language ja
```

The visual prompt exporter writes prompt text files under `model/assets/visuals/generated/{language}/{dialogue_id}/prompts/` so image and video tools can be driven from the same source data. Draft image generation does not update `visual_prompts.json`; production generation records generated status and reference images.

## Practice Card Principle

Learning-engine decisions are documented in `skills/learning-engine-flow/SKILL.md`.

The default new-card template is `guided-dialogue-replay-v1` in `model/content/curriculum/card_templates.json`.

It uses the working first-card loop:

1. Autoplay the full visual dialogue once, rotating frames as each spoken line plays.
2. Hide inactive controls during the first autoplay.
3. Show a green glow while scene audio is playing.
4. After the first watch, show `Try`.
5. On `Try`, replay only the partner cue line.
6. Play the "Now you try" prompt while switching to the learner frame.
7. Start the microphone after the cue finishes; the on-screen listening state tells the learner it is their turn.
8. Show a blue glow only while the microphone is actually listening.
9. Hold the learner frame during recording and AI checking.
10. Show concise AI feedback; play the partner response after a successful attempt when available.

Frame 2 / final partner response is optional but useful as post-success confirmation. It should not interrupt a retry after failure.

For beginner cards, keep the first session to short chunks first. Longer survival phrases should unlock by extension. Romanized pronunciation should remain hidden until after a failed attempt, then appear with full-speed and slow target audio as recovery support.

The template supplies the shared support flags server-side, so individual cards should only override differences:

```json
{
  "template_id": "guided-dialogue-replay-v1",
  "mode": "ai_guided_response",
  "support": {}
}
```

Every card using this template must include an `ai_scene_contract` with a plain-English target-function definition, required semantic slots, optional slots, likely wrong intents, and short feedback rules.

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

The source app still has `model/assets/audio_sources/dialogues.json`; this directory is the richer graph for the MVP curriculum.
