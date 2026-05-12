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

Speech bubbles may contain only a neutral placeholder such as `...` when useful for turn-taking. Do not reveal the line in the image.

## Default Panel Structure

Use three panels for a basic practice card:

1. **Cue panel**
   - Partner/world creates the need to respond.
   - Partner may have a `...` speech bubble.
   - The learner should understand the situation before knowing the words.

2. **Learner-turn panel**
   - Show the learner's intended communicative act.
   - Use gesture, gaze, object handling, and posture to make the meaning visible.
   - Learner may have a `...` speech bubble.

3. **Resolution panel**
   - Show the partner's reaction or the practical result.
   - Confirm that the response worked.
   - This panel should make the social payoff visible.

For harder transfer cards, keep the same function but vary the setting, partner, stakes, or object while preserving the learner's intention.

## Prompt Rules

Every image prompt should include:

- style: simple flat webcomic illustration
- setting: concrete real-world location
- characters: learner and partner roles
- composition: who is foregrounded and why
- gesture: the visual clue for meaning
- bubble rule: empty speech bubble or `...` only, if needed
- continuity: same characters, clothing, setting, and props across the card
- constraints: no captions, no translations, no readable sentence text, no logos

Example:

```text
Simple flat webcomic illustration, clean line art, expressive human characters.
A learner stands at a market stall facing a friendly vendor behind the counter.
The vendor gestures toward fresh fruit and has an empty speech bubble with "...".
The learner looks attentive, holding a small shopping bag.
Bright market background with simple produce crates, no readable signs.
No subtitles, no translations, no dialogue text except "...", no logos.
```

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
- Would this transfer to a real human situation?
- Is the generated image decorative, or does it actually teach the moment?

If a visual does not clarify the learner's intention, revise the panel prompt before adding more text to the UI.
