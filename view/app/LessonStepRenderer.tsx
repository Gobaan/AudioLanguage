import { useEffect, useRef, useState } from 'react';
import { AudioButton, BackwardBuild, ChoicePrompt, DialogueReveal, PromptedRecording, SceneFrame } from '../components';
import type {
  BackwardBuildPrompt,
  ChoiceOption,
  Chunk,
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
};

export function LessonStepRenderer({
  lesson,
  step,
  isPlaying = false,
  selectedChoiceId,
  onPlayAudio,
  onSelectChoice,
}: LessonStepRendererProps) {
  if (step.component === 'ProductionPrompt') {
    return (
      <ProductionPracticeStep
        lesson={lesson}
        step={step}
        frame={frameForStep(lesson, step)}
        prompt={productionPromptText(step)}
        recordingAudioUrl={step.audio?.url}
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
      />
    );
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
        <PromptedRecording audioUrl={step.audio?.url} prompt="Now you say it." />
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
          chunks={backwardBuildChunks(step)}
          prompts={backwardBuildPrompts(step)}
          fallbackMeaning={lesson.target.meaning}
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
}: {
  lesson: Lesson;
  step: LessonStep;
  frame?: SceneFrameData;
  prompt: string;
  recordingAudioUrl?: string | null;
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
            prompt={recordingPromptText(step)}
            startMode={step.type === 'scene_recall' ? 'auto' : 'manual'}
            startLabel="Record"
            onRecording={() => setPhase('recording')}
            onCaptured={() => setPhase('response')}
          />
        ) : null}
        {phase === 'response' && responseFrame?.audioUrl ? <ResponsePlayback audioUrl={responseFrame.audioUrl} /> : null}
      </section>
    </section>
  );
}

function ResponsePlayback({ audioUrl }: { audioUrl: string }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    playResponse();
    return () => {
      stopAudio(audioRef.current);
    };
  }, [audioUrl]);

  function playResponse() {
    stopAudio(audioRef.current);
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
    return null;
  }

  return <AudioButton label="Play" isPlaying={isPlaying} disabled={isPlaying} onPlay={onPlayAudio} />;
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

function backwardBuildTarget(step: LessonStep): string | undefined {
  return typeof step.props.targetPhrase === 'string' ? step.props.targetPhrase : undefined;
}

function backwardBuildChunks(step: LessonStep): Chunk[] {
  return Array.isArray(step.props.chunks) ? (step.props.chunks as Chunk[]) : [];
}

function backwardBuildPrompts(step: LessonStep): BackwardBuildPrompt[] {
  return Array.isArray(step.props.prompts) ? (step.props.prompts as BackwardBuildPrompt[]) : [];
}
