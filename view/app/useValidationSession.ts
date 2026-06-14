import { useCallback, useEffect, useState } from 'react';

import {
  logValidationEvent,
  startValidationSession,
  uploadValidationAttempt,
  type ValidationEvent,
} from '../api/validation';
import type { Lesson, LessonStep } from '../components';
import { learnerTargetAudioUrl, validationSessionIdForToday } from './lessonUrls';

type CaptureAttemptExtra = Record<string, unknown>;

function attemptExpectedPhrase(
  lesson: Lesson,
  attemptStep: LessonStep,
  extra: CaptureAttemptExtra,
): { expectedText: string; expectedTransliteration: string } {
  const buildPromptText = typeof extra.buildPromptText === 'string' ? extra.buildPromptText.trim() : '';
  if (buildPromptText) {
    return { expectedText: buildPromptText, expectedTransliteration: buildPromptText };
  }

  return {
    expectedText: attemptStep.mic?.expectedText ?? lesson.target.text,
    expectedTransliteration: attemptStep.mic?.expectedTransliteration ?? lesson.target.transliteration,
  };
}

type UseValidationSessionOptions = {
  participantId: string | null;
  language: string;
  sceneSet: string;
  lessonPage: string;
};

export function useValidationSession({
  participantId,
  language,
  sceneSet,
  lessonPage,
}: UseValidationSessionOptions) {
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    if (!participantId) return;

    let isCurrent = true;

    startValidationSession({
      sessionId: validationSessionIdForToday(participantId, language, sceneSet),
      language,
      sceneSet,
      lessonPage,
      participantId,
    })
      .then((session) => {
        if (isCurrent) {
          setSessionId(session.sessionId);
        }
      })
      .catch(() => {
        if (isCurrent) {
          setSessionId(null);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [language, sceneSet, participantId]);

  const logEvent = useCallback(
    (event: ValidationEvent) => {
      if (!sessionId) return;

      void logValidationEvent(sessionId, {
        participantId: participantId ?? undefined,
        language,
        sceneSet,
        ...event,
      }).catch(() => undefined);
    },
    [sessionId, participantId, language, sceneSet],
  );

  const captureAttempt = useCallback(
    (
      lesson: Lesson,
      attemptStep: LessonStep,
      recording: { blob: Blob; durationMs: number; mimeType: string },
      extra: CaptureAttemptExtra = {},
    ) => {
      if (!sessionId) return;

      const attemptId = crypto.randomUUID();
      const expectedPhrase = attemptExpectedPhrase(lesson, attemptStep, extra);
      const buildPromptAudioUrl =
        typeof extra.buildPromptAudioUrl === 'string' ? extra.buildPromptAudioUrl : undefined;
      void uploadValidationAttempt(sessionId, recording.blob, {
        attemptId,
        participantId,
        language,
        sceneSet,
        lessonId: lesson.id,
        lessonPage,
        stepId: attemptStep.id,
        targetId: lesson.target.id,
        expectedText: expectedPhrase.expectedText,
        expectedTransliteration: expectedPhrase.expectedTransliteration,
        targetAudioUrl: buildPromptAudioUrl ?? learnerTargetAudioUrl(lesson),
        recordingDurationMs: recording.durationMs,
        byteCount: recording.blob.size,
        mimeType: recording.mimeType,
        buildPromptId: typeof extra.buildPromptId === 'string' ? extra.buildPromptId : undefined,
        buildPromptText: typeof extra.buildPromptText === 'string' ? extra.buildPromptText : undefined,
      }).catch(() => undefined);
    },
    [sessionId, participantId, language, sceneSet, lessonPage],
  );

  return {
    sessionId,
    logEvent,
    captureAttempt,
  };
}
