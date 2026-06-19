type LearnerSessionLandingProps = {
  language: string;
  displayName?: string | null;
  lessonCount?: number;
  sessionPhase: 'landing' | 'complete';
  planState: 'loading' | 'ready' | 'error';
  participantReady: boolean;
  onStartSession: () => void;
  onContinue: () => void;
  actionsDisabled?: boolean;
};

export function LearnerSessionLanding({
  language,
  displayName,
  lessonCount,
  sessionPhase,
  planState,
  participantReady,
  onStartSession,
  onContinue,
  actionsDisabled = false,
}: LearnerSessionLandingProps) {
  if (!participantReady) {
    return <div className="frame-placeholder" aria-label="Preparing your session" />;
  }

  const languageLabel = displayName ?? language.toUpperCase();
  const hasQueuedLessons = planState === 'ready' && Boolean(lessonCount && lessonCount > 0);
  const hasNothingDue = planState === 'ready' && !hasQueuedLessons;
  const canStart = hasQueuedLessons && !actionsDisabled;
  const isComplete = sessionPhase === 'complete';
  const queueSummary = lessonCount ? `${lessonCount} scene${lessonCount === 1 ? '' : 's'} in your last queue` : '';
  const headline =
    planState === 'loading'
      ? 'Preparing your next session...'
      : planState === 'error'
        ? 'Session queue unavailable'
        : hasNothingDue
          ? 'Nothing due, come back tomorrow!'
          : isComplete
            ? 'Nice work'
            : 'Ready for your next session?';
  const description =
    planState === 'loading'
      ? `Checking what is due for ${languageLabel}.`
      : planState === 'error'
        ? `Couldn't load your ${languageLabel} session queue. Try again in a moment.`
        : hasNothingDue
          ? `${languageLabel} is all caught up for now.`
          : isComplete
            ? `You finished your ${languageLabel} queue. Keep going when you want more practice.`
            : `${languageLabel} — ${queueSummary}.`;

  return (
    <section className="learner-session-landing" aria-label="Learner session home">
      <header>
        <span>Audio Language</span>
        <h1>{headline}</h1>
        <p>{description}</p>
      </header>

      {hasQueuedLessons ? (
        <div className="learner-session-actions">
          {isComplete ? (
            <button type="button" className="session-primary-action" onClick={onContinue} disabled={!canStart}>
              {actionsDisabled ? 'Scoring...' : 'Continue'}
            </button>
          ) : (
            <button type="button" className="session-primary-action" onClick={onStartSession} disabled={!canStart}>
              Next session
            </button>
          )}
        </div>
      ) : null}
    </section>
  );
}
