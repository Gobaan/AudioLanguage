import { AudioButton } from '../components';
import type { LessonStep } from '../components';

export function StepAudioButton({
  step,
  isPlaying,
  onPlayAudio,
}: {
  step: LessonStep;
  isPlaying: boolean;
  onPlayAudio?: () => void;
}) {
  if (!step.audio?.url) {
    if (step.audio?.audioText) {
      return <AudioButton label="Play" isPlaying={isPlaying} disabled={isPlaying} onPlay={onPlayAudio} />;
    }
    return null;
  }

  return <AudioButton label="Play" isPlaying={isPlaying} disabled={isPlaying} onPlay={onPlayAudio} />;
}
