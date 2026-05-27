import type { ModeOption } from './types';

type ModeSelectorProps = {
  modes?: ModeOption[];
  selectedModeId?: string;
  ariaLabel?: string;
  onSelectMode?: (mode: ModeOption) => void;
};

const DEFAULT_MODES: ModeOption[] = [
  { id: 'traveller', label: 'Traveller' },
  { id: 'tv', label: 'TV' },
  { id: 'practice', label: 'Practice' },
];

export function ModeSelector({
  modes = DEFAULT_MODES,
  selectedModeId = String(modes[0]?.id ?? ''),
  ariaLabel = 'Lesson mode',
  onSelectMode,
}: ModeSelectorProps) {
  return (
    <div className="mode-selector" role="tablist" aria-label={ariaLabel}>
      {modes.map((mode) => (
        <button
          key={mode.id}
          type="button"
          role="tab"
          aria-label={mode.ariaLabel}
          aria-selected={String(mode.id) === selectedModeId}
          className={String(mode.id) === selectedModeId ? 'selected' : ''}
          onClick={() => onSelectMode?.(mode)}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}
