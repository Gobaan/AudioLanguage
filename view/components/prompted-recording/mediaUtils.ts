export function rootMeanSquare(samples: Uint8Array): number {
  let total = 0;
  for (const sample of samples) {
    const centered = (sample - 128) / 128;
    total += centered * centered;
  }
  return Math.sqrt(total / samples.length);
}

export function stopRecorder(recorder: MediaRecorder | null) {
  if (recorder?.state === 'recording') {
    recorder.stop();
  }
}

export function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop());
}

