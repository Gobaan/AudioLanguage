---
name: visual-character-system
description: Create and maintain reusable character bibles, avatar reference sheets, partner archetypes, visual identity rules, and reference-image workflows for language-learning comic scenes. Use when Codex designs base characters, generates or updates avatar references, preserves character consistency across AI-generated panels, chooses symbolic meaning bubbles versus body cues, or organizes visual assets under visuals/style.
---

# Visual Character System

## Purpose

Use this skill to keep language-learning scene visuals consistent across cards, languages, and generated assets.

Do not depend on text prompts alone for recurring characters. Store approved base references locally and use them as actual image inputs for production scene panels. A filename written inside a prompt is not a visual reference; the model cannot see local files unless the image is attached by the tool or script.

Keep character and scene prompts language-neutral unless the visual situation itself must change for cultural or environmental reasons. The learner avatar, partner archetypes, turn-taking, gesture logic, and most everyday scenes should be reusable across Japanese, Tamil, Spanish, Russian, Cantonese, and other languages.

## Asset Structure

Use this project structure:

```text
visuals/style/
  character_bible.md
  examples/
    approved-comic-panel-sumimasen-cue.png
  characters/
    learner-reference.png
    staff-reference.png
    vendor-reference.png
    friend-reference.png
    pharmacist-reference.png
  prompts/
    learner-reference.txt
    staff-reference.txt
```

Scene frames should live near the card or scenario:

```text
visuals/<language-or-shared>/<scene-id>/
  frame-0.png
  frame-1.png
  frame-2.png
  prompts/
    frame-0.txt
    frame-1.txt
    frame-2.txt
```

## Character Bible

Create `visuals/style/character_bible.md` before making many scene frames.

Include:

- global style: polished clean anime/comic style, line weight, palette, rendering level
- learner avatar: age range, outfit, hair, silhouette, recurring props
- partner archetypes: staff, vendor, friend, pharmacist, local helper
- turn-taking conventions: where learner and partner usually appear
- symbol rules: how speech bubbles and meaning bubbles work
- invariants: what must not change between panels
- review checklist: what counts as identity drift

Keep the bible concise enough to paste into generation prompts when image references are unavailable.

Use `visuals/style/examples/approved-comic-panel-sumimasen-cue.png` as the approved scene-panel style and framing example. New scene panels should match its polished clean anime/comic look, crisp controlled linework, warm flat colors, readable character scale, card-box fit, and mobile-safe composition unless the user approves a different style reference.

Reject scene panels that drift into rough sketchbook style, children's-book illustration, thick marker outlines, decorative sketch borders, photorealism, or generic prompt-only character designs.

## Reference Sheets

Generate or maintain one approved reference sheet per recurring character or archetype.

Each reference should show:

- front-facing neutral pose
- side or three-quarter pose
- two common expressions
- simple outfit and color palette
- no text, labels, logos, captions, or target-language dialogue
- transparent or plain background if practical

For the learner, prefer a human avatar with a warm, ordinary look. Avoid mascots or animals for core survival-dialogue practice because the learner should transfer the scene to real human interactions.

For partners, create archetypes rather than one-off strangers. A staff archetype can appear at counters, offices, and transport desks; a vendor archetype can appear in food and shop scenes.

## Generation Workflow

1. Create or update the character bible.
2. Generate one learner reference sheet and one needed partner reference sheet.
3. Save the approved references under `visuals/style/characters/`.
4. Prepare one panel prompt and show it to the user before generating.
5. Generate exactly one image.
6. Inspect for identity, gesture, turn-taking, box fit, and meaning clarity.
7. Wait for user approval before generating the next panel.
8. Only scale to more cards after one full three-panel card is approved.

Never bulk-generate scene panels before the user has approved the prompt style and first output image. Prompt-only identity is not enough for production panels. If the generation tool cannot use image references directly, stop and tell the user the result will only be a draft.

When generating a scene panel, use both kinds of references:

- character identity references from `visuals/style/characters/`
- style/framing reference `visuals/style/examples/approved-comic-panel-sumimasen-cue.png`
- for frame 1 or later, the previous approved frame from the same card as a continuity reference

For multi-frame cards, frame-to-frame continuity matters. Frame 1 should be generated with frame 0 attached as a continuity reference; frame 2 should be generated with frame 1 attached. This makes the generator update the scene instead of reinventing the room, camera angle, partner identity, or layout. Only use a previous frame after the user approves it.

Generated scene images should usually contain no speech bubbles. Speech bubbles are turn-taking UI, so the app should overlay them from speaker metadata. This prevents the generator from attaching a bubble to the wrong person and lets the interface animate or highlight the active speaker consistently.

For this repo, production scene panels should be generated through `scripts/generate_images_from_manifest.py` with real reference inputs:

