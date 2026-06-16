import { useEffect } from 'react';

import { AudioButton } from '../components';
import { useAudioPlayback } from './useAudioPlayback';

export function ResponsePlayback({
  audioUrl,
  audioText,
}: {
  audioUrl?: string | null;
  audioText?: string | null;
}) {
  const { isPlaying, audioError, playAudioOrSpeak, stop } = useAudioPlayback();

  useEffect(() => {
    playAudioOrSpeak(audioUrl, audioText);
    return stop;
  }, [audioUrl, audioText, playAudioOrSpeak, stop]);

  return (
    <div className="response-playback">
      {audioError ? (
        <p className="audio-error" role="alert">
          {audioError}
        </p>
      ) : null}
      <AudioButton
        label="Play response"
        isPlaying={isPlaying}
        disabled={isPlaying}
        onPlay={() => playAudioOrSpeak(audioUrl, audioText)}
      />
    </div>
  );
}
