import type { SceneFrameData } from './types';

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
      {frame?.imageUrl ? (
        <img src={frame.imageUrl} alt={frame.alt || frame.title || placeholderLabel} />
      ) : (
        <div className="scene-frame-placeholder" aria-label={placeholderLabel} />
      )}
      {showCaption ? (
        <figcaption>
          <strong>{frame?.title || fallbackTitle}</strong>
          {frame?.speaker ? <span>{frame.speaker}</span> : null}
        </figcaption>
      ) : null}
    </figure>
  );
}
