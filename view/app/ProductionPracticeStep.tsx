import { useEffect, useState } from 'react';

import { PromptedRecording, SceneFrame } from '../components';
import type { Lesson, LessonStep, SceneFrameData } from '../components';
import { frameForStep, learnerFrameForLesson, productionPromptText, recordingPromptText, responseFrameForLesson } from './lessonStepHelpers';
import { ResponsePlayback } from './ResponsePlayback';

type ProductionPracticeStepProps = {
  lesson: Lesson;
  step: LessonStep;
  frame?: SceneFrameData;
  prompt: string;
  recordingAudioUrl?: string | null;
  onCaptureAttempt?: (
    step: LessonStep,
    recording: { blob: Blob; durationMs: number; mimeType: string },
    extra?: Record<string, unknown>,
  ) => void;
};

export function ProductionPracticeStep({
  lesson,
  step,
  frame,
  prompt,
  recordingAudioUrl,
  onCaptureAttempt,
}: ProductionPracticeStepProps) {
  const [phase, setPhase] = useState<'cue' | 'recording' | 'response'>('cue');
  const learnerFrame = learnerFrameForLesson(lesson);
  const responseFrame = responseFrameForLesson(lesson);
  const displayFrame = phase === 'response' ? responseFrame ?? frame : phase === 'recording' ? learnerFrame ?? frame : frame;

  useEffect(() => {
    setPhase('cue');
  }, [step.id]);

  return (
    <section className="lesson-step-view" aria-label={step.type}>
      <SceneFrame frame={displayFrame} isActive showCaption={false} placeholderLabel="Lesson scene frame" />
      <section className="production-practice">
        <p>{prompt}</p>
        {phase !== 'response' ? (
          <PromptedRecording
            audioUrl={recordingAudioUrl}
            audioText={step.audio?.audioText}
            prompt={recordingPromptText(step)}
            startMode={step.type === 'scene_recall' ? 'auto' : 'manual'}
            startLabel="Record"
            onRecording={() => setPhase('recording')}
            onCaptured={(recording) => {
              setPhase('response');
              onCaptureAttempt?.(step, recording);
            }}
          />
        ) : null}
        {phase === 'response' && responseFrame?.audioUrl ? <ResponsePlayback audioUrl={responseFrame.audioUrl} /> : null}
        {phase === 'response' && !responseFrame?.audioUrl && responseFrame?.audioText ? (
          <ResponsePlayback audioText={responseFrame.audioText} />
        ) : null}
      </section>
    </section>
  );
}

export function productionPracticeProps(
  lesson: Lesson,
  step: LessonStep,
  prompt = productionPromptText(step),
): Omit<ProductionPracticeStepProps, 'onCaptureAttempt'> {
  return {
    lesson,
    step,
    frame: frameForStep(lesson, step),
    prompt,
    recordingAudioUrl: step.audio?.url,
  };
}
