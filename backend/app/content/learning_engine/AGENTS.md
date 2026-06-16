# Learning Engine Instructions

The learning engine chooses the user's next session plan. Keep it deterministic, content-driven, and inspectable.

## Runtime Boundary

- Return a full session plan up front; do not make the frontend request one lesson at a time.
- Preserve the public import contract: `from app.content.learning_engine import build_learning_plan`.
- The frontend should render the returned JSON plan. Scheduling decisions belong here, not in React.
- Use curated model content. Do not generate beginner runtime lessons live.

## Current MVP Policy

- Target session size is 3 useful scenes.
- Sessions may be shorter than 3 scenes when there is nothing useful to practice.
- Do not pad sessions with filler review.
- Keep a later hard max of 5 scenes, but do not optimize around filling it now.
- Repair is next-session prioritization, not a long same-lesson remediation flow.
- Same-lesson correction stays lightweight: correct choice highlighting and post-attempt model line.
- Opener audio plus visual cue is the default recall and transfer cue.
- Visual-only recall is not part of beginner MVP repair.
- Learner-controlled replay is UI support, not a separate scheduled repair step.
- Unscored attempts are pending and neutral; do not count them as learned or failed.
- Multiple choice is diagnostic, not mastery.
- Spoken production scores dominate scheduling.

## Repair Categories

- `meaning_repair`: wrong meaning choice, off-target response, or evidence that the learner misunderstood the scene intent.
- `recall_repair`: learner understood the scene but could not produce the phrase.
- `transfer_repair`: learner passed the anchor but failed to use the function in a transfer scene.
- `memory_repair`: learner previously passed but failed delayed recall.
- `healthy`: learner passed the current expected review.
- `new`: unseen i+1 anchor candidate.

## Repair Diagnosis And Presentation

Diagnose repair from the strongest available signal first. Spoken production scores beat multiple-choice events. Unscored attempts are pending, not failure.

## Required Diagnostic Signals

For MVP scheduling, the current validation logs are close enough to start, but the learning engine should make these fields explicit before depending on repair classification:

- `participant_id` must be sent to the learning-plan endpoint; without it, the engine cannot personalize.
- `lessonStage` should be recorded on attempts and events, such as `guided_scene_production`, `same_day_transfer`, or `delayed_review`.
- `planPurpose` should be recorded when a planned lesson is presented, such as `meaning_repair`, `recall_repair`, `transfer_repair`, `memory_repair`, `due_review`, or `new`.
- `recording_skipped` events should be logged when the learner reaches a production step and leaves without a usable recording.
- `recordingDurationMs` and `byteCount` should continue to be stored so empty or near-empty recordings can be treated as weak production evidence.
- AI score results should preserve `communication.status`, `close_enough`, `missing_slots`, and `extra_intent`.
- Multiple-choice events should continue to store `choiceId`, `isCorrect`, `targetId`, `lessonId`, `stepId`, and `sceneSet`.

Do not infer stable scheduling policy from brittle filename parsing when an explicit field can be stored cheaply. It is acceptable to infer from existing data during migration, but new scheduler-facing events should be explicit.

### `meaning_repair`

Diagnose when:

- The learner chooses the wrong multiple-choice meaning.
- The AI score says the response is off-target, wrong function, or valid speech for the wrong scene.
- The learner says a different known phrase that fits the broad setting but not the current target.
- Wrong meaning plus failed production appears in the same target/session.

Present next:

- Use the anchor scene or the clearest available scene for that target.
- Keep opener audio plus visual cue.
- Include the meaning choice again, with plausible distractors.
- After the attempt, play the model learner line and world response.
- Do not use transfer first; the function is not anchored yet.

### `recall_repair`

Diagnose when:

- The learner chose the correct meaning but failed spoken production.
- The AI score is unclear, no response, wrong pronunciation beyond understanding, or missing required semantic slots.
- The learner skipped or submitted a very short/empty recording after reaching a production step.

Present next:

- Use the same anchor or a close anchor scene.
- Keep opener audio plus visual cue before recording.
- Play the model learner line after the attempt.
- If the phrase has 3+ meaningful chunks, include backward build.
- If the phrase is short, avoid backward build; use model audio plus one repeat attempt.

### `transfer_repair`

Diagnose when:

- The learner previously passed anchor production for the target.
- A same-day transfer or transfer-like scene failed.
- The attempt repeats the anchor context too literally or uses another known phrase instead of the same function.

Present next:

- Use a transfer scene for the same target.
- Keep opener audio plus visual cue.
- Do not play target audio before recording.
- After the attempt, play the model learner line and world response.
- If transfer fails repeatedly, downgrade the next repair to anchor recall before trying transfer again.

### `memory_repair`

Diagnose when:

- The learner previously passed the target.
- A delayed review or later recall attempt fails.
- The failure happens after the target should have been retained, not during first exposure.

Present next:

- Use the delayed review scene first when available.
- Keep opener audio plus visual cue.
- Record before playing the model learner line.
- If the learner fails again, downgrade to `recall_repair` with the anchor or a clearer scene.
- If the learner passes, restore the target to spaced review with a shorter interval than before.

### Healthy And New Content

- Mark a target `healthy` when the latest scored production is remembered in the expected mode.
- Treat correct multiple choice alone as understanding evidence, not as `healthy`.
- Select `new` content only when repair load is light.
- Pick `new` content by curriculum order until richer i+1 difficulty metadata exists.

## Session Selection

Choose scenes in this order:

1. High-priority repairs.
2. Due delayed reviews.
3. One new i+1 anchor when repair load is light.
4. Transfer for recently passed anchors.

If useful content runs out, end the session early. Short useful sessions are better than long repetitive ones.

## Critical Gaps

- Personalization requires the frontend to send `participant_id` to the learning-plan endpoint.
- Current local validation data is enough for MVP scheduling, but it is not a true long-term learner model.
- If AI scoring is delayed or unavailable, do not overreact to pending attempts.
- Current content has only 5 anchor targets, so 3-scene sessions are better for testing scheduling without exhausting content.
- i+1 selection is currently curriculum-order based; richer difficulty metadata can come later.
- Same-day transfer is optional value, not mandatory padding.
