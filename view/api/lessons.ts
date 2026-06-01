import type { LessonListResponse } from '../components/types';

export async function fetchLessons(language: string, lesson?: string): Promise<LessonListResponse> {
  const params = new URLSearchParams();
  if (lesson) {
    params.set('lesson', lesson);
  }
  const query = params.size ? `?${params.toString()}` : '';
  const response = await fetch(`/api/languages/${encodeURIComponent(language)}/lessons${query}`);

  if (!response.ok) {
    throw new Error(`Failed to load lessons for ${language}: ${response.status}`);
  }

  return response.json() as Promise<LessonListResponse>;
}