```powershell
python scripts\generate_images_from_manifest.py --language ja --dialogue-id <dialogue-id> --limit 1 --force --reference-mode always --quality low
```

After generation, verify the manifest entry includes `reference_images`. If that field is missing or empty, the image was not generated with real references and should not be accepted.

Use `gpt-image-1-mini` with low quality for prototype composition checks. Upgrade to `gpt-image-1` with medium quality after the composition, scene blocking, and character placement are working. Use high only for final polish, not while testing prompts.

When generating a frame, include:

- the exact reference filenames used
- the role of each character in the scene
- the panel number and timing role
- the learner intention as a language-neutral communicative function, not target-language words
- the body cue or meaning bubble that carries meaning
- mobile-safe composition: central characters, large faces/hands, readable bubbles, and no key meaning in the lower overlay area
- landscape `3:2` / `1536x1024` framing for two-person dialogue scenes, square `1:1` for compact one-person/object scenes
- constraints: no readable dialogue, no translations, no subtitles, no logos

Use landscape `3:2` / `1536x1024` as the default for two-person dialogue scenes. It gives the generator enough horizontal room for natural side-view staging, believable distance, counters, doorways, and sightlines. Use square `1:1` for compact one-person, object, symptom, or review scenes. Keep the important action in a central safe area so the app can contain, crop, or letterbox on mobile.

Use natural candid comic-scene composition. Characters should feel located in the environment with believable distance, furniture, counters, doorways, and sightlines. Avoid oversized foreground portraits, sticker poses, staged two-character poses, reaction shots, and character reference-sheet framing. For learner-turn panels, the learner should direct gaze and gesture toward the partner, not toward the viewer, unless the scene specifically requires direct address.

Use the same generic visual frame roles across languages: cue, learner turn, and resolution. Change audio, target text, romanization, and AI judging by language; change visuals only when the scene meaning or cultural action truly changes.

Write scene prompts as readable multiline text with short paragraphs separated by blank lines. Do not store one long paragraph unless required by an external tool.

Before generation, show the user:

- scenario summary
- English dialogue
- panel role
- exact prompt
- character references being used
- style/framing example being used
- previous approved frame being used for continuity, if any

Then wait for refinement or approval.

## Meaning Bubbles

Use two visual channels:

- **Body cue**: what the character visibly does or feels.
- **Meaning bubble**: a symbolic icon/diagram for hidden, internal, absent, or specific information.

Prefer body cues for social functions:

- greeting: wave and eye contact
- apology: small bow or raised hand
- thanks: nod or hand to chest
- confusion: puzzled face and hesitant posture
- asking directions: map, gaze, pointing

Use meaning bubbles for details that body language cannot reliably encode:

- medical symptoms: cough, fever, stomach pain, leg pain
- lost objects: passport, phone, wallet
- desired items: sandwich, water, medicine
- abstract states: lateness, price concern, location, form confusion

Combine them when needed. For "my leg hurts," show the learner favoring one leg and add a small leg icon with pain rays. Do not use English text inside the bubble.

## Prompt Template

```text
Polished clean anime/comic illustration matching visuals/style/examples/approved-comic-panel-sumimasen-cue.png.
Use crisp controlled linework, warm flat colors, expressive human characters, and the same mobile-safe card-box framing as the approved panel.
Use character references: <learner-reference.png> for the learner and <partner-reference.png> for the partner.
Scene: <concrete location>.
Panel role: <cue | learner turn | resolution>.
Action: <what happens in this panel>.
Meaning support: <body cue and/or symbolic meaning bubble>.
Composition: stable medium comic panel, clear turn-taking, learner and partner both readable.
Mobile-safe composition: keep active characters, faces, hands, speech bubbles, and meaning bubbles in the central 70% of the frame; avoid placing key cues at the far edges or lower 25% of the image.
Continuity: preserve reference character identity, clothing, palette, proportions, and style.
Constraints: no subtitles, no translations, no target-language text, no source-language text, no readable dialogue text, no speech bubbles unless explicitly approved, no logos, no extra characters unless required.
Reject rough sketchbook style, children's-book style, thick marker outlines, decorative sketch borders, photorealism, and generic character drift.
```

## Quality Checklist

Before accepting generated visual assets:

- Does the learner match the approved reference?
- Does the partner match the intended archetype?
- Is the learner's turn obvious without text?
- Does the visual teach the intent, not just decorate the card?
- Are speech bubbles limited to `...` or empty bubbles?
- Are faces, hands, speech bubbles, and meaning cues readable on a phone screen?
- Are meaning bubbles symbolic rather than English labels?
- Is the panel culturally ordinary and respectful?
- Are there no captions, translations, watermarks, logos, or accidental readable text?
- Could the same character continue into the next card without feeling like a different person?
- Was the image generated with actual attached reference images, not just reference filenames in the prompt?
