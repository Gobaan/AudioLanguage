import type { ChoiceOption, Lesson, LessonStep } from '../components';
import { frameForStep } from './lessonStepHelpers';
import { renderLessonStep } from './lessonStepRegistry';

type LessonStepRendererProps = {
  lesson: Lesson;
  step: LessonStep;
  isPlaying?: boolean;
  selectedChoiceId?: string;
  onPlayAudio?: () => void;
  onSelectChoice?: (stepId: string, choice: ChoiceOption) => void;
  onCaptureAttempt?: (
    step: LessonStep,
    recording: { blob: Blob; durationMs: number; mimeType: string },
    extra?: Record<string, unknown>,
  ) => void;
};

export function LessonStepRenderer(props: LessonStepRendererProps) {
  return renderLessonStep(props);
}

export { frameForStep };
