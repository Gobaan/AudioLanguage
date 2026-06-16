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

export function sceneSetupStopAtLineType(lesson: Lesson, step: LessonStep): string | undefined {
  if (typeof step.props.stopAtLineType === 'string' && step.props.stopAtLineType) {
    return step.props.stopAtLineType;
  }

  if (lesson.stage === 'same_day_transfer' || lesson.stage === 'delayed_review') {
    return 'world_opener';
  }

  return undefined;
}

export function sceneSetupFrames(lesson: Lesson, step: LessonStep): SceneFrameData[] {
  const frames =
    lesson.frames.length > 0
      ? lesson.frames
      : Array.isArray(step.props.frames)
        ? (step.props.frames as SceneFrameData[])
        : [];

  return framesThroughLineType(frames, sceneSetupStopAtLineType(lesson, step));
}

export function framesThroughLineType(
  frames: SceneFrameData[],
  stopAtLineType: unknown,
): SceneFrameData[] {
  if (typeof stopAtLineType !== 'string' || !stopAtLineType) {
    return frames;
  }

  const playableFrames = frames.filter((frame) => frame.imageUrl || frame.audioUrl || frame.audioText);
  const stopIndex = playableFrames.findIndex((frame) => frame.lineType === stopAtLineType);
  if (stopIndex < 0) {
    return playableFrames;
  }

  return playableFrames.slice(0, stopIndex + 1);
}

export function choiceQuestion(step: LessonStep): string | undefined {
  return typeof step.props.question === 'string' ? step.props.question : undefined;
}

export function choiceOptions(step: LessonStep): ChoiceOption[] {
  return Array.isArray(step.props.choices) ? (step.props.choices as ChoiceOption[]).slice(0, 4) : [];
}

