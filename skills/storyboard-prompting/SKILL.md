---
name: storyboard-prompting
description: "Create AI image or video prompts for language-learning dialogue scenes, especially three-beat video storyboards that make context, speaker turns, gestures, gaze, and word meaning visually inferable. Use when Codex needs to turn dialogues, scene cards, vocabulary, or learner lines into storyboard prompts for generated videos, multi-frame visuals, image sequences, Sora-style clips, or other AI visual generation assets."
---

# Storyboard Prompting

## Purpose

Use this skill to turn a short dialogue into visual prompts that help a learner understand the situation before they understand every word.

Prefer a three-beat video arc over a static three-frame storyboard when the learning value depends on motion, gesture, gaze, turn-taking, or emotional shift.

Still-image prompts are still required for most workflows. Use stills as the controllable source of truth for character, setting, and composition, then animate them later with image-to-video when desired.

## Core Principle

Make meaning visible.

Every storyboard should show:

- Who is speaking.
- Who is being addressed.
- What the speaker wants or feels.
- Which gesture, object, or movement supports the target words.
- How the other person reacts.
- Why the learner's line is socially appropriate.

Do not make generic decorative scenes. The visual should teach context.

## Three-Beat Video Arc

Use three short video prompts for a first-exposure dialogue:

1. **Setup / Cue**: establish place, roles, and why the first line happens.
2. **Learner Turn / Meaning Gesture**: show the learner response with gestures that map to important words.
3. **Response / Resolution**: switch to the responder and show the social result.

Each beat should be 3-6 seconds. Together they should feel like one continuous micro-scene, not three unrelated clips.

## Audio-To-Visual Beat Mapping

Every storyboard beat must explicitly map the visual to the audio it supports.

For each beat, include:

- **Dialogue line**: the spoken line and speaker.
- **Audio file**: the generated audio file expected to play with the beat, such as `audio/<scene-id>-0.mp3`.
- **Timing role**: when the app should show this beat, such as "play while line 0 audio plays" or "show while waiting for the learner response."
- **Meaning target**: the word, chunk, or communicative function the visual should make inferable.
- **Visual mapping**: the gesture/object/gaze/reaction that carries each target meaning.

Example:

```markdown
Dialogue line: Learner says, "Hello! How are you?"

Audio file: `audio/ta-greeting-hello-1.mp3`

Timing role: Play this visual while line 1 audio plays; reuse it as the listening visual when prompting the learner to produce the same line.

Meaning target: "Hello! How are you?"

Visual mapping:

- Wave = "Hello"
- Open hand toward the friend = "you"
- Raised eyebrows and slight forward lean = friendly question / "How are you?"
```

The prompt text itself should also include the important visual mappings, because many generation tools will only see the prompt file, not the surrounding storyboard notes.

## Still-Image Prompt Anatomy

For every beat, create a still-image prompt as well as a video prompt.

A still-image prompt should include:

- Composition: what is visible in one frame.
- Speaker focus: whose turn or cue the image supports.
- Gesture pose: the frozen gesture that carries meaning.
- Context objects: desk, notebook, water bottle, market stall, bus sign, phone, etc.
- Continuity: same people, setting, clothing, lighting, and visual style across frames.
- Constraints: no subtitles, no dialogue text, no translations, no logos.

Still prompts should be slightly more explicit about composition than video prompts because there is no motion to clarify the action.

Suggested still workflow:

1. Generate `frame-0.png`, `frame-1.png`, and `frame-2.png`.
2. Use those images directly in the app with pan/zoom/crossfade.
3. Later use each still as the input/reference for image-to-video generation.

## Video Prompt Anatomy

Each video prompt should include:

- Setting: concrete place and time.
- Characters: relationship, rough age, posture, emotional tone.
- Action: observable movement during the line.
- Gesture mapping: gestures that clarify word meaning.
- Audio role: what dialogue line or learner response this visual supports.
- Camera: speaker-focused but context-aware shot.
- Continuity: same people, location, lighting, clothing, and props across beats.
- Constraints: no subtitles, no captions, no text overlays, no logos, no surreal motion.

Keep prompts concise enough for generation, but specific enough to preserve the learning context.

## Gesture Mapping

Gestures should clarify meaning without becoming pantomime.

Useful mappings:

