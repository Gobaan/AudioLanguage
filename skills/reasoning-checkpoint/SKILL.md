---
name: reasoning-checkpoint
description: Stress-test project reasoning, MVP assumptions, validation plans, learning-science claims, retention tests, or whether an AudioLanguage idea is already validated by existing tools. Use when the user asks if their reasoning makes sense, whether this MVP is testing anything, what critical assumptions are being tested, whether to give it to friends, whether a learning mechanic is worth the time cost, or whether evidence from products like Duolingo, Pimsleur, Anki, or similar tools already validates the premise.
---

# Reasoning Checkpoint

Use this skill to be critically helpful, not reassuring by default. Separate what is already known from what this project still needs to prove.

## Default Stance

- Be direct, reasonable, and practical.
- Name the actual assumption being tested.
- Distinguish learning-science validation from product/business validation.
- Prefer a smaller, cleaner experiment over a feature-heavy MVP.
- Avoid treating positive usability feedback as proof of learning or retention.
- Push for observable behavior: completion, recall, recordings, return rate, and follow-up usage.

## Lean Startup Check

When evaluating an MVP, answer these questions:

1. What critical assumption is this testing?
2. What user behavior would confirm or falsify it?
3. Is this the cheapest test of that assumption?
4. Is the signal contaminated by UI confusion, novelty, hints, or short-term memory?
5. Has the generic principle already been validated elsewhere?
6. What is unique enough here that still needs validation?

If the answer is vague, reframe the MVP around a sharper assumption.

## Learning Product Heuristics

Treat these as already partly validated by existing tools:

- Spaced retrieval helps retention.
- Audio-first recall can work, as shown by Pimsleur-like systems.
- Bite-sized practice and habit loops can work, as shown by Duolingo-like systems.
- Flashcard-style spaced repetition can work, as shown by Anki-like systems.

Do not use AudioLanguage to prove only those generic ideas again.

Look for the project's unique wedge instead, such as:

- Can generated scene-based lessons feel natural enough for beginners?
- Can comic/visual context plus audio make meaning clear without translation-first instruction?
- Can the system produce measurable spoken recall without a human tutor?
- Can generated transfer or delayed-review scenes test usable language rather than rote repetition?
- Will users return for a second session without being personally reminded?

## Scene-Based Language MVP Notes

For AudioLanguage, treat the current MVP as a usability plus delayed-recall smoke test, not proof that the whole method works.

Valuable things to test:

- Can a beginner finish a session without handholding?
- Do they understand when to listen, choose, speak, and continue?
- Does the scene make the intended meaning guessable?
- Can they produce the phrase later from a cue?
- Are recordings and scorecards good enough to tell what happened?
- Would they voluntarily do a second short session?

Weak or contaminated signals:

- Immediate repetition after hearing a phrase.
- Multiple-choice recognition in English.
- Same-session success while the answer is still warm.
- Users saying they liked it without returning later.

## Multiple Choice Guidance

Treat multiple choice mostly as a diagnostic scaffold in early MVPs.

It helps debug:

- Scene comprehensibility.
- Distractor quality.
- Whether the user understands what the app wants.
- Whether visuals/audio are enough to infer intent.

It is a weaker learning signal because recognition is much easier than recall. In mature flows, remove it from review and delayed recall unless users are confused. Keep it for first exposure or as a fallback after failed production to distinguish scene confusion from speaking failure.

## Transfer And Delayed Recall Guidance

Same-day transfer can help, but be skeptical of its value per minute.

It tests near transfer:

- Can the user use the phrase when the surface scene changes?
- Did they learn the phrase as a usable function rather than one comic panel?
- Is the phrase function clear across contexts?

But same-day transfer is weaker than next-day or multi-day recall because the phrase is still in short-term memory.

Prefer this priority when user time is scarce:

1. Anchor exposure.
2. Immediate production.
3. Next-day recall.
4. Multi-day recall.
5. Same-day transfer only for ambiguous or high-value phrases.

If same-day transfer is kept, make it short: new visual cue, user responds, model answer plays. Avoid turning it into a second full lesson.

## Suggested Friend Test

Recommend giving an MVP to friends only when the question is specific.

A clean early test:

- Day 1: five anchor scenes.
- Day 2: five delayed recall scenes.
- Day 4 or 7: repeat delayed recall, optionally with transfer visuals.

Useful success metrics:

- 80%+ complete without explanation.
- 60%+ delayed spoken responses are understandable.
- Users can explain what the scene asked them to do.
- Some users return for day 2 without heavy prompting.

If those fail, test simpler UI, clearer scenes, better phrase choice, or shorter sessions before adding more AI or more languages.

## Response Shape

When using this skill, keep the answer crisp:

- Start with the verdict.
- State what is actually being tested.
- State what is not being tested.
- Say whether existing tools already validate the generic premise.
- Recommend the next sharper experiment.
