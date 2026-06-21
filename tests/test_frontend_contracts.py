import json
import subprocess
import tempfile
import textwrap
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
TYPESCRIPT_PACKAGE = PROJECT_DIR / "view" / "node_modules" / "typescript"
PROMPTED_RECORDING_DIR = PROJECT_DIR / "view" / "components" / "prompted-recording"


def prompted_recording_source() -> str:
    parts = []
    for path in sorted(PROMPTED_RECORDING_DIR.rglob("*")):
        if path.suffix in {".ts", ".tsx"}:
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


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
        const anchorRecallLesson = { ...lesson, stage: 'same_day_anchor_recall' };

        console.log(JSON.stringify({
          recallFrameId: recordingFrameForProduction(lesson, recallStep).id,
          anchorFrameId: recordingFrameForProduction(lesson, anchorStep).id,
          anchorRecallFrameId: recordingFrameForProduction(anchorRecallLesson, recallStep).id,
        }));
        """,
    )

    assert result["recallFrameId"] == "line-1"
    assert result["anchorFrameId"] == "line-1"
    assert result["anchorRecallFrameId"] == "line-0"


def test_recording_timer_uses_five_second_countdown_bar():
    recording_source = prompted_recording_source()
    preview_source = (PROJECT_DIR / "view" / "app" / "RecordingCountdownPreview.tsx").read_text(encoding="utf-8")
    countdown_source = (PROJECT_DIR / "view" / "components" / "RecordingCountdownBar.tsx").read_text(
        encoding="utf-8"
    )
    production_source = (PROJECT_DIR / "view" / "app" / "ProductionPracticeStep.tsx").read_text(encoding="utf-8")
    registry_source = (PROJECT_DIR / "view" / "app" / "lessonStepRegistry.tsx").read_text(encoding="utf-8")
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")

    assert "step.mic?.maxDurationMs" in production_source
    assert "recordingMs={recordingMs}" in production_source
    assert "DEFAULT_RECORDING_MS = 5000" in recording_source
    assert "RecordingCountdownBar" in recording_source
    assert "isPaused={props.isSpeechActive}" in recording_source
    assert "rootMeanSquare(samples)" in recording_source
    assert "SPEECH_VISUAL_HOLD_MS = 500" in recording_source
    assert "clearHold()" in recording_source
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
    recording_source = prompted_recording_source()
    validation_source = (PROJECT_DIR / "view" / "app" / "useValidationSession.ts").read_text(encoding="utf-8")
    types_source = (PROJECT_DIR / "view" / "components" / "types.ts").read_text(encoding="utf-8")

    assert "export type CapturedRecording" in types_source
    assert "speechDetected?: boolean" in types_source
    assert "timedOutWithoutSpeech?: boolean" in types_source
    assert "recordingStoppedBy?: string" in (PROJECT_DIR / "view" / "api" / "validationTypes.ts").read_text(
        encoding="utf-8"
    )
    assert "startSpeechDetector(stream" in recording_source
    assert "rootMeanSquare(samples)" in recording_source
    assert "stoppedByRef.current = 'no_speech_timeout'" in recording_source
    assert "stoppedByRef.current = 'speech_completed'" in recording_source
    assert "args.recordingMs + 5000" in recording_source
    assert "speechDetected: recording.speechDetected" in validation_source
    assert "timedOutWithoutSpeech: recording.timedOutWithoutSpeech" in validation_source
    assert "recordingStoppedBy: recording.stoppedBy" in validation_source


def test_lesson_audio_errors_instead_of_browser_tts_fallback():
    audio_source = (PROJECT_DIR / "view" / "app" / "audioPlayback.ts").read_text(encoding="utf-8")
    hook_source = (PROJECT_DIR / "view" / "app" / "useAudioPlayback.ts").read_text(encoding="utf-8")
    scene_source = (PROJECT_DIR / "view" / "components" / "ScenePlayback.tsx").read_text(encoding="utf-8")
    recording_source = prompted_recording_source()
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
    assert "}, [autoplay, initialFrameIndex, playbackKey]);" in scene_playback_source
    assert "}, [autoplay, playableFrames]);" not in scene_playback_source


def test_scene_playback_pauses_for_frame_tutorials():
    scene_playback_source = (PROJECT_DIR / "view" / "components" / "ScenePlayback.tsx").read_text(
        encoding="utf-8"
    )

    assert "initialFrameId?: string | null;" in scene_playback_source
    assert "onActiveFrameChange?: (frame: SceneFrameData) => void;" in scene_playback_source
    assert "playableFrames.findIndex((frame) => frame.id === initialFrameId)" in scene_playback_source
    assert "onActiveFrameChange?.(activeFrame)" in scene_playback_source
    assert "tutorialForFrame?: (frame: SceneFrameData, index: number) => ScenePlaybackTutorial | null;" in scene_playback_source
    assert "const [pendingTutorial, setPendingTutorial]" in scene_playback_source
    assert "const tutorial = tutorialForFrame?.(frame, index) ?? null;" in scene_playback_source
    assert "setPendingTutorial({ index, tutorial });" in scene_playback_source
    assert "playFrameAudio(tutorialIndex);" in scene_playback_source
    assert "onDismissTutorial?.(pendingTutorial.tutorial.dismissId);" in scene_playback_source


def test_anchor_frame_role_tutorials_map_only_to_anchor_setup_frames():
    result = run_frontend_script(
        ["view/app/transferTutorialStorage.ts", "view/app/lessonTutorials.ts"],
        """
        const { anchorSceneTutorialForFrame } = requireSource('view/app/lessonTutorials.ts');

        const anchorLesson = { stage: 'guided_scene_production' };
        const transferLesson = { stage: 'same_day_transfer' };

        console.log(JSON.stringify({
          worldByIndex: anchorSceneTutorialForFrame(anchorLesson, { lineType: 'other' }, 0),
          worldByType: anchorSceneTutorialForFrame(anchorLesson, { lineIndex: 5, lineType: 'world_opener' }, 5),
          learnerByIndex: anchorSceneTutorialForFrame(anchorLesson, { lineType: 'other' }, 1),
          learnerByType: anchorSceneTutorialForFrame(anchorLesson, { lineIndex: 5, lineType: 'learner_target' }, 5),
          laterAnchor: anchorSceneTutorialForFrame(anchorLesson, { lineIndex: 2, lineType: 'world_response' }, 2),
          transferFrame: anchorSceneTutorialForFrame(transferLesson, { lineIndex: 0, lineType: 'world_opener' }, 0),
        }));
        """,
    )

    assert result["worldByIndex"]["dismissId"] == "anchor-world-role-frame"
    assert result["worldByIndex"]["title"] == "World role"
    assert "sets the scene" in result["worldByType"]["message"]
    assert result["learnerByIndex"]["dismissId"] == "anchor-learner-role-frame"
    assert result["learnerByType"]["title"] == "Your role"
    assert "Watch the mic bubble" in result["learnerByType"]["message"]
    assert result["laterAnchor"] is None
    assert result["transferFrame"] is None


def test_scene_frame_renders_icon_only_speech_bubbles():
    result = run_frontend_script(
        ["view/components/SpeechIconBubble.tsx", "view/components/SceneFrame.tsx"],
        """
        const React = require('react');
        const { renderToStaticMarkup } = require('react-dom/server');
        const { SceneFrame } = requireSource('view/components/SceneFrame.tsx');

        const withMic = renderToStaticMarkup(
          React.createElement(SceneFrame, {
            frame: {
              id: 'line-1',
              imageUrl: '/visuals/test.png',
              speechBubble: {
                kind: 'mic',
                anchorX: 0.35,
                anchorY: 0.18,
                side: 'bottom',
                rotationDegrees: 27,
              },
            },
            showCaption: false,
          })
        );
        const withoutBubble = renderToStaticMarkup(
          React.createElement(SceneFrame, {
            frame: { id: 'line-0', imageUrl: '/visuals/test.png' },
            showCaption: false,
          })
        );
        console.log(JSON.stringify({ withMic, withoutBubble }));
        """,
    )

    assert "speech-icon-bubble--mic" in result["withMic"]
    assert "active-speaker-glow" not in result["withMic"]
    assert "left:35%" in result["withMic"]
    assert "top:18%" in result["withMic"]
    assert "--speech-bubble-rotate:27deg" in result["withMic"]
    assert "--speech-bubble-icon-rotate:-27deg" in result["withMic"]
    assert "speech-icon-bubble" not in result["withoutBubble"]
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")
    assert ".scene-frame-media {\n  aspect-ratio: 3 / 2;" in styles_source


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


def test_lesson_landing_offers_optional_daily_notification_reminder():
    result = run_frontend_script(
        ["view/app/dailyReminderNotifications.ts"],
        """
        const {
          DEFAULT_DAILY_REMINDER_TIME,
          DAILY_REMINDER_STORAGE_KEY,
          canUsePushReminders,
          loadDailyReminderSettings,
          reminderPermission,
          pushReminderUnavailableMessage,
        } = requireSource('view/app/dailyReminderNotifications.ts');

        global.localStorage = {
          value: null,
          getItem(key) {
            return key === DAILY_REMINDER_STORAGE_KEY ? this.value : null;
          },
          setItem(key, value) {
            if (key === DAILY_REMINDER_STORAGE_KEY) this.value = value;
          },
        };

        console.log(JSON.stringify({
          defaultTime: DEFAULT_DAILY_REMINDER_TIME,
          defaultSettings: loadDailyReminderSettings(),
          unsupportedPermission: reminderPermission(),
          canUsePush: canUsePushReminders(),
          unavailableMessage: pushReminderUnavailableMessage(),
        }));
        """,
    )
    selection_source = (PROJECT_DIR / "view" / "app" / "LanguageSelectionApp.tsx").read_text(encoding="utf-8")
    landing_source = (PROJECT_DIR / "view" / "app" / "LearnerSessionLanding.tsx").read_text(encoding="utf-8")
    app_source = (PROJECT_DIR / "view" / "app" / "TravellerMvpApp.tsx").read_text(encoding="utf-8")
    prompt_source = (PROJECT_DIR / "view" / "app" / "DailyReminderPrompt.tsx").read_text(encoding="utf-8")
    api_source = (PROJECT_DIR / "view" / "api" / "reminders.ts").read_text(encoding="utf-8")
    service_worker_source = (PROJECT_DIR / "view" / "app" / "public" / "service-worker.js").read_text(encoding="utf-8")
    reminder_source = (PROJECT_DIR / "view" / "app" / "dailyReminderNotifications.ts").read_text(encoding="utf-8")
    pages_source = (PROJECT_DIR / "backend" / "app" / "routes" / "pages.py").read_text(encoding="utf-8")

    assert result["defaultTime"] == "22:00"
    assert result["defaultSettings"] == {"enabled": False, "time": "22:00"}
    assert result["unsupportedPermission"] == "unsupported"
    assert result["canUsePush"] is False
    assert result["unavailableMessage"] == "Push notifications are unavailable in this browser."
    assert "DailyReminderPrompt" not in selection_source
    assert "DailyReminderPrompt" in landing_source
    assert "participantId={participantId}" in app_source
    assert "requestReminderPermission" in prompt_source
    assert "Reminder server is missing Web Push dependencies" in prompt_source
    assert "Reminder worker is unavailable" in prompt_source
    assert "Browser push registration failed" in prompt_source
    assert "Turn it off here anytime." in prompt_source
    assert "registerReminderServiceWorker" in prompt_source
    assert "saveReminderSubscription" in prompt_source
    assert "reminderTimezone()" in prompt_source
    assert "window.isSecureContext === true" in reminder_source
    assert "navigator.serviceWorker.register('/service-worker.js')" in reminder_source
    assert "navigator.serviceWorker.ready" in reminder_source
    assert '"/service-worker.js"' in pages_source
    assert "body.detail" in api_source
    assert "/api/reminders/subscriptions" in api_source
    assert "skipWaiting" in service_worker_source
    assert "clients.claim" in service_worker_source
    assert "showNotification" in service_worker_source
    assert "audio-language-daily-reminder" in service_worker_source


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


def test_speech_bubble_debug_page_uses_hi_intro_scene_frame_overlay():
    main_source = (PROJECT_DIR / "view" / "app" / "main.tsx").read_text(encoding="utf-8")
    debug_source = (PROJECT_DIR / "view" / "app" / "DebugSpeechBubblePage.tsx").read_text(encoding="utf-8")
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")

    assert "if (pathname === '/debug/speech-bubbles')" in main_source
    assert "HI_INTRO_LESSON_ID = 'ja-card-first-hi-dialogue-practice'" in debug_source
    assert "fetchLearningPlan('ja', 'mvp', 'speech-bubble-debug:ja:mvp')" in debug_source
    assert "<SceneFrame frame={frame} isActive showCaption={false}" in debug_source
    assert '<SpeechIconBubble kind="speaker"' in debug_source
    assert '<SpeechIconBubble kind="mic"' in debug_source
    assert "withDebugBubbleOverlay" in debug_source
    assert "hiIntroDebugBubble(frame)" in debug_source
    assert "anchorX: 0.36" in debug_source
    assert "anchorX: 0.66" in debug_source
    assert "speechBubble:" in debug_source
    assert "rotationDegrees: isLearner ? -12 : 12" in debug_source
    assert "bubbleLabel(frame)" in debug_source
    assert ".speech-bubble-component-preview" in styles_source
    assert ".speech-bubble-debug-grid" in styles_source
    assert "aspect-ratio: 3 / 2" in styles_source
    assert "height: 38px" in styles_source
    assert "content: \"bubble\"" not in styles_source
    assert "speech-bubble-anchor::before" not in styles_source


def test_speech_bubble_editor_contact_sheet_drags_and_saves_overrides():
    main_source = (PROJECT_DIR / "view" / "app" / "main.tsx").read_text(encoding="utf-8")
    editor_source = (PROJECT_DIR / "view" / "app" / "DebugSpeechBubbleEditorPage.tsx").read_text(encoding="utf-8")
    api_source = (PROJECT_DIR / "view" / "api" / "lessons.ts").read_text(encoding="utf-8")
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")

    assert "if (pathname === '/debug/speech-bubble-editor')" in main_source
    assert "fetchLearningPlan(LANGUAGE, SCENE_SET, 'speech-bubble-editor:ja:mvp')" in editor_source
    assert "fetchLearningPlan(LANGUAGE, DELAYED_SCENE_SET, 'speech-bubble-editor:ja:delayed')" in editor_source
    assert "setLessons([...mvpPlan.lessons, ...delayedPlan.lessons])" in editor_source
    assert "setBubbleScale(saved.bubbleScale ?? DEFAULT_BUBBLE_SCALE)" in editor_source
    assert "editorFrameWidth: APP_FRAME_WIDTH" in editor_source
    assert "app-size MVP, transfer, and delayed review frames" in editor_source
    assert "overrides[key] ?? defaultOverride(lesson, frame)" in editor_source
    assert "lineIndex === 1 ? 'mic' : 'speaker'" in editor_source
    assert "onPointerDown={startDrag}" in editor_source
    assert "onPointerMove={drag}" in editor_source
    assert "SpeechBubbleOverlay" in editor_source
    assert 'className="scene-frame active speech-bubble-editor-scene-frame"' in editor_source
    assert 'className="scene-frame-media"' in editor_source
    assert "const speechBubble = { ...override, scale: bubbleScale }" in editor_source
    assert "rotationDegrees" in editor_source
    assert "Bubble scale" in editor_source
    assert "saveSpeechBubbleOverrides(payload)" in editor_source
    assert "JSON.stringify(payload, null, 2)" in editor_source
    assert "fetch('/api/debug/speech-bubble-overrides'" in api_source
    assert ".speech-bubble-editor-sheet" in styles_source
    assert "grid-template-columns: 920px" in styles_source
    assert "width: 920px" in styles_source
    assert ".speech-bubble-editor-image" not in styles_source
    assert "--speech-editor-bubble-scale" not in styles_source


def test_speech_icon_bubble_renders_speaker_and_mic_variants():
    result = run_frontend_script(
        ["view/components/SpeechIconBubble.tsx"],
        """
        const React = require('react');
        const { renderToStaticMarkup } = require('react-dom/server');
        const { SpeechIconBubble } = requireSource('view/components/SpeechIconBubble.tsx');

        console.log(JSON.stringify({
          speaker: renderToStaticMarkup(React.createElement(SpeechIconBubble, {
            kind: 'speaker',
            tipPosition: 'right',
            tipTilt: 'right',
            rotationDegrees: 31,
          })),
          mic: renderToStaticMarkup(React.createElement(SpeechIconBubble, {
            kind: 'mic',
            tipPosition: 'left',
            tipTilt: 'left',
          })),
        }));
        """,
    )

    assert "speech-icon-bubble--speaker" in result["speaker"]
    assert "speech-icon-bubble--tip-right" in result["speaker"]
    assert "speech-icon-bubble--tip-tilt-right" in result["speaker"]
    assert "--speech-bubble-rotate:31deg" in result["speaker"]
    assert "--speech-bubble-icon-rotate:-31deg" in result["speaker"]
    assert "World speaking" in result["speaker"]
    assert "speech-icon-bubble--mic" in result["mic"]
    assert "speech-icon-bubble--tip-left" in result["mic"]
    assert "speech-icon-bubble--tip-tilt-left" in result["mic"]
    assert "Learner speaking" in result["mic"]
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")
    assert "transform: rotate(var(--speech-bubble-rotate, 0deg))" in styles_source
    assert "scale(var(--speech-bubble-scale, 1))" in styles_source
    assert "--speech-bubble-rotate: -12deg" in styles_source
    assert "--speech-bubble-rotate: 12deg" in styles_source
    assert "left: var(--speech-bubble-tip-left" not in styles_source


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
        [
            "view/api/reminders.ts",
            "view/app/dailyReminderNotifications.ts",
            "view/app/DailyReminderPrompt.tsx",
            "view/app/LearnerSessionLanding.tsx",
        ],
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
            planState: 'ready',
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
            planState: 'ready',
            participantReady: true,
            onStartSession() {},
            onContinue() {},
          })
        );
        const emptyReady = renderToStaticMarkup(
          React.createElement(LearnerSessionLanding, {
            language: 'ja',
            displayName: 'Japanese',
            lessonCount: 0,
            sessionPhase: 'landing',
            planState: 'ready',
            participantReady: true,
            onStartSession() {},
            onContinue() {},
          })
        );
        const loading = renderToStaticMarkup(
          React.createElement(LearnerSessionLanding, {
            language: 'ja',
            displayName: 'Japanese',
            lessonCount: 0,
            sessionPhase: 'landing',
            planState: 'loading',
            participantReady: true,
            onStartSession() {},
            onContinue() {},
          })
        );
        console.log(JSON.stringify({ landing, complete, emptyReady, loading }));
        """,
    )

    assert "Next session" in result["landing"]
    assert "Ready for your next session?" in result["landing"]
    assert "Continue" in result["complete"]
    assert "Nice work" in result["complete"]
    assert "Nothing due, come back tomorrow!" in result["emptyReady"]
    assert "Preparing your next session..." in result["loading"]
    assert "Next session" not in result["emptyReady"]
    assert "Take a break" not in result["complete"]


