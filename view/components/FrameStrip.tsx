import type { SceneFrameData } from './types';

type FrameStripProps = {
  frames?: SceneFrameData[];
  activeFrameId?: string;
  ariaLabel?: string;
  onSelectFrame?: (frame: SceneFrameData) => void;
};

export function FrameStrip({
  frames = [],
  activeFrameId,
  ariaLabel = 'Scene frames',
  onSelectFrame,
}: FrameStripProps) {
  return (
    <div className="frame-strip" aria-label={ariaLabel}>
      {frames.map((frame) => (
        <button
          key={frame.id}
          type="button"
          className={frame.id === activeFrameId ? 'active' : ''}
          onClick={() => onSelectFrame?.(frame)}
        >
          {frame.imageUrl ? <img src={frame.imageUrl} alt="" /> : null}
          <span>{frame.title || frame.id}</span>
        </button>
      ))}
    </div>
  );
}
