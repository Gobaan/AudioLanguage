# Refactor Plan Round 2

Executable follow-up plan for AudioLanguage. Closes missed done-criteria from round 1.
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

## Verification result (round 1 gaps)

Round 1 done-criteria check: tests and build green, `main.py` at 36 lines, no duplicate audio/JSON helpers. Three misses:

- `backend/app/validation.py` is 529 raw lines (criterion: none over 500)
- `view/app/TravellerMvpApp.tsx` is 314 raw lines (criterion: under 250)
- `PREFERRED_LANGUAGE_ORDER` hardcoded in `view/app/LanguageSelectionApp.tsx`
- Leftover dead field: backend still emits `player_component` (`player_component_for` in `backend/app/content/lessons.py`) referencing components deleted in round 1 Stage 1; asserted only by `tests/test_lessons_api.py`

---

## Stage 1 — Remove player_component leftover

**Goal:** Delete backend field that the frontend no longer consumes.

1. Delete `player_component_for` and the `"player_component"` key from `lesson_from_card` in `backend/app/content/lessons.py`.
2. Remove the assertion at `tests/test_lessons_api.py` that checks `player_component`.
3. Grep repo to confirm no other runtime consumers (docs/contact-sheet references are fine).

**Verify:** `python -m pytest`
**Commit:** `Remove unused player_component from lesson payload`

---

## Stage 2 — Split validation.py into a package

**Goal:** No source file over 500 lines; keep import paths stable.

Convert to `backend/app/validation/` package, move code verbatim:

1. `store.py` — the `ValidationStore` class unchanged.
2. `jsonl_io.py` — `write_json`, `append_jsonl`, `write_jsonl`, `read_jsonl`, `relative_to_root`, `delete_file`, `safe_id`, `safe_suffix`, `now_iso`, `SAFE_ID`.
3. `scoring.py` — `is_remembered_score`, `score_status`, `participant_id_from`, `HUMAN_NAMES`.
4. `__init__.py` — re-export everything currently importable from `app.validation` (tests import `ValidationStore`; routes import via `app.runtime`).

Note: `HUMAN_NAMES` is used by `ValidationStore.suggest_participant_name`; keep import direction `store.py` → `scoring.py` / `jsonl_io.py` only.

5. Delete the old `backend/app/validation.py` module file.

**Verify:** `python -m pytest`
**Commit:** `Split validation store into a package`

---

## Stage 3 — Trim TravellerMvpApp.tsx under 250

**Goal:** Shell under 250 raw lines via move-only extractions.

From `view/app/TravellerMvpApp.tsx`:

1. `view/app/useLanguageOptions.ts` — the `fetchLanguages` effect + `languageOptions` state.
2. `view/app/useScorecard.ts` — `scorecard`/`scorecardState` state + `showScorecard`; takes `validationSessionId`, `logEvent`, and current step context as inputs.
3. `view/app/LessonNavBars.tsx` — language-switcher and lesson-switcher `<nav>` JSX; props: `languageOptions`, `language`, `lessonTabs`, `lessonPage`, `onSelectLanguage`, `onSelectLessonPage`.

Do ONE extraction per sub-step and run `npm run build` after each. Do not change behavior.

**Verify:** `npm run build`; `python -m pytest` if any shared types changed.
**Commit:** `Trim TravellerMvpApp with language and scorecard hooks`

---

## Stage 4 — Backend-served language sort order

**Goal:** Remove hardcoded language ordering from the UI.

Backend first:

1. Add `"sort_order"` to the `metadata` block in each `model/content/languages/<lang>/targets.json` (ja=1, yue=2, zh=3, ta=4, en=5, matching current `PREFERRED_LANGUAGE_ORDER`).
2. Extend `list_languages` in `backend/app/content/session_hydration.py` to read `sort_order` (fallback large number), include it in the payload, and sort results by `(sort_order, id)`.
3. Add a test in `tests/test_lessons_api.py` asserting `/api/languages` returns languages in sort order.

Frontend second:

4. Delete `PREFERRED_LANGUAGE_ORDER` and `sortLanguages` from `view/app/LanguageSelectionApp.tsx`; render fetched order as-is.
5. Extend `LanguageSummary` in `view/api/languages.ts` with optional `sort_order` if the client needs it for typing (ordering comes from API response order).

**Verify:** `python -m pytest`; `npm run build`
**Commit:** `Serve language sort order from the backend`

---

## Stage 5 — Split lessons.py (optional, only if explicitly asked)

- `backend/app/content/lesson_steps.py` — `lesson_steps`, `step`, `audio_behavior`, `mic_off`, `recording_mic`, `backward_build_*`, `should_include_backward_build`, `localized_*`
- Keep `lessons.py` as the entry (`lessons_from_session`, `lesson_from_card`, `frame_data`, `meaning_choices`, helpers), importing from `lesson_steps.py`

---

## Noted, deliberately not staged

- `scripts/content_assets.py` `read_json` vs backend `graph_core.read_json`: separate runtimes, acceptable duplication
- `localized_audio_text`/`localized_mic_text` hardcode Japanese UI strings in `lessons.py`: moving to model content is a contract change; needs separate sign-off
- `asset_folder_slug` hardcoded language-prefix set in `asset_paths.py`: low value to change

---

## Done criteria

- `python -m pytest` green, same-or-more tests than baseline
- `npm run build` green
- No source file over 500 raw lines; `TravellerMvpApp.tsx` under 250 raw lines
- `view/` contains no hardcoded language id lists (grep for `'ja'` finds only `DEFAULT_LANGUAGE`)
- `/api/languages` payload drives card order, descriptions, and scene sets