def test_lesson_loader_waits_for_participant_and_session_request():
    loader_source = (PROJECT_DIR / "view" / "app" / "useLessonLoader.ts").read_text(encoding="utf-8")
    app_source = (PROJECT_DIR / "view" / "app" / "TravellerMvpApp.tsx").read_text(encoding="utf-8")

    assert "sessionRequestId: number" in loader_source
    assert "sessionRequestId === 0" in loader_source
    assert "!participantId || sessionRequestId === 0" in loader_source
    assert "'idle'" in loader_source
    assert "FALLBACK_LESSON" not in loader_source
    assert "sessionRequestId" in app_source
    assert "LearnerSessionLanding" in app_source
    assert "beginSession" in app_source
    assert "initialLessonPageFromUrl" in app_source
    assert "initialLessonPageFromUrl.current === START_LESSON" in app_source
    assert "setSessionPhase('running');" in app_source
    assert "selectLessonPage(START_LESSON);" in app_source
    assert "sessionPhase === 'running'" in loader_source
    assert "completeSession()" in app_source
    assert "PlanSelectionDebugPanel" in app_source


def test_session_queue_completion_shows_scorecard_with_next_lesson_action():
    app_source = (PROJECT_DIR / "view" / "app" / "TravellerMvpApp.tsx").read_text(encoding="utf-8")
    scorecard_source = (PROJECT_DIR / "view" / "app" / "ScorecardView.tsx").read_text(encoding="utf-8")
    validation_api_source = (PROJECT_DIR / "view" / "api" / "validation.ts").read_text(encoding="utf-8")
    validation_types_source = (PROJECT_DIR / "view" / "api" / "validationTypes.ts").read_text(encoding="utf-8")

    assert "completeSession();" in app_source
    assert "if (appView === 'scorecard')" in app_source
    assert "onNextLesson={sessionPhase === 'complete' ? beginSession : null}" in app_source
    assert "const canBeginSession = loadState === 'ready' && lessons.length > 0 && scorecardState !== 'loading';" in app_source
    assert "Loading your next session..." in app_source
    assert "planState={loadState === 'idle' ? 'loading' : loadState}" in app_source
    assert "onContinue={beginSession}" in app_source
    assert "disabled={state === 'loading'}" in scorecard_source
    assert "Scoring..." in scorecard_source
    assert "Mark correct" in scorecard_source
    assert "Mark incorrect" in scorecard_source
    assert "const nextIsCorrect = !isCorrect" in scorecard_source
    assert "onOverride(attempt.attemptId, nextIsCorrect)" in scorecard_source
    assert "Corrected by learner" in scorecard_source
    assert "scoreOverrideErrorMessage" in scorecard_source
    assert "overrideValidationAttemptScore" in scorecard_source
    assert "score-override" in validation_api_source
    assert "validationApiErrorMessage" in validation_api_source
    assert "learnerOverride" in validation_types_source
    assert "overridesAttemptScore" in validation_types_source


