import type { CSSProperties } from 'react';

export type SpeechIconBubbleKind = 'mic' | 'speaker';
export type SpeechIconBubbleTipPosition = 'left' | 'center' | 'right';
export type SpeechIconBubbleTipTilt = 'left' | 'none' | 'right';

type SpeechIconBubbleProps = {
  kind: SpeechIconBubbleKind;
  label?: string;
  tipPosition?: SpeechIconBubbleTipPosition;
  tipTilt?: SpeechIconBubbleTipTilt;
  rotationDegrees?: number;
  scale?: number;
};

export function SpeechIconBubble({
  kind,
  label,
  tipPosition = 'center',
  tipTilt = 'none',
  rotationDegrees,
  scale,
}: SpeechIconBubbleProps) {
  const title = label ?? (kind === 'mic' ? 'Learner speaking' : 'World speaking');
  const bubbleStyle =
    typeof rotationDegrees === 'number' || typeof scale === 'number'
      ? ({
          ...(typeof rotationDegrees === 'number'
            ? {
                '--speech-bubble-rotate': `${rotationDegrees}deg`,
                '--speech-bubble-icon-rotate': `${-rotationDegrees}deg`,
              }
            : {}),
          ...(typeof scale === 'number' ? { '--speech-bubble-scale': String(scale) } : {}),
        } as CSSProperties)
      : undefined;

  return (
    <span
      className={[
        'speech-icon-bubble',
        `speech-icon-bubble--${kind}`,
        `speech-icon-bubble--tip-${tipPosition}`,
        `speech-icon-bubble--tip-tilt-${tipTilt}`,
      ].join(' ')}
      style={bubbleStyle}
      title={title}
    >
      {kind === 'mic' ? <MicIcon /> : <SpeakerIcon />}
    </span>
  );
}

function SpeakerIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
      <path d="M16 8.5a5 5 0 0 1 0 7" />
      <path d="M18.5 6a8.5 8.5 0 0 1 0 12" />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
      <rect x="9" y="3" width="6" height="10" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <path d="M12 18v3" />
      <path d="M8 21h8" />
    </svg>
  );
}
