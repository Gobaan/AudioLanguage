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
    assert "selectLessonForPage(lessonPage, lessonTabs, lessons)" in loader_source
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

    assert result["mvp"] == "/learn?language=ja&lesson=hello"
    assert result["delayed"] == "/learn?language=ja&lesson=start&scene_set=delayed"
    assert "participant" not in result["mvp"]
    assert "participant" not in result["delayed"]


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
