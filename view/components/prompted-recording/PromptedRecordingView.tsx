import { AudioButton } from '../AudioButton';
import { RecordingCountdownBar } from '../RecordingCountdownBar';
import type { CapturedRecording } from '../types';
import { statusText } from './statusText';
import type { RecordingState } from './types';

type PromptedRecordingViewProps = {
  state: RecordingState;
  prompt: string;
  playbackPrompt: string;
  blockedReason?: string | null;
  startMode: 'auto' | 'manual';
  startLabel: string;
  recordingMs: number;
  isSpeechActive: boolean;
  audioError?: string | null;
  modelAudioError?: string | null;
  recordingUrl?: string | null;
  canReplayModel: boolean;
  modelReplayNormalLabel: string;
  modelReplaySlowLabel?: string;
  isModelPlaying: boolean;
  pendingCapture: CapturedRecording | null;
  reRecordLabel: string;
  nextLabel: string;
  onStart: () => void;
  onReplayModelNormal: () => void;
  onReplayModelSlow: () => void;
  onReRecord: () => void;
  onConfirm: () => void;
};

export function PromptedRecordingView(props: PromptedRecordingViewProps) {
  const visibleError = props.audioError || props.modelAudioError;
  return (
    <section className={`prompted-recording ${props.state}`} aria-live="polite">
      <p>{statusText(props.state, props.prompt, props.playbackPrompt, props.blockedReason)}</p>
      {props.state === 'ready' && props.startMode === 'manual' ? <button type="button" className="record-button" onClick={props.onStart}>{props.startLabel}</button> : null}
      {props.state === 'recording' ? <RecordingCountdownBar durationMs={props.recordingMs} isPaused={props.isSpeechActive} /> : null}
      {visibleError ? <p className="audio-error" role="alert">{visibleError}</p> : null}
      {props.recordingUrl ? <audio className="recording-playback" controls src={props.recordingUrl} /> : null}
      {props.state === 'captured' && props.canReplayModel ? (
        <div className="recording-replay-actions">
          {props.modelReplaySlowLabel ? (
            <AudioButton
              label={props.modelReplaySlowLabel}
              isPlaying={props.isModelPlaying}
              disabled={props.isModelPlaying}
              onPlay={props.onReplayModelSlow}
              text={{ playLabel: props.modelReplaySlowLabel, playingLabel: 'Playing…' }}
            />
          ) : null}
          <AudioButton
            label={props.modelReplayNormalLabel}
            isPlaying={props.isModelPlaying}
            disabled={props.isModelPlaying}
            onPlay={props.onReplayModelNormal}
            text={{ playLabel: props.modelReplayNormalLabel, playingLabel: 'Playing…' }}
          />
        </div>
      ) : null}
      {props.state === 'captured' && props.pendingCapture ? (
        <div className="recording-review-actions">
          <button type="button" className="record-button record-button-secondary" onClick={props.onReRecord}>{props.reRecordLabel}</button>
          <button type="button" className="record-button" onClick={props.onConfirm}>{props.nextLabel}</button>
        </div>
      ) : null}
    </section>
  );
}

