import { useState } from 'react';

import type { ValidationAdminTarget, ValidationAdminTargetSession } from '../../api/validation';
import { RecordingCell } from './RecordingCell';

export function AttemptCells({
  attempts,
  sessionId,
  deletingAttemptKey,
  scoringAttemptKey,
  onDeleteAttempt,
  onScoreAttempt,
}: {
  attempts: Array<ValidationAdminTargetSession & { target: ValidationAdminTarget }>;
  sessionId: string;
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  onDeleteAttempt: (sessionId: string, attemptId: string) => void;
  onScoreAttempt: (sessionId: string, attemptId: string) => void;
}) {
  const [recordingIndex, setRecordingIndex] = useState(0);

  if (attempts.length === 0) {
    return <span className="attempt-empty">-</span>;
  }

  const choiceEvents = attempts.filter((attempt) => attempt.type === 'choice');
  const recordings = attempts.filter((attempt) => attempt.type !== 'choice');
  const activeRecording = recordings[Math.min(recordingIndex, Math.max(recordings.length - 1, 0))];

  return (
    <div className="admin-attempt-cells">
      {choiceEvents.map((attempt, index) => {
        const isCorrect = attempt.choiceCorrect === true;
        return (
          <div
            key={`${attempt.eventId ?? index}:${attempt.choiceId ?? ''}`}
            className={isCorrect ? 'choice-cell passed' : 'choice-cell failed'}
          >
            <span>{isCorrect ? 'choice correct' : 'choice wrong'}</span>
          </div>
        );
      })}
      {activeRecording ? (
        <RecordingCell
          attempt={activeRecording}
          sessionId={sessionId}
          attemptNumber={Math.min(recordingIndex, recordings.length - 1) + 1}
          attemptCount={recordings.length}
          deletingAttemptKey={deletingAttemptKey}
          scoringAttemptKey={scoringAttemptKey}
          onDeleteAttempt={onDeleteAttempt}
          onScoreAttempt={onScoreAttempt}
          onNextAttempt={() => setRecordingIndex((value) => (value + 1) % recordings.length)}
        />
      ) : null}
    </div>
  );
}
