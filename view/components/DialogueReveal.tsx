import { useEffect, useRef, useState } from 'react';
import { AudioButton } from './AudioButton';

export type DialogueRevealLine = {
  id: string;
  speaker?: string;
  text?: string;
  translation?: string;
  audioUrl?: string;
  isTranslated?: boolean;
};

type DialogueRevealProps = {
  lines: DialogueRevealLine[];
  title?: string;
};

export function DialogueReveal({ lines, title = 'Dialogue' }: DialogueRevealProps) {
  const [playingLineId, setPlayingLineId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      stopAudio(audioRef.current);
    };
  }, []);

  function playLine(line: DialogueRevealLine) {
    if (!line.audioUrl) return;

    stopAudio(audioRef.current);
    const audio = new Audio(line.audioUrl);
    audioRef.current = audio;
    setPlayingLineId(line.id);

    audio.addEventListener(
      'ended',
      () => {
        setPlayingLineId(null);
        audioRef.current = null;
      },
      { once: true },
    );

    audio.addEventListener(
      'error',
      () => {
        setPlayingLineId(null);
        audioRef.current = null;
      },
      { once: true },
    );

    audio.play().catch(() => {
      setPlayingLineId(null);
      audioRef.current = null;
    });
  }

  return (
    <section className="dialogue-reveal" aria-label={title}>
      <h2>{title}</h2>
      <ol>
        {lines.map((line) => (
          <li key={line.id} className={line.isTranslated ? 'translated' : ''}>
            <span className="dialogue-speaker">{speakerLabel(line)}</span>
            <span className="dialogue-line-text">{line.text}</span>
            {line.isTranslated && line.translation ? (
              <span className="dialogue-translation">
                <span>{line.translation}</span>
                {line.audioUrl ? (
                  <AudioButton
                    label="Hear line"
                    isPlaying={playingLineId === line.id}
                    disabled={playingLineId === line.id}
                    onPlay={() => playLine(line)}
                  />
                ) : null}
              </span>
            ) : null}
          </li>
        ))}
      </ol>
    </section>
  );
}

function speakerLabel(line: DialogueRevealLine): string {
  if (line.isTranslated) {
    return 'You';
  }

  return line.speaker || 'Them';
}

function stopAudio(audio: HTMLAudioElement | null) {
  if (!audio) return;

  audio.pause();
  audio.currentTime = 0;
}
