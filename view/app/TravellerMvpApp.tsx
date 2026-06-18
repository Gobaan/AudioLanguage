import { useCallback, useEffect, useMemo, useState } from 'react';

import { ValidationScorecardView } from './ScorecardView';
import { FitToViewport } from './FitToViewport';
import { LearnerSessionLanding } from './LearnerSessionLanding';
import { PlanSelectionDebugPanel } from './PlanSelectionDebugPanel';
import { TravellerLessonShell } from './TravellerLessonShell';
import { useActiveLessonStep } from './useActiveLessonStep';
import { useLessonLoader } from './useLessonLoader';
import { useParticipantId } from './useParticipantId';
import { useScorecard } from './useScorecard';
import { useTravellerRoute } from './useTravellerRoute';
import { START_LESSON, updateLessonUrl, viewFromUrl } from './lessonUrls';
import { useValidationSession } from './useValidationSession';
import { isLocalHost } from './urlParams';

type SessionPhase = 'landing' | 'running' | 'complete';

export function TravellerMvpApp() {
  const { language, lessonPage, sceneSet, selectLessonPage } = useTravellerRoute();
  const participantId = useParticipantId();
  const [sessionPhase, setSessionPhase] = useState<SessionPhase>('landing');
  const [sessionRequestId, setSessionRequestId] = useState(0);

  const { lessonTabs, lessons, lesson, displayName, planVersion, sessionId, loadState } = useLessonLoader({
    language,
    lessonPage,
    sceneSet,
    participantId,
    sessionRequestId,
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
    audioError,
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
    setSessionPhase('landing');
    setSessionRequestId(0);
  }, [language, sceneSet, resetScorecard]);

  useEffect(() => {
    if (viewFromUrl() !== 'scorecard' || !validationSessionId || sessionPhase !== 'running') {
      return;
    }

    showScorecard();
  }, [language, sceneSet, validationSessionId, sessionPhase, showScorecard]);

  const nextLessonTab = useMemo(() => {
    const currentIndex = lessonTabs.findIndex((tab) => tab.id === lessonPage);
    if (currentIndex < 0) return null;
    return lessonTabs[currentIndex + 1] ?? null;
  }, [lessonTabs, lessonPage]);

  const beginSession = useCallback(() => {
    resetScorecard();
    setSessionPhase('running');
    setSessionRequestId((value) => value + 1);
    selectLessonPage(START_LESSON);
    updateLessonUrl(language, START_LESSON, sceneSet, true, null);
  }, [language, sceneSet, resetScorecard, selectLessonPage]);

  const completeSession = useCallback(() => {
    resetScorecard();
    setSessionPhase('complete');
    selectLessonPage(START_LESSON);
    updateLessonUrl(language, START_LESSON, sceneSet, true, null);
  }, [language, sceneSet, resetScorecard, selectLessonPage]);

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

  const debugPlanPanel =
    isLocalHost() && lessons.length > 0 ? (
      <PlanSelectionDebugPanel
        lessons={lessons}
        lessonTabs={lessonTabs}
        currentLessonPage={lessonPage}
        planVersion={planVersion}
        sessionId={sessionId}
      />
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
    completeSession();
  }, [isLastStep, goToStep, nextLessonTab, selectLessonPage, completeSession]);

  if (sessionPhase === 'landing' || sessionPhase === 'complete') {
    return (
      <FitToViewport scrollable={isLocalHost()}>
        <LearnerSessionLanding
          language={language}
          displayName={displayName}
          lessonCount={lessons.length}
          sessionPhase={sessionPhase}
          participantReady={participantId !== null}
          onStartSession={beginSession}
          onContinue={beginSession}
        />
        {isLocalHost() && sessionPhase === 'complete' && lessons.length > 0 ? (
          <PlanSelectionDebugPanel
            lessons={lessons}
            lessonTabs={lessonTabs}
            planVersion={planVersion}
            sessionId={sessionId}
          />
        ) : null}
      </FitToViewport>
    );
  }

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

  if (loadState === 'loading' || loadState === 'idle') {
    return <div className="frame-placeholder" aria-label="Loading session queue" />;
  }

  if (loadState === 'error' || !stepLesson || !step) {
    return <div className="frame-placeholder" aria-label="MVP step unavailable" />;
  }

  return (
    <FitToViewport scrollable={isLocalHost()}>
      {debugPlanPanel}
      <TravellerLessonShell
        language={language}
        stepLesson={stepLesson}
        step={step}
        isPlaying={isPlaying}
        audioError={audioError}
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
