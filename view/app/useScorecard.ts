import { useCallback, useState } from 'react';

import { fetchValidationScorecard, type ValidationEvent, type ValidationScorecard } from '../api/validation';
import { ScorecardState } from './ScorecardView';

export type AppView = 'lesson' | 'scorecard';

type UseScorecardOptions = {
  validationSessionId: string | null;
  logEvent: (event: ValidationEvent) => void;
  lessonPage: string;
  stepIndex: number;
  lessonId?: string;
  stepId?: string;
  targetId?: string;
};

export function useScorecard({
  validationSessionId,
  logEvent,
  lessonPage,
  stepIndex,
  lessonId,
  stepId,
  targetId,
}: UseScorecardOptions) {
  const [appView, setAppView] = useState<AppView>('lesson');
  const [scorecardState, setScorecardState] = useState<ScorecardState>('idle');
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
    logEvent({
      type: 'scorecard_viewed',
      lessonId,
      lessonPage,
      stepId,
      stepIndex,
      targetId,
    });
    fetchValidationScorecard(validationSessionId, true)
      .then((nextScorecard) => {
        setScorecard(nextScorecard);
        setScorecardState('ready');
      })
      .catch(() => {
        setScorecard(null);
        setScorecardState('error');
      });
  }, [validationSessionId, logEvent, lessonId, lessonPage, stepId, stepIndex, targetId]);

  const backToLesson = useCallback(() => {
    setAppView('lesson');
  }, []);

  return {
    appView,
    scorecardState,
    scorecard,
    showScorecard,
    backToLesson,
    resetScorecard,
  };
}
