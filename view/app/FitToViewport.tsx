import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';

type FitLayout = {
  scale: number;
  scaledHeight: number;
};

type FitToViewportProps = {
  children: ReactNode;
  className?: string;
  scrollable?: boolean;
};

export function FitToViewport({ children, className, scrollable = false }: FitToViewportProps) {
  const shellRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [layout, setLayout] = useState<FitLayout>({ scale: 1, scaledHeight: 0 });

  useLayoutEffect(() => {
    if (scrollable) {
      return undefined;
    }

    const shell = shellRef.current;
    const content = contentRef.current;
    if (!shell || !content) return;

    function updateLayout() {
      content.style.transform = 'none';

      const naturalWidth = content.offsetWidth;
      const naturalHeight = content.scrollHeight;
      const availableWidth = shell.clientWidth;
      const availableHeight = shell.clientHeight;

      if (naturalWidth === 0 || naturalHeight === 0 || availableWidth === 0 || availableHeight === 0) {
        return;
      }

      const scale = Math.min(1, availableWidth / naturalWidth, availableHeight / naturalHeight);
      setLayout({
        scale,
        scaledHeight: naturalHeight * scale,
      });
    }

    const observer = new ResizeObserver(updateLayout);
    observer.observe(shell);
    observer.observe(content);
    window.addEventListener('resize', updateLayout);
    updateLayout();

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', updateLayout);
    };
  }, [scrollable]);

  const shellClassName = [
    'fit-viewport-shell',
    scrollable ? 'fit-viewport-shell--scroll' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  if (scrollable) {
    return (
      <div ref={shellRef} className={shellClassName}>
        <div className="fit-viewport-content">{children}</div>
      </div>
    );
  }

  return (
    <div ref={shellRef} className={shellClassName}>
      <div className="fit-viewport-frame" style={{ height: layout.scaledHeight || undefined }}>
        <div
          ref={contentRef}
          className="fit-viewport-content"
          style={{
            transform: layout.scale < 1 ? `scale(${layout.scale})` : undefined,
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}
