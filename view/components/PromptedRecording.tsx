import { useEffect, useRef, useState } from 'react';

type RecordingState = 'ready' | 'prompting' | 'recording' | 'captured' | 'blocked';

type PromptedRecordingProps = {
  audioUrl?: string | null;
  audioText?: string | null;
  prompt?: string;
  playbackPrompt?: string;
  recordingMs?: number;
  startMode?: 'auto' | 'manual';
  startLabel?: string;
  onRecording?: () => void;
  onCaptured?: (recording: { blob: Blob; durationMs: number; mimeType: string }) => void;
};

export function PromptedRecording({
  audioUrl,
  audioText,
  prompt = 'Now you say it.',
  playbackPrompt = 'Listen.',
  recordingMs = 4000,
  startMode = 'auto',
  startLabel = 'Record',
  onRecording,
  onCaptured,
}: PromptedRecordingProps) {
  const [state, setState] = useState<RecordingState>('ready');
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingUrlRef = useRef<string | null>(null);
  const stopTimerRef = useRef<number | null>(null);
  const recordingStartedAtRef = useRef<number | null>(null);

  useEffect(() => {
    setState('ready');
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

    if (!audioUrl) {
      speakPromptThenRecord();
      return;
    }

    setState('prompting');
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.addEventListener(
      'ended',
      () => {
        audioRef.current = null;
        startRecording();
      },
      { once: true },
    );

    audio.addEventListener(
      'error',
      () => {
        audioRef.current = null;
        startRecording();
      },
      { once: true },
    );

    audio.play().catch(() => {
      audioRef.current = null;
      speakPromptThenRecord();
    });
  }

  function speakPromptThenRecord() {
    const text = audioText?.trim();
    if (!text || !window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') {
      startRecording();
      return;
    }

    setState('prompting');
    const utterance = new SpeechSynthesisUtterance(text);
    utteranceRef.current = utterance;
    utterance.addEventListener(
      'end',
      () => {
        utteranceRef.current = null;
        startRecording();
      },
      { once: true },
    );
    utterance.addEventListener(
      'error',
      () => {
        utteranceRef.current = null;
        startRecording();
      },
      { once: true },
    );
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
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
          setState('captured');
          onCaptured?.({ blob, durationMs, mimeType: blob.type });
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

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }

    if (utteranceRef.current) {
      window.speechSynthesis?.cancel();
      utteranceRef.current = null;
    }

    stopRecorder(mediaRecorderRef.current);
    mediaRecorderRef.current = null;
    stopStream(streamRef.current);
    streamRef.current = null;
    recordingStartedAtRef.current = null;
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
    </section>
  );
}

function statusText(state: RecordingState, prompt: string, playbackPrompt: string): string {
  if (state === 'prompting') return playbackPrompt;
  if (state === 'recording') return prompt;
  if (state === 'captured') return 'Captured.';
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
