import type { AudioButtonText } from './types';

type AudioButtonProps = {
  label?: string;
  isPlaying?: boolean;
  disabled?: boolean;
  text?: AudioButtonText;
  onPlay?: () => void;
};

const DEFAULT_TEXT: AudioButtonText = {
  playLabel: 'Play audio',
  playingLabel: 'Playing',
};

export function AudioButton({
  label,
  isPlaying = false,
  disabled = false,
  text = DEFAULT_TEXT,
  onPlay,
}: AudioButtonProps) {
  return (
    <button
      type="button"
      className={`audio-button ${isPlaying ? 'playing' : ''}`}
      disabled={disabled}
      onClick={onPlay}
    >
      {isPlaying ? text.playingLabel : label || text.playLabel}
    </button>
  );
}
