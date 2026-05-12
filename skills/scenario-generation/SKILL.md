---
kay 
name: scenario-generation
description: Generate language-learning scenarios, scene cards, and short dialogues that are emotionally engaging, culturally grounded, audio-first, and sequenced for i+1 progression. Use when Codex needs to create new scenes, write alternating speaker dialogue, decide whether to deepen one scene or create varied transfer scenes, design visual scene prompts, tag vocabulary, or turn weak vocabulary into contextual practice.
---

# Scenario Generation

## Core Principle

Make the situation the unit of learning. A scenario is not a vocabulary container; it is a small human moment where the target language would naturally be used.

Each scenario should combine:

- A vivid visual setup
- Two speakers with clear roles
- A small emotional or practical stake
- A short alternating dialogue
- Mostly known language with one meaningful stretch
- A retrieval path that changes over time

## Scene Shape

Start with a concrete situation:

- **Place**: where the exchange happens
- **People**: who is speaking and what they want
- **Tension**: what makes the exchange matter
- **Gesture/action**: what the learner can infer visually
- **Target function**: what communicative job the learner practices
- **Target language**: phrases or slots being introduced

Good scenes feel like something interrupted from real life: buying water on a hot day, greeting a neighbor while carrying groceries, asking a bus driver before the bus leaves, telling a doctor where it hurts, thanking someone who helped.

Avoid scenes that exist only to demonstrate a word.

## Dialogue Flow

Use short turn-taking. Dialogue should alternate between speakers unless there is a clear natural reason for one speaker to continue.

Basic pattern:

1. Speaker A opens with a natural cue or need.
2. Speaker B responds directly.
3. Speaker A adds a small complication, preference, clarification, or emotional color.
4. Speaker B resolves, confirms, refuses, asks back, or offers the next step.

For first exposure, use 2-4 turns. For deeper versions, grow toward 6-8 turns. Keep each line short enough to remember as a chunk.

Use speaker roles consistently:

- **Learner role**: the person the user is likely to speak as.
- **World role**: shopkeeper, neighbor, driver, relative, doctor, classmate, official.
- **Pressure role**: someone impatient, kind, confused, busy, warm, worried, playful, or formal.

Do not make both speakers emotionally flat. One speaker should carry a recognizable human attitude.

## Emotional Engagement

Give the scene a small reason to matter. The emotion can be mild; it does not need drama.

Useful stakes:

- Relief: the learner gets help.
- Urgency: the bus is leaving, the shop is closing, someone is waiting.
- Belonging: someone recognizes or welcomes the learner.
- Care: family, health, food, tiredness, home, weather.
- Pride: the learner manages something alone.
- Friction: price is too high, directions are unclear, the speaker talks too fast.
- Warmth: a recurring character remembers the learner.

Prefer ordinary emotional truth over plot. A short scene with a friendly aunt who remembers what the learner likes is stronger than a generic "restaurant dialogue."

## One Scene Growing vs Many Varied Scenes

Use both, but for different jobs.

### Deepen Anchor Scenes

Return to a strong scene over time when the goal is chunking, confidence, and progressive i+1 growth. Keep the image, people, and situation stable while adding one new sentence, slot, or complication.

Example progression:

1. "How much?"
2. "How much? Too expensive."
3. "How much? Too expensive. I will take this one."
4. "Can you make it cheaper? I only have cash."

Anchor scenes reduce grind because the learner already understands the world of the exchange.

### Add Varied Transfer Scenes

Create new scenes when the goal is transfer. The learner must use the same word, phrase, or structure in a different situation so it is not tied to one image or card.

Example transfer:

- "I want water" at a shop
- "I want to go home" near a bus stop
- "I want this one" at a market
- "I want to see a doctor" at a clinic

Transfer scenes reveal whether the learner acquired the pattern or only memorized the card.

### Rule of Thumb

For a new concept, use one vivid anchor scene first. Then add 2-3 transfer scenes over later reviews. Do not create endless near-duplicate scenes; vary place, speaker attitude, and communicative pressure.

## i+1 Sequencing

Each new scenario should be mostly comprehensible. Add one meaningful stretch at a time:

- New word inside known phrase
- Known word in new slot
- Familiar scene with one new complication
- Same function with a different speaker attitude
- Same phrase at faster speed or with less support

If a scene needs too many new words to make sense, split it into smaller scenes or add visual support.

## Retrieval Over Time

Do not replay the exact same card forever. Keep the scenario anchor stable while rotating the task.

Useful review modes:

- Hear the dialogue and identify the target phrase.
- See the image and produce the learner's line.
- Hear only the response and infer what was asked.
- Fill in one missing word.
- Choose the best response under time pressure.
- Repair a misunderstanding.
- Reuse the phrase in a transfer scene.
- Continue the dialogue freely with a chatbot.

The repeated scene gives memory an anchor; the changing challenge prevents pattern matching.

## Default Speaking Card Template

When creating a new beginner speaking card for this project, use `guided-speaking-scene-v1` from `data/curriculum/card_templates.json` unless the user explicitly asks for a different card type.

Default card structure:

1. **They say** prompt audio plays while frame 0 is visible.
2. The scene partner's cue line plays while frame 0 remains visible.
3. **You say** prompt audio plays while switching to frame 1.
4. The learner model line plays while frame 1 remains visible.
5. **Now you try** prompt audio plays while frame 1 remains visible.
6. The app records the learner and verifies against both target script and transliteration.
7. On failure, show heard pronunciation, expected pronunciation, and a Try Again button.

