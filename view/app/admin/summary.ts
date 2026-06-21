import type { ValidationAdminSession, ValidationAdminSummary, ValidationAdminTarget } from '../../api/validation';
import type { Day, PhraseRow, UserSummary } from './types';

export function usersFromSummary(summary: ValidationAdminSummary): UserSummary[] {
  const users: Record<string, UserSummary & { latestSeenAt: string }> = {};
  for (const session of summary.sessions) {
    const participantId = session.participantId || 'local';
    const language = session.language || 'unknown';
    const userKey = adminUserKey(participantId, language);
    const createdAt = String(session.createdAt || '');
    const user = users[userKey] ?? {
      userKey,
      participantId,
      displayName: `${participantId}-${language}`,
      language,
      locationFlag: session.locationFlag || undefined,
      clientIp: session.clientIp || undefined,
      sessionCount: 0,
      attemptCount: 0,
      rememberedAttemptCount: 0,
      latestSeenAt: createdAt,
    };
    user.sessionCount += 1;
    user.attemptCount += session.attemptCount;
    user.rememberedAttemptCount += session.rememberedAttemptCount;
    if (createdAt >= user.latestSeenAt) {
      user.latestSeenAt = createdAt;
      user.locationFlag = session.locationFlag || undefined;
      user.clientIp = session.clientIp || undefined;
    }
    users[userKey] = user;
  }

  return Object.values(users)
    .map(({ latestSeenAt: _latestSeenAt, ...rest }) => rest)
    .sort((left, right) => left.displayName.localeCompare(right.displayName));
}

export function daysForUser(sessions: ValidationAdminSession[], participantId: string, language?: string): Day[] {
  return sessions
    .filter((session) => sessionBelongsToUser(session, participantId, language))
    .sort((left, right) => String(left.createdAt || '').localeCompare(String(right.createdAt || '')))
    .map((session, index) => ({ ...session, dayNumber: index + 1 }));
}

export function phrasesForUser(targets: ValidationAdminTarget[], participantId: string, language?: string): PhraseRow[] {
  const rows: Record<string, PhraseRow> = {};

  for (const target of targets) {
    for (const attempt of target.sessions) {
      if (!targetAttemptBelongsToUser(target, attempt.participantId || 'local', participantId, language)) continue;

      const phrase = target.expectedTransliteration || target.expectedText || target.targetId;
      const phraseKey = `${target.language}:${target.targetId}`;
      const row = rows[phraseKey] ?? {
        phrase,
        phraseKey,
        targetId: target.targetId,
        sceneKind: target.sceneKind,
        sceneKindLabel: target.sceneKindLabel,
        attemptsBySession: {},
      };
      const attempts = row.attemptsBySession[attempt.sessionId] ?? [];
      attempts.push({ ...attempt, target });
      row.attemptsBySession[attempt.sessionId] = attempts.sort((left, right) =>
        String(left.receivedAt || '').localeCompare(String(right.receivedAt || '')),
      );
      rows[phraseKey] = row;
    }
  }

  return Object.values(rows).sort((left, right) => {
    return left.phrase.localeCompare(right.phrase);
  });
}

export function adminUserKey(participantId: string, language: string): string {
  return `${participantId}::${language}`;
}

function sessionBelongsToUser(session: ValidationAdminSession, participantId: string, language?: string): boolean {
  if ((session.participantId || 'local') !== participantId) return false;
  if (!language) return true;
  return session.language === language;
}

function targetAttemptBelongsToUser(
  target: ValidationAdminTarget,
  attemptParticipantId: string,
  participantId: string,
  language?: string,
): boolean {
  if (attemptParticipantId !== participantId) return false;
  if (!language) return true;
  return target.language === language;
}
