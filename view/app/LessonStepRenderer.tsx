import { useEffect, useRef, useState } from 'react';
import {
  AudioButton,
  BackwardBuild,
  ChoicePrompt,
  DialogueReveal,
  PromptedRecording,
  SceneFrame,
  ScenePlayback,
} from '../components';
import type {
  BackwardBuildPrompt,
  ChoiceOption,
  DialogueRevealLine,
  Lesson,
  LessonStep,
  SceneFrameData,
} from '../components';

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

export function LessonStepRenderer({
  lesson,
  step,
  isPlaying = false,
  selectedChoiceId,
  onPlayAudio,
  onSelectChoice,
  onCaptureAttempt,
}: LessonStepRendererProps) {
  if (step.component === 'ProductionPrompt') {
    return (
      <ProductionPracticeStep
        lesson={lesson}
        step={step}
        frame={frameForStep(lesson, step)}
        prompt={productionPromptText(step)}
        recordingAudioUrl={step.audio?.url}
        onCaptureAttempt={onCaptureAttempt}
      />
    );
  }

  if (step.type === 'scene_recall' && step.mic?.enabled) {
    return (
      <ProductionPracticeStep
        lesson={lesson}
        step={step}
        frame={frameForStep(lesson, step)}
        prompt="What do you say?"
        recordingAudioUrl={step.audio?.url}
        onCaptureAttempt={onCaptureAttempt}
      />
    );
  }

  if (step.type === 'scene_setup') {
    return <ScenePlayback frames={sceneSetupFrames(lesson, step)} autoplay={step.audio?.autoplay} />;
  }

  if (step.component === 'SceneFrame') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <StepAudioButton step={step} isPlaying={isPlaying} onPlayAudio={onPlayAudio} />
      </section>
    );
  }

  if (step.component === 'AudioButton') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <StepAudioButton step={step} isPlaying={isPlaying} onPlayAudio={onPlayAudio} />
      </section>
    );
  }

  if (step.component === 'ChoicePrompt') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <div className={selectedChoiceId ? 'choice-with-reveal revealed' : 'choice-with-reveal'}>
          <ChoicePrompt
            question={choiceQuestion(step)}
            choices={choiceOptions(step)}
            selectedChoiceId={selectedChoiceId}
            onSelectChoice={(choice) => onSelectChoice?.(step.id, choice)}
          />
          {selectedChoiceId ? <DialogueReveal lines={dialogueRevealLines(lesson)} /> : null}
        </div>
        <StepAudioButton step={step} isPlaying={isPlaying} onPlayAudio={onPlayAudio} />
      </section>
    );
  }

  if (step.component === 'TranslationReveal') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <DialogueReveal lines={dialogueRevealLines(lesson)} />
        <StepAudioButton step={step} isPlaying={isPlaying} onPlayAudio={onPlayAudio} />
      </section>
    );
  }

  if (step.component === 'MicPrompt') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <PromptedRecording
          audioUrl={step.audio?.url}
          audioText={step.audio?.audioText}
          prompt="Now you say it."
          onCaptured={(recording) => onCaptureAttempt?.(step, recording)}
        />
      </section>
    );
  }

  if (step.component === 'BackwardBuild') {
    return (
      <section className="lesson-step-view" aria-label={step.type}>
        <SceneFrame
          frame={frameForStep(lesson, step)}
          isActive
          showCaption={false}
          placeholderLabel="Lesson scene frame"
        />
        <BackwardBuild
          targetPhrase={backwardBuildTarget(step)}
          prompts={backwardBuildPrompts(step)}
          onCaptured={(recording, prompt) =>
            onCaptureAttempt?.(step, recording, {
              buildPromptId: prompt.id,
              buildPromptText: prompt.text,
            })
          }
        />
      </section>
    );
  }

  return <div className="frame-placeholder" aria-label="Lesson step unavailable" />;
}

