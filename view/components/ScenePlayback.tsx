import { useEffect, useMemo, useRef, useState } from 'react';

import { playAudioUrl, speakTextAudio, stopAudio, stopSpeech } from '../app/audioPlayback';
import { AudioButton } from './AudioButton';
import { SceneFrame } from './SceneFrame';
import type { SceneFrameData } from './types';

type ScenePlaybackProps = {
  frames?: SceneFrameData[];
  autoplay?: boolean;
  stopAtLineType?: string;
};

export function ScenePlayback({ frames = [], autoplay = false, stopAtLineType }: ScenePlaybackProps) {
  const playableFrames = useMemo(() => {
    const withMedia = frames.filter((frame) => frame.imageUrl || frame.audioUrl || frame.audioText);
    if (!stopAtLineType) {
      return withMedia.filter((frame) => frame.imageUrl || frame.audioUrl);
    }

    const stopIndex = withMedia.findIndex((frame) => frame.lineType === stopAtLineType);
    if (stopIndex < 0) {
      return withMedia.filter((frame) => frame.imageUrl || frame.audioUrl);
    }

    return withMedia.slice(0, stopIndex + 1).filter((frame) => frame.imageUrl || frame.audioUrl);
  }, [frames, stopAtLineType]);
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

    playAudioUrl(frame.audioUrl, audioRef, (playing) => {
      if (!playing) {
        playFrameAt(index + 1);
      }
    });
  }

  function speakFrameText(text: string | undefined, onDone: () => void) {
    speakTextAudio(text, utteranceRef, (playing) => {
      if (!playing) {
        onDone();
      }
    });
  }

  return (
    <section className="scene-playback" aria-label="Scene playback">
      <SceneFrame frame={activeFrame} isActive showCaption={false} placeholderLabel="Lesson scene frame" />
      <AudioButton label="Play scene" isPlaying={isPlaying} disabled={isPlaying} onPlay={playScene} />
    </section>
  );
}
