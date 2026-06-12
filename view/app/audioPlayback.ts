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

export function playAudioOrSpeakThen(
  url: string | null | undefined,
  text: string | null | undefined,
  audioRef: { current: HTMLAudioElement | null },
  utteranceRef: { current: SpeechSynthesisUtterance | null },
  onComplete: () => void,
  language?: string,
) {
  stopAudio(audioRef.current);
  stopSpeech(utteranceRef.current);

  if (url) {
    const audio = new Audio(url);
    audioRef.current = audio;
    const complete = () => {
      audioRef.current = null;
      onComplete();
    };
    audio.addEventListener('ended', complete, { once: true });
    audio.addEventListener('error', complete, { once: true });
    audio.play().catch(complete);
    return;
  }

  const spokenText = text?.trim();
  if (!spokenText || !window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') {
    utteranceRef.current = null;
    onComplete();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(spokenText);
  if (language) {
    utterance.lang = language;
  }
  utteranceRef.current = utterance;
  const complete = () => {
    utteranceRef.current = null;
    onComplete();
  };
  utterance.addEventListener('end', complete, { once: true });
  utterance.addEventListener('error', complete, { once: true });
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}
