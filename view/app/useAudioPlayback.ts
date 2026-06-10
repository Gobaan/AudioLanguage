import { useCallback, useEffect, useRef, useState } from 'react';

import { playAudioUrl, speakTextAudio, stopAudio, stopSpeech } from './audioPlayback';

export function useAudioPlayback() {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const stop = useCallback(() => {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    audioRef.current = null;
    utteranceRef.current = null;
    setIsPlaying(false);
  }, []);

  const playAudio = useCallback((url: string | null | undefined) => {
    if (!url) return;

    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    playAudioUrl(url, audioRef, setIsPlaying);
  }, []);

  const speakText = useCallback((text: string | null | undefined, language?: string) => {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    speakTextAudio(text, utteranceRef, setIsPlaying, language);
  }, []);

  const playAudioOrSpeak = useCallback(
    (url: string | null | undefined, text: string | null | undefined, language?: string) => {
      if (url) {
        playAudio(url);
        return;
      }

      speakText(text, language);
    },
    [playAudio, speakText],
  );

  useEffect(() => stop, [stop]);

  return {
    isPlaying,
    playAudio,
    speakText,
    playAudioOrSpeak,
    stop,
  };
}
