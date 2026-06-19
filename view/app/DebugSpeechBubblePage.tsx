import { useEffect, useMemo, useState } from 'react';

import { fetchLearningPlan } from '../api/lessons';
import { SceneFrame, SpeechIconBubble } from '../components';
import type { Lesson, SceneFrameData } from '../components';
import { assetUrl } from './lessonUrls';

type LoadState = 'loading' | 'ready' | 'error';

const HI_INTRO_LESSON_ID = 'ja-card-first-hi-dialogue-practice';

export function DebugSpeechBubblePage() {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');

  useEffect(() => {
    let isCurrent = true;
    setLoadState('loading');

    fetchLearningPlan('ja', 'mvp', 'speech-bubble-debug:ja:mvp')
      .then((payload) => {
        if (!isCurrent) return;
        setLesson(payload.lessons.find((item) => item.id === HI_INTRO_LESSON_ID) ?? payload.lessons[0] ?? null);
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

  const frames = useMemo(() => lesson?.frames.map(withDebugBubbleOverlay) ?? [], [lesson]);

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading speech bubble debug page" />;
  }

  if (loadState === 'error' || !lesson) {
    return (
      <section className="speech-bubble-debug-page" aria-label="Speech bubble debug page">
        <header>
          <span>Debug</span>
          <h1>Speech Bubble Placement</h1>
        </header>
        <p className="audio-error" role="alert">
          Could not load the Japanese hi intro scene.
        </p>
      </section>
    );
  }

  return (
    <section className="speech-bubble-debug-page" aria-label="Speech bubble debug page">
      <header>
        <span>Debug</span>
        <h1>Hi Intro Bubble Placement</h1>
        <p>{lesson.id}</p>
      </header>

      <section className="speech-bubble-component-preview" aria-label="Standalone speech bubble preview">
        <article>
          <SpeechIconBubble kind="speaker" label="World speaker bubble" tipPosition="right" tipTilt="right" />
          <strong>World speaking</strong>
          <span>Speaker bubble, rotated right</span>
        </article>
        <article>
          <SpeechIconBubble kind="mic" label="Learner mic bubble" tipPosition="left" tipTilt="left" />
          <strong>Learner speaking</strong>
          <span>Mic bubble, rotated left</span>
        </article>
      </section>

      <div className="speech-bubble-debug-grid">
        {frames.map((frame) => (
          <article key={frame.id} className="speech-bubble-debug-frame">
            <SceneFrame frame={frame} isActive showCaption={false} placeholderLabel="Hi intro frame" />
            <dl>
              <div>
                <dt>Frame</dt>
                <dd>{frame.title || frame.id}</dd>
              </div>
              <div>
                <dt>Speaker</dt>
                <dd>{frame.speaker || 'unknown'}</dd>
              </div>
              <div>
                <dt>Bubble</dt>
                <dd>{bubbleLabel(frame)}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

function withDebugBubbleOverlay(frame: SceneFrameData): SceneFrameData {
  const isLearner = frame.speaker === 'learner' || frame.lineType === 'learner_target';
  return {
    ...frame,
    imageUrl: frame.imageUrl ? assetUrl(frame.imageUrl) : frame.imageUrl,
    speechBubble:
      hiIntroDebugBubble(frame) ??
      frame.speechBubble ??
      {
        kind: isLearner ? 'mic' : 'speaker',
        anchorX: isLearner ? 0.38 : 0.62,
        anchorY: 0.18,
        side: 'bottom',
        tipPosition: isLearner ? 'left' : 'right',
        tipTilt: isLearner ? 'left' : 'right',
        rotationDegrees: isLearner ? -12 : 12,
      },
  };
}

function hiIntroDebugBubble(frame: SceneFrameData): SceneFrameData['speechBubble'] | null {
  if (frame.lineIndex === 0) {
    return {
      kind: 'speaker',
      anchorX: 0.36,
      anchorY: 0.12,
      side: 'bottom',
      tipPosition: 'right',
      tipTilt: 'right',
      rotationDegrees: 10,
    };
  }
  if (frame.lineIndex === 1) {
    return {
      kind: 'mic',
      anchorX: 0.66,
      anchorY: 0.16,
      side: 'bottom',
      tipPosition: 'left',
      tipTilt: 'left',
      rotationDegrees: -10,
    };
  }
  if (frame.lineIndex === 2) {
    return {
      kind: 'speaker',
      anchorX: 0.36,
      anchorY: 0.13,
      side: 'bottom',
      tipPosition: 'right',
      tipTilt: 'right',
      rotationDegrees: 10,
    };
  }
  return null;
}

function bubbleLabel(frame: SceneFrameData): string {
  const bubble = frame.speechBubble;
  if (!bubble) {
    return 'none';
  }
  return `${bubble.kind} @ ${Math.round(bubble.anchorX * 100)}%, ${Math.round(bubble.anchorY * 100)}%; rotate ${
    bubble.rotationDegrees ?? 0
  }deg`;
}
