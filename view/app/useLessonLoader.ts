import { useEffect, useState } from 'react';

import { fetchLessons } from '../api/lessons';
import type { Lesson, LessonListResponse } from '../components';
import { FALLBACK_LESSON } from './fallbackLesson';
import {
  DEFAULT_LESSON,
  activeMvpLesson,
  updateLessonUrl,
} from './lessonUrls';

export type LessonTab = {
  id: string;
  label: string;
};

export type LoadState = 'loading' | 'ready' | 'error';

type UseLessonLoaderOptions = {
  language: string;
  lessonPage: string;
  sceneSet: string;
  onLessonPageChange: (lessonPage: string) => void;
};

export function useLessonLoader({
  language,
  lessonPage,
  sceneSet,
  onLessonPageChange,
}: UseLessonLoaderOptions) {
  const [lessonTabs, setLessonTabs] = useState<LessonTab[]>([]);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');

  useEffect(() => {
    let isCurrent = true;

    async function loadLesson() {
      setLoadState('loading');
      try {
        const payload = await fetchLessons(language, lessonPage, sceneSet);
        if (!isCurrent) return;
        applyLessonPayload(payload);
        setLoadState('ready');
      } catch {
        try {
          const payload = await fetchLessons(language, DEFAULT_LESSON, sceneSet);
          if (!isCurrent) return;
          applyLessonPayload(payload);
          onLessonPageChange(DEFAULT_LESSON);
          updateLessonUrl(language, DEFAULT_LESSON, sceneSet, true);
          setLoadState('ready');
        } catch {
          if (!isCurrent) return;
          setLessonTabs([]);
          setLesson(activeMvpLesson(FALLBACK_LESSON));
          setLoadState('ready');
        }
      }
    }

    function applyLessonPayload(payload: LessonListResponse) {
      setLessonTabs(payload.lesson_tabs ?? []);
      setLesson(activeMvpLesson(payload.lessons[0] ?? FALLBACK_LESSON));
    }

    loadLesson();

    return () => {
      isCurrent = false;
    };
  }, [language, lessonPage, sceneSet, onLessonPageChange]);

  return {
    lessonTabs,
    lesson,
    loadState,
  };
}
