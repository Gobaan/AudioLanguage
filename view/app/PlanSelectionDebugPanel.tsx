import { planQueueItems, type PlanLessonMetadata } from './planSelectionDebug';
import type { LessonTab } from './lessonSelection';

type PlanSelectionDebugPanelProps = {
  lessons: PlanLessonMetadata[];
  lessonTabs: LessonTab[];
  currentLessonPage?: string;
  planVersion?: number | null;
  sessionId?: string | null;
};

export function PlanSelectionDebugPanel({
  lessons,
  lessonTabs,
  currentLessonPage,
  planVersion,
  sessionId,
}: PlanSelectionDebugPanelProps) {
  if (lessons.length === 0) {
    return null;
  }

  const items = planQueueItems(lessonTabs, lessons);

  return (
    <aside className="plan-selection-debug" aria-label="Learning engine queue debug">
      <h2>Why these scenes?</h2>
      {planVersion || sessionId ? (
        <p className="plan-selection-debug-meta">
          {planVersion ? `plan v${planVersion}` : null}
          {planVersion && sessionId ? ' · ' : null}
          {sessionId ? `session ${sessionId}` : null}
        </p>
      ) : null}
      <ol>
        {items.map((item) => (
          <li key={`${item.tabId}-${item.targetId}`} className={item.tabId === currentLessonPage ? 'active' : ''}>
            <strong>{item.tabLabel}</strong>
            <span>{item.summary}</span>
            <small>
              target={item.targetId} · purpose={item.planPurpose} · repair={item.repairCategory} · stage=
              {item.stage}
            </small>
          </li>
        ))}
      </ol>
    </aside>
  );
}
