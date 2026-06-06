import { useEffect, useMemo, useState } from 'react';
import {
  deleteValidationSession,
  fetchValidationAdminSummary,
  type ValidationAdminSummary,
  type ValidationAdminSession,
  type ValidationAdminTarget,
} from '../api/validation';

type LoadState = 'loading' | 'ready' | 'error';
type SelectedPair = {
  participantId: string;
  language: string;
};

export function AdminValidationApp() {
  const [summary, setSummary] = useState<ValidationAdminSummary | null>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [selectedPair, setSelectedPair] = useState<SelectedPair | null>(null);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  useEffect(() => {
    loadSummary();
  }, []);

  function loadSummary() {
    setLoadState('loading');
    fetchValidationAdminSummary()
      .then((nextSummary) => {
        setSummary(nextSummary);
        setLoadState('ready');
      })
      .catch(() => {
        setSummary(null);
        setLoadState('error');
      });
  }

  if (loadState === 'loading') {
    return <p className="admin-status">Loading validation summary.</p>;
  }

  if (loadState === 'error' || !summary) {
    return (
      <section className="validation-admin">
        <AdminHeader onRefresh={loadSummary} />
        <p className="admin-status">Validation summary is unavailable.</p>
      </section>
    );
  }

  return (
    <section className="validation-admin" aria-label="Validation admin dashboard">
      <AdminHeader onRefresh={loadSummary} />
      <SummaryStats summary={summary} />
      <LearnerLanguagePairs
        summary={summary}
        selectedPair={selectedPair}
        onSelectPair={setSelectedPair}
      />
      {selectedPair ? (
        <PairProgress
          summary={summary}
          pair={selectedPair}
          deletingSessionId={deletingSessionId}
          onDeleteSession={deleteSession}
        />
      ) : null}
      <TargetTable targets={summary.targets} />
      <RecentSessions summary={summary} />
    </section>
  );

  function deleteSession(sessionId: string) {
    if (!window.confirm(`Delete session ${sessionId}?`)) return;

    setDeletingSessionId(sessionId);
    deleteValidationSession(sessionId)
      .then(() => {
        loadSummary();
      })
      .finally(() => {
        setDeletingSessionId(null);
      });
  }
}

function AdminHeader({ onRefresh }: { onRefresh: () => void }) {
  return (
    <header className="admin-header">
      <div>
        <span>Experiment dashboard</span>
        <h1>Validation Admin</h1>
      </div>
      <nav className="admin-actions" aria-label="Admin controls">
        <a href="/">Lesson app</a>
        <button type="button" onClick={onRefresh}>
          Refresh
        </button>
      </nav>
    </header>
  );
}

function SummaryStats({ summary }: { summary: ValidationAdminSummary }) {
  return (
    <dl className="admin-summary">
      <SummaryStat label="Sessions" value={summary.sessionCount} />
      <SummaryStat label="Attempts" value={summary.attemptCount} />
      <SummaryStat label="Scored" value={summary.scoredAttemptCount} />
      <SummaryStat label="Remembered" value={summary.rememberedAttemptCount} />
    </dl>
  );
}

