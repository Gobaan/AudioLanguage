import { isLocalHost } from './urlParams';

type LessonAppLinksProps = {
  participantId: string | null;
  onOpenScorecard: () => void;
};

export function LessonAppLinks({ participantId, onOpenScorecard }: LessonAppLinksProps) {
  return (
    <nav className="local-app-links" aria-label="App links">
      <button type="button" className="app-link-button" onClick={onOpenScorecard}>
        Scorecard
      </button>
      {isLocalHost() ? (
        <>
          {participantId ? <span>{participantId}</span> : null}
          <a href="/admin/validation">Admin</a>
        </>
      ) : null}
    </nav>
  );
}
