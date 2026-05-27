import type { SceneFrameData } from './types';

type SceneFrameProps = {
  frame?: SceneFrameData;
  isActive?: boolean;
  placeholderLabel?: string;
  fallbackTitle?: string;
};

export function SceneFrame({
  frame,
  isActive = false,
  placeholderLabel = 'Scene frame placeholder',
  fallbackTitle = 'Scene frame',
}: SceneFrameProps) {
  return (
    <figure className={`scene-frame ${isActive ? 'active' : ''}`}>
      {frame?.imageUrl ? (
        <img src={frame.imageUrl} alt={frame.alt || frame.title || placeholderLabel} />
      ) : (
        <div className="scene-frame-placeholder" aria-label={placeholderLabel} />
      )}
      <figcaption>
        <strong>{frame?.title || fallbackTitle}</strong>
        {frame?.speaker ? <span>{frame.speaker}</span> : null}
      </figcaption>
    </figure>
  );
}