function ProductionPracticeStep({
  lesson,
  step,
  frame,
  prompt,
  recordingAudioUrl,
  onCaptureAttempt,
}: {
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
}) {
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

function ResponsePlayback({ audioUrl, audioText }: { audioUrl?: string; audioText?: string }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    playResponse();
    return () => {
      stopAudio(audioRef.current);
      stopSpeech(utteranceRef.current);
    };
  }, [audioUrl, audioText]);

  function playResponse() {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    if (!audioUrl) {
      speakResponse();
      return;
    }

    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    setIsPlaying(true);

    audio.addEventListener(
      'ended',
      () => {
        setIsPlaying(false);
        audioRef.current = null;
      },
      { once: true },
    );

    audio.addEventListener(
      'error',
      () => {
        setIsPlaying(false);
        audioRef.current = null;
      },
      { once: true },
    );

    audio.play().catch(() => {
      setIsPlaying(false);
      audioRef.current = null;
    });
  }

  function speakResponse() {
    const spokenText = audioText?.trim();
    if (!spokenText || !window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') {
      setIsPlaying(false);
      utteranceRef.current = null;
      return;
    }

    const utterance = new SpeechSynthesisUtterance(spokenText);
    utteranceRef.current = utterance;
    setIsPlaying(true);
    utterance.addEventListener(
      'end',
      () => {
        setIsPlaying(false);
        utteranceRef.current = null;
      },
      { once: true },
    );
    utterance.addEventListener(
      'error',
      () => {
        setIsPlaying(false);
        utteranceRef.current = null;
      },
      { once: true },
    );
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  return (
    <div className="response-playback">
      <AudioButton label="Play response" isPlaying={isPlaying} disabled={isPlaying} onPlay={playResponse} />
    </div>
  );
}

export function frameForStep(lesson: Lesson, step: LessonStep): SceneFrameData | undefined {
  return lesson.frames.find((frame) => frame.id === step.frameId) ?? lesson.frames[0];
}

function StepAudioButton({
  step,
  isPlaying,
  onPlayAudio,
}: {
  step: LessonStep;
  isPlaying: boolean;
  onPlayAudio?: () => void;
}) {
  if (!step.audio?.url) {
    if (step.audio?.audioText) {
      return <AudioButton label="Play" isPlaying={isPlaying} disabled={isPlaying} onPlay={onPlayAudio} />;
    }
    return null;
  }

  return <AudioButton label="Play" isPlaying={isPlaying} disabled={isPlaying} onPlay={onPlayAudio} />;
}

function sceneSetupFrames(lesson: Lesson, step: LessonStep): SceneFrameData[] {
  if (lesson.frames.length > 0) {
    return lesson.frames;
  }

  return Array.isArray(step.props.frames) ? (step.props.frames as SceneFrameData[]) : [];
}

function choiceQuestion(step: LessonStep): string | undefined {
  return typeof step.props.question === 'string' ? step.props.question : undefined;
}

function choiceOptions(step: LessonStep): ChoiceOption[] {
  return Array.isArray(step.props.choices) ? (step.props.choices as ChoiceOption[]).slice(0, 4) : [];
}

function dialogueRevealLines(lesson: Lesson): DialogueRevealLine[] {
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

function productionPromptText(step: LessonStep): string {
  if (typeof step.displayText === 'string' && step.displayText) {
    return step.displayText;
  }

  if (typeof step.props.targetMeaning === 'string' && step.props.targetMeaning) {
    return `How do you say: ${step.props.targetMeaning}`;
  }

  return 'What do you say?';
}

function recordingPromptText(step: LessonStep): string {
  return step.type === 'scene_recall' ? 'Now you respond.' : 'Now you say it.';
}

function responseFrameForLesson(lesson: Lesson): SceneFrameData | undefined {
  return lesson.frames.find((frame) => frame.lineType === 'world_response');
}

function learnerFrameForLesson(lesson: Lesson): SceneFrameData | undefined {
  return lesson.frames.find((frame) => frame.lineType === 'learner_target');
}

function stopAudio(audio: HTMLAudioElement | null) {
  if (!audio) return;

  audio.pause();
  audio.currentTime = 0;
}

function stopSpeech(utterance: SpeechSynthesisUtterance | null) {
  if (!utterance) return;

  window.speechSynthesis?.cancel();
}

function backwardBuildTarget(step: LessonStep): string | undefined {
  return typeof step.props.targetPhrase === 'string' ? step.props.targetPhrase : undefined;
}

function backwardBuildPrompts(step: LessonStep): BackwardBuildPrompt[] {
  return Array.isArray(step.props.prompts) ? (step.props.prompts as BackwardBuildPrompt[]) : [];
}
