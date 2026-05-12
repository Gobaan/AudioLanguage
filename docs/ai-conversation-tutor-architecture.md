# AI Conversation Tutor Architecture

This is the new product direction: curated curriculum provides the learning structure, while an AI conversation runtime handles messy learner speech, contextual judgement, and in-world response.

## Core Product Loop

```text
Scene context
  -> AI/world speaks first
  -> learner receives an intention
  -> learner speaks
  -> conversation coach interprets the attempt
  -> coach judges whether it fits the scene
  -> AI/world responds in character
  -> learning state updates
```

The product should optimize for communicative success, not pronunciation scoring.

## User Session Shape

1. Warm up with one familiar scene.
2. AI character speaks first to establish context.
3. App prompts the learner with an intention, such as "greet your friend and ask how they are."
4. Learner speaks the full line naturally.
5. Coach shows what it heard and whether it fit the scene.
6. AI character responds in-world if the attempt was close enough.
7. Session rotates review, transfer, and one small new/extended target.
8. End on a successful scene.

## Stable Curriculum, Flexible Runtime

Stable data:

- functions
- targets
- scenes
- dialogue anchors
- accepted variants
- target meanings
- review modes
- user progress

Runtime AI:

- transcribes/interprets learner speech
- maps learner utterance to communicative intent
- judges whether it fits the current scene
- responds in character
- suggests one gentle repair if needed

## Backend Shape

```text
content graph
  -> session planner
  -> conversation runtime
     -> speech interpreter
     -> communication judge
     -> roleplay responder
  -> progress updater
```

Current implementation starts with:

```text
backend/app/conversation/
  models.py
  speech.py
  judge.py
  coach.py
```

## Boundary Decisions

- `conversation` owns user attempts, scene context, interpretation, and judgement.
- `speech` owns low-level transcription, romanization, and text similarity helpers.
- `/api/conversation/attempt` is the new speech endpoint.
- `/api/transcribe` remains temporarily as a compatibility wrapper.
- The frontend should speak in terms of "fits the scene", not "pronunciation score".

## Future AI Adapter

The local judge is deliberately simple. Replace it with an AI adapter behind the same boundary:

```text
CommunicationJudge
  LocalCommunicationJudge
  OpenAICommunicationJudge
```

The AI judge should return structured output:

```json
{
  "heard_as": "vanakkam eppadi irukeenga",
  "intent": "greet_and_ask_wellbeing",
  "fits_scene": true,
  "close_enough": true,
  "response_text": "நன்றாக இருக்கிறேன். நன்றி.",
  "support_hint": "Good. The ending can be clearer, but the meaning worked."
}
```

## What To Stop Building

- waveform pronunciation grading
- chunk retry loops
- local phoneme correction as a primary feature
- deterministic pass/fail based on brittle speech matching

## What To Build Next

1. Replace the local communication judge with an AI-backed adapter.
2. Add in-character AI/world responses after a successful attempt.
3. Store attempts and update user target state.
4. Add a simple session planner over current content data.
5. Support accepted variants and valid-but-off-target responses in the judge prompt.

## Visual Design TODOs

- Design a consistent human learner avatar for comic scenes so users quickly understand which character represents them.
- Keep scene partners human and role-specific for real-world transfer.
- Use a small coach/helper outside the comic panel if extra turn clarity is needed.
