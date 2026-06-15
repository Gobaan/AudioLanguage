type LessonAppLinksProps = {
  onOpenScorecard: () => void;
};

export function LessonAppLinks({ onOpenScorecard }: LessonAppLinksProps) {
  return (
    <nav className="local-app-links" aria-label="App links">
      <button type="button" className="app-link-button" onClick={onOpenScorecard}>
        Scorecard
      </button>
    </nav>
  );
}
