import type { UserSummary } from './types';

export function UserList({
  users,
  selectedUser,
  onSelectUser,
}: {
  users: UserSummary[];
  selectedUser: string | null;
  onSelectUser: (userKey: string) => void;
}) {
  return (
    <aside className="admin-user-list" aria-label="Users">
      <h2>Users</h2>
      {users.map((user) => (
        <button
          key={user.userKey}
          type="button"
          className={selectedUser === user.userKey ? 'active' : ''}
          onClick={() => onSelectUser(user.userKey)}
        >
          <strong>{user.displayName}</strong>
          <span>{user.locationFlag || '❓ Unknown'}</span>
          <span>
            {user.rememberedAttemptCount} / {user.attemptCount}
          </span>
        </button>
      ))}
    </aside>
  );
}
