type TransferTutorialModalProps = {
  onDismiss: () => void;
};

export function TransferTutorialModal({ onDismiss }: TransferTutorialModalProps) {
  return (
    <section className="transfer-tutorial-overlay" role="presentation" aria-hidden="true">
      <div
        className="transfer-tutorial-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="transfer-tutorial-title"
      >
        <p className="transfer-tutorial-badge">Tutorial</p>
        <h2 id="transfer-tutorial-title">Transfer scene</h2>
        <p>
          This is a transfer scene. It tests your ability to recall what you know and use it in a separate context.
          Be prepared to respond.
        </p>
        <nav className="transfer-tutorial-actions" aria-label="Transfer tutorial actions">
          <button type="button" onClick={onDismiss}>
            Got it
          </button>
        </nav>
      </div>
    </section>
  );
}
