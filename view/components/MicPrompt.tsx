import type { MicPromptText } from './types';

type MicPromptProps = {
  prompt?: string;
  isListening?: boolean;
  disabled?: boolean;
  text?: MicPromptText;
  onStartRecording?: () => void;
};

const DEFAULT_TEXT: MicPromptText = {
  prompt: 'Try saying it',
  listeningLabel: 'Listening...',
  startLabel: 'Start',
};

export function MicPrompt({
  prompt,
  isListening = false,
  disabled = false,
  text = DEFAULT_TEXT,
  onStartRecording,
}: MicPromptProps) {
  return (
    <section className={`mic-prompt ${isListening ? 'listening' : ''}`}>
      <p>{isListening ? text.listeningLabel : prompt || text.prompt}</p>
      <button type="button" disabled={disabled || isListening} onClick={onStartRecording}>
        {text.startLabel}
      </button>
    </section>
  );
}
