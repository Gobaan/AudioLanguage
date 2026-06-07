import { useEffect, useMemo, useRef, useState } from 'react';
import { fetchLessons } from '../api/lessons';
import {
  fetchSuggestedParticipantName,
  fetchValidationScorecard,
  logValidationEvent,
  startValidationSession,
  uploadValidationAttempt,
  validationAttemptAudioUrl,
  type ValidationScorecard,
} from '../api/validation';
import type { ChoiceOption, Lesson, LessonListResponse, LessonStep } from '../components';
import { LessonStepRenderer } from './LessonStepRenderer';

type LanguageOption = {
  id: string;
  label: string;
};

type LessonTab = {
  id: string;
  label: string;
};

const LANGUAGE_OPTIONS: LanguageOption[] = [
  { id: 'ja', label: 'Japanese' },
  { id: 'yue', label: 'Cantonese' },
  { id: 'ta', label: 'Tamil' },
  { id: 'en', label: 'English' },
];

const DEFAULT_LANGUAGE = 'ja';
const DEFAULT_LESSON = 'hello';
const DEFAULT_SCENE_SET = 'mvp';
const PARTICIPANT_STORAGE_KEY = 'audio-language-participant';

const FALLBACK_LESSON: Lesson = {
  id: 'en-card-first-hi-dialogue-practice',
  language: 'en',
  title: 'First hello dialogue',
  mode: 'ai_guided_response',
  stage: 'guided_scene_production',
  player_component: 'TravellerLessonPlayer',
  target: {
    id: 'en-target-respond-hi',
    text: 'Hi!',
    transliteration: '',
    meaning: 'Respond to Hi.',
  },
  frames: [
    {
      id: 'line-0',
      lineIndex: 0,
      frameNumber: 1,
      imageUrl: '/visuals/final/first-hi-response/frame-1.png',
      audioUrl: '/audio/generated/en/en-first-hi-response/line-0.mp3',
      title: 'World Opener',
      speaker: 'friend',
      text: 'Hi!',
      transliteration: '',
      lineType: 'world_opener',
    },
    {
      id: 'line-1',
      lineIndex: 1,
      frameNumber: 2,
      imageUrl: '/visuals/final/first-hi-response/frame-2.png',
      audioUrl: '/audio/generated/en/en-first-hi-response/line-1.mp3',
      title: 'Learner Target',
      speaker: 'learner',
      text: 'Hi!',
      transliteration: '',
      lineType: 'learner_target',
    },
    {
      id: 'line-2',
      lineIndex: 2,
      frameNumber: 3,
      imageUrl: '/visuals/final/first-hi-response/frame-3.png',
      audioUrl: '/audio/generated/en/en-first-hi-response/line-2.mp3',
      title: 'World Response',
      speaker: 'friend',
      text: 'Nice to see you.',
      transliteration: '',
      lineType: 'world_response',
    },
  ],
  steps: [
    {
      id: 'scene_setup',
      type: 'scene_setup',
      component: 'SceneFrame',
      frameId: 'line-0',
      frameMode: 'single',
      displayText: 'Listen.',
      audio: {
        url: '/audio/generated/en/en-first-hi-response/line-0.mp3',
        autoplay: true,
        replayable: true,
        playBeforeMic: false,
      },
      mic: {
        enabled: false,
        record: false,
        scoring: 'none',
      },
      props: {
        initialFrameId: 'line-0',
        frames: [],
      },
    },
    {
      id: 'target_audio',
      type: 'target_audio',
      component: 'AudioButton',
      frameId: 'line-1',
      frameMode: 'single',
      displayText: 'Listen to what they say.',
      audio: {
        url: '/audio/generated/en/en-first-hi-response/line-1.mp3',
        autoplay: true,
        replayable: true,
        playBeforeMic: false,
      },
      mic: {
        enabled: false,
        record: false,
        scoring: 'none',
      },
      props: {
        audioUrl: '/audio/generated/en/en-first-hi-response/line-1.mp3',
        text: {
          playLabel: 'Play',
          playingLabel: 'Playing',
        },
      },
    },
    {
      id: 'broad_meaning_guess',
      type: 'broad_meaning_guess',
      component: 'ChoicePrompt',
      frameId: 'line-2',
      frameMode: 'single',
      displayText: 'What happened?',
      audio: {
        url: '/audio/generated/en/en-first-hi-response/line-1.mp3',
        autoplay: false,
        replayable: true,
        playBeforeMic: false,
      },
      mic: {
        enabled: false,
        record: false,
        scoring: 'none',
      },
      props: {
        question: 'What happened?',
        choices: [
          {
            id: 'respond_to_greeting',
            label: 'They greeted the person back.',
            isCorrect: true,
          },
          {
            id: 'say_goodbye',
            label: 'They said goodbye.',
            isCorrect: false,
          },
          {
            id: 'ask_location',
            label: 'They asked where something is.',
            isCorrect: false,
          },
          {
            id: 'apologize',
            label: 'They apologized.',
            isCorrect: false,
          },
        ],
      },
    },
    {
      id: 'repeat_with_mic',
      type: 'repeat_with_mic',
      component: 'MicPrompt',
      frameId: 'line-1',
      frameMode: 'single',
      displayText: 'Now you say it.',
      audio: {
        url: '/audio/generated/en/en-first-hi-response/line-1.mp3',
        autoplay: true,
        replayable: true,
        playBeforeMic: true,
      },
      mic: {
        enabled: true,
        record: true,
        startsAfterAudio: true,
        scoring: 'deferred',
        continueOnRecord: true,
        blockingFeedback: false,
      },
      props: {
        expectedText: 'Hi!',
        expectedTransliteration: '',
      },
    },
  ],
};

