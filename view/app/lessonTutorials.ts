import type { Lesson, SceneFrameData } from '../components';
import {
  ANCHOR_LEARNER_ROLE_TUTORIAL_ID,
  ANCHOR_WORLD_ROLE_TUTORIAL_ID,
  DELAYED_REVIEW_TUTORIAL_ID,
  TRANSFER_SCENE_TUTORIAL_ID,
} from './transferTutorialStorage';

export type LessonTutorial = {
  dismissId: string;
  badgeLabel: string;
  title: string;
  message: string;
  dismissLabel: string;
};

const TUTORIALS_BY_STAGE: Record<string, LessonTutorial> = {
  same_day_transfer: {
    dismissId: TRANSFER_SCENE_TUTORIAL_ID,
    badgeLabel: 'Tutorial',
    title: 'Transfer scene',
    message:
      'This is a transfer scene. It tests your ability to recall what you know and use it in a separate context. Be prepared to respond.',
    dismissLabel: 'Got it',
  },
  delayed_review: {
    dismissId: DELAYED_REVIEW_TUTORIAL_ID,
    badgeLabel: 'Tutorial',
    title: 'Delayed review',
    message:
      'This scene checks memory after a break. Try your best first, then use the feedback to tighten recall.',
    dismissLabel: 'Got it',
  },
};

const ANCHOR_WORLD_ROLE_TUTORIAL: LessonTutorial = {
  dismissId: ANCHOR_WORLD_ROLE_TUTORIAL_ID,
  badgeLabel: 'Quick cue',
  title: 'World role',
  message: 'This person sets the scene. Listen to them so you know what is happening.',
  dismissLabel: 'Got it',
};

const ANCHOR_LEARNER_ROLE_TUTORIAL: LessonTutorial = {
  dismissId: ANCHOR_LEARNER_ROLE_TUTORIAL_ID,
  badgeLabel: 'Quick cue',
  title: 'Your role',
  message: 'You are the girl. Watch the mic bubble: those are the lines you listen for and practice saying.',
  dismissLabel: 'Got it',
};

export function tutorialForLesson(lesson: Lesson | null | undefined): LessonTutorial | null {
  if (!lesson?.stage) {
    return null;
  }
  return tutorialForStage(lesson.stage);
}

export function tutorialForStage(stage: string | null | undefined): LessonTutorial | null {
  if (!stage) {
    return null;
  }
  return TUTORIALS_BY_STAGE[stage] ?? null;
}

export function anchorSceneTutorialForFrame(
  lesson: Lesson,
  frame: SceneFrameData,
  index: number,
): LessonTutorial | null {
  if (lesson.stage !== 'guided_scene_production') {
    return null;
  }

  if (index === 0 || frame.lineIndex === 0 || frame.lineType === 'world_opener') {
    return ANCHOR_WORLD_ROLE_TUTORIAL;
  }

  if (index === 1 || frame.lineIndex === 1 || frame.lineType === 'learner_target') {
    return ANCHOR_LEARNER_ROLE_TUTORIAL;
  }

  return null;
}
