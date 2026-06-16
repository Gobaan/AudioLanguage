import { useEffect, useRef, useState, type CSSProperties } from 'react';

import { useAudioPlayback } from '../app/useAudioPlayback';
import { playAudioOrSpeakThen, stopAudio, stopSpeech } from '../app/audioPlayback';
import { AudioButton } from './AudioButton';
import type { CapturedRecording } from './types';

type RecordingState = 'ready' | 'prompting' | 'recording' | 'captured' | 'submitted' | 'blocked';

type PromptedRecordingProps = {
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
  autoConfirmCapture?: boolean;
  onListenComplete?: () => void;
  onRecording?: () => void;
  onCaptured?: (recording: CapturedRecording) => void;
  onNext?: () => void;
};

export function PromptedRecording({
  audioUrl,
  audioText,
  prompt = 'Now you say it.',
  playbackPrompt = 'Listen.',
  recordingMs = 5000,
  startMode = 'auto',
  startLabel = 'Record',
  nextLabel = 'Next',
  reRecordLabel = 'Re-record',
  modelReplayLabel = 'Listen again',
  autoConfirmCapture = false,
  onListenComplete,
  onRecording,
  onCaptured,
  onNext,
}: PromptedRecordingProps) {
  const [state, setState] = useState<RecordingState>('ready');
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [pendingCapture, setPendingCapture] = useState<CapturedRecording | null>(null);
  const [audioError, setAudioError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioLevelFrameRef = useRef<number | null>(null);
  const recordingUrlRef = useRef<string | null>(null);
  const stopTimerRef = useRef<number | null>(null);
  const hardStopTimerRef = useRef<number | null>(null);
  const recordingStartedAtRef = useRef<number | null>(null);
  const speechDetectedRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const lastSpeechAtRef = useRef<number | null>(null);
  const softTimeoutReachedRef = useRef(false);
  const stoppedByRef = useRef<CapturedRecording['stoppedBy']>('manual');
  const modelPlayback = useAudioPlayback();
  const canReplayModel = Boolean(modelReplayLabel && (audioUrl || audioText?.trim()));

  useEffect(() => {
    setState('ready');
    setPendingCapture(null);
    setAudioError(null);
    setRecordingUrl((currentUrl) => {
      if (currentUrl) URL.revokeObjectURL(currentUrl);
      return null;
    });

    if (startMode === 'auto') {
      startPromptFlow();
    }

    return () => {
      cleanup();
    };
  }, [audioUrl, audioText, startMode]);

  useEffect(() => {
    recordingUrlRef.current = recordingUrl;
  }, [recordingUrl]);

  function startPromptFlow() {
    cleanupActiveFlow();
    setState('prompting');
    setAudioError(null);
    playAudioOrSpeakThen(audioUrl, audioText, audioRef, utteranceRef, () => {
      onListenComplete?.();
      startRecording();
    }, undefined, setAudioError);
  }

  async function startRecording() {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setState('blocked');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks: Blob[] = [];
      const recorder = new MediaRecorder(stream);
      const stopAfterSilenceMs = Math.min(900, Math.max(450, Math.floor(recordingMs * 0.18)));
      const hardLimitMs = recordingMs + 5000;

      streamRef.current = stream;
      mediaRecorderRef.current = recorder;
      speechDetectedRef.current = false;
      isSpeakingRef.current = false;
      lastSpeechAtRef.current = null;
      softTimeoutReachedRef.current = false;
      stoppedByRef.current = 'manual';
      startSpeechDetection(stream, stopAfterSilenceMs);

      recorder.addEventListener('dataavailable', (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      });

      recorder.addEventListener(
        'stop',
        () => {
          clearRecordingTimers();
          const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
          const durationMs = recordingStartedAtRef.current ? Date.now() - recordingStartedAtRef.current : recordingMs;
          const speechDetected = speechDetectedRef.current;
          const timedOutWithoutSpeech = stoppedByRef.current === 'no_speech_timeout';
          recordingStartedAtRef.current = null;
          setRecordingUrl((currentUrl) => {
            if (currentUrl) URL.revokeObjectURL(currentUrl);
            return URL.createObjectURL(blob);
          });
          stopSpeechDetection();
          stopStream(stream);
          streamRef.current = null;
          mediaRecorderRef.current = null;
          const capture = {
            blob,
            durationMs,
            mimeType: blob.type,
            speechDetected,
            timedOutWithoutSpeech,
            stoppedBy: stoppedByRef.current,
          };
          if (onCaptured) {
            if (autoConfirmCapture) {
              onCaptured(capture);
              setState('submitted');
              return;
            }
            setPendingCapture(capture);
            setState('captured');
            return;
          }
          setState('submitted');
        },
        { once: true },
      );

      recorder.start();
      recordingStartedAtRef.current = Date.now();
      setState('recording');
      onRecording?.();
      stopTimerRef.current = window.setTimeout(() => {
        softTimeoutReachedRef.current = true;
        if (!speechDetectedRef.current) {
          stoppedByRef.current = 'no_speech_timeout';
          stopRecorder(recorder);
          return;
        }

        if (!isSpeakingRef.current && recordingHasBeenSilentFor(stopAfterSilenceMs)) {
          stoppedByRef.current = 'timer';
          stopRecorder(recorder);
        }
      }, recordingMs);
      hardStopTimerRef.current = window.setTimeout(() => {
        stoppedByRef.current = 'hard_limit';
        stopRecorder(recorder);
      }, hardLimitMs);
    } catch {
      setState('blocked');
    }
  }

  function startSpeechDetection(stream: MediaStream, stopAfterSilenceMs: number) {
    const AudioContextConstructor = window.AudioContext;
    if (!AudioContextConstructor) {
      return;
    }

    const audioContext = new AudioContextConstructor();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 1024;
    source.connect(analyser);
    audioContextRef.current = audioContext;
    const samples = new Uint8Array(analyser.fftSize);

    function watchAudioLevel() {
      analyser.getByteTimeDomainData(samples);
      const level = rootMeanSquare(samples);
      const isSpeaking = level > 0.025;
      const now = Date.now();

      isSpeakingRef.current = isSpeaking;
      if (isSpeaking) {
        speechDetectedRef.current = true;
        lastSpeechAtRef.current = now;
      }

      if (
        softTimeoutReachedRef.current &&
        speechDetectedRef.current &&
        !isSpeaking &&
        recordingHasBeenSilentFor(stopAfterSilenceMs)
      ) {
        stoppedByRef.current = 'speech_completed';
        stopRecorder(mediaRecorderRef.current);
        return;
      }

      audioLevelFrameRef.current = window.requestAnimationFrame(watchAudioLevel);
    }

    audioLevelFrameRef.current = window.requestAnimationFrame(watchAudioLevel);
  }

  function recordingHasBeenSilentFor(durationMs: number): boolean {
    const lastSpeechAt = lastSpeechAtRef.current;
    return lastSpeechAt === null || Date.now() - lastSpeechAt >= durationMs;
  }

  function replayModelAudio() {
    modelPlayback.playAudioOrSpeak(audioUrl, audioText);
  }

  function cleanup() {
    modelPlayback.stop();
    cleanupActiveFlow();
    if (recordingUrlRef.current) {
      URL.revokeObjectURL(recordingUrlRef.current);
      recordingUrlRef.current = null;
    }
  }

  function cleanupActiveFlow() {
    clearRecordingTimers();

    stopAudio(audioRef.current);
    audioRef.current = null;
    stopSpeech(utteranceRef.current);
    utteranceRef.current = null;

    stopSpeechDetection();
    stopRecorder(mediaRecorderRef.current);
    mediaRecorderRef.current = null;
    stopStream(streamRef.current);
    streamRef.current = null;
    recordingStartedAtRef.current = null;
  }

  function stopSpeechDetection() {
    if (audioLevelFrameRef.current !== null) {
      window.cancelAnimationFrame(audioLevelFrameRef.current);
      audioLevelFrameRef.current = null;
    }

    const audioContext = audioContextRef.current;
    audioContextRef.current = null;
    if (audioContext && audioContext.state !== 'closed') {
      void audioContext.close().catch(() => undefined);
    }
  }

  function clearRecordingTimers() {
    if (stopTimerRef.current !== null) {
      window.clearTimeout(stopTimerRef.current);
      stopTimerRef.current = null;
    }

    if (hardStopTimerRef.current !== null) {
      window.clearTimeout(hardStopTimerRef.current);
      hardStopTimerRef.current = null;
    }
  }

  function confirmRecording() {
    if (!pendingCapture) return;
    onCaptured?.(pendingCapture);
    setPendingCapture(null);
    setState('submitted');
    onNext?.();
  }

  function reRecord() {
    modelPlayback.stop();
    if (recordingUrlRef.current) {
      URL.revokeObjectURL(recordingUrlRef.current);
      recordingUrlRef.current = null;
    }
    setRecordingUrl(null);
    setPendingCapture(null);
    setState('ready');
    startPromptFlow();
  }

  return (
    <section className={`prompted-recording ${state}`} aria-live="polite">
      <p>{statusText(state, prompt, playbackPrompt)}</p>
      {state === 'ready' && startMode === 'manual' ? (
        <button type="button" className="record-button" onClick={startPromptFlow}>
          {startLabel}
        </button>
      ) : null}
      {state === 'recording' ? (
        <div
          className="recording-countdown"
          aria-hidden="true"
          style={{ '--recording-duration': `${recordingMs}ms` } as CSSProperties}
        >
          <span />
        </div>
      ) : null}
      {audioError || modelPlayback.audioError ? (
        <p className="audio-error" role="alert">
          {audioError || modelPlayback.audioError}
        </p>
      ) : null}
      {recordingUrl ? (
        <audio className="recording-playback" controls src={recordingUrl} />
      ) : null}
      {state === 'captured' && canReplayModel ? (
        <AudioButton
          label={modelReplayLabel}
          isPlaying={modelPlayback.isPlaying}
          disabled={modelPlayback.isPlaying}
          onPlay={replayModelAudio}
          text={{ playLabel: modelReplayLabel, playingLabel: 'Playing…' }}
        />
      ) : null}
      {state === 'captured' && pendingCapture ? (
        <div className="recording-review-actions">
          <button type="button" className="record-button record-button-secondary" onClick={reRecord}>
            {reRecordLabel}
          </button>
          <button type="button" className="record-button" onClick={confirmRecording}>
            {nextLabel}
          </button>
        </div>
      ) : null}
    </section>
  );
}

function statusText(state: RecordingState, prompt: string, playbackPrompt: string): string {
  if (state === 'prompting') return playbackPrompt;
  if (state === 'recording') return prompt;
  if (state === 'captured') return 'Review your recording.';
  if (state === 'submitted') return 'Saved.';
  if (state === 'blocked') return 'Microphone access is needed.';
  return prompt;
}

function rootMeanSquare(samples: Uint8Array): number {
  let total = 0;
  for (const sample of samples) {
    const centered = (sample - 128) / 128;
    total += centered * centered;
  }
  return Math.sqrt(total / samples.length);
}

function stopRecorder(recorder: MediaRecorder | null) {
  if (recorder?.state === 'recording') {
    recorder.stop();
  }
}

function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop());
}
