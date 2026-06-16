# Language Scenario Instructions

Generate scenarios as small human moments, not vocabulary containers. Each scene needs a clear place, two speaker roles, a tiny stake, a visible action or gesture, and one target communicative function.

Dialogue shape:

- Use short alternating turns.
- First exposure scenes usually need 2 to 4 turns.
- Deeper scenes can grow to 6 to 8 turns, but freeze an anchor at 4 to 6 turns if adding more would bloat it.
- Prefer this line shape when possible: world opener, learner target, optional world response.
- Keep learner/world roles consistent so the learner knows when they are expected to respond.
- For beginner active session cards, treat the dialogue as a cue contract: `world_opener` cues the response, `learner_target` is the taught target, and `world_response` confirms that the response worked.
- Keep beginner `world_opener` lines short and cue-like. They should not require the learner to understand extra task logic such as filling forms, pressing buttons, moving to another counter, or following multi-step instructions.
- Keep beginner `world_response` lines as simple confirmation only. Do not introduce a new task, new important vocabulary, or a follow-up question unless that response is the target of a later card.
- Let the visual scene carry object/task complexity. The dialogue should not become an explanation of the visual.
- Keep dialogue speaker roles aligned with the scene characters in `model/content/curriculum/scenes.json`. Audio generation resolves `speaker_role` through `scripts/character_cast.py`; do not introduce a new speaker role without adding its character identity, visual reference, and voice mapping.

Learning progression:

- Use one meaningful stretch at a time.
- Deepen anchor scenes for chunking only when the original scene still stays clear.
- Use transfer scenes when the learner needs to prove they can use the same function in a different situation.
- For long breaks, return to familiar anchors, increase support, pause new content unless recall is strong, then rebuild intervals from today's performance.

Beginner language display:

- For Japanese, Cantonese, Tamil, and other non-Latin beginner lessons, include romanized learner-facing text or `audioText` that approximates the sound.
- Native script can be retained as source data, but do not make it the only visible support in the MVP.
- Do not reveal the target line before the first meaning/response attempt unless the step is explicitly a listen-and-repeat step.

Scenario quality checks:

- The learner should be able to infer the scene from visuals and audio cues.
- The target response should feel like something a real person would say under the scene pressure.
- Wrong multiple-choice answers should be plausible but clearly wrong after the reveal.
- Avoid scenes that only demonstrate a word without a reason to say it.
- Avoid tab names, titles, or other UI labels that leak the answer before the learner has to infer it.
