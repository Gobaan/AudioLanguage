import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { AudioButton, ChoicePrompt, DialogueReveal, SceneFrame } from '../components';
import type { ChoiceOption, Lesson, LessonStep, SceneFrameData } from '../components';
import { playAudioOrSpeakThen, stopAudio, stopSpeech } from './audioPlayback';
import {
  choiceOptions,
  choiceQuestion,
  dialogueRevealLines,
  frameForStep,
  introFramesThroughLineType,
  stepRevealsChoicesAfterAudio,
  stepRevealsDialogueAfterChoice,
} from './lessonStepHelpers';

type MeaningGuessStepProps = {
  lesson: Lesson;
  step: LessonStep;
  language: string;
  isPlaying?: boolean;
  selectedChoiceId?: string;
  onPlayAudio?: () => void;
  onLogAudioPlayed?: () => void;
  onSelectChoice?: (stepId: string, choice: ChoiceOption) => void;
};

export function MeaningGuessStep({
  lesson,
  step,
  language,
  isPlaying = false,
  selectedChoiceId,
  onPlayAudio,
  onLogAudioPlayed,
  onSelectChoice,
}: MeaningGuessStepProps) {
  const revealAfterAudio = stepRevealsChoicesAfterAudio(step);
  const introFrames = useMemo(() => introFramesThroughLineType(lesson, step), [lesson, step]);
  const useIntroPlayback = introFrames.length > 0;
  const choices = choiceOptions(step);
  const selectedChoice = choices.find((choice) => choice.id === selectedChoiceId);
  const showDialogueReveal = stepRevealsDialogueAfterChoice(step, selectedChoice);
  const [choicesVisible, setChoicesVisible] = useState(!revealAfterAudio);
  const [isIntroPlaying, setIsIntroPlaying] = useState(false);
  const [activeFrame, setActiveFrame] = useState<SceneFrameData | undefined>(() =>
    frameForStep(lesson, step),
  );
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    setChoicesVisible(!revealAfterAudio);
    setIsIntroPlaying(false);
    setActiveFrame(frameForStep(lesson, step));
  }, [lesson, step, revealAfterAudio]);

  const stopPlayback = useCallback(() => {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    audioRef.current = null;
    utteranceRef.current = null;
    setIsIntroPlaying(false);
  }, []);

  const playFrameAudio = useCallback(
    (frame: SceneFrameData, onComplete: () => void) => {
      onLogAudioPlayed?.();
      playAudioOrSpeakThen(
        frame.audioUrl,
        frame.audioText || frame.transliteration || frame.text,
        audioRef,
        utteranceRef,
        onComplete,
        language,
      );
    },
    [language, onLogAudioPlayed],
  );

  const playIntroSequence = useCallback(
    (revealOnComplete: boolean) => {
      if (introFrames.length === 0) {
        if (revealOnComplete) {
          setChoicesVisible(true);
        }
        return;
      }

      setIsIntroPlaying(true);
      setChoicesVisible(false);
      setActiveFrame(introFrames[0]);

      const playFrameAt = (index: number) => {
        const frame = introFrames[index];
        if (!frame) {
          setIsIntroPlaying(false);
          if (revealOnComplete) {
            setChoicesVisible(true);
            setActiveFrame(frameForStep(lesson, step));
          }
          return;
        }

        setActiveFrame(frame);
        playFrameAudio(frame, () => playFrameAt(index + 1));
      };

      playFrameAt(0);
    },
    [introFrames, lesson, playFrameAudio, step],
  );

  const playTargetAudio = useCallback(
    (revealOnComplete: boolean) => {
      const audioUrl = step.audio?.url;
      const audioText = step.audio?.audioText;
      if (!audioUrl && !audioText) {
        if (revealOnComplete) {
          setChoicesVisible(true);
        }
        return;
      }

      setIsIntroPlaying(true);
      onLogAudioPlayed?.();
      playAudioOrSpeakThen(
        audioUrl,
        audioText,
        audioRef,
        utteranceRef,
        () => {
          setIsIntroPlaying(false);
          if (revealOnComplete) {
            setChoicesVisible(true);
          }
        },
        language,
      );
    },
    [language, onLogAudioPlayed, step.audio?.audioText, step.audio?.url],
  );

  useEffect(() => {
    if (!revealAfterAudio) return undefined;

    if (useIntroPlayback) {
      playIntroSequence(true);
    } else {
      playTargetAudio(true);
    }

    return stopPlayback;
  }, [playIntroSequence, playTargetAudio, revealAfterAudio, step.id, stopPlayback, useIntroPlayback]);

  const replayVisible =
    step.audio?.replayable &&
    (useIntroPlayback ? introFrames.some((frame) => frame.audioUrl || frame.audioText) : step.audio?.url || step.audio?.audioText);
  const playbackIsPlaying = revealAfterAudio ? isIntroPlaying : isPlaying;
  const handleReplay = revealAfterAudio
    ? () => {
        stopPlayback();
        if (useIntroPlayback) {
          playIntroSequence(false);
          return;
        }
        playTargetAudio(false);
      }
    : () => onPlayAudio?.();

  return (
    <section className="lesson-step-view" aria-label={step.type}>
      <SceneFrame
        frame={activeFrame}
        isActive
        showCaption={false}
        placeholderLabel="Lesson scene frame"
      />
      <div className={showDialogueReveal ? 'choice-with-reveal revealed' : 'choice-with-reveal'}>
        {revealAfterAudio && !choicesVisible ? (
          <p className="meaning-guess-listening" aria-live="polite">
            Listen.
          </p>
        ) : null}
        {choicesVisible ? (
          <ChoicePrompt
            question={choiceQuestion(step)}
            choices={choices}
            selectedChoiceId={selectedChoiceId}
            onSelectChoice={(choice) => onSelectChoice?.(step.id, choice)}
          />
        ) : null}
        {showDialogueReveal ? <DialogueReveal lines={dialogueRevealLines(lesson)} /> : null}
      </div>
      {replayVisible ? (
        <AudioButton
          label="Play"
          isPlaying={playbackIsPlaying}
          disabled={playbackIsPlaying}
          onPlay={handleReplay}
        />
      ) : null}
    </section>
  );
}
