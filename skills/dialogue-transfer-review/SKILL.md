---
name: dialogue-transfer-review
description: "Design transfer scenes and spaced review tasks for language dialogue chunks. Use when Codex needs to create varied scenes for the same communicative function, schedule reviews, handle acceptable variants, measure memory decay, design retrieval modes, or decide when a target moves from active practice to maintenance."
---

# Dialogue Transfer Review

## Purpose

Use this skill to make spaced repetition contextual. The target is not the whole dialogue; the target is a chunk, function, or response under a support level.

## Core Rule

Repeat the communicative job, not the exact card forever.

For a target such as "Hello! How are you?", review can appear as:

- Same anchor visual, produce the line.
- New transfer scene, same response.
- Hear the other person's reply and infer the missing line.
- Free response after mastery.

## Target Model

Track targets like this:

```json
{
  "target_id": "greet_and_ask_wellbeing",
  "canonical_phrase": "Hello! How are you?",
  "function": "ask wellbeing after greeting",
  "anchor_scene_id": "ta-greeting-hello",
  "accepted_variants": ["Hi, how are you?", "Hello, how are you?"],
  "support_level": "visual_only",
  "last_success_at": null,
  "next_due_at": null,
  "transfer_successes": 0
}
```

## Review Modes

Use a support ladder:

1. Full model: hear line and see visual.
2. Echo: hear line, repeat it.
3. Visual cue: see scene, produce line.
4. Response cue: hear reply, infer your line.
5. Transfer: same function in a new scene.
6. Free response: respond naturally.

Success should push the target up the ladder or lengthen the interval. Failure should shorten the interval or add support.

## Transfer Scene Rules

Transfer scenes should preserve the function while varying surface context.

Good transfer for greeting:

- Friend enters study room.
- Neighbor waves at the gate.
- Classmate sees the learner in the hallway.

Bad early transfer:

- Doctor asks what hurts.
- Cashier asks what the learner wants.
- Friend texts late at night.

The new scene should be different enough to prevent memorized pattern matching but clear enough to cue the same response.

## Non-Deterministic Language

Natural language has many valid responses. Keep practice mode explicit.

Score in layers:

- Exact canonical phrase: strongest targeted retrieval.
- Accepted variant: communicatively correct.
- Same function but off-target: acknowledge, then ask for practiced phrase.
- Valid but wrong mode: accept only in free response.
- Wrong function: retry with support.

Example feedback:

```text
That works as a greeting. For this card, practice: "Hello! How are you?"
```

## Spacing Logic

Use intervals as estimates, not punishments.

Suggested early intervals:

```text
same session -> next day -> 3 days -> 7 days -> 14 days -> 30 days
```

After success:

- Increase interval.
- Reduce support.
- Add transfer if not yet proven.

After failure:

- Shorten interval.
- Return to anchor.
- Increase support.
- Avoid adding new extension that session.

## Long Breaks And Decay

Do not reset the learner after a break. Recalibrate.

If overdue by:

- 1-2x interval: test at current support.
- 3-5x interval: add one support level.
- 5x+ interval: return to anchor scene first.

Measure decay through:

- Accuracy.
- Time to start speaking.
- Attempts.
- Support needed.
- Transfer success.
- Last successful interval.

## Maintenance

Move a target to maintenance when:

- Successful on 3 separate days.
- Successful in 2 different scenes.
- Successful at 7+ day interval.
- Produced with low support.

Maintenance does not mean deleted. Bring it back at longer intervals or when related scenes need it.

## Output Format

When designing review/transfer, output:

- Target id and canonical phrase
- Function
- Anchor scene
- Review mode
- Support level
- Transfer scene setup
- Expected response and accepted variants
- Scoring behavior
- Next scheduling rule
- Decay handling

## Quality Checklist

- Is the target a function/chunk, not just a whole dialogue?
- Does the scene cue the expected response clearly?
- Are variants accepted without losing the target?
- Does success change interval/support?
- Does failure recover rather than shame?
- Does transfer test real flexibility?