def test_scorecard_anchor_review_and_relearn_contracts():
    app_source = (PROJECT_DIR / "view" / "app" / "TravellerMvpApp.tsx").read_text(encoding="utf-8")
    loader_source = (PROJECT_DIR / "view" / "app" / "useLessonLoader.ts").read_text(encoding="utf-8")
    production_source = (PROJECT_DIR / "view" / "app" / "ProductionPracticeStep.tsx").read_text(encoding="utf-8")
    scorecard_source = (PROJECT_DIR / "view" / "app" / "ScorecardView.tsx").read_text(encoding="utf-8")
    helper_source = (PROJECT_DIR / "view" / "app" / "lessonStepHelpers.ts").read_text(encoding="utf-8")
    shell_source = (PROJECT_DIR / "view" / "app" / "TravellerLessonShell.tsx").read_text(encoding="utf-8")
    lessons_api_source = (PROJECT_DIR / "view" / "api" / "lessons.ts").read_text(encoding="utf-8")
    validation_types_source = (PROJECT_DIR / "view" / "api" / "validationTypes.ts").read_text(encoding="utf-8")

    assert "anchorLessonPage?: string" in validation_types_source
    assert "anchorLessonId?: string" in validation_types_source
    assert "View anchor" in scorecard_source
    assert "Relearn" not in scorecard_source
    assert "scorecard-learner-audio" not in scorecard_source
    assert "target.targetAudioUrl" not in scorecard_source
    assert "validationAttemptAudioUrl(sessionId, attempt.attemptId)" in scorecard_source
    assert "lessonSupportsRelearn" in helper_source
    assert "guided_scene_production" in helper_source
    assert "same_day_anchor_recall" in helper_source
    assert "onRelearn={relearnAction}" in app_source
    assert "lessonSupportsRelearn(stepLesson) ? handleRelearn : undefined" in app_source
    assert "onRelearn={onRelearn}" in shell_source
    assert "phase === 'done' && onStepComplete" in production_source
    assert "isRelearning ? 'Adding...' : 'Relearn'" in production_source
    assert "POST" in lessons_api_source
    assert "/api/learning-engine/relearn-target" in lessons_api_source
    assert "insertLessonBundleAfter" in loader_source
    assert "insertBundleWithRecallGap" in loader_source
    assert "interveningItem" in loader_source
    assert "const currentIndex = lessonTabs.findIndex((tab) => tab.id === lessonPage)" in app_source
    assert "ScorecardAnchorReview" in app_source
    assert "<h1>Anchor scene</h1>" in app_source
    assert "<h1>{lesson?.title ?? 'Anchor scene'}</h1>" not in app_source
    assert "<ScenePlayback frames={withAssetUrls(lesson)?.frames ?? []} autoplay />" in app_source
    assert "fetchLessons(language, target.anchorLessonPage, sceneSet)" in app_source
    assert "relearnTarget({" in app_source
    assert "selectLessonPage(firstInsertedPage)" in app_source


def test_learn_and_admin_pages_support_phrase_recommendations():
    app_source = (PROJECT_DIR / "view" / "app" / "TravellerMvpApp.tsx").read_text(encoding="utf-8")
    button_source = (PROJECT_DIR / "view" / "app" / "RecommendPhraseButton.tsx").read_text(encoding="utf-8")
    api_source = (PROJECT_DIR / "view" / "api" / "recommendedPhrases.ts").read_text(encoding="utf-8")
    admin_header_source = (PROJECT_DIR / "view" / "app" / "admin" / "AdminHeader.tsx").read_text(encoding="utf-8")
    admin_dialog_source = (PROJECT_DIR / "view" / "app" / "admin" / "RecommendedPhrasesDialog.tsx").read_text(
        encoding="utf-8"
    )
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")

    assert "RecommendPhraseButton" in app_source
    assert app_source.count("<RecommendPhraseButton />") == 1
    assert "learn-page-bottom-actions" in app_source
    assert "Recommend phrases" in button_source
    assert "className=\"session-primary-action\"" in button_source
    assert "maxLength={MAX_RECOMMENDED_PHRASE_LENGTH}" in button_source
    assert "saveRecommendedPhrase(phrase)" in button_source
    assert "/api/recommended-phrases" in api_source
    assert "/api/admin/recommended-phrases" in api_source
    assert "RecommendedPhrasesDialog" in admin_header_source
    assert "Recommended phrases" in admin_dialog_source
    assert "fetchRecommendedPhraseSummary" in admin_dialog_source
    assert "Previous" in admin_dialog_source
    assert "Next" in admin_dialog_source
    assert ".learn-page-bottom-actions" in styles_source
    assert "justify-content: center" in styles_source
    assert ".recommend-phrase-open" not in styles_source
    assert ".recommend-phrase-dialog" in styles_source
    assert ".recommended-phrases-dialog" in styles_source


def test_scorecard_links_to_read_only_user_history():
    main_source = (PROJECT_DIR / "view" / "app" / "main.tsx").read_text(encoding="utf-8")
    scorecard_source = (PROJECT_DIR / "view" / "app" / "ScorecardView.tsx").read_text(encoding="utf-8")
    history_source = (PROJECT_DIR / "view" / "app" / "admin" / "UserHistoryApp.tsx").read_text(encoding="utf-8")
    progress_source = (PROJECT_DIR / "view" / "app" / "admin" / "UserProgress.tsx").read_text(encoding="utf-8")
    summary_source = (PROJECT_DIR / "view" / "app" / "admin" / "summary.ts").read_text(encoding="utf-8")
    validation_api_source = (PROJECT_DIR / "view" / "api" / "validation.ts").read_text(encoding="utf-8")
    validation_types_source = (PROJECT_DIR / "view" / "api" / "validationTypes.ts").read_text(encoding="utf-8")

    assert "History" in scorecard_source
    assert 'href="/history"' in scorecard_source
    assert "/history?participant=" not in scorecard_source
    assert "pathname === '/history'" in main_source
    assert "fetchValidationHistorySummary(participantId)" in history_source
    assert "participantFromUrl" not in history_source
    assert "localStorage.getItem(PARTICIPANT_STORAGE_KEY)" in history_source
    assert "isReadOnly" in progress_source
    assert "phrasesForUser" in summary_source
    assert "scenePhraseGroupsForUser" not in summary_source
    assert "sceneKind: ValidationSceneKind" in validation_types_source
    assert "/api/validation/history/summary" in validation_api_source


def test_admin_user_summary_splits_one_participant_by_language():
    result = run_frontend_script(
        ["view/app/admin/summary.ts"],
        """
        const {
          usersFromSummary,
          daysForUser,
          phrasesForUser,
        } = requireSource('view/app/admin/summary.ts');
        const summary = {
          sessions: [
            {
              sessionId: 'ja-day',
              participantId: 'Friend',
              language: 'ja',
              sceneSet: 'mvp',
              createdAt: '2026-01-01T00:00:00Z',
              eventCount: 0,
              attemptCount: 1,
              scoredAttemptCount: 1,
              rememberedAttemptCount: 1,
            },
            {
              sessionId: 'es-day',
              participantId: 'Friend',
              language: 'es',
              sceneSet: 'mvp',
              createdAt: '2026-01-02T00:00:00Z',
              eventCount: 0,
              attemptCount: 1,
              scoredAttemptCount: 0,
              rememberedAttemptCount: 0,
            },
          ],
          targets: [
            {
              language: 'ja',
              sceneSet: 'mvp',
              sceneKind: 'anchor',
              sceneKindLabel: 'Anchor',
              targetId: 'shared',
              expectedTransliteration: 'ja phrase',
              attemptCount: 1,
              scoredAttemptCount: 1,
              rememberedAttemptCount: 1,
              sessions: [{ type: 'recording', sessionId: 'ja-day', participantId: 'Friend', scoreStatus: 'exact' }],
            },
            {
              language: 'ja',
              sceneSet: 'mvp',
              sceneKind: 'transfer',
              sceneKindLabel: 'Transfer',
              targetId: 'shared',
              expectedTransliteration: 'ja phrase',
              attemptCount: 1,
              scoredAttemptCount: 0,
              rememberedAttemptCount: 0,
              sessions: [{ type: 'recording', sessionId: 'ja-day', participantId: 'Friend', scoreStatus: 'missed' }],
            },
            {
              language: 'es',
              sceneSet: 'mvp',
              sceneKind: 'anchor',
              sceneKindLabel: 'Anchor',
              targetId: 'shared',
              expectedTransliteration: 'es phrase',
              attemptCount: 1,
              scoredAttemptCount: 0,
              rememberedAttemptCount: 0,
              sessions: [{ type: 'recording', sessionId: 'es-day', participantId: 'Friend', scoreStatus: 'unscored' }],
            },
          ],
        };
        const users = usersFromSummary(summary);
        console.log(JSON.stringify({
          users,
          jaDays: daysForUser(summary.sessions, 'Friend', 'ja').map((day) => day.sessionId),
          esDays: daysForUser(summary.sessions, 'Friend', 'es').map((day) => day.sessionId),
          jaPhrases: phrasesForUser(summary.targets, 'Friend', 'ja').map((phrase) => phrase.phrase),
          jaAttemptCount: phrasesForUser(summary.targets, 'Friend', 'ja')[0].attemptsBySession['ja-day'].length,
          allPhrases: phrasesForUser(summary.targets, 'Friend').map((phrase) => phrase.phrase).sort(),
        }));
        """,
    )

    assert [user["displayName"] for user in result["users"]] == ["Friend-es", "Friend-ja"]
    assert [user["userKey"] for user in result["users"]] == ["Friend::es", "Friend::ja"]
    assert result["jaDays"] == ["ja-day"]
    assert result["esDays"] == ["es-day"]
    assert result["jaPhrases"] == ["ja phrase"]
    assert result["jaAttemptCount"] == 2
    assert result["allPhrases"] == ["es phrase", "ja phrase"]


