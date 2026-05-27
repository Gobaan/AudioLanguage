import { useEffect, useMemo, useState } from 'react';
import { fetchLessons } from '../api/lessons';
import { SceneFrame } from '../components';
import type { Lesson, SceneFrameData } from '../components';

const FALLBACK_LESSON: Lesson = {
  id: 'en-card-first-hi-dialogue-practice',
  language: 'en',
  title: 'First hello dialogue',
  mode: 'ai_guided_response',
  stage: 'guided_scene_production',
  player_component: 'TravellerLessonPlayer',
  target: {
    id: 'en-target-respond-hi',
    text: 'Hi!',
    transliteration: '',
    meaning: 'Respond to Hi.',
  },
  frames: [
    {
      id: 'line-0',
      lineIndex: 0,
      frameNumber: 1,
      imageUrl: '/visuals/final/first-hi-response/frame-1.png',
      audioUrl: '/audio/generated/en/en-first-hi-response/line-0.mp3',
      title: 'World Opener',
      speaker: 'friend',
      text: 'Hi!',
      transliteration: '',
      lineType: 'world_opener',
    },
  ],
  steps: [],
};

type LoadState = 'loading' | 'ready' | 'error';

export function TravellerMvpApp() {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');

  useEffect(() => {
    let isCurrent = true;

    fetchLessons('en')
      .then((payload) => {
        if (!isCurrent) return;
        setLesson(payload.lessons[0] ?? FALLBACK_LESSON);
        setLoadState('ready');
      })
      .catch(() => {
        if (!isCurrent) return;
        setLesson(FALLBACK_LESSON);
        setLoadState('ready');
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  const firstFrame = lesson?.frames[0];
  const visibleFrame = useMemo(() => withAssetUrls(firstFrame), [firstFrame]);

  useEffect(() => {
    if (!firstFrame?.audioUrl || loadState !== 'ready') return;

    const audio = new Audio(assetUrl(firstFrame.audioUrl));
    audio.play().catch(() => {
      // Browser autoplay policy may require one user interaction before sound can play.
    });

    return () => {
      audio.pause();
      audio.currentTime = 0;
    };
  }, [firstFrame?.audioUrl, loadState]);

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading first frame" />;
  }

  if (loadState === 'error' || !visibleFrame) {
    return <div className="frame-placeholder" aria-label="First frame unavailable" />;
  }

  return (
    <section className="first-frame-app" aria-label="First lesson frame">
      <SceneFrame frame={visibleFrame} isActive showCaption={false} placeholderLabel="First lesson frame" />
    </section>
  );
}

function withAssetUrls(frame: SceneFrameData | undefined): SceneFrameData | undefined {
  if (!frame) return undefined;

  return {
    ...frame,
    imageUrl: frame.imageUrl ? assetUrl(frame.imageUrl) : frame.imageUrl,
    audioUrl: frame.audioUrl ? assetUrl(frame.audioUrl) : frame.audioUrl,
  };
}

function assetUrl(url: string): string {
  if (window.location.protocol !== 'file:' || !url.startsWith('/')) {
    return url;
  }

  return `../../model/assets${url}`;
}
