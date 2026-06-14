import { useCallback, useState } from 'react';

import { fetchScoredValidationScorecard, type ValidationEvent, type ValidationScorecard } from '../api/validation';
import { updateLessonUrl, viewFromUrl } from './lessonUrls';
import { ScorecardState } from './ScorecardView';

export type AppView = 'lesson' | 'scorecard';

type UseScorecardOptions = {
  validationSessionId: string | null;
  logEvent: (event: ValidationEvent) => void;
  language: string;
  lessonPage: string;
  sceneSet: string;
  lessonId?: string;
  stepId?: string;
  stepIndex: number;
  targetId?: string;
};

export function useScorecard({
  validationSessionId,
  logEvent,
  language,
  lessonPage,
  sceneSet,
  lessonId,
  stepId,
  stepIndex,
  targetId,
}: UseScorecardOptions) {
  const [appView, setAppView] = useState<AppView>(() => (viewFromUrl() === 'scorecard' ? 'scorecard' : 'lesson'));
  const [scorecardState, setScorecardState] = useState<ScorecardState>(() =>
    viewFromUrl() === 'scorecard' ? 'loading' : 'idle',
  );
  const [scorecard, setScorecard] = useState<ValidationScorecard | null>(null);

  const resetScorecard = useCallback(() => {
    setAppView('lesson');
    setScorecard(null);
    setScorecardState('idle');
  }, []);

  const showScorecard = useCallback(() => {
    if (!validationSessionId) {
      setScorecardState('error');
      setAppView('scorecard');
      return;
    }

    setAppView('scorecard');
    setScorecardState('loading');
    updateLessonUrl(language, lessonPage, sceneSet, true, 'scorecard');
    logEvent({
      type: 'scorecard_viewed',
      lessonId,
      lessonPage,
      stepId,
      stepIndex,
      targetId,
    });
    fetchScoredValidationScorecard(validationSessionId)
      .then((nextScorecard) => {
        setScorecard(nextScorecard);
        setScorecardState('ready');
      })
      .catch(() => {
        setScorecard(null);
        setScorecardState('error');
      });
  }, [validationSessionId, logEvent, language, lessonPage, sceneSet, lessonId, stepId, stepIndex, targetId]);

  const backToLesson = useCallback(() => {
    setAppView('lesson');
    updateLessonUrl(language, lessonPage, sceneSet, true, null);
  }, [language, lessonPage, sceneSet]);

  return {
    appView,
    scorecardState,
    scorecard,
    showScorecard,
    backToLesson,
    resetScorecard,
  };
}
