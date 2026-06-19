import type { ReactNode } from 'react';

import type { CapturedRecording, ChoiceOption, Lesson, LessonStep } from '../components';
import { LessonAppLinks } from './LessonAppLinks';
import { LessonStepRenderer } from './LessonStepRenderer';
import { TransferTutorialModal } from './TransferTutorialModal';
import { stepBlocksNextUntilChoice, stepHandlesOwnNext } from './lessonStepHelpers';

type TravellerLessonShellProps = {
  language: string;
  stepLesson: Lesson;
  step: LessonStep;
  isPlaying: boolean;
  audioError?: string | null;
  selectedChoiceByStep: Record<string, string>;
  isLastStep: boolean;
  hasNextLesson: boolean;
  onPlayAudio: () => void;
  onLogAudioPlayed: () => void;
  onSelectChoice: (stepId: string, choice: ChoiceOption) => void;
  onCaptureAttempt: (
    step: LessonStep,
    recording: CapturedRecording,
    extra?: Record<string, unknown>,
  ) => void;
  onOpenScorecard: () => void;
  onNext: () => void;
  showTransferTutorial?: boolean;
  onDismissTransferTutorial?: () => void;
  debugLessonSwitcher?: ReactNode;
};

export function TravellerLessonShell({
  language,
  stepLesson,
  step,
  isPlaying,
  audioError,
  selectedChoiceByStep,
  isLastStep,
  hasNextLesson,
  onPlayAudio,
  onLogAudioPlayed,
  onSelectChoice,
  onCaptureAttempt,
  onOpenScorecard,
  onNext,
  showTransferTutorial = false,
  onDismissTransferTutorial,
  debugLessonSwitcher,
}: TravellerLessonShellProps) {
  const nextLabel = isLastStep ? (hasNextLesson ? 'Next' : 'Scorecard') : 'Next';
  const stepHandlesNext = !stepHandlesOwnNext(step);
  const nextBlocked = stepBlocksNextUntilChoice(step, selectedChoiceByStep[step.id]);

  return (
    <section className="traveller-mvp-app" aria-label="Traveller MVP step">
      <LessonAppLinks onOpenScorecard={onOpenScorecard} />
      {debugLessonSwitcher}
      {audioError ? (
        <p className="audio-error" role="alert">
          {audioError}
        </p>
      ) : null}
      <div className="lesson-step-with-tutorial">
        <LessonStepRenderer
          lesson={stepLesson}
          step={step}
          language={language}
          isPlaying={isPlaying}
          selectedChoiceId={selectedChoiceByStep[step.id]}
          suspendSceneAutoplay={showTransferTutorial && step.type === 'scene_setup'}
          onPlayAudio={onPlayAudio}
          onLogAudioPlayed={onLogAudioPlayed}
          onSelectChoice={onSelectChoice}
          onCaptureAttempt={onCaptureAttempt}
          onStepComplete={onNext}
          nextLabel={nextLabel}
        />
        {showTransferTutorial && onDismissTransferTutorial ? (
          <TransferTutorialModal onDismiss={onDismissTransferTutorial} />
        ) : null}
      </div>
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
