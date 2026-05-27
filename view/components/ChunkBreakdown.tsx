import type { Chunk } from './types';

type ChunkBreakdownProps = {
  chunks?: Chunk[];
  fallbackMeaning?: string;
};

export function ChunkBreakdown({
  chunks = [],
  fallbackMeaning = 'Meaning placeholder',
}: ChunkBreakdownProps) {
  return (
    <dl className="chunk-breakdown">
      {chunks.map((chunk) => (
        <div key={chunk.id}>
          <dt>{chunk.text}</dt>
          <dd>{chunk.meaning || fallbackMeaning}</dd>
        </div>
      ))}
    </dl>
  );
}
