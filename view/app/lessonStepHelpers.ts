import type {
  BackwardBuildPrompt,
  ChoiceOption,
  DialogueRevealLine,
  Lesson,
  LessonStep,
  SceneFrameData,
} from '../components';

export function frameForStep(lesson: Lesson, step: LessonStep): SceneFrameData | undefined {
  return lesson.frames.find((frame) => frame.id === step.frameId) ?? lesson.frames[0];
}

export function sceneSetupFrames(lesson: Lesson, step: LessonStep): SceneFrameData[] {
  if (lesson.frames.length > 0) {
    return lesson.frames;
  }

  return Array.isArray(step.props.frames) ? (step.props.frames as SceneFrameData[]) : [];
}

export function choiceQuestion(step: LessonStep): string | undefined {
  return typeof step.props.question === 'string' ? step.props.question : undefined;
}

export function choiceOptions(step: LessonStep): ChoiceOption[] {
  return Array.isArray(step.props.choices) ? (step.props.choices as ChoiceOption[]).slice(0, 4) : [];
}

export function dialogueRevealLines(lesson: Lesson): DialogueRevealLine[] {
  const learnerFrame = lesson.frames.find((frame) => frame.lineType === 'learner_target') ?? lesson.frames[1];

  return lesson.frames.map((frame) => {
    const isTranslated = frame.id === learnerFrame?.id;

    return {
      id: frame.id,
      speaker: frame.speaker,
      text: frame.text,
      transliteration: frame.transliteration,
      audioUrl: frame.audioUrl,
      isTranslated,
      translation: isTranslated ? lesson.target.meaning : undefined,
    };
  });
}

export function productionPromptText(step: LessonStep): string {
  if (typeof step.displayText === 'string' && step.displayText) {
    return step.displayText;
  }

  if (typeof step.props.targetMeaning === 'string' && step.props.targetMeaning) {
    return `How do you say: ${step.props.targetMeaning}`;
  }

  return 'What do you say?';
}

export function recordingPromptText(step: LessonStep): string {
  return step.type === 'scene_recall' ? 'Now you respond.' : 'Now you say it.';
}

export function responseFrameForLesson(lesson: Lesson): SceneFrameData | undefined {
  return lesson.frames.find((frame) => frame.lineType === 'world_response');
}

export function learnerFrameForLesson(lesson: Lesson): SceneFrameData | undefined {
  return lesson.frames.find((frame) => frame.lineType === 'learner_target');
}

export function backwardBuildTarget(step: LessonStep): string | undefined {
  return typeof step.props.targetPhrase === 'string' ? step.props.targetPhrase : undefined;
}

export function backwardBuildPrompts(step: LessonStep): BackwardBuildPrompt[] {
  return Array.isArray(step.props.prompts) ? (step.props.prompts as BackwardBuildPrompt[]) : [];
}

export function stepHandlesOwnAutoplay(step: LessonStep): boolean {
  if (step.type === 'scene_setup') return true;
  if (step.component === 'MicPrompt') return true;
  if (step.component === 'ProductionPrompt') return true;
  if (step.type === 'scene_recall' && step.mic?.enabled) return true;
  return false;
}