function SummaryStat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function LearnerLanguagePairs({
  summary,
  selectedPair,
  onSelectPair,
}: {
  summary: ValidationAdminSummary;
  selectedPair: SelectedPair | null;
  onSelectPair: (pair: SelectedPair) => void;
}) {
  const pairs = useMemo(() => learnerLanguagePairs(summary.sessions), [summary.sessions]);

  return (
    <section className="admin-section" aria-label="Learner language pairs">
      <header>
        <h2>Learners</h2>
      </header>
      {pairs.length === 0 ? (
        <p className="admin-status">No learners have connected yet.</p>
      ) : (
        <div className="admin-pair-list">
          {pairs.map((pair) => {
            const isSelected =
              selectedPair?.participantId === pair.participantId && selectedPair?.language === pair.language;
            return (
              <button
                key={`${pair.participantId}:${pair.language}`}
                type="button"
                className={isSelected ? 'active' : ''}
                onClick={() => onSelectPair({ participantId: pair.participantId, language: pair.language })}
              >
                <strong>{pair.participantId}</strong>
                <span>{pair.language}</span>
                <em>{pair.rememberedAttemptCount} / {pair.scoredAttemptCount || pair.attemptCount}</em>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}

function PairProgress({
  summary,
  pair,
  deletingSessionId,
  onDeleteSession,
}: {
  summary: ValidationAdminSummary;
  pair: SelectedPair;
  deletingSessionId: string | null;
  onDeleteSession: (sessionId: string) => void;
}) {
  const sessions = useMemo(
    () =>
      summary.sessions
        .filter((session) => session.participantId === pair.participantId && session.language === pair.language)
        .sort((left, right) => String(left.createdAt || '').localeCompare(String(right.createdAt || ''))),
    [summary.sessions, pair],
  );

  return (
    <section className="admin-section" aria-label="Learner session progress">
      <header>
        <h2>{pair.participantId} / {pair.language}</h2>
      </header>
      <div className="admin-progress-days">
        {sessions.map((session) => (
          <article className="admin-progress-day" key={session.sessionId}>
            <header>
              <div>
                <span>{sceneSetLabel(session.sceneSet)}</span>
                <h3>{session.lessonPage || 'Session'}</h3>
              </div>
              <button
                type="button"
                className="danger"
                disabled={deletingSessionId === session.sessionId}
                onClick={() => onDeleteSession(session.sessionId)}
              >
                {deletingSessionId === session.sessionId ? 'Deleting' : 'Delete'}
              </button>
            </header>
            <dl>
              <div>
                <dt>Attempts</dt>
                <dd>{session.attemptCount}</dd>
              </div>
              <div>
                <dt>Scored</dt>
                <dd>{session.scoredAttemptCount}</dd>
              </div>
              <div>
                <dt>Remembered</dt>
                <dd>{session.rememberedAttemptCount}</dd>
              </div>
            </dl>
            <SessionTargets summary={summary} session={session} />
          </article>
        ))}
      </div>
    </section>
  );
}

function SessionTargets({ summary, session }: { summary: ValidationAdminSummary; session: ValidationAdminSession }) {
  const targetSessions = summary.targets.flatMap((target) =>
    target.sessions
      .filter((targetSession) => targetSession.sessionId === session.sessionId)
      .map((targetSession) => ({
        target,
        targetSession,
      })),
  );

  if (targetSessions.length === 0) {
    return <p className="admin-status">No recordings in this session yet.</p>;
  }

  return (
    <ul className="admin-progress-targets">
      {targetSessions.map(({ target, targetSession }) => (
        <li key={`${targetSession.sessionId}:${targetSession.attemptId}`}>
          <span>{target.expectedTransliteration || target.expectedText || target.targetId}</span>
          <strong>{targetSession.scoreStatus}</strong>
        </li>
      ))}
    </ul>
  );
}

function TargetTable({ targets }: { targets: ValidationAdminTarget[] }) {
  const sortedTargets = useMemo(
    () =>
      [...targets].sort((left, right) =>
        [left.language, left.sceneSet, left.targetId].join(':').localeCompare(
          [right.language, right.sceneSet, right.targetId].join(':'),
        ),
      ),
    [targets],
  );

  return (
    <section className="admin-section" aria-label="Target retention summary">
      <header>
        <h2>Targets</h2>
      </header>
      {sortedTargets.length === 0 ? (
        <p className="admin-status">No recordings have been saved yet.</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Language</th>
                <th>Day type</th>
                <th>Target</th>
                <th>Remembered</th>
                <th>Attempts</th>
                <th>Audio</th>
              </tr>
            </thead>
            <tbody>
              {sortedTargets.map((target) => (
                <tr key={`${target.language}:${target.sceneSet}:${target.targetId}`}>
                  <td>{target.language}</td>
                  <td>{sceneSetLabel(target.sceneSet)}</td>
                  <td>
                    <strong>{target.expectedTransliteration || target.expectedText || target.targetId}</strong>
                    <span>{target.targetId}</span>
                  </td>
                  <td>{target.rememberedAttemptCount} / {target.scoredAttemptCount || target.attemptCount}</td>
                  <td>{target.attemptCount}</td>
                  <td>{target.targetAudioUrl ? <audio controls src={target.targetAudioUrl} /> : null}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function RecentSessions({ summary }: { summary: ValidationAdminSummary }) {
  const sessions = useMemo(
    () =>
      [...summary.sessions].sort((left, right) =>
        String(right.createdAt || '').localeCompare(String(left.createdAt || '')),
      ),
    [summary.sessions],
  );

  return (
    <section className="admin-section" aria-label="Recent validation sessions">
      <header>
        <h2>Recent Sessions</h2>
      </header>
      <div className="admin-session-list">
        {sessions.map((session) => (
          <article className="admin-session" key={session.sessionId}>
            <div>
              <strong>{session.participantId || 'local'}</strong>
              <span>{session.sessionId}</span>
            </div>
            <dl>
              <div>
                <dt>Language</dt>
                <dd>{session.language}</dd>
              </div>
              <div>
                <dt>Day type</dt>
                <dd>{sceneSetLabel(session.sceneSet)}</dd>
              </div>
              <div>
                <dt>Remembered</dt>
                <dd>{session.rememberedAttemptCount} / {session.scoredAttemptCount || session.attemptCount}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

function sceneSetLabel(sceneSet: string): string {
  if (sceneSet === 'mvp') return 'Day 1';
  if (sceneSet === 'delayed' || sceneSet === 'delayed_review') return 'Day 2';
  if (sceneSet === 'transfer') return 'Transfer';
  return sceneSet;
}

function learnerLanguagePairs(sessions: ValidationAdminSession[]) {
  const pairs: Record<
    string,
    {
      participantId: string;
      language: string;
      attemptCount: number;
      scoredAttemptCount: number;
      rememberedAttemptCount: number;
    }
  > = {};

  for (const session of sessions) {
    const participantId = session.participantId || 'local';
    const key = `${participantId}:${session.language}`;
    const pair = pairs[key] ?? {
      participantId,
      language: session.language,
      attemptCount: 0,
      scoredAttemptCount: 0,
      rememberedAttemptCount: 0,
    };
    pair.attemptCount += session.attemptCount;
    pair.scoredAttemptCount += session.scoredAttemptCount;
    pair.rememberedAttemptCount += session.rememberedAttemptCount;
    pairs[key] = pair;
  }

  return Object.values(pairs).sort((left, right) =>
    [left.participantId, left.language].join(':').localeCompare([right.participantId, right.language].join(':')),
  );
}
