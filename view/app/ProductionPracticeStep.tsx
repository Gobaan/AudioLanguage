import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { DialogueReveal, PromptedRecording, SceneFrame } from '../components';
import type { CapturedRecording, Lesson, LessonStep, SceneFrameData } from '../components';
import { playAudioOrSpeakThen, stopAudio, stopSpeech } from './audioPlayback';
import {
  dialogueRevealLines,
  frameForStep,
  learnerFrameForLesson,
  postAttemptFeedbackFrames,
  productionPromptText,
  recordingFrameForProduction,
  recordingPromptText,
  recordingStartsAutomatically,
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
    recording: CapturedRecording,
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
  const [audioError, setAudioError] = useState<string | null>(null);
  const learnerFrame = learnerFrameForLesson(lesson);
  const responseFrame = responseFrameForLesson(lesson);
  const feedbackFrames = useMemo(() => postAttemptFeedbackFrames(lesson, step), [lesson, step]);
  const usesPostAttemptFeedback = stepUsesPostAttemptFeedback(step);
  const showDialogueRevealAfterAttempt = stepShowsDialogueRevealAfterAttempt(step);
  const startsRecordingAutomatically = recordingStartsAutomatically(step);
  const recordingMs =
    typeof step.mic?.maxDurationMs === 'number' && step.mic.maxDurationMs > 0
      ? step.mic.maxDurationMs
      : 5000;
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const activeFeedbackFrame = feedbackFrames[feedbackIndex];
  const recordFrame = recordingFrameForProduction(lesson, step, frame);
  const displayFrame =
    phase === 'record'
      ? recordFrame
      : phase === 'feedback'
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

      await new Promise<void>((resolve, reject) => {
        playAudioOrSpeakThen(
          targetFrame.audioUrl,
          targetFrame.audioText || targetFrame.transliteration || targetFrame.text,
          audioRef,
          utteranceRef,
          resolve,
          language,
          (message) => {
            setAudioError(message);
            reject(new Error(message));
          },
        );
      });
    },
    [language],
  );

  const waitForFrameReady = useCallback(async (targetFrame: SceneFrameData | undefined) => {
    const imageUrl = targetFrame?.imageUrl;
    if (!imageUrl) {
      return;
    }

    await new Promise<void>((resolve) => {
      const image = new Image();
      let settled = false;
      const finish = () => {
        if (settled) {
          return;
        }
        settled = true;
        resolve();
      };

      image.onload = finish;
      image.onerror = finish;
      image.src = imageUrl;

      if (image.complete) {
        finish();
        return;
      }

      // Never block audio forever on a bad/slow image request.
      window.setTimeout(finish, 2000);
    });

    // Give React a paint tick so the new frame is visible before audio starts.
    await new Promise<void>((resolve) => window.setTimeout(resolve, 80));
  }, []);

  useEffect(() => {
    setPhase('record');
    setFeedbackIndex(0);
    setAudioError(null);
    stopPlayback();
  }, [lesson.id, step.id, stopPlayback]);

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
      try {
        await waitForFrameReady(targetFrame);
        if (cancelled) {
          return;
        }
        await playFrameAudio(targetFrame);
      } catch {
        return;
      }
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
  }, [feedbackFrames, feedbackIndex, phase, playFrameAudio, stopPlayback, waitForFrameReady]);

  const handleCaptured = useCallback(
    (recording: CapturedRecording) => {
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

  const handleContinueDuringFeedback = useCallback(() => {
    stopPlayback();
    if (onStepComplete) {
      onStepComplete();
      return;
    }
    setPhase('done');
  }, [onStepComplete, stopPlayback]);

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
        {audioError ? (
          <p className="audio-error" role="alert">
            {audioError}
          </p>
        ) : null}
        {phase === 'record' ? <p>{prompt}</p> : null}
        {phase === 'record' ? (
          <PromptedRecording
            audioUrl={recordingAudioUrl ?? step.audio?.url}
            audioText={step.audio?.audioText}
            prompt={recordingPromptText(step)}
            modelReplayNormalLabel="🔊 Normal speed"
            modelReplaySlowLabel="🐌 Half speed"
            recordingMs={recordingMs}
            startMode={startsRecordingAutomatically ? 'auto' : 'manual'}
            startLabel="Record"
            onCaptured={handleCaptured}
          />
        ) : null}
        {phase === 'feedback' ? <p aria-live="polite">Listen to the model dialogue.</p> : null}
        {phase === 'feedback' ? (
          <nav className="step-controls" aria-label="Production feedback controls">
            <button type="button" onClick={handleContinueDuringFeedback}>
              {nextLabel}
            </button>
          </nav>
        ) : null}
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
