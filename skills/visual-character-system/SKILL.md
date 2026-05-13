---
name: visual-character-system
description: Create and maintain reusable character bibles, avatar reference sheets, partner archetypes, visual identity rules, and reference-image workflows for language-learning comic scenes. Use when Codex designs base characters, generates or updates avatar references, preserves character consistency across AI-generated panels, chooses symbolic meaning bubbles versus body cues, or organizes visual assets under visuals/style.
---

# Visual Character System

## Purpose

Use this skill to keep language-learning scene visuals consistent across cards, languages, and generated assets.

Do not depend on text prompts alone for recurring characters. Store approved base references locally, use them as image inputs when possible, and treat prompt-only generations as drafts until identity is checked.

## Asset Structure

Use this project structure:

```text
visuals/style/
  character_bible.md
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

- global style: comic style, line weight, palette, rendering level
- learner avatar: age range, outfit, hair, silhouette, recurring props
- partner archetypes: staff, vendor, friend, pharmacist, local helper
- turn-taking conventions: where learner and partner usually appear
- symbol rules: how speech bubbles and meaning bubbles work
- invariants: what must not change between panels
- review checklist: what counts as identity drift

Keep the bible concise enough to paste into generation prompts when image references are unavailable.

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
4. Generate one card's three frames using the references.
5. Inspect for identity, gesture, turn-taking, and meaning clarity.
6. Only then scale to more cards.

When generating a frame, include:

- the exact reference filenames used
- the role of each character in the scene
- the panel number and timing role
- the learner intention
- the body cue or meaning bubble that carries meaning
- mobile-safe composition: central characters, large faces/hands, readable bubbles, and no key meaning in the lower overlay area
- constraints: no readable dialogue, no translations, no subtitles, no logos

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
Simple flat webcomic illustration, clean line art, expressive human characters.
Use character references: <learner-reference.png> for the learner and <partner-reference.png> for the partner.
Scene: <concrete location>.
Panel role: <cue | learner turn | resolution>.
Action: <what happens in this panel>.
Meaning support: <body cue and/or symbolic meaning bubble>.
Composition: stable medium comic panel, clear turn-taking, learner and partner both readable.
Mobile-safe composition: keep active characters, faces, hands, speech bubbles, and meaning bubbles in the central 70% of the frame; avoid placing key cues at the far edges or lower 25% of the image.
Continuity: preserve reference character identity, clothing, palette, proportions, and style.
Constraints: no subtitles, no translations, no readable dialogue text except optional "...", no logos, no extra characters unless required.
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
