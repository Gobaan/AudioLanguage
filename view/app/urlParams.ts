export function participantFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get('participant');
}

export function isLocalHost(): boolean {
  return ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
}
