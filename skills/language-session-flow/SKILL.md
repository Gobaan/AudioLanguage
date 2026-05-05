---
name: language-session-flow
description: "Design adaptive daily language-learning session flow. Use when Codex needs to plan what a user experiences in a session, balance review/new/transfer work, handle long breaks, measure journey progress, choose whether to add new content, and keep sessions short, motivating, and capability-building."
---

# Language Session Flow

## Purpose

Use this skill to design the user's daily language-learning experience. A session should feel like a short successful interaction, not a pile of cards.

## Core Rule

Every session should end with a real communicative success.

The app should adapt to review load, memory decay, user confidence, and current capability before adding new content.

## Session Mix

Default session distribution:

```text
60% due review
25% new or extended content
15% transfer or playful challenge
```

For beginners:

```text
Minimum habit: 10 minutes/day
Good session: 20-30 minutes/day
Active speaking: 3-6 minutes/day
```

Do not force long free conversation early. Use short successful exchanges.

## Normal Daily Flow

Use this order:

1. Warm return: one easy familiar scene.
2. Due review: targets scheduled today.
3. Transfer check: one practiced target in a new scene.
4. New or extension: only if review performance is healthy.
5. Success close: a short line the learner can produce.

Avoid starting with the hardest overdue item. Confidence matters.

## Long-Break Flow

After a long break, run recalibration.

1. Start with familiar anchors.
2. Test recognition or visual-only production.
3. Increase support if rusty.
4. Pause new content unless performance is strong.
5. Rebuild intervals based on today, not guilt.

The user experience should feel like:

```text
Welcome back. Let's warm up with something familiar.
```

Not:

```text
You missed 37 reviews.
```

## Add New Content Rule

Add new content only when:

- Due review load is manageable.
- Recent success rate is healthy.
- Current target has at least one low-support success.
- User is not returning rusty after a long break.

If review load is high, deepen confidence instead of adding more.

## Journey Measurement

Track capability, not only completion.

Dimensions:

- **Coverage**: functions/chunks introduced.
- **Control**: support level needed.
- **Retention**: longest interval successfully remembered.
- **Transfer**: success in new contexts.
- **Fluency**: response latency and attempts.
- **Repair**: ability to ask for repetition/help.
- **Maintenance**: remembered after breaks.

User-facing states:

```text
Introduced
Can repeat
Can say with scene
Can use in new scene
Remembered after a break
Maintained
```

## Session Decision Rules

If the user succeeds:

- Increase interval.
- Reduce support.
- Consider a transfer.
- Consider extension only if stable.

If the user struggles:

- Add support.
- Return to anchor.
- Shorten interval.
- Do not add new dialogue that session.

If the user gives a valid but off-target response:

- Mark communicative intent as good.
- Keep canonical target due for more practice.
- Explain the target softly.

## Avoiding Bloat

Do not let one main dialogue grow forever.

When a scene reaches 4-6 turns, consider freezing it. When it wants to teach a second function, create a sibling scene.

The session can revisit familiar characters and settings, but each practice unit needs one learning job.

## First Session Shape

A strong first session:

1. See/hear one vivid anchor scene.
2. Echo the learner line.
3. Produce from the same visual.
4. Hear success response.
5. Try one tiny transfer or preview.
6. End with a line they can say.

The first session should prove: "I can use a real phrase in a real-feeling moment."

## Output Format

When designing a session flow, output:

- User state assumption
- Session goal
- Review/new/transfer mix
- Ordered activity list
- Support levels used
- What gets scheduled next
- What metrics update
- Long-break behavior if relevant
- Failure/recovery behavior

## Quality Checklist

- Does the session start with achievable context?
- Does it prioritize due memory before new content?
- Does it include production, not just recognition?
- Does it end with success?
- Does it avoid overloading the user after a break?
- Does it measure capability and transfer?
- Does it avoid endless anchor growth?
