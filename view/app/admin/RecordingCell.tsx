import { validationAttemptAudioUrl, type ValidationAdminTarget, type ValidationAdminTargetSession } from '../../api/validation';

export function RecordingCell({
  attempt,
  sessionId,
  attemptNumber,
  attemptCount,
  deletingAttemptKey,
  scoringAttemptKey,
  onDeleteAttempt,
  onScoreAttempt,
  onNextAttempt,
}: {
  attempt: ValidationAdminTargetSession & { target: ValidationAdminTarget };
  sessionId: string;
  attemptNumber: number;
  attemptCount: number;
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  onDeleteAttempt: (sessionId: string, attemptId: string) => void;
  onScoreAttempt: (sessionId: string, attemptId: string) => void;
  onNextAttempt: () => void;
}) {
  const hasPassed = attempt.scorePassed === true;
  const attemptId = attempt.attemptId;
  const attemptKey = `${sessionId}:${attemptId}`;
  const canScore =
    !!attemptId &&
    attempt.scoreStatus !== 'scored' &&
    attempt.scoreStatus !== 'exact' &&
    attempt.scoreStatus !== 'close';

  return (
    <div className={hasPassed ? 'attempt-cell passed' : 'attempt-cell failed'}>
      <header>
        <span>{attempt.scoreStatus || 'unscored'}</span>
        {attemptCount > 1 ? (
          <button type="button" className="retry-toggle" onClick={onNextAttempt}>
            Try {attemptNumber} / {attemptCount}
          </button>
        ) : null}
      </header>
      {attemptId ? (
        <>
          <audio controls src={validationAttemptAudioUrl(sessionId, attemptId)} />
          <div className="attempt-actions">
            {canScore ? (
              <button
                type="button"
                className="score-button"
                disabled={scoringAttemptKey === attemptKey}
                onClick={() => onScoreAttempt(sessionId, attemptId)}
              >
                {scoringAttemptKey === attemptKey ? 'Scoring' : 'Score'}
              </button>
            ) : null}
            <button
              type="button"
              disabled={deletingAttemptKey === attemptKey}
              onClick={() => onDeleteAttempt(sessionId, attemptId)}
            >
              {deletingAttemptKey === attemptKey ? 'Deleting' : 'Delete'}
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}
