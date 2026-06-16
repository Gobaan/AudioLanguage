import { useEffect, useState } from 'react';
import { fetchLanguages, type LanguageSummary } from '../api/languages';
import { clearLocalValidationSessions } from '../api/validation';
import { isLocalHost } from './urlParams';
import { languageAudioDebugLink, languageLessonLink } from './lessonLinks';
import { PARTICIPANT_STORAGE_KEY } from './useParticipantId';

type LoadState = 'loading' | 'ready' | 'error';
type ClearState = 'idle' | 'clearing' | 'cleared' | 'error';

export function LanguageSelectionApp() {
  const [languages, setLanguages] = useState<LanguageSummary[]>([]);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [clearState, setClearState] = useState<ClearState>('idle');

  useEffect(() => {
    let isCurrent = true;
    fetchLanguages()
      .then((payload) => {
        if (!isCurrent) return;
        setLanguages(payload);
        setLoadState('ready');
      })
      .catch(() => {
        if (!isCurrent) return;
        setLoadState('error');
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  if (loadState === 'loading') {
    return <div className="frame-placeholder" aria-label="Loading languages" />;
  }

  if (loadState === 'error') {
    return (
      <section className="language-selection-page" aria-label="Language selection">
        <h1>Choose a language</h1>
        <p>Language options are unavailable.</p>
      </section>
    );
  }

  return (
    <section className="language-selection-page" aria-label="Language selection">
      <header>
        <span>Audio Language</span>
        <h1>Choose a language</h1>
      </header>
      <div className="language-card-grid">
        {languages.map((language) => (
          <article className="language-card" key={language.id}>
            <h2>{language.display_name}</h2>
            <p>{language.description || 'Starter speaking scenes.'}</p>
            <div className="language-card-actions">
              <a href={languageLessonLink(language.id, 'mvp')}>Original</a>
              {isLocalHost() ? <a href={languageAudioDebugLink(language.id, 'mvp')}>Audio debug</a> : null}
              {language.scene_sets.includes('delayed') ? (
                <>
                  <a href={languageLessonLink(language.id, 'delayed')}>Delayed</a>
                  {isLocalHost() ? <a href={languageAudioDebugLink(language.id, 'delayed')}>Delayed audio</a> : null}
                </>
              ) : null}
            </div>
          </article>
        ))}
      </div>
      {isLocalHost() ? (
        <nav className="local-app-links" aria-label="Local app links">
          <a href="/admin/validation">Admin</a>
          <button type="button" className="app-link-button danger" disabled={clearState === 'clearing'} onClick={clearAllLocalFiles}>
            {clearState === 'clearing' ? 'Clearing...' : 'Clear all files'}
          </button>
          {clearState === 'cleared' ? <span>Cleared</span> : null}
          {clearState === 'error' ? <span>Clear failed</span> : null}
        </nav>
      ) : null}
    </section>
  );

  async function clearAllLocalFiles() {
    const confirmed = window.confirm('Delete all local validation recordings, scores, events, and sessions?');
    if (!confirmed) {
      return;
    }

    setClearState('clearing');
    try {
      await clearLocalValidationSessions();
      localStorage.removeItem(PARTICIPANT_STORAGE_KEY);
      setClearState('cleared');
    } catch {
      setClearState('error');
    }
  }
}
