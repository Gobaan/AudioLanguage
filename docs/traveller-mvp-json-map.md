# Traveller MVP JSON Walkthrough

This shows the Traveller MVP lesson loop in plain order. Under each MVP step is the JSON section that drives it in `docs/api-first-hello-lesson-en.json`.

## Lesson Target

The learner is practicing this phrase:

```json
"target": {
  "id": "en-target-respond-hi",
  "text": "Hi!",
  "transliteration": "",
  "meaning": "Respond to Hi."
}
```

## Comic Frames

The lesson uses these three visual frames. Visual frames start at 1.

```json
"frames": [
  {
    "id": "line-0",
    "lineIndex": 0,
    "frameNumber": 1,
    "imageUrl": "/visuals/final/first-hi-response/frame-1.png",
    "audioUrl": "/audio/generated/en/en-first-hi-response/line-0.mp3",
    "title": "World Opener",
    "speaker": "friend",
    "text": "Hi!",
    "lineType": "world_opener"
  },
  {
    "id": "line-1",
    "lineIndex": 1,
    "frameNumber": 2,
    "imageUrl": "/visuals/final/first-hi-response/frame-2.png",
    "audioUrl": "/audio/generated/en/en-first-hi-response/line-1.mp3",
    "title": "Learner Target",
    "speaker": "learner",
    "text": "Hi!",
    "lineType": "learner_target"
  },
  {
    "id": "line-2",
    "lineIndex": 2,
    "frameNumber": 3,
    "imageUrl": "/visuals/final/first-hi-response/frame-3.png",
    "audioUrl": "/audio/generated/en/en-first-hi-response/line-2.mp3",
    "title": "World Response",
    "speaker": "friend",
    "text": "Nice to see you.",
    "lineType": "world_response"
  }
]
```

## Step 1: Show Social Scene

MVP behavior:

- Show the opening scene.
- Play the scene cue.
- Mic is off.

JSON:

```json
{
  "id": "scene_setup",
  "type": "scene_setup",
  "component": "SceneFrame",
  "frameId": "line-0",
  "frameMode": "single",
  "displayText": "Listen.",
  "audio": {
    "url": "/audio/generated/en/en-first-hi-response/line-0.mp3",
    "autoplay": true,
    "replayable": true,
    "playBeforeMic": false
  },
  "mic": {
    "enabled": false,
    "record": false,
    "scoring": "none"
  }
}
```

## Step 2: Play Target Audio

MVP behavior:

- Show the learner speaking frame.
- Play target phrase audio.
- Mic is off.

JSON:

```json
{
  "id": "target_audio",
  "type": "target_audio",
  "component": "AudioButton",
  "frameId": "line-1",
  "frameMode": "single",
  "displayText": "Listen to what they say.",
  "audio": {
    "url": "/audio/generated/en/en-first-hi-response/line-1.mp3",
    "autoplay": true,
    "replayable": true,
    "playBeforeMic": false
  },
  "mic": {
    "enabled": false,
    "record": false,
    "scoring": "none"
  }
}
```

## Step 3: Ask What Happened

MVP behavior:

- Show the social outcome.
- Ask what happened.
- Learner chooses meaning.
- Mic is off.

JSON:

```json
{
  "id": "broad_meaning_guess",
  "type": "broad_meaning_guess",
  "component": "ChoicePrompt",
  "frameId": "line-2",
  "frameMode": "single",
  "displayText": "What happened?",
  "audio": {
    "url": "/audio/generated/en/en-first-hi-response/line-1.mp3",
    "autoplay": false,
    "replayable": true,
    "playBeforeMic": false
  },
  "mic": {
    "enabled": false,
    "record": false,
    "scoring": "none"
  },
  "props": {
    "choices": [
      {
        "id": "en-target-respond-hi",
        "label": "Respond to Hi.",
        "isCorrect": true
      }
    ]
  }
}
```

## Step 4: Reveal Translation

MVP behavior:

- Show the strip.
- Reveal phrase meaning.
- Replay target audio.
- Mic is off.

JSON:

```json
{
  "id": "translation_reveal",
  "type": "translation_reveal",
  "component": "TranslationReveal",
  "frameId": "line-1",
  "frameMode": "strip",
  "displayText": "Hi!",
  "audio": {
    "url": "/audio/generated/en/en-first-hi-response/line-1.mp3",
    "autoplay": true,
    "replayable": true,
    "playBeforeMic": false
  },
  "mic": {
    "enabled": false,
    "record": false,
    "scoring": "none"
  },
  "props": {
    "translation": "Respond to Hi.",
    "usage": "Respond to Hi."
  }
}
```

## Step 5: Replay Audio

MVP behavior:

- Replay the target audio before speaking practice.
- Mic is off.

JSON:

