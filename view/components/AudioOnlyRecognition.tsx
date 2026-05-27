import { AudioButton } from './AudioButton';
import { MicPrompt } from './MicPrompt';
import type { AudioButtonText, MicPromptText } from './types';

type AudioOnlyRecognitionProps = {
  prompt?: string;
  audioText?: AudioButtonText;
  micText?: MicPromptText;
};

export function AudioOnlyRecognition({
  prompt = 'Listen, then repeat',
  audioText,
  micText,
}: AudioOnlyRecognitionProps) {
  return (
    <section className="audio-only-recognition">
      <h2>{prompt}</h2>
      <AudioButton text={audioText} />
      <MicPrompt text={micText} />
    </section>
  );
}
