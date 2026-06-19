import { START_LESSON } from './lessonUrls';

export type LessonSceneSet = 'mvp' | 'delayed';

export function languageLessonLink(language: string, sceneSet: LessonSceneSet): string {
  const params = new URLSearchParams({ language, lesson: START_LESSON });
  if (sceneSet !== 'mvp') params.set('scene_set', sceneSet);
  return `/learn?${params.toString()}`;
}

export function languageAudioDebugLink(language: string, sceneSet: LessonSceneSet): string {
  const params = new URLSearchParams({ language });
  if (sceneSet !== 'mvp') params.set('scene_set', sceneSet);
  return `/debug/audio?${params.toString()}`;
}

export function languagePreloaderDebugLink(language: string, sceneSet: LessonSceneSet): string {
  const params = new URLSearchParams({ language });
  if (sceneSet !== 'mvp') params.set('scene_set', sceneSet);
  return `/debug/preloader?${params.toString()}`;
}
