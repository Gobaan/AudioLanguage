import { useCallback, useEffect, useState } from 'react';

import { linkGoogleAccount, type GoogleLinkResponse } from '../api/auth';
import { fetchSuggestedParticipantName } from '../api/validation';
import { participantFromUrl } from './urlParams';

export const PARTICIPANT_STORAGE_KEY = 'audio-language-participant';
const GOOGLE_ACCOUNT_STORAGE_KEY = 'audio-language-google-account';

type GoogleAccount = {
  participantId: string;
  email?: string | null;
  name?: string | null;
};

export type ParticipantAuthStatus = 'idle' | 'linking' | 'linked' | 'error';

function saveParticipantId(participantId: string) {
  localStorage.setItem(PARTICIPANT_STORAGE_KEY, participantId);
}

function fallbackParticipantId(): string {
  return `Learner-${Math.floor(1000 + Math.random() * 9000)}`;
}

export function useParticipantId() {
  const [participantId, setParticipantId] = useState<string | null>(null);
  const [googleAccount, setGoogleAccount] = useState<GoogleAccount | null>(storedGoogleAccount);
  const [authStatus, setAuthStatus] = useState<ParticipantAuthStatus>(() =>
    storedGoogleAccount() ? 'linked' : 'idle',
  );
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;
    const urlParticipant = participantFromUrl();
    if (urlParticipant) {
      saveParticipantId(urlParticipant);
      setParticipantId(urlParticipant);
      return () => {
        isCurrent = false;
      };
    }

    const storedParticipant = localStorage.getItem(PARTICIPANT_STORAGE_KEY);
    if (storedParticipant) {
      setParticipantId(storedParticipant);
      return () => {
        isCurrent = false;
      };
    }

    const storedAccount = storedGoogleAccount();
    if (storedAccount) {
      saveParticipantId(storedAccount.participantId);
      setParticipantId(storedAccount.participantId);
      return () => {
        isCurrent = false;
      };
    }

    fetchSuggestedParticipantName()
      .then((participant) => {
        if (!isCurrent) return;
        saveParticipantId(participant.participantId);
        setParticipantId(participant.participantId);
      })
      .catch(() => {
        if (!isCurrent) return;
        const fallbackParticipant = fallbackParticipantId();
        saveParticipantId(fallbackParticipant);
        setParticipantId(fallbackParticipant);
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  const linkGoogleCredential = useCallback(
    async (credential: string) => {
      if (!participantId) {
        return;
      }

      setAuthStatus('linking');
      setAuthError(null);
      try {
        const linkedAccount = await linkGoogleAccount({
          credential,
          localParticipantId: participantId,
        });
        const nextAccount = googleAccountFromResponse(linkedAccount);
        saveParticipantId(nextAccount.participantId);
        saveGoogleAccount(nextAccount);
        setParticipantId(nextAccount.participantId);
        setGoogleAccount(nextAccount);
        setAuthStatus('linked');
      } catch (error) {
        setAuthStatus('error');
        setAuthError(googleAuthErrorMessage(error));
      }
    },
    [participantId],
  );

  return {
    participantId,
    authStatus,
    authError,
    googleAccount,
    linkGoogleCredential,
  };
}

function storedGoogleAccount(): GoogleAccount | null {
  try {
    const raw = localStorage.getItem(GOOGLE_ACCOUNT_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as Partial<GoogleAccount>;
    if (typeof parsed.participantId !== 'string' || !parsed.participantId) {
      return null;
    }
    return {
      participantId: parsed.participantId,
      email: typeof parsed.email === 'string' ? parsed.email : null,
      name: typeof parsed.name === 'string' ? parsed.name : null,
    };
  } catch {
    return null;
  }
}

function saveGoogleAccount(account: GoogleAccount) {
  localStorage.setItem(GOOGLE_ACCOUNT_STORAGE_KEY, JSON.stringify(account));
}

function googleAccountFromResponse(response: GoogleLinkResponse): GoogleAccount {
  return {
    participantId: response.participantId,
    email: response.email ?? null,
    name: response.name ?? null,
  };
}

function googleAuthErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return 'Could not link Google account.';
}
