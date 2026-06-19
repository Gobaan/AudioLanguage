import { useEffect, useMemo, useRef, useState } from 'react';

import { fetchLearningPlan } from '../api/lessons';
import type { Lesson } from '../components';
import { assetUrl, DEFAULT_LANGUAGE, DEFAULT_SCENE_SET, languageFromUrl, sceneSetFromUrl } from './lessonUrls';
import { getPrefetchedAudioElement, prefetchAssets, prefetchHasAsset } from './useAssetPrefetcher';

type LoadState = 'loading' | 'ready' | 'error';

type PreloadItem = {
  id: string;
  lessonTitle: string;
  frameLabel: string;
  imageUrl: string;
  audioUrl: string;
};

const MAX_ITEMS = 10;

export function DebugPreloaderPage() {
  const [language] = useState(() => languageFromUrl() || DEFAULT_LANGUAGE);
  const [sceneSet] = useState(() => sceneSetFromUrl() || DEFAULT_SCENE_SET);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [audioStatus, setAudioStatus] = useState<'idle' | 'playing' | 'error'>('idle');
  const [audioError, setAudioError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    let isCurrent = true;
    setLoadState('loading');
    fetchLearningPlan(language, sceneSet, `preloader-debug:${language}:${sceneSet}`)
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

  const items = useMemo(() => buildPreloadItems(lessons), [lessons]);
  const currentItem = items[currentIndex] ?? null;

  useEffect(() => {
    if (items.length === 0) return;
    prefetchForIndex(items, 0);
    if (items.length > 1) {
      prefetchForIndex(items, 1);
    }
  }, [items]);

  function stopAudio() {
    if (!audioRef.current) return;
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    audioRef.current = null;
  }

  function playCurrentAudio(index: number) {
    const item = items[index];
    if (!item) return;

    setAudioError(null);
    stopAudio();
    const audio = getPrefetchedAudioElement(item.audioUrl) ?? new Audio(item.audioUrl);
    audioRef.current = audio;
    setAudioStatus('playing');

    audio.addEventListener(
      'ended',
      () => {
        if (audioRef.current !== audio) return;
        audioRef.current = null;
        setAudioStatus('idle');
      },
      { once: true },
    );
    audio.addEventListener(
      'error',
      () => {
        if (audioRef.current !== audio) return;
        audioRef.current = null;
        setAudioStatus('error');
        setAudioError('Could not play the preloaded audio line.');
      },
      { once: true },
    );
    audio.play().catch(() => {
      if (audioRef.current !== audio) return;
      audioRef.current = null;
      setAudioStatus('error');
      setAudioError('Could not play the preloaded audio line.');
    });
  }

  function handleNext() {
    if (items.length === 0) return;
    const nextIndex = Math.min(currentIndex + 1, items.length - 1);
    if (nextIndex === currentIndex) return;

    setCurrentIndex(nextIndex);
    prefetchForIndex(items, nextIndex + 1);
    playCurrentAudio(nextIndex);
  }

  function handlePlayCurrent() {
    if (!currentItem) return;
    playCurrentAudio(currentIndex);
  }

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading preloader debug page" />;
  }

  if (loadState === 'error') {
    return (
      <section className="audio-debug-page" aria-label="Preloader debug page">
        <header>
          <span>Preloader Debug</span>
          <h1>Plan unavailable</h1>
        </header>
        <p className="audio-error" role="alert">Could not load lessons for preload testing.</p>
      </section>
    );
  }

  return (
    <section className="audio-debug-page preloader-debug-page" aria-label="Preloader debug page">
      <header>
        <span>Preloader Debug</span>
        <h1>{language.toUpperCase()} {sceneSet}</h1>
      </header>
      <p>
        Loads up to 10 image/audio pairs. It preloads the current and next pair, then each Next click advances one
        step and preloads one more pair.
      </p>

      <div className="transfer-debug-state">
        <div>
          <dt>Loaded pairs</dt>
          <dd>{items.length} / {MAX_ITEMS}</dd>
        </div>
        <div>
          <dt>Current index</dt>
          <dd>{items.length ? currentIndex + 1 : 0}</dd>
        </div>
        <div>
          <dt>Audio state</dt>
          <dd>{audioStatus}</dd>
        </div>
      </div>

      {currentItem ? (
        <article className="preloader-debug-current">
          <img src={currentItem.imageUrl} alt={currentItem.frameLabel} />
          <div className="preloader-debug-copy">
            <strong>{currentItem.frameLabel}</strong>
            <span>{currentItem.lessonTitle}</span>
            <small>
              image: {prefetchHasAsset(currentItem.imageUrl) ? 'ready' : 'loading'} | audio:{' '}
              {prefetchHasAsset(currentItem.audioUrl) ? 'ready' : 'loading'}
            </small>
          </div>
        </article>
      ) : (
        <p>No frame/audio pairs found in this plan.</p>
      )}

      <div className="audio-debug-controls">
        <button type="button" onClick={handlePlayCurrent} disabled={!currentItem}>
          Play current
        </button>
        <button type="button" onClick={handleNext} disabled={!currentItem || currentIndex >= items.length - 1}>
          Next
        </button>
      </div>

      {audioError ? <p className="audio-error" role="alert">{audioError}</p> : null}

      <ol className="audio-debug-list">
        {items.map((item, index) => (
          <li key={item.id} className={index === currentIndex ? 'active' : ''}>
            <span>{index + 1}</span>
            <div>
              <strong>{item.frameLabel}</strong>
              <em>{item.lessonTitle}</em>
              <small>
                image {prefetchHasAsset(item.imageUrl) ? 'ready' : 'pending'} | audio{' '}
                {prefetchHasAsset(item.audioUrl) ? 'ready' : 'pending'}
              </small>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function buildPreloadItems(lessons: Lesson[]): PreloadItem[] {
  const imageSeen = new Set<string>();
  const audioSeen = new Set<string>();
  const items: PreloadItem[] = [];

  for (const lesson of lessons) {
    for (const frame of lesson.frames) {
      const rawImage = frame.imageUrl;
      const rawAudio = frame.audioUrl;
      if (!rawImage || !rawAudio) continue;

      const imageUrl = assetUrl(rawImage);
      const audioUrl = assetUrl(rawAudio);
      if (imageSeen.has(imageUrl) || audioSeen.has(audioUrl)) continue;

      imageSeen.add(imageUrl);
      audioSeen.add(audioUrl);
      items.push({
        id: `${lesson.id}:${frame.id}`,
        lessonTitle: lesson.title,
        frameLabel: frame.title || frame.lineType || frame.id,
        imageUrl,
        audioUrl,
      });

      if (items.length >= MAX_ITEMS) {
        return items;
      }
    }
  }

  return items;
}

function prefetchForIndex(items: PreloadItem[], index: number) {
  const item = items[index];
  if (!item) return;
  prefetchAssets([item.imageUrl], 'critical');
  prefetchAssets([item.audioUrl], 'critical');
}
