# Code Fix-Up Plan

Executable refactor plan for AudioLanguage. Stages are ordered low-risk to high-risk.
Each stage is independent, behavior-preserving, and ends with verification and one commit.

## Rules for the executing agent

- Do ONE stage at a time. Verify, commit, then start the next stage.
- Never change behavior and structure in the same stage.
- Verification commands (run from repo root):
  - Backend: `python -m pytest`
  - Frontend: `npm run build` (run in `view/`)
- If a verification fails, fix the regression inside the same stage before committing.
- Before deleting anything, grep the whole repo for usages. If a usage exists, skip the deletion and note it.
- Keep import order and code style matching the surrounding file.

---

## Stage 0 — Baseline

**Goal:** Prove the suite is green before touching anything.

1. Run `python -m pytest` from repo root. All 46 tests must pass.
2. Run `npm run build` in `view/`. Must succeed.
3. If either fails, STOP and report — do not start refactoring on a red baseline.

No commit.

---

## Stage 1 — Delete dead code

**Goal:** Remove code with zero callers so later stages read less.

**Backend:**
1. `backend/app/main.py` line ~18: remove unused imports `normalize_for_match`, `text_similarity` (grep `main.py` first to confirm they are unused there).
2. `backend/app/content/lessons.py`: delete `phrase_contrast_choices` (~line 452) after grepping the repo to confirm no callers.

**Frontend:**
3. `view/api/validation.ts`: delete `deleteValidationSession` and `deleteValidationSessionData` exports after grepping `view/` confirms no imports.
4. Delete unused components from `view/components/` — for EACH file, grep `view/app/` and `view/components/` for imports first; delete only if unreferenced (note: some are referenced only by other unused components — delete leaves first, then wrappers):
   - `TravellerLessonPlayer.tsx`, `TVLessonPlayer.tsx`, `MiniRoleplay.tsx`,
     `AudioOnlyRecognition.tsx`, `SimilarPhraseContrast.tsx`, `ChunkBreakdown.tsx`,
     `ProgressCard.tsx`, `ModeSelector.tsx`, `FrameStrip.tsx`,
     `ProductionPrompt.tsx`, `TranslationReveal.tsx`, `MicPrompt.tsx`
5. Update `view/components/index.ts` to remove deleted exports.
6. `view/components/types.ts`: remove `player_component` from `Lesson` (grep confirms it is never read at runtime) and remove it from `FALLBACK_LESSON` in `TravellerMvpApp.tsx`.

**Verify:** `python -m pytest`; `npm run build`.
**Commit:** `Remove dead code and unused components`

---

## Stage 2 — Quarantine legacy backend systems

**Goal:** Remove the two parallel legacy content systems the frontend never calls.

1. Grep `view/` for `/api/scenes`, `/api/dialogues`, `/api/prompts`. Expected: no hits.
2. If no hits, delete from `backend/app/main.py`: routes `list_scenes`, `get_scene`, `list_dialogues`, `list_prompts` and their imports.
3. Delete `backend/app/scenes.py`, `backend/app/models.py` (legacy `Scene`/`Turn`), `backend/app/content/loader.py`, `backend/app/content/models.py` — but FIRST grep `tests/` for imports of these. `tests/test_content_loader.py` imports `app.content.loader`; delete the corresponding legacy test (`test_content_loader` for the old dialogues loader only — keep the data-graph tests in that file).
4. Remove `DIALOGUES_PATH` / `PROMPTS_PATH` constants from `main.py` if now unused.

**Verify:** `python -m pytest`. Manually start the server (`python scripts/launch_server.py`) and load `/learn?language=ja` to confirm lessons still serve. Stop the server.
**Commit:** `Remove legacy scenes and dialogues content systems`

---

## Stage 3 — Split backend routes into routers

**Goal:** `main.py` becomes a composition root under 100 lines. No logic changes — move code only.

Create `backend/app/routes/` with:

1. `backend/app/routes/pages.py` — APIRouter with the 4 `FileResponse` HTML shell routes (`/`, `/languages`, `/learn`, `/admin/validation`).
2. `backend/app/routes/content.py` — APIRouter with `/api/languages`, `/api/languages/{language}/session`, `/api/languages/{language}/lessons`, `/api/languages/{language}/distractors`.
3. `backend/app/routes/validation.py` — APIRouter with all `/api/validation/...` routes plus the request models `ValidationSessionRequest`, `ValidationEventRequest` and the scoring helpers `score_validation_attempts`, `score_validation_attempt`.
4. `backend/app/routes/conversation.py` — APIRouter with `/api/transcribe`, `/api/conversation/attempt` plus `evaluate_conversation_attempt` helpers (`conversation_response_payload`, `romanized_communication`, `parse_scene_contract`).
5. Move lesson-tab ordering logic (`lesson_tab_key`, `ordered_lesson_tabs`, `shuffled_tabs`, `is_transfer_tab`, `lessons_in_tab_order`, `selected_lessons`, `lesson_aliases_from_session`, `raw_lesson_tabs`, `lesson_tabs_from_ordered_tabs`, `lesson_tabs_from_session`) into a new `backend/app/content/lesson_tabs.py`. `routes/content.py` imports from it.
6. Shared app-level objects (`PATHS`, `validation_store`, `conversation_coach`) move to a new `backend/app/runtime.py` that routers import. Keep them module-level (simple), but `runtime.py` is now the single place that owns them.
7. `main.py` keeps: FastAPI app creation, CORS, cache middleware, static mounts, and `include_router` calls for the 4 routers.

