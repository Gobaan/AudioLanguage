import { useMemo } from 'react';

import type { ValidationAdminSummary } from '../../api/validation';
import { AttemptCells } from './AttemptCells';
import { daysForUser, phrasesForUser } from './summary';

export function UserProgress({
  summary,
  participantId,
  deletingAttemptKey,
  scoringAttemptKey,
  deletingUser,
  onDeleteAttempt,
  onScoreAttempt,
  onDeleteUser,
}: {
  summary: ValidationAdminSummary;
  participantId: string;
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  deletingUser: string | null;
  onDeleteAttempt: (sessionId: string, attemptId: string) => void;
  onScoreAttempt: (sessionId: string, attemptId: string) => void;
  onDeleteUser: (participantId: string) => void;
}) {
  const days = useMemo(() => daysForUser(summary.sessions, participantId), [summary.sessions, participantId]);
  const phrases = useMemo(() => phrasesForUser(summary.targets, participantId), [summary.targets, participantId]);

  return (
    <section className="admin-progress-panel" aria-label={`${participantId} progress`}>
      <header>
        <div>
          <span>User</span>
          <h2>{participantId}</h2>
        </div>
        <button
          type="button"
          className="admin-delete-user"
          disabled={deletingUser === participantId}
          onClick={() => onDeleteUser(participantId)}
        >
          {deletingUser === participantId ? 'Deleting' : 'Delete User'}
        </button>
      </header>
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
              <tr key={phrase.targetId}>
                <th>{phrase.phrase}</th>
                {days.map((day) => (
                  <td key={`${phrase.targetId}:${day.sessionId}`}>
                    <AttemptCells
                      attempts={phrase.attemptsBySession[day.sessionId] ?? []}
                      sessionId={day.sessionId}
                      deletingAttemptKey={deletingAttemptKey}
                      scoringAttemptKey={scoringAttemptKey}
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
    </section>
  );
}
