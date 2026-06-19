import { useState } from 'react';

import { tutorialForStage } from './lessonTutorials';
import { TutorialBubbleModal } from './TransferTutorialModal';
import {
  TRANSFER_SCENE_TUTORIAL_ID,
  dismissTutorial,
  isTutorialDismissed,
  resetTutorialDismissed,
  tutorialDismissedStorageKey,
} from './transferTutorialStorage';

export function DebugTransferTutorialPage() {
  const transferTutorial = tutorialForStage('same_day_transfer');
  const [dismissed, setDismissed] = useState<boolean>(() => isTutorialDismissed(TRANSFER_SCENE_TUTORIAL_ID));
  const [isOpen, setIsOpen] = useState<boolean>(() => !isTutorialDismissed(TRANSFER_SCENE_TUTORIAL_ID));

  function refreshFromStorage() {
    const nextDismissed = isTutorialDismissed(TRANSFER_SCENE_TUTORIAL_ID);
    setDismissed(nextDismissed);
    setIsOpen(!nextDismissed);
  }

  function handleDismiss() {
    dismissTutorial(TRANSFER_SCENE_TUTORIAL_ID);
    setDismissed(true);
    setIsOpen(false);
  }

  function handleReset() {
    resetTutorialDismissed(TRANSFER_SCENE_TUTORIAL_ID);
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
          <dd>{tutorialDismissedStorageKey(TRANSFER_SCENE_TUTORIAL_ID)}</dd>
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
        {isOpen && transferTutorial ? (
          <TutorialBubbleModal
            badgeLabel={transferTutorial.badgeLabel}
            title={transferTutorial.title}
            message={transferTutorial.message}
            dismissLabel={transferTutorial.dismissLabel}
            onDismiss={handleDismiss}
          />
        ) : null}
      </div>
      {!isOpen ? <p className="audio-debug-status">Dialog closed.</p> : null}
    </section>
  );
}
