import { useEffect, useMemo, useState } from 'react';

import { fetchLanguages, type LanguageSummary } from '../api/languages';
import { fetchValidationScorecard, type ValidationScorecard } from '../api/validation';
import type { ChoiceOption, LessonStep } from '../components';
import { LessonStepRenderer } from './LessonStepRenderer';
import {
  DEFAULT_LESSON,
  languageFromUrl,
  lessonPageFromUrl,
  sceneSetFromUrl,
  updateLessonUrl,
  withAssetUrls,
  withStepAssetUrls,
} from './lessonUrls';
import { ScorecardState, ValidationScorecardView } from './ScorecardView';
import { useAudioPlayback } from './useAudioPlayback';
import { useLessonLoader } from './useLessonLoader';
import { useParticipantId } from './useParticipantId';
import { useValidationSession } from './useValidationSession';
import { isLocalHost } from './urlParams';

type AppView = 'lesson' | 'scorecard';

export function TravellerMvpApp() {
  const [language, setLanguage] = useState(() => languageFromUrl());
  const [lessonPage, setLessonPage] = useState(() => lessonPageFromUrl());
  const [sceneSet] = useState(() => sceneSetFromUrl());
  const [stepIndex, setStepIndex] = useState(0);
  const [selectedChoiceByStep, setSelectedChoiceByStep] = useState<Record<string, string>>({});
  const [appView, setAppView] = useState<AppView>('lesson');
  const [scorecardState, setScorecardState] = useState<ScorecardState>('idle');
  const [scorecard, setScorecard] = useState<ValidationScorecard | null>(null);
  const [languageOptions, setLanguageOptions] = useState<LanguageSummary[]>([]);

  const participantId = useParticipantId();

  useEffect(() => {
    let isCurrent = true;
    fetchLanguages()
      .then((payload) => {
        if (!isCurrent) return;
        setLanguageOptions(payload);
      })
      .catch(() => {
        if (!isCurrent) return;
        setLanguageOptions([]);
      });

    return () => {
      isCurrent = false;
    };
  }, []);
  const { lessonTabs, lesson, loadState } = useLessonLoader({
    language,
    lessonPage,
    sceneSet,
    onLessonPageChange: setLessonPage,
  });
  const { sessionId: validationSessionId, logEvent, captureAttempt } = useValidationSession({
    participantId,
    language,
    sceneSet,
    lessonPage,
  });
  const { isPlaying, playAudioOrSpeak, stop: stopPlayback } = useAudioPlayback();

  useEffect(() => {
    setStepIndex(0);
    setSelectedChoiceByStep({});
    setAppView('lesson');
    setScorecard(null);
    setScorecardState('idle');
  }, [language, lessonPage, sceneSet]);

  const currentStep = lesson?.steps[stepIndex];
  const stepLesson = useMemo(() => withAssetUrls(lesson), [lesson]);
  const step = useMemo(() => withStepAssetUrls(currentStep), [currentStep]);

  useEffect(() => {
    stopPlayback();
  }, [stepIndex, stopPlayback]);

  useEffect(() => {
    if (!validationSessionId || !stepLesson || !step) return;

    logEvent({
      type: 'page_view',
      lessonId: stepLesson.id,
      lessonPage,
      stepId: step.id,
      stepIndex,
      frameId: step.frameId,
      targetId: stepLesson.target.id,
    });
  }, [validationSessionId, stepLesson?.id, step?.id, stepIndex, lessonPage, logEvent]);

  function playStepAudio() {
    const audioUrl = step?.audio?.url;
    const audioText = step?.audio?.audioText;
    if (!audioUrl && !audioText) return;

    if (stepLesson && step) {
      logEvent({
        type: 'audio_played',
        lessonId: stepLesson.id,
        lessonPage,
        stepId: step.id,
        stepIndex,
        frameId: step.frameId,
        targetId: stepLesson.target.id,
      });
    }

    playAudioOrSpeak(audioUrl, audioText, language);
  }

  function selectChoice(stepId: string, choice: ChoiceOption) {
    setSelectedChoiceByStep((current) => ({
      ...current,
      [stepId]: choice.id,
    }));
    if (stepLesson) {
      logEvent({
        type: 'choice_selected',
        lessonId: stepLesson.id,
        lessonPage,
        stepId,
        stepIndex,
        choiceId: choice.id,
        isCorrect: choice.isCorrect,
        targetId: stepLesson.target.id,
      });
    }
  }

  function selectLanguage(nextLanguage: string) {
    setLanguage(nextLanguage);
    setLessonPage(DEFAULT_LESSON);
    updateLessonUrl(nextLanguage, DEFAULT_LESSON, sceneSet);
  }

  function selectLessonPage(nextPage: string) {
    setLessonPage(nextPage);
    updateLessonUrl(language, nextPage, sceneSet);
  }

  function goToStep(direction: 'previous' | 'next') {
    setStepIndex((value) => {
      const nextValue =
        direction === 'previous'
          ? Math.max(0, value - 1)
          : Math.min((stepLesson?.steps.length ?? 1) - 1, value + 1);
      if (nextValue !== value && stepLesson && step) {
        logEvent({
          type: 'navigation',
          direction,
          lessonId: stepLesson.id,
          lessonPage,
          stepId: step.id,
          stepIndex: value,
          frameId: step.frameId,
          targetId: stepLesson.target.id,
        });
      }
      return nextValue;
    });
  }

  function showScorecard() {
    if (!validationSessionId) {
      setScorecardState('error');
      setAppView('scorecard');
      return;
    }

    setAppView('scorecard');
    setScorecardState('loading');
    logEvent({
      type: 'scorecard_viewed',
      lessonId: stepLesson?.id,
      lessonPage,
      stepId: step?.id,
      stepIndex,
      targetId: stepLesson?.target.id,
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
  }

  function handleCaptureAttempt(
    attemptStep: LessonStep,
    recording: { blob: Blob; durationMs: number; mimeType: string },
    extra: Record<string, unknown> = {},
  ) {
    if (!stepLesson) return;
    captureAttempt(stepLesson, attemptStep, recording, extra);
  }

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading first MVP step" />;
  }

  if (loadState === 'error' || !stepLesson || !step) {
    return <div className="frame-placeholder" aria-label="MVP step unavailable" />;
  }

  const isFirstStep = stepIndex === 0;
  const isLastStep = stepIndex >= stepLesson.steps.length - 1;

  if (appView === 'scorecard') {
    return (
      <ValidationScorecardView
        sessionId={validationSessionId}
        state={scorecardState}
        scorecard={scorecard}
        onBack={() => setAppView('lesson')}
        onRefresh={showScorecard}
      />
    );
  }

  return (
    <section className="traveller-mvp-app" aria-label="Traveller MVP step">
      {isLocalHost() ? (
        <nav className="local-app-links" aria-label="Local app links">
          {participantId ? <span>{participantId}</span> : null}
          <a href="/admin/validation">Admin</a>
        </nav>
      ) : null}
      <nav className="language-switcher" aria-label="Language">
        {(languageOptions.length > 0
          ? languageOptions
          : [{ id: language, display_name: language, description: '', scene_sets: ['mvp'] }]
        ).map((option) => (
          <button
            key={option.id}
            type="button"
            className={language === option.id ? 'active' : ''}
            onClick={() => selectLanguage(option.id)}
          >
            {option.display_name}
          </button>
        ))}
      </nav>
      <nav className="lesson-switcher" aria-label="Lesson test pages">
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
      <div className="page-number" aria-label={`Page ${stepIndex + 1} of ${stepLesson.steps.length}`}>
        Page {stepIndex + 1} / {stepLesson.steps.length}
      </div>
      <LessonStepRenderer
        lesson={stepLesson}
        step={step}
        isPlaying={isPlaying}
        selectedChoiceId={selectedChoiceByStep[step.id]}
        onPlayAudio={playStepAudio}
        onSelectChoice={selectChoice}
        onCaptureAttempt={handleCaptureAttempt}
      />
      <nav className="step-controls" aria-label="Lesson step controls">
        <button type="button" onClick={() => goToStep('previous')} disabled={isFirstStep}>
          Previous
        </button>
        <button type="button" onClick={() => (isLastStep ? showScorecard() : goToStep('next'))}>
          {isLastStep ? 'Scorecard' : 'Next'}
        </button>
      </nav>
    </section>
  );
}
