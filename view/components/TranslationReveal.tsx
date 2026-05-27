import type { TranslationRevealText } from './types';

type TranslationRevealProps = {
  translation?: string;
  isRevealed?: boolean;
  text?: TranslationRevealText;
  onReveal?: () => void;
};

const DEFAULT_TEXT: TranslationRevealText = {
  revealLabel: 'Reveal translation',
};

export function TranslationReveal({
  translation = 'Translation placeholder',
  isRevealed = false,
  text = DEFAULT_TEXT,
  onReveal,
}: TranslationRevealProps) {
  if (isRevealed) {
    return <p className="translation-reveal">{translation}</p>;
  }

  return (
    <button type="button" className="translation-reveal" onClick={onReveal}>
      {text.revealLabel}
    </button>
  );
}
