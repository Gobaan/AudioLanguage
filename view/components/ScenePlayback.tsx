import { useEffect, useMemo, useRef, useState } from 'react';
import { AudioButton } from './AudioButton';
import { SceneFrame } from './SceneFrame';
import type { SceneFrameData } from './types';

type ScenePlaybackProps = {
  frames?: SceneFrameData[];
  autoplay?: boolean;
};

export function ScenePlayback({ frames = [], autoplay = false }: ScenePlaybackProps) {
  const playableFrames = useMemo(() => frames.filter((frame) => frame.imageUrl || frame.audioUrl), [frames]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const activeFrame = playableFrames[activeIndex] ?? playableFrames[0];

  useEffect(() => {
    setActiveIndex(0);
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    audioRef.current = null;
    utteranceRef.current = null;
    setIsPlaying(false);
  }, [playableFrames]);

  useEffect(() => {
    if (!autoplay || playableFrames.length === 0) return;
    playScene();

    return () => {
      stopAudio(audioRef.current);
      stopSpeech(utteranceRef.current);
    };
  }, [autoplay, playableFrames]);

  function playScene() {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    setIsPlaying(true);
    playFrameAt(0);
  }

  function playFrameAt(index: number) {
    const frame = playableFrames[index];
    if (!frame) {
      setIsPlaying(false);
      audioRef.current = null;
      return;
    }

    setActiveIndex(index);
    if (!frame.audioUrl) {
      speakFrameText(frame.audioText || frame.transliteration || frame.text, () => playFrameAt(index + 1));
      return;
    }

    const audio = new Audio(frame.audioUrl);
    audioRef.current = audio;

    audio.addEventListener(
      'ended',
      () => {
        audioRef.current = null;
        playFrameAt(index + 1);
      },
      { once: true },
    );

    audio.addEventListener(
      'error',
      () => {
        audioRef.current = null;
        playFrameAt(index + 1);
      },
      { once: true },
    );

    audio.play().catch(() => {
      setIsPlaying(false);
      audioRef.current = null;
    });
  }

  function speakFrameText(text: string | undefined, onDone: () => void) {
    const spokenText = text?.trim();
    if (!spokenText || !window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') {
      onDone();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(spokenText);
    utteranceRef.current = utterance;
    utterance.addEventListener(
      'end',
      () => {
        utteranceRef.current = null;
        onDone();
      },
      { once: true },
    );
    utterance.addEventListener(
      'error',
      () => {
        utteranceRef.current = null;
        onDone();
      },
      { once: true },
    );
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  return (
    <section className="scene-playback" aria-label="Scene playback">
      <SceneFrame frame={activeFrame} isActive showCaption={false} placeholderLabel="Lesson scene frame" />
      <AudioButton label="Play scene" isPlaying={isPlaying} disabled={isPlaying} onPlay={playScene} />
    </section>
  );
}

function stopAudio(audio: HTMLAudioElement | null) {
  if (!audio) return;

  audio.pause();
  audio.currentTime = 0;
}

function stopSpeech(utterance: SpeechSynthesisUtterance | null) {
  if (!utterance) return;

  window.speechSynthesis?.cancel();
}
