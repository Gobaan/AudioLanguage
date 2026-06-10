import { useEffect, useState } from 'react';

import {
  deleteValidationAttempt,
  deleteValidationUser,
  fetchValidationAdminSummary,
  scoreValidationAttempt,
  type ValidationAdminSummary,
} from '../../api/validation';
import { AdminHeader } from './AdminHeader';
import { usersFromSummary } from './summary';
import { UserList } from './UserList';
import { UserProgress } from './UserProgress';

type LoadState = 'loading' | 'ready' | 'error';

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
