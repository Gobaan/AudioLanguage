type LearnerSessionLandingProps = {
  language: string;
  displayName?: string | null;
  lessonCount?: number;
  sessionPhase: 'landing' | 'complete';
  participantReady: boolean;
  onStartSession: () => void;
  onContinue: () => void;
};

export function LearnerSessionLanding({
  language,
  displayName,
  lessonCount,
  sessionPhase,
  participantReady,
  onStartSession,
  onContinue,
}: LearnerSessionLandingProps) {
  if (!participantReady) {
    return <div className="frame-placeholder" aria-label="Preparing your session" />;
  }

  const languageLabel = displayName ?? language.toUpperCase();
  const isComplete = sessionPhase === 'complete';
  const queueSummary =
    lessonCount && lessonCount > 0
      ? `${lessonCount} scene${lessonCount === 1 ? '' : 's'} in your last queue`
      : 'Short adaptive scenes picked for you';

  return (
    <section className="learner-session-landing" aria-label="Learner session home">
      <header>
        <span>Audio Language</span>
        <h1>{isComplete ? 'Nice work' : 'Ready for your next session?'}</h1>
        <p>
          {isComplete
            ? `You finished your ${languageLabel} queue. Keep going when you want more practice.`
            : `${languageLabel} — ${queueSummary}.`}
        </p>
      </header>

      <div className="learner-session-actions">
        {isComplete ? (
          <button type="button" className="session-primary-action" onClick={onContinue}>
            Continue
          </button>
        ) : (
          <button type="button" className="session-primary-action" onClick={onStartSession}>
            Next session
          </button>
        )}
      </div>
    </section>
  );
}
