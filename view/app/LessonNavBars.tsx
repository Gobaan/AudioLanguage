import type { LanguageSummary } from '../api/languages';
import type { LessonTab } from './useLessonLoader';

type LessonNavBarsProps = {
  languageOptions: LanguageSummary[];
  language: string;
  lessonTabs: LessonTab[];
  lessonPage: string;
  onSelectLanguage: (language: string) => void;
  onSelectLessonPage: (lessonPage: string) => void;
};

export function LessonNavBars({
  languageOptions,
  language,
  lessonTabs,
  lessonPage,
  onSelectLanguage,
  onSelectLessonPage,
}: LessonNavBarsProps) {
  const options =
    languageOptions.length > 0
      ? languageOptions
      : [{ id: language, display_name: language, description: '', scene_sets: ['mvp'] }];

  return (
    <>
      <nav className="language-switcher" aria-label="Language">
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            className={language === option.id ? 'active' : ''}
            onClick={() => onSelectLanguage(option.id)}
          >
            {option.display_name}
          </button>
        ))}
      </nav>
      <nav className="lesson-switcher" aria-label="Lesson test pages">
        {lessonTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={lessonPage === tab.id ? 'active' : ''}
            onClick={() => onSelectLessonPage(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </>
  );
}
