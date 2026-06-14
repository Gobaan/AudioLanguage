import { useEffect, useMemo, useState } from 'react';
import type { BackwardBuildPrompt, Chunk } from './types';
import { PromptedRecording } from './PromptedRecording';

type BackwardBuildProps = {
  targetPhrase?: string;
  prompts?: BackwardBuildPrompt[];
  chunks?: Chunk[];
  recordingMs?: number;
  onCaptured?: (
    recording: { blob: Blob; durationMs: number; mimeType: string },
    prompt: BackwardBuildPrompt,
  ) => void;
  onStepComplete?: () => void;
};

function chunkLabel(chunk: Chunk): string {
  return chunk.text.replace(/\b\w/g, (character) => character.toUpperCase());
}

export function BackwardBuild({
  targetPhrase = 'Target phrase',
  prompts = [],
  chunks = [],
  recordingMs,
  onCaptured,
  onStepComplete,
}: BackwardBuildProps) {
  const buildPrompts = useMemo(() => prompts.filter((prompt) => prompt.text), [prompts]);
  const [promptIndex, setPromptIndex] = useState(0);
  const [phraseRevealed, setPhraseRevealed] = useState(false);
  const currentPrompt = buildPrompts[promptIndex];
  const isLastPrompt = promptIndex >= buildPrompts.length - 1;
  const showChunkGuide = chunks.length > 1;

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

  const focusHeading =
    currentPrompt.focusUnit === 'full'
      ? 'Put it together'
      : currentPrompt.focusLabel
        ? `This step: ${currentPrompt.focusLabel}`
        : null;

  return (
    <section className="backward-build">
      {showChunkGuide ? (
        <dl className="chunk-breakdown backward-build-chunks" aria-label="Phrase parts">
          {chunks.map((chunk) => {
            const isActive =
              currentPrompt.focusUnit === chunk.meaning ||
              (currentPrompt.focusUnit === 'full' && Boolean(chunk.meaning));
            return (
              <div key={chunk.id} className={isActive ? 'is-active' : undefined}>
                <dt>{chunkLabel(chunk)}</dt>
                <dd>{chunk.meaning === 'one' ? 'How many' : 'Polite marker'}</dd>
              </div>
            );
          })}
        </dl>
      ) : null}
      <div className="backward-build-header">
        <span>{stepLabel}</span>
        {focusHeading ? <p className="backward-build-focus">{focusHeading}</p> : null}
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
