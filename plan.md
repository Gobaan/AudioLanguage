# App Development Plan

A staged approach where each stage ships working software that real people use.

## Stage 1: Core Scene Experience
**Goal:** Prove the scene card feels right — the whole product lives or dies on this

### How scenes work — the two-pass model

**First encounter with a scene:**

1. **Pass 1 — Pure exposure:** Hear the full exchange. Echo each line as you hear it. Low pressure, just getting the mouth around the sounds.
2. **Pass 2 — Forced anticipation:** Scene replays, situation text appears ("You enter a shop"), prompted to say your line *before* hearing it. Correct version plays. You compare.

A single new scene takes ~2-3 minutes. Slow, but the right slow.

**Across days (once SRS is added in Stage 2):**
- Day 1: both passes
- Day 3: Pass 2 only (retrieval review)
- Day 7: harder retrieval — hear only the other person's response, identify what *you* said to prompt it

The retrieval challenge escalates while the scene stays the same. Prevents pattern-matching the card.

### What to build
- 5-8 scenes for one language (Spanish or French), hand-crafted
- Simple generated/static images per scene
- Audio: high-quality TTS dialogues (ElevenLabs or similar), 2-4 turns per scene
- Forced production on every turn (no "hear again" skip)
- Post-attempt transcript (target language only, "show meaning" as escape hatch)
- Linear progression, no SRS yet
- Session summary: "You can now do X in [language]"

### Success signal
A friend uses it for 15 minutes and can actually say something in the language without looking at notes

### Why this first
If the scene card doesn't feel engaging, nothing else matters. Everything builds on this.

---

## Stage 2: Spaced Repetition + Content Depth
**Goal:** Turn a novelty into a habit

### What to build
- Expand to 40-50 scenes covering survival → basic conversation
- SRS engine with **varied retrieval challenges** per scene:
  - Identify the phrase (hear → pick)
  - Produce from image (see → say)
  - Reverse (hear response → identify prompt)
  - Fill-in (partial dialogue → complete)
- Track per-card: correct/incorrect, response latency
- Category-level tracking (food words hard, greetings easy)
- Session queue: mix of new scenes + reviews at due intervals
- Progress view: what's learned, what's due, what's weak

### Success signal
Someone comes back on day 3 without being nudged

---

## Stage 3: AI Chatbot Layer
**Goal:** Unlock the conversation layer — where real acquisition happens

### What to build
- Simple browser-based chatbot (text + audio)
- Scenarios gated by vocabulary exposure:
  - 20 words → greeting neighbor
  - 50 words → market transaction
  - 100 words → asking directions
- Small model (Haiku / GPT-4o-mini) with tight roleplay prompt
- System prompt includes known vocabulary so bot stays in range
- Voice input → STT → LLM → TTS response loop
- Hints available when stuck ("try saying X")
- No social fear, accepts approximate answers

### Success signal
Someone has a 5-minute conversation and doesn't feel like they're being tested

---

## Stage 4: Two-Layer Feedback Loop
**Goal:** Make the app learn the user, not just schedule cards

### What to build
- Response latency becomes the honesty signal (1s correct ≠ 8s correct)
- Confusion pair detection (words mixed up repeatedly → forced comparison)
- Receptive vs productive gap tracking
- Scene transfer test: same word in different scene, does it stick?
- Chatbot struggles feed back → prioritized review cards
- Weak areas auto-queue into next session
- Self-report calibration: if user says "easy" but fails, discount future self-ratings

### Success signal
The app surfaces a weakness the user didn't know they had, and fixing it feels like a win

---

## Stage 5: Content Pipeline + Scale
**Goal:** Make adding languages and scenes cheap

### What to build
- Scene generation pipeline:
  - Image generation (one-time per scene, shared across languages)
  - Audio generation per language (TTS dialogue)
  - Metadata: vocabulary tags, difficulty, i+1 sequencing
- Multi-language support (Sinhala, Tamil, Russian, etc.)
- Prompt caching for chatbot (biggest cost lever)
- Admin tool: create/edit scenes, preview, publish
- Culture-specific image prompts per language

### Success signal
Adding a new language costs hours, not weeks

---

## Stage 6: Maintenance + Long-Term Engagement
**Goal:** The app becomes a practice partner, not a teacher

### What to build
- Deep vocabulary maintenance (30+ day retention threshold)
- Complex chatbot scenarios (job interview, phone call, bureaucracy)
- Natural-speed conversations, no patient repetition
- User-flagged unknown words → auto-generate new scenes
- "You struggled with X this week" weekly summary
- Social features if valuable (not gamification-for-retention)

---

## Validation Table

| Stage | Hypothesis |
|---|---|
| 1 | Situational echo works better than flashcards |
| 2 | Varied SRS + scene depth creates a habit |
| 3 | Parallel chatbot layer is engaging from low vocabulary |
| 4 | Two-layer feedback loop actually targets weak points |
| 5 | Content pipeline makes scale economically viable |
| 6 | App transitions from teacher to practice partner |
