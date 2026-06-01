import { useEffect, useMemo, useRef, useState } from 'react';
import { fetchLessons } from '../api/lessons';
import type { ChoiceOption, Lesson, LessonStep } from '../components';
import { LessonStepRenderer } from './LessonStepRenderer';

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
type LessonPage = 'hello' | 'introduce' | 'repair' | 'food-order' | 'hospital';

const LESSON_TABS: Array<{ id: LessonPage; label: string }> = [
  { id: 'hello', label: 'Hello' },
  { id: 'introduce', label: 'Introduce' },
  { id: 'repair', label: 'Repair' },
  { id: 'food-order', label: 'Food' },
  { id: 'hospital', label: 'Hospital' },
];

export function TravellerMvpApp() {
  const [lessonPage, setLessonPage] = useState<LessonPage>(() => lessonPageFromUrl());
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [stepIndex, setStepIndex] = useState(0);
  const [selectedChoiceByStep, setSelectedChoiceByStep] = useState<Record<string, string>>({});
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    let isCurrent = true;

    fetchLessons('en', lessonPage)
      .then((payload) => {
        if (!isCurrent) return;
        setLesson(activeMvpLesson(payload.lessons[0] ?? FALLBACK_LESSON));
        setLoadState('ready');
      })
      .catch(() => {
        if (!isCurrent) return;
        setLesson(activeMvpLesson(FALLBACK_LESSON));
        setLoadState('ready');
      });

    return () => {
      isCurrent = false;
    };
  }, [lessonPage]);

  useEffect(() => {
    setStepIndex(0);
    setSelectedChoiceByStep({});
  }, [lessonPage]);

  const currentStep = lesson?.steps[stepIndex];
  const stepLesson = useMemo(() => withAssetUrls(lesson), [lesson]);
  const step = useMemo(() => withStepAssetUrls(currentStep), [currentStep]);

  useEffect(() => {
    return () => {
      stopAudio(audioRef.current);
    };
  }, []);

  useEffect(() => {
    stopAudio(audioRef.current);
    audioRef.current = null;
    setIsPlaying(false);
  }, [stepIndex]);

  function playStepAudio() {
    const audioUrl = step?.audio?.url;
    if (!audioUrl) return;

    stopAudio(audioRef.current);
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

  function selectChoice(stepId: string, choice: ChoiceOption) {
    setSelectedChoiceByStep((current) => ({
      ...current,
      [stepId]: choice.id,
    }));
  }

  function selectLessonPage(nextPage: LessonPage) {
    setLessonPage(nextPage);
    const url = new URL(window.location.href);
    url.searchParams.set('lesson', nextPage);
    window.history.pushState({}, '', url);
  }

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading first MVP step" />;
  }

  if (loadState === 'error' || !stepLesson || !step) {
    return <div className="frame-placeholder" aria-label="MVP step unavailable" />;
  }

  const isFirstStep = stepIndex === 0;
  const isLastStep = stepIndex >= stepLesson.steps.length - 1;

  return (
    <section className="traveller-mvp-app" aria-label="Traveller MVP step">
      <nav className="lesson-switcher" aria-label="Lesson test pages">
        {LESSON_TABS.map((tab) => (
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
      />
      <nav className="step-controls" aria-label="Lesson step controls">
        <button type="button" onClick={() => setStepIndex((value) => Math.max(0, value - 1))} disabled={isFirstStep}>
          Previous
        </button>
        <button
          type="button"
          onClick={() => setStepIndex((value) => Math.min(stepLesson.steps.length - 1, value + 1))}
          disabled={isLastStep}
        >
          Next
        </button>
      </nav>
    </section>
  );
}

function lessonPageFromUrl(): LessonPage {
  const lesson = new URLSearchParams(window.location.search).get('lesson');
  return LESSON_TABS.some((tab) => tab.id === lesson) ? (lesson as LessonPage) : 'hello';
}

function stopAudio(audio: HTMLAudioElement | null) {
  if (!audio) return;

  audio.pause();
  audio.currentTime = 0;
}

function activeMvpLesson(lesson: Lesson): Lesson {
  return {
    ...lesson,
    steps: lesson.steps.filter((step) => {
      if (step.id === 'translation_reveal') return false;
      if (step.id === 'audio_replay') return false;
      if (step.id === 'production_prompt') return false;
      if (step.id === 'backward_build') return shouldShowBackwardBuild(lesson.target.text);
      return true;
    }),
  };
}

function shouldShowBackwardBuild(targetText: string): boolean {
  return phraseWords(targetText).length >= 3;
}

function phraseWords(value: string): string[] {
  return value.match(/[\p{L}\p{N}']+/gu) ?? [];
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
