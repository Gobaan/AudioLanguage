import { useState } from 'react';

import { TransferTutorialModal } from './TransferTutorialModal';
import {
  dismissTransferTutorial,
  isTransferTutorialDismissed,
  resetTransferTutorialDismissed,
} from './transferTutorialStorage';

export function DebugTransferTutorialPage() {
  const [dismissed, setDismissed] = useState<boolean>(() => isTransferTutorialDismissed());
  const [isOpen, setIsOpen] = useState<boolean>(() => !isTransferTutorialDismissed());

  function refreshFromStorage() {
    const nextDismissed = isTransferTutorialDismissed();
    setDismissed(nextDismissed);
    setIsOpen(!nextDismissed);
  }

  function handleDismiss() {
    dismissTransferTutorial();
    setDismissed(true);
    setIsOpen(false);
  }

  function handleReset() {
    resetTransferTutorialDismissed();
    setDismissed(false);
    setIsOpen(true);
  }

  return (
    <section className="audio-debug-page" aria-label="Transfer tutorial debug page">
      <header>
        <span>Debug</span>
        <h1>Transfer tutorial state</h1>
      </header>
      <p>Use this page to test the transfer tutorial dialog and localStorage dismissal flag.</p>
      <dl className="transfer-debug-state">
        <div>
          <dt>Storage key</dt>
          <dd>`audiolanguage.transferTutorial.dismissed`</dd>
        </div>
        <div>
          <dt>Dismissed</dt>
          <dd>{dismissed ? 'true' : 'false'}</dd>
        </div>
        <div>
          <dt>Dialog open</dt>
          <dd>{isOpen ? 'true' : 'false'}</dd>
        </div>
      </dl>
      <div className="audio-debug-controls">
        <button type="button" onClick={() => setIsOpen(true)} disabled={isOpen}>
          Open dialog
        </button>
        <button type="button" onClick={handleDismiss} disabled={dismissed}>
          Set dismissed=true
        </button>
        <button type="button" onClick={handleReset}>
          Reset dismissed flag
        </button>
        <button type="button" onClick={refreshFromStorage}>
          Refresh from storage
        </button>
      </div>
      <div className="transfer-tutorial-preview-host" aria-label="Transfer tutorial preview over scene frame">
        {isOpen ? <TransferTutorialModal onDismiss={handleDismiss} /> : null}
      </div>
      {!isOpen ? <p className="audio-debug-status">Dialog closed.</p> : null}
    </section>
  );
}
