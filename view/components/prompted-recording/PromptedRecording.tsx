import { useMemo } from 'react';

import type { PromptedRecordingProps } from './types';
import { PromptedRecordingView } from './PromptedRecordingView';
import { usePromptedRecordingController } from './usePromptedRecordingController';

export function PromptedRecording(props: PromptedRecordingProps) {
  const controller = usePromptedRecordingController(props);
  const canReplayModel = useMemo(
    () =>
      Boolean(
        (props.modelReplayLabel || props.modelReplayNormalLabel || props.modelReplaySlowLabel) &&
          (props.audioUrl || props.audioText?.trim()),
      ),
    [
      props.modelReplayLabel,
      props.modelReplayNormalLabel,
      props.modelReplaySlowLabel,
      props.audioUrl,
      props.audioText,
    ],
  );

  return (
    <PromptedRecordingView
      state={controller.state}
      prompt={controller.prompt}
      playbackPrompt={controller.playbackPrompt}
      startMode={props.startMode ?? 'auto'}
      startLabel={props.startLabel ?? 'Record'}
      recordingMs={controller.recordingMs}
      isSpeechActive={controller.isSpeechActive}
      audioError={controller.audioError}
      modelAudioError={controller.modelPlayback.audioError}
      recordingUrl={controller.recordingUrl}
      canReplayModel={canReplayModel}
      modelReplayNormalLabel={props.modelReplayNormalLabel ?? props.modelReplayLabel ?? 'Listen again'}
      modelReplaySlowLabel={props.modelReplaySlowLabel}
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

