export function stopAudio(audio: HTMLAudioElement | null) {
  if (!audio) return;

  audio.pause();
  audio.currentTime = 0;
}

export function stopSpeech(utterance: SpeechSynthesisUtterance | null) {
  if (!utterance) return;

  window.speechSynthesis?.cancel();
}

export function playAudioUrl(
  url: string,
  audioRef: { current: HTMLAudioElement | null },
  setIsPlaying: (playing: boolean) => void,
) {
  const audio = new Audio(url);
  audioRef.current = audio;
  setIsPlaying(true);

  audio.addEventListener(
    'ended',
    () => {
      setIsPlaying(false);
      audioRef.current = null;
    },
    { once: true },
  );

  audio.addEventListener(
    'error',
    () => {
      setIsPlaying(false);
      audioRef.current = null;
    },
    { once: true },
  );

  audio.play().catch(() => {
    setIsPlaying(false);
    audioRef.current = null;
  });
}

export function speakTextAudio(
  text: string | null | undefined,
  utteranceRef: { current: SpeechSynthesisUtterance | null },
  setIsPlaying: (playing: boolean) => void,
  language?: string,
) {
  const spokenText = text?.trim();
  if (!spokenText || !window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') {
    setIsPlaying(false);
    utteranceRef.current = null;
    return;
  }

  const utterance = new SpeechSynthesisUtterance(spokenText);
  if (language) {
    utterance.lang = language;
  }
  utteranceRef.current = utterance;
  setIsPlaying(true);
  utterance.addEventListener(
    'end',
    () => {
      setIsPlaying(false);
      utteranceRef.current = null;
    },
    { once: true },
  );
  utterance.addEventListener(
    'error',
    () => {
      setIsPlaying(false);
      utteranceRef.current = null;
    },
    { once: true },
  );
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}
