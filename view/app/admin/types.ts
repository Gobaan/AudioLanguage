import type {
  ValidationAdminSession,
  ValidationAdminTarget,
  ValidationAdminTargetSession,
  ValidationSceneKind,
} from '../../api/validation';

export type UserSummary = {
  userKey: string;
  participantId: string;
  displayName: string;
  language: string;
  locationFlag?: string;
  clientIp?: string;
  sessionCount: number;
  attemptCount: number;
  rememberedAttemptCount: number;
};

export type Day = ValidationAdminSession & { dayNumber: number };

export type PhraseRow = {
  phrase: string;
  phraseKey: string;
  targetId: string;
  sceneKind: ValidationSceneKind;
  sceneKindLabel: string;
  attemptsBySession: Record<string, Array<ValidationAdminTargetSession & { target: ValidationAdminTarget }>>;
};