- Greeting words: wave, open hand, smile, eye contact.
- "I/me": speaker lightly touches chest or gestures toward self.
- "You": speaker gestures gently toward the other person with an open hand, not an aggressive point.
- Asking a question: head tilt, raised eyebrows, palm-up gesture, slight lean forward.
- Thanks: nod, softened face, hand to chest, small smile.
- Directions: point toward the route, trace path with hand, look in the direction.
- Want/request: point to object, hold object, glance between person and object.
- Price/quantity: show item, count on fingers, hold money or phone.
- Not understanding: pause, puzzled expression, lean closer, small shake of head.
- Apology: lowered shoulders, concerned face, hand slightly raised.

Use one or two clear gestures per beat. Too many gestures distract from the dialogue.

## Camera Rules

Use camera changes to support turn-taking:

- Setup beat: medium shot with both characters and the place visible.
- Learner beat: medium close-up or over-the-shoulder on the learner, with the other person still present enough to show who is addressed.
- Response beat: switch to the responder's face and hands, showing reaction and resolution.

Avoid fast cuts, dramatic zooms, spinning camera, or shots where mouths must be inspected. Early learning clips do not require perfect lip sync; they require clear social meaning.

## Continuity Rules

Across the three beats, keep:

- Same characters.
- Same clothes.
- Same room or location.
- Same lighting and time of day.
- Same key props.
- Same visual style.

If the AI generation model struggles with continuity, restate the continuity constraints in every beat.

## Language-Learning Constraints

Do not include written dialogue in the image or video. No captions, subtitles, UI text, floating vocabulary, or translated word labels.

The visuals should support listening by showing:

- Who speaks first.
- When the learner should respond.
- What the learner's line accomplishes.
- How the other person reacts.

Do not overload the visual with every word. Highlight the words that carry the communicative function.

## Proper Noun Labels

Allow small identity labels for names and proper nouns when they prevent the learner from treating a name as the main target word.

Good use:

- A subtle name tag, desk label, contact card, or small lower-third style label that identifies a person as "Ana."
- A shop sign or map label when the proper noun is a place name and context depends on recognizing it.
- A contact list or invitation card when the dialogue naturally involves a named person.

Rules:

- Label only proper nouns or identity/context anchors.
- Do not label ordinary vocabulary, grammar, translations, or full dialogue.
- Keep labels visually secondary and non-distracting.
- Use the same spelling as the audio/script.
- Prefer diegetic labels that belong in the scene, such as a name tag, notebook cover, phone contact, desk placard, or sign.
- If the name is not important to the learning goal, make the label even subtler or omit it.

Example:

If the line is "Hello, Ana," the storyboard may show a small name tag reading "Ana" on the responder. This tells the learner that Ana is a person's name, while the wave, gaze, and tone carry the meaning of "hello."

## Example: Hello, How Are You?

Dialogue:

1. Friend: "Hello!"
2. Learner: "Hello! How are you?"
3. Friend: "Fine. Thank you."

Three-beat video storyboard:

### Beat 1: Setup / Cue

Dialogue line: Friend says, "Hello!"

Audio file: `audio/ta-greeting-hello-0.mp3`

Timing role: Play this visual while line 0 audio plays.

Meaning target: "Hello"

Visual mapping:

- Wave = greeting / "Hello"
- Friend's gaze toward learner = the learner is being addressed
- Learner looking up = the learner's turn is coming

Still-image prompt:

Realistic still image, cozy home study room in warm indoor light. A learner sits at a small desk with an open notebook, pencil, and headphones nearby. A friend has just entered through an open doorway and is smiling while raising one hand in a friendly wave. The learner is looking up from the notebook, surprised but happy. Both characters visible in a stable medium composition, natural body language, same character designs and room details to reuse across later frames, no subtitles, no dialogue text, no translations, no logos.

Prompt:

3-5 second realistic video. A learner sits at a small desk studying with a notebook and headphones nearby. A friend enters the room quietly through an open doorway, catches the learner's attention, smiles, and gives a friendly wave while saying hello. The learner looks up from the desk, surprised but happy. Warm indoor light, casual home study room, both people visible in a stable medium shot, natural body language, no subtitles, no dialogue text, no logos.

Learning purpose:

The wave and entrance make "hello" visually obvious and show why the learner needs to respond.

### Beat 2: Learner Turn / Meaning Gesture

Dialogue line: Learner says, "Hello! How are you?"

Audio file: `audio/ta-greeting-hello-1.mp3`

Timing role: Play this visual while line 1 audio plays; reuse it as the listening visual when the app asks the learner to produce this line.

Meaning target: "Hello! How are you?"

Visual mapping:

- Wave = "Hello"
- Open-hand gesture toward friend = "you"
- Raised eyebrows and slight forward lean = friendly question / "How are you?"

