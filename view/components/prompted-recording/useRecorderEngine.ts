import { useEffect, useRef, useState } from 'react';
import type { CapturedRecording } from '../types';
import { stopRecorder, stopStream } from './mediaUtils';
import { startSpeechDetector } from './speechDetector';
import type { RecordingState } from './types';
type UseRecorderEngineArgs = {
  recordingMs: number;
  autoConfirmCapture: boolean;
  onRecording?: () => void;
  onCaptured?: (recording: CapturedRecording) => void;
};
export function useRecorderEngine(args: UseRecorderEngineArgs) {
  const [state, setState] = useState<RecordingState>('ready');
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [pendingCapture, setPendingCapture] = useState<CapturedRecording | null>(null);
  const [isSpeechActive, setIsSpeechActive] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const stopDetectorRef = useRef<(() => void) | null>(null);
  const startedAtRef = useRef<number | null>(null);
  const speechDetectedRef = useRef(false);
  const stoppedByRef = useRef<CapturedRecording['stoppedBy']>('manual');
  const softStopRef = useRef<number | null>(null);
  const hardStopRef = useRef<number | null>(null);
  const ensureStopRef = useRef<number | null>(null);
  const clearTimers = () => {
    if (softStopRef.current !== null) window.clearTimeout(softStopRef.current);
    if (hardStopRef.current !== null) window.clearTimeout(hardStopRef.current);
    if (ensureStopRef.current !== null) window.clearTimeout(ensureStopRef.current);
    softStopRef.current = null;
    hardStopRef.current = null;
    ensureStopRef.current = null;
  };
  const stopDetection = () => {
    stopDetectorRef.current?.();
    stopDetectorRef.current = null;
  };
  const stopForCompletedSpeech = () => {
    if (!speechDetectedRef.current) return;
    const recorder = recorderRef.current;
    if (recorder?.state !== 'recording') return;
    stoppedByRef.current = 'speech_completed';
    stopRecorder(recorder);
    ensureStopRef.current = window.setTimeout(() => {
      if (recorder.state === 'recording') {
        stopStream(streamRef.current);
        stopRecorder(recorder);
      }
      stopDetection();
      ensureStopRef.current = null;
    }, 200);
  };
  const resetRecording = () => setRecordingUrl((url: string | null) => (url ? (URL.revokeObjectURL(url), null) : null));
  const cleanup = () => {
    clearTimers();
    stopDetection();
    stopRecorder(recorderRef.current);
    stopStream(streamRef.current);
    recorderRef.current = null;
    streamRef.current = null;
    startedAtRef.current = null;
    setIsSpeechActive(false);
  };
  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') return setState('blocked');
    try {
      cleanup();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      streamRef.current = stream;
      recorderRef.current = recorder;
      speechDetectedRef.current = false;
      stoppedByRef.current = 'manual';
      stopDetectorRef.current = startSpeechDetector(stream, { onSpeechActiveChange: setIsSpeechActive, onSpeechStart: () => {
        speechDetectedRef.current = true; }, onSpeechSettled: stopForCompletedSpeech });
      recorder.addEventListener('dataavailable', (event) => { if (event.data.size > 0) chunks.push(event.data); });
      recorder.addEventListener('stop', () => {
        clearTimers(); stopDetection(); stopStream(stream); streamRef.current = null; recorderRef.current = null;
        const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
        const capture: CapturedRecording = { blob, durationMs: startedAtRef.current ? Date.now() - startedAtRef.current : args.recordingMs, mimeType: blob.type, speechDetected: speechDetectedRef.current, timedOutWithoutSpeech: stoppedByRef.current === 'no_speech_timeout', stoppedBy: stoppedByRef.current };
        startedAtRef.current = null; setRecordingUrl((url: string | null) => (url && URL.revokeObjectURL(url), URL.createObjectURL(blob)));
        if (!args.onCaptured) return setState('submitted');
        if (args.autoConfirmCapture) { args.onCaptured(capture); return setState('submitted'); }
        setPendingCapture(capture); setState('captured');
      }, { once: true });
      recorder.start(); startedAtRef.current = Date.now(); setState('recording'); args.onRecording?.();
      softStopRef.current = window.setTimeout(() => { if (!speechDetectedRef.current) { stoppedByRef.current = 'no_speech_timeout'; stopRecorder(recorder); } }, args.recordingMs);
      hardStopRef.current = window.setTimeout(() => { stoppedByRef.current = 'hard_limit'; stopRecorder(recorder); }, args.recordingMs + 5000);
    } catch { setState('blocked'); }
  };
  useEffect(() => cleanup, []);
  return { state, setState, recordingUrl, pendingCapture, isSpeechActive, setPendingCapture, resetRecording, cleanup, startRecording };
}
