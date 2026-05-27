import type { Chunk } from './types';
import { ChunkBreakdown } from './ChunkBreakdown';

type BackwardBuildProps = {
  targetPhrase?: string;
  chunks?: Chunk[];
  fallbackMeaning?: string;
};

export function BackwardBuild({
  targetPhrase = 'Target phrase',
  chunks = [],
  fallbackMeaning,
}: BackwardBuildProps) {
  return (
    <section className="backward-build">
      <h2>{targetPhrase}</h2>
      <ChunkBreakdown chunks={chunks} fallbackMeaning={fallbackMeaning} />
    </section>
  );
}
