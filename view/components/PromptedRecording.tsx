import { useEffect, useRef, useState } from 'react';

type RecordingState = 'ready' | 'prompting' | 'recording' | 'captured' | 'blocked';

type PromptedRecordingProps = {
  audioUrl?: string | null;
  prompt?: string;
  recordingMs?: number;
};

export function PromptedRecording({
  audioUrl,
  prompt = 'Now you say it.',
  recordingMs = 4000,
}: PromptedRecordingProps) {
  const [state, setState] = useState<RecordingState>('ready');
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingUrlRef = useRef<string | null>(null);
  const stopTimerRef = useRef<number | null>(null);

  useEffect(() => {
    startPromptFlow();

    return () => {
      cleanup();
    };
  }, [audioUrl]);

  useEffect(() => {
    recordingUrlRef.current = recordingUrl;
  }, [recordingUrl]);

  function startPromptFlow() {
    cleanupActiveFlow();

    if (!audioUrl) {
      startRecording();
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
          setRecordingUrl((currentUrl) => {
            if (currentUrl) URL.revokeObjectURL(currentUrl);
            return URL.createObjectURL(blob);
          });
          stopStream(stream);
          streamRef.current = null;
          mediaRecorderRef.current = null;
          setState('captured');
        },
        { once: true },
      );

      recorder.start();
      setState('recording');
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

    stopRecorder(mediaRecorderRef.current);
    mediaRecorderRef.current = null;
    stopStream(streamRef.current);
    streamRef.current = null;
  }

  return (
    <section className={`prompted-recording ${state}`} aria-live="polite">
      <p>{statusText(state, prompt)}</p>
      {recordingUrl ? (
        <audio className="recording-playback" controls src={recordingUrl} />
      ) : null}
    </section>
  );
}

function statusText(state: RecordingState, prompt: string): string {
  if (state === 'prompting') return prompt;
  if (state === 'recording') return 'Listening...';
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
