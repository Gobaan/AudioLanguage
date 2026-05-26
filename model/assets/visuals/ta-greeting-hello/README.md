# ta-greeting-hello Visual Prompts

These prompts generate the three short video beats described in `storyboards/ta-greeting-hello.md`.

Use the frame prompts first if you are starting with image generation:

- `prompts/frame-0.txt` -> `frame-0.png`
- `prompts/frame-1.txt` -> `frame-1.png`
- `prompts/frame-2.txt` -> `frame-2.png`

Use one beat prompt per generated video:

- `prompts/beat-0.txt` -> `beat-0.mp4`
- `prompts/beat-1.txt` -> `beat-1.mp4`
- `prompts/beat-2.txt` -> `beat-2.mp4`

Keep the same character appearance, clothing, room, lighting, and camera style across all three generations.

If the video model supports image references, use each generated frame as the reference image for the matching video beat.
