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
};

export function BackwardBuild({
  targetPhrase = 'Target phrase',
  prompts = [],
  recordingMs,
  onCaptured,
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
      <div className="backward-build-header">
        <span>
          Build {promptIndex + 1} / {buildPrompts.length}
        </span>
        <h2>{currentPrompt.text}</h2>
      </div>
      <PromptedRecording
        key={currentPrompt.id}
        audioUrl={currentPrompt.audioUrl}
        audioText={currentPrompt.audioText ?? currentPrompt.text}
        prompt="Now you say it."
        recordingMs={recordingMs}
        onCaptured={(recording) => onCaptured?.(recording, currentPrompt)}
      />
      <button
        type="button"
        className="build-next-button"
        onClick={() => setPromptIndex((value) => Math.min(buildPrompts.length - 1, value + 1))}
        disabled={isLastPrompt}
      >
        Next build
      </button>
    </section>
  );
}
