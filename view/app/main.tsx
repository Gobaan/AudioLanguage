import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { AdminValidationApp } from './admin/AdminValidationApp';
import { DebugAudioLessonPlayer } from './DebugAudioLessonPlayer';
import { LanguageSelectionApp } from './LanguageSelectionApp';
import { RecordingCountdownPreview } from './RecordingCountdownPreview';
import { TravellerMvpApp } from './TravellerMvpApp';
import './styles.css';

const root = document.querySelector('#root');

if (!root) {
  throw new Error('Missing #root element');
}

createRoot(root).render(
  <StrictMode>
    {appForPath(window.location.pathname)}
  </StrictMode>,
);

function appForPath(pathname: string) {
  if (pathname === '/gobi-admin') return <AdminValidationApp />;
  if (pathname === '/gobi-home') return <LanguageSelectionApp />;
  if (pathname === '/debug/audio') return <DebugAudioLessonPlayer />;
  if (pathname === '/debug/recording-countdown') return <RecordingCountdownPreview />;
  if (pathname === '/learn') return <TravellerMvpApp />;
  return <div className="frame-placeholder" aria-label="Page unavailable" />;
}
