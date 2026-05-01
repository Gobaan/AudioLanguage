## Card workflow (prompts + dialogue audio)

### Terminology

- **Prompt audio**: clips from `audio/prompts/*.mp3` (keys in `prompts.json`)
  - `opening`, `first_time`, `second_time`, `call_to_action`, `feedback_failure`, `feedback_success`, `closing`
- **Dialogue audio**: scene line clips from `audio/<sceneId>-<lineIndex>.mp3`

### First time opening a dialogue card (for that `scene.id`)

- Play prompt `opening`
- Play **dialogue line 1** (scene line index 0)
- Play prompt `first_time`
- Play **dialogue line 2** (scene line index 1)
- Play prompt `call_to_action`
- Open mic, wait for user response, compare to expected answer
  - If incorrect: play prompt `feedback_failure`
  - If incorrect twice: tell the user “try again tomorrow” (needs its own prompt if it should be spoken)
  - Else (correct): play prompt `feedback_success`, then `closing`, then play the **final dialogue line**

### Second+ time opening the same dialogue card

- Play prompt `opening`
- Play **dialogue line 1** (scene line index 0)
- Play prompt `call_to_action`
- Open mic, wait for user response, compare to expected answer
  - If incorrect: play prompt `feedback_failure`
- Play prompt `second_time`
- Play **dialogue line 2** (scene line index 1)
- Play prompt `call_to_action` again
- Open mic again
  - If incorrect again: tell the user “try again tomorrow”
  - Else (correct): play prompt `feedback_success`, then `closing`, then play the **final dialogue line**