from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_scene_recall_recording_uses_auto_start_helper():
    helper_source = (PROJECT_DIR / "view" / "app" / "lessonStepHelpers.ts").read_text(encoding="utf-8")
    production_source = (PROJECT_DIR / "view" / "app" / "ProductionPracticeStep.tsx").read_text(encoding="utf-8")

    assert "export function recordingStartsAutomatically" in helper_source
    assert "recordingUsesPromptAudio(step)" in helper_source
    assert "step.type === 'scene_recall'" in helper_source
    assert "step.props.recordBeforeModelLine === true" in helper_source
    assert "recordingStartsAutomatically" in production_source
    assert "startMode={startsRecordingAutomatically ? 'auto' : 'manual'}" in production_source


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
    assert "fetchLearningPlan(language, sceneSet, stableOrderSeed(language, sceneSet))" in loader_source
    assert "lessonForPage(lessonPage, lessonTabs, lessons)" in loader_source
    assert "fetchLessons(language, lessonPage" not in loader_source
    assert "stableOrderSeed(language, sceneSet)" in loader_source
    assert "local-debug:${language}:${sceneSet}" in loader_source


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
    lesson_links_source = (PROJECT_DIR / "view" / "app" / "LessonAppLinks.tsx").read_text(encoding="utf-8")
    lesson_shell_source = (PROJECT_DIR / "view" / "app" / "TravellerLessonShell.tsx").read_text(encoding="utf-8")
    language_selection_source = (PROJECT_DIR / "view" / "app" / "LanguageSelectionApp.tsx").read_text(
        encoding="utf-8"
    )

    assert 'href="/admin/validation"' not in lesson_links_source
    assert "participantId" not in lesson_links_source
    assert "participantId" not in lesson_shell_source
    assert 'href="/admin/validation"' in language_selection_source
    assert "params.set('participant'" not in language_selection_source


def test_delayed_review_starts_from_first_backend_plan_tab():
    language_selection_source = (PROJECT_DIR / "view" / "app" / "LanguageSelectionApp.tsx").read_text(
        encoding="utf-8"
    )
    lesson_urls_source = (PROJECT_DIR / "view" / "app" / "lessonUrls.ts").read_text(encoding="utf-8")
    loader_source = (PROJECT_DIR / "view" / "app" / "useLessonLoader.ts").read_text(encoding="utf-8")

    assert "export const START_LESSON = 'start'" in lesson_urls_source
    assert "sceneSet === 'delayed' ? START_LESSON : 'hello'" in language_selection_source
    assert "lessonPage === START_LESSON ? null : lessonForPage" in loader_source
    assert "fallbackLessonPage(lessonTabs, lessonPage !== START_LESSON)" in loader_source
