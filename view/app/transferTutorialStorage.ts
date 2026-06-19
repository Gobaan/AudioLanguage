const TUTORIAL_DISMISSED_KEY_PREFIX = 'audiolanguage.tutorial.dismissed';

export const TRANSFER_SCENE_TUTORIAL_ID = 'transfer-scene';
export const DELAYED_REVIEW_TUTORIAL_ID = 'delayed-review-scene';

export function tutorialDismissedStorageKey(tutorialId: string): string {
  return `${TUTORIAL_DISMISSED_KEY_PREFIX}.${tutorialId}`;
}

export function isTutorialDismissed(tutorialId: string): boolean {
  try {
    return localStorage.getItem(tutorialDismissedStorageKey(tutorialId)) === 'true';
  } catch {
    return false;
  }
}

export function dismissTutorial(tutorialId: string): void {
  try {
    localStorage.setItem(tutorialDismissedStorageKey(tutorialId), 'true');
  } catch {
    // Ignore localStorage write failures and allow session-only dismissal.
  }
}

export function resetTutorialDismissed(tutorialId: string): void {
  try {
    localStorage.removeItem(tutorialDismissedStorageKey(tutorialId));
  } catch {
    // Ignore localStorage failures.
  }
}

// Backward-compatible helpers for the original transfer tutorial.
export function isTransferTutorialDismissed(): boolean {
  return isTutorialDismissed(TRANSFER_SCENE_TUTORIAL_ID);
}

export function dismissTransferTutorial(): void {
  dismissTutorial(TRANSFER_SCENE_TUTORIAL_ID);
}

export function resetTransferTutorialDismissed(): void {
  resetTutorialDismissed(TRANSFER_SCENE_TUTORIAL_ID);
}
