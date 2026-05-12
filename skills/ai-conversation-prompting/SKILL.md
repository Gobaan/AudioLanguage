---
name: ai-conversation-prompting
description: Create strict AI conversation prompts for language-learning scene cards. Use when Codex designs, reviews, or implements prompts that ask an AI to judge learner audio/text in context, infer acceptable variants, produce in-character responses, avoid tangents, map utterances to communicative intent, or return structured feedback for guided roleplay.
---

# AI Conversation Prompting

## Purpose

Use this skill to prompt an AI conversation judge or roleplay partner for a specific language-learning scene.

The AI should not freely decide the lesson. The curriculum defines the goal; the AI interprets messy learner speech and judges whether it satisfies that goal.

Core shape:

```text
learner audio/text + scene contract + target intention -> structured judgement + in-world response
```

## Prompt Contract

Every AI prompt should include a scene contract with:

- language being practiced
- learner role
- partner/world role
- physical scene
- current turn
- target function
- plain-English intent definition
- required semantic slots
- optional semantic slots
- wrong or off-target intents
- allowed feedback style
- output schema

Do not rely on compact intent ids alone. Intent ids are for the app; the AI needs definitions.

For runtime, avoid repeating long prose in every request. Prefer reusable compact contracts:

- A stable system/developer instruction that defines the judge behavior once.
- A reusable function catalog keyed by intent id.
- A small per-scene contract containing only the current scene, target slots, and turn.
- A strict output schema that always includes learning-engine signals.

Bad:

```json
{
  "target_function": "ask_location"
}
```

Good:

```json
{
  "target_function": {
    "id": "ask_location",
    "definition": "The learner asks where a specific place or object is."
  },
  "learner_intention": "Ask where the hospital is.",
  "required_slots": {
    "request_type": "location",
    "place": "hospital"
  },
  "optional_slots": {
    "politeness": true
  },
  "wrong_intents": [
    {
      "id": "greet_only",
      "definition": "The learner only greets the partner without asking for the needed information."
    },
    {
      "id": "ask_price",
      "definition": "The learner asks how much something costs."
    }
  ]
}
```

## Division of Responsibility

Curriculum owns:

- what the learner is practicing
- the scene
- the required meaning
- accepted semantic range
- progression and review scheduling

AI owns:

- interpreting learner speech or text
- recognizing flexible surface forms
- deciding whether the meaning fits the current scene
- giving one brief repair hint when needed
- producing the partner's next in-world response
- returning learning signals the scheduler can use

The AI may infer phrasing variants. It should not infer the target lesson from the scene alone.

## Prompt Reuse Strategy

Use two prompt sizes.

**Authoring/debug prompt**

Use when designing a new card, testing in the browser, or diagnosing bad behavior. It can include full definitions, examples, anti-tangent rules, and human-readable explanations.

**Runtime prompt**

Use in the app. It should be compact and data-driven:

```json
{
  "task": "judge_guided_scene_attempt",
  "scene": {
    "id": "study-room-friend",
    "learner_role": "person being greeted",
    "partner_role": "friendly acquaintance",
    "turn": "learner_response_to_greeting"
  },
  "target": {
    "function_id": "respond_to_greeting",
    "definition": "Respond appropriately when someone says hi or hello.",
    "required_slots": { "speech_act": "greeting_response" },
    "optional_slots": { "ask_wellbeing": true }
  },
  "attempt": {
    "heard_as": "hey how are you",
    "support_level": 3,
    "attempt_number": 1,
    "latency_ms": 2400
  }
}
```

Do not send a giant list of all possible functions on every request. Send only:

- the target function
- 2-4 likely confusable functions when useful
- accepted examples only when a slot is ambiguous

If a provider supports prompt caching, keep the stable judge instructions and common schema identical across calls so repeated tokens can be cached.

## Required Slots Over Phrase Lists

Prefer semantic slots over exhaustive accepted responses.

Use phrase examples only as helpers, not as the complete answer key.

Example:

```json
{
  "learner_intention": "Order one mango politely.",
  "required_slots": {
    "speech_act": "request",
    "quantity": "one",
    "item": "mango"
  },
  "optional_slots": {
    "politeness_marker": true
  },
  "example_valid_responses": [
    "One mango, please.",
    "Can I have one mango?",
    "I would like a mango."
  ]
}
```

This lets the AI accept natural variants without accepting unrelated market-scene utterances such as asking the price or asking where apples are.

## Structured Output

Ask for structured output only. Keep the schema small enough to validate.

Recommended schema:

```json
{
  "heard_as": "string",
  "language_detected": "string or null",
  "intent_match": "exact | close | off_target | unclear",
  "fits_scene": true,
  "required_slots_present": ["string"],
  "missing_slots": ["string"],
  "extra_intent": "string or null",
  "support_used": "string",
  "response_latency_ms": 0,
  "confidence": 0.0,
  "learner_feedback": "string",
  "partner_response": "string",
  "next_action": "continue | retry | show_hint"
}
```

Rules:

- `partner_response` must stay in character.
- `partner_response` must be short.
- `learner_feedback` must be in the user's support language unless the app requests otherwise.
- Do not introduce a new lesson target inside feedback.
- Do not translate the full target line unless the UI explicitly asks for rescue help.

## Learning Engine Signals

Every runtime judgement should return enough information for deterministic progress updates.

The model should report:

- `intent_match`: exact, close, off_target, or unclear
- `fits_scene`: whether the utterance accomplishes the current scene goal
- `required_slots_present`: which required meaning slots were heard
- `missing_slots`: which required meaning slots were absent
- `extra_intent`: a valid but wrong communicative act, if present
- `support_used`: the support mode the app supplied
- `response_latency_ms`: copied from the app if available
- `confidence`: model confidence, not user score
- `next_action`: continue, retry, or show_hint

The AI should not decide spaced repetition intervals. It supplies evidence; the learning engine updates state.

Example scheduler interpretation:

```text
exact/close + fits_scene + low support -> increase interval
exact/close in transfer scene -> mark transfer progress
off_target -> keep target due soon and contrast the intent
unclear -> retry with more support
correct but slow -> keep active for fluency practice
long break + miss -> rebuild interval from today's result
```

## Anti-Tangent Rules

Include explicit boundaries:

- Judge only the current learner turn.
- Do not continue into unrelated conversation.
- Do not teach grammar unless requested by the app.
- Do not add new vocabulary targets.
- Do not accept an utterance just because it fits the broad setting.
- If the learner says something valid but not the target intention, mark `off_target` and briefly name the mismatch.

Example:

```text
If the learner says a valid sentence that does not satisfy the required slots, do not pass it.
Return intent_match="off_target" and explain the missing goal in one sentence.
```

## Prompt Template

Use this authoring/debug structure:

```text
You are a language-learning conversation judge for one guided scene.
Your job is to decide whether the learner's attempt satisfies the scene's target intention.
Do not invent a new lesson, change the scene, or continue a free conversation.

Scene contract:
{SCENE_CONTRACT_JSON}

Learner attempt:
{AUDIO_OR_TRANSCRIPT}

Return only JSON matching this schema:
{OUTPUT_SCHEMA_JSON}
```

Use this compact runtime structure:

```text
Judge one guided language-learning turn. The curriculum defines the target; do not change it.
Return only schema-valid JSON. Do not teach grammar or continue free chat.

{COMPACT_SCENE_CONTRACT_JSON}
```

The compact contract should still include plain-English definitions for any intent ids used in that request.

## Quality Checks

Before using a prompt, check:

- Could the AI understand every intent id from definitions, not memory?
- Are required slots concrete enough to reject wrong-but-plausible utterances?
- Can the AI accept natural variants without a huge phrase list?
- Is the current scene specific enough to ground the partner response?
- Does the output schema prevent rambling?
- Is feedback supportive without turning into translation-first teaching?
- Does the runtime prompt avoid repeated long text while preserving definitions?
- Does the output include scheduler-ready learning signals?

If any answer is no, fix the scene contract before changing model settings.
