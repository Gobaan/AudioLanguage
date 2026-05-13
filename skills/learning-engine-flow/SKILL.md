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
