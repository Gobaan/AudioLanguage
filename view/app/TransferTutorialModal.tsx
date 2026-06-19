import type { LessonTutorial } from './lessonTutorials';

type TutorialBubbleModalProps = LessonTutorial & {
  onDismiss: () => void;
};

export function TutorialBubbleModal({
  onDismiss,
  badgeLabel,
  title,
  message,
  dismissLabel,
}: TutorialBubbleModalProps) {
  return (
    <section className="transfer-tutorial-overlay" role="presentation" aria-hidden="true">
      <div
        className="transfer-tutorial-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="transfer-tutorial-title"
      >
        <p className="transfer-tutorial-badge">{badgeLabel}</p>
        <h2 id="transfer-tutorial-title">{title}</h2>
        <p>{message}</p>
        <nav className="transfer-tutorial-actions" aria-label="Transfer tutorial actions">
          <button type="button" onClick={onDismiss}>
            {dismissLabel}
          </button>
        </nav>
      </div>
    </section>
  );
}
