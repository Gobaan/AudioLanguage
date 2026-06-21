import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { AdminScenePage } from './admin/AdminScenePage';
import { AdminValidationApp } from './admin/AdminValidationApp';
import { UserHistoryApp } from './admin/UserHistoryApp';
import { DebugAudioLessonPlayer } from './DebugAudioLessonPlayer';
import { DebugPreloaderPage } from './DebugPreloaderPage';
import { DebugSpeechBubbleEditorPage } from './DebugSpeechBubbleEditorPage';
import { DebugSpeechBubblePage } from './DebugSpeechBubblePage';
import { DebugTransferTutorialPage } from './DebugTransferTutorialPage';
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
  if (pathname === '/history') return <UserHistoryApp />;
  if (pathname === '/scene') return <AdminScenePage />;
  if (pathname === '/gobi-home') return <LanguageSelectionApp />;
  if (pathname === '/debug/audio') return <DebugAudioLessonPlayer />;
  if (pathname === '/debug/preloader') return <DebugPreloaderPage />;
  if (pathname === '/debug/speech-bubble-editor') return <DebugSpeechBubbleEditorPage />;
  if (pathname === '/debug/speech-bubbles') return <DebugSpeechBubblePage />;
  if (pathname === '/debug/transfer-tutorial') return <DebugTransferTutorialPage />;
  if (pathname === '/debug/recording-countdown') return <RecordingCountdownPreview />;
  if (pathname === '/learn') return <TravellerMvpApp />;
  return <div className="frame-placeholder" aria-label="Page unavailable" />;
}
