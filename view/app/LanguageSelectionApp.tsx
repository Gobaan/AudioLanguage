import { useEffect, useMemo, useState } from 'react';
import { fetchLanguages, type LanguageSummary } from '../api/languages';
import { isLocalHost, participantFromUrl } from './urlParams';

type LoadState = 'loading' | 'ready' | 'error';

export function LanguageSelectionApp() {
  const [languages, setLanguages] = useState<LanguageSummary[]>([]);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const participant = useMemo(() => participantFromUrl(), []);

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
              <a href={lessonLink(language.id, participant, 'mvp')}>Original</a>
              {language.scene_sets.includes('delayed') ? (
                <a href={lessonLink(language.id, participant, 'delayed')}>Delayed</a>
              ) : null}
            </div>
          </article>
        ))}
      </div>
      {isLocalHost() ? (
        <nav className="local-app-links" aria-label="Local app links">
          <a href="/admin/validation">Admin</a>
        </nav>
      ) : null}
    </section>
  );
}

function lessonLink(language: string, participant: string | null, sceneSet: 'mvp' | 'delayed'): string {
  const params = new URLSearchParams({ language, lesson: 'hello' });
  if (sceneSet !== 'mvp') params.set('scene_set', sceneSet);
  if (participant) params.set('participant', participant);
  return `/learn?${params.toString()}`;
}
