import type { Lesson, LessonStep } from '../components';

export const DEFAULT_LANGUAGE = 'ja';
export const DEFAULT_LESSON = 'hello';
export const DEFAULT_SCENE_SET = 'mvp';

export function languageFromUrl(): string {
  return new URLSearchParams(window.location.search).get('language') ?? DEFAULT_LANGUAGE;
}

export function lessonPageFromUrl(): string {
  return new URLSearchParams(window.location.search).get('lesson') ?? DEFAULT_LESSON;
}

export function sceneSetFromUrl(): string {
  return new URLSearchParams(window.location.search).get('scene_set') ?? DEFAULT_SCENE_SET;
}

export function updateLessonUrl(language: string, lesson: string, sceneSet: string, replace = false) {
  const url = new URL(window.location.href);
  if (url.pathname !== '/learn') {
    url.pathname = '/learn';
  }
  url.searchParams.set('language', language);
  url.searchParams.set('lesson', lesson);
  if (sceneSet === DEFAULT_SCENE_SET) {
    url.searchParams.delete('scene_set');
  } else {
    url.searchParams.set('scene_set', sceneSet);
  }
  if (replace) {
    window.history.replaceState({}, '', url);
  } else {
    window.history.pushState({}, '', url);
  }
}

export function validationSessionIdForToday(participantId: string, language: string, sceneSet: string): string {
  return ['validation', safeId(participantId), safeId(language), safeId(sceneSet), localDateKey()].join('-');
}

function localDateKey(): string {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function safeId(value: string): string {
  return value.replace(/[^A-Za-z0-9_.-]+/g, '-');
}

export function learnerTargetAudioUrl(lesson: Lesson): string | null {
  return lesson.frames.find((frame) => frame.lineType === 'learner_target')?.audioUrl ?? null;
}

export function activeMvpLesson(lesson: Lesson): Lesson {
  return {
    ...lesson,
    steps: lesson.steps.filter((step) => {
      if (step.id === 'translation_reveal') return false;
      if (step.id === 'audio_replay') return false;
      if (step.id === 'production_prompt') return false;
      return true;
    }),
  };
}

export function withAssetUrls(lesson: Lesson | null): Lesson | null {
  if (!lesson) return null;

  return {
    ...lesson,
    frames: lesson.frames.map((frame) => ({
      ...frame,
      imageUrl: frame.imageUrl ? assetUrl(frame.imageUrl) : frame.imageUrl,
      audioUrl: frame.audioUrl ? assetUrl(frame.audioUrl) : frame.audioUrl,
    })),
  };
}

export function withStepAssetUrls(step: LessonStep | undefined): LessonStep | undefined {
  if (!step) return undefined;

  return {
    ...step,
    audio: step.audio
      ? {
          ...step.audio,
          url: step.audio.url ? assetUrl(step.audio.url) : step.audio.url,
        }
      : step.audio,
  };
}

function assetUrl(url: string): string {
  if (window.location.protocol !== 'file:' || !url.startsWith('/')) {
    return url;
  }

  return `../../model/assets${url}`;
}
