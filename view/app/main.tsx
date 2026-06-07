import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { AdminValidationApp } from './AdminValidationApp';
import { LanguageSelectionApp } from './LanguageSelectionApp';
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
  if (pathname === '/admin/validation') return <AdminValidationApp />;
  if (pathname === '/learn') return <TravellerMvpApp />;
  return <LanguageSelectionApp />;
}