type LoadState = 'loading' | 'ready' | 'error';
type AppView = 'lesson' | 'scorecard';
type ScorecardState = 'idle' | 'loading' | 'ready' | 'error';

export function TravellerMvpApp() {
  const [language, setLanguage] = useState(() => languageFromUrl());
  const [lessonPage, setLessonPage] = useState(() => lessonPageFromUrl());
  const [sceneSet] = useState(() => sceneSetFromUrl());
  const [lessonTabs, setLessonTabs] = useState<LessonTab[]>([]);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [stepIndex, setStepIndex] = useState(0);
  const [selectedChoiceByStep, setSelectedChoiceByStep] = useState<Record<string, string>>({});
  const [validationSessionId, setValidationSessionId] = useState<string | null>(null);
  const [appView, setAppView] = useState<AppView>('lesson');
  const [scorecardState, setScorecardState] = useState<ScorecardState>('idle');
  const [scorecard, setScorecard] = useState<ValidationScorecard | null>(null);
  const [participantId, setParticipantId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    let isCurrent = true;
    const urlParticipant = participantFromUrl();
    if (urlParticipant) {
      saveParticipantId(urlParticipant);
      setParticipantId(urlParticipant);
      return () => {
        isCurrent = false;
      };
    }

    const storedParticipant = localStorage.getItem(PARTICIPANT_STORAGE_KEY);
    if (storedParticipant) {
      setParticipantId(storedParticipant);
      return () => {
        isCurrent = false;
      };
    }

    fetchSuggestedParticipantName()
      .then((participant) => {
        if (!isCurrent) return;
        saveParticipantId(participant.participantId);
        setParticipantId(participant.participantId);
      })
      .catch(() => {
        if (!isCurrent) return;
        const fallbackParticipant = fallbackParticipantId();
        saveParticipantId(fallbackParticipant);
        setParticipantId(fallbackParticipant);
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  useEffect(() => {
    if (!participantId) return;

    let isCurrent = true;

    startValidationSession({
      sessionId: validationSessionIdForToday(participantId, language, sceneSet),
      language,
      sceneSet,
      lessonPage,
      participantId: participantId ?? undefined,
    })
      .then((session) => {
        if (isCurrent) {
          setValidationSessionId(session.sessionId);
        }
      })
      .catch(() => {
        if (isCurrent) {
          setValidationSessionId(null);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [language, sceneSet, participantId]);

  useEffect(() => {
    let isCurrent = true;

    async function loadLesson() {
      setLoadState('loading');
      try {
        const payload = await fetchLessons(language, lessonPage, sceneSet);
        if (!isCurrent) return;
        applyLessonPayload(payload);
        setLoadState('ready');
      } catch {
        try {
          const payload = await fetchLessons(language, DEFAULT_LESSON, sceneSet);
          if (!isCurrent) return;
          applyLessonPayload(payload);
          setLessonPage(DEFAULT_LESSON);
          updateLessonUrl(language, DEFAULT_LESSON, sceneSet, true);
          setLoadState('ready');
        } catch {
          if (!isCurrent) return;
          setLessonTabs([]);
          setLesson(activeMvpLesson(FALLBACK_LESSON));
          setLoadState('ready');
        }
      }
    }

    function applyLessonPayload(payload: LessonListResponse) {
      setLessonTabs(payload.lesson_tabs ?? []);
      setLesson(activeMvpLesson(payload.lessons[0] ?? FALLBACK_LESSON));
    }

    loadLesson();

    return () => {
      isCurrent = false;
    };
  }, [language, lessonPage, sceneSet]);

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
    return () => {
      stopAudio(audioRef.current);
      stopSpeech(utteranceRef.current);
    };
  }, []);

  useEffect(() => {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    audioRef.current = null;
    utteranceRef.current = null;
    setIsPlaying(false);
  }, [stepIndex]);

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
  }, [validationSessionId, stepLesson?.id, step?.id, stepIndex, lessonPage]);

  function playStepAudio() {
    const audioUrl = step?.audio?.url;
    const audioText = step?.audio?.audioText;
    if (!audioUrl && !audioText) return;

    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
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
    if (!audioUrl) {
      speakStepAudio(audioText);
      return;
    }

    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    setIsPlaying(true);

    audio.addEventListener(
      'ended',
      () => {
        setIsPlaying(false);
        audioRef.current = null;
      },
      { once: true },
    );

    audio.addEventListener(
      'error',
      () => {
        setIsPlaying(false);
        audioRef.current = null;
      },
      { once: true },
    );

    audio.play().catch(() => {
      setIsPlaying(false);
      audioRef.current = null;
    });
  }

  function speakStepAudio(audioText: string | null | undefined) {
    const spokenText = audioText?.trim();
    if (!spokenText || !window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') {
      setIsPlaying(false);
      utteranceRef.current = null;
      return;
    }

    const utterance = new SpeechSynthesisUtterance(spokenText);
    utteranceRef.current = utterance;
    setIsPlaying(true);
    utterance.addEventListener(
      'end',
      () => {
        setIsPlaying(false);
        utteranceRef.current = null;
      },
      { once: true },
    );
    utterance.addEventListener(
      'error',
      () => {
        setIsPlaying(false);
        utteranceRef.current = null;
      },
      { once: true },
    );
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
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

  function captureAttempt(
    attemptStep: LessonStep,
    recording: { blob: Blob; durationMs: number; mimeType: string },
    extra: Record<string, unknown> = {},
  ) {
    if (!validationSessionId || !stepLesson) return;

    const attemptId = crypto.randomUUID();
    void uploadValidationAttempt(validationSessionId, recording.blob, {
      attemptId,
      participantId,
      language,
      sceneSet,
      lessonId: stepLesson.id,
      lessonPage,
      stepId: attemptStep.id,
      targetId: stepLesson.target.id,
      expectedText: attemptStep.mic?.expectedText ?? stepLesson.target.text,
      expectedTransliteration: attemptStep.mic?.expectedTransliteration ?? stepLesson.target.transliteration,
      targetAudioUrl: learnerTargetAudioUrl(stepLesson),
      recordingDurationMs: recording.durationMs,
      byteCount: recording.blob.size,
      mimeType: recording.mimeType,
      buildPromptId: typeof extra.buildPromptId === 'string' ? extra.buildPromptId : undefined,
      buildPromptText: typeof extra.buildPromptText === 'string' ? extra.buildPromptText : undefined,
    }).catch(() => undefined);
  }

  function logEvent(event: Parameters<typeof logValidationEvent>[1]) {
    if (!validationSessionId) return;

    void logValidationEvent(validationSessionId, {
      participantId: participantId ?? undefined,
      language,
      sceneSet,
      ...event,
    }).catch(() => undefined);
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
        {LANGUAGE_OPTIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            className={language === option.id ? 'active' : ''}
            onClick={() => selectLanguage(option.id)}
          >
            {option.label}
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
        onCaptureAttempt={captureAttempt}
      />
      <nav className="step-controls" aria-label="Lesson step controls">
        <button type="button" onClick={() => goToStep('previous')} disabled={isFirstStep}>
          Previous
        </button>
        <button
          type="button"
          onClick={() => (isLastStep ? showScorecard() : goToStep('next'))}
        >
          {isLastStep ? 'Scorecard' : 'Next'}
        </button>
      </nav>
    </section>
  );
}

function ValidationScorecardView({
  sessionId,
  state,
  scorecard,
  onBack,
  onRefresh,
}: {
  sessionId: string | null;
  state: ScorecardState;
  scorecard: ValidationScorecard | null;
  onBack: () => void;
  onRefresh: () => void;
}) {
  return (
    <section className="validation-scorecard" aria-label="Validation scorecard">
      <header className="scorecard-header">
        <div>
          <span>Local validation</span>
          <h1>Scorecard</h1>
        </div>
        <nav className="scorecard-actions" aria-label="Scorecard controls">
          <button type="button" onClick={onBack}>
            Back
          </button>
          <button type="button" onClick={onRefresh}>
            Refresh
          </button>
        </nav>
      </header>

      {state === 'loading' ? <p className="scorecard-status">Loading scorecard.</p> : null}
      {state === 'error' ? (
        <p className="scorecard-status">Scorecard is unavailable. Session: {sessionId ?? 'none'}</p>
      ) : null}
      {state === 'ready' && scorecard ? <ScorecardDetails scorecard={scorecard} /> : null}
    </section>
  );
}

function ScorecardDetails({ scorecard }: { scorecard: ValidationScorecard }) {
  return (
    <>
      <dl className="scorecard-summary">
        <div>
          <dt>Session</dt>
          <dd>{scorecard.session.sessionId}</dd>
        </div>
        <div>
          <dt>Events</dt>
          <dd>{scorecard.eventCount}</dd>
        </div>
        <div>
          <dt>Attempts</dt>
          <dd>{scorecard.attemptCount}</dd>
        </div>
      </dl>

      <section className="scorecard-targets" aria-label="Scorecard targets">
        {scorecard.targets.length === 0 ? (
          <p className="scorecard-status">No recordings have been captured yet.</p>
        ) : (
          scorecard.targets.map((target) => (
            <article className="scorecard-target" key={target.targetId}>
              <header>
                <div>
                  <span>{target.targetId}</span>
                  <h2>{target.expectedTransliteration || target.expectedText || 'Target'}</h2>
                </div>
                {target.targetAudioUrl ? <audio controls src={target.targetAudioUrl} aria-label="Target audio" /> : null}
              </header>
              <ul>
                {target.attempts.map((attempt) => (
                  <li key={attempt.attemptId}>
                    <div>
                      <strong>{attempt.stepId}</strong>
                      <span>{scoreLabel(attempt)}</span>
                    </div>
                    <audio controls src={validationAttemptAudioUrl(scorecard.session.sessionId, attempt.attemptId)} />
                  </li>
                ))}
              </ul>
            </article>
          ))
        )}
      </section>
    </>
  );
}

function scoreLabel(attempt: { buildPromptText?: string; lessonPage?: string; aiScore?: unknown }): string {
  const score = attempt.aiScore as
    | { status?: string; result?: { communication?: { status?: string; confidence?: number } } }
    | null
    | undefined;
  if (!score) {
    return attempt.buildPromptText || attempt.lessonPage || 'Needs score';
  }
  if (score.status !== 'scored') {
    return 'AI score unavailable';
  }

  const communication = score.result?.communication;
  const confidence = typeof communication?.confidence === 'number' ? ` ${Math.round(communication.confidence * 100)}%` : '';
  return `${communication?.status || 'scored'}${confidence}`;
}

function languageFromUrl(): string {
  const language = new URLSearchParams(window.location.search).get('language');
  return LANGUAGE_OPTIONS.some((option) => option.id === language) ? language : DEFAULT_LANGUAGE;
}

function lessonPageFromUrl(): string {
  return new URLSearchParams(window.location.search).get('lesson') ?? DEFAULT_LESSON;
}

function sceneSetFromUrl(): string {
  return new URLSearchParams(window.location.search).get('scene_set') ?? DEFAULT_SCENE_SET;
}

function participantFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get('participant');
}

function saveParticipantId(participantId: string) {
  localStorage.setItem(PARTICIPANT_STORAGE_KEY, participantId);
}

function fallbackParticipantId(): string {
  return `Learner-${Math.floor(1000 + Math.random() * 9000)}`;
}

function isLocalHost(): boolean {
  return ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
}

function updateLessonUrl(language: string, lesson: string, sceneSet: string, replace = false) {
  const url = new URL(window.location.href);
  if (url.pathname !== '/learn') {
    url.pathname = '/learn';
  }
  url.searchParams.set('language', language);
  url.searchParams.set('lesson', lesson);
  if (sceneSet === DEFAULT_SCENE_SET) {
    url.searchParams.delete('scene_set');
  } else {
    url.searchParams.set('scene_set', sceneSet);
  }
  if (replace) {
    window.history.replaceState({}, '', url);
  } else {
    window.history.pushState({}, '', url);
  }
}

function stopAudio(audio: HTMLAudioElement | null) {
  if (!audio) return;

  audio.pause();
  audio.currentTime = 0;
}

function stopSpeech(utterance: SpeechSynthesisUtterance | null) {
  if (!utterance) return;

  window.speechSynthesis?.cancel();
}

function validationSessionIdForToday(participantId: string, language: string, sceneSet: string): string {
  return ['validation', safeId(participantId), safeId(language), safeId(sceneSet), localDateKey()].join('-');
}

function localDateKey(): string {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function safeId(value: string): string {
  return value.replace(/[^A-Za-z0-9_.-]+/g, '-');
}

function learnerTargetAudioUrl(lesson: Lesson): string | null {
  return lesson.frames.find((frame) => frame.lineType === 'learner_target')?.audioUrl ?? null;
}

function activeMvpLesson(lesson: Lesson): Lesson {
  return {
    ...lesson,
    steps: lesson.steps.filter((step) => {
      if (step.id === 'translation_reveal') return false;
      if (step.id === 'audio_replay') return false;
      if (step.id === 'production_prompt') return false;
      return true;
    }),
  };
}

function withAssetUrls(lesson: Lesson | null): Lesson | null {
  if (!lesson) return null;

  return {
    ...lesson,
    frames: lesson.frames.map((frame) => ({
      ...frame,
      imageUrl: frame.imageUrl ? assetUrl(frame.imageUrl) : frame.imageUrl,
      audioUrl: frame.audioUrl ? assetUrl(frame.audioUrl) : frame.audioUrl,
    })),
  };
}

function withStepAssetUrls(step: LessonStep | undefined): LessonStep | undefined {
  if (!step) return undefined;

  return {
    ...step,
    audio: step.audio
      ? {
          ...step.audio,
          url: step.audio.url ? assetUrl(step.audio.url) : step.audio.url,
        }
      : step.audio,
  };
}

function assetUrl(url: string): string {
  if (window.location.protocol !== 'file:' || !url.startsWith('/')) {
    return url;
  }

  return `../../model/assets${url}`;
}
