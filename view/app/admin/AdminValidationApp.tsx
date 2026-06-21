import { useEffect, useState } from 'react';

import {
  deleteValidationAttempt,
  deleteValidationUser,
  fetchValidationAdminSummary,
  scoreValidationAttempt,
  type ValidationAdminSummary,
} from '../../api/validation';
import { AdminHeader } from './AdminHeader';
import { adminUserKey, usersFromSummary } from './summary';
import { UserList } from './UserList';
import { UserProgress } from './UserProgress';
import type { UserSummary } from './types';

type LoadState = 'loading' | 'ready' | 'error';

export function AdminValidationApp() {
  const [summary, setSummary] = useState<ValidationAdminSummary | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [selectedUserKey, setSelectedUserKey] = useState<string | null>(null);
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
        const nextUsers = usersFromSummary(nextSummary);
        const currentUserKey = selectedUserKey && nextUsers.some((user) => user.userKey === selectedUserKey) ? selectedUserKey : null;
        const nextUserKey = currentUserKey ?? selectedUserKeyFromUrl(nextSummary) ?? nextUsers[0]?.userKey ?? null;
        setSummary(nextSummary);
        setLoadState('ready');
        setSelectedUserKey(nextUserKey);
        const nextUser = nextUsers.find((user) => user.userKey === nextUserKey);
        if (nextUser) {
          window.history.replaceState({}, '', adminUserPath(nextUser));
        }
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
  const activeUserKey = selectedUserKey ?? users[0]?.userKey ?? null;
  const activeUser = users.find((user) => user.userKey === activeUserKey) ?? users[0] ?? null;

  return (
    <section className="validation-admin simple" aria-label="Validation admin dashboard">
      <AdminHeader onRefresh={loadSummary} />
      <div className="admin-user-progress-shell">
        <UserList users={users} selectedUser={activeUser?.userKey ?? null} onSelectUser={selectUser} />
        {activeUser ? (
          <UserProgress
            summary={summary}
            participantId={activeUser.participantId}
            language={activeUser.language}
            displayName={activeUser.displayName}
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
        setSelectedUserKey(null);
        window.history.replaceState({}, '', '/gobi-admin');
        loadSummary();
      })
      .finally(() => setDeletingUser(null));
  }

  function selectUser(userKey: string) {
    setSelectedUserKey(userKey);
    const user = users.find((item) => item.userKey === userKey);
    if (user) {
      window.history.replaceState({}, '', adminUserPath(user));
    }
  }

  function scoreAttempt(sessionId: string, attemptId: string) {
    const attemptKey = `${sessionId}:${attemptId}`;
    setScoringAttemptKey(attemptKey);
    scoreValidationAttempt(sessionId, attemptId)
      .then(loadSummary)
      .finally(() => setScoringAttemptKey(null));
  }
}

function selectedUserKeyFromUrl(summary: ValidationAdminSummary): string | null {
  const params = new URLSearchParams(window.location.search);
  const participantId = params.get('participant');
  const language = params.get('language');
  if (!participantId || !language) return null;

  const userKey = adminUserKey(participantId, language);
  return usersFromSummary(summary).some((user) => user.userKey === userKey) ? userKey : null;
}

function adminUserPath(user: UserSummary): string {
  const params = new URLSearchParams();
  params.set('participant', user.participantId);
  params.set('language', user.language);
  return `/gobi-admin?${params.toString()}`;
}
