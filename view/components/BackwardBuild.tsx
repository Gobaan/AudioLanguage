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
  const currentPrompt = buildPrompts[promptIndex];
  const isLastPrompt = promptIndex >= buildPrompts.length - 1;

  useEffect(() => {
    setPromptIndex(0);
  }, [targetPhrase, buildPrompts.length]);

  if (!currentPrompt) {
    return (
      <section className="backward-build">
        <h2>{targetPhrase}</h2>
      </section>
    );
  }

  return (
    <section className="backward-build">
      <PromptedRecording
        key={currentPrompt.id}
        audioUrl={currentPrompt.audioUrl}
        audioText={currentPrompt.audioText ?? currentPrompt.text}
        prompt="Now you say it."
        playbackPrompt="Listen."
        recordingMs={recordingMs}
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
