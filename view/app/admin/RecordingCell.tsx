import { validationAttemptAudioUrl, type ValidationAdminTarget, type ValidationAdminTargetSession } from '../../api/validation';
import type { AdminTry } from './AttemptCells';

export function TryCell({
  item,
  sessionId,
  deletingAttemptKey,
  scoringAttemptKey,
  isReadOnly = false,
  onDeleteAttempt,
  onScoreAttempt,
}: {
  item: AdminTry;
  sessionId: string;
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  isReadOnly?: boolean;
  onDeleteAttempt?: (sessionId: string, attemptId: string) => void;
  onScoreAttempt?: (sessionId: string, attemptId: string) => void;
}) {
  const attempt = item.scene;
  const recording = item.recording;
  const choice = item.choice;
  const hasPassed = recording?.scorePassed === true;
  const attemptId = recording?.attemptId;
  const attemptKey = `${sessionId}:${attemptId}`;
  const sceneUrl = sceneHref(attempt);
  const canScore =
    !!attemptId &&
    recording?.scoreStatus !== 'scored' &&
    recording?.scoreStatus !== 'exact' &&
    recording?.scoreStatus !== 'close';

  return (
    <article className={hasPassed ? 'attempt-cell passed' : 'attempt-cell failed'}>
      <dl className="attempt-fields">
        <div>
          <dt>Type</dt>
          <dd>{tryHeading(attempt)}</dd>
        </div>
        <div>
          <dt>Choice</dt>
          <dd>{choiceStatus(choice)}</dd>
        </div>
        <div>
          <dt>Recording</dt>
          <dd>
            {recording && attemptId ? (
              <>
                <span>{recording.scoreStatus || 'Unscored'}</span>
                <audio controls src={validationAttemptAudioUrl(sessionId, attemptId)} />
              </>
            ) : (
              <span>No recording</span>
            )}
          </dd>
        </div>
        <div>
          <dt>Actions</dt>
          <dd>
            <div className="attempt-actions">
              {sceneUrl ? (
                <a className="scene-button" href={sceneUrl}>
                  View scene
                </a>
              ) : null}
              {!isReadOnly && recording && attemptId ? (
                <>
                  {canScore ? (
                    <button
                      type="button"
                      className="score-button"
                      disabled={scoringAttemptKey === attemptKey}
                      onClick={() => onScoreAttempt?.(sessionId, attemptId)}
                    >
                      {scoringAttemptKey === attemptKey ? 'Scoring' : 'Score'}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    disabled={deletingAttemptKey === attemptKey}
                    onClick={() => onDeleteAttempt?.(sessionId, attemptId)}
                  >
                    {deletingAttemptKey === attemptKey ? 'Deleting' : 'Delete record'}
                  </button>
                </>
              ) : null}
            </div>
          </dd>
        </div>
      </dl>
    </article>
  );

}

export const RecordingCell = TryCell;

function tryHeading(attempt: ValidationAdminTargetSession): string {
  return attempt.tryKindLabel || attempt.sceneKindLabel || 'Try';
}

function choiceStatus(attempt: ValidationAdminTargetSession | undefined): string {
  if (!attempt) {
    return 'No choice';
  }
  const result = attempt.choiceCorrect === true ? 'Right' : 'Wrong';
  return attempt.choiceId ? `${result}: ${attempt.choiceId}` : result;
}

function sceneHref(attempt: ValidationAdminTargetSession & { target: ValidationAdminTarget }): string | null {
  const sceneLanguage = attempt.language || attempt.target.language;
  const sceneSet = attempt.sceneSet || attempt.target.sceneSet;
  const lessonPage = attempt.lessonPage;
  if (!sceneLanguage || (!lessonPage && !attempt.lessonId)) return null;

  const params = new URLSearchParams();
  params.set('language', sceneLanguage);
  if (lessonPage) params.set('lessonPage', lessonPage);
  if (sceneSet) params.set('sceneSet', sceneSet);
  if (attempt.lessonId) params.set('lessonId', attempt.lessonId);
  params.set('returnTo', currentReturnPath());
  return `/scene?${params.toString()}`;
}

function currentReturnPath(): string {
  if (typeof window === 'undefined') return '/gobi-admin';
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}
