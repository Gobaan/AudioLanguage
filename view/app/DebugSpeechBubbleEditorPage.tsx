import type { PointerEvent } from 'react';
import { useEffect, useMemo, useState } from 'react';

import { fetchLearningPlan, fetchSpeechBubbleOverrides, saveSpeechBubbleOverrides } from '../api/lessons';
import { SpeechBubbleOverlay } from '../components';
import type { Lesson, SceneFrameData } from '../components';
import { assetUrl } from './lessonUrls';

type LoadState = 'loading' | 'ready' | 'error';
type SaveState = 'idle' | 'saving' | 'saved' | 'error';

export type SpeechBubbleOverride = {
  lessonId: string;
  frameId: string;
  lineIndex: number;
  imageUrl?: string | null;
  kind: 'mic' | 'speaker';
  anchorX: number;
  anchorY: number;
  rotationDegrees: number;
  side: string;
  tipPosition: 'left' | 'center' | 'right';
  tipTilt: 'left' | 'none' | 'right';
};

export type SpeechBubbleOverridePayload = {
  language: string;
  sceneSet: string;
  bubbleScale: number;
  editorFrameWidth?: number;
  frames: SpeechBubbleOverride[];
};

type EditorFrame = {
  lesson: Lesson;
  frame: SceneFrameData;
  override: SpeechBubbleOverride;
};

const LANGUAGE = 'ja';
const SCENE_SET = 'mvp';
const DELAYED_SCENE_SET = 'delayed';
const DEFAULT_BUBBLE_SCALE = 1;
const APP_FRAME_WIDTH = 896;

export function DebugSpeechBubbleEditorPage() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [overrides, setOverrides] = useState<Record<string, SpeechBubbleOverride>>({});
  const [bubbleScale, setBubbleScale] = useState(DEFAULT_BUBBLE_SCALE);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [saveState, setSaveState] = useState<SaveState>('idle');
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    let isCurrent = true;
    setLoadState('loading');

    Promise.all([
      fetchLearningPlan(LANGUAGE, SCENE_SET, 'speech-bubble-editor:ja:mvp'),
      fetchLearningPlan(LANGUAGE, DELAYED_SCENE_SET, 'speech-bubble-editor:ja:delayed'),
      fetchSpeechBubbleOverrides().catch(() => ({
        language: LANGUAGE,
        sceneSet: SCENE_SET,
        bubbleScale: DEFAULT_BUBBLE_SCALE,
        frames: [],
      })),
    ])
      .then(([mvpPlan, delayedPlan, saved]) => {
        if (!isCurrent) return;
        setLessons([...mvpPlan.lessons, ...delayedPlan.lessons]);
        setBubbleScale(saved.bubbleScale ?? DEFAULT_BUBBLE_SCALE);
        setOverrides(Object.fromEntries(saved.frames.map((item) => [overrideKey(item.lessonId, item.frameId), item])));
        setLoadState('ready');
      })
      .catch(() => {
        if (!isCurrent) return;
        setLoadState('error');
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  const editorFrames = useMemo(() => {
    return lessons.flatMap((lesson) =>
      lesson.frames.map((frame) => {
        const key = overrideKey(lesson.id, frame.id);
        return {
          lesson,
          frame: { ...frame, imageUrl: frame.imageUrl ? assetUrl(frame.imageUrl) : frame.imageUrl },
          override: overrides[key] ?? defaultOverride(lesson, frame),
        };
      }),
    );
  }, [lessons, overrides]);

  const payload = useMemo<SpeechBubbleOverridePayload>(
    () => ({
      language: LANGUAGE,
      sceneSet: SCENE_SET,
      bubbleScale,
      editorFrameWidth: APP_FRAME_WIDTH,
      frames: editorFrames.map((item) => item.override),
    }),
    [bubbleScale, editorFrames],
  );

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading speech bubble editor" />;
  }

  if (loadState === 'error') {
    return (
      <section className="speech-bubble-editor-page" aria-label="Speech bubble editor">
        <p className="audio-error" role="alert">
          Could not load the speech bubble editor.
        </p>
      </section>
    );
  }

  function updateOverride(next: SpeechBubbleOverride) {
    setSaveState('idle');
    setOverrides((current) => ({ ...current, [overrideKey(next.lessonId, next.frameId)]: next }));
  }

  function save() {
    setSaveState('saving');
    saveSpeechBubbleOverrides(payload)
      .then((result) => {
        setSaveState('saved');
        setSaveMessage(`Saved ${result.frames} frames to ${result.path}`);
      })
      .catch(() => {
        setSaveState('error');
        setSaveMessage('Save failed.');
      });
  }

  return (
    <section className="speech-bubble-editor-page" aria-label="Speech bubble editor">
      <header className="speech-bubble-editor-toolbar">
        <div>
          <span>Debug</span>
          <h1>Speech Bubble Contact Sheet</h1>
          <p>Drag bubbles on app-size MVP, transfer, and delayed review frames. Frame 0 and 2 use speaker; frame 1 uses mic.</p>
        </div>
        <label>
          Bubble scale
          <input
            max="3"
            min="0.5"
            onChange={(event) => setBubbleScale(Number(event.currentTarget.value))}
            step="0.01"
            type="range"
            value={bubbleScale}
          />
          <output>{Math.round(bubbleScale * 100)}%</output>
        </label>
        <button disabled={saveState === 'saving'} onClick={save} type="button">
          {saveState === 'saving' ? 'Saving' : 'Save JSON'}
        </button>
        <span className={`speech-bubble-editor-save speech-bubble-editor-save--${saveState}`}>
          {saveMessage || 'Unsaved edits stay in this browser until saved.'}
        </span>
      </header>

      <div className="speech-bubble-editor-sheet">
        {editorFrames.map((item) => (
          <SpeechBubbleEditorCard
            bubbleScale={bubbleScale}
            frame={item.frame}
            key={`${item.lesson.id}:${item.frame.id}`}
            lesson={item.lesson}
            onChange={updateOverride}
            override={item.override}
          />
        ))}
      </div>

      <textarea
        className="speech-bubble-editor-json"
        readOnly
        value={JSON.stringify(payload, null, 2)}
        aria-label="Speech bubble override JSON preview"
      />
    </section>
  );
}

