---
name: learning-engine-flow
description: Design and revise the language-learning engine, card progression, support reveal policy, adaptive difficulty, beginner scaffolding, spaced review, and session sequencing. Use when Codex needs to decide what cards a learner sees, when to add or remove support such as romanization, how to handle failure/retry/skip, how to order beginner chunks versus longer survival phrases, or how the app should guide growth over time.
---

# Learning Engine Flow

## Core Principle

Make the learner retrieve first, then rescue quickly.

The first attempt should exercise audio-context memory. Support should appear after struggle, not before, unless the target is known to be too long for the learner's current level.

## Beginner Progression

Start with tiny fixed chunks before longer survival lines.

Good first targets:

- Greetings: `konnichiwa`, `hi`, `vanakkam`
- Identity: `Anna desu`, `my name is Anna`
- Repair: `wakarimasen`, `I don't understand`
- Politeness: `sumimasen`, `arigatou`, `please`, `thank you`

Delay longer lines until the learner has small wins:

- Start: `Sandoicchi kudasai`
- Later: `Sandoicchi o hitotsu onegaishimasu`
- Start: `Byouin?` or `Byouin wa doko?` when culturally acceptable
- Later: `Byouin wa doko desu ka?`

## Support Reveal Policy

Use support in this order:

1. Full scene audio and visual context.
2. Cue replay.
3. Learner tries from memory/context.
4. On failure, reveal recovery tools:
   - play target line at full speed
   - play target line slowly
   - show romanized pronunciation
   - allow retry
   - allow skip/continue for debugging or frustration recovery

Do not show romanized text before the first attempt for normal beginner cards. It can train reading-to-speech instead of scene-to-speech.

## Anchor vs Transfer vs Review

Different card types should treat the correct learner line differently.

### Anchor / First Exposure

Goal: build the visual-context-to-sound memory.

For short MVP phrases, use the fast prompted-shadowing anchor flow:

1. Play the full mini-dialogue: partner cue, correct learner line, partner response.
1. Play the partner cue.
2. Play the correct learner line once.
3. Record the learner attempt immediately after the correct learner line.
4. Play the partner response to close the social loop.
5. Send the recording for background judgement and later scorecard feedback.

Do not play the full dialogue twice passively. For the MVP's short chunks, do not force a cue replay before the attempt; transfer/review cards are where recall from cue alone gets tested.

For longer or confusing anchors, the engine may use a more scaffolded flow:

1. Full mini-dialogue.
2. Cue replay.
3. Learner attempt.
4. Correct learner line as comparison.
5. Partner response.

Card playback should be controlled by the card/template JSON. The visual card component should be a generic runner that executes declarative steps such as `play_line`, `record_attempt`, `play_response`, `show_support`, and `submit_for_scorecard`.

### Same-Day Transfer

Goal: see whether the learner can use the same communicative function in a slightly different scene.

Flow:

1. Show a near-transfer scene with the same intent and different surface details.
2. Play only the partner cue.
3. Record the learner attempt.
4. In easy mode, play the correct learner line after recording, then the partner response.
5. In test mode, delay the correct learner line until failure, scorecard, or explicit help.

Use easy mode when the phrase is new or confidence is fragile. Use test mode when measuring recall matters more than momentum.

### Delayed Review

Goal: measure memory after decay.

Flow:

1. Show a review or far-transfer scene after a delay, usually next day for MVP.
2. Play the partner cue without replaying the learner answer first.
3. Record the learner attempt.
4. Do not reveal the correct line until after the attempt is captured.
5. Use background judgement to update scheduling and the session scorecard.
6. Reveal support if the learner misses, asks for help, or the scorecard marks the phrase weak.

For the MVP, test immediate transfer and next-day review before building 3-day and 7-day retention schedules.

## AI Judgement Timing

Do not block every beginner card on live AI judgement.

Anchor cards should record and continue immediately. AI can judge recordings in the background and produce an end-of-session scorecard. This preserves learning rhythm and avoids turning every card into a slow test.

Use live or near-live AI judgement mainly for transfer and review cards, and always provide a timeout or continue path. The learning engine should treat AI output as coaching and scheduling evidence, not as a hard gate that can trap the user.

## Long Phrase Rule

If a learner line has more than 3-4 romanized words or more than about 8 syllable beats, either:

- split it into a smaller first card, or
- mark the card as a stretch and reveal romanized rescue after the first miss.

Long survival phrases should be built by extension:

```text
food name -> food + please -> food + one + please -> full polite sentence
```

## Failure Behavior

Failure is information, not a stop sign.

After one miss:

- keep the learner on the same visual frame
- show concise feedback
- reveal full-speed and slow target audio
- reveal romanized pronunciation
- keep `Try` available
- allow `Continue` so a brittle card cannot block a session

For local development, always allow `Skip`, including during autoplay.

## Session Ordering

Beginner first session:

1. Warm greeting.
2. Identity line.
3. One repair phrase.
4. One politeness phrase.
5. One practical request using the shortest natural form.

Do not put multiple long survival phrases in the first session. The session should end with the user feeling, "I can say real things," not "I failed a pronunciation exam."

## Card Redesign Checklist

Before adding a card to a beginner session, check:

- Is the learner line short enough to hold from audio?
- Is the scene meaning visible without translation?
- Is there only one new speech job?
- Does the card have audio at full and slow playback?
- Does romanized rescue appear only after failure?
- Can the user skip or continue if the card gets stuck?
- Does the card lead to a future longer phrase by extension?
- Is this card an anchor, transfer, or delayed review, and does its reveal policy match that role?
- Does AI judgement happen in the background unless recall testing truly needs immediate feedback?