Rules:
- Move functions verbatim; do not edit bodies.
- Update test imports if any test imports moved names from `app.main`.

**Verify:** `python -m pytest`.
**Commit:** `Split main.py into routers and extract lesson tab ordering`

---

## Stage 4 — Consolidate script duplication

**Goal:** One shared helper module for scripts; no duplicate JSON I/O.

1. `scripts/content_assets.py` is the existing shared module. Move into it (keeping names):
   - `read_json` / `write_json` (delete copies in `add_transfer_scenes.py`; point `verify_audio.load_dialogues` at it).
   - A `DEFAULT_DATA_DIR = "model/content"` constant; replace the hardcoded `"model/content"` default in the 6 scripts that define `--data-dir` (`build_audio_manifest.py`, `build_visual_prompt_manifest.py`, `generate_tts_from_manifest.py`, `generate_images_from_manifest.py`, `export_visual_prompt_files.py`, `validate_asset_manifests.py`).
2. `scripts/add_transfer_scenes.py` lines ~15-16: replace `ROOT / "model" / "content" / "languages"` with `repo_paths()` from `project_config.paths`.

**Verify:** `python -m pytest`; run `python scripts/validate_asset_manifests.py` and confirm it exits 0.
**Commit:** `Consolidate script JSON I/O and data-dir defaults`

---

## Stage 5 — Rename and split the misnamed test file

**Goal:** Tests named by what they cover.

1. Split `tests/test_cache_headers.py` (543 lines) into:
   - `tests/test_cache_headers.py` — keep ONLY the 2 cache-middleware/static-header tests.
   - `tests/test_lessons_api.py` — the 11 language/lesson/distractor API tests.
   - `tests/test_validation_api.py` — the 6 validation API tests.
2. Move shared fixtures/setup either into `tests/conftest.py` or duplicate the small client setup per file — prefer `conftest.py`.

**Verify:** `python -m pytest` — same total test count as before the split.
**Commit:** `Split API tests out of test_cache_headers`

---

## Stage 6 — Frontend shared helpers and audio hook

**Goal:** Kill the 4-5x duplicated audio and URL logic. Extract pure helpers first, then the hook.

1. Create `view/app/urlParams.ts` exporting `participantFromUrl()`, `isLocalHost()` (move from `LanguageSelectionApp.tsx` and `TravellerMvpApp.tsx`; both files import from it).
2. Create `view/app/useAudioPlayback.ts` — a hook owning: `audioRef`, `utteranceRef`, `isPlaying`, `playAudio(url)`, `speakText(text, lang)`, `stop()`. Behavior must match the existing pattern in `TravellerMvpApp.tsx` lines ~379-459 and ~816-827 (HTML Audio first, speech-synthesis fallback, cleanup on stop).
3. Replace inline audio logic with the hook in, one file per sub-step (verify build after each):
   a. `TravellerMvpApp.tsx`
   b. `LessonStepRenderer.tsx` (`ResponsePlayback`)
   c. `ScenePlayback.tsx`
   d. `DialogueReveal.tsx`
   e. `PromptedRecording.tsx` (keep its MediaRecorder logic in place; only swap the prompt-audio playback part if it matches the pattern, otherwise leave and note it)
4. Add a `requireOk(response)` helper in a new `view/api/http.ts` that throws on `!response.ok`; use it in `logValidationEvent` and `uploadValidationAttempt` in `view/api/validation.ts`.

**Verify:** `npm run build`; manually load `/learn` and play audio on a scene step and a response step.
**Commit:** `Extract shared audio playback hook and URL helpers`

---

## Stage 7 — Break up TravellerMvpApp

**Goal:** `TravellerMvpApp.tsx` under 250 lines; each workflow in its own file. Extract in this order:

1. Move `FALLBACK_LESSON` (lines ~38-210) to `view/app/fallbackLesson.ts` as a typed `Lesson` export.
2. Move `ValidationScorecardView`, `ScorecardDetails`, `scoreLabel` to `view/app/ScorecardView.tsx`. Props: `scorecard`, `scorecardState`, `onBack`, `onRefresh`. No logic changes.
3. Create `view/app/useParticipantId.ts` — hook owning the URL → localStorage → API-suggestion → random-fallback resolution (current effect at lines ~234-269 plus `saveParticipantId`, `fallbackParticipantId`, `PARTICIPANT_STORAGE_KEY`).
4. Create `view/app/useValidationSession.ts` — hook owning session start (effect at ~271-297), `logValidationEvent` wrapper, and `captureAttempt` upload. Inputs: `participantId`, `language`, `sceneSet`, `lessonPage`. Returns: `sessionId`, `logEvent`, `uploadAttempt`.
5. Create `view/app/useLessonLoader.ts` — hook owning lesson fetch with the double-fallback chain (effect at ~299-336) and `activeMvpLesson` filtering. Returns: `lesson`, `lessonTabs`, `loadState`.
6. Keep in `TravellerMvpApp.tsx`: route/URL state, step navigation, view toggle, composition of the hooks above, and the JSX shell.
7. Module-level helpers that survive (`languageFromUrl`, `lessonPageFromUrl`, `sceneSetFromUrl`, `updateLessonUrl`, asset URL rewriting) move to `view/app/lessonUrls.ts`.

