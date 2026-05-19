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

Design visual prompts to be language-neutral by default. A greeting, apology, food order, direction request, or pharmacy request should usually reuse the same visual scene across target languages. Only make the visual culturally specific when the setting, object, etiquette, or social distance truly changes the learner's intended action.

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

Prefer polished human comic/anime-style characters that match the approved example.

Use `visuals/style/examples/approved-comic-panel-sumimasen-cue.png` as the approved style, composition, and card-box-fit example when preparing new image prompts. This image is the current reference for:

- polished clean anime/comic rendering
- crisp controlled linework, not rough sketchbook lines
- warm flat color with light environmental detail, not painterly realism
- readable character scale inside the card image box
- mobile-safe framing
- restrained background detail
- clear turn-taking without target-language text

Use:

- clean line art
- polished flat colors with the same finish as the approved panel
- expressive human faces
- readable gestures
- simple backgrounds
- consistent clothing, props, and setting across panels

Avoid:

- rough hand-drawn sketch style
- children's-book illustration style
- thick uneven marker outlines or decorative sketch borders
- realistic characters for MVP, because consistency and gesture fidelity are harder
- animal mascots for real-world dialogue scenes, because they weaken transfer to human social situations
- decorative backgrounds that do not teach the interaction
- captions, subtitles, translations, or target-language sentence text

For guided dialogue cards, prefer rendering speech bubbles in the app instead of baking them into generated images. The bubble is functional turn-taking UI and must attach to the correct speaker every time. Generated images should usually contain no speech bubbles or text; store speaker/bubble anchor metadata separately and let the frontend overlay `...`, highlights, and timing.

Only allow baked-in `...` bubbles for a deliberate visual experiment, and reject the image if the bubble attaches to the wrong person, blocks the gesture, or weakens mobile readability.

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
  examples/
    approved-comic-panel-sumimasen-cue.png
  characters/
    learner-reference.png
    staff-reference.png
    vendor-reference.png
    friend-reference.png
    pharmacist-reference.png
