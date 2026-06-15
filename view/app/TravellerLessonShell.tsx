import type { ReactNode } from 'react';

import type { ChoiceOption, Lesson, LessonStep } from '../components';
import { LessonAppLinks } from './LessonAppLinks';
import { LessonStepRenderer } from './LessonStepRenderer';
import { stepBlocksNextUntilChoice, stepHandlesOwnNext } from './lessonStepHelpers';

type TravellerLessonShellProps = {
  language: string;
  stepLesson: Lesson;
  step: LessonStep;
  isPlaying: boolean;
  selectedChoiceByStep: Record<string, string>;
  isLastStep: boolean;
  hasNextLesson: boolean;
  onPlayAudio: () => void;
  onLogAudioPlayed: () => void;
  onSelectChoice: (stepId: string, choice: ChoiceOption) => void;
  onCaptureAttempt: (
    step: LessonStep,
    recording: { blob: Blob; durationMs: number; mimeType: string },
    extra?: Record<string, unknown>,
  ) => void;
  onOpenScorecard: () => void;
  onNext: () => void;
  debugLessonSwitcher?: ReactNode;
};

export function TravellerLessonShell({
  language,
  stepLesson,
  step,
  isPlaying,
  selectedChoiceByStep,
  isLastStep,
  hasNextLesson,
  onPlayAudio,
  onLogAudioPlayed,
  onSelectChoice,
  onCaptureAttempt,
  onOpenScorecard,
  onNext,
  debugLessonSwitcher,
}: TravellerLessonShellProps) {
  const nextLabel = isLastStep ? (hasNextLesson ? 'Next' : 'Scorecard') : 'Next';
  const stepHandlesNext = !stepHandlesOwnNext(step);
  const nextBlocked = stepBlocksNextUntilChoice(step, selectedChoiceByStep[step.id]);

  return (
    <section className="traveller-mvp-app" aria-label="Traveller MVP step">
      <LessonAppLinks onOpenScorecard={onOpenScorecard} />
      {debugLessonSwitcher}
      <LessonStepRenderer
        lesson={stepLesson}
        step={step}
        language={language}
        isPlaying={isPlaying}
        selectedChoiceId={selectedChoiceByStep[step.id]}
        onPlayAudio={onPlayAudio}
        onLogAudioPlayed={onLogAudioPlayed}
        onSelectChoice={onSelectChoice}
        onCaptureAttempt={onCaptureAttempt}
        onStepComplete={onNext}
        nextLabel={nextLabel}
      />
      {stepHandlesNext && !nextBlocked ? (
        <nav className="step-controls" aria-label="Lesson step controls">
          <button type="button" onClick={onNext}>
            {nextLabel}
          </button>
        </nav>
      ) : null}
    </section>
  );
}
