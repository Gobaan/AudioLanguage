import type { CSSProperties } from 'react';

type RecordingCountdownBarProps = {
  durationMs: number;
  isPaused?: boolean;
};

export function RecordingCountdownBar({ durationMs, isPaused = false }: RecordingCountdownBarProps) {
  const safeDurationMs = Math.max(1, durationMs);
  const className = `recording-countdown${isPaused ? ' recording-countdown--paused' : ''}`;

  return (
    <div
      className={className}
      aria-hidden="true"
      style={{ '--recording-duration': `${safeDurationMs}ms` } as CSSProperties}
    >
      <span />
    </div>
  );
}
