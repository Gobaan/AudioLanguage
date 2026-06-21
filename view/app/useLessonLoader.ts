import { useCallback, useEffect, useState } from 'react';

import { fetchLearningPlan } from '../api/lessons';
import type { Lesson } from '../components';
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
        setLessons([]);
        setLesson(null);
        setDisplayName(null);
        setPlanVersion(null);
        setSessionId(null);
        setLoadState('error');
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
    setLesson(selected.lesson);

    if (selected.shouldReplaceUrl && selected.resolvedLessonPage) {
      onLessonPageChange(selected.resolvedLessonPage);
      updateLessonUrl(language, selected.resolvedLessonPage, sceneSet, true);
    }
  }, [language, lessonPage, lessonTabs, lessons, loadState, sceneSet, onLessonPageChange]);

  const insertLessonBundleAfter = useCallback(
    (currentLessonPage: string, bundleTabs: LessonTab[], bundleLessons: Lesson[]): string | null => {
      if (bundleTabs.length === 0 || bundleLessons.length === 0) {
        return null;
      }

      const uniqueSuffix = relearnQueueSuffix();
      const insertedTabs = bundleTabs.map((tab) => ({
        ...tab,
        id: `${tab.id}-relearn-${uniqueSuffix}`,
      }));
      const insertedLessons = bundleLessons.map(activeMvpLesson);
      const firstInsertedPage = insertedTabs[0]?.id ?? null;

      setLessonTabs((currentTabs) => {
        const insertionIndex = lessonInsertionIndex(currentTabs, currentLessonPage);
        return insertBundleWithRecallGap(currentTabs, insertedTabs, insertionIndex);
      });
      setLessons((currentLessons) => {
        const insertionIndex = lessonInsertionIndex(lessonTabs, currentLessonPage);
        return insertBundleWithRecallGap(currentLessons, insertedLessons, insertionIndex);
      });
      setLoadState('ready');

      return firstInsertedPage;
    },
    [lessonTabs],
  );

  return {
    lessonTabs,
    lessons,
    lesson,
    displayName,
    planVersion,
    sessionId,
    loadState,
    insertLessonBundleAfter,
  };
}

function lessonInsertionIndex(lessonTabs: LessonTab[], currentLessonPage: string): number {
  const currentIndex = lessonTabs.findIndex((tab) => tab.id === currentLessonPage);
  return currentIndex < 0 ? lessonTabs.length : currentIndex + 1;
}

function insertBundleWithRecallGap<TItem>(currentItems: TItem[], bundleItems: TItem[], insertionIndex: number): TItem[] {
  const [anchorItem, recallItem, ...remainingItems] = bundleItems;
  if (!anchorItem || !recallItem) {
    return [
      ...currentItems.slice(0, insertionIndex),
      ...bundleItems,
      ...currentItems.slice(insertionIndex),
    ];
  }

  const beforeInsertion = currentItems.slice(0, insertionIndex);
  const afterInsertion = currentItems.slice(insertionIndex);
  const interveningItem = afterInsertion[0];

  if (interveningItem) {
    return [
      ...beforeInsertion,
      anchorItem,
      interveningItem,
      recallItem,
      ...remainingItems,
      ...afterInsertion.slice(1),
    ];
  }

  return [...beforeInsertion, anchorItem, recallItem, ...remainingItems];
}

function relearnQueueSuffix(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
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
