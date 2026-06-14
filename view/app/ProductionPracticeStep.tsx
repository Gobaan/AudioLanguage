import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { DialogueReveal, PromptedRecording, SceneFrame } from '../components';
import type { Lesson, LessonStep, SceneFrameData } from '../components';
import { playAudioOrSpeakThen, stopAudio, stopSpeech } from './audioPlayback';
import {
  dialogueRevealLines,
  frameForStep,
  learnerFrameForLesson,
  postAttemptFeedbackFrames,
  productionPromptText,
  recordingPromptText,
  recordingUsesPromptAudio,
  responseFrameForLesson,
  stepShowsDialogueRevealAfterAttempt,
  stepUsesPostAttemptFeedback,
} from './lessonStepHelpers';
import { ResponsePlayback } from './ResponsePlayback';

type ProductionPracticeStepProps = {
  lesson: Lesson;
  step: LessonStep;
  language: string;
  frame?: SceneFrameData;
  prompt: string;
  recordingAudioUrl?: string | null;
  nextLabel?: string;
  onCaptureAttempt?: (
    step: LessonStep,
    recording: { blob: Blob; durationMs: number; mimeType: string },
    extra?: Record<string, unknown>,
  ) => void;
  onStepComplete?: () => void;
};

type PracticePhase = 'record' | 'feedback' | 'done';

export function ProductionPracticeStep({
  lesson,
  step,
  language,
  frame,
  prompt,
  recordingAudioUrl,
  nextLabel = 'Next',
  onCaptureAttempt,
  onStepComplete,
}: ProductionPracticeStepProps) {
  const [phase, setPhase] = useState<PracticePhase>('record');
  const [feedbackIndex, setFeedbackIndex] = useState(0);
  const learnerFrame = learnerFrameForLesson(lesson);
  const responseFrame = responseFrameForLesson(lesson);
  const feedbackFrames = useMemo(() => postAttemptFeedbackFrames(lesson, step), [lesson, step]);
  const usesPostAttemptFeedback = stepUsesPostAttemptFeedback(step);
  const showDialogueRevealAfterAttempt = stepShowsDialogueRevealAfterAttempt(step);
  const usesPromptAudio = recordingUsesPromptAudio(step);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const activeFeedbackFrame = feedbackFrames[feedbackIndex];
  const displayFrame =
    phase === 'feedback'
      ? activeFeedbackFrame ?? learnerFrame ?? frame
      : phase === 'done'
        ? responseFrame ?? feedbackFrames[feedbackFrames.length - 1] ?? learnerFrame ?? frame
        : learnerFrame ?? frame ?? frameForStep(lesson, step);

  const stopPlayback = useCallback(() => {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    audioRef.current = null;
    utteranceRef.current = null;
  }, []);

  const playFrameAudio = useCallback(
    async (targetFrame: SceneFrameData | undefined) => {
      if (!targetFrame?.audioUrl && !targetFrame?.audioText && !targetFrame?.text && !targetFrame?.transliteration) {
        return;
      }

      await new Promise<void>((resolve) => {
        playAudioOrSpeakThen(
          targetFrame.audioUrl,
          targetFrame.audioText || targetFrame.transliteration || targetFrame.text,
          audioRef,
          utteranceRef,
          resolve,
          language,
        );
      });
    },
    [language],
  );

  useEffect(() => {
    setPhase('record');
    setFeedbackIndex(0);
    stopPlayback();
  }, [step.id, stopPlayback]);

  useEffect(() => stopPlayback, [stopPlayback]);

  useEffect(() => {
    if (phase !== 'feedback') {
      return undefined;
    }

    const targetFrame = feedbackFrames[feedbackIndex];
    if (!targetFrame) {
      setPhase('done');
      return undefined;
    }

    let cancelled = false;

    async function runFeedbackSequence() {
      await playFrameAudio(targetFrame);
      if (cancelled) {
        return;
      }

      if (feedbackIndex + 1 < feedbackFrames.length) {
        setFeedbackIndex((value) => value + 1);
        return;
      }

      setPhase('done');
    }

    void runFeedbackSequence();

    return () => {
      cancelled = true;
      stopPlayback();
    };
  }, [feedbackFrames, feedbackIndex, phase, playFrameAudio, stopPlayback]);

  const handleCaptured = useCallback(
    (recording: { blob: Blob; durationMs: number; mimeType: string }) => {
      onCaptureAttempt?.(step, recording);

      if (usesPostAttemptFeedback && feedbackFrames.length > 0) {
        setFeedbackIndex(0);
        setPhase('feedback');
        return;
      }

      setPhase('done');
    },
    [feedbackFrames.length, onCaptureAttempt, step, usesPostAttemptFeedback],
  );

  const showLegacyResponsePlayback =
    phase === 'done' && !usesPostAttemptFeedback && Boolean(responseFrame?.audioUrl);
  const showLegacyResponseTextPlayback =
    phase === 'done' &&
    !usesPostAttemptFeedback &&
    !responseFrame?.audioUrl &&
    Boolean(responseFrame?.audioText);

  return (
    <section className="lesson-step-view" aria-label={step.type}>
      <SceneFrame frame={displayFrame} isActive showCaption={false} placeholderLabel="Lesson scene frame" />
      <section className="production-practice">
        {phase === 'record' ? <p>{prompt}</p> : null}
        {phase === 'record' ? (
          <PromptedRecording
            audioUrl={usesPromptAudio ? recordingAudioUrl : null}
            audioText={usesPromptAudio ? step.audio?.audioText : null}
            prompt={recordingPromptText(step)}
            startMode={usesPromptAudio ? 'auto' : 'manual'}
            startLabel="Record"
            autoConfirmCapture={usesPostAttemptFeedback}
            onCaptured={handleCaptured}
          />
        ) : null}
        {phase === 'feedback' ? <p aria-live="polite">Listen to the model dialogue.</p> : null}
        {showLegacyResponsePlayback ? <ResponsePlayback audioUrl={responseFrame?.audioUrl} /> : null}
        {showLegacyResponseTextPlayback ? <ResponsePlayback audioText={responseFrame?.audioText} /> : null}
        {phase === 'done' && showDialogueRevealAfterAttempt ? (
          <DialogueReveal lines={dialogueRevealLines(lesson)} />
        ) : null}
        {phase === 'done' && onStepComplete ? (
          <nav className="step-controls" aria-label="Production step controls">
            <button type="button" onClick={onStepComplete}>
              {nextLabel}
            </button>
          </nav>
        ) : null}
      </section>
    </section>
  );
}

export function productionPracticeProps(
  lesson: Lesson,
  step: LessonStep,
  language: string,
  prompt = productionPromptText(step),
): Omit<ProductionPracticeStepProps, 'onCaptureAttempt' | 'onStepComplete'> {
  return {
    lesson,
    step,
    language,
    frame: frameForStep(lesson, step),
    prompt,
    recordingAudioUrl: step.audio?.url,
  };
}
