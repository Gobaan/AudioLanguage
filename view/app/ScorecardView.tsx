import { validationAttemptAudioUrl, type ScorecardAttempt, type ValidationScorecard } from '../api/validation';
import { assetUrl } from './lessonUrls';

export type ScorecardState = 'idle' | 'loading' | 'ready' | 'error';

const ACCURACY_PASS_THRESHOLD = 0.8;
const HAN_PATTERN = /[\u3400-\u9FFF]/;

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
        <p className="scorecard-status">Scorecard is unavailable.</p>
      ) : null}
      {state === 'ready' && scorecard ? <ScorecardDetails scorecard={scorecard} /> : null}
    </section>
  );
}

function ScorecardDetails({ scorecard }: { scorecard: ValidationScorecard }) {
  return (
    <>
      <section className="scorecard-targets" aria-label="Scorecard targets">
        {scorecard.targets.length === 0 ? (
          <p className="scorecard-status">No recordings have been captured yet.</p>
        ) : (
          scorecard.targets.map((target) => (
            <article className="scorecard-target" key={target.targetId}>
              <header className="scorecard-target-intro">
                <span>Learner line</span>
                {target.targetAudioUrl ? (
                  <audio
                    className="scorecard-learner-audio"
                    controls
                    src={assetUrl(target.targetAudioUrl)}
                    aria-label="Learner line"
                  />
                ) : (
                  <p className="scorecard-status">Learner line audio unavailable.</p>
                )}
              </header>
              <ul>
                {target.attempts.map((attempt) => (
                  <ScorecardAttemptRow
                    key={attempt.attemptId}
                    attempt={attempt}
                    sessionId={scorecard.session.sessionId}
                  />
                ))}
              </ul>
            </article>
          ))
        )}
      </section>
    </>
  );
}

function ScorecardAttemptRow({
  attempt,
  sessionId,
}: {
  attempt: ScorecardAttempt;
  sessionId: string;
}) {
  const saidLine = attemptSaidLine(attempt);

  return (
    <li className={attemptAccuracyClass(attempt)}>
      <div className="scorecard-attempt-copy">
        <div className="scorecard-attempt-heading">
          <strong>{attemptStepLabel(attempt)}</strong>
          <span>{scoreLabel(attempt)}</span>
        </div>
        <dl className="scorecard-attempt-phrases">
          <div>
            <dt>You said</dt>
            <dd>{saidLine ?? (attempt.aiScore ? '—' : 'Not scored yet')}</dd>
          </div>
        </dl>
      </div>
      <div className="scorecard-attempt-audio">
        <span className="scorecard-audio-label">Your recording</span>
        <audio controls src={validationAttemptAudioUrl(sessionId, attempt.attemptId)} />
      </div>
    </li>
  );
}

function attemptStepLabel(attempt: ScorecardAttempt): string {
  if (attempt.stepId === 'backward_build') {
    return 'Production';
  }
  if (attempt.stepId === 'scene_recall') {
    return 'Scene recall';
  }
  if (attempt.stepId === 'production_prompt') {
    return 'Production';
  }

  return attempt.stepId?.replace(/_/g, ' ') || 'Recording';
}

function attemptSaidLine(attempt: ScorecardAttempt): string | null {
  const romanized = attempt.aiScore?.result?.transcript_romanized?.trim();
  if (!romanized) {
    return null;
  }

  return learnerFacingRomanized(romanized);
}

function learnerFacingRomanized(value: string): string {
  if (!HAN_PATTERN.test(value)) {
    return value;
  }

  const latin = value.match(/[A-Za-z]+(?:'[A-Za-z]+)?/g)?.join(' ').trim();
  return latin || value;
}

function scoreLabel(attempt: ScorecardAttempt): string {
  const score = attempt.aiScore;
  if (!score) {
    return 'Needs score';
  }
  if (score.status !== 'scored') {
    return 'AI score unavailable';
  }

  const communication = score.result?.communication;
  const confidence = typeof communication?.confidence === 'number' ? ` ${Math.round(communication.confidence * 100)}%` : '';
  return `${communication?.status || 'scored'}${confidence}`;
}

function attemptAccuracyClass(attempt: ScorecardAttempt): 'passed' | 'failed' {
  const confidence = attemptAccuracy(attempt);
  if (confidence === null) {
    return 'failed';
  }

  return confidence > ACCURACY_PASS_THRESHOLD ? 'passed' : 'failed';
}

function attemptAccuracy(attempt: ScorecardAttempt): number | null {
  const score = attempt.aiScore;
  if (!score || score.status !== 'scored') {
    return null;
  }

  const confidence = score.result?.communication?.confidence;
  return typeof confidence === 'number' ? confidence : null;
}
