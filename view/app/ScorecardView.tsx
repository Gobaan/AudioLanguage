import { useState } from 'react';
import {
  overrideValidationAttemptScore,
  validationAttemptAudioUrl,
  type ScorecardAttempt,
  type ScorecardTarget,
  type ValidationScorecard,
} from '../api/validation';

export type ScorecardState = 'idle' | 'loading' | 'ready' | 'error';

const ACCURACY_PASS_THRESHOLD = 0.8;
const HAN_PATTERN = /[\u3400-\u9FFF]/;

type ValidationScorecardViewProps = {
  sessionId: string | null;
  state: ScorecardState;
  scorecard: ValidationScorecard | null;
  onBack: () => void;
  onRefresh: () => void;
  onNextLesson?: (() => void) | null;
  onViewAnchor?: (target: ScorecardTarget) => void;
};

export function ValidationScorecardView({
  sessionId,
  state,
  scorecard,
  onBack,
  onRefresh,
  onNextLesson,
  onViewAnchor,
}: ValidationScorecardViewProps) {
  return (
    <section className="validation-scorecard" aria-label="Validation scorecard">
      <header className="scorecard-header">
        <div>
          <h1>Scorecard</h1>
        </div>
        <nav className="scorecard-actions" aria-label="Scorecard controls">
          {scorecard?.session.participantId ? <a href="/history">History</a> : null}
          {onNextLesson ? (
            <button type="button" onClick={onNextLesson} disabled={state === 'loading'}>
              {state === 'loading' ? 'Scoring...' : 'Next lesson'}
            </button>
          ) : null}
          <button type="button" onClick={onBack}>
            Back
          </button>
          <button type="button" onClick={onRefresh}>
            Refresh
          </button>
        </nav>
      </header>

      {state === 'loading' ? <p className="scorecard-status">Scoring your recordings...</p> : null}
      {state === 'error' ? (
        <p className="scorecard-status">Scorecard is unavailable.</p>
      ) : null}
      {state === 'ready' && scorecard ? (
        <ScorecardDetails
          scorecard={scorecard}
          onRefresh={onRefresh}
          onViewAnchor={onViewAnchor}
        />
      ) : null}
    </section>
  );
}

function ScorecardDetails({
  scorecard,
  onRefresh,
  onViewAnchor,
}: {
  scorecard: ValidationScorecard;
  onRefresh: () => void;
  onViewAnchor?: (target: ScorecardTarget) => void;
}) {
  const [overrideAttemptKey, setOverrideAttemptKey] = useState<string | null>(null);
  const [overrideError, setOverrideError] = useState<string | null>(null);

  return (
    <>
      <section className="scorecard-targets" aria-label="Scorecard targets">
        {scorecard.targets.length === 0 ? (
          <p className="scorecard-status">No recordings have been captured yet.</p>
        ) : (
          scorecard.targets.map((target) => (
            <article className="scorecard-target" key={target.targetId}>
              <header>
                <div className="scorecard-target-intro">
                  <span>Learner line</span>
                  <h2>{targetLineLabel(target)}</h2>
                </div>
                <div className="scorecard-target-actions">
                  {target.anchorLessonPage && onViewAnchor ? (
                    <button type="button" onClick={() => onViewAnchor(target)}>
                      View anchor
                    </button>
                  ) : null}
                </div>
              </header>
              <ul>
                {target.attempts.map((attempt) => (
                  <ScorecardAttemptRow
                    key={attempt.attemptId}
                    attempt={attempt}
                    sessionId={scorecard.session.sessionId}
                    isOverriding={overrideAttemptKey === attempt.attemptId}
                    onOverride={overrideAttempt}
                  />
                ))}
              </ul>
              {overrideError ? <p className="scorecard-status">{overrideError}</p> : null}
            </article>
          ))
        )}
      </section>
    </>
  );

  async function overrideAttempt(attemptId: string, isCorrect: boolean) {
    setOverrideAttemptKey(attemptId);
    setOverrideError(null);
    try {
      await overrideValidationAttemptScore(scorecard.session.sessionId, attemptId, isCorrect);
      onRefresh();
    } catch (error) {
      setOverrideError(scoreOverrideErrorMessage(error));
    } finally {
      setOverrideAttemptKey(null);
    }
  }
}

function ScorecardAttemptRow({
  attempt,
  sessionId,
  isOverriding,
  onOverride,
}: {
  attempt: ScorecardAttempt;
  sessionId: string;
  isOverriding: boolean;
  onOverride: (attemptId: string, isCorrect: boolean) => void;
}) {
  const saidLine = attemptSaidLine(attempt);
  const isCorrect = attemptIsRemembered(attempt);
  const nextIsCorrect = !isCorrect;

  return (
    <li className={attemptAccuracyClass(attempt)}>
      <div className="scorecard-attempt-copy">
        <div className="scorecard-attempt-heading">
          <strong>{attemptStepLabel(attempt)}</strong>
          <span>{scoreLabel(attempt)}</span>
          {attempt.aiScore?.overridesAttemptScore ? <span>Corrected by learner</span> : null}
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
        <div className="scorecard-override-actions" aria-label="Correct this score">
          <button type="button" disabled={isOverriding} onClick={() => onOverride(attempt.attemptId, nextIsCorrect)}>
            {isOverriding ? 'Saving...' : nextIsCorrect ? 'Mark correct' : 'Mark incorrect'}
          </button>
        </div>
      </div>
    </li>
  );
}

function targetLineLabel(target: ScorecardTarget): string {
  return target.learnerLine || target.expectedTransliteration || target.expectedText || target.targetId;
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
  return attemptIsRemembered(attempt) ? 'passed' : 'failed';
}

function attemptAccuracy(attempt: ScorecardAttempt): number | null {
  const score = attempt.aiScore;
  if (!score || score.status !== 'scored') {
    return null;
  }

  const confidence = score.result?.communication?.confidence;
  return typeof confidence === 'number' ? confidence : null;
}

function attemptIsRemembered(attempt: ScorecardAttempt): boolean {
  const score = attempt.aiScore;
  if (!score || score.status !== 'scored') {
    return false;
  }
  const communication = score.result?.communication;
  if (communication?.close_enough === true) {
    return true;
  }
  const status = communication?.status || '';
  if (status === 'exact' || status === 'close' || status === 'understood' || status === 'learner_correct') {
    return true;
  }
  const confidence = attemptAccuracy(attempt);
  return confidence !== null && confidence > ACCURACY_PASS_THRESHOLD;
}

function scoreOverrideErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return 'Could not save that correction.';
  }
  return `Could not save that correction: ${error.message}`;
}
