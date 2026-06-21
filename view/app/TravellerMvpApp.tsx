import { useCallback, useEffect, useMemo, useState } from 'react';

import { fetchLessons, relearnTarget } from '../api/lessons';
import type { ScorecardTarget } from '../api/validation';
import { ScenePlayback, type Lesson } from '../components';
import { ValidationScorecardView } from './ScorecardView';
import { FitToViewport } from './FitToViewport';
import { LearnerSessionLanding } from './LearnerSessionLanding';
import { PlanSelectionDebugPanel } from './PlanSelectionDebugPanel';
import { RecommendPhraseButton } from './RecommendPhraseButton';
import { TravellerLessonShell } from './TravellerLessonShell';
import { tutorialForLesson } from './lessonTutorials';
import { lessonSupportsRelearn } from './lessonStepHelpers';
import { useAssetPrefetcher } from './useAssetPrefetcher';
import { useActiveLessonStep } from './useActiveLessonStep';
import { useLessonLoader } from './useLessonLoader';
import { useParticipantId } from './useParticipantId';
import { useScorecard } from './useScorecard';
import { dismissTutorial, isTutorialDismissed } from './transferTutorialStorage';
import { useTravellerRoute } from './useTravellerRoute';
import { activeMvpLesson, START_LESSON, updateLessonUrl, viewFromUrl, withAssetUrls } from './lessonUrls';
import { useValidationSession } from './useValidationSession';
import { isLocalHost } from './urlParams';

type SessionPhase = 'landing' | 'running' | 'complete';

