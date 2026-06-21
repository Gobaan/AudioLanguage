import { useEffect, useState } from 'react';

import {
  fetchValidationHistorySummary,
  type ValidationAdminSummary,
} from '../../api/validation';
import { PARTICIPANT_STORAGE_KEY } from '../useParticipantId';
import { UserProgress } from './UserProgress';

type LoadState = 'loading' | 'ready' | 'error';

export function UserHistoryApp() {
  const participantId = historyParticipantId();
  const [summary, setSummary] = useState<ValidationAdminSummary | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');

  useEffect(() => {
    if (!participantId) {
      setLoadState('error');
      return;
    }

    setLoadState('loading');
    fetchValidationHistorySummary(participantId)
      .then((nextSummary) => {
        setSummary(nextSummary);
        setLoadState('ready');
      })
      .catch(() => {
        setSummary(null);
        setLoadState('error');
      });
  }, [participantId]);

  if (loadState === 'loading') {
    return <p className="admin-status">Loading history.</p>;
  }

  if (loadState === 'error' || !summary || !participantId) {
    return (
      <section className="validation-admin simple">
        <HistoryHeader />
        <p className="admin-status">History is unavailable.</p>
      </section>
    );
  }

  return (
    <section className="validation-admin simple" aria-label="User history">
      <HistoryHeader />
      <UserProgress
        summary={summary}
        participantId={participantId}
        deletingAttemptKey={null}
        scoringAttemptKey={null}
        deletingUser={null}
        isReadOnly
      />
    </section>
  );
}

function HistoryHeader() {
  return (
    <header className="admin-header">
      <div>
        <span>Your practice history</span>
        <h1>History</h1>
      </div>
      <nav className="admin-actions" aria-label="History controls">
        <a href="/learn">Lesson app</a>
      </nav>
    </header>
  );
}

function historyParticipantId(): string | null {
  return localStorage.getItem(PARTICIPANT_STORAGE_KEY);
}