Do ONE extraction per sub-step and run `npm run build` after each. Do not change behavior — this is a move-only stage.

**Verify:** `npm run build`; manual smoke: load `/learn?language=ja`, navigate steps, open scorecard, switch language.
**Commit (one per extraction or one final):** `Split TravellerMvpApp into feature hooks and scorecard view`

---

## Stage 8 — Data-driven language metadata (contract change)

**Goal:** Remove hardcoded language branches from the UI, per project rule "prefer backend-served JSON over hardcoded UI branches".

Backend first:
1. Extend `list_languages` in `backend/app/content/data_graph.py` so each language entry also returns `description` and `scene_sets` (e.g. `["mvp", "delayed"]`). Source these from a new optional `metadata` block in each `model/content/languages/<lang>/targets.json` (or a small `language.json` per language folder — pick whichever file already carries display_name). Fall back to empty description and `["mvp"]` when absent.
2. Add the metadata for existing languages: en, ta, ja, yue, zh. Copy the description strings currently hardcoded in `view/app/LanguageSelectionApp.tsx` lines ~95-102; delayed-review support currently hardcoded as ja/zh at lines ~104-106.
3. Add a test in `tests/test_lessons_api.py` asserting `/api/languages` returns `description` and `scene_sets` per language.

Frontend second:
4. `LanguageSelectionApp.tsx`: delete `languageDescription()` and `supportsDelayedReview()`; read `description` and `scene_sets` from the fetched payload.
5. `TravellerMvpApp.tsx`: delete `LANGUAGE_OPTIONS`; populate the language switcher from `fetchLanguages()` (load once alongside the lesson). `languageFromUrl` validation accepts any fetched language id; before the list loads, accept the URL value as-is.

**Verify:** `python -m pytest`; `npm run build`; manual: language cards show descriptions, delayed link appears only for ja/zh, switcher lists all languages.
**Commit:** `Serve language descriptions and scene sets from the backend`

---

## Stage 9 — Error-handling consistency pass (backend)

**Goal:** One consistent boundary-error story; no silent data loss.

1. `backend/app/validation.py` `read_jsonl` (~line 470): on `JSONDecodeError`, log a warning with file path and line number (use the `logging` module) instead of bare `continue`. Keep skipping the line.
2. `routes/content.py` `get_language_distractors`: replace the manual `language_dir.exists()` check with the same `DataGraphError` → 404 pattern used by session/lessons routes (move the existence check into `load_distractors` raising `DataGraphError`).
3. `routes/validation.py` `score_validation_attempt`: keep the catch-and-persist-unavailable behavior but log the exception with `logging.exception`.
4. Add `pattern=r"^[a-z]{2,3}(-[a-z]+)?$"`-style validation for the `language` path param on content routes (FastAPI `Path(...)`), matching existing language folder ids.
5. Make scorecard scoring explicit: keep `GET /scorecard?score=true` working but log a deprecation warning; this avoids breaking the frontend now. (Do NOT change the frontend in this stage.)

**Verify:** `python -m pytest`.
**Commit:** `Consistent API error handling and JSONL skip logging`

---

## Stage 10 — Optional cleanups (do only if explicitly asked)

- Stop committing built artifacts: add `view/static/assets/` to `.gitignore` and have deploy build instead (requires deploy script change in `scripts/deploy_linode.ps1`).
- Split `backend/app/content/data_graph.py` (314 lines) into `session_hydration.py` + `asset_paths.py` + `manifests.py`.
- Split `view/app/LessonStepRenderer.tsx` (427 lines): extract `ProductionPracticeStep` and `ResponsePlayback` into their own files; replace the if/else chain with a step-type → component registry map.
- Split `view/app/AdminValidationApp.tsx` (412 lines) into `admin/` folder components.
- Move `conversation_coach` creation behind a FastAPI dependency so `OPENAI_API_KEY` is read per-request-scope instead of at import.
- Wire `step.audio.autoplay` for non-scene steps (currently only `scene_setup` honors it) — this is a behavior change, needs user sign-off.

---

## Done criteria

- `python -m pytest` green, same-or-more tests than baseline.
- `npm run build` green.
- No source file over 500 lines; `main.py` and `TravellerMvpApp.tsx` under 250.
- Zero duplicate `read_json`/`stopAudio` implementations.
- UI has no hardcoded per-language branches (descriptions, delayed gating, language options).
