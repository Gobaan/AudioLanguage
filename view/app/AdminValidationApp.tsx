import { useEffect, useMemo, useState } from 'react';
import {
  deleteValidationAttempt,
  deleteValidationUser,
  fetchValidationAdminSummary,
  scoreValidationAttempt,
  validationAttemptAudioUrl,
  type ValidationAdminSession,
  type ValidationAdminSummary,
  type ValidationAdminTarget,
  type ValidationAdminTargetSession,
} from '../api/validation';

type LoadState = 'loading' | 'ready' | 'error';
type UserSummary = {
  participantId: string;
  sessionCount: number;
  attemptCount: number;
  rememberedAttemptCount: number;
};
type Day = ValidationAdminSession & { dayNumber: number };
type PhraseRow = {
  phrase: string;
  targetId: string;
  attemptsBySession: Record<string, Array<ValidationAdminTargetSession & { target: ValidationAdminTarget }>>;
};

export function AdminValidationApp() {
  const [summary, setSummary] = useState<ValidationAdminSummary | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [deletingAttemptKey, setDeletingAttemptKey] = useState<string | null>(null);
  const [scoringAttemptKey, setScoringAttemptKey] = useState<string | null>(null);
  const [deletingUser, setDeletingUser] = useState<string | null>(null);

  useEffect(() => {
    loadSummary();
  }, []);

  function loadSummary() {
    setLoadState('loading');
    fetchValidationAdminSummary()
      .then((nextSummary) => {
        setSummary(nextSummary);
        setLoadState('ready');
        setSelectedUser((currentUser) => currentUser ?? usersFromSummary(nextSummary)[0]?.participantId ?? null);
      })
      .catch(() => {
        setSummary(null);
        setLoadState('error');
      });
  }

  if (loadState === 'loading') {
    return <p className="admin-status">Loading validation summary.</p>;
  }

  if (loadState === 'error' || !summary) {
    return (
      <section className="validation-admin simple">
        <AdminHeader onRefresh={loadSummary} />
        <p className="admin-status">Validation summary is unavailable.</p>
      </section>
    );
  }

  const users = usersFromSummary(summary);
  const activeUser = selectedUser ?? users[0]?.participantId ?? null;

  return (
    <section className="validation-admin simple" aria-label="Validation admin dashboard">
      <AdminHeader onRefresh={loadSummary} />
      <div className="admin-user-progress-shell">
        <UserList users={users} selectedUser={activeUser} onSelectUser={setSelectedUser} />
        {activeUser ? (
          <UserProgress
            summary={summary}
            participantId={activeUser}
            deletingAttemptKey={deletingAttemptKey}
            scoringAttemptKey={scoringAttemptKey}
            deletingUser={deletingUser}
            onDeleteAttempt={deleteAttempt}
            onScoreAttempt={scoreAttempt}
            onDeleteUser={deleteUser}
          />
        ) : (
          <p className="admin-status">No users have connected yet.</p>
        )}
      </div>
    </section>
  );

  function deleteAttempt(sessionId: string, attemptId: string) {
    if (!window.confirm('Delete this recording and score?')) return;

    const attemptKey = `${sessionId}:${attemptId}`;
    setDeletingAttemptKey(attemptKey);
    deleteValidationAttempt(sessionId, attemptId)
      .then(loadSummary)
      .finally(() => setDeletingAttemptKey(null));
  }

  function deleteUser(participantId: string) {
    if (!window.confirm(`Delete all validation data for ${participantId}?`)) return;

    setDeletingUser(participantId);
    deleteValidationUser(participantId)
      .then(() => {
        setSelectedUser(null);
        loadSummary();
      })
      .finally(() => setDeletingUser(null));
  }

  function scoreAttempt(sessionId: string, attemptId: string) {
    const attemptKey = `${sessionId}:${attemptId}`;
    setScoringAttemptKey(attemptKey);
    scoreValidationAttempt(sessionId, attemptId)
      .then(loadSummary)
      .finally(() => setScoringAttemptKey(null));
  }
}

function AdminHeader({ onRefresh }: { onRefresh: () => void }) {
  return (
    <header className="admin-header">
      <div>
        <span>Experiment dashboard</span>
        <h1>Validation Admin</h1>
      </div>
      <nav className="admin-actions" aria-label="Admin controls">
        <a href="/">Lesson app</a>
        <button type="button" onClick={onRefresh}>
          Refresh
        </button>
      </nav>
    </header>
  );
}

function UserList({
  users,
  selectedUser,
  onSelectUser,
}: {
  users: UserSummary[];
  selectedUser: string | null;
  onSelectUser: (participantId: string) => void;
}) {
  return (
    <aside className="admin-user-list" aria-label="Users">
      <h2>Users</h2>
      {users.map((user) => (
        <button
          key={user.participantId}
          type="button"
          className={selectedUser === user.participantId ? 'active' : ''}
          onClick={() => onSelectUser(user.participantId)}
        >
          <strong>{user.participantId}</strong>
          <span>{user.rememberedAttemptCount} / {user.attemptCount}</span>
        </button>
      ))}
    </aside>
  );
}

