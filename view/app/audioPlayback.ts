import { getPrefetchedAudioElement } from './useAssetPrefetcher';

export const AUDIO_PLAYBACK_ERROR = 'Audio file could not be played.';
export const AUDIO_MISSING_ERROR = 'Audio file is missing.';

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
  onError?: (message: string) => void,
) {
  const audio = getPrefetchedAudioElement(url) ?? new Audio(url);
  audioRef.current = audio;
  setIsPlaying(true);

  audio.addEventListener(
    'ended',
    () => {
      if (audioRef.current !== audio) {
        return;
      }
      setIsPlaying(false);
      audioRef.current = null;
    },
    { once: true },
  );

  audio.addEventListener(
    'error',
    () => {
      if (audioRef.current !== audio) {
        return;
      }
      setIsPlaying(false);
      audioRef.current = null;
      onError?.(AUDIO_PLAYBACK_ERROR);
    },
    { once: true },
  );

  audio.play().catch(() => {
    if (audioRef.current !== audio) {
      return;
    }
    setIsPlaying(false);
    audioRef.current = null;
    onError?.(AUDIO_PLAYBACK_ERROR);
  });
}

export function playAudioOrSpeakThen(
  url: string | null | undefined,
  text: string | null | undefined,
  audioRef: { current: HTMLAudioElement | null },
  utteranceRef: { current: SpeechSynthesisUtterance | null },
  onComplete: () => void,
  _language?: string,
  onError?: (message: string) => void,
) {
  stopAudio(audioRef.current);
  stopSpeech(utteranceRef.current);

  if (url) {
    const audio = getPrefetchedAudioElement(url) ?? new Audio(url);
    audioRef.current = audio;
    const complete = () => {
      if (audioRef.current !== audio) {
        return;
      }
      audioRef.current = null;
      onComplete();
    };
    audio.addEventListener('ended', complete, { once: true });
    audio.addEventListener(
      'error',
      () => {
        if (audioRef.current !== audio) {
          return;
        }
        audioRef.current = null;
        onError?.(AUDIO_PLAYBACK_ERROR);
      },
      { once: true },
    );
    audio.play().catch(() => {
      if (audioRef.current !== audio) {
        return;
      }
      audioRef.current = null;
      onError?.(AUDIO_PLAYBACK_ERROR);
    });
    return;
  }

  const spokenText = text?.trim();
  if (!spokenText) {
    utteranceRef.current = null;
    onComplete();
    return;
  }

  utteranceRef.current = null;
  onError?.(AUDIO_MISSING_ERROR);
}
