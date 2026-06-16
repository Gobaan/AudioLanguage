import type { CapturedRecording, ChoiceOption, Lesson, LessonStep } from '../components';
import { frameForStep } from './lessonStepHelpers';
import { renderLessonStep } from './lessonStepRegistry';

type LessonStepRendererProps = {
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
    recording: CapturedRecording,
    extra?: Record<string, unknown>,
  ) => void;
  onStepComplete?: () => void;
  nextLabel?: string;
};

export function LessonStepRenderer(props: LessonStepRendererProps) {
  return renderLessonStep(props);
}

export { frameForStep };