function UserProgress({
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

function AttemptCells({
  attempts,
  sessionId,
  deletingAttemptKey,
  scoringAttemptKey,
  onDeleteAttempt,
  onScoreAttempt,
}: {
  attempts: Array<ValidationAdminTargetSession & { target: ValidationAdminTarget }>;
  sessionId: string;
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  onDeleteAttempt: (sessionId: string, attemptId: string) => void;
  onScoreAttempt: (sessionId: string, attemptId: string) => void;
}) {
  const [recordingIndex, setRecordingIndex] = useState(0);

  if (attempts.length === 0) {
    return <span className="attempt-empty">-</span>;
  }

  const choiceEvents = attempts.filter((attempt) => attempt.type === 'choice');
  const recordings = attempts.filter((attempt) => attempt.type !== 'choice');
  const activeRecording = recordings[Math.min(recordingIndex, Math.max(recordings.length - 1, 0))];

  return (
    <div className="admin-attempt-cells">
      {choiceEvents.map((attempt, index) => {
        const isCorrect = attempt.choiceCorrect === true;
        return (
          <div
            key={`${attempt.eventId ?? index}:${attempt.choiceId ?? ''}`}
            className={isCorrect ? 'choice-cell passed' : 'choice-cell failed'}
          >
            <span>{isCorrect ? 'choice correct' : 'choice wrong'}</span>
          </div>
        );
      })}
      {activeRecording ? (
        <RecordingCell
          attempt={activeRecording}
          sessionId={sessionId}
          attemptNumber={Math.min(recordingIndex, recordings.length - 1) + 1}
          attemptCount={recordings.length}
          deletingAttemptKey={deletingAttemptKey}
          scoringAttemptKey={scoringAttemptKey}
          onDeleteAttempt={onDeleteAttempt}
          onScoreAttempt={onScoreAttempt}
          onNextAttempt={() => setRecordingIndex((value) => (value + 1) % recordings.length)}
        />
      ) : null}
    </div>
  );
}

function RecordingCell({
  attempt,
  sessionId,
  attemptNumber,
  attemptCount,
  deletingAttemptKey,
  scoringAttemptKey,
  onDeleteAttempt,
  onScoreAttempt,
  onNextAttempt,
}: {
  attempt: ValidationAdminTargetSession & { target: ValidationAdminTarget };
  sessionId: string;
  attemptNumber: number;
  attemptCount: number;
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  onDeleteAttempt: (sessionId: string, attemptId: string) => void;
  onScoreAttempt: (sessionId: string, attemptId: string) => void;
  onNextAttempt: () => void;
}) {
  const hasPassed = attempt.scorePassed === true;
  const attemptId = attempt.attemptId;
  const attemptKey = `${sessionId}:${attemptId}`;
  const canScore = !!attemptId && attempt.scoreStatus !== 'scored' && attempt.scoreStatus !== 'exact' && attempt.scoreStatus !== 'close';

  return (
    <div className={hasPassed ? 'attempt-cell passed' : 'attempt-cell failed'}>
      <header>
        <span>{attempt.scoreStatus || 'unscored'}</span>
        {attemptCount > 1 ? (
          <button type="button" className="retry-toggle" onClick={onNextAttempt}>
            Try {attemptNumber} / {attemptCount}
          </button>
        ) : null}
      </header>
      {attemptId ? (
        <>
          <audio controls src={validationAttemptAudioUrl(sessionId, attemptId)} />
          <div className="attempt-actions">
            {canScore ? (
              <button
                type="button"
                className="score-button"
                disabled={scoringAttemptKey === attemptKey}
                onClick={() => onScoreAttempt(sessionId, attemptId)}
              >
                {scoringAttemptKey === attemptKey ? 'Scoring' : 'Score'}
              </button>
            ) : null}
            <button
              type="button"
              disabled={deletingAttemptKey === attemptKey}
              onClick={() => onDeleteAttempt(sessionId, attemptId)}
            >
              {deletingAttemptKey === attemptKey ? 'Deleting' : 'Delete'}
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}

function usersFromSummary(summary: ValidationAdminSummary): UserSummary[] {
  const users: Record<string, UserSummary> = {};
  for (const session of summary.sessions) {
    const participantId = session.participantId || 'local';
    const user = users[participantId] ?? {
      participantId,
      sessionCount: 0,
      attemptCount: 0,
      rememberedAttemptCount: 0,
    };
    user.sessionCount += 1;
    user.attemptCount += session.attemptCount;
    user.rememberedAttemptCount += session.rememberedAttemptCount;
    users[participantId] = user;
  }

  return Object.values(users).sort((left, right) => left.participantId.localeCompare(right.participantId));
}

function daysForUser(sessions: ValidationAdminSession[], participantId: string): Day[] {
  return sessions
    .filter((session) => (session.participantId || 'local') === participantId)
    .sort((left, right) => String(left.createdAt || '').localeCompare(String(right.createdAt || '')))
    .map((session, index) => ({ ...session, dayNumber: index + 1 }));
}

function phrasesForUser(targets: ValidationAdminTarget[], participantId: string): PhraseRow[] {
  const rows: Record<string, PhraseRow> = {};

  for (const target of targets) {
    for (const attempt of target.sessions) {
      if ((attempt.participantId || 'local') !== participantId) continue;

      const phrase = target.expectedTransliteration || target.expectedText || target.targetId;
      const row = rows[target.targetId] ?? {
        phrase,
        targetId: target.targetId,
        attemptsBySession: {},
      };
      const attempts = row.attemptsBySession[attempt.sessionId] ?? [];
      attempts.push({ ...attempt, target });
      row.attemptsBySession[attempt.sessionId] = attempts.sort((left, right) =>
        String(left.receivedAt || '').localeCompare(String(right.receivedAt || '')),
      );
      rows[target.targetId] = row;
    }
  }

  return Object.values(rows).sort((left, right) => left.phrase.localeCompare(right.phrase));
}
