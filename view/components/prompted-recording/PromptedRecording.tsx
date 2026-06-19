import { useMemo } from 'react';

import type { PromptedRecordingProps } from './types';
import { PromptedRecordingView } from './PromptedRecordingView';
import { usePromptedRecordingController } from './usePromptedRecordingController';

export function PromptedRecording(props: PromptedRecordingProps) {
  const controller = usePromptedRecordingController(props);
  const modelReplayNormalLabel = props.modelReplayNormalLabel ?? props.modelReplayLabel ?? '🔊 Normal speed';
  const modelReplaySlowLabel = props.modelReplaySlowLabel ?? '🐌 Half speed';
  const canReplayModel = useMemo(
    () =>
      Boolean(
        (modelReplayNormalLabel.trim() || modelReplaySlowLabel.trim()) &&
          (props.audioUrl || props.audioText?.trim()),
      ),
    [
      modelReplayNormalLabel,
      modelReplaySlowLabel,
      props.audioUrl,
      props.audioText,
    ],
  );

  return (
    <PromptedRecordingView
      state={controller.state}
      prompt={controller.prompt}
      playbackPrompt={controller.playbackPrompt}
      blockedReason={controller.blockedReason}
      startMode={props.startMode ?? 'auto'}
      startLabel={props.startLabel ?? 'Record'}
      recordingMs={controller.recordingMs}
      isSpeechActive={controller.isSpeechActive}
      audioError={controller.audioError}
      modelAudioError={controller.modelPlayback.audioError}
      recordingUrl={controller.recordingUrl}
      canReplayModel={canReplayModel}
      modelReplayNormalLabel={modelReplayNormalLabel}
      modelReplaySlowLabel={modelReplaySlowLabel}
      isModelPlaying={controller.modelPlayback.isPlaying}
      pendingCapture={controller.pendingCapture}
      reRecordLabel={props.reRecordLabel ?? 'Re-record'}
      nextLabel={props.nextLabel ?? 'Next'}
      onStart={controller.startPromptFlow}
      onReplayModelNormal={() => controller.replayModelAtSpeed(1)}
      onReplayModelSlow={() => controller.replayModelAtSpeed(0.5)}
      onReRecord={controller.reRecord}
      onConfirm={controller.confirmRecording}
    />
  );
}

