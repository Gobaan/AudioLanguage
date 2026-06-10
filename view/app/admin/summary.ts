import type { ValidationAdminSession, ValidationAdminSummary, ValidationAdminTarget } from '../../api/validation';
import type { Day, PhraseRow, UserSummary } from './types';

export function usersFromSummary(summary: ValidationAdminSummary): UserSummary[] {
  const users: Record<string, UserSummary> = {};
  for (const session of summary.sessions) {
    const participantId = session.participantId || 'local';
    const user = users[participantId] ?? {
      participantId,
      sessionCount: 0,
      attemptCount: 0,
      rememberedAttemptCount: 0,
    };
    user.sessionCount += 1;
    user.attemptCount += session.attemptCount;
    user.rememberedAttemptCount += session.rememberedAttemptCount;
    users[participantId] = user;
  }

  return Object.values(users).sort((left, right) => left.participantId.localeCompare(right.participantId));
}

export function daysForUser(sessions: ValidationAdminSession[], participantId: string): Day[] {
  return sessions
    .filter((session) => (session.participantId || 'local') === participantId)
    .sort((left, right) => String(left.createdAt || '').localeCompare(String(right.createdAt || '')))
    .map((session, index) => ({ ...session, dayNumber: index + 1 }));
}

export function phrasesForUser(targets: ValidationAdminTarget[], participantId: string): PhraseRow[] {
  const rows: Record<string, PhraseRow> = {};

  for (const target of targets) {
    for (const attempt of target.sessions) {
      if ((attempt.participantId || 'local') !== participantId) continue;

      const phrase = target.expectedTransliteration || target.expectedText || target.targetId;
      const row = rows[target.targetId] ?? {
        phrase,
        targetId: target.targetId,
        attemptsBySession: {},
      };
      const attempts = row.attemptsBySession[attempt.sessionId] ?? [];
      attempts.push({ ...attempt, target });
      row.attemptsBySession[attempt.sessionId] = attempts.sort((left, right) =>
        String(left.receivedAt || '').localeCompare(String(right.receivedAt || '')),
      );
      rows[target.targetId] = row;
    }
  }

  return Object.values(rows).sort((left, right) => left.phrase.localeCompare(right.phrase));
}
