import { AudioButton, ChoicePrompt, DialogueReveal, SceneFrame } from '../components';
import type { ChoiceOption, DialogueRevealLine, Lesson, LessonStep, SceneFrameData } from '../components';

type LessonStepRendererProps = {
  lesson: Lesson;
  step: LessonStep;
  isPlaying?: boolean;
  selectedChoiceId?: string;
  onPlayAudio?: () => void;
  onSelectChoice?: (stepId: string, choice: ChoiceOption) => void;
};

export function LessonStepRenderer({
  lesson,
  step,
  isPlaying = false,
  selectedChoiceId,
  onPlayAudio,
  onSelectChoice,
}: LessonStepRendererProps) {
  if (step.component === 'SceneFrame') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <StepAudioButton step={step} isPlaying={isPlaying} onPlayAudio={onPlayAudio} />
      </section>
    );
  }

  if (step.component === 'AudioButton') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <StepAudioButton step={step} isPlaying={isPlaying} onPlayAudio={onPlayAudio} />
      </section>
    );
  }

  if (step.component === 'ChoicePrompt') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <div className={selectedChoiceId ? 'choice-with-reveal revealed' : 'choice-with-reveal'}>
          <ChoicePrompt
            question={choiceQuestion(step)}
            choices={choiceOptions(step)}
            selectedChoiceId={selectedChoiceId}
            onSelectChoice={(choice) => onSelectChoice?.(step.id, choice)}
          />
          {selectedChoiceId ? <DialogueReveal lines={dialogueRevealLines(lesson)} /> : null}
        </div>
        <StepAudioButton step={step} isPlaying={isPlaying} onPlayAudio={onPlayAudio} />
      </section>
    );
  }

  return <div className="frame-placeholder" aria-label="Lesson step unavailable" />;
}

export function frameForStep(lesson: Lesson, step: LessonStep): SceneFrameData | undefined {
  return lesson.frames.find((frame) => frame.id === step.frameId) ?? lesson.frames[0];
}

function StepAudioButton({
  step,
  isPlaying,
  onPlayAudio,
}: {
  step: LessonStep;
  isPlaying: boolean;
  onPlayAudio?: () => void;
}) {
  if (!step.audio?.url) {
    return null;
  }

  return <AudioButton label="Play" isPlaying={isPlaying} disabled={isPlaying} onPlay={onPlayAudio} />;
}

function choiceQuestion(step: LessonStep): string | undefined {
  return typeof step.props.question === 'string' ? step.props.question : undefined;
}

function choiceOptions(step: LessonStep): ChoiceOption[] {
  return Array.isArray(step.props.choices) ? (step.props.choices as ChoiceOption[]).slice(0, 4) : [];
}

function dialogueRevealLines(lesson: Lesson): DialogueRevealLine[] {
  const learnerFrame = lesson.frames.find((frame) => frame.lineType === 'learner_target') ?? lesson.frames[1];

  return lesson.frames.map((frame) => {
    const isTranslated = frame.id === learnerFrame?.id;

    return {
      id: frame.id,
      speaker: frame.speaker,
      text: frame.text,
      audioUrl: frame.audioUrl,
      isTranslated,
      translation: isTranslated ? lesson.target.meaning : undefined,
    };
  });
}
