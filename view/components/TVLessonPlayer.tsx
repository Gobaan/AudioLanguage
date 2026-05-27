import type { AudioButtonText, SceneFrameData } from './types';
import { AudioButton } from './AudioButton';
import { SceneFrame } from './SceneFrame';

type TVLessonPlayerProps = {
  title?: string;
  frame?: SceneFrameData;
  audioText?: AudioButtonText;
};

export function TVLessonPlayer({ title = 'TV lesson', frame, audioText }: TVLessonPlayerProps) {
  return (
    <main className="tv-lesson-player">
      <h1>{title}</h1>
      <SceneFrame frame={frame} isActive />
      <AudioButton text={audioText} />
    </main>
  );
}
