import { DEFAULT_LESSON, START_LESSON } from './lessonUrls';

export type LessonTab = {
  id: string;
  label: string;
};

export type LessonPageSelection<TLesson> = {
  lesson: TLesson | null;
  resolvedLessonPage: string | null;
  shouldReplaceUrl: boolean;
};

export function selectLessonForPage<TLesson>(
  lessonPage: string,
  lessonTabs: LessonTab[],
  lessons: TLesson[],
): LessonPageSelection<TLesson> {
  if (lessonPage !== START_LESSON) {
    const selectedLesson = lessonForPage(lessonPage, lessonTabs, lessons);
    if (selectedLesson) {
      return {
        lesson: selectedLesson,
        resolvedLessonPage: lessonPage,
        shouldReplaceUrl: false,
      };
    }
  }

  const fallbackPage = fallbackLessonPage(lessonTabs, lessonPage !== START_LESSON);
  const fallbackLesson = fallbackPage ? lessonForPage(fallbackPage, lessonTabs, lessons) : lessons[0];

  return {
    lesson: fallbackLesson ?? null,
    resolvedLessonPage: fallbackPage,
    shouldReplaceUrl: Boolean(fallbackPage && fallbackPage !== lessonPage),
  };
}

function lessonForPage<TLesson>(lessonPage: string, lessonTabs: LessonTab[], lessons: TLesson[]): TLesson | null {
  const lessonIndex = lessonTabs.findIndex((tab) => tab.id === lessonPage);
  if (lessonIndex === -1) {
    return null;
  }

  return lessons[lessonIndex] ?? null;
}

function fallbackLessonPage(lessonTabs: LessonTab[], preferDefaultLesson: boolean): string | null {
  if (preferDefaultLesson && lessonTabs.some((tab) => tab.id === DEFAULT_LESSON)) {
    return DEFAULT_LESSON;
  }

  return lessonTabs[0]?.id ?? null;
}
