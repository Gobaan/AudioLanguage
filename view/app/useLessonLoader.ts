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

export type LoadState = 'idle' | 'loading' | 'ready' | 'error';

type UseLessonLoaderOptions = {
  language: string;
  lessonPage: string;
  sceneSet: string;
  participantId: string | null;
  sessionRequestId: number;
  onLessonPageChange: (lessonPage: string) => void;
};

export function useLessonLoader({
  language,
  lessonPage,
  sceneSet,
  participantId,
  sessionRequestId,
  onLessonPageChange,
}: UseLessonLoaderOptions) {
  const [lessonTabs, setLessonTabs] = useState<LessonTab[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [planVersion, setPlanVersion] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('idle');

  useEffect(() => {
    if (!participantId || sessionRequestId === 0) {
      setLoadState('idle');
      return;
    }

    let isCurrent = true;

    async function loadPlan() {
      setLoadState('loading');
      try {
        const payload = await fetchLearningPlan(language, sceneSet, stableOrderSeed(language, sceneSet), participantId);
        if (!isCurrent) return;
        setLessonTabs(payload.lesson_tabs ?? []);
        setLessons((payload.lessons ?? []).map(activeMvpLesson));
        setDisplayName(payload.display_name ?? null);
        setPlanVersion(payload.plan_version ?? null);
        setSessionId(payload.session_id ?? null);
        setLoadState('ready');
      } catch {
        if (!isCurrent) return;
        setLessonTabs([]);
        setLessons([activeMvpLesson(FALLBACK_LESSON)]);
        setLesson(activeMvpLesson(FALLBACK_LESSON));
        setDisplayName(null);
        setPlanVersion(null);
        setSessionId(null);
        setLoadState('ready');
      }
    }

    loadPlan();

    return () => {
      isCurrent = false;
    };
  }, [language, sceneSet, participantId, sessionRequestId]);

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
    lessons,
    lesson,
    displayName,
    planVersion,
    sessionId,
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
