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

export type LessonStepType =
  | 'scene_setup'
  | 'target_audio'
  | 'broad_meaning_guess'
  | 'translation_reveal'
  | 'audio_replay'
  | 'repeat_with_mic'
  | 'backward_build'
  | 'production_prompt'
  | 'scene_recall'
  | 'transfer_scene'
  | 'micro_note'
  | 'mini_roleplay'
  | 'audio_only_recognition'
  | 'different_speaker'
  | 'natural_speed'
  | 'similar_phrase_contrast'
  | 'schedule_review';

export type LessonStep = {
  id: string;
  type: LessonStepType;
  component: string;
  props: Record<string, unknown>;
};

export type Lesson = {
  id: string;
  language: string;
  title: string;
  mode?: string;
  stage?: string;
  player_component: string;
  target: {
    id: string;
    text: string;
    transliteration: string;
    meaning: string;
  };
  frames: SceneFrameData[];
  steps: LessonStep[];
};

export type LessonListResponse = {
  language: string;
  display_name: string;
  lessons: Lesson[];
};
