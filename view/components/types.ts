export type LessonMode = 'traveller' | 'tv' | 'practice';

export type ModeOption = {
  id: LessonMode | string;
  label: string;
  ariaLabel?: string;
};

export type SceneFrameData = {
  id: string;
  imageUrl?: string;
  alt?: string;
  title?: string;
  speaker?: string;
};

export type ChoiceOption = {
  id: string;
  label: string;
  isCorrect?: boolean;
};

export type Chunk = {
  id: string;
  text: string;
  meaning?: string;
  audioUrl?: string;
};

export type ProgressMetric = {
  label: string;
  value: string | number;
};

export type AudioButtonText = {
  playLabel: string;
  playingLabel: string;
};

export type MicPromptText = {
  prompt: string;
  listeningLabel: string;
  startLabel: string;
};

export type TranslationRevealText = {
  revealLabel: string;
};
