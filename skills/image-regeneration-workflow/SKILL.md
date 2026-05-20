---
name: image-regeneration-workflow
description: Regenerate or revise existing AI-generated image assets with small targeted changes while preserving approved style, character identity, composition, and useful parts of the current draft. Use when Codex needs to fix cropped hands, wrong gaze, wrong speech bubble placement, layout drift, style drift, continuity errors, or other small visual defects in generated language-learning comic panels.
---

# Image Regeneration Workflow

## Core Rule

Choose the regeneration mode based on what is broken.

Attach:

- the approved style reference
- the required character references
- the previous approved frame when preserving multi-frame continuity

Attach the current rejected draft only when it helps. Tell the model what to preserve and what to change.

For final dialogue images, add a deterministic speech-bubble contract before generation:

- Read the dialogue metadata for the exact frame speaker before writing the image prompt.
- If the frame has an active speaking character, draw exactly one clean white speech bubble containing exactly `...`.
- Attach the bubble tail to that frame's speaker only. Name the role, visual identity, and intended left/right/center position in the prompt.
- Explicitly forbid attaching the bubble to the other character.
- If the frame is a silent action/setup beat, draw no speech bubble.
- Never include any other readable text, including target language, translations, signs, labels, captions, or accidental words such as "hello".

Use this prompt shape:

```text
Speech bubble contract:
- Speaker for this frame: <role>.
- Speaker visual identity and position: <description, left/right/center>.
- Draw exactly one white speech bubble containing exactly: ...
- Bubble tail must point to <role>, not <other role>.
- Do not attach the bubble to <other role>.
```

For silent openers:

```text
Speech bubble contract:
- This frame has no speaking character.
- Draw no speech bubble.
```

## Two Regeneration Modes

Use **draft-reference revision** for crop, layout, color, framing, and small environment fixes where the current draft is mostly right.

Good examples:

- cropped hand, elbow, doorway, or object
- scene needs slightly wider framing
- background detail needs to stay similar
- character identity/style is good and the fix is local

Use the rejected draft as a reference in this mode.

Use **clean regeneration** for pose, gesture, gaze, object physics, wrong active speaker, wrong expression, wrong speech bubble placement, or any issue where the rejected draft visually demonstrates the exact mistake.

Good examples:

- hand is waving toward the camera instead of another character
- pencil floats in midair
- learner looks at the viewer instead of the partner
- speech bubble attaches to the wrong speaker
- body pose contradicts the intended action

Do not attach the rejected draft in this mode. It reinforces the bad pose. Use the previous approved frame, style reference, and character references instead.

Use **role-separated reference regeneration** when one image has the right style/continuity and another image has the right pose/action but the wrong style.

Good examples:

- frame 1 has the right art style and room continuity
- frame 2 has the right lowered-hand response posture but a mismatched art style

Attach both images, but name their jobs clearly:

- primary style/continuity reference: the approved frame whose art style, linework, lighting, camera, character identity, and room layout should dominate
- action-only reference: the draft whose pose, gesture, or object placement should be borrowed without copying its rendering style

Do not let the action-only reference override style, character proportions, lighting, camera, or room layout.

For final art, prefer **prompt promotion** over using prototype images as references. Mini-model outputs are disposable sketches: use them to discover scene blocking and gesture wording, then promote the useful prompt changes into a full-model generation that uses only approved style references, character references, and approved full-model continuity frames. Do not use mini outputs as final continuity/style references unless there is no better option.

## Revision Prompt Shape

Use readable multiline text:

```text
Use <current-frame.png> as the current draft to revise.

Preserve: <specific good parts>.

Change: <specific visual defects to fix>.

Do not change: <identity, style, camera family, useful setting details>.
```

For crop fixes, ask for reframing:

```text
Move or reframe the subject farther inside the square image.
Leave comfortable margin around the cropped hand, elbow, head, object, or doorway.
Do not crop the corrected area again.
```

For pose/object fixes, ask for a clean update:

```text
Use the previous approved frame as continuity reference.

Change: <new pose, gaze, gesture, or object placement>.

Avoid: <the specific bad pose or impossible object physics>.

Do not use the rejected draft as a reference for this pose fix.
```

For role-separated reference fixes, ask for reference precedence:

```text
Use <approved-frame.png> as the primary style, continuity, character identity, room layout, camera, and lighting reference.

Use <action-draft.png> only as a loose action/posture reference for <specific gesture>.

Preserve the primary reference style exactly. Do not copy the action draft's face style, linework, proportions, lighting, or rendering.
```

## Prompt Visibility

Do not show the full prompt during normal visual iteration unless the user asks, the prompt needs approval, or the session is explicitly in debug mode.

In normal mode, summarize the intended change in one or two sentences, then generate one image.

## Review Discipline

Generate one revision at a time.

After generation, compare the revision against:

- the approved style example
- the character references
- the rejected draft, only if it was useful as a revision reference
- the specific defect being fixed

Accept only if the targeted defect is fixed without introducing a worse issue.

## Repo Command

For this repo, image generation defaults to draft output under `visuals/Drafts/<dialogue-id>/`.

Draft output is only for prototype images: `gpt-image-1-mini` with `--quality low`. Never write medium-quality, high-quality, or full `gpt-image-1` generations into Drafts. Those are good-copy or production assets and must use `--output-mode production`.
Include the current draft with `--reference-image` only for draft-reference revision mode:

```powershell
python scripts\generate_images_from_manifest.py --language ja --prompt-id <prompt-id> --limit 1 --force --reference-mode always --quality low --reference-image <current-draft.png>
```

Use `--no-previous-frame` for frame 0. For frame 1 or later, keep previous-frame continuity enabled unless explicitly revising a standalone asset.

For clean regeneration mode, omit `--reference-image`.

Use `gpt-image-1-mini` and `--quality low` for prototype fixes. Upgrade to `gpt-image-1` and `--quality medium` only after the correction is visually working. Medium-quality upgrades must be generated with `--output-mode production`, not Drafts. Reserve `--quality high` for final polish after the scene direction is approved.

Only write production app assets after a draft has been accepted:

```powershell
python scripts\generate_images_from_manifest.py --language ja --prompt-id <prompt-id> --output-mode production --model gpt-image-1 --quality medium --force
```

Before generating frame 1 or frame 2 as a good copy, verify the previous frame reference is itself an accepted production/good-copy image. If frame 0 is still only a low-quality draft, regenerate/promote frame 0 first or explicitly tell the user that frame 1 will inherit a draft anchor.
