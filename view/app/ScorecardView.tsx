import { validationAttemptAudioUrl, type ValidationScorecard } from '../api/validation';

export type ScorecardState = 'idle' | 'loading' | 'ready' | 'error';

type ValidationScorecardViewProps = {
  sessionId: string | null;
  state: ScorecardState;
  scorecard: ValidationScorecard | null;
  onBack: () => void;
  onRefresh: () => void;
};

export function ValidationScorecardView({
  sessionId,
  state,
  scorecard,
  onBack,
  onRefresh,
}: ValidationScorecardViewProps) {
  return (
    <section className="validation-scorecard" aria-label="Validation scorecard">
      <header className="scorecard-header">
        <div>
          <span>Local validation</span>
          <h1>Scorecard</h1>
        </div>
        <nav className="scorecard-actions" aria-label="Scorecard controls">
          <button type="button" onClick={onBack}>
            Back
          </button>
          <button type="button" onClick={onRefresh}>
            Refresh
          </button>
        </nav>
      </header>

      {state === 'loading' ? <p className="scorecard-status">Loading scorecard.</p> : null}
      {state === 'error' ? (
        <p className="scorecard-status">Scorecard is unavailable. Session: {sessionId ?? 'none'}</p>
      ) : null}
      {state === 'ready' && scorecard ? <ScorecardDetails scorecard={scorecard} /> : null}
    </section>
  );
}

function ScorecardDetails({ scorecard }: { scorecard: ValidationScorecard }) {
  return (
    <>
      <dl className="scorecard-summary">
        <div>
          <dt>Session</dt>
          <dd>{scorecard.session.sessionId}</dd>
        </div>
        <div>
          <dt>Events</dt>
          <dd>{scorecard.eventCount}</dd>
        </div>
        <div>
          <dt>Attempts</dt>
          <dd>{scorecard.attemptCount}</dd>
        </div>
      </dl>

      <section className="scorecard-targets" aria-label="Scorecard targets">
        {scorecard.targets.length === 0 ? (
          <p className="scorecard-status">No recordings have been captured yet.</p>
        ) : (
          scorecard.targets.map((target) => (
            <article className="scorecard-target" key={target.targetId}>
              <header>
                <div>
                  <span>{target.targetId}</span>
                  <h2>{target.expectedTransliteration || target.expectedText || 'Target'}</h2>
                </div>
                {target.targetAudioUrl ? <audio controls src={target.targetAudioUrl} aria-label="Target audio" /> : null}
              </header>
              <ul>
                {target.attempts.map((attempt) => (
                  <li key={attempt.attemptId}>
                    <div>
                      <strong>{attempt.stepId}</strong>
                      <span>{scoreLabel(attempt)}</span>
                    </div>
                    <audio controls src={validationAttemptAudioUrl(scorecard.session.sessionId, attempt.attemptId)} />
                  </li>
                ))}
              </ul>
            </article>
          ))
        )}
      </section>
    </>
  );
}

function scoreLabel(attempt: { buildPromptText?: string; lessonPage?: string; aiScore?: unknown }): string {
  const score = attempt.aiScore as
    | { status?: string; result?: { communication?: { status?: string; confidence?: number } } }
    | null
    | undefined;
  if (!score) {
    return attempt.buildPromptText || attempt.lessonPage || 'Needs score';
  }
  if (score.status !== 'scored') {
    return 'AI score unavailable';
  }

  const communication = score.result?.communication;
  const confidence = typeof communication?.confidence === 'number' ? ` ${Math.round(communication.confidence * 100)}%` : '';
  return `${communication?.status || 'scored'}${confidence}`;
}
