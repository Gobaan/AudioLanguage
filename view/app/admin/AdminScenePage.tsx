import { useCallback, useEffect, useState } from 'react';

import { fetchLessons } from '../../api/lessons';
import { ScenePlayback, type Lesson } from '../../components';
import type { SceneFrameData } from '../../components/types';
import { withAssetUrls } from '../lessonUrls';

type LoadState = 'loading' | 'ready' | 'error';

export function AdminScenePage() {
  const params = new URLSearchParams(window.location.search);
  const language = params.get('language') || '';
  const lessonPage = params.get('lessonPage') || '';
  const lessonId = params.get('lessonId') || '';
  const frameId = params.get('frame') || '';
  const sceneSet = params.get('sceneSet');
  const returnTo = safeReturnPath(params.get('returnTo'));
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const updateFrameInUrl = useCallback((frame: SceneFrameData) => {
    const url = new URL(window.location.href);
    url.searchParams.set('frame', frame.id);
    window.history.replaceState({}, '', url);
  }, []);

  useEffect(() => {
    if (!language || (!lessonPage && !lessonId)) {
      setLoadState('error');
      return;
    }

    setLoadState('loading');
    loadScene(language, lessonPage, lessonId, sceneSet)
      .then((payload) => {
        setLesson(payload);
        setLoadState('ready');
      })
      .catch(() => {
        setLesson(null);
        setLoadState('error');
      });
  }, [language, lessonId, lessonPage, sceneSet]);

  return (
    <section className="validation-admin simple admin-scene-page" aria-label="Scene viewer">
      <nav className="admin-actions admin-scene-actions" aria-label="Scene controls">
        <a href={returnTo}>Back</a>
      </nav>
      {loadState === 'loading' ? <p className="admin-status">Loading scene.</p> : null}
      {loadState === 'error' ? <p className="admin-status">Scene is unavailable.</p> : null}
      {loadState === 'ready' && lesson ? (
        <ScenePlayback
          frames={withAssetUrls(lesson)?.frames ?? []}
          autoplay={!frameId}
          initialFrameId={frameId}
          onActiveFrameChange={updateFrameInUrl}
        />
      ) : null}
    </section>
  );
}

async function loadScene(
  language: string,
  lessonPage: string,
  lessonId: string,
  sceneSet: string | null,
): Promise<Lesson> {
  if (lessonPage) {
    try {
      const payload = await fetchLessons(language, lessonPage, sceneSet);
      const lesson = payload.lessons.find((item) => item.id === lessonId) ?? payload.lessons[0] ?? null;
      if (lesson) return lesson;
    } catch {
      if (!lessonId) throw new Error('Scene was not returned.');
    }
  }

  if (lessonId) {
    const payload = await fetchLessons(language, null, sceneSet);
    const lesson = payload.lessons.find((item) => item.id === lessonId) ?? null;
    if (lesson) return lesson;
  }

  throw new Error('Scene was not returned.');
}

function safeReturnPath(value: string | null): string {
  if (!value || !value.startsWith('/') || value.startsWith('//')) {
    return '/gobi-admin';
  }
  return value;
}