export function dialogueRevealLines(
  lesson: Lesson,
  options: { hideLearnerLine?: boolean } = {},
): DialogueRevealLine[] {
  const learnerFrame = lesson.frames.find((frame) => frame.lineType === 'learner_target') ?? lesson.frames[1];

  return lesson.frames
    .filter((frame) => !(options.hideLearnerLine && frame.lineType === 'learner_target'))
    .map((frame) => {
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

export function recordingFrameForProduction(
  lesson: Lesson,
  step: LessonStep,
  fallbackFrame?: SceneFrameData,
): SceneFrameData | undefined {
  const learnerFrame = learnerFrameForLesson(lesson);

  if (step.type === 'scene_recall') {
    return learnerFrame ?? frameForStep(lesson, step);
  }

  if (stepHidesLearnerScriptBeforeAttempt(lesson, step)) {
    return openerFrameForLesson(lesson) ?? frameForStep(lesson, step);
  }

  return learnerFrame ?? fallbackFrame ?? frameForStep(lesson, step);
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

export function openerFrameForLesson(lesson: Lesson): SceneFrameData | undefined {
  return lesson.frames.find((frame) => frame.lineType === 'world_opener');
}

export function stepHidesLearnerScriptBeforeAttempt(lesson: Lesson, step: LessonStep): boolean {
  if (step.props.recordBeforeModelLine === true) {
    return true;
  }

  return lesson.stage === 'same_day_transfer' || lesson.stage === 'delayed_review';
}

export function backwardBuildTarget(step: LessonStep): string | undefined {
  return typeof step.props.targetPhrase === 'string' ? step.props.targetPhrase : undefined;
}

export function backwardBuildPrompts(step: LessonStep): BackwardBuildPrompt[] {
  return Array.isArray(step.props.prompts) ? (step.props.prompts as BackwardBuildPrompt[]) : [];
}

export function isFinalBackwardBuildPrompt(step: LessonStep, prompt: BackwardBuildPrompt): boolean {
  const prompts = backwardBuildPrompts(step).filter((entry) => entry.text);
  if (prompts.length === 0) {
    return false;
  }

  return prompts[prompts.length - 1]?.id === prompt.id;
}

export function introFramesThroughLineType(lesson: Lesson, step: LessonStep): SceneFrameData[] {
  const stopAt =
    typeof step.props.playIntroThroughLineType === 'string' ? step.props.playIntroThroughLineType : null;
  if (!stopAt) {
    return [];
  }

  const frames = lesson.frames.filter((frame) => frame.imageUrl || frame.audioUrl || frame.audioText);
  const stopIndex = frames.findIndex((frame) => frame.lineType === stopAt);
  if (stopIndex < 0) {
    return frames;
  }

  return frames.slice(0, stopIndex + 1);
}

export function stepBlocksNextUntilChoice(step: LessonStep, selectedChoiceId?: string): boolean {
  if (!stepRevealsChoicesAfterAudio(step)) {
    return false;
  }

  return !selectedChoiceId;
}

export function stepRevealsDialogueAfterChoice(step: LessonStep, selectedChoice?: ChoiceOption): boolean {
  if (!selectedChoice) {
    return false;
  }

  if (step.props.revealDialogueOnIncorrectOnly === true) {
    return !selectedChoice.isCorrect;
  }

  if (step.props.revealDialogueAfterChoice === false) {
    return false;
  }

  return true;
}

type PlaybackFlowItem = {
  type?: string;
  line_type?: string;
};

export function postAttemptFeedbackFrames(lesson: Lesson, step: LessonStep): SceneFrameData[] {
  const playbackFlow = Array.isArray(step.props.playbackFlow)
    ? (step.props.playbackFlow as PlaybackFlowItem[])
    : null;

  if (playbackFlow) {
    const recordIndex = playbackFlow.findIndex((item) => item.type === 'record_attempt');
    if (recordIndex >= 0) {
      const frames: SceneFrameData[] = [];
      for (const item of playbackFlow.slice(recordIndex + 1)) {
        if (item.type !== 'play_line' || !item.line_type) {
          continue;
        }
        const frame = lesson.frames.find((candidate) => candidate.lineType === item.line_type);
        if (frame) {
          frames.push(frame);
        }
      }
      if (frames.length > 0) {
        return frames;
      }
    }
  }

  const frames: SceneFrameData[] = [];
  if (stepPlaysModelLineAfterAttempt(step)) {
    const learnerFrame = learnerFrameForLesson(lesson);
    if (learnerFrame) {
      frames.push(learnerFrame);
    }
  }
  if (stepPlaysWorldResponseAfterAttempt(step)) {
    const responseFrame = responseFrameForLesson(lesson);
    if (responseFrame) {
      frames.push(responseFrame);
    }
  }
  return frames;
}

export function stepPlaysModelLineAfterAttempt(step: LessonStep): boolean {
  return step.props.playModelLineAfterAttempt === true;
}

export function stepPlaysWorldResponseAfterAttempt(step: LessonStep): boolean {
  return step.props.playWorldResponseAfterAttempt === true;
}

export function stepShowsDialogueRevealAfterAttempt(step: LessonStep): boolean {
  return step.props.showDialogueRevealAfterAttempt === true;
}

export function stepUsesPostAttemptFeedback(step: LessonStep): boolean {
  return stepPlaysModelLineAfterAttempt(step);
}

export function stepHandlesOwnNext(step: LessonStep): boolean {
  if (step.component === 'BackwardBuild') {
    return true;
  }

  return step.type === 'scene_recall' && stepUsesPostAttemptFeedback(step);
}

export function recordingUsesPromptAudio(step: LessonStep): boolean {
  return step.audio?.playBeforeMic === true && Boolean(step.audio?.url || step.audio?.audioText);
}

export function recordingStartsAutomatically(step: LessonStep): boolean {
  if (recordingUsesPromptAudio(step)) {
    return true;
  }

  return step.type === 'scene_recall' && step.mic?.enabled === true && step.props.recordBeforeModelLine === true;
}

export function stepRevealsChoicesAfterAudio(step: LessonStep): boolean {
  if (step.props.revealChoicesAfterAudio === true) {
    return true;
  }

  return step.type === 'broad_meaning_guess' && step.audio?.autoplay === true;
}

export function stepHandlesOwnAutoplay(step: LessonStep): boolean {
  if (step.type === 'scene_setup') return true;
  if (stepRevealsChoicesAfterAudio(step)) return true;
  if (step.component === 'BackwardBuild') return true;
  if (step.component === 'MicPrompt') return true;
  if (step.component === 'ProductionPrompt') return true;
  if (step.type === 'scene_recall' && step.mic?.enabled) return true;
  return false;
}
