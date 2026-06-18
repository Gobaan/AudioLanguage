import json
import subprocess
import tempfile
import textwrap
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
TYPESCRIPT_PACKAGE = PROJECT_DIR / "view" / "node_modules" / "typescript"


def run_frontend_script(source_paths: list[str], script: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        runner_path = Path(temp_dir) / "runner.cjs"
        runner_path.write_text(
            textwrap.dedent(
                f"""
                const fs = require('fs');
                const path = require('path');
                const Module = require('module');
                const ts = require({json.dumps(str(TYPESCRIPT_PACKAGE))});

                const projectDir = {json.dumps(str(PROJECT_DIR))};
                const outDir = {json.dumps(temp_dir)};
                const sourcePaths = {json.dumps(source_paths)};
                process.env.NODE_PATH = path.join(projectDir, 'view', 'node_modules');
                Module._initPaths();

                function outputPathFor(sourcePath) {{
                  return path.join(outDir, sourcePath).replace(/\\.[tj]sx?$/, '.js');
                }}

                for (const sourcePath of sourcePaths) {{
                  const fullPath = path.join(projectDir, sourcePath);
                  const source = fs.readFileSync(fullPath, 'utf8');
                  const output = ts.transpileModule(source, {{
                    compilerOptions: {{
                      target: ts.ScriptTarget.ES2022,
                      module: ts.ModuleKind.CommonJS,
                      jsx: ts.JsxEmit.ReactJSX,
                      esModuleInterop: true,
                    }},
                  }}).outputText;
                  const outputPath = outputPathFor(sourcePath);
                  fs.mkdirSync(path.dirname(outputPath), {{ recursive: true }});
                  fs.writeFileSync(outputPath, output);
                }}

                function requireSource(sourcePath) {{
                  return require(outputPathFor(sourcePath));
                }}

                {script}
                """
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            ["node", str(runner_path)],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)


def test_scene_recall_recording_uses_auto_start_helper():
    helper_source = (PROJECT_DIR / "view" / "app" / "lessonStepHelpers.ts").read_text(encoding="utf-8")
    production_source = (PROJECT_DIR / "view" / "app" / "ProductionPracticeStep.tsx").read_text(encoding="utf-8")

    assert "export function recordingStartsAutomatically" in helper_source
    assert "recordingUsesPromptAudio(step)" in helper_source
    assert "step.type === 'scene_recall'" in helper_source
    assert "step.props.recordBeforeModelLine === true" in helper_source
    assert "recordingStartsAutomatically" in production_source
    assert "startMode={startsRecordingAutomatically ? 'auto' : 'manual'}" in production_source


def test_recording_steps_show_learner_frame_before_attempt():
    result = run_frontend_script(
        ["view/app/lessonStepHelpers.ts"],
        """
        const { recordingFrameForProduction } = requireSource('view/app/lessonStepHelpers.ts');
        const lesson = {
          stage: 'same_day_transfer',
          frames: [
            { id: 'line-0', lineType: 'world_opener' },
            { id: 'line-1', lineType: 'learner_target' },
            { id: 'line-2', lineType: 'world_response' },
          ],
        };
        const recallStep = {
          type: 'scene_recall',
          frameId: 'line-1',
          props: { recordBeforeModelLine: true },
          mic: { enabled: true, record: true },
        };
        const anchorStep = {
          type: 'backward_build',
          frameId: 'line-1',
          props: { recordBeforeModelLine: true },
          mic: { enabled: true, record: true },
        };

        console.log(JSON.stringify({
          recallFrameId: recordingFrameForProduction(lesson, recallStep).id,
          anchorFrameId: recordingFrameForProduction(lesson, anchorStep).id,
        }));
        """,
    )

    assert result["recallFrameId"] == "line-1"
    assert result["anchorFrameId"] == "line-1"


def test_recording_timer_uses_five_second_countdown_bar():
    recording_source = (PROJECT_DIR / "view" / "components" / "PromptedRecording.tsx").read_text(
        encoding="utf-8"
    )
    preview_source = (PROJECT_DIR / "view" / "app" / "RecordingCountdownPreview.tsx").read_text(encoding="utf-8")
    countdown_source = (PROJECT_DIR / "view" / "components" / "RecordingCountdownBar.tsx").read_text(
        encoding="utf-8"
    )
    production_source = (PROJECT_DIR / "view" / "app" / "ProductionPracticeStep.tsx").read_text(encoding="utf-8")
    registry_source = (PROJECT_DIR / "view" / "app" / "lessonStepRegistry.tsx").read_text(encoding="utf-8")
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")

    assert "step.mic?.maxDurationMs" in production_source
    assert "recordingMs={recordingMs}" in production_source
    assert "recordingMs = 5000" in recording_source
    assert "RecordingCountdownBar" in recording_source
    assert "isPaused={isSpeechActive}" in recording_source
    assert "setSpeechActive(isSpeaking)" in recording_source
    assert "SPEECH_VISUAL_HOLD_MS = 500" in recording_source
    assert "clearSpeechVisualHoldTimer()" in recording_source
    assert "recordingDurationMs(context.step)" in registry_source
    assert "recordingMs={recordingDurationMs(context.step)}" in registry_source
    assert "recording-countdown" in countdown_source
    assert "--recording-duration" in countdown_source
    assert "recording-countdown--paused" in countdown_source
    assert "<PromptedRecording" in preview_source
    assert 'startMode="manual"' in preview_source
    assert "animation-play-state: paused" in styles_source
    assert "@keyframes recording-countdown-drain" in styles_source


def test_recording_timer_tracks_no_response_and_extends_while_speaking():
    recording_source = (PROJECT_DIR / "view" / "components" / "PromptedRecording.tsx").read_text(
        encoding="utf-8"
    )
    validation_source = (PROJECT_DIR / "view" / "app" / "useValidationSession.ts").read_text(encoding="utf-8")
    types_source = (PROJECT_DIR / "view" / "components" / "types.ts").read_text(encoding="utf-8")

    assert "export type CapturedRecording" in types_source
    assert "speechDetected?: boolean" in types_source
    assert "timedOutWithoutSpeech?: boolean" in types_source
    assert "recordingStoppedBy?: string" in (PROJECT_DIR / "view" / "api" / "validationTypes.ts").read_text(
        encoding="utf-8"
    )
    assert "startSpeechDetection(stream, stopAfterSilenceMs)" in recording_source
    assert "rootMeanSquare(samples)" in recording_source
    assert "stoppedByRef.current = 'no_speech_timeout'" in recording_source
    assert "stoppedByRef.current = 'speech_completed'" in recording_source
    assert "hardLimitMs = recordingMs + 5000" in recording_source
    assert "speechDetected: recording.speechDetected" in validation_source
    assert "timedOutWithoutSpeech: recording.timedOutWithoutSpeech" in validation_source
    assert "recordingStoppedBy: recording.stoppedBy" in validation_source


def test_lesson_audio_errors_instead_of_browser_tts_fallback():
    audio_source = (PROJECT_DIR / "view" / "app" / "audioPlayback.ts").read_text(encoding="utf-8")
    hook_source = (PROJECT_DIR / "view" / "app" / "useAudioPlayback.ts").read_text(encoding="utf-8")
    scene_source = (PROJECT_DIR / "view" / "components" / "ScenePlayback.tsx").read_text(encoding="utf-8")
    recording_source = (PROJECT_DIR / "view" / "components" / "PromptedRecording.tsx").read_text(
        encoding="utf-8"
    )
    step_audio_source = (PROJECT_DIR / "view" / "app" / "StepAudioButton.tsx").read_text(encoding="utf-8")
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")

    assert "speechSynthesis.speak" not in audio_source
    assert "AUDIO_PLAYBACK_ERROR" in audio_source
    assert "AUDIO_MISSING_ERROR" in audio_source
    assert "audioError" in hook_source
    assert "role=\"alert\"" in scene_source
    assert "role=\"alert\"" in recording_source
    assert "step.audio?.audioText" not in step_audio_source
    assert ".audio-error" in styles_source


def test_localhost_lesson_jump_uses_backend_lesson_tabs():
    app_source = (PROJECT_DIR / "view" / "app" / "TravellerMvpApp.tsx").read_text(encoding="utf-8")
    shell_source = (PROJECT_DIR / "view" / "app" / "TravellerLessonShell.tsx").read_text(encoding="utf-8")
    loader_source = (PROJECT_DIR / "view" / "app" / "useLessonLoader.ts").read_text(encoding="utf-8")
    api_source = (PROJECT_DIR / "view" / "api" / "lessons.ts").read_text(encoding="utf-8")

    assert "isLocalHost() ?" in app_source
    assert 'aria-label="Local lesson jump"' in app_source
    assert "lessonTabs.map((tab)" in app_source
    assert "onClick={() => selectLessonPage(tab.id)}" in app_source
    assert "debugLessonSwitcher" in shell_source
    assert "orderSeed?: string | null" in api_source
    assert "params.set('order_seed', orderSeed)" in api_source
    assert "fetchLearningPlan" in api_source
    assert "/api/learning-engine/lessons" in api_source
    assert "fetchLearningPlan(language, sceneSet, stableOrderSeed(language, sceneSet), participantId)" in loader_source
    assert "participantId: string | null" in loader_source
    assert "participantId," in app_source
    assert "selectLessonForPage(lessonPage, lessonTabs, lessons)" in loader_source
    assert "fetchLessons(language, lessonPage" not in loader_source
    assert "stableOrderSeed(language, sceneSet)" in loader_source
    assert "local-debug:${language}:${sceneSet}" in loader_source


def test_frontend_sends_learning_plan_metadata_to_validation():
    active_step_source = (PROJECT_DIR / "view" / "app" / "useActiveLessonStep.ts").read_text(encoding="utf-8")
    validation_source = (PROJECT_DIR / "view" / "app" / "useValidationSession.ts").read_text(encoding="utf-8")
    types_source = (PROJECT_DIR / "view" / "components" / "types.ts").read_text(encoding="utf-8")
    api_types_source = (PROJECT_DIR / "view" / "api" / "validationTypes.ts").read_text(encoding="utf-8")
    lesson_api_source = (PROJECT_DIR / "view" / "api" / "lessons.ts").read_text(encoding="utf-8")

    assert "targetId?: string" in types_source
    assert "planPurpose?: string" in types_source
    assert "repairCategory?: string" in types_source
    assert "participant_id" in lesson_api_source
    assert "planPurpose: stepLesson.planPurpose" in active_step_source
    assert "repairCategory: stepLesson.repairCategory" in active_step_source
    assert "planPurpose: lesson.planPurpose" in validation_source
    assert "repairCategory: lesson.repairCategory" in validation_source
    assert "planPurpose?: string" in api_types_source
    assert "repairCategory?: string" in api_types_source


def test_scene_playback_autoplay_depends_on_frame_identity_not_array_reference():
    scene_playback_source = (PROJECT_DIR / "view" / "components" / "ScenePlayback.tsx").read_text(
        encoding="utf-8"
    )

    assert "const playbackKey = useMemo" in scene_playback_source
    assert "frame.id" in scene_playback_source
    assert "frame.audioUrl" in scene_playback_source
    assert "frame.audioText" in scene_playback_source
    assert "}, [autoplay, playbackKey]);" in scene_playback_source
    assert "}, [autoplay, playableFrames]);" not in scene_playback_source


def test_admin_link_and_participant_name_stay_off_lesson_page():
    result = run_frontend_script(
        ["view/app/LessonAppLinks.tsx"],
        """
        const React = require('react');
        const { renderToStaticMarkup } = require('react-dom/server');
        const { LessonAppLinks } = requireSource('view/app/LessonAppLinks.tsx');

        const html = renderToStaticMarkup(
          React.createElement(LessonAppLinks, {
            participantId: 'Bob',
            onOpenScorecard() {},
          })
        );
        console.log(JSON.stringify({ html }));
        """,
    )

    assert "Scorecard" in result["html"]
    assert "/admin/validation" not in result["html"]
    assert "Admin" not in result["html"]
    assert "Bob" not in result["html"]


def test_localhost_admin_link_uses_private_route():
    result = run_frontend_script(
        ["view/app/LocalDevLinks.tsx", "view/app/LanguageSelectionApp.tsx", "view/app/main.tsx"],
        """
        const localLinksSource = require('fs').readFileSync(
          require('path').join(projectDir, 'view/app/LocalDevLinks.tsx'),
          'utf8'
        );
        const languageSelectionSource = require('fs').readFileSync(
          require('path').join(projectDir, 'view/app/LanguageSelectionApp.tsx'),
          'utf8'
        );
        const mainSource = require('fs').readFileSync(
          require('path').join(projectDir, 'view/app/main.tsx'),
          'utf8'
        );
        console.log(JSON.stringify({ localLinksSource, languageSelectionSource, mainSource }));
        """,
    )

    assert 'href="/gobi-admin"' in result["localLinksSource"]
    assert 'href="/gobi-admin"' in result["languageSelectionSource"]
    assert "pathname === '/gobi-admin'" in result["mainSource"]
    assert "/admin/validation" not in result["localLinksSource"]
    assert "/admin/validation" not in result["languageSelectionSource"]
    assert "/admin/validation" not in result["mainSource"]


def test_homepage_uses_private_route():
    main_source = (PROJECT_DIR / "view" / "app" / "main.tsx").read_text(encoding="utf-8")

    assert "pathname === '/gobi-home'" in main_source
    assert 'aria-label="Page unavailable"' in main_source


def test_language_links_do_not_expose_participant_and_delayed_uses_start_marker():
    result = run_frontend_script(
        ["view/app/lessonUrls.ts", "view/app/lessonLinks.ts"],
        """
        const { languageLessonLink } = requireSource('view/app/lessonLinks.ts');
        console.log(JSON.stringify({
          mvp: languageLessonLink('ja', 'mvp'),
          delayed: languageLessonLink('ja', 'delayed'),
        }));
        """,
    )

    assert result["mvp"] == "/learn?language=ja&lesson=start"
    assert result["delayed"] == "/learn?language=ja&lesson=start&scene_set=delayed"
    assert "participant" not in result["mvp"]
    assert "participant" not in result["delayed"]


def test_audio_debug_player_skips_choices_and_recording_uploads():
    debug_source = (PROJECT_DIR / "view" / "app" / "DebugAudioLessonPlayer.tsx").read_text(encoding="utf-8")
    selection_source = (PROJECT_DIR / "view" / "app" / "LanguageSelectionApp.tsx").read_text(encoding="utf-8")
    main_source = (PROJECT_DIR / "view" / "app" / "main.tsx").read_text(encoding="utf-8")
    link_source = (PROJECT_DIR / "view" / "app" / "lessonLinks.ts").read_text(encoding="utf-8")

    assert "fetchLearningPlan" in debug_source
    assert "new Audio(item.url)" in debug_source
    assert "contextTextForFrame(frame, lesson)" in debug_source
    assert "targetPhraseMeaning(lesson)" in debug_source
    assert "lesson.target.englishMeaning || lesson.target.meaning" in debug_source
    assert "World opener: context prompt" not in debug_source
    assert "World response: follow-up" not in debug_source
    assert "lineDisplayText(frame)" in debug_source
    assert "<small>{item.contextText}</small>" in debug_source
    assert "uploadValidationAttempt" not in debug_source
    assert "useValidationSession" not in debug_source
    assert "PromptedRecording" not in debug_source
    assert "ChoicePrompt" not in debug_source
    assert "languageAudioDebugLink" in selection_source
    assert "isLocalHost() ? <a href={languageAudioDebugLink" in selection_source
    assert "if (pathname === '/debug/audio')" in main_source
    assert "return `/debug/audio?${params.toString()}`" in link_source
    assert "return `/?${params.toString()}`" not in link_source


def test_delayed_review_start_marker_resolves_to_first_backend_plan_tab():
    result = run_frontend_script(
        ["view/app/lessonUrls.ts", "view/app/lessonSelection.ts"],
        """
        const { START_LESSON } = requireSource('view/app/lessonUrls.ts');
        const { selectLessonForPage } = requireSource('view/app/lessonSelection.ts');
        const tabs = [
          { id: 'repair', label: 'Scene 1' },
          { id: 'hello', label: 'Scene 2' },
        ];
        const lessons = [
          { id: 'repair-lesson' },
          { id: 'hello-lesson' },
        ];

        console.log(JSON.stringify({
          start: selectLessonForPage(START_LESSON, tabs, lessons),
          explicit: selectLessonForPage('hello', tabs, lessons),
          missing: selectLessonForPage('missing', tabs, lessons),
        }));
        """,
    )

    assert result["start"]["lesson"]["id"] == "repair-lesson"
    assert result["start"]["resolvedLessonPage"] == "repair"
    assert result["start"]["shouldReplaceUrl"] is True
    assert result["explicit"]["lesson"]["id"] == "hello-lesson"
    assert result["explicit"]["shouldReplaceUrl"] is False
    assert result["missing"]["lesson"]["id"] == "hello-lesson"
    assert result["missing"]["resolvedLessonPage"] == "hello"


def test_learner_session_landing_renders_next_session_actions():
    result = run_frontend_script(
        ["view/app/LearnerSessionLanding.tsx"],
        """
        const React = require('react');
        const { renderToStaticMarkup } = require('react-dom/server');
        const { LearnerSessionLanding } = requireSource('view/app/LearnerSessionLanding.tsx');

        const landing = renderToStaticMarkup(
          React.createElement(LearnerSessionLanding, {
            language: 'ja',
            displayName: 'Japanese',
            lessonCount: 3,
            sessionPhase: 'landing',
            participantReady: true,
            onStartSession() {},
            onContinue() {},
          })
        );
        const complete = renderToStaticMarkup(
          React.createElement(LearnerSessionLanding, {
            language: 'ja',
            displayName: 'Japanese',
            lessonCount: 3,
            sessionPhase: 'complete',
            participantReady: true,
            onStartSession() {},
            onContinue() {},
          })
        );
        console.log(JSON.stringify({ landing, complete }));
        """,
    )

    assert "Next session" in result["landing"]
    assert "Ready for your next session?" in result["landing"]
    assert "Continue" in result["complete"]
    assert "Nice work" in result["complete"]
    assert "Take a break" not in result["complete"]


def test_lesson_loader_waits_for_participant_and_session_request():
    loader_source = (PROJECT_DIR / "view" / "app" / "useLessonLoader.ts").read_text(encoding="utf-8")
    app_source = (PROJECT_DIR / "view" / "app" / "TravellerMvpApp.tsx").read_text(encoding="utf-8")

    assert "sessionRequestId: number" in loader_source
    assert "sessionRequestId === 0" in loader_source
    assert "!participantId || sessionRequestId === 0" in loader_source
    assert "'idle'" in loader_source
    assert "sessionRequestId" in app_source
    assert "LearnerSessionLanding" in app_source
    assert "beginSession" in app_source
    assert "completeSession()" in app_source
    assert "PlanSelectionDebugPanel" in app_source


def test_session_queue_completion_returns_to_landing():
    app_source = (PROJECT_DIR / "view" / "app" / "TravellerMvpApp.tsx").read_text(encoding="utf-8")

    assert "sessionPhase === 'landing' || sessionPhase === 'complete'" in app_source
    assert "completeSession();" in app_source
    assert "onContinue={beginSession}" in app_source


def test_frontend_sends_lesson_stage_to_validation():
    active_step_source = (PROJECT_DIR / "view" / "app" / "useActiveLessonStep.ts").read_text(encoding="utf-8")
    validation_source = (PROJECT_DIR / "view" / "app" / "useValidationSession.ts").read_text(encoding="utf-8")
    api_types_source = (PROJECT_DIR / "view" / "api" / "validationTypes.ts").read_text(encoding="utf-8")

    assert "lessonStage: stepLesson.stage" in active_step_source
    assert "lessonStage: lesson.stage" in validation_source
    assert "lessonStage?: string" in api_types_source


def test_localhost_plan_selection_debug_panel_shows_engine_reasons():
    result = run_frontend_script(
        ["view/app/planSelectionDebug.ts", "view/app/PlanSelectionDebugPanel.tsx", "view/app/lessonSelection.ts", "view/app/lessonUrls.ts"],
        """
        const React = require('react');
        const { renderToStaticMarkup } = require('react-dom/server');
        const { planSelectionSummary } = requireSource('view/app/planSelectionDebug.ts');
        const { PlanSelectionDebugPanel } = requireSource('view/app/PlanSelectionDebugPanel.tsx');

        const lesson = {
          id: 'ja-card-first-hi-dialogue-practice',
          language: 'ja',
          title: 'Hello',
          stage: 'guided_scene_production',
          planPurpose: 'new',
          repairCategory: 'new',
          target: { id: 'ja-target-respond-hi', text: 'x', transliteration: 'x', meaning: 'hi' },
          frames: [],
          steps: [],
        };

        const html = renderToStaticMarkup(
          React.createElement(PlanSelectionDebugPanel, {
            lessons: [lesson],
            lessonTabs: [{ id: 'hello', label: 'Hello' }],
            planVersion: 2,
            sessionId: 'Bob:ja:mvp:seed',
          })
        );
        console.log(JSON.stringify({
          summary: planSelectionSummary(lesson),
          html,
        }));
        """,
    )

    assert "New i+1 anchor" in result["summary"]
    assert "Why these scenes?" in result["html"]
    assert "purpose=new" in result["html"]
    assert "ja-target-respond-hi" in result["html"]
