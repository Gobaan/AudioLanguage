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
  return (
    <fieldset className="choice-prompt">
      <legend>{question || fallbackQuestion}</legend>
      {choices.map((choice) => (
        <button
          key={choice.id}
          type="button"
          className={choice.id === selectedChoiceId ? 'selected' : ''}
          onClick={() => onSelectChoice?.(choice)}
        >
          {choice.label}
        </button>
      ))}
    </fieldset>
  );
}
