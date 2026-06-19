const TRANSFER_TUTORIAL_DISMISSED_KEY = 'audiolanguage.transferTutorial.dismissed';

export function isTransferTutorialDismissed(): boolean {
  try {
    return localStorage.getItem(TRANSFER_TUTORIAL_DISMISSED_KEY) === 'true';
  } catch {
    return false;
  }
}

export function dismissTransferTutorial(): void {
  try {
    localStorage.setItem(TRANSFER_TUTORIAL_DISMISSED_KEY, 'true');
  } catch {
    // Ignore localStorage write failures and allow session-only dismissal.
  }
}

export function resetTransferTutorialDismissed(): void {
  try {
    localStorage.removeItem(TRANSFER_TUTORIAL_DISMISSED_KEY);
  } catch {
    // Ignore localStorage failures.
  }
}
