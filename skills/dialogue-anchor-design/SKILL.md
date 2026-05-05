---
name: dialogue-anchor-design
description: "Design short vivid anchor dialogue scenes for first exposure language learning. Use when Codex needs to create or revise the first stable scene for a phrase, chunk, communicative function, or scene family; define learner/world roles, emotional stake, visual cues, target response, acceptable variants, and initial retrieval path."
---

# Dialogue Anchor Design

## Purpose

Use this skill to create the first memorable scene for a language target. An anchor scene is the learner's home base for a chunk or communicative function.

The anchor should be stable enough to remember, vivid enough to matter, and short enough to avoid becoming a memorized script.

## Core Rule

Anchor scenes teach one communicative job.

Examples:

- Greet and ask wellbeing.
- Ask for a price.
- Request help.
- Apologize.
- Ask for directions.
- Refuse politely.

Do not use one anchor to teach many jobs. When a second job appears, create a sibling scene or extension.

## Anchor Shape

For first exposure, prefer 3 turns:

1. World speaker gives a cue.
2. Learner gives the target line.
3. World speaker responds or resolves.

Good beginner anchor:

```text
Friend: Hello!
Learner: Hello! How are you?
Friend: Fine. Thank you.
```

Maximum useful beginner anchor:

```text
4-6 turns
```

Avoid going beyond 6-8 turns. Long anchors become script memorization.

## Scene Requirements

Each anchor must define:

- **Scene id**: stable kebab-case id.
- **Function**: the communicative job.
- **Place**: concrete location.
- **People**: learner role and world speaker role.
- **Stake**: why the exchange matters, even mildly.
- **Visual cue**: what makes the learner know it is their turn.
- **Target response**: the canonical learner line.
- **Accepted variants**: close responses allowed later.
- **Too-open variants**: valid language that should wait for free-response modes.
- **Dialogue**: 3-4 lines for first exposure.
- **Storyboard hook**: what gesture/object/gaze makes meaning visible.

## Target Response Contract

Early practice needs a clear target. Natural language is non-deterministic, but first exposure should not be.

For each target, specify:

```json
{
  "target_function": "greet_and_ask_wellbeing",
  "canonical_response": "Hello! How are you?",
  "accepted_variants": [
    "Hi, how are you?",
    "Hello, how are you?"
  ],
  "valid_but_off_target": [
    "Hey, what's up?"
  ]
}
```

Accept variants only when the practice mode allows them. In targeted recall, guide the learner back to the canonical chunk.

## Visual Design

The visual should explain why the target line fits.

Include:

- Speaker gaze and body orientation.
- Turn-taking cue.
- Gesture mapping for the target phrase.
- Object or setting clue when relevant.
- Emotional result after the learner response.

Use natural gestures, not formal sign-language signs, unless explicitly teaching a signed language with expert review.

## Output Format

When creating an anchor scene, output:

- Scene id
- Function
- Level: first exposure
- Scene setup
- Target response contract
- Dialogue
- Learner line
- Visual cue and gesture mapping
- First review mode
- Extension candidates
- Transfer candidates

## Quality Checklist

- Is the scene one small human moment?
- Does the world speaker cue the learner clearly?
- Is the learner line useful outside this scene?
- Is there one main target response?
- Are acceptable variants separated from the canonical target?
- Is the scene short enough to replay without fatigue?
- Does the visual context carry meaning without translation text?
