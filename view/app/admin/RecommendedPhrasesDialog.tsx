import { useEffect, useRef, useState } from 'react';

import { fetchRecommendedPhraseSummary, type RecommendedPhraseSummary } from '../../api/recommendedPhrases';

type LoadState = 'idle' | 'loading' | 'ready' | 'error';

export function RecommendedPhrasesDialog() {
  const dialogRef = useRef<HTMLDialogElement | null>(null);
  const [summary, setSummary] = useState<RecommendedPhraseSummary | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('idle');
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (loadState === 'idle') return;
    loadPhrase(index);
  }, [index]);

  const phrase = summary?.phrase ?? null;
  const count = summary?.count ?? 0;

  return (
    <>
      <button type="button" onClick={openDialog}>
        Recommended phrases
      </button>
      <dialog ref={dialogRef} className="recommended-phrases-dialog" aria-label="Recommended phrases">
        <form method="dialog" className="recommend-phrase-close-form">
          <button type="submit" aria-label="Close">
            Close
          </button>
        </form>
        <section className="recommended-phrases-panel">
          <header>
            <span>{count} phrases</span>
            <h2>Recommended phrases</h2>
          </header>
          {loadState === 'loading' ? <p>Loading recommendations.</p> : null}
          {loadState === 'error' ? <p role="alert">Phrase recommendations are unavailable.</p> : null}
          {loadState === 'ready' && !phrase ? <p>No phrases have been recommended yet.</p> : null}
          {phrase ? (
            <article>
              <p>{phrase.phrase}</p>
              <dl>
                <div>
                  <dt>From</dt>
                  <dd>{phrase.locationFlag || 'Unknown'}</dd>
                </div>
                <div>
                  <dt>IP</dt>
                  <dd>{phrase.clientIp || 'Unknown'}</dd>
                </div>
                <div>
                  <dt>Saved</dt>
                  <dd>{formatRecommendedAt(phrase.recommendedAt)}</dd>
                </div>
              </dl>
            </article>
          ) : null}
          <nav aria-label="Recommended phrase navigation">
            <button type="button" disabled={index <= 0 || loadState === 'loading'} onClick={() => setIndex((value) => value - 1)}>
              Previous
            </button>
            <span>
              {count === 0 ? 0 : index + 1} / {count}
            </span>
            <button
              type="button"
              disabled={count === 0 || index >= count - 1 || loadState === 'loading'}
              onClick={() => setIndex((value) => value + 1)}
            >
              Next
            </button>
          </nav>
        </section>
      </dialog>
    </>
  );

  function openDialog() {
    dialogRef.current?.showModal();
    loadPhrase(index);
  }

  function loadPhrase(nextIndex: number) {
    setLoadState('loading');
    fetchRecommendedPhraseSummary(nextIndex)
      .then((nextSummary) => {
        setSummary(nextSummary);
        setIndex(nextSummary.index);
        setLoadState('ready');
      })
      .catch(() => {
        setSummary(null);
        setLoadState('error');
      });
  }
}

function formatRecommendedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