def test_admin_attempt_cells_select_tries_with_status_pills_and_open_scene_page():
    main_source = (PROJECT_DIR / "view" / "app" / "main.tsx").read_text(encoding="utf-8")
    attempt_cells_source = (PROJECT_DIR / "view" / "app" / "admin" / "AttemptCells.tsx").read_text(encoding="utf-8")
    try_cell_source = (PROJECT_DIR / "view" / "app" / "admin" / "RecordingCell.tsx").read_text(encoding="utf-8")
    progress_source = (PROJECT_DIR / "view" / "app" / "admin" / "UserProgress.tsx").read_text(encoding="utf-8")
    scene_page_source = (PROJECT_DIR / "view" / "app" / "admin" / "AdminScenePage.tsx").read_text(encoding="utf-8")
    admin_source = (PROJECT_DIR / "view" / "app" / "admin" / "AdminValidationApp.tsx").read_text(encoding="utf-8")
    api_types_source = (PROJECT_DIR / "view" / "api" / "validationTypes.ts").read_text(encoding="utf-8")
    styles_source = (PROJECT_DIR / "view" / "app" / "styles.css").read_text(encoding="utf-8")

    assert "sortedAttempts" in attempt_cells_source
    assert "TryCell" in attempt_cells_source
    assert "try-pills" in attempt_cells_source
    assert "try-pill" in attempt_cells_source
    assert "tryPassed(item)" in attempt_cells_source
    assert "tryTypeAbbreviation(item)" in attempt_cells_source
    assert "if (typeName === 'Anchor transfer') return 'AT';" in attempt_cells_source
    assert "tryKind === 'anchor_transfer'" in attempt_cells_source
    assert 'aria-label={`${tryTypeName(item)} try`}' in attempt_cells_source
    assert "Try {index + 1}" not in attempt_cells_source
    assert "aria-pressed={index === activeTryIndex}" in attempt_cells_source
    assert "onClick={() => setTryIndex(index)}" in attempt_cells_source
    assert "onNextTry" not in attempt_cells_source
    assert "recording?.scorePassed === true" in try_cell_source
    assert "choice ? choice.choiceCorrect" not in try_cell_source
    assert "View scene" in try_cell_source
    assert "href={sceneUrl}" in try_cell_source
    assert "if (lessonPage) params.set('lessonPage', lessonPage)" in try_cell_source
    assert "returnTo" in try_cell_source
    assert "<dt>Type</dt>" in try_cell_source
    assert "<dt>Choice</dt>" in try_cell_source
    assert "<dt>Recording</dt>" in try_cell_source
    assert "<dt>Actions</dt>" in try_cell_source
    assert "choiceId" in try_cell_source
    assert "Delete record" in try_cell_source
    assert "handleTryClick" not in try_cell_source
    assert "Next" not in try_cell_source
    assert "attempt.tryKindLabel" in try_cell_source
    assert "phrasesForUser(summary.targets, participantId, language)" in progress_source
    assert "sceneGroups.map" not in progress_source
    assert "ScenePreviewDialog" not in progress_source
    assert "pathname === '/scene'" in main_source
    assert "loadScene(language, lessonPage, lessonId, sceneSet)" in scene_page_source
    assert "fetchLessons(language, lessonPage, sceneSet)" in scene_page_source
    assert "fetchLessons(language, null, sceneSet)" in scene_page_source
    assert "initialFrameId={frameId}" in scene_page_source
    assert "autoplay={!frameId}" in scene_page_source
    assert "onActiveFrameChange={updateFrameInUrl}" in scene_page_source
    assert "url.searchParams.set('frame', frame.id)" in scene_page_source
    assert "window.history.replaceState({}, '', url)" in scene_page_source
    assert "<h1>Scene</h1>" not in scene_page_source
    assert "<span>Scene</span>" not in scene_page_source
    assert "admin-scene-actions" in scene_page_source
    assert "lesson?.title" not in scene_page_source
    assert "href={returnTo}" in scene_page_source
    assert ".admin-scene-page .scene-playback" in styles_source
    assert "width: min(100%, calc((100vh - 110px) * 1.5));" in styles_source
    assert "adminUserPath(user)" in admin_source
    assert "tryKind?: ValidationTryKind" in api_types_source
    assert "lessonStage?: string" in api_types_source


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
