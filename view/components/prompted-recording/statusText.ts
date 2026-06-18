import type { RecordingState } from './types';

export function statusText(
  state: RecordingState,
  prompt: string,
  playbackPrompt: string,
  blockedReason?: string | null,
): string {
  if (state === 'prompting') return playbackPrompt;
  if (state === 'recording') return prompt;
  if (state === 'captured') return 'Review your recording.';
  if (state === 'submitted') return 'Saved.';
  if (state === 'blocked') return blockedReason || 'Microphone access is needed.';
  return prompt;
}

