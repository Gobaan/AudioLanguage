import { useEffect, useRef, useState } from 'react';

import { fetchGoogleAuthConfig } from '../api/auth';

type GoogleAccountLinkProps = {
  participantId: string | null;
  authEmail?: string | null;
  authStatus: 'idle' | 'linking' | 'linked' | 'error';
  authError: string | null;
  onCredential: (credential: string) => void;
};

type GoogleCredentialResponse = {
  credential?: string;
};

type GoogleAccountsId = {
  initialize: (options: {
    client_id: string;
    callback: (response: GoogleCredentialResponse) => void;
  }) => void;
  renderButton: (
    element: HTMLElement,
    options: {
      theme: 'outline';
      size: 'large';
      type: 'standard';
      text: 'continue_with';
      shape: 'rectangular';
    },
  ) => void;
};

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: GoogleAccountsId;
      };
    };
  }
}

let googleIdentityScriptPromise: Promise<void> | null = null;

export function GoogleAccountLink({
  participantId,
  authEmail,
  authStatus,
  authError,
  onCredential,
}: GoogleAccountLinkProps) {
  const buttonRef = useRef<HTMLDivElement | null>(null);
  const [clientId, setClientId] = useState<string | null>(null);
  const [configState, setConfigState] = useState<'loading' | 'disabled' | 'ready' | 'error'>('loading');
  const [configError, setConfigError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;
    fetchGoogleAuthConfig()
      .then((config) => {
        if (!isCurrent) return;
        if (!config.enabled || !config.clientId) {
          setConfigState('disabled');
          return;
        }
        setClientId(config.clientId);
        setConfigState('ready');
      })
      .catch(() => {
        if (isCurrent) {
          setConfigError('Restart the updated backend to enable account sync.');
          setConfigState('error');
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  useEffect(() => {
    if (!participantId || !clientId || configState !== 'ready' || !buttonRef.current) {
      return;
    }

    let isCurrent = true;
    loadGoogleIdentityScript()
      .then(() => {
        if (!isCurrent || !buttonRef.current || !window.google?.accounts?.id) {
          return;
        }
        buttonRef.current.replaceChildren();
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => {
            if (response.credential) {
              onCredential(response.credential);
            }
          },
        });
        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: 'outline',
          size: 'large',
          type: 'standard',
          text: 'continue_with',
          shape: 'rectangular',
        });
      })
      .catch(() => {
        if (isCurrent) {
          setConfigError('Google sign-in could not load in this browser.');
          setConfigState('error');
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [clientId, configState, onCredential, participantId]);

  if (configState === 'disabled' || configState === 'loading' || !participantId) {
    return null;
  }

  return (
    <section className="google-account-link" aria-label="Account sync">
      <div>
        <strong>{authStatus === 'linked' ? 'Sync on' : 'Sync across devices'}</strong>
        <span>{authEmail ? authEmail : 'Use Google to keep your learning queue on every device.'}</span>
      </div>
      {configState === 'ready' ? <div ref={buttonRef} aria-busy={authStatus === 'linking'} /> : null}
      {authStatus === 'linking' ? <span className="google-account-status">Linking...</span> : null}
      {authError ? <span className="google-account-error">{authError}</span> : null}
      {configState === 'error' ? (
        <span className="google-account-error">{configError ?? 'Google sign-in is unavailable.'}</span>
      ) : null}
    </section>
  );
}

function loadGoogleIdentityScript(): Promise<void> {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }
  if (googleIdentityScriptPromise) {
    return googleIdentityScriptPromise;
  }

  const existingScript = document.getElementById('google-identity-services');
  if (existingScript) {
    googleIdentityScriptPromise = new Promise((resolve, reject) => {
      existingScript.addEventListener('load', () => resolve(), { once: true });
      existingScript.addEventListener('error', () => reject(new Error('Failed to load Google Identity Services')), {
        once: true,
      });
    });
    return googleIdentityScriptPromise;
  }

  googleIdentityScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.id = 'google-identity-services';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google Identity Services'));
    document.head.appendChild(script);
  });
  return googleIdentityScriptPromise;
}