export function TravellerMvpApp() {
  const { language, lessonPage, sceneSet, selectLessonPage } = useTravellerRoute();
  const {
    participantId,
    authStatus,
    authError,
    googleAccount,
    linkGoogleCredential,
  } = useParticipantId();
  const [sessionPhase, setSessionPhase] = useState<SessionPhase>('landing');
  const [sessionRequestId, setSessionRequestId] = useState(1);
  const [dismissedTutorials, setDismissedTutorials] = useState<Record<string, true>>({});
  const [anchorReviewLesson, setAnchorReviewLesson] = useState<Lesson | null>(null);
  const [anchorReviewState, setAnchorReviewState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [isRelearning, setIsRelearning] = useState(false);
  const [relearnError, setRelearnError] = useState<string | null>(null);

  const {
    lessonTabs,
    lessons,
    lesson,
    displayName,
    planVersion,
    sessionId,
    loadState,
    insertLessonBundleAfter,
  } = useLessonLoader({
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
    setRelearnError(null);
    setIsRelearning(false);
  }, [language, sceneSet, participantId, resetScorecard]);

  useEffect(() => {
    setRelearnError(null);
    setIsRelearning(false);
  }, [lessonPage]);

  useEffect(() => {
    if (viewFromUrl() !== 'scorecard' || !validationSessionId || sessionPhase !== 'running') {
      return;
    }

    showScorecard();
  }, [language, sceneSet, validationSessionId, sessionPhase, showScorecard]);

  const nextLessonTab = useMemo(() => {
    const currentIndex = lessonTabs.findIndex((tab) => tab.id === lessonPage);
    if (currentIndex < 0) {
      return null;
    }
    return lessonTabs[currentIndex + 1] ?? null;
  }, [lessonPage, lessonTabs]);

  const nextLesson = useMemo(() => {
    const currentIndex = lessonTabs.findIndex((tab) => tab.id === lessonPage);
    if (currentIndex < 0) {
      return null;
    }
    return lessons[currentIndex + 1] ?? null;
  }, [lessonPage, lessonTabs, lessons]);

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

  const handleViewAnchor = useCallback(
    async (target: ScorecardTarget) => {
      if (!target.anchorLessonPage) {
        return;
      }

      setAnchorReviewLesson(null);
      setAnchorReviewState('loading');
      try {
        const payload = await fetchLessons(language, target.anchorLessonPage, sceneSet);
        const anchorLesson = payload.lessons.find((item) => item.id === target.anchorLessonId) ?? payload.lessons[0];
        if (!anchorLesson) {
          throw new Error('Anchor lesson was not returned.');
        }
        setAnchorReviewLesson(activeMvpLesson(anchorLesson));
        setAnchorReviewState('idle');
      } catch {
        setAnchorReviewState('error');
      }
    },
    [language, sceneSet],
  );

  const handleBackFromAnchorReview = useCallback(() => {
    setAnchorReviewLesson(null);
    setAnchorReviewState('idle');
  }, []);

  const handleRelearn = useCallback(
    async () => {
      if (!participantId || !stepLesson || !lessonSupportsRelearn(stepLesson)) {
        setRelearnError('Relearn is unavailable until a participant is ready.');
        return;
      }

      setRelearnError(null);
      setIsRelearning(true);
      try {
        const bundle = await relearnTarget({
          language,
          participantId,
          targetId: stepLesson.target.id,
        });
        const firstInsertedPage = insertLessonBundleAfter(
          lessonPage,
          bundle.lesson_tabs ?? [],
          bundle.lessons ?? [],
        );
        logEvent({
          type: 'relearn_requested',
          lessonId: stepLesson.id,
          lessonPage,
          stepId: step?.id,
          stepIndex,
          targetId: stepLesson.target.id,
          planPurpose: stepLesson.planPurpose,
          repairCategory: stepLesson.repairCategory,
          lessonStage: stepLesson.stage,
        });

        if (firstInsertedPage) {
          resetScorecard();
          setSessionPhase('running');
          selectLessonPage(firstInsertedPage);
          updateLessonUrl(language, firstInsertedPage, sceneSet, true, null);
        }
      } catch (error) {
        setRelearnError(relearnErrorMessage(error));
      } finally {
        setIsRelearning(false);
      }
    },
    [
      insertLessonBundleAfter,
      language,
      lessonPage,
      logEvent,
      participantId,
      resetScorecard,
      sceneSet,
      selectLessonPage,
      step?.id,
      stepIndex,
      stepLesson,
    ],
  );

  if (appView === 'scorecard') {
    return (
      <FitToViewport scrollable>
        {anchorReviewLesson || anchorReviewState !== 'idle' ? (
          <ScorecardAnchorReview
            lesson={anchorReviewLesson}
            state={anchorReviewState}
            onBack={handleBackFromAnchorReview}
          />
        ) : (
          <ValidationScorecardView
            sessionId={validationSessionId}
            state={scorecardState}
            scorecard={scorecard}
            onBack={backToLesson}
            onRefresh={showScorecard}
            onNextLesson={sessionPhase === 'complete' ? beginSession : null}
            onViewAnchor={handleViewAnchor}
          />
        )}
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
          authStatus={authStatus}
          authError={authError}
          authEmail={googleAccount?.email ?? null}
          actionsDisabled={scorecardState === 'loading'}
          onStartSession={beginSession}
          onContinue={beginSession}
          onGoogleCredential={linkGoogleCredential}
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
          authStatus={authStatus}
          authError={authError}
          authEmail={googleAccount?.email ?? null}
          actionsDisabled={scorecardState === 'loading'}
          onStartSession={beginSession}
          onContinue={beginSession}
          onGoogleCredential={linkGoogleCredential}
        />
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
      </FitToViewport>
    );
  }

  const activeTutorial = sessionPhase === 'running' ? tutorialForLesson(stepLesson) : null;
  const tutorialDismissed = activeTutorial
    ? dismissedTutorials[activeTutorial.dismissId] === true || isTutorialDismissed(activeTutorial.dismissId)
    : true;
  const tutorial = activeTutorial && !tutorialDismissed ? activeTutorial : null;
  const relearnAction = lessonSupportsRelearn(stepLesson) ? handleRelearn : undefined;

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
        onRelearn={relearnAction}
        isRelearning={isRelearning}
        relearnError={relearnError}
        debugLessonSwitcher={debugLessonSwitcher}
      />
    </FitToViewport>
  );
}

function ScorecardAnchorReview({
  lesson,
  state,
  onBack,
}: {
  lesson: Lesson | null;
  state: 'idle' | 'loading' | 'error';
  onBack: () => void;
}) {
  return (
    <section className="scorecard-anchor-review" aria-label="Anchor review">
      <header className="scorecard-header">
        <div>
          <span>Anchor</span>
          <h1>Anchor scene</h1>
        </div>
        <nav className="scorecard-actions" aria-label="Anchor review controls">
          <button type="button" onClick={onBack}>
            Back
          </button>
        </nav>
      </header>
      {state === 'loading' ? <p className="scorecard-status">Loading anchor...</p> : null}
      {state === 'error' ? <p className="scorecard-status">Anchor is unavailable.</p> : null}
      {lesson ? <ScenePlayback frames={withAssetUrls(lesson)?.frames ?? []} autoplay /> : null}
    </section>
  );
}

function relearnErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return `Could not add relearn scenes: ${error.message}`;
  }
  return 'Could not add relearn scenes.';
}
