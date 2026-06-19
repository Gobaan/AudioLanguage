import type { Lesson } from '../components';
import { DELAYED_REVIEW_TUTORIAL_ID, TRANSFER_SCENE_TUTORIAL_ID } from './transferTutorialStorage';

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
