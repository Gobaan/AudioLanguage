import { useCallback, useRef, useState } from 'react';

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
  const scorecardRequestRef = useRef(0);
  const [appView, setAppView] = useState<AppView>(() => (viewFromUrl() === 'scorecard' ? 'scorecard' : 'lesson'));
  const [scorecardState, setScorecardState] = useState<ScorecardState>(() =>
    viewFromUrl() === 'scorecard' ? 'loading' : 'idle',
  );
  const [scorecard, setScorecard] = useState<ValidationScorecard | null>(null);

  const resetScorecard = useCallback(() => {
    scorecardRequestRef.current += 1;
    setAppView('lesson');
    setScorecard(null);
    setScorecardState('idle');
  }, []);

  const showScorecard = useCallback(() => {
    const requestId = scorecardRequestRef.current + 1;
    scorecardRequestRef.current = requestId;
    if (!validationSessionId) {
      if (scorecardRequestRef.current !== requestId) {
        return;
      }
      setScorecardState('error');
      setAppView('scorecard');
      return;
    }

    setScorecard(null);
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
        if (scorecardRequestRef.current !== requestId) {
          return;
        }
        setScorecard(nextScorecard);
        setScorecardState('ready');
      })
      .catch(() => {
        if (scorecardRequestRef.current !== requestId) {
          return;
        }
        setScorecard(null);
        setScorecardState('error');
      });
  }, [validationSessionId, logEvent, language, lessonPage, sceneSet, lessonId, stepId, stepIndex, targetId]);

  const backToLesson = useCallback(() => {
    scorecardRequestRef.current += 1;
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
