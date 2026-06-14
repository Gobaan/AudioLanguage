import { useEffect, useRef, useState } from 'react';

import { playAudioOrSpeakThen, stopAudio, stopSpeech } from '../app/audioPlayback';

type RecordingState = 'ready' | 'prompting' | 'recording' | 'captured' | 'submitted' | 'blocked';

type CapturedRecording = {
  blob: Blob;
  durationMs: number;
  mimeType: string;
};

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
  recordingMs = 4000,
  startMode = 'auto',
  startLabel = 'Record',
  nextLabel = 'Next',
  reRecordLabel = 'Re-record',
  onListenComplete,
  onRecording,
  onCaptured,
  onNext,
}: PromptedRecordingProps) {
  const [state, setState] = useState<RecordingState>('ready');
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [pendingCapture, setPendingCapture] = useState<CapturedRecording | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingUrlRef = useRef<string | null>(null);
  const stopTimerRef = useRef<number | null>(null);
  const recordingStartedAtRef = useRef<number | null>(null);

  useEffect(() => {
    setState('ready');
    setPendingCapture(null);
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
    playAudioOrSpeakThen(audioUrl, audioText, audioRef, utteranceRef, () => {
      onListenComplete?.();
      startRecording();
    });
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

      streamRef.current = stream;
      mediaRecorderRef.current = recorder;

      recorder.addEventListener('dataavailable', (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      });

      recorder.addEventListener(
        'stop',
        () => {
          const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
          const durationMs = recordingStartedAtRef.current ? Date.now() - recordingStartedAtRef.current : recordingMs;
          recordingStartedAtRef.current = null;
          setRecordingUrl((currentUrl) => {
            if (currentUrl) URL.revokeObjectURL(currentUrl);
            return URL.createObjectURL(blob);
          });
          stopStream(stream);
          streamRef.current = null;
          mediaRecorderRef.current = null;
          const capture = { blob, durationMs, mimeType: blob.type };
          if (onCaptured) {
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
        stopRecorder(recorder);
      }, recordingMs);
    } catch {
      setState('blocked');
    }
  }

  function cleanup() {
    cleanupActiveFlow();
    if (recordingUrlRef.current) {
      URL.revokeObjectURL(recordingUrlRef.current);
      recordingUrlRef.current = null;
    }
  }

  function cleanupActiveFlow() {
    if (stopTimerRef.current !== null) {
      window.clearTimeout(stopTimerRef.current);
      stopTimerRef.current = null;
    }

    stopAudio(audioRef.current);
    audioRef.current = null;
    stopSpeech(utteranceRef.current);
    utteranceRef.current = null;

    stopRecorder(mediaRecorderRef.current);
    mediaRecorderRef.current = null;
    stopStream(streamRef.current);
    streamRef.current = null;
    recordingStartedAtRef.current = null;
  }

  function confirmRecording() {
    if (!pendingCapture) return;
    onCaptured?.(pendingCapture);
    setPendingCapture(null);
    setState('submitted');
    onNext?.();
  }

  function reRecord() {
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
      {recordingUrl ? (
        <audio className="recording-playback" controls src={recordingUrl} />
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

function stopRecorder(recorder: MediaRecorder | null) {
  if (recorder?.state === 'recording') {
    recorder.stop();
  }
}

function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop());
}
