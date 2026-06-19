import { useEffect, useMemo, useRef, useState } from 'react';

import { playAudioOrSpeakThen, stopAudio, stopSpeech } from '../app/audioPlayback';
import { AudioButton } from './AudioButton';
import { SceneFrame } from './SceneFrame';
import type { SceneFrameData } from './types';

export type ScenePlaybackTutorial = {
  dismissId: string;
  badgeLabel: string;
  title: string;
  message: string;
  dismissLabel: string;
};

type ScenePlaybackProps = {
  frames?: SceneFrameData[];
  autoplay?: boolean;
  stopAtLineType?: string;
  tutorialForFrame?: (frame: SceneFrameData, index: number) => ScenePlaybackTutorial | null;
  onDismissTutorial?: (tutorialId: string) => void;
};

type PendingTutorial = {
  index: number;
  tutorial: ScenePlaybackTutorial;
};

export function ScenePlayback({
  frames = [],
  autoplay = false,
  stopAtLineType,
  tutorialForFrame,
  onDismissTutorial,
}: ScenePlaybackProps) {
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
  const playbackKey = useMemo(
    () =>
      playableFrames
        .map((frame) => `${frame.id}:${frame.audioUrl ?? ''}:${frame.audioText ?? ''}`)
        .join('|'),
    [playableFrames],
  );
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [pendingTutorial, setPendingTutorial] = useState<PendingTutorial | null>(null);
  const dismissedTutorialsRef = useRef<Set<string>>(new Set());
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
    setAudioError(null);
    setPendingTutorial(null);
  }, [playbackKey]);

  useEffect(() => {
    if (!autoplay || playableFrames.length === 0) return;
    playScene();

    return () => {
      stopAudio(audioRef.current);
      stopSpeech(utteranceRef.current);
    };
  }, [autoplay, playbackKey]);

  function playScene() {
    stopAudio(audioRef.current);
    stopSpeech(utteranceRef.current);
    setIsPlaying(true);
    setAudioError(null);
    setPendingTutorial(null);
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
    const tutorial = tutorialForFrame?.(frame, index) ?? null;
    if (tutorial && !dismissedTutorialsRef.current.has(tutorial.dismissId)) {
      setPendingTutorial({ index, tutorial });
      return;
    }

    playFrameAudio(index);
  }

  function playFrameAudio(index: number) {
    const frame = playableFrames[index];
    if (!frame) {
      setIsPlaying(false);
      audioRef.current = null;
      return;
    }

    playAudioOrSpeakThen(
      frame.audioUrl,
      frame.audioText || frame.transliteration || frame.text,
      audioRef,
      utteranceRef,
      () => playFrameAt(index + 1),
      undefined,
      (message) => {
        setIsPlaying(false);
        setAudioError(message);
      },
    );
  }

  function dismissPendingTutorial() {
    if (!pendingTutorial) {
      return;
    }

    const tutorialIndex = pendingTutorial.index;
    dismissedTutorialsRef.current.add(pendingTutorial.tutorial.dismissId);
    onDismissTutorial?.(pendingTutorial.tutorial.dismissId);
    setPendingTutorial(null);
    setIsPlaying(true);
    playFrameAudio(tutorialIndex);
  }

  return (
    <section className="scene-playback" aria-label="Scene playback">
      <SceneFrame frame={activeFrame} isActive showCaption={false} placeholderLabel="Lesson scene frame" />
      {pendingTutorial ? (
        <section className="transfer-tutorial-overlay" role="presentation">
          <div
            className="transfer-tutorial-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby={`scene-playback-tutorial-${pendingTutorial.tutorial.dismissId}`}
          >
            <p className="transfer-tutorial-badge">{pendingTutorial.tutorial.badgeLabel}</p>
            <h2 id={`scene-playback-tutorial-${pendingTutorial.tutorial.dismissId}`}>
              {pendingTutorial.tutorial.title}
            </h2>
            <p>{pendingTutorial.tutorial.message}</p>
            <nav className="transfer-tutorial-actions" aria-label="Scene tutorial actions">
              <button type="button" onClick={dismissPendingTutorial}>
                {pendingTutorial.tutorial.dismissLabel}
              </button>
            </nav>
          </div>
        </section>
      ) : null}
      {audioError ? (
        <p className="audio-error" role="alert">
          {audioError}
        </p>
      ) : null}
      <AudioButton label="Play scene" isPlaying={isPlaying} disabled={isPlaying} onPlay={playScene} />
    </section>
  );
}