type SpeechBubbleEditorCardProps = {
  lesson: Lesson;
  frame: SceneFrameData;
  override: SpeechBubbleOverride;
  bubbleScale: number;
  onChange: (override: SpeechBubbleOverride) => void;
};

function SpeechBubbleEditorCard({ lesson, frame, override, bubbleScale, onChange }: SpeechBubbleEditorCardProps) {
  const speechBubble = { ...override, scale: bubbleScale };

  function moveBubble(event: PointerEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    onChange({
      ...override,
      anchorX: clamp((event.clientX - rect.left) / rect.width),
      anchorY: clamp((event.clientY - rect.top) / rect.height),
    });
  }

  function startDrag(event: PointerEvent<HTMLDivElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    moveBubble(event);
  }

  function drag(event: PointerEvent<HTMLDivElement>) {
    if (event.buttons !== 1) return;
    moveBubble(event);
  }

  return (
    <article className="speech-bubble-editor-card">
      <figure className="scene-frame active speech-bubble-editor-scene-frame">
        <div
          className="scene-frame-media"
          onPointerDown={startDrag}
          onPointerMove={drag}
          role="img"
          aria-label={`${lesson.id} ${frame.id}`}
        >
          {frame.imageUrl ? (
            <img src={frame.imageUrl} alt={frame.title || frame.id} draggable={false} />
          ) : (
            <div className="scene-frame-placeholder" aria-label={`${lesson.id} ${frame.id}`} />
          )}
          <SpeechBubbleOverlay bubble={speechBubble} />
        </div>
      </figure>
      <div className="speech-bubble-editor-card-meta">
        <strong>{lesson.id}</strong>
        <span>
          Frame {override.lineIndex}: {override.kind}
        </span>
        <label>
          Rotation
          <input
            max="45"
            min="-45"
            onChange={(event) => onChange({ ...override, rotationDegrees: Number(event.currentTarget.value) })}
            step="1"
            type="range"
            value={override.rotationDegrees}
          />
          <output>{override.rotationDegrees}deg</output>
        </label>
        <small>
          x {override.anchorX.toFixed(3)}, y {override.anchorY.toFixed(3)}
        </small>
      </div>
    </article>
  );
}

function defaultOverride(lesson: Lesson, frame: SceneFrameData): SpeechBubbleOverride {
  const lineIndex = frame.lineIndex ?? 0;
  const kind = lineIndex === 1 ? 'mic' : 'speaker';
  const isMic = kind === 'mic';
  return {
    lessonId: lesson.id,
    frameId: frame.id,
    lineIndex,
    imageUrl: frame.imageUrl ?? null,
    kind,
    anchorX: isMic ? 0.66 : 0.36,
    anchorY: lineIndex === 1 ? 0.16 : 0.13,
    rotationDegrees: isMic ? -10 : 10,
    side: 'bottom',
    tipPosition: isMic ? 'left' : 'right',
    tipTilt: isMic ? 'left' : 'right',
  };
}

function overrideKey(lessonId: string, frameId: string): string {
  return `${lessonId}:${frameId}`;
}

function clamp(value: number): number {
  return Math.min(1, Math.max(0, value));
}
