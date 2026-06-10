import type {
  ValidationAdminSession,
  ValidationAdminTarget,
  ValidationAdminTargetSession,
} from '../../api/validation';

export type UserSummary = {
  participantId: string;
  sessionCount: number;
  attemptCount: number;
  rememberedAttemptCount: number;
};

export type Day = ValidationAdminSession & { dayNumber: number };

export type PhraseRow = {
  phrase: string;
  targetId: string;
  attemptsBySession: Record<string, Array<ValidationAdminTargetSession & { target: ValidationAdminTarget }>>;
};