```json
{
  "id": "audio_replay",
  "type": "audio_replay",
  "component": "AudioButton",
  "frameId": "line-1",
  "frameMode": "single",
  "displayText": "Listen again.",
  "audio": {
    "url": "/audio/generated/en/en-first-hi-response/line-1.mp3",
    "autoplay": true,
    "replayable": true,
    "playBeforeMic": false
  },
  "mic": {
    "enabled": false,
    "record": false,
    "scoring": "none"
  }
}
```

## Step 6: User Repeats With Mic

MVP behavior:

- Play target audio.
- Then turn mic on.
- Record the learner.
- Continue without waiting for feedback.

JSON:

```json
{
  "id": "repeat_with_mic",
  "type": "repeat_with_mic",
  "component": "MicPrompt",
  "frameId": "line-1",
  "frameMode": "single",
  "displayText": "Now say it.",
  "audio": {
    "url": "/audio/generated/en/en-first-hi-response/line-1.mp3",
    "autoplay": true,
    "replayable": true,
    "playBeforeMic": true
  },
  "mic": {
    "enabled": true,
    "record": true,
    "startsAfterAudio": true,
    "expectedText": "Hi!",
    "expectedTransliteration": "",
    "scoring": "deferred",
    "continueOnRecord": true,
    "blockingFeedback": false
  }
}
```

## Step 7: Backward Build

MVP behavior:

- Practice smaller chunks.
- Each prompt records and continues.
- Feedback is deferred.

JSON:

```json
{
  "id": "backward_build",
  "type": "backward_build",
  "component": "BackwardBuild",
  "frameMode": "neutral",
  "displayText": "Build it from the end.",
  "mic": {
    "enabled": true,
    "record": true,
    "scoring": "deferred",
    "continueOnRecord": true,
    "blockingFeedback": false
  },
  "props": {
    "prompts": [
      {
        "text": "hello response",
        "audioUrl": "/audio/generated/en/en-first-hi-response/line-1.mp3",
        "mic": {
          "enabled": true,
          "record": true,
          "scoring": "deferred",
          "continueOnRecord": true,
          "blockingFeedback": false
        }
      },
      {
        "text": "response",
        "audioUrl": "/audio/generated/en/en-first-hi-response/line-1.mp3",
        "mic": {
          "enabled": true,
          "record": true,
          "scoring": "deferred",
          "continueOnRecord": true,
          "blockingFeedback": false
        }
      },
      {
        "text": "Hi!",
        "audioUrl": "/audio/generated/en/en-first-hi-response/line-1.mp3",
        "mic": {
          "enabled": true,
          "record": true,
          "scoring": "deferred",
          "continueOnRecord": true,
          "blockingFeedback": false
        }
      }
    ]
  }
}
```

## Step 8: Pimsleur-Style Prompt

MVP behavior:

- Ask from meaning.
- Mic is on.
- Record and continue.

JSON:

```json
{
  "id": "production_prompt",
  "type": "production_prompt",
  "component": "ProductionPrompt",
  "frameMode": "neutral",
  "displayText": "How do you say: Respond to Hi?",
  "mic": {
    "enabled": true,
    "record": true,
    "expectedText": "Hi!",
    "scoring": "deferred",
    "continueOnRecord": true,
    "blockingFeedback": false
  }
}
```

## Step 9: Scene-Based Spoken Recall

MVP behavior:

- Show the opening scene again.
- Play cue audio.
- Then mic turns on.
- Record and continue.

JSON:

```json
{
  "id": "scene_recall",
  "type": "scene_recall",
  "component": "SceneFrame",
  "frameId": "line-0",
  "frameMode": "single",
  "displayText": "What would you say?",
  "audio": {
    "url": "/audio/generated/en/en-first-hi-response/line-0.mp3",
    "autoplay": true,
    "replayable": true,
    "playBeforeMic": true
  },
  "mic": {
    "enabled": true,
    "record": true,
    "startsAfterAudio": true,
    "expectedText": "Hi!",
    "scoring": "deferred",
    "continueOnRecord": true,
    "blockingFeedback": false
  }
}
```

## Future Task: Transfer Scene

Transfer scenes are not part of this lesson JSON.

They should be separate lesson/task records because they are different scenes with their own frames, cue audio, recall prompt, and review scheduling.

## Future Task: Mini Guided Roleplay

Mini roleplay is not part of this lesson JSON.

It belongs in a future MVP task type with its own turn sequence, state machine, and scoring/scorecard behavior.

## Overall Lesson Plan: End-of-Lesson Scorecard

The scorecard is not part of this lesson JSON.

It belongs to the session or lesson-plan layer that receives recordings from the card, waits for deferred scoring, and summarizes feedback after the lesson flow is complete.

## Overall Lesson Plan: Schedule Spaced Review

Spaced review scheduling is not part of this lesson JSON.

It belongs to the learning engine layer that updates review state after the lesson or scorecard result is processed.
