import { SPEECH_RMS_THRESHOLD, SPEECH_VISUAL_HOLD_MS } from './constants';
import { rootMeanSquare } from './mediaUtils';

type SpeechDetectorCallbacks = {
  onSpeechStart: () => void;
  onSpeechSettled: () => void;
  onSpeechActiveChange: (isActive: boolean) => void;
};

export function startSpeechDetector(
  stream: MediaStream,
  callbacks: SpeechDetectorCallbacks,
): () => void {
  const AudioContextConstructor = window.AudioContext;
  if (!AudioContextConstructor) return () => undefined;

  const audioContext = new AudioContextConstructor();
  const source = audioContext.createMediaStreamSource(stream);
  const analyser = audioContext.createAnalyser();
  analyser.fftSize = 1024;
  source.connect(analyser);
  const samples = new Uint8Array(analyser.fftSize);

  let rafId: number | null = null;
  let holdTimer: number | null = null;

  const clearHold = () => {
    if (holdTimer === null) return;
    window.clearTimeout(holdTimer);
    holdTimer = null;
  };

  const tick = () => {
    analyser.getByteTimeDomainData(samples);
    const isSpeaking = rootMeanSquare(samples) > SPEECH_RMS_THRESHOLD;
    if (isSpeaking) {
      clearHold();
      callbacks.onSpeechStart();
      callbacks.onSpeechActiveChange(true);
    } else if (holdTimer === null) {
      holdTimer = window.setTimeout(() => {
        holdTimer = null;
        callbacks.onSpeechActiveChange(false);
        callbacks.onSpeechSettled();
      }, SPEECH_VISUAL_HOLD_MS);
    }
    rafId = window.requestAnimationFrame(tick);
  };

  rafId = window.requestAnimationFrame(tick);
  return () => {
    clearHold();
    if (rafId !== null) window.cancelAnimationFrame(rafId);
    if (audioContext.state !== 'closed') void audioContext.close().catch(() => undefined);
  };
}

