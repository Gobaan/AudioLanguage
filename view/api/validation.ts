export type ValidationSession = {
  sessionId: string;
};

export type ValidationParticipant = {
  participantId: string;
};

export type ScorecardAttempt = {
  attemptId: string;
  lessonId?: string;
  lessonPage?: string;
  stepId?: string;
  targetId?: string;
  expectedText?: string;
  expectedTransliteration?: string;
  recordingPath?: string;
  recordingDurationMs?: number;
  byteCount?: number;
  mimeType?: string;
  buildPromptText?: string;
  receivedAt?: string;
  aiScore?: {
    status?: string;
    result?: {
      transcript_romanized?: string;
      communication?: {
        status?: string;
        close_enough?: boolean;
        confidence?: number;
      };
    };
    error?: string;
  } | null;
};

export type ScorecardTarget = {
  targetId: string;
  expectedText?: string;
  expectedTransliteration?: string;
  targetAudioUrl?: string;
  reviewStatus: string;
  attempts: ScorecardAttempt[];
};

export type ValidationScorecard = {
  session: {
    sessionId: string;
    participantId?: string;
    language?: string;
    sceneSet?: string;
    createdAt?: string;
  };
  eventCount: number;
  attemptCount: number;
  targets: ScorecardTarget[];
};

export type ValidationAdminSession = {
  sessionId: string;
  participantId?: string;
  language: string;
  sceneSet: string;
  lessonPage?: string;
  createdAt?: string;
  eventCount: number;
  attemptCount: number;
  scoredAttemptCount: number;
  rememberedAttemptCount: number;
};

export type ValidationAdminTargetSession = {
  sessionId: string;
  participantId?: string;
  lessonPage?: string;
  stepId?: string;
  attemptId?: string;
  receivedAt?: string;
  scoreStatus: string;
};

export type ValidationAdminTarget = {
  language: string;
  sceneSet: string;
  targetId: string;
  expectedText?: string;
  expectedTransliteration?: string;
  targetAudioUrl?: string | null;
  attemptCount: number;
  scoredAttemptCount: number;
  rememberedAttemptCount: number;
  sessions: ValidationAdminTargetSession[];
};

export type ValidationAdminSummary = {
  sessionCount: number;
  attemptCount: number;
  scoredAttemptCount: number;
  rememberedAttemptCount: number;
  sessions: ValidationAdminSession[];
  targets: ValidationAdminTarget[];
};

export type ValidationEvent = {
  type: string;
  eventId?: string;
  participantId?: string;
  language?: string;
  sceneSet?: string;
  lessonId?: string;
  lessonPage?: string;
  stepId?: string;
  stepIndex?: number;
  frameId?: string | null;
  choiceId?: string;
  isCorrect?: boolean;
  direction?: string;
  targetId?: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
};

export type AttemptMetadata = {
  attemptId: string;
  participantId?: string;
  language: string;
  sceneSet: string;
  lessonId: string;
  lessonPage: string;
  stepId: string;
  targetId: string;
  expectedText: string;
  expectedTransliteration: string;
  targetAudioUrl?: string | null;
  recordingDurationMs?: number;
  byteCount?: number;
  mimeType?: string;
  buildPromptId?: string;
  buildPromptText?: string;
};

export async function startValidationSession(input: {
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
  await fetch(`/api/validation/sessions/${encodeURIComponent(sessionId)}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      eventId: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      ...event,
    }),
  });
}

export async function uploadValidationAttempt(
  sessionId: string,
  blob: Blob,
  metadata: AttemptMetadata,
): Promise<void> {
  const formData = new FormData();
  formData.append('metadata', JSON.stringify(metadata));
  formData.append('file', blob, `${metadata.attemptId}.webm`);
  await fetch(`/api/validation/sessions/${encodeURIComponent(sessionId)}/attempts`, {
    method: 'POST',
    body: formData,
  });
}

export async function fetchValidationScorecard(sessionId: string, score = false): Promise<ValidationScorecard> {
  const query = score ? '?score=true' : '';
  const response = await fetch(`/api/validation/sessions/${encodeURIComponent(sessionId)}/scorecard${query}`);
  if (!response.ok) {
    throw new Error(`Failed to load validation scorecard: ${response.status}`);
  }
  return response.json() as Promise<ValidationScorecard>;
}

export async function fetchValidationAdminSummary(): Promise<ValidationAdminSummary> {
  const response = await fetch('/api/validation/admin/summary');
  if (!response.ok) {
    throw new Error(`Failed to load validation admin summary: ${response.status}`);
  }
  return response.json() as Promise<ValidationAdminSummary>;
}

export async function deleteValidationSession(sessionId: string): Promise<void> {
  const response = await fetch(`/api/validation/sessions/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete validation session: ${response.status}`);
  }
}

export function validationAttemptAudioUrl(sessionId: string, attemptId: string): string {
  return `/api/validation/sessions/${encodeURIComponent(sessionId)}/attempts/${encodeURIComponent(attemptId)}/audio`;
}