```

When a generation tool supports image references, the approved reference images must be attached as real image inputs. Naming a local filename inside the prompt is not enough; the model cannot see local files from text.

When a generation tool supports style/reference images, include `visuals/style/examples/approved-comic-panel-sumimasen-cue.png` as a style and framing reference in addition to the character references. If the tool only accepts text prompts, stop and tell the user the result will be a draft only. Do not present prompt-only output as production-ready.

For multi-frame cards, include the previous approved frame as an additional continuity reference when generating the next frame. Frame 1 should see frame 0; frame 2 should see frame 1. This helps preserve character placement, room layout, camera distance, lighting, and the visual progression of the dialogue. Do not use a rejected previous frame as continuity input.

For multi-frame cards, prompt the next frame as an update to a believable scene, not as a fresh character pose. The new frame should preserve the room geometry, camera family, character scale, and social sightlines from the previous approved frame.

For this repo, use `scripts/generate_images_from_manifest.py` with reference mode enabled for production panels:

```powershell
python scripts\generate_images_from_manifest.py --language ja --dialogue-id <dialogue-id> --limit 1 --force --reference-mode always --quality low
```

The manifest entry should record `reference_images` after generation. If it does not, the panel was not generated with real visual references.

During prototype visual exploration, use `gpt-image-1-mini` and `--quality low` by default. Move to `gpt-image-1` and `--quality medium` only when composition and prompt shape are mostly working. Use `--quality high` only for final or near-final assets after the user approves the scene direction. Do not burn high-quality generations while still discovering composition.

## Human Review Workflow

Do not bulk-generate scene images.

Visual production must proceed one image at a time until the user explicitly approves the style, character identity, framing, and scene readability. In normal mode, summarize the next visual change briefly instead of pasting the full prompt. Show the full prompt only when the user asks, when prompt approval is explicitly needed, or when working in debug mode.

Before generating any image in debug or prompt-approval mode, present:

1. Scenario id and plain-English scenario summary.
2. The dialogue in English, with speaker roles and turn order.
3. Which single panel is being designed: cue, learner turn, or resolution.
4. The exact image prompt.
5. A short note about which local character reference images should be used.
6. A note that `visuals/style/examples/approved-comic-panel-sumimasen-cue.png` is the approved style/framing example.
7. For frame 1 or later, which previously approved frame will be attached as continuity reference.

Wait for the user to refine or approve the prompt before calling any image-generation tool. If the user changes the prompt, update the saved prompt file first, then generate only that one image. After generation, show or reference the single output and wait for approval before generating the next panel.

If a generated image does not match the approved characters, comic style, box framing, or mobile-safe composition, treat it as rejected. Revise the prompt or reference workflow instead of continuing to the next image.

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

- style: polished clean anime/comic illustration matching `approved-comic-panel-sumimasen-cue.png`
- character references: approved learner and partner reference filenames, plus concise character descriptions from the character bible
- style example: `visuals/style/examples/approved-comic-panel-sumimasen-cue.png`
- setting: concrete real-world location
- characters: learner and partner roles
- composition: who is foregrounded and why
- gesture: the visual clue for meaning
- language-neutral communicative function: what the learner is trying to do, not the target-language words
- meaning bubble: symbolic visual bubble only when it clarifies internal state, pain, desire, object choice, or hidden information
- bubble rule: do not draw speech bubbles by default; the app should overlay turn-taking bubbles from metadata
- mobile-safe composition: keep active characters, faces, hands, bubbles, and meaning cues in the central 70% of the frame and above the lower 25% so phone scaling and app overlays do not hide them
- continuity: same characters, clothing, setting, and props across the card
- constraints: no captions, no translations, no target-language text, no source-language text, no readable sentence text, no logos

Write prompts as readable multiline text. Use short paragraphs separated by blank lines instead of one long paragraph. This makes prompts easier to review, refine, diff, and reuse.

Prompt scene composition as a natural candid comic panel:

- Characters should feel placed inside a real environment with believable distance, furniture, counters, doorways, and sightlines.
- Avoid oversized foreground portraits unless the learning moment truly needs a close-up.
- Avoid staged two-character poses, sticker-like character art, reaction shots, and character reference-sheet framing.
- Avoid having characters face the camera unless the scene specifically requires direct address.
- Use human eye-level medium-wide framing with enough room context to understand where both people are.
- For learner-turn panels, aim the learner's gaze, face angle, torso, and gesture toward the partner, not toward the viewer.

Use stable generic frame roles across all languages:

- Frame 0 cue: partner/world creates the need to respond.
- Frame 1 learner turn: learner performs the intended action.
- Frame 2 resolution: partner/world confirms the response worked.

Do not put the target words into the image prompt unless the user is explicitly creating text assets. The same visual prompt should work for Japanese, Tamil, Spanish, Russian, Cantonese, or any other language by swapping the audio and evaluation target, not by changing the visual meaning.

The prompt must also specify the output framing:

- Use landscape `3:2` / `1536x1024` for two-person dialogue scenes where natural staging, distance, counters, doorways, or approach paths matter.
- Use square `1:1` for simple one-person, object, symptom, or compact review scenes.
- Do not force two-person dialogue scenes into square if it causes oversized foreground portraits or camera-facing character poses.
- Keep the important action in the central safe area so the app can contain, crop, or letterbox on mobile.
- Use portrait `4:5` or `3:4` only when the learning moment truly needs more body language or vertical space.
- Match the framing and visual density of `approved-comic-panel-sumimasen-cue.png`.
- Stable medium comic panel, not a full app screenshot and not a poster.
- Important faces, hands, speech bubbles, and props centered and large enough for phone display.
- Leave quiet lower space for app controls and avoid placing essential cues near the lower edge.
- No cropped-off heads, hands, speech bubbles, or key props.

Example:

```text
Polished clean anime/comic illustration matching visuals/style/examples/approved-comic-panel-sumimasen-cue.png.
Use crisp controlled linework, warm flat colors, light realistic environment detail, readable human faces, and the same card-box composition discipline as the approved panel.
Use learner-reference.png for the learner and vendor-reference.png for the vendor.
A learner stands at a market stall facing a friendly vendor behind the counter.
The vendor gestures toward fresh fruit and has an empty speech bubble with "...".
The learner looks attentive, holding a small shopping bag.
Bright market background with simple produce crates, no readable signs.
Mobile-safe composition: both characters and the vendor gesture are readable in the central 70% of a phone-sized frame; leave quiet space near the bottom center for the app overlay.
No subtitles, no translations, no dialogue text, no speech bubbles, no logos.
Reject rough sketch style, children's-book style, thick marker outlines, decorative sketch borders, photorealism, and app screenshot layouts.
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
