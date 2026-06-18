import { useCallback, useEffect, useMemo, useState } from 'react';

import type { ValidationEvent } from '../api/validation';
import type { CapturedRecording, ChoiceOption, Lesson, LessonStep } from '../components';
import { stepHandlesOwnAutoplay } from './lessonStepHelpers';
import { withAssetUrls, withStepAssetUrls } from './lessonUrls';
import { useAudioPlayback } from './useAudioPlayback';

type CaptureAttempt = (
  lesson: Lesson,
  step: LessonStep,
  recording: CapturedRecording,
  extra?: Record<string, unknown>,
) => void;

type UseActiveLessonStepOptions = {
  lesson: Lesson | null;
  language: string;
  lessonPage: string;
  sceneSet: string;
  validationSessionId: string | null;
  logEvent: (event: ValidationEvent) => void;
  captureAttempt: CaptureAttempt;
};

export function useActiveLessonStep({
  lesson,
  language,
  lessonPage,
  sceneSet,
  validationSessionId,
  logEvent,
  captureAttempt,
}: UseActiveLessonStepOptions) {
  const [stepIndex, setStepIndex] = useState(0);
  const [selectedChoiceByStep, setSelectedChoiceByStep] = useState<Record<string, string>>({});
  const { isPlaying, audioError, playAudioOrSpeak, stop: stopPlayback } = useAudioPlayback();

  const currentStep = lesson?.steps[stepIndex];
  const stepLesson = useMemo(() => withAssetUrls(lesson), [lesson]);
  const step = useMemo(() => withStepAssetUrls(currentStep), [currentStep]);

  const resetStepState = useCallback(() => {
    setStepIndex(0);
    setSelectedChoiceByStep({});
  }, []);

  useEffect(() => {
    resetStepState();
  }, [language, lessonPage, sceneSet, resetStepState]);

  useEffect(() => {
    stopPlayback();
  }, [stepIndex, stopPlayback]);

  const logStepAudioPlayed = useCallback(() => {
    if (stepLesson && step) {
      logEvent({
        type: 'audio_played',
        lessonId: stepLesson.id,
        lessonPage,
        stepId: step.id,
        stepIndex,
        frameId: step.frameId,
        targetId: stepLesson.target.id,
        planPurpose: stepLesson.planPurpose,
        repairCategory: stepLesson.repairCategory,
        lessonStage: stepLesson.stage,
      });
    }
  }, [step, stepLesson, lessonPage, stepIndex, logEvent]);

  const playStepAudio = useCallback(() => {
    const audioUrl = step?.audio?.url;
    const audioText = step?.audio?.audioText;
    if (!audioUrl && !audioText) return;

    logStepAudioPlayed();
    playAudioOrSpeak(audioUrl, audioText, language);
  }, [step, language, logStepAudioPlayed, playAudioOrSpeak]);

  useEffect(() => {
    if (!step?.audio?.autoplay || stepHandlesOwnAutoplay(step)) return;
    playStepAudio();
  }, [step?.id, step?.audio?.autoplay, playStepAudio]);

  useEffect(() => {
    if (!validationSessionId || !stepLesson || !step) return;

    logEvent({
      type: 'page_view',
      lessonId: stepLesson.id,
      lessonPage,
      stepId: step.id,
      stepIndex,
      frameId: step.frameId,
      targetId: stepLesson.target.id,
      planPurpose: stepLesson.planPurpose,
      repairCategory: stepLesson.repairCategory,
      lessonStage: stepLesson.stage,
    });
  }, [validationSessionId, stepLesson?.id, step?.id, stepIndex, lessonPage, logEvent]);

  const selectChoice = useCallback(
    (stepId: string, choice: ChoiceOption) => {
      setSelectedChoiceByStep((current) => ({
        ...current,
        [stepId]: choice.id,
      }));
      if (stepLesson) {
        logEvent({
          type: 'choice_selected',
          lessonId: stepLesson.id,
          lessonPage,
          stepId,
          stepIndex,
          choiceId: choice.id,
          isCorrect: choice.isCorrect,
          targetId: stepLesson.target.id,
          planPurpose: stepLesson.planPurpose,
          repairCategory: stepLesson.repairCategory,
          lessonStage: stepLesson.stage,
        });
      }
    },
    [stepLesson, lessonPage, stepIndex, logEvent],
  );

  const goToStep = useCallback(
    (direction: 'previous' | 'next') => {
      setStepIndex((value) => {
        const nextValue =
          direction === 'previous'
            ? Math.max(0, value - 1)
            : Math.min((stepLesson?.steps.length ?? 1) - 1, value + 1);
        if (nextValue !== value && stepLesson && step) {
          logEvent({
            type: 'navigation',
            direction,
            lessonId: stepLesson.id,
            lessonPage,
            stepId: step.id,
            stepIndex: value,
            frameId: step.frameId,
            targetId: stepLesson.target.id,
            planPurpose: stepLesson.planPurpose,
            repairCategory: stepLesson.repairCategory,
            lessonStage: stepLesson.stage,
          });
        }
        return nextValue;
      });
    },
    [stepLesson, step, lessonPage, logEvent],
  );

  const handleCaptureAttempt = useCallback(
    (
      attemptStep: LessonStep,
      recording: CapturedRecording,
      extra: Record<string, unknown> = {},
    ) => {
      if (!stepLesson) return;
      captureAttempt(stepLesson, attemptStep, recording, extra);
    },
    [stepLesson, captureAttempt],
  );

  const isFirstStep = stepIndex === 0;
  const isLastStep = stepLesson ? stepIndex >= stepLesson.steps.length - 1 : true;

  return {
    stepLesson,
    step,
    stepIndex,
    isPlaying,
    audioError,
    selectedChoiceByStep,
    isFirstStep,
    isLastStep,
    playStepAudio,
    logStepAudioPlayed,
    selectChoice,
    goToStep,
    handleCaptureAttempt,
  };
}
