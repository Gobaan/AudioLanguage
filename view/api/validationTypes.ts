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
  type?: 'recording' | 'choice';
  sessionId: string;
  participantId?: string;
  lessonPage?: string;
  stepId?: string;
  eventId?: string;
  choiceId?: string;
  choiceCorrect?: boolean;
  attemptId?: string;
  receivedAt?: string;
  createdAt?: string;
  scorePassed?: boolean;
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
