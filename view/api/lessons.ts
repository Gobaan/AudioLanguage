import type { LearningPlanResponse, LessonListResponse } from '../components/types';

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
