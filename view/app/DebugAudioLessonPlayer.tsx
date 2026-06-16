import { useEffect, useMemo, useRef, useState } from 'react';

import { fetchLearningPlan } from '../api/lessons';
import type { Lesson } from '../components';
import { DEFAULT_LANGUAGE, DEFAULT_SCENE_SET, sceneSetFromUrl, languageFromUrl } from './lessonUrls';

type LoadState = 'loading' | 'ready' | 'error';
type PlayState = 'idle' | 'playing' | 'paused' | 'done' | 'error';

type AudioDebugItem = {
  id: string;
  lessonTitle: string;
  label: string;
  url: string;
};

export function DebugAudioLessonPlayer() {
  const [language] = useState(() => languageFromUrl() || DEFAULT_LANGUAGE);
  const [sceneSet] = useState(() => sceneSetFromUrl() || DEFAULT_SCENE_SET);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [playState, setPlayState] = useState<PlayState>('idle');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    let isCurrent = true;
    setLoadState('loading');
    fetchLearningPlan(language, sceneSet, `audio-debug:${language}:${sceneSet}`)
      .then((payload) => {
        if (!isCurrent) return;
        setLessons(payload.lessons ?? []);
        setLoadState('ready');
      })
      .catch(() => {
        if (!isCurrent) return;
        setLoadState('error');
      });

    return () => {
      isCurrent = false;
      stopAudio();
    };
  }, [language, sceneSet]);

  const queue = useMemo(() => lessons.flatMap(audioItemsForLesson), [lessons]);
  const currentItem = queue[currentIndex];

  function playFrom(index: number) {
    const item = queue[index];
    stopAudio();
    setErrorMessage(null);

    if (!item) {
      setPlayState('done');
      return;
    }

    const audio = new Audio(item.url);
    audioRef.current = audio;
    setCurrentIndex(index);
    setPlayState('playing');
    audio.addEventListener('ended', () => playFrom(index + 1), { once: true });
    audio.addEventListener(
      'error',
      () => {
        audioRef.current = null;
        setPlayState('error');
        setErrorMessage(`Could not play ${item.label}.`);
      },
      { once: true },
    );
    audio.play().catch(() => {
      audioRef.current = null;
      setPlayState('error');
      setErrorMessage(`Could not play ${item.label}.`);
    });
  }

  function stopAudio() {
    if (!audioRef.current) return;
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    audioRef.current = null;
  }

  function pause() {
    audioRef.current?.pause();
    setPlayState('paused');
  }

  function resume() {
    if (!audioRef.current) {
      playFrom(currentIndex);
      return;
    }
    setPlayState('playing');
    audioRef.current.play().catch(() => {
      setPlayState('error');
      setErrorMessage('Could not resume audio.');
    });
  }

  function stop() {
    stopAudio();
    setPlayState('idle');
    setCurrentIndex(0);
    setErrorMessage(null);
  }

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading audio debug lessons" />;
  }

  if (loadState === 'error') {
    return (
      <section className="audio-debug-page" aria-label="Audio debug player">
        <h1>Audio debug</h1>
        <p className="audio-error" role="alert">Audio debug lessons are unavailable.</p>
      </section>
    );
  }

  return (
    <section className="audio-debug-page" aria-label="Audio debug player">
      <header>
        <span>Audio Debug</span>
        <h1>{language.toUpperCase()} {sceneSet}</h1>
      </header>
      <p>This plays lesson audio in order, skips choices and recordings, and does not save validation data.</p>
      <div className="audio-debug-controls">
        {playState === 'playing' ? (
          <button type="button" onClick={pause}>Pause</button>
        ) : (
          <button type="button" onClick={resume}>Start</button>
        )}
        <button type="button" onClick={stop}>Stop</button>
      </div>
      {errorMessage ? <p className="audio-error" role="alert">{errorMessage}</p> : null}
      <ol className="audio-debug-list">
        {queue.map((item, index) => (
          <li key={item.id} className={index === currentIndex && playState === 'playing' ? 'active' : ''}>
            <span>{index + 1}</span>
            <div>
              <strong>{item.label}</strong>
              <em>{item.lessonTitle}</em>
            </div>
          </li>
        ))}
      </ol>
      {!currentItem && playState === 'done' ? <p className="audio-debug-status">Done.</p> : null}
    </section>
  );
}

function audioItemsForLesson(lesson: Lesson): AudioDebugItem[] {
  const frameItems = lesson.frames
    .filter((frame) => Boolean(frame.audioUrl))
    .map((frame) => ({
      id: `${lesson.id}:${frame.id}`,
      lessonTitle: lesson.title,
      label: frame.title || frame.lineType || frame.id,
      url: frame.audioUrl as string,
    }));

  const backwardBuildItems = lesson.steps.flatMap((step) => {
    if (step.type !== 'backward_build') return [];
    const prompts = Array.isArray(step.props.prompts) ? step.props.prompts : [];
    return prompts
      .filter((prompt): prompt is { id?: string; text?: string; audioUrl: string } => {
        return typeof prompt === 'object' && prompt !== null && typeof prompt.audioUrl === 'string';
      })
      .map((prompt, index) => ({
        id: `${lesson.id}:${step.id}:prompt-${prompt.id ?? index}`,
        lessonTitle: lesson.title,
        label: `Backward build: ${prompt.text || prompt.id || index + 1}`,
        url: prompt.audioUrl,
      }));
  });

  return [...frameItems, ...backwardBuildItems];
}
