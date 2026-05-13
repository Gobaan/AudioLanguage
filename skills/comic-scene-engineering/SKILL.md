---
name: comic-scene-engineering
description: Design and engineer comic-panel visual scenes for language-learning practice cards. Use when Codex creates or refactors scene data, practice cards, image prompts, comic panel metadata, visual turn-taking, speech bubbles, asset pipelines, or app UI that teaches meaning through context without showing translations or target dialogue by default.
---

# Comic Scene Engineering

## Purpose

Use this skill to build language-learning scenes as programmable comic panels.

The visual system should help the learner infer:

- Who is speaking.
- What situation they are in.
- What the learner is supposed to accomplish.
- When it is the learner's turn.
- Whether the response worked socially.

The app should teach meaning through context, gesture, turn-taking, and consequence rather than native-language translation.

## Core Decision

Generate comic panels as visual assets. Render the learning interface in code.

Do not generate a whole app screen as one image. The image generator should produce panels; the frontend should own:

- audio playback
- recording state
- "They say" / "You say" prompts
- turn progression
- feedback
- retry buttons
- accessibility labels
- spacing and responsive layout

This keeps learning behavior programmable and keeps generated images reusable.

## Visual Style

Prefer simple human webcomic characters.

Use:

- clean line art
- flat colors
- expressive human faces
- readable gestures
- simple backgrounds
- consistent clothing, props, and setting across panels

Avoid:

- realistic characters for MVP, because consistency and gesture fidelity are harder
- animal mascots for real-world dialogue scenes, because they weaken transfer to human social situations
- decorative backgrounds that do not teach the interaction
- captions, subtitles, translations, or target-language sentence text

For guided dialogue cards, every speaking panel should include one speech bubble from the active speaker containing only `...`, unless it would hide the key gesture or make the panel cluttered. The bubble is a turn-taking signal, not a text hint. Do not reveal the line, phonetics, or translation in the image.

## Character References

Use stored reference images and a character bible when generating scene panels. Do not rely only on repeated text descriptions for recurring avatars; prompt-only identity will drift.

Before producing production panels for a recurring card family:

- Create or load `visuals/style/character_bible.md`.
- Use approved reference sheets from `visuals/style/characters/`.
- Name the reference image used for each character in every panel prompt.
- Keep learner, partner archetype, clothing, body proportions, line style, and palette stable across panels.
- Create a new partner archetype only when the social role changes in a way learners must recognize.

Recommended reference assets:

```text
visuals/style/
  character_bible.md
  characters/
    learner-reference.png
    staff-reference.png
    vendor-reference.png
    friend-reference.png
    pharmacist-reference.png
```

When a generation tool supports image references, use the approved reference image as an input. When it does not, copy the concise character bible description into the prompt and mark the resulting asset for identity review.

## Default Panel Structure

Use three panels for a basic practice card:

1. **Cue panel**
   - Partner/world creates the need to respond.
   - Partner should have a `...` speech bubble when the partner is speaking.
   - The learner should understand the situation before knowing the words.

2. **Learner-turn panel**
   - Show the learner's intended communicative act.
   - Use gesture, gaze, object handling, and posture to make the meaning visible.
   - Learner should have a `...` speech bubble when the learner is speaking.

3. **Resolution panel**
   - Show the partner's reaction or the practical result.
   - Partner should have a `...` speech bubble when the partner responds.
   - Confirm that the response worked.
   - This panel should make the social payoff visible.

For harder transfer cards, keep the same function but vary the setting, partner, stakes, or object while preserving the learner's intention.

## Prompt Rules

Every image prompt should include:

