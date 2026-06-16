import { useCallback, useEffect, useRef, useState } from 'react';

import { AUDIO_MISSING_ERROR, playAudioUrl, stopAudio, stopSpeech } from './audioPlayback';

export function useAudioPlayback() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const stop = useCallback(() => {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    audioRef.current = null;
    utteranceRef.current = null;
    setIsPlaying(false);
    setAudioError(null);
  }, []);

  const playAudio = useCallback((url: string | null | undefined) => {
    setAudioError(null);
    if (!url) {
      setAudioError(AUDIO_MISSING_ERROR);
      return;
    }

    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    playAudioUrl(url, audioRef, setIsPlaying, setAudioError);
  }, []);

  const playAudioOrSpeak = useCallback(
    (url: string | null | undefined, text: string | null | undefined, _language?: string) => {
      if (url) {
        playAudio(url);
        return;
      }

      setIsPlaying(false);
      setAudioError(text?.trim() ? AUDIO_MISSING_ERROR : null);
    },
    [playAudio],
  );

  useEffect(() => stop, [stop]);

  return {
    isPlaying,
    audioError,
    playAudio,
    playAudioOrSpeak,
    stop,
  };
}
