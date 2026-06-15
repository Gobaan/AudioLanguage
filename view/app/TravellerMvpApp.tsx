import { useCallback, useEffect, useMemo } from 'react';

import { ValidationScorecardView } from './ScorecardView';
import { FitToViewport } from './FitToViewport';
import { TravellerLessonShell } from './TravellerLessonShell';
import { useActiveLessonStep } from './useActiveLessonStep';
import { useLessonLoader } from './useLessonLoader';
import { useParticipantId } from './useParticipantId';
import { useScorecard } from './useScorecard';
import { useTravellerRoute } from './useTravellerRoute';
import { viewFromUrl } from './lessonUrls';
import { useValidationSession } from './useValidationSession';
import { isLocalHost } from './urlParams';

export function TravellerMvpApp() {
  const { language, lessonPage, sceneSet, selectLessonPage } = useTravellerRoute();
  const participantId = useParticipantId();
  const { lessonTabs, lesson, loadState } = useLessonLoader({
    language,
    lessonPage,
    sceneSet,
    onLessonPageChange: selectLessonPage,
  });
  const { sessionId: validationSessionId, logEvent, captureAttempt } = useValidationSession({
    participantId,
    language,
    sceneSet,
    lessonPage,
  });

  const {
    stepLesson,
    step,
    stepIndex,
    isPlaying,
    selectedChoiceByStep,
    isLastStep,
    playStepAudio,
    logStepAudioPlayed,
    selectChoice,
    goToStep,
    handleCaptureAttempt,
  } = useActiveLessonStep({
    lesson,
    language,
    lessonPage,
    sceneSet,
    validationSessionId,
    logEvent,
    captureAttempt,
  });

  const { appView, scorecardState, scorecard, showScorecard, backToLesson, resetScorecard } = useScorecard({
    validationSessionId,
    logEvent,
    language,
    lessonPage,
    sceneSet,
    stepIndex,
    lessonId: stepLesson?.id,
    stepId: step?.id,
    targetId: stepLesson?.target.id,
  });

  useEffect(() => {
    resetScorecard();
  }, [language, sceneSet, resetScorecard]);

  useEffect(() => {
    if (viewFromUrl() !== 'scorecard' || !validationSessionId) {
      return;
    }

    showScorecard();
  }, [language, sceneSet, validationSessionId, showScorecard]);

  const nextLessonTab = useMemo(() => {
    const currentIndex = lessonTabs.findIndex((tab) => tab.id === lessonPage);
    if (currentIndex < 0) return null;
    return lessonTabs[currentIndex + 1] ?? null;
  }, [lessonTabs, lessonPage]);

  const debugLessonSwitcher = isLocalHost() ? (
    <nav className="lesson-switcher debug-lesson-switcher" aria-label="Local lesson jump">
      {lessonTabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={lessonPage === tab.id ? 'active' : ''}
          onClick={() => selectLessonPage(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  ) : null;

  const handleNext = useCallback(() => {
    if (!isLastStep) {
      goToStep('next');
      return;
    }
    if (nextLessonTab) {
      selectLessonPage(nextLessonTab.id);
      return;
    }
    showScorecard();
  }, [isLastStep, goToStep, nextLessonTab, selectLessonPage, showScorecard]);

  if (appView === 'scorecard') {
    return (
      <FitToViewport scrollable>
        <ValidationScorecardView
          sessionId={validationSessionId}
          state={scorecardState}
          scorecard={scorecard}
          onBack={backToLesson}
          onRefresh={showScorecard}
        />
      </FitToViewport>
    );
  }

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading first MVP step" />;
  }

  if (loadState === 'error' || !stepLesson || !step) {
    return <div className="frame-placeholder" aria-label="MVP step unavailable" />;
  }

  return (
    <FitToViewport>
      <TravellerLessonShell
        language={language}
        stepLesson={stepLesson}
        step={step}
        isPlaying={isPlaying}
        selectedChoiceByStep={selectedChoiceByStep}
        isLastStep={isLastStep}
        hasNextLesson={nextLessonTab !== null}
        onPlayAudio={playStepAudio}
        onLogAudioPlayed={logStepAudioPlayed}
        onSelectChoice={selectChoice}
        onCaptureAttempt={handleCaptureAttempt}
        onOpenScorecard={showScorecard}
        onNext={handleNext}
        debugLessonSwitcher={debugLessonSwitcher}
      />
    </FitToViewport>
  );
}
