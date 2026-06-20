import type { LessonTab } from './lessonSelection';

const PURPOSE_LABELS: Record<string, string> = {
  meaning_repair: 'Repair after wrong meaning choice',
  recall_repair: 'Repair after failed anchor production',
  transfer_repair: 'Repair after failed transfer',
  memory_repair: 'Repair after failed delayed review',
  transfer_practice: 'Due spaced transfer/review practice',
  same_day_anchor_recall: 'Same-day anchor recall',
  new: 'New i+1 anchor',
};

const STAGE_LABELS: Record<string, string> = {
  guided_scene_production: 'anchor',
  same_day_anchor_recall: 'anchor recall',
  same_day_transfer: 'transfer',
  delayed_review: 'delayed review',
};

export type PlanLessonMetadata = {
  targetId?: string;
  target: { id: string };
  planPurpose?: string;
  repairCategory?: string;
  stage?: string;
  lessonUnitId?: string;
};

export function planSelectionSummary(lesson: PlanLessonMetadata): string {
  const purpose = lesson.planPurpose ?? 'unknown';
  const reason = PURPOSE_LABELS[purpose] ?? purpose;
  const stage = lesson.stage ? (STAGE_LABELS[lesson.stage] ?? lesson.stage) : 'unknown stage';
  return `${reason} · ${stage} scene`;
}

export type PlanQueueItem = {
  tabId: string;
  tabLabel: string;
  targetId: string;
  planPurpose: string;
  repairCategory: string;
  stage: string;
  lessonUnitId: string;
  summary: string;
};

export function planQueueItems(lessonTabs: LessonTab[], lessons: PlanLessonMetadata[]): PlanQueueItem[] {
  return lessons.map((lesson, index) => {
    const tab = lessonTabs[index];
    return {
      tabId: tab?.id ?? `scene-${index + 1}`,
      tabLabel: tab?.label ?? tab?.id ?? `Scene ${index + 1}`,
      targetId: lesson.targetId ?? lesson.target.id,
      planPurpose: lesson.planPurpose ?? '—',
      repairCategory: lesson.repairCategory ?? '—',
      stage: lesson.stage ?? '—',
      lessonUnitId: lesson.lessonUnitId ?? '—',
      summary: planSelectionSummary(lesson),
    };
  });
}
