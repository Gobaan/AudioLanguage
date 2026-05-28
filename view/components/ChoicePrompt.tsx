import type { ChoiceOption } from './types';

type ChoicePromptProps = {
  question?: string;
  choices?: ChoiceOption[];
  selectedChoiceId?: string;
  fallbackQuestion?: string;
  onSelectChoice?: (choice: ChoiceOption) => void;
};

export function ChoicePrompt({
  question,
  choices = [],
  selectedChoiceId,
  fallbackQuestion = 'Choose the best response',
  onSelectChoice,
}: ChoicePromptProps) {
  const hasSelection = Boolean(selectedChoiceId);

  return (
    <fieldset className="choice-prompt">
      <legend>{question || fallbackQuestion}</legend>
      {choices.map((choice) => (
        <button
          key={choice.id}
          type="button"
          className={choiceClassName(choice)}
          aria-pressed={choice.id === selectedChoiceId}
          onClick={() => onSelectChoice?.(choice)}
        >
          {choice.label}
        </button>
      ))}
    </fieldset>
  );

  function choiceClassName(choice: ChoiceOption): string {
    if (!hasSelection) {
      return '';
    }

    if (choice.isCorrect) {
      return 'correct';
    }

    return choice.id === selectedChoiceId ? 'selected incorrect' : '';
  }
}
