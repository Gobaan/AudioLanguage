import { useEffect, useState } from 'react';

import { fetchLanguages, type LanguageSummary } from '../api/languages';

export function useLanguageOptions() {
  const [languageOptions, setLanguageOptions] = useState<LanguageSummary[]>([]);

  useEffect(() => {
    let isCurrent = true;
    fetchLanguages()
      .then((payload) => {
        if (!isCurrent) return;
        setLanguageOptions(payload);
      })
      .catch(() => {
        if (!isCurrent) return;
        setLanguageOptions([]);
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  return languageOptions;
}
