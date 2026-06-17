import { isLocalHost } from './urlParams';

export function LocalDevLinks({ participantId }: { participantId: string | null }) {
  if (!isLocalHost()) return null;

  return (
    <nav className="local-app-links" aria-label="Local app links">
      {participantId ? <span>{participantId}</span> : null}
      <a href="/gobi-admin">Admin</a>
    </nav>
  );
}
