# Content Model Instructions

Content is the source of truth for lessons. The app should be able to switch languages, scene sets, and review modes by requesting different backend-served JSON, not by changing frontend logic.

Keep content graph files focused:

- `targets.json`: phrase/function targets and learner-facing text/audio text.
- `dialogues.json`: ordered speaker turns and scene dialogue.
- `practice_cards.json`: runtime lesson/review card structure.
- `visual_beats.json`: frame-level visual references.
- `audio_assets.json`: audio file references and playback targets.
- `distractors.json`: plausible multiple-choice alternatives.

Runtime lesson JSON should say what happens at each step: visual frame, audio target, prompt text, recording mode, choices, and expected response. It should not include generation-only visual metadata.

Session flow rules:

- Start with due review before adding new content.
- A normal session should bias toward review, then transfer, then new/extension content only when review is healthy.
- End with a real communicative success, not just exposure.
- Track capability as coverage, control, retention, transfer, fluency, repair, and maintenance.
- User-facing progress states should be meaningful: introduced, can repeat, can say with scene, can use in new scene, remembered after a break, maintained.

Scene and review boundaries:

- Anchor scenes introduce a phrase in a vivid stable context.
- Repeat-with-mic is useful for first exposure and should combine listen, "now you say it", and recording for the same target.
- Scene recall is better for transfer or later review than immediately forcing the same line twice.
- Transfer scenes are separate scenes that test the same communicative function in a new context.
- Delayed scenes are separate review sessions or links during the MVP.
- Scorecards and scheduled review plans are overall lesson/session concerns, not embedded inside individual lesson JSON.

Stage playback rules:

- **Anchor** (`guided_scene_production`): hear the model learner line before the first record attempt; full-scene primer and meaning guess before production are allowed.
- **Same-day transfer** (`same_day_transfer`): test first in the new scene. Play only the partner opener cue before production. Do not autoplay the learner line or world response before the mic step. Do not reveal learner script text before the first record attempt. Play the model learner line and optional world response only after the attempt.
- **Delayed review** (`delayed_review`): same test-first rule as transfer, with stricter meaning-check difficulty and no full-scene primer beyond the opener cue.
- **Remediation after failure**: optional replay of the model line before a retry only; do not restore full-scene primer on every transfer or delayed run.

Transfer and delayed cards should follow their `playback_flow` order: partner cue, record attempt, model learner line after attempt, optional world response after attempt.

Distractor rules:

- Multiple-choice options should be plausible interpretations of the same scene, not random phrases.
- Do not prefix wrong answers with boilerplate such as "the learner says".
- Use four reasonable options by default.
- Easy distractors can differ in intent; medium distractors should be close but wrong; hard distractors should be tempting alternatives that a learner could confuse with the target.
- Distractors can be shared across languages when the scene meaning is the same, unless a language-specific nuance changes the correct interpretation.
