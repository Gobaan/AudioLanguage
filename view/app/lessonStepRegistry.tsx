import type { ReactNode } from 'react';

import {
  BackwardBuild,
  DialogueReveal,
  PromptedRecording,
  SceneFrame,
  ScenePlayback,
} from '../components';
import type { ChoiceOption, Lesson, LessonStep } from '../components';
import { MeaningGuessStep } from './MeaningGuessStep';
import { productionPracticeProps, ProductionPracticeStep } from './ProductionPracticeStep';
import {
  backwardBuildPrompts,
  backwardBuildTarget,
  dialogueRevealLines,
  frameForStep,
  sceneSetupFrames,
  sceneSetupStopAtLineType,
} from './lessonStepHelpers';
import { StepAudioButton } from './StepAudioButton';

export type LessonStepRenderContext = {
  lesson: Lesson;
  step: LessonStep;
  language: string;
  isPlaying?: boolean;
  selectedChoiceId?: string;
  onPlayAudio?: () => void;
  onLogAudioPlayed?: () => void;
  onSelectChoice?: (stepId: string, choice: ChoiceOption) => void;
  onCaptureAttempt?: (
    step: LessonStep,
    recording: { blob: Blob; durationMs: number; mimeType: string },
    extra?: Record<string, unknown>,
  ) => void;
  onStepComplete?: () => void;
  nextLabel?: string;
};

type StepRenderer = (context: LessonStepRenderContext) => ReactNode;

function framedStep(
  context: LessonStepRenderContext,
  children: ReactNode,
): ReactNode {
  const { lesson, step, isPlaying, onPlayAudio } = context;

  return (
    <section className="lesson-step-view" aria-label={step.type}>
      <SceneFrame
        frame={frameForStep(lesson, step)}
        isActive
        showCaption={false}
        placeholderLabel="Lesson scene frame"
      />
      {children}
      <StepAudioButton step={step} isPlaying={!!isPlaying} onPlayAudio={onPlayAudio} />
    </section>
  );
}

const STEP_RENDERERS: StepRenderer[] = [
  (context) => {
    if (context.step.component !== 'ProductionPrompt') return null;
    return (
      <ProductionPracticeStep
        {...productionPracticeProps(context.lesson, context.step, context.language)}
        onCaptureAttempt={context.onCaptureAttempt}
        onStepComplete={context.onStepComplete}
        nextLabel={context.nextLabel}
      />
    );
  },
  (context) => {
    if (context.step.type !== 'scene_recall' || !context.step.mic?.enabled) return null;
    return (
      <ProductionPracticeStep
        {...productionPracticeProps(context.lesson, context.step, context.language)}
        onCaptureAttempt={context.onCaptureAttempt}
        onStepComplete={context.onStepComplete}
        nextLabel={context.nextLabel}
      />
    );
  },
  (context) => {
    if (context.step.type !== 'scene_setup') return null;
    return (
      <ScenePlayback
        frames={sceneSetupFrames(context.lesson, context.step)}
        autoplay={context.step.audio?.autoplay}
        stopAtLineType={sceneSetupStopAtLineType(context.lesson, context.step)}
      />
    );
  },
  (context) => {
    if (context.step.component !== 'SceneFrame' && context.step.component !== 'AudioButton') return null;
    return framedStep(context, null);
  },
  (context) => {
    if (context.step.component !== 'ChoicePrompt') return null;
    return (
      <MeaningGuessStep
        lesson={context.lesson}
        step={context.step}
        language={context.language}
        isPlaying={context.isPlaying}
        selectedChoiceId={context.selectedChoiceId}
        onPlayAudio={context.onPlayAudio}
        onLogAudioPlayed={context.onLogAudioPlayed}
        onSelectChoice={context.onSelectChoice}
      />
    );
  },
  (context) => {
    if (context.step.component !== 'TranslationReveal') return null;
    return framedStep(context, <DialogueReveal lines={dialogueRevealLines(context.lesson)} />);
  },
  (context) => {
    if (context.step.component !== 'MicPrompt') return null;
    return (
      <section className="lesson-step-view" aria-label={context.step.type}>
        <SceneFrame
          frame={frameForStep(context.lesson, context.step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <PromptedRecording
          audioUrl={context.step.audio?.url}
          audioText={context.step.audio?.audioText}
          prompt="Now you say it."
          onCaptured={(recording) => context.onCaptureAttempt?.(context.step, recording)}
        />
      </section>
    );
  },
  (context) => {
    if (context.step.component !== 'BackwardBuild') return null;
    return (
      <section className="lesson-step-view" aria-label={context.step.type}>
        <SceneFrame
          frame={frameForStep(context.lesson, context.step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <BackwardBuild
          targetPhrase={backwardBuildTarget(context.step)}
          prompts={backwardBuildPrompts(context.step)}
          onCaptured={(recording, prompt) =>
            context.onCaptureAttempt?.(context.step, recording, {
              buildPromptId: prompt.id,
              buildPromptText: prompt.text,
              buildPromptAudioUrl: prompt.audioUrl ?? undefined,
            })
          }
          onStepComplete={context.onStepComplete}
        />
      </section>
    );
  },
];

export function renderLessonStep(context: LessonStepRenderContext): ReactNode {
  for (const renderer of STEP_RENDERERS) {
    const rendered = renderer(context);
    if (rendered !== null) {
      return rendered;
    }
  }

  return <div className="frame-placeholder" aria-label="Lesson step unavailable" />;
}
