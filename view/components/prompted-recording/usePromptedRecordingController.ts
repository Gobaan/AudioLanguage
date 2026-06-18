import { useEffect, useRef, useState } from 'react';

import { playAudioOrSpeakThen, stopAudio, stopSpeech } from '../../app/audioPlayback';
import { useAudioPlayback } from '../../app/useAudioPlayback';
import { DEFAULT_PLAYBACK_PROMPT, DEFAULT_PROMPT, DEFAULT_RECORDING_MS } from './constants';
import type { PromptedRecordingProps } from './types';
import { useRecorderEngine } from './useRecorderEngine';

export function usePromptedRecordingController(props: PromptedRecordingProps) {
  const {
    audioUrl, audioText, startMode = 'auto', onListenComplete, onNext, onCaptured, onRecording,
    recordingMs = DEFAULT_RECORDING_MS, autoConfirmCapture = false,
    prompt = DEFAULT_PROMPT, playbackPrompt = DEFAULT_PLAYBACK_PROMPT,
  } = props;
  const [audioError, setAudioError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const modelPlayback = useAudioPlayback();
  const engine = useRecorderEngine({ recordingMs, autoConfirmCapture, onCaptured, onRecording });

  const stopPromptPlayback = () => {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    audioRef.current = null;
    utteranceRef.current = null;
  };

  const cleanup = () => {
    modelPlayback.stop();
    stopPromptPlayback();
    engine.cleanup();
  };

  const startPromptFlow = () => {
    cleanup();
    engine.setState('prompting');
    setAudioError(null);
    playAudioOrSpeakThen(audioUrl, audioText, audioRef, utteranceRef, () => {
      onListenComplete?.();
      void engine.startRecording();
    }, undefined, setAudioError);
  };

  const confirmRecording = () => {
    if (!engine.pendingCapture) return;
    onCaptured?.(engine.pendingCapture);
    engine.setPendingCapture(null);
    engine.setState('submitted');
    onNext?.();
  };

  const reRecord = () => {
    modelPlayback.stop();
    engine.resetRecording();
    engine.setPendingCapture(null);
    engine.setState('ready');
    startPromptFlow();
  };

  useEffect(() => {
    engine.setState('ready');
    engine.setPendingCapture(null);
    setAudioError(null);
    engine.resetRecording();
    if (startMode === 'auto') startPromptFlow();
    return cleanup;
  }, [audioUrl, audioText, startMode]);

  return { ...engine, modelPlayback, audioError, prompt, playbackPrompt, recordingMs, startPromptFlow, confirmRecording, reRecord };
}

