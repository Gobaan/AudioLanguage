import type { Lesson, LessonStep } from '../components';
import { assetUrl } from './lessonUrls';

export type AssetPrefetchPlan = {
  critical: string[];
  soon: string[];
  background: string[];
};

type PlanOptions = {
  initialStepCount?: number;
  lookaheadStepCount?: number;
  nextLessonCriticalStepCount?: number;
  nextLessonTriggerRemainingSteps?: number;
};

const DEFAULT_INITIAL_STEP_COUNT = 6;
const DEFAULT_LOOKAHEAD_STEP_COUNT = 4;
const DEFAULT_NEXT_LESSON_CRITICAL_STEP_COUNT = 1;
const DEFAULT_NEXT_LESSON_TRIGGER_REMAINING_STEPS = 4;

export function planLessonStartAssets(
  lesson: Lesson,
  options: PlanOptions = {},
): AssetPrefetchPlan {
  const initialStepCount = Math.max(1, options.initialStepCount ?? DEFAULT_INITIAL_STEP_COUNT);
  const criticalEnd = Math.min(lesson.steps.length, initialStepCount);
  const soonEnd = Math.min(lesson.steps.length, initialStepCount + 2);
  const critical = collectStepRangeAssets(lesson, 0, criticalEnd);
  const soon = collectStepRangeAssets(lesson, criticalEnd, soonEnd);
  const background = collectStepRangeAssets(lesson, soonEnd, lesson.steps.length);
  return { critical, soon, background };
}

export function planUpcomingStepAssets(
  lesson: Lesson,
  currentStepId: string,
  options: PlanOptions = {},
): AssetPrefetchPlan {
  const currentIndex = lesson.steps.findIndex((step) => step.id === currentStepId);
  if (currentIndex < 0) {
    return { critical: [], soon: [], background: [] };
  }

  const lookaheadStepCount = Math.max(1, options.lookaheadStepCount ?? DEFAULT_LOOKAHEAD_STEP_COUNT);
  const criticalStart = currentIndex + 1;
  const criticalEnd = Math.min(lesson.steps.length, criticalStart + Math.min(2, lookaheadStepCount));
  const soonEnd = Math.min(lesson.steps.length, criticalStart + lookaheadStepCount);

  return {
    critical: collectStepRangeAssets(lesson, criticalStart, criticalEnd),
    soon: collectStepRangeAssets(lesson, criticalEnd, soonEnd),
    background: [],
  };
}

export function shouldPrimeNextLesson(
  lesson: Lesson,
  currentStepId: string,
  options: PlanOptions = {},
): boolean {
  const currentIndex = lesson.steps.findIndex((step) => step.id === currentStepId);
  if (currentIndex < 0) {
    return false;
  }
  const remainingSteps = lesson.steps.length - currentIndex - 1;
  const threshold = Math.max(
    0,
    options.nextLessonTriggerRemainingSteps ?? DEFAULT_NEXT_LESSON_TRIGGER_REMAINING_STEPS,
  );
  return remainingSteps <= threshold;
}

export function planNextLessonAssets(
  lesson: Lesson,
  options: PlanOptions = {},
): AssetPrefetchPlan {
  const criticalStepCount = Math.max(
    1,
    options.nextLessonCriticalStepCount ?? DEFAULT_NEXT_LESSON_CRITICAL_STEP_COUNT,
  );
  const criticalEnd = Math.min(lesson.steps.length, criticalStepCount);
  return {
    critical: collectStepRangeAssets(lesson, 0, criticalEnd),
    soon: collectStepRangeAssets(lesson, criticalEnd, Math.min(lesson.steps.length, criticalEnd + 2)),
    background: [],
  };
}

function collectStepRangeAssets(
  lesson: Lesson,
  fromStepIndexInclusive: number,
  toStepIndexExclusive: number = lesson.steps.length,
): string[] {
  if (fromStepIndexInclusive >= toStepIndexExclusive || fromStepIndexInclusive >= lesson.steps.length) {
    return [];
  }

  const urls = new Set<string>();
  for (let index = fromStepIndexInclusive; index < toStepIndexExclusive; index += 1) {
    const step = lesson.steps[index];
    if (!step) {
      continue;
    }
    collectAssetsForStep(lesson, step, urls);
  }
  return Array.from(urls);
}

function collectAssetsForStep(lesson: Lesson, step: LessonStep, urls: Set<string>) {
  if (step.type === 'scene_setup') {
    for (const frame of lesson.frames) {
      addUrl(urls, frame.imageUrl);
      addUrl(urls, frame.audioUrl);
    }
  } else {
    const stepFrame = lesson.frames.find((frame) => frame.id === step.frameId);
    addUrl(urls, stepFrame?.imageUrl);
    addUrl(urls, stepFrame?.audioUrl);
  }

  addUrl(urls, step.audio?.url);

  const prompts = step.props?.prompts;
  if (Array.isArray(prompts)) {
    for (const prompt of prompts) {
      if (typeof prompt !== 'object' || prompt === null) {
        continue;
      }
      addUrl(urls, (prompt as { audioUrl?: unknown }).audioUrl);
    }
  }
}

function addUrl(urls: Set<string>, value: unknown) {
  if (typeof value !== 'string' || !value) {
    return;
  }
  urls.add(assetUrl(value));
}
