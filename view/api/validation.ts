import { requireOk } from './http';
import type {
  AttemptMetadata,
  ValidationAdminSummary,
  ValidationEvent,
  ValidationParticipant,
  ValidationScorecard,
  ValidationSession,
} from './validationTypes';

export type {
  AttemptMetadata,
  ScorecardAttempt,
  ScorecardTarget,
  ValidationAdminSession,
  ValidationAdminSummary,
  ValidationAdminTarget,
  ValidationAdminTargetSession,
  ValidationEvent,
  ValidationParticipant,
  ValidationScorecard,
  ValidationSession,
} from './validationTypes';

export async function startValidationSession(input: {
  sessionId?: string;
  language: string;
  sceneSet: string;
  lessonPage: string;
  participantId?: string | null;
}): Promise<ValidationSession> {
  const response = await fetch('/api/validation/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error(`Failed to start validation session: ${response.status}`);
  }
  return response.json() as Promise<ValidationSession>;
}

export async function fetchSuggestedParticipantName(): Promise<ValidationParticipant> {
  const response = await fetch('/api/validation/participant-name');
  if (!response.ok) {
    throw new Error(`Failed to load participant name: ${response.status}`);
  }
  return response.json() as Promise<ValidationParticipant>;
}

export async function logValidationEvent(sessionId: string, event: ValidationEvent): Promise<void> {
  const response = await fetch(`/api/validation/sessions/${encodeURIComponent(sessionId)}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      eventId: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      ...event,
    }),
  });
  await requireOk(response, 'Failed to log validation event');
}

export async function uploadValidationAttempt(
  sessionId: string,
  blob: Blob,
  metadata: AttemptMetadata,
): Promise<void> {
  const formData = new FormData();
  formData.append('metadata', JSON.stringify(metadata));
  formData.append('file', blob, `${metadata.attemptId}.webm`);
  const response = await fetch(`/api/validation/sessions/${encodeURIComponent(sessionId)}/attempts`, {
    method: 'POST',
    body: formData,
  });
  await requireOk(response, 'Failed to upload validation attempt');
}

export async function fetchValidationScorecard(sessionId: string): Promise<ValidationScorecard> {
  const response = await fetch(`/api/validation/sessions/${encodeURIComponent(sessionId)}/scorecard`);
  if (!response.ok) {
    throw new Error(`Failed to load validation scorecard: ${response.status}`);
  }
  return response.json() as Promise<ValidationScorecard>;
}

export async function fetchScoredValidationScorecard(sessionId: string): Promise<ValidationScorecard> {
  const initial = await fetchValidationScorecard(sessionId);
  const attemptIds = [
    ...new Set(
      initial.targets.flatMap((target) =>
        target.attempts
          .filter((attempt) => !attempt.aiScore || attempt.aiScore.status !== 'scored')
          .map((attempt) => attempt.attemptId),
      ),
    ),
  ];

  if (attemptIds.length === 0) {
    return initial;
  }

  await Promise.all(attemptIds.map((attemptId) => scoreValidationAttempt(sessionId, attemptId)));
  return fetchValidationScorecard(sessionId);
}

export async function fetchValidationAdminSummary(): Promise<ValidationAdminSummary> {
  const response = await fetch('/api/validation/admin/summary');
  if (!response.ok) {
    throw new Error(`Failed to load validation admin summary: ${response.status}`);
  }
  return response.json() as Promise<ValidationAdminSummary>;
}

export async function deleteValidationAttempt(sessionId: string, attemptId: string): Promise<void> {
  const response = await fetch(
    `/api/validation/sessions/${encodeURIComponent(sessionId)}/attempts/${encodeURIComponent(attemptId)}`,
    {
      method: 'DELETE',
    },
  );
  if (!response.ok) {
    throw new Error(`Failed to delete validation attempt: ${response.status}`);
  }
}

export async function deleteValidationUser(participantId: string): Promise<void> {
  const response = await fetch(`/api/validation/users/${encodeURIComponent(participantId)}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete validation user: ${response.status}`);
  }
}

export async function clearLocalValidationSessions(): Promise<void> {
  const response = await fetch('/api/validation/local/sessions', {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to clear local validation sessions: ${response.status}`);
  }
}

export async function scoreValidationAttempt(sessionId: string, attemptId: string): Promise<void> {
  const response = await fetch(
    `/api/validation/sessions/${encodeURIComponent(sessionId)}/attempts/${encodeURIComponent(attemptId)}/score`,
    {
      method: 'POST',
    },
  );
  if (!response.ok) {
    throw new Error(`Failed to score validation attempt: ${response.status}`);
  }
}

export function validationAttemptAudioUrl(sessionId: string, attemptId: string): string {
  return `/api/validation/sessions/${encodeURIComponent(sessionId)}/attempts/${encodeURIComponent(attemptId)}/audio`;
}
