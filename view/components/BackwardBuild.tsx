import { useEffect, useMemo, useState } from 'react';
import type { BackwardBuildPrompt, Chunk } from './types';
import { ChunkBreakdown } from './ChunkBreakdown';
import { PromptedRecording } from './PromptedRecording';

type BackwardBuildProps = {
  targetPhrase?: string;
  chunks?: Chunk[];
  prompts?: BackwardBuildPrompt[];
  fallbackMeaning?: string;
  recordingMs?: number;
};

export function BackwardBuild({
  targetPhrase = 'Target phrase',
  chunks = [],
  prompts = [],
  fallbackMeaning,
  recordingMs,
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
        <ChunkBreakdown chunks={chunks} fallbackMeaning={fallbackMeaning} />
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
      <ChunkBreakdown chunks={chunks} fallbackMeaning={fallbackMeaning} />
      <PromptedRecording
        key={currentPrompt.id}
        audioUrl={currentPrompt.audioUrl}
        prompt="Now you say it."
        recordingMs={recordingMs}
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
