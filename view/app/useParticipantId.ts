import { useEffect, useState } from 'react';

import { fetchSuggestedParticipantName } from '../api/validation';
import { participantFromUrl } from './urlParams';

export const PARTICIPANT_STORAGE_KEY = 'audio-language-participant';

function saveParticipantId(participantId: string) {
  localStorage.setItem(PARTICIPANT_STORAGE_KEY, participantId);
}

function fallbackParticipantId(): string {
  return `Learner-${Math.floor(1000 + Math.random() * 9000)}`;
}

export function useParticipantId() {
  const [participantId, setParticipantId] = useState<string | null>(null);

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

  return participantId;
}
