import { useEffect, useRef, useState, type FormEvent } from 'react';

import { saveRecommendedPhrase } from '../api/recommendedPhrases';

const MAX_RECOMMENDED_PHRASE_LENGTH = 250;

type SaveState = 'idle' | 'saving' | 'saved' | 'error';

export function RecommendPhraseButton() {
  const dialogRef = useRef<HTMLDialogElement | null>(null);
  const [phrase, setPhrase] = useState('');
  const [saveState, setSaveState] = useState<SaveState>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const remainingCharacters = MAX_RECOMMENDED_PHRASE_LENGTH - phrase.length;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    function resetStatus() {
      setSaveState('idle');
      setErrorMessage(null);
    }

    dialog.addEventListener('close', resetStatus);
    return () => dialog.removeEventListener('close', resetStatus);
  }, []);

  return (
    <>
      <button type="button" className="session-primary-action" onClick={openDialog}>
        Recommend phrases
      </button>
      <dialog ref={dialogRef} className="recommend-phrase-dialog" aria-label="Recommend phrases">
        <form method="dialog" className="recommend-phrase-close-form">
          <button type="submit" aria-label="Close">
            Close
          </button>
        </form>
        <form className="recommend-phrase-form" onSubmit={submitRecommendation}>
          <h2>Recommend phrases</h2>
          <label>
            <span>Phrase</span>
            <textarea
              value={phrase}
              maxLength={MAX_RECOMMENDED_PHRASE_LENGTH}
              onChange={(event) => setPhrase(event.target.value)}
              rows={4}
            />
          </label>
          <span>{remainingCharacters} characters left</span>
          {saveState === 'saved' ? <p>Saved. Thank you.</p> : null}
          {errorMessage ? <p role="alert">{errorMessage}</p> : null}
          <button type="submit" disabled={saveState === 'saving' || phrase.trim().length === 0}>
            {saveState === 'saving' ? 'Saving...' : 'Submit'}
          </button>
        </form>
      </dialog>
    </>
  );

  function openDialog() {
    dialogRef.current?.showModal();
  }

  async function submitRecommendation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaveState('saving');
    setErrorMessage(null);
    try {
      await saveRecommendedPhrase(phrase);
      setPhrase('');
      setSaveState('saved');
    } catch (error) {
      setSaveState('error');
      setErrorMessage(error instanceof Error ? error.message : 'Could not save phrase recommendation.');
    }
  }
}
