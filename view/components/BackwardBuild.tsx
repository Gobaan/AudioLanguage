import { useEffect, useMemo, useState } from 'react';
import type { BackwardBuildPrompt } from './types';
import { PromptedRecording } from './PromptedRecording';

type BackwardBuildProps = {
  targetPhrase?: string;
  prompts?: BackwardBuildPrompt[];
  recordingMs?: number;
  onCaptured?: (
    recording: { blob: Blob; durationMs: number; mimeType: string },
    prompt: BackwardBuildPrompt,
  ) => void;
  onStepComplete?: () => void;
};

export function BackwardBuild({
  targetPhrase = 'Target phrase',
  prompts = [],
  recordingMs,
  onCaptured,
  onStepComplete,
}: BackwardBuildProps) {
  const buildPrompts = useMemo(() => prompts.filter((prompt) => prompt.text), [prompts]);
  const [promptIndex, setPromptIndex] = useState(0);
  const [phraseRevealed, setPhraseRevealed] = useState(false);
  const currentPrompt = buildPrompts[promptIndex];
  const isLastPrompt = promptIndex >= buildPrompts.length - 1;

  useEffect(() => {
    setPromptIndex(0);
  }, [targetPhrase, buildPrompts.length]);

  useEffect(() => {
    setPhraseRevealed(false);
  }, [currentPrompt?.id]);

  if (!currentPrompt) {
    return (
      <section className="backward-build">
        <h2>{targetPhrase}</h2>
      </section>
    );
  }

  const stepLabel =
    buildPrompts.length === 1
      ? 'Say the phrase'
      : isLastPrompt
        ? `Final build ${promptIndex + 1} / ${buildPrompts.length}`
        : `Build ${promptIndex + 1} / ${buildPrompts.length}`;

  return (
    <section className="backward-build">
      <div className="backward-build-header">
        <span>{stepLabel}</span>
        <h2 aria-live="polite">{phraseRevealed ? currentPrompt.text : 'Listen first.'}</h2>
      </div>
      <PromptedRecording
        key={currentPrompt.id}
        audioUrl={currentPrompt.audioUrl}
        audioText={currentPrompt.audioText ?? currentPrompt.text}
        prompt="Now you say it."
        playbackPrompt="Listen."
        recordingMs={recordingMs}
        onListenComplete={() => setPhraseRevealed(true)}
        onCaptured={(recording) => onCaptured?.(recording, currentPrompt)}
        onNext={() => {
          if (isLastPrompt) {
            onStepComplete?.();
            return;
          }
          setPromptIndex((value) => Math.min(buildPrompts.length - 1, value + 1));
        }}
      />
    </section>
  );
}
