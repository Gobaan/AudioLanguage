import { useEffect, useRef, useState } from 'react';

import { playAudioUrl, stopAudio } from '../app/audioPlayback';
import { AudioButton } from './AudioButton';

export type DialogueRevealLine = {
  id: string;
  speaker?: string;
  text?: string;
  transliteration?: string;
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
    setPlayingLineId(line.id);
    playAudioUrl(line.audioUrl, audioRef, (playing) => {
      if (!playing) {
        setPlayingLineId(null);
      }
    });
  }

  return (
    <section className="dialogue-reveal" aria-label={title}>
      <h2>{title}</h2>
      <ol>
        {lines.map((line) => (
          <li key={line.id} className={line.isTranslated ? 'translated' : ''}>
            <span className="dialogue-speaker">{speakerLabel(line)}</span>
            <span className="dialogue-line-text">{displayLineText(line)}</span>
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

function displayLineText(line: DialogueRevealLine): string | undefined {
  return line.transliteration || line.text;
}

function speakerLabel(line: DialogueRevealLine): string {
  if (line.isTranslated) {
    return 'You';
  }

  return line.speaker || 'Them';
}

