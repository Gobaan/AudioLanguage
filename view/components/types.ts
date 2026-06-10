export type LessonMode = 'traveller' | 'tv' | 'practice';

export type ModeOption = {
  id: LessonMode | string;
  label: string;
  ariaLabel?: string;
};

export type SceneFrameData = {
  id: string;
  frameNumber?: number;
  lineIndex?: number;
  imageUrl?: string;
  alt?: string;
  title?: string;
  speaker?: string;
  text?: string;
  originalText?: string;
  transliteration?: string;
  audioText?: string;
  lineType?: string;
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

export type BackwardBuildPrompt = {
  id: string;
  text: string;
  audioUrl?: string | null;
  audioText?: string | null;
  mic?: LessonStep['mic'];
};

export type ProgressMetric = {
  label: string;
  value: string | number;
};

export type AudioButtonText = {
  playLabel: string;
  playingLabel: string;
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
  | 'similar_phrase_contrast';

export type LessonStep = {
  id: string;
  type: LessonStepType;
  component: string;
  frameId?: string | null;
  frameMode?: 'single' | 'strip' | 'neutral' | string;
  displayText?: string;
  audio?: {
    url?: string | null;
    audioText?: string | null;
    autoplay: boolean;
    replayable: boolean;
    playBeforeMic?: boolean;
  };
  mic?: {
    enabled: boolean;
    record: boolean;
    startsAfterAudio?: boolean;
    expectedText?: string;
    expectedTransliteration?: string;
    scoring: 'none' | 'deferred' | string;
    continueOnRecord?: boolean;
    blockingFeedback?: boolean;
  };
  props: Record<string, unknown>;
};

export type Lesson = {
  id: string;
  language: string;
  title: string;
  mode?: string;
  stage?: string;
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
  scene_set?: string;
  lesson_tabs?: Array<{
    id: string;
    label: string;
  }>;
  lessons: Lesson[];
};