Still-image prompt:

Realistic still image, same cozy home study room, same learner and friend, same clothing and warm lighting as frame 0. Camera is closer to the learner at the desk, with the friend partly visible over the learner's shoulder. The learner is smiling, one hand raised in a small returning wave, the other hand open gently toward the friend to indicate "you," with raised eyebrows and a slight forward lean to show a friendly question. Natural conversational pose, stable medium close-up, no subtitles, no dialogue text, no translations, no logos.

Prompt:

3-5 second realistic video, same room, same characters and lighting. Camera shifts closer to the learner at the desk. The learner smiles, waves back for "hello," then gestures gently toward the friend with an open hand on "you" and raises eyebrows slightly to show a friendly question. The friend is partly visible over the learner's shoulder, listening. Natural conversational timing, no subtitles, no dialogue text, no logos.

Learning purpose:

The learner's wave maps to "hello"; the open-hand gesture toward the friend maps to "you"; raised eyebrows and posture signal a question.

### Beat 3: Response / Resolution

Dialogue line: Friend says, "Fine. Thank you."

Audio file: `audio/ta-greeting-hello-2.mp3`

Timing role: Play this visual while line 2 audio plays after a successful learner response.

Meaning target: "Fine. Thank you."

Visual mapping:

- Relaxed smile and nod = "Fine"
- Hand-to-chest and appreciative nod = "Thank you"
- Learner relaxes = the exchange succeeded socially

Still-image prompt:

Realistic still image, same cozy home study room, same learner and friend, same clothing and warm lighting as frames 0 and 1. Camera focuses on the friend's face and upper body. The friend smiles warmly, nodding slightly, with one hand lightly touching their chest to show appreciation. The learner is visible softly in the foreground or side of frame, relaxed and pleased. Stable medium close-up, ordinary friendly mood, no subtitles, no dialogue text, no translations, no logos.

Prompt:

3-5 second realistic video, same room, same characters and lighting. Camera switches to the friend's face and upper body. The friend smiles warmly, nods, and lightly touches their chest while answering that they are fine, then gives a small appreciative nod for thank you. The learner is visible in the foreground, relaxed and pleased. Stable medium close-up, warm ordinary mood, no subtitles, no dialogue text, no logos.

Learning purpose:

The friend's relaxed expression and nod show a positive response; the hand-to-chest and appreciative nod support "fine" and "thank you."

## Output Format

When creating a storyboard file, use:

- Scene id
- Source dialogue path
- Scene setup
- Dialogue lines
- Visual continuity notes
- Beat 1 audio-to-visual mapping, prompt, and learning purpose
- Beat 2 audio-to-visual mapping, prompt, and learning purpose
- Beat 3 audio-to-visual mapping, prompt, and learning purpose
- Asset output directory and filenames

Suggested asset structure:

```text
visuals/<scene-id>/
  frame-0.png
  frame-1.png
  frame-2.png
  beat-0.mp4
  beat-1.mp4
  beat-2.mp4
```

Prompt files should usually be stored as:

```text
visuals/<scene-id>/prompts/
  frame-0.txt
  frame-1.txt
  frame-2.txt
  beat-0.txt
  beat-1.txt
  beat-2.txt
```

## Quality Checklist

Before finalizing prompts, check:

- Does each beat correspond to a dialogue turn or social function?
- Does each beat name the audio file it supports?
- Does each beat say when the app should show it?
- Does each beat identify the target word/chunk/function?
- Does each beat map gestures, gaze, objects, or reactions to the target meaning?
- Does each beat include both a still-image prompt and a video prompt?
- Is the learner's expected line visually motivated?
- Are gestures natural and tied to meaning?
- Is the responder's reaction clear?
- Are all continuity details repeated enough for AI generation?
- Are subtitles, dialogue text, translations, and logos explicitly forbidden?
- Are any proper-noun labels justified, subtle, and limited to identity/context?
- Is the scene emotionally ordinary but memorable?
- Would a learner understand the context even with the audio muted?

## Common Mistakes

Avoid:

- Generic people standing and talking with no reason.
- Visuals that only decorate the card but do not teach meaning.
- Too many gestures in one beat.
- Written dialogue, subtitles, translations, or vocabulary labels.
- Proper-noun labels that distract from the spoken target phrase.
- Different character appearance across beats.
- Camera movement that distracts from the speaker turn.
- Cultural details that are vague, stereotyped, or inaccurate.
- Making the learner passive when the learner line is the target.
