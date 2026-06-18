import type { CapturedRecording } from '../types';

export type RecordingState = 'ready' | 'prompting' | 'recording' | 'captured' | 'submitted' | 'blocked';

export type PromptedRecordingProps = {
  audioUrl?: string | null;
  audioText?: string | null;
  prompt?: string;
  playbackPrompt?: string;
  recordingMs?: number;
  startMode?: 'auto' | 'manual';
  startLabel?: string;
  nextLabel?: string;
  reRecordLabel?: string;
  modelReplayLabel?: string;
  modelReplayNormalLabel?: string;
  modelReplaySlowLabel?: string;
  autoConfirmCapture?: boolean;
  onListenComplete?: () => void;
  onRecording?: () => void;
  onCaptured?: (recording: CapturedRecording) => void;
  onNext?: () => void;
};

