import { MicPrompt } from './MicPrompt';
import type { MicPromptText } from './types';

type ProductionPromptProps = {
  cue?: string;
  targetMeaning?: string;
  micText?: MicPromptText;
  onStartRecording?: () => void;
};

export function ProductionPrompt({
  cue = 'Respond to the scene',
  targetMeaning = 'Target meaning placeholder',
  micText,
  onStartRecording,
}: ProductionPromptProps) {
  return (
    <section className="production-prompt">
      <p>{cue}</p>
      <small>{targetMeaning}</small>
      <MicPrompt text={micText} onStartRecording={onStartRecording} />
    </section>
  );
}
