import { useCallback, useState } from 'react';

import { DEFAULT_LESSON, languageFromUrl, lessonPageFromUrl, sceneSetFromUrl, updateLessonUrl } from './lessonUrls';

export function useTravellerRoute() {
  const [language, setLanguage] = useState(() => languageFromUrl());
  const [lessonPage, setLessonPage] = useState(() => lessonPageFromUrl());
  const [sceneSet] = useState(() => sceneSetFromUrl());

  const selectLanguage = useCallback(
    (nextLanguage: string) => {
      setLanguage(nextLanguage);
      setLessonPage(DEFAULT_LESSON);
      updateLessonUrl(nextLanguage, DEFAULT_LESSON, sceneSet, false, null);
    },
    [sceneSet],
  );

  const selectLessonPage = useCallback(
    (nextPage: string) => {
      setLessonPage(nextPage);
      updateLessonUrl(language, nextPage, sceneSet, false, null);
    },
    [language, sceneSet],
  );

  return {
    language,
    lessonPage,
    sceneSet,
    setLessonPage,
    selectLanguage,
    selectLessonPage,
  };
}