Required dialogue line shape:

- Line 0: `world_opener`, scene partner, visible cue, `frame-0.png`
- Line 1: `learner_target`, learner, target production line, `frame-1.png`
- Line 2: optional `world_response`, scene partner, natural confirmation, `frame-2.png`

Frame rules:

- Every spoken line should have a matching frame.
- Frame 0 should make the partner's cue visually obvious.
- Frame 1 should show the learner-character ready to speak the target line.
- Keep frame 1 visible during "You say", learner model audio, "Now you try", mic recording, and retry.
- Do not include the final partner response in default practice playback. Use it later for full-dialogue review or post-success confirmation.

Text support rules:

- Do not show target text before the first attempt.
- Reveal target script only after success, manual reveal, or failed attempt feedback.
- Keep transliteration hidden by default.
- Use transliteration as corrective feedback after failure or behind an explicit pronunciation toggle.

## Visual Setup

The image should explain why the dialogue is happening.

Include:

- Setting details that establish the culture and place
- Body language and gaze direction
- Relevant objects
- Speaker positions that make turn-taking legible
- A hint of the problem or desire

Use consistent visual style and recurring characters where possible. Recurring people create continuity without requiring a full story.

Avoid generic, culturally vague, or over-polished stock-like scenes. If cultural accuracy matters, flag the scene for human review.

## Video Scene Prompts

When generating a short video for a dialogue scene, prompt for a small observable moment, not a trailer. The video should make the social situation, speaker roles, and emotional stake legible before the learner understands the words.

Keep video prompts short and concrete:

- 5-8 seconds for first exposure
- One location
- Two visible speakers
- One clear action or exchange
- Natural body language
- Culturally specific setting details
- No subtitles, captions, labels, or text overlays
- No fast cuts, camera tricks, or dramatic zooms

Prompt structure:

1. **Setting**: where the scene happens and what culturally grounded details are visible.
2. **Characters**: who is present, their relationship, approximate age, and emotional tone.
3. **Action**: what happens during the clip, including gestures that support meaning.
4. **Camera**: stable medium shot or gentle handheld, with both speakers visible.
5. **Mood**: warm, urgent, awkward, relieved, playful, formal, or tired.
6. **Constraints**: no text, no subtitles, no logos, no surreal motion, no extra characters unless needed.

Example prompt:

```text
5-second realistic video, Colombo neighborhood corner shop in late afternoon, warm natural light. A young adult customer stands at the counter holding a small water bottle, slightly tired from the heat. A friendly middle-aged shopkeeper smiles and gestures toward the bottle, then the customer points to it and nods. Both speakers visible in a stable medium shot, natural conversational body language, culturally accurate Sri Lankan shop details, no subtitles, no text, no logos, no dramatic camera movement.
```

Use video to carry inference:

- Show the object being requested.
- Show urgency with movement, waiting, weather, or time pressure.
- Show warmth through recognition, smiles, or familiar body language.
- Show confusion through pauses, pointing, leaning closer, or repeated gestures.
- Show resolution at the end: nod, handoff, smile, direction pointed out, or visible relief.

For dialogue audio, the video does not need perfect lip sync at early stages. Prioritize emotional readability and situational clarity. If lip sync is required, keep lines extremely short and avoid shots where the mouth must be inspected closely.

Generate one reusable anchor video for a strong scene, then reuse still frames or short loops for later review variants. Create new videos for transfer scenes only when the new setting or emotional pressure changes the meaning enough to matter.

## Dialogue Writing Rules

Write target-language dialogue as full target language, not mixed-language sentences. English or the learner's base language can be used for situation prompts, hints, or optional post-attempt meaning, but not inserted mid-dialogue.

Keep lines natural:

- Use chunks people actually say.
- Prefer phrases over isolated words.
- Let grammar emerge through repeated slots.
- Include clarification and repair phrases early.
- Keep beginner lines short, but not robotic.
- Avoid textbook symmetry where every line exists only to ask and answer.

## Scenario Output Format

When generating a scenario, include:

- **Scenario id**: short kebab-case name
- **Level**: first exposure, review, transfer, or chatbot unlock
- **Purpose**: communicative function
- **Scene setup**: place, people, stakes, visual details
- **Image prompt**: concise prompt for a generated/static image
- **Video prompt**: concise prompt for a 5-8 second scene clip when video is useful
- **Known language**: assumed known words or chunks
- **New language**: one or two target chunks
- **Dialogue**: alternating speaker lines
- **Learner line**: the line the user should eventually produce
- **Review variants**: 2-4 retrieval challenges
- **Transfer links**: related scenes that reuse the same chunk
- **Cultural notes**: accuracy risks or review needs

## Quality Checks

Before finalizing a scenario, check:

- Does the scene make the meaning inferable without translation?
- Is there a small emotional or practical stake?
- Do speakers alternate naturally?
- Is the learner role obvious?
- Is there only one main new stretch?
- Could the same phrase later transfer to another scene?
- Does the image carry situational meaning, not just decoration?
- Would a short video make the roles, stakes, or gestures clearer?
- Would repeating this exact card cause pattern matching?
- Is the dialogue something a real person might say?
- Does the scene unlock or support a real conversation later?
