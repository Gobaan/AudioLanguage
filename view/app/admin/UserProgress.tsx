import { useMemo } from 'react';

import type { ValidationAdminSummary } from '../../api/validation';
import { AttemptCells } from './AttemptCells';
import { daysForUser, phrasesForUser } from './summary';
import type { Day, PhraseRow } from './types';

export function UserProgress({
  summary,
  participantId,
  language,
  displayName,
  deletingAttemptKey,
  scoringAttemptKey,
  deletingUser,
  isReadOnly = false,
  onDeleteAttempt,
  onScoreAttempt,
  onDeleteUser,
}: {
  summary: ValidationAdminSummary;
  participantId: string;
  language?: string;
  displayName?: string;
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  deletingUser: string | null;
  isReadOnly?: boolean;
  onDeleteAttempt?: (sessionId: string, attemptId: string) => void;
  onScoreAttempt?: (sessionId: string, attemptId: string) => void;
  onDeleteUser?: (participantId: string) => void;
}) {
  const days = useMemo(() => daysForUser(summary.sessions, participantId, language), [
    summary.sessions,
    participantId,
    language,
  ]);
  const phrases = useMemo(
    () => phrasesForUser(summary.targets, participantId, language),
    [summary.targets, participantId, language],
  );

  return (
    <section className="admin-progress-panel" aria-label={`${participantId} progress`}>
      <header>
        <div>
          <span>User</span>
          <h2>{displayName ?? participantId}</h2>
        </div>
        {!isReadOnly && onDeleteUser ? (
          <button
            type="button"
            className="admin-delete-user"
            disabled={deletingUser === participantId}
            onClick={() => onDeleteUser(participantId)}
          >
            {deletingUser === participantId ? 'Deleting' : 'Delete User'}
          </button>
        ) : null}
      </header>
      {phrases.length === 0 ? <p className="admin-status">No history yet.</p> : null}
      {phrases.length > 0 ? (
        <ProgressTable
          days={days}
          phrases={phrases}
          deletingAttemptKey={deletingAttemptKey}
          scoringAttemptKey={scoringAttemptKey}
          isReadOnly={isReadOnly}
          onDeleteAttempt={onDeleteAttempt}
          onScoreAttempt={onScoreAttempt}
        />
      ) : null}
    </section>
  );
}

function ProgressTable({
  days,
  phrases,
  deletingAttemptKey,
  scoringAttemptKey,
  isReadOnly,
  onDeleteAttempt,
  onScoreAttempt,
}: {
  days: Day[];
  phrases: PhraseRow[];
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  isReadOnly: boolean;
  onDeleteAttempt?: (sessionId: string, attemptId: string) => void;
  onScoreAttempt?: (sessionId: string, attemptId: string) => void;
}) {
  return (
    <div className="admin-progress-grid-wrap">
      <table className="admin-progress-grid">
        <thead>
          <tr>
            <th>Phrase</th>
            {days.map((day) => (
              <th key={day.sessionId}>
                <span>Day {day.dayNumber}</span>
                <em>{day.language}</em>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {phrases.map((phrase) => (
            <tr key={phrase.phraseKey}>
              <th>{phrase.phrase}</th>
              {days.map((day) => (
                <td key={`${phrase.phraseKey}:${day.sessionId}`}>
                  <AttemptCells
                    attempts={phrase.attemptsBySession[day.sessionId] ?? []}
                    sessionId={day.sessionId}
                    deletingAttemptKey={deletingAttemptKey}
                    scoringAttemptKey={scoringAttemptKey}
                    isReadOnly={isReadOnly}
                    onDeleteAttempt={onDeleteAttempt}
                    onScoreAttempt={onScoreAttempt}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
