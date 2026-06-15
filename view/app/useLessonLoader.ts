import { useEffect, useState } from 'react';

import { fetchLearningPlan } from '../api/lessons';
import type { Lesson } from '../components';
import { FALLBACK_LESSON } from './fallbackLesson';
import {
  activeMvpLesson,
  updateLessonUrl,
} from './lessonUrls';
import { selectLessonForPage, type LessonTab } from './lessonSelection';
import { isLocalHost } from './urlParams';

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
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');

  useEffect(() => {
    let isCurrent = true;

    async function loadPlan() {
      setLoadState('loading');
      try {
        const payload = await fetchLearningPlan(language, sceneSet, stableOrderSeed(language, sceneSet));
        if (!isCurrent) return;
        setLessonTabs(payload.lesson_tabs ?? []);
        setLessons((payload.lessons ?? []).map(activeMvpLesson));
        setLoadState('ready');
      } catch {
        if (!isCurrent) return;
        setLessonTabs([]);
        setLessons([activeMvpLesson(FALLBACK_LESSON)]);
        setLesson(activeMvpLesson(FALLBACK_LESSON));
        setLoadState('ready');
      }
    }

    loadPlan();

    return () => {
      isCurrent = false;
    };
  }, [language, sceneSet]);

  useEffect(() => {
    if (loadState !== 'ready') {
      return;
    }

    const selected = selectLessonForPage(lessonPage, lessonTabs, lessons);
    setLesson(selected.lesson ?? activeMvpLesson(FALLBACK_LESSON));

    if (selected.shouldReplaceUrl && selected.resolvedLessonPage) {
      onLessonPageChange(selected.resolvedLessonPage);
      updateLessonUrl(language, selected.resolvedLessonPage, sceneSet, true);
    }
  }, [language, lessonPage, lessonTabs, lessons, loadState, sceneSet, onLessonPageChange]);

  return {
    lessonTabs,
    lesson,
    loadState,
  };
}

function stableOrderSeed(language: string, sceneSet: string): string | null {
  if (!isLocalHost()) {
    return browserSessionOrderSeed(language, sceneSet);
  }

  return `local-debug:${language}:${sceneSet}`;
}

function browserSessionOrderSeed(language: string, sceneSet: string): string {
  const storageKey = `audio-language-order-seed:${language}:${sceneSet}`;
  try {
    const existingSeed = window.sessionStorage.getItem(storageKey);
    if (existingSeed) {
      return existingSeed;
    }

    const seed = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    window.sessionStorage.setItem(storageKey, seed);
    return seed;
  } catch {
    return `session:${language}:${sceneSet}`;
  }
}
