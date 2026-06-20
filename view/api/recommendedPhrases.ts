export type RecommendedPhrase = {
  id: string;
  phrase: string;
  recommendedAt: string;
  clientIp?: string | null;
  locationFlag?: string | null;
};

export type RecommendedPhraseSummary = {
  count: number;
  index: number;
  phrase: RecommendedPhrase | null;
};

export async function saveRecommendedPhrase(phrase: string): Promise<RecommendedPhrase> {
  const response = await fetch('/api/recommended-phrases', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phrase }),
  });
  if (!response.ok) {
    throw new Error(await recommendedPhraseErrorMessage(response, 'Could not save phrase recommendation'));
  }
  return response.json() as Promise<RecommendedPhrase>;
}

export async function fetchRecommendedPhraseSummary(index = 0): Promise<RecommendedPhraseSummary> {
  const response = await fetch(`/api/admin/recommended-phrases?index=${encodeURIComponent(index)}`);
  if (!response.ok) {
    throw new Error(await recommendedPhraseErrorMessage(response, 'Could not load phrase recommendations'));
  }
  return response.json() as Promise<RecommendedPhraseSummary>;
}

async function recommendedPhraseErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === 'string' && body.detail.length > 0) {
      return `${fallback}: ${body.detail}`;
    }
  } catch {
    // Non-JSON responses still include the status code below.
  }
  return `${fallback}: ${response.status}`;
}
