import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { AdminValidationApp } from './AdminValidationApp';
import { TravellerMvpApp } from './TravellerMvpApp';
import './styles.css';

const root = document.querySelector('#root');

if (!root) {
  throw new Error('Missing #root element');
}

createRoot(root).render(
  <StrictMode>
    {window.location.pathname === '/admin/validation' ? <AdminValidationApp /> : <TravellerMvpApp />}
  </StrictMode>,
);
