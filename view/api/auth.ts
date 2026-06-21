export type GoogleAuthConfig = {
  enabled: boolean;
  clientId: string | null;
};

export type GoogleLinkResponse = {
  participantId: string;
  provider: 'google';
  email?: string | null;
  name?: string | null;
  mergedTargetCount: number;
};

export async function fetchGoogleAuthConfig(): Promise<GoogleAuthConfig> {
  const response = await fetch('/api/auth/google/config');
  if (!response.ok) {
    throw new Error(`Failed to load Google sign-in config: ${response.status}`);
  }
  return response.json() as Promise<GoogleAuthConfig>;
}

export async function linkGoogleAccount(input: {
  credential: string;
  localParticipantId: string;
}): Promise<GoogleLinkResponse> {
  const response = await fetch('/api/auth/google/link', {
    body: JSON.stringify(input),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to link Google account: ${response.status}`);
  }

  return response.json() as Promise<GoogleLinkResponse>;
}
