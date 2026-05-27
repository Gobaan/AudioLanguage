import type { AudioButtonText, MicPromptText, SceneFrameData } from './types';
import { AudioButton } from './AudioButton';
import { FrameStrip } from './FrameStrip';
import { MicPrompt } from './MicPrompt';
import { SceneFrame } from './SceneFrame';

type TravellerLessonPlayerProps = {
  title?: string;
  frames?: SceneFrameData[];
  activeFrameId?: string;
  frameStripLabel?: string;
  audioText?: AudioButtonText;
  micText?: MicPromptText;
};

export function TravellerLessonPlayer({
  title = 'Traveller lesson',
  frames = [],
  activeFrameId,
  frameStripLabel,
  audioText,
  micText,
}: TravellerLessonPlayerProps) {
  const activeFrame = frames.find((frame) => frame.id === activeFrameId) ?? frames[0];

  return (
    <main className="traveller-lesson-player">
      <h1>{title}</h1>
      <SceneFrame frame={activeFrame} isActive />
      <FrameStrip frames={frames} activeFrameId={activeFrame?.id} ariaLabel={frameStripLabel} />
      <AudioButton text={audioText} />
      <MicPrompt text={micText} />
    </main>
  );
}
