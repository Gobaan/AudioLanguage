import { useCallback, useEffect, useMemo, useState } from 'react';

import { ValidationScorecardView } from './ScorecardView';
import { FitToViewport } from './FitToViewport';
import { LearnerSessionLanding } from './LearnerSessionLanding';
import { PlanSelectionDebugPanel } from './PlanSelectionDebugPanel';
import { RecommendPhraseButton } from './RecommendPhraseButton';
import { TravellerLessonShell } from './TravellerLessonShell';
import { tutorialForLesson } from './lessonTutorials';
import { useAssetPrefetcher } from './useAssetPrefetcher';
import { useActiveLessonStep } from './useActiveLessonStep';
import { useLessonLoader } from './useLessonLoader';
import { useParticipantId } from './useParticipantId';
import { useScorecard } from './useScorecard';
import { dismissTutorial, isTutorialDismissed } from './transferTutorialStorage';
import { useTravellerRoute } from './useTravellerRoute';
import { START_LESSON, updateLessonUrl, viewFromUrl } from './lessonUrls';
import { useValidationSession } from './useValidationSession';
import { isLocalHost } from './urlParams';

type SessionPhase = 'landing' | 'running' | 'complete';

export function TravellerMvpApp() {
  const { language, lessonPage, sceneSet, selectLessonPage } = useTravellerRoute();
  const participantId = useParticipantId();
  const [sessionPhase, setSessionPhase] = useState<SessionPhase>('landing');
  const [sessionRequestId, setSessionRequestId] = useState(1);
  const [dismissedTutorials, setDismissedTutorials] = useState<Record<string, true>>({});

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
    setSessionRequestId(1);
  }, [language, sceneSet, resetScorecard]);

  useEffect(() => {
    if (viewFromUrl() !== 'scorecard' || !validationSessionId || sessionPhase !== 'running') {
      return;
    }

    showScorecard();
  }, [language, sceneSet, validationSessionId, sessionPhase, showScorecard]);

  const nextLessonTab = useMemo(() => {
    const currentLessonId = stepLesson?.id;
    if (!currentLessonId) {
      return null;
    }
    const currentIndex = lessons.findIndex((item) => item.id === currentLessonId);
    if (currentIndex < 0) {
      return null;
    }
    return lessonTabs[currentIndex + 1] ?? null;
  }, [lessonTabs, lessons, stepLesson?.id]);

  const nextLesson = useMemo(() => {
    const currentLessonId = stepLesson?.id;
    if (!currentLessonId) {
      return null;
    }
    const currentIndex = lessons.findIndex((item) => item.id === currentLessonId);
    if (currentIndex < 0) {
      return null;
    }
    return lessons[currentIndex + 1] ?? null;
  }, [lessons, stepLesson?.id]);

  useAssetPrefetcher({
    sessionPhase,
    firstLesson: lessons[0] ?? null,
    currentLesson: stepLesson ?? null,
    currentStepId: step?.id ?? null,
    nextLesson,
    isAudioPlaying: isPlaying,
  });

  const canBeginSession = loadState === 'ready' && lessons.length > 0 && scorecardState !== 'loading';

  const beginSession = useCallback(() => {
    if (!canBeginSession) {
      return;
    }
    resetScorecard();
    setSessionPhase('running');
    if (sessionPhase === 'complete') {
      setSessionRequestId((value) => value + 1);
    }
    selectLessonPage(START_LESSON);
    updateLessonUrl(language, START_LESSON, sceneSet, true, null);
  }, [canBeginSession, language, sceneSet, resetScorecard, selectLessonPage, sessionPhase]);

  const completeSession = useCallback(() => {
    setSessionPhase('complete');
    showScorecard();
  }, [showScorecard]);

  const handleDismissTutorial = useCallback((tutorialId: string) => {
    dismissTutorial(tutorialId);
    setDismissedTutorials((current) => ({ ...current, [tutorialId]: true }));
  }, []);

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
      resetScorecard();
      setSessionPhase('running');
      selectLessonPage(nextLessonTab.id);
      return;
    }
    completeSession();
  }, [isLastStep, goToStep, nextLessonTab, selectLessonPage, completeSession, resetScorecard]);

  if (appView === 'scorecard') {
    return (
      <FitToViewport scrollable>
        <ValidationScorecardView
          sessionId={validationSessionId}
          state={scorecardState}
          scorecard={scorecard}
          onBack={backToLesson}
          onRefresh={showScorecard}
          onNextLesson={sessionPhase === 'complete' ? beginSession : null}
        />
        <div className="learn-page-bottom-actions">
          <RecommendPhraseButton />
        </div>
      </FitToViewport>
    );
  }

  if (sessionPhase === 'landing' || sessionPhase === 'complete') {
    return (
      <FitToViewport scrollable={isLocalHost()}>
        <LearnerSessionLanding
          language={language}
          displayName={displayName}
          lessonCount={lessons.length}
          sessionPhase={sessionPhase}
          planState={loadState === 'idle' ? 'loading' : loadState}
          participantReady={participantId !== null}
          participantId={participantId}
          actionsDisabled={scorecardState === 'loading'}
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
        <div className="learn-page-bottom-actions">
          <RecommendPhraseButton />
        </div>
      </FitToViewport>
    );
  }

  if (loadState === 'loading' || loadState === 'idle') {
    return (
      <FitToViewport>
        <section className="learner-session-landing" aria-label="Loading session queue">
          <header>
            <span>Audio Language</span>
            <h1>Loading your next session...</h1>
            <p>Scoring and queue selection can take a moment.</p>
          </header>
        </section>
        <div className="learn-page-bottom-actions">
          <RecommendPhraseButton />
        </div>
      </FitToViewport>
    );
  }

  if (loadState === 'error' || lessons.length === 0 || !lesson) {
    return (
      <FitToViewport scrollable={isLocalHost()}>
        <LearnerSessionLanding
          language={language}
          displayName={displayName}
          lessonCount={lessons.length}
          sessionPhase="landing"
          planState={loadState}
          participantReady={participantId !== null}
          participantId={participantId}
          actionsDisabled={scorecardState === 'loading'}
          onStartSession={beginSession}
          onContinue={beginSession}
        />
        <div className="learn-page-bottom-actions">
          <RecommendPhraseButton />
        </div>
      </FitToViewport>
    );
  }

  if (!stepLesson || !step) {
    return (
      <FitToViewport>
        <section className="learner-session-landing" aria-label="MVP step unavailable">
          <header>
            <span>Audio Language</span>
            <h1>Loading your next scene...</h1>
            <p>Preparing lesson steps.</p>
          </header>
        </section>
        <div className="learn-page-bottom-actions">
          <RecommendPhraseButton />
        </div>
      </FitToViewport>
    );
  }

  const activeTutorial = sessionPhase === 'running' ? tutorialForLesson(stepLesson) : null;
  const tutorialDismissed = activeTutorial
    ? dismissedTutorials[activeTutorial.dismissId] === true || isTutorialDismissed(activeTutorial.dismissId)
    : true;
  const tutorial = activeTutorial && !tutorialDismissed ? activeTutorial : null;

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
        tutorial={tutorial}
        onDismissTutorial={tutorial ? () => handleDismissTutorial(tutorial.dismissId) : undefined}
        onPlayAudio={playStepAudio}
        onLogAudioPlayed={logStepAudioPlayed}
        onSelectChoice={selectChoice}
        onCaptureAttempt={handleCaptureAttempt}
        onOpenScorecard={showScorecard}
        onNext={handleNext}
        debugLessonSwitcher={debugLessonSwitcher}
      />
      <div className="learn-page-bottom-actions">
        <RecommendPhraseButton />
      </div>
    </FitToViewport>
  );
}
