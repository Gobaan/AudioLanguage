# Visual Production Tracker

This file tracks language-neutral visual assets and the recommended generation order.

## Process

Use this workflow for each three-frame scenario:

1. Prototype prompts with `gpt-image-1-mini` + `quality low` if the scene blocking is still unknown.
2. Promote the useful prompt wording, not the mini image.
3. Generate MVP candidate art with `gpt-image-1` + `quality medium`.
4. Use real reference inputs:
   - `visuals/style/examples/approved-comic-panel-sumimasen-cue.png`
   - needed character references from `visuals/style/characters/`
   - frame 0 as the stable scene/style anchor for later frames when consistency matters
5. Do not bake text or speech bubbles into images. The app overlays turn-taking UI.
6. Keep prompts language-neutral. Swap audio/evaluation targets per language; change visuals only when the scene or cultural action truly changes.

## Current Approved/Working Set

Scenario: `first-hi-response`

Language-neutral function: respond to a greeting.

Current files:

| Frame | Role | File | Status | Notes |
|---|---|---|---|---|
| 0 | Cue | `visuals/generated/ja/ja-first-hi-response/frame-0.png` | Working anchor | Landscape 3:2, full model, high quality. Friend greets from doorway; learner looks toward friend. |
| 1 | Learner turn | `visuals/generated/ja/ja-first-hi-response/frame-1.png` | Working | Landscape 3:2, full model. Learner responds toward friend. |
| 2 | Resolution | `visuals/generated/ja/ja-first-hi-response/frame-2.png` | Working prototype/MVP candidate | Landscape 3:2, full model medium. Friend responds with lowered hand. |

Prompt files:

- `visuals/generated/ja/ja-first-hi-response/prompts/frame-0.txt`
- `visuals/generated/ja/ja-first-hi-response/prompts/frame-1.txt`
- `visuals/generated/ja/ja-first-hi-response/prompts/frame-2.txt`

Quality comparison folder:

- `visuals/generated/ja/ja-first-hi-response/quality-examples/frame-0-high-anchor.png`
- `visuals/generated/ja/ja-first-hi-response/quality-examples/frame-2-medium-current.png`

Note: a low-quality comparison was attempted, but the saved `frame-2-low.png` needs to be regenerated if needed.

## Generation Order

Generate and approve one scenario at a time. For each scenario, generate frames in this order:

1. Frame 0: cue/setup, using style + character references only.
2. Frame 1: learner turn, using frame 0 as continuity.
3. Frame 2: resolution, usually using frame 0 as the stable scene/style anchor to avoid broken-telephone drift.

For dialogue scenes, prefer landscape `3:2` / `1536x1024`. Use square only for compact one-person/object/symptom review scenes.

## Next Scenario Order

Regenerate these legacy visuals with the new language-neutral landscape process. Existing files may exist, but they were produced before the current reference-audited workflow and should be treated as drafts.

| Order | Scenario | Type | Function | Scene | Frames |
|---:|---|---|---|---|---:|
| 1 | `ja-first-hi-response` | anchor | `respond_to_greeting` | `study-room-friend` | 3 |
| 2 | `ja-introduce-self` | anchor | `introduce_self` | `school-hallway-classmate` | 3 |
| 3 | `ja-repair-dont-understand` | anchor | `say_do_not_understand` | `busy-service-counter` | 3 |
| 4 | `ja-apologize-small-mistake` | anchor | `apologize` | `station-information-desk` | 3 |
| 5 | `ja-order-local-food` | anchor | `order_local_food` | `local-food-counter` | 3 |
| 6 | `ja-directions-hospital` | anchor | `ask_where_hospital_is` | `hospital-street-corner` | 3 |
| 7 | `ja-greeting-neighbor-transfer` | transfer | `respond_to_greeting` | `neighbor-gate` | 3 |
| 8 | `ja-greeting-entry-review` | delayed review | `respond_to_greeting` | `apartment-entry-neighbor` | 3 |
| 9 | `ja-introduce-class-transfer` | transfer | `introduce_self` | `language-class-name-tags` | 3 |
| 10 | `ja-introduce-community-review` | delayed review | `introduce_self` | `community-table-introduction` | 3 |
| 11 | `ja-repair-ticket-transfer` | transfer | `say_do_not_understand` | `ticket-machine-help` | 3 |
| 12 | `ja-repair-clinic-review` | delayed review | `say_do_not_understand` | `clinic-form-counter` | 3 |
| 13 | `ja-sumimasen-cafe-transfer` | transfer | `apologize` | `cafe-counter-attention` | 3 |
| 14 | `ja-sumimasen-station-review` | delayed review | `apologize` | `station-information-desk` | 3 |
| 15 | `ja-order-convenience-transfer` | transfer | `order_local_food` | `convenience-store-sandwich` | 3 |
| 16 | `ja-order-bakery-review` | delayed review | `order_local_food` | `bakery-counter-sandwich` | 3 |

## Prompt Preparation Status

| Scenario | Status | Notes |
|---|---|---|
| `ja-introduce-self` | Prompts prepared, images pending | Language-neutral school hallway introduction. Frame 0 uses style + learner + friend references; frames 1 and 2 are prepared to use frame 0 as continuity once approved. |

## Acceptance Checklist

Before marking a scenario usable:

- All frames use the same art style and character identity.
- No image contains readable dialogue, translations, labels, or baked-in speech bubbles.
- Characters look at each other, not the camera, unless direct address is intentional.
- The frame 0 cue makes the learner's need clear.
- The frame 1 learner action clearly expresses the target function.
- The frame 2 resolution shows the response worked socially.
- The image works on phone when contained or cropped.
- The manifest records `reference_images` for each generated frame.