- style: simple flat webcomic illustration
- character references: approved learner and partner reference filenames, or a concise reference description if image input is unavailable
- setting: concrete real-world location
- characters: learner and partner roles
- composition: who is foregrounded and why
- gesture: the visual clue for meaning
- meaning bubble: symbolic visual bubble only when it clarifies internal state, pain, desire, object choice, or hidden information
- bubble rule: guided dialogue speaking panels use a `...` speech bubble from the active speaker by default; never include line text
- mobile-safe composition: keep active characters, faces, hands, bubbles, and meaning cues in the central 70% of the frame and above the lower 25% so phone scaling and app overlays do not hide them
- continuity: same characters, clothing, setting, and props across the card
- constraints: no captions, no translations, no readable sentence text, no logos

Example:

```text
Simple flat webcomic illustration, clean line art, expressive human characters.
Use learner-reference.png for the learner and vendor-reference.png for the vendor.
A learner stands at a market stall facing a friendly vendor behind the counter.
The vendor gestures toward fresh fruit and has an empty speech bubble with "...".
The learner looks attentive, holding a small shopping bag.
Bright market background with simple produce crates, no readable signs.
Mobile-safe composition: both characters and the vendor gesture are readable in the central 70% of a phone-sized frame; leave quiet space near the bottom center for the app overlay.
No subtitles, no translations, no dialogue text except "...", no logos.
```

## Meaning Bubbles and Body Cues

Use body cues for visible social meaning. Use symbolic meaning bubbles for hidden or specific meaning.

Show it on the character when the meaning is directly observable:

- greeting: wave, smile, eye contact
- apology: small bow, softened posture, raised hand
- confusion: puzzled face, hesitant posture
- request: pointing to a visible object
- direction: looking or pointing toward a path

Use a symbolic meaning bubble when the meaning is internal, medical, absent, or too specific to infer from posture alone:

- pain location: leg icon with pain rays, stomach discomfort icon
- symptoms: cough cloud, thermometer, medicine bottle
- lost item: passport, phone, wallet icon
- preference or choice: desired food/item icon when multiple objects are visible
- abstract problem: clock for lateness, map pin for location, question mark over a form

Do not use English words inside meaning bubbles. Prefer icons, simple diagrams, arrows, color emphasis, and facial/body context. When useful, combine both: the learner limps and a small leg-pain bubble clarifies the exact issue.

## Data Shape

Scene and card data should separate curriculum meaning from visual rendering.

Prefer a structure like:

```json
{
  "card_id": "ta-market-order-001",
  "function_id": "order_food",
  "scene_id": "market_stall",
  "panels": [
    {
      "id": "cue",
      "role": "partner_speaks",
      "image_prompt": "...",
      "character_refs": ["staff-reference.png", "learner-reference.png"],
      "audio_role": "partner_line",
      "meaning": "The vendor is ready to take an order."
    },
    {
      "id": "learner_turn",
      "role": "learner_speaks",
      "image_prompt": "...",
      "audio_role": "learner_prompt",
      "meaning": "The learner asks for the item."
    },
    {
      "id": "resolution",
      "role": "partner_responds",
      "image_prompt": "...",
      "audio_role": "partner_response",
      "meaning": "The vendor understood and starts preparing the order."
    }
  ]
}
```

## Engineering Rules

- Keep visual panels reusable, but do not reuse a panel if the learner intention changes.
- Keep scene logic in data, not hard-coded branches.
- Let the app decide which panel is active based on the current turn.
- Let generated assets be replaceable without changing the learning flow.
- Store prompts beside generated assets so panels can be regenerated.
- Use stable ids for panels, scenes, functions, and dialogue turns.
- Support language-specific cultural variants, but keep the interaction function language-neutral when possible.

## Learning Checks

Before accepting a scene, ask:

- Can the learner infer what is happening without translation?
- Is the learner's turn visually obvious?
- Does the resolution show why the response mattered?
- Are gestures clarifying meaning without becoming silly pantomime?
- Are the characters, speech bubbles, and key gestures readable on a phone viewport?
- Would this transfer to a real human situation?
- Is the generated image decorative, or does it actually teach the moment?

If a visual does not clarify the learner's intention, revise the panel prompt before adding more text to the UI.
