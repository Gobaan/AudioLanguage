import type { UserSummary } from './types';

export function UserList({
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
          <span>{user.locationFlag || '❓ Unknown'}</span>
          <span>
            {user.rememberedAttemptCount} / {user.attemptCount}
          </span>
        </button>
      ))}
    </aside>
  );
}
