import { useEffect } from 'react';

import { AudioButton } from '../components';
import { useAudioPlayback } from './useAudioPlayback';

export function ResponsePlayback({ audioUrl, audioText }: { audioUrl?: string; audioText?: string }) {
  const { isPlaying, playAudioOrSpeak, stop } = useAudioPlayback();

  useEffect(() => {
    playAudioOrSpeak(audioUrl, audioText);
    return stop;
  }, [audioUrl, audioText, playAudioOrSpeak, stop]);

  return (
    <div className="response-playback">
      <AudioButton
        label="Play response"
        isPlaying={isPlaying}
        disabled={isPlaying}
        onPlay={() => playAudioOrSpeak(audioUrl, audioText)}
      />
    </div>
  );
}
