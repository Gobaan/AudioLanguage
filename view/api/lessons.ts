import type { LessonListResponse } from '../components/types';

export async function fetchLessons(language: string): Promise<LessonListResponse> {
  const response = await fetch(`/api/languages/${encodeURIComponent(language)}/lessons`);

  if (!response.ok) {
    throw new Error(`Failed to load lessons for ${language}: ${response.status}`);
  }

  return response.json() as Promise<LessonListResponse>;
}

