import { START_LESSON } from './lessonUrls';

export type LessonSceneSet = 'mvp' | 'delayed';

export function languageLessonLink(language: string, sceneSet: LessonSceneSet): string {
  const lesson = sceneSet === 'delayed' ? START_LESSON : 'hello';
  const params = new URLSearchParams({ language, lesson });
  if (sceneSet !== 'mvp') params.set('scene_set', sceneSet);
  return `/learn?${params.toString()}`;
}
