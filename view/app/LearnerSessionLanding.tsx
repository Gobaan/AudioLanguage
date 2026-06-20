import { DailyReminderPrompt } from './DailyReminderPrompt';

type LearnerSessionLandingProps = {
  language: string;
  displayName?: string | null;
  lessonCount?: number;
  sessionPhase: 'landing' | 'complete';
  planState: 'loading' | 'ready' | 'error';
  participantReady: boolean;
  participantId: string | null;
  onStartSession: () => void;
  onContinue: () => void;
  actionsDisabled?: boolean;
};

const VALUE_PANELS = [
  {
    title: 'Travel phrases first',
    body:
      'Focus on greetings, ordering, asking for help, repairing confusion, and small social moments that make trips smoother.',
  },
  {
    title: 'Respond like real life',
    body:
      'Visual scenes give you context first, then push you to figure out what to say before the answer is handed to you.',
  },
  {
    title: 'Review what your brain needs',
    body:
      'Adaptive spaced repetition brings back the phrases and scenarios you struggle with, at the time they are most useful.',
  },
];

const METHOD_STEPS = [
  {
    title: 'Scene',
    body: 'See what is happening before translating.',
  },
  {
    title: 'Meaning',
    body: 'Infer the situation from audio and visuals.',
  },
  {
    title: 'Your turn',
    body: 'Speak before you feel fully ready.',
  },
  {
    title: 'Feedback',
    body: 'Check whether communication worked.',
  },
  {
    title: 'New situation later',
    body: 'Recall it again in a different travel moment.',
  },
];

export function LearnerSessionLanding({
  language,
  displayName,
  lessonCount,
  sessionPhase,
  planState,
  participantReady,
  participantId,
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
  const queuedSceneCount = lessonCount ?? 0;
  const queuedSceneLabel = `${queuedSceneCount} travel scene${queuedSceneCount === 1 ? '' : 's'} queued for ${languageLabel}`;
  const headline =
    planState === 'loading'
      ? 'Preparing your next session...'
      : planState === 'error'
        ? 'Session queue unavailable'
        : hasNothingDue
          ? 'Nothing due, come back tomorrow!'
          : isComplete
            ? 'Nice work. Your travel queue is complete.'
            : 'Ready for your next session?';
  const description =
    planState === 'loading'
      ? `Checking what is due for ${languageLabel}.`
      : planState === 'error'
        ? `Couldn't load your ${languageLabel} session queue. Try again in a moment.`
        : hasNothingDue
          ? `${languageLabel} is all caught up for now. Come back when more travel practice is ready.`
          : isComplete
            ? `You finished your ${languageLabel} queue. Keep going when you want more practice.`
            : 'Skip textbook coverage. Learn the high-value phrases travelers need, then practice responding quickly inside realistic visual scenes.';
  const actionLabel = actionsDisabled ? 'Scoring...' : isComplete ? 'Continue practicing' : 'Next session';
  const actionHandler = isComplete ? onContinue : onStartSession;

  return (
    <section className="learner-session-landing" aria-label="Learner session home">
      <div className="learner-session-hero">
        <header>
          <span>Audio Language</span>
          <h1>{headline}</h1>
          <p>{description}</p>
        </header>

        {hasQueuedLessons ? (
          <div className="learner-session-actions">
            <button type="button" className="session-primary-action" onClick={actionHandler} disabled={!canStart}>
              {actionLabel}
            </button>
            <span>{queuedSceneLabel}</span>
          </div>
        ) : null}
      </div>

      <DailyReminderPrompt participantId={participantId} />

      <section className="learning-value-grid" aria-label="Why this works">
        {VALUE_PANELS.map((panel) => (
          <article key={panel.title}>
            <h2>{panel.title}</h2>
            <p>{panel.body}</p>
          </article>
        ))}
      </section>

      <section className="learning-method-strip" aria-label="How one session works">
        <header>
          <span>Method</span>
          <h2>How one session works</h2>
        </header>
        <ol>
          {METHOD_STEPS.map((step) => (
            <li key={step.title}>
              <strong>{step.title}</strong>
              <span>{step.body}</span>
            </li>
          ))}
        </ol>
      </section>
    </section>
  );
}
