# Frontend App Instructions

This folder is for the real frontend application source.

Use the reusable components in `view/components` by default. App-level code should compose components such as `SceneFrame`, `FrameStrip`, `AudioButton`, `MicPrompt`, `ChoicePrompt`, and `TravellerLessonPlayer` instead of rebuilding their UI directly in plain static scripts.

`view/static` is for browser-served output or very small throwaway prototypes. If a feature is part of the actual lesson experience, build it in `view/app` and import from `view/components`.

Preferred boundaries:

- `view/app`: app entry points, page-level state, lesson runner orchestration, routing or screen composition.
- `view/components`: reusable presentational and interaction components.
- `view/api`: frontend API client helpers.
- `view/static`: static shell and built assets served by the backend.

When adding lesson UI, start from the JSON contract and choose the matching component for each step. Add a new component only when none of the existing components owns that responsibility cleanly.
