import type { ChoiceOption } from './types';
import { ChoicePrompt } from './ChoicePrompt';

type SimilarPhraseContrastProps = {
  explanation?: string;
  choices?: ChoiceOption[];
  question?: string;
  fallbackQuestion?: string;
};

export function SimilarPhraseContrast({
  explanation = 'Pick the phrase that matches the scene.',
  choices = [],
  question,
  fallbackQuestion,
}: SimilarPhraseContrastProps) {
  return (
    <section className="similar-phrase-contrast">
      <p>{explanation}</p>
      <ChoicePrompt choices={choices} question={question} fallbackQuestion={fallbackQuestion} />
    </section>
  );
}
