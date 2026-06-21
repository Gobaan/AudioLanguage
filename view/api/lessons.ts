import type { LearningPlanResponse, Lesson, LessonListResponse } from '../components/types';
import type { SpeechBubbleOverridePayload } from '../app/DebugSpeechBubbleEditorPage';

export type RelearnTargetResponse = {
  targetId: string;
  language: string;
  display_name?: string;
  lesson_tabs?: Array<{
    id: string;
    label: string;
  }>;
  lessons: Lesson[];
};

export async function fetchLessons(
  language: string,
  lesson?: string | null,
  sceneSet?: string | null,
  orderSeed?: string | null,
): Promise<LessonListResponse> {
  const params = new URLSearchParams();
  if (lesson) {
    params.set('lesson', lesson);
  }
  if (sceneSet && sceneSet !== 'mvp') {
    params.set('scene_set', sceneSet);
  }
  if (orderSeed) {
    params.set('order_seed', orderSeed);
  }
  const query = params.size ? `?${params.toString()}` : '';
  const response = await fetch(`/api/languages/${encodeURIComponent(language)}/lessons${query}`);

  if (!response.ok) {
    throw new Error(`Failed to load lessons for ${language}: ${response.status}`);
  }

  return response.json() as Promise<LessonListResponse>;
}

export async function fetchLearningPlan(
  language: string,
  sceneSet?: string | null,
  orderSeed?: string | null,
  participantId?: string | null,
): Promise<LearningPlanResponse> {
  const params = new URLSearchParams();
  params.set('language', language);
  if (sceneSet && sceneSet !== 'mvp') {
    params.set('scene_set', sceneSet);
  }
  if (orderSeed) {
    params.set('order_seed', orderSeed);
  }
  if (participantId) {
    params.set('participant_id', participantId);
  }

  const response = await fetch(`/api/learning-engine/lessons?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to load learning plan for ${language}: ${response.status}`);
  }

  return response.json() as Promise<LearningPlanResponse>;
}

export async function relearnTarget(input: {
  language: string;
  participantId: string;
  targetId: string;
}): Promise<RelearnTargetResponse> {
  const response = await fetch('/api/learning-engine/relearn-target', {
    body: JSON.stringify(input),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to relearn target ${input.targetId}: ${response.status}`);
  }

  return response.json() as Promise<RelearnTargetResponse>;
}

export async function fetchSpeechBubbleOverrides(): Promise<SpeechBubbleOverridePayload> {
  const response = await fetch('/api/debug/speech-bubble-overrides');

  if (!response.ok) {
    throw new Error(`Failed to load speech bubble overrides: ${response.status}`);
  }

  return response.json() as Promise<SpeechBubbleOverridePayload>;
}

export async function saveSpeechBubbleOverrides(
  payload: SpeechBubbleOverridePayload,
): Promise<{ saved: boolean; path: string; frames: number }> {
  const response = await fetch('/api/debug/speech-bubble-overrides', {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to save speech bubble overrides: ${response.status}`);
  }

  return response.json() as Promise<{ saved: boolean; path: string; frames: number }>;
}
