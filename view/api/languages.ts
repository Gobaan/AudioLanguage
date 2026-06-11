export type LanguageSummary = {
  id: string;
  display_name: string;
  description: string;
  scene_sets: string[];
  sort_order?: number;
};

export async function fetchLanguages(): Promise<LanguageSummary[]> {
  const response = await fetch('/api/languages');
  if (!response.ok) {
    throw new Error(`Failed to load languages: ${response.status}`);
  }

  return response.json() as Promise<LanguageSummary[]>;
}
