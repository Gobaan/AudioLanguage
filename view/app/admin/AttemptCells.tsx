import { useState } from 'react';

import type { ValidationAdminTarget, ValidationAdminTargetSession } from '../../api/validation';
import { TryCell } from './RecordingCell';

export type AdminTry = {
  key: string;
  scene: ValidationAdminTargetSession & { target: ValidationAdminTarget };
  choice?: ValidationAdminTargetSession & { target: ValidationAdminTarget };
  recording?: ValidationAdminTargetSession & { target: ValidationAdminTarget };
};

export function AttemptCells({
  attempts,
  sessionId,
  deletingAttemptKey,
  scoringAttemptKey,
  isReadOnly = false,
  onDeleteAttempt,
  onScoreAttempt,
}: {
  attempts: Array<ValidationAdminTargetSession & { target: ValidationAdminTarget }>;
  sessionId: string;
  deletingAttemptKey: string | null;
  scoringAttemptKey: string | null;
  isReadOnly?: boolean;
  onDeleteAttempt?: (sessionId: string, attemptId: string) => void;
  onScoreAttempt?: (sessionId: string, attemptId: string) => void;
}) {
  const [tryIndex, setTryIndex] = useState(0);

  if (attempts.length === 0) {
    return <span className="attempt-empty">-</span>;
  }

  const tries = triesFromAttempts(attempts);
  const activeTryIndex = Math.min(tryIndex, tries.length - 1);
  const activeTry = tries[activeTryIndex];

  return (
    <div className="admin-attempt-cells">
      <div className="try-pills" aria-label="Tries">
        {tries.map((item, index) => (
          <button
            key={item.key}
            type="button"
            className={`try-pill ${tryPassed(item) ? 'passed' : 'failed'}${index === activeTryIndex ? ' active' : ''}`}
            aria-label={`${tryTypeName(item)} try`}
            aria-pressed={index === activeTryIndex}
            onClick={() => setTryIndex(index)}
          >
            <span>{tryTypeAbbreviation(item)}</span>
          </button>
        ))}
      </div>
      {activeTry ? (
        <TryCell
          item={activeTry}
          sessionId={sessionId}
          deletingAttemptKey={deletingAttemptKey}
          scoringAttemptKey={scoringAttemptKey}
          isReadOnly={isReadOnly}
          onDeleteAttempt={onDeleteAttempt}
          onScoreAttempt={onScoreAttempt}
        />
      ) : null}
    </div>
  );
}

function triesFromAttempts(attempts: Array<ValidationAdminTargetSession & { target: ValidationAdminTarget }>): AdminTry[] {
  const sortedAttempts = [...attempts].sort((left, right) =>
    String(left.receivedAt || left.createdAt || '').localeCompare(String(right.receivedAt || right.createdAt || '')),
  );
  const choiceEvents = sortedAttempts.filter((attempt) => attempt.type === 'choice');
  const recordings = sortedAttempts.filter((attempt) => attempt.type !== 'choice');
  const usedChoiceKeys = new Set<string>();

  const tries = recordings.map((recording) => {
    const choice = nearestChoiceForRecording(recording, choiceEvents, usedChoiceKeys);
    if (choice) {
      usedChoiceKeys.add(attemptKey(choice));
    }
    return {
      key: attemptKey(recording),
      scene: recording,
      choice,
      recording,
    };
  });

  for (const choice of choiceEvents) {
    if (usedChoiceKeys.has(attemptKey(choice))) continue;
    tries.push({
      key: attemptKey(choice),
      scene: choice,
      choice,
    });
  }

  return tries.sort((left, right) =>
    String(tryTimestamp(left)).localeCompare(String(tryTimestamp(right))),
  );
}

function nearestChoiceForRecording(
  recording: ValidationAdminTargetSession,
  choiceEvents: ValidationAdminTargetSession[],
  usedChoiceKeys: Set<string>,
): (ValidationAdminTargetSession & { target: ValidationAdminTarget }) | undefined {
  const candidates = choiceEvents.filter((choice) => {
    if (usedChoiceKeys.has(attemptKey(choice))) return false;
    if (choice.lessonId && recording.lessonId && choice.lessonId !== recording.lessonId) return false;
    if (choice.lessonPage && recording.lessonPage && choice.lessonPage !== recording.lessonPage) return false;
    return true;
  });
  return candidates[candidates.length - 1] as (ValidationAdminTargetSession & { target: ValidationAdminTarget }) | undefined;
}

function attemptKey(attempt: ValidationAdminTargetSession): string {
  return attempt.attemptId || attempt.eventId || `${attempt.type ?? 'try'}:${attempt.receivedAt ?? attempt.createdAt ?? ''}`;
}

function tryTimestamp(item: AdminTry): string | undefined {
  return item.recording?.receivedAt || item.choice?.receivedAt || item.scene.createdAt;
}

function tryPassed(item: AdminTry): boolean {
  return item.recording?.scorePassed === true;
}

function tryTypeAbbreviation(item: AdminTry): 'A' | 'AT' | 'T' {
  const typeName = tryTypeName(item);
  if (typeName === 'Anchor') return 'A';
  if (typeName === 'Anchor transfer') return 'AT';
  return 'T';
}

function tryTypeName(item: AdminTry): 'Anchor' | 'Anchor transfer' | 'Transfer' {
  const tryKind = item.scene.tryKind || item.scene.sceneKind || '';
  const tryLabel = item.scene.tryKindLabel || item.scene.sceneKindLabel || '';
  if (tryKind === 'anchor_transfer' || tryLabel.toLowerCase() === 'anchor transfer') {
    return 'Anchor transfer';
  }
  if (tryKind === 'anchor' || tryLabel.toLowerCase() === 'anchor') {
    return 'Anchor';
  }
  return 'Transfer';
}
