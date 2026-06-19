import type { SceneFrameData } from './types';
import { SpeechIconBubble } from './SpeechIconBubble';

type SceneFrameProps = {
  frame?: SceneFrameData;
  isActive?: boolean;
  showCaption?: boolean;
  placeholderLabel?: string;
  fallbackTitle?: string;
};

export function SceneFrame({
  frame,
  isActive = false,
  showCaption = true,
  placeholderLabel = 'Scene frame placeholder',
  fallbackTitle = 'Scene frame',
}: SceneFrameProps) {
  return (
    <figure className={`scene-frame ${isActive ? 'active' : ''}`}>
      <div className="scene-frame-media">
        {frame?.imageUrl ? (
          <img src={frame.imageUrl} alt={frame.alt || frame.title || placeholderLabel} />
        ) : (
          <div className="scene-frame-placeholder" aria-label={placeholderLabel} />
        )}
        {frame?.speechBubble ? <SpeechBubbleOverlay bubble={frame.speechBubble} /> : null}
      </div>
      {showCaption ? (
        <figcaption>
          <strong>{frame?.title || fallbackTitle}</strong>
          {frame?.speaker ? <span>{frame.speaker}</span> : null}
        </figcaption>
      ) : null}
    </figure>
  );
}

type SpeechBubbleOverlayProps = {
  bubble: NonNullable<SceneFrameData['speechBubble']>;
};

export function SpeechBubbleOverlay({ bubble }: SpeechBubbleOverlayProps) {
  const style = {
    left: `${bubble.anchorX * 100}%`,
    top: `${bubble.anchorY * 100}%`,
  };
  const label = bubble.kind === 'mic' ? 'Learner speaking' : 'World speaking';

  return (
    <div
      aria-hidden="true"
      className={`speech-bubble-anchor speech-bubble-anchor--${bubble.side}`}
      style={style}
      title={label}
    >
      <SpeechIconBubble
        kind={bubble.kind}
        label={label}
        tipPosition={bubble.tipPosition ?? tipPositionForSide(bubble.side)}
        tipTilt={bubble.tipTilt ?? tipTiltForSide(bubble.side)}
        rotationDegrees={bubble.rotationDegrees}
        scale={bubble.scale}
      />
    </div>
  );
}

function tipPositionForSide(side: string): 'left' | 'center' | 'right' {
  if (side.includes('left')) return 'left';
  if (side.includes('right')) return 'right';
  return 'center';
}

function tipTiltForSide(side: string): 'left' | 'none' | 'right' {
  if (side.includes('left')) return 'left';
  if (side.includes('right')) return 'right';
  return 'none';
}
