# Component Instructions

Components in this folder should be reusable and language-agnostic. Accept labels, prompts, options, translations, audio paths, speaker roles, and state through props derived from lesson JSON.

Do not hardcode English lesson content inside reusable components. English UI chrome such as "Next", "Play", or "Record" is acceptable for now, but lesson-specific text should come from the backend payload.

Prefer existing components before creating new ones. Add a component only when no existing component owns the interaction cleanly.

Interaction components should expose clear states for selected, correct, incorrect, recording, playing, pending score, and disabled behavior where relevant. Keep feedback visual and minimal in the MVP unless the lesson step explicitly asks for explanation.
