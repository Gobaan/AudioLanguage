const state = {
  languages: [],
  language: 'en',
  session: null,
  cardIndex: 0,
  activeLineIndex: 0,
  selectedChoiceIndex: null,
  isAnswerRevealed: false,
  showPronunciation: false,
  isPlaying: false,
  isListening: false,
  isTranscribing: false,
  heldVisual: '',
  speechTranscript: '',
  heardRhythm: '',
  heardBeats: [],
  speechScore: null,
  speechMatched: null,
  speechStatus: '',
  turnPrompt: '',
  expectedPronunciation: '',
  expectedRhythm: '',
  rhythmScore: null,
  rhythmFeedback: '',
  phoneAvailable: false,
  phoneScore: null,
  phoneFeedback: '',
  learnerPhones: [],
  targetPhones: [],
  communication: null,
  copiedPrompt: false,
  lastRecordingUrl: '',
  lastRecordingFilename: '',
  hasWatchedDialogue: false,
  hasAutoplayedDialogue: false,
  isAutoplayingDialogue: false,
};

const PROMPT_AUDIO = {
  theySay: '/audio/prompts/opening.mp3',
  youSay: '/audio/prompts/user_says.mp3',
};

const TEMPLATE_IDS = {
  guidedDialogueReplay: 'guided-dialogue-replay-v1',
};

const TEMPLATE_SUPPORT_DEFAULTS = {
  [TEMPLATE_IDS.guidedDialogueReplay]: {
    show_visual: true,
    play_full_dialogue_first: true,
    autoplay_full_dialogue: true,
    replay_until_learner_turn: true,
    show_target_text_after_attempt: true,
    show_examples_before_attempt: false,
    show_transliteration_after_failure: true,
  },
};

const preloadedImages = new Map();

const RECORDING_POLICY = {
  minMs: 800,
  shortMaxMs: 2500,
  baseMaxMs: 1800,
  wordMs: 650,
  hardMaxMs: 6500,
  silenceMs: 700,
  silenceThreshold: 0.018,
};

const RHYTHM_OVERRIDES = {
  'Vanakkam! Eppadi irukkireergal?': 'Vanakkam | Eppadi | irukkireergal',
  'En peyar Anna.': 'En | peyar | Anna',
  'Methuvaga solla mudiyuma?': 'Methuvaga | solla | mudiyuma',
};

const app = document.querySelector('#app');

init();

async function init() {
  try {
    state.languages = await fetchJson('/api/languages');
    const savedLanguage = window.localStorage.getItem('audio-language-selected');
    if (savedLanguage && state.languages.some(language => language.id === savedLanguage)) {
      state.language = savedLanguage;
    } else if (!state.languages.some(language => language.id === state.language)) {
      state.language = state.languages[0]?.id || 'en';
    }
    renderLanguageSelect();
  } catch (error) {
    renderError(error.message);
  }
}

async function loadSession(language) {
  state.language = language;
  window.localStorage.setItem('audio-language-selected', language);
  state.session = await fetchJson(`/api/languages/${encodeURIComponent(language)}/session`);
  preloadSessionImages(state.session);
  state.cardIndex = 0;
  resetCardState();
  render();
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load ${url}`);
  return response.json();
}

function render() {
  if (!state.session) {
    renderLanguageSelect();
    return;
  }

  if (state.cardIndex >= state.session.cards.length) {
    renderComplete();
    return;
  }

  const card = currentCard();
  app.innerHTML = `
    <section class="${cardShellClass(card)}">
      ${renderHeader()}
      ${renderIntentionHero(card)}
      ${renderScene(card)}
      ${renderCardBody(card)}
      ${renderControls(card)}
    </section>
  `;

  bind('[data-action="play-dialogue"]', 'click', () => runPracticeTurn(card));
  bind('[data-action="watch-dialogue"]', 'click', () => watchDialogue(card));
  bind('[data-action="try-dialogue"]', 'click', () => tryDialogue(card));
  bind('[data-action="play-target"]', 'click', () => playTarget(card));
  bind('[data-action="play-target-slow"]', 'click', () => playTarget(card, 0.5));
  bind('[data-action="try-line"]', 'click', () => recordAndVerify(card));
  bind('[data-action="retry-speech"]', 'click', () => recordAndVerify(card));
  bind('[data-action="reveal"]', 'click', revealAnswer);
  bind('[data-action="toggle-pronunciation"]', 'click', togglePronunciation);
  bind('[data-action="copy-ai-prompt"]', 'click', () => copyAiPrompt(card));
  bind('[data-action="next"]', 'click', nextCard);
  bind('[data-action="previous"]', 'click', previousCard);

  document.querySelectorAll('[data-choice-index]').forEach(button => {
    button.addEventListener('click', () => chooseAnswer(Number(button.dataset.choiceIndex)));
  });

  maybeAutoplayDialogue(card);
}

function renderLanguageSelect() {
  app.innerHTML = `
    <section class="language-start">
      <div class="language-start-copy">
        <span>Choose a practice language</span>
        <h1>Audio Language</h1>
      </div>
      <div class="language-grid">
        ${state.languages.map(language => `
          <button class="language-card ${language.id === state.language ? 'selected' : ''}" data-language-id="${escapeHtml(language.id)}">
            <strong>${escapeHtml(language.display_name)}</strong>
            <small>${escapeHtml(language.id.toUpperCase())}</small>
          </button>
        `).join('')}
      </div>
    </section>
  `;

  document.querySelectorAll('[data-language-id]').forEach(button => {
    button.addEventListener('click', () => loadSession(button.dataset.languageId));
  });
}

function cardShellClass(card) {
  const classes = [
    'card-shell',
    `scene-${card.scene.domain || card.function.domain}`,
  ];
  if (state.isPlaying) classes.push('is-playing');
  if (state.isListening) classes.push('is-listening');
  if (state.isTranscribing) classes.push('is-checking');
  if (state.speechMatched === true) classes.push('is-success');
  if (state.speechMatched === false) classes.push('is-retry');
  return classes.map(escapeHtml).join(' ');
}

function renderHeader() {
  return '';
}

function renderIntentionHero(card) {
  const label = card.scene.domain || card.function.domain || 'scene';
  return `
    <section class="intention-hero">
      <h2>${escapeHtml(label.replaceAll('_', ' '))}</h2>
    </section>
  `;
}

function renderScene(card) {
  const imageUrl = activeVisual(card);
  const scene = card.scene;

  if (imageUrl) {
    return `
      <figure class="scene-art scene-frame" style="--scene-image: url('${escapeCssUrl(imageUrl)}')" aria-label="${escapeHtml(scene.description)}">
        ${renderTurnOverlay(card)}
      </figure>
    `;
  }

  return `
    <figure class="scene-art generated-scene" aria-label="${escapeHtml(scene.description)}">
      <div class="scene-sky"></div>
      <div class="scene-ground"></div>
      <div class="figure figure-a"></div>
      <div class="figure figure-b"></div>
      <div class="context-object"></div>
      <figcaption>
        <strong>${escapeHtml(scene.environment)}</strong>
        <span>${escapeHtml(scene.mood || scene.domain)}</span>
      </figcaption>
      ${renderTurnOverlay(card)}
    </figure>
  `;
}

function renderTurnOverlay(card) {
  if (state.isListening) {
    return `
      <div class="turn-overlay listening" aria-live="assertive">
        <span class="mic-dot"></span>
        <strong>Now you try</strong>
        <small>${escapeHtml(state.turnPrompt || listeningInstruction(card))}</small>
      </div>
    `;
  }

  if (state.turnPrompt) {
    return `
      <div class="turn-overlay ready" aria-live="assertive">
        <span class="ready-dot"></span>
        <strong>${escapeHtml(state.turnPrompt)}</strong>
      </div>
    `;
  }

  if (state.isPlaying) {
    return `
      <div class="turn-overlay playing" aria-live="polite">
        <span class="play-dot"></span>
        <strong>Listen</strong>
      </div>
    `;
  }

  if (state.isTranscribing) {
    return `
      <div class="turn-overlay checking" aria-live="polite">
        <span class="check-dot"></span>
        <strong>Checking</strong>
      </div>
    `;
  }

  return '';
}

function renderCardBody(card) {
  const content = [
    renderBeginnerExamples(card),
    renderChoices(card),
    renderFeedback(card),
    renderSpeechResult(),
    renderFailureRescue(card),
    renderDebugTools(card),
  ].join('');

  if (!content.trim()) return '';

  return `
    <section class="practice-panel">
      ${content}
    </section>
  `;
}

function renderBeginnerExamples(card) {
  const shouldShow = supportFor(card).show_examples_before_attempt || false;
  if (!shouldShow) return '';

  const examples = exampleResponsesFor(card).slice(0, 4);
  if (examples.length === 0) return '';

  return `
    <div class="example-card">
      <span>Try saying</span>
      <div class="example-row">
        ${examples.map(example => `<strong>${escapeHtml(example)}</strong>`).join('')}
      </div>
    </div>
  `;
}

function exampleResponsesFor(card) {
  const contractExamples = card.ai_scene_contract?.example_valid_responses || [];
  const targetExamples = card.target?.accepted_variants || [];
  const canonical = card.target?.canonical ? [card.target.canonical] : [];
  return [...new Set([...canonical, ...contractExamples, ...targetExamples])].filter(Boolean);
}

function renderPronunciationHelp(transliteration) {
  if (!transliteration) return '';

  return `
    <div class="pronunciation-help">
      <span>Rhythm</span>
      <strong class="rhythm-text">${escapeHtml(rhythmFor(transliteration))}</strong>
      <span>Phonetics</span>
      <strong class="target-translit">${escapeHtml(transliteration)}</strong>
    </div>
  `;
}

function renderChoices(card) {
  if (!card.choices?.length) return '';

  return `
    <div class="choices">
      ${card.choices.map((choice, index) => renderChoice(choice, index)).join('')}
    </div>
  `;
}

function renderChoice(choice, index) {
  const isSelected = state.selectedChoiceIndex === index;
  const hasAnswered = state.selectedChoiceIndex !== null;
  const correctnessClass = hasAnswered && choice.is_correct ? 'correct' : hasAnswered && isSelected ? 'incorrect' : '';

  return `
    <button class="choice ${isSelected ? 'selected' : ''} ${correctnessClass}" data-choice-index="${index}">
      <span>${escapeHtml(choice.text || choice.label)}</span>
      ${choice.transliteration ? `<small>${escapeHtml(choice.transliteration)}</small>` : ''}
    </button>
  `;
}

function renderDetailsDrawer(card) {
  const lines = card.dialogue.lines || [];

  if (!canShowTargetSupport()) {
    return `
      <details class="dialogue-lines">
        <summary>Details</summary>
        <p class="muted">Transcript and meaning unlock after you try.</p>
      </details>
    `;
  }

  return `
    <details class="dialogue-lines">
      <summary>Details</summary>
      <div class="meaning-note">
        <span>Meaning check</span>
        <strong>${escapeHtml(card.target.display_meaning)}</strong>
      </div>
      ${lines.length ? `
        <div class="dialogue-transcript">
          <span>Transcript</span>
        </div>
      ` : ''}
      ${lines.map(line => `
        <div class="dialogue-line ${line.is_learner_target ? 'learner-line' : ''}">
          <span>${escapeHtml(roleLabel(line.speaker_role))}</span>
          <div>
            <strong>${escapeHtml(line.text || '[visual action]')}</strong>
            ${line.transliteration ? `<small>${escapeHtml(line.transliteration)}</small>` : ''}
          </div>
        </div>
      `).join('')}
    </details>
  `;
}

function renderFeedback(card) {
  if (state.selectedChoiceIndex === null || !card.choices?.length) return '';

  const choice = card.choices[state.selectedChoiceIndex];
  return `
    <div class="feedback ${choice.is_correct ? 'good' : 'bad'}">
      <strong>${choice.is_correct ? 'Fits the scene' : 'Not this moment'}</strong>
      ${choice.why ? `<p>${escapeHtml(choice.why)}</p>` : ''}
    </div>
  `;
}

function renderSpeechResult() {
  if (!state.speechStatus) return '';

  const scoreText = state.speechScore === null ? '' : ` (${Math.round(state.speechScore * 100)}%)`;
  const className = state.speechMatched === null ? '' : state.speechMatched ? 'good' : 'bad';

  return `
    <div class="feedback ${className}" aria-live="polite">
      <strong>${escapeHtml(state.speechStatus)}${scoreText}</strong>
      ${state.speechTranscript ? `<p class="muted">Heard as: ${escapeHtml(state.speechTranscript)}</p>` : ''}
      ${renderCommunicationFeedback()}
    </div>
  `;
}

function renderCommunicationFeedback() {
  if (!state.communication) return '';

  return `
    <div class="communication-result">
      <span>${escapeHtml(state.communication.status || 'heard')}</span>
      <p>${escapeHtml(state.communication.message || '')}</p>
      ${state.communication.partner_response ? `
        <strong class="partner-response">${escapeHtml(state.communication.partner_response)}</strong>
      ` : ''}
    </div>
  `;
}

function renderFailureRescue(card) {
  if (state.speechMatched !== false) return '';
  if (!supportFor(card).show_transliteration_after_failure) return '';

  const line = targetLine(card);
  const transliteration = line?.transliteration || card.target?.transliteration || '';
  if (!transliteration) return '';

  return `
    <div class="rescue-card">
      <span>Pronunciation rescue</span>
      <strong>${escapeHtml(transliteration)}</strong>
    </div>
  `;
}

function renderDebugTools(card) {
  if (!isLocalDebugHost()) return '';
  if (!state.lastRecordingUrl && !state.speechTranscript) return '';

  return `
    <details class="debug-tools" open>
      <summary>Debug tools</summary>
      <div class="debug-tool-grid">
        ${state.lastRecordingUrl ? `
          <a class="text-button" href="${escapeHtml(state.lastRecordingUrl)}" download="${escapeHtml(state.lastRecordingFilename || 'recording.webm')}">
            Download recording
          </a>
        ` : ''}
        ${state.speechTranscript ? `
          <div class="debug-readout">
            <span>Displayed transcript</span>
            <code>${escapeHtml(state.speechTranscript)}</code>
          </div>
        ` : ''}
        ${card.id ? `
          <div class="debug-readout">
            <span>Card</span>
            <code>${escapeHtml(card.id)}</code>
          </div>
        ` : ''}
      </div>
    </details>
  `;
}

function renderPhoneShape() {
  if (!state.phoneAvailable) {
    return '<strong>Phone recognizer unavailable</strong>';
  }

  return `
    <div class="phone-compare">
      <div>
        <small>Target phonemes</small>
        <div class="phone-row">${renderPhoneChips(state.targetPhones)}</div>
        <code class="phone-sequence">${escapeHtml(phoneSequence(state.targetPhones))}</code>
      </div>
      <div>
        <small>Your phonemes</small>
        <div class="phone-row">${renderPhoneChips(state.learnerPhones)}</div>
        <code class="phone-sequence">${escapeHtml(phoneSequence(state.learnerPhones))}</code>
      </div>
      <small class="rhythm-inline">Recognized by Allosaurus from audio. These are approximate IPA-like phones, useful for comparing your sound shape to the generated target.</small>
    </div>
  `;
}

function renderPhoneChips(phones) {
  if (!Array.isArray(phones) || phones.length === 0) {
    return '<span class="phone-chip missing">none</span>';
  }
  return phones.map(phone => `<span class="phone-chip">${escapeHtml(phone)}</span>`).join('');
}

function phoneSequence(phones) {
  if (!Array.isArray(phones) || phones.length === 0) return 'none';
  return phones.join(' ');
}

function renderHeardSoundShape() {
  return `
    <div class="heard-shape">
      ${renderBeatChips(state.heardBeats)}
      ${state.heardRhythm ? `<small class="rhythm-inline">${escapeHtml(state.heardRhythm)}</small>` : ''}
    </div>
  `;
}

function renderBeatChips(beats) {
  if (!Array.isArray(beats) || beats.length === 0) {
    return '<div class="beat-row"><span class="beat-chip quiet">no clear beats</span></div>';
  }

  return `
    <div class="beat-row" aria-label="Detected loud and soft beats">
      ${beats.map(beat => `
        <span class="beat-chip ${beat.loud ? 'loud' : 'quiet'}" title="strength ${Math.round(Number(beat.strength || 0) * 100)}%">
          ${escapeHtml(beat.label || 'da')}
        </span>
      `).join('')}
    </div>
  `;
}

function renderControls(card) {
  if (isGuidedDialogueReplay(card)) {
    return renderGuidedDialogueControls(card);
  }

  const hasSceneAudio = scenePlaybackSteps(card).some(step => step.url);
  const targetAudio = targetLine(card)?.audio;
  const isBusy = state.isPlaying || state.isListening || state.isTranscribing;
  const shouldShowReveal = card.mode !== 'listen' && !card.ai_scene_contract && !state.isAnswerRevealed;
  const canShowPronunciation = canShowTargetSupport() && card.target.transliteration;
  const canTryLine = card.mode !== 'listen';
  const tryLabel = card.ai_scene_contract ? 'Start Roleplay' : 'Try Line';

  return `
    <footer class="controls">
      <button class="icon-button" data-action="previous" ${state.cardIndex === 0 ? 'disabled' : ''} aria-label="Previous card">‹</button>
      ${hasSceneAudio ? `<button class="text-button" data-action="play-dialogue" ${isBusy ? 'disabled' : ''}>Play Scene</button>` : ''}
      ${targetAudio ? `<button class="text-button" data-action="play-target" ${isBusy ? 'disabled' : ''}>Play Target</button>` : ''}
      ${canTryLine ? `<button class="text-button primary" data-action="try-line" ${isBusy ? 'disabled' : ''}>${tryLabel}</button>` : ''}
      ${shouldShowReveal ? '<button class="text-button primary" data-action="reveal">Reveal</button>' : ''}
      ${canShowPronunciation ? `<button class="text-button" data-action="toggle-pronunciation">${state.showPronunciation ? 'Hide Mouth Help' : 'Mouth Help'}</button>` : ''}
      <button class="icon-button" data-action="next" aria-label="Next card">›</button>
    </footer>
  `;
}

function renderGuidedDialogueControls(card) {
  const isBusy = state.isPlaying || state.isListening || state.isTranscribing;
  const hasNextCard = state.cardIndex < state.session.cards.length - 1;
  const hasAttemptResult = state.speechMatched !== null;
  const canContinue = state.hasWatchedDialogue && hasAttemptResult && !isBusy;
  const canHearTarget = state.speechMatched === false && Boolean(targetLine(card)?.audio);
  const continueLabel = hasNextCard ? 'Continue' : 'Finish';
  const skipLabel = hasNextCard ? 'Skip' : 'Finish';

  if (!state.hasWatchedDialogue && (state.isAutoplayingDialogue || state.isPlaying)) {
    return `
      <footer class="controls guided-controls">
        <button class="text-button subtle" data-action="next">${skipLabel}</button>
      </footer>
    `;
  }

  return `
    <footer class="controls guided-controls">
      ${!state.hasWatchedDialogue ? '<button class="text-button" data-action="watch-dialogue">Watch Dialogue</button>' : ''}
      <button class="text-button primary" data-action="try-dialogue" ${isBusy || !state.hasWatchedDialogue ? 'disabled' : ''}>Try</button>
      ${canHearTarget ? `
        <button class="text-button" data-action="play-target" ${isBusy ? 'disabled' : ''}>Hear Line</button>
        <button class="text-button" data-action="play-target-slow" ${isBusy ? 'disabled' : ''}>Hear Slow</button>
      ` : ''}
      ${canContinue ? `<button class="text-button" data-action="next">${continueLabel}</button>` : ''}
      ${!canContinue ? `<button class="text-button subtle" data-action="next" ${isBusy ? 'disabled' : ''}>${skipLabel}</button>` : ''}
      ${!state.hasWatchedDialogue ? '<span class="control-hint">Watch once, then try your part.</span>' : ''}
    </footer>
  `;
}

function firstVisual(card) {
  return card.dialogue.lines?.find(line => line.visual)?.visual || null;
}

function preloadSessionImages(session) {
  for (const card of session?.cards || []) {
    for (const line of card.dialogue?.lines || []) {
      preloadImage(line.visual);
    }
  }
}

function preloadImage(url) {
  if (!url || preloadedImages.has(url)) return;
  const image = new Image();
  image.src = url;
  preloadedImages.set(url, image);
}

function activeVisual(card) {
  if ((state.isListening || state.isTranscribing) && state.heldVisual) {
    return state.heldVisual;
  }

  const lines = card.dialogue.lines || [];
  const activeLine = lines.find(line => Number(line.index) === state.activeLineIndex);
  return activeLine?.visual || firstVisual(card);
}

function targetLine(card) {
  return card.dialogue.lines?.find(line => line.is_learner_target || line.target_id === card.target_id);
}

function scenePlaybackSteps(card) {
  const lines = card.dialogue.lines || [];
  const targetIndex = lines.findIndex(line => line.is_learner_target || line.target_id === card.target_id);
  if (card.mode === 'listen') {
    return lines
      .filter(line => line.audio)
      .map(line => ({ url: line.audio, lineIndex: line.index }));
  }
  if (targetIndex === -1) return lines.filter(line => line.audio).map(line => ({ url: line.audio }));

  const previousLine = findPreviousSpokenLine(lines, targetIndex);
  const learnerLine = lines[targetIndex];
  const steps = [];

  if (previousLine?.audio) {
    steps.push({ url: previousLine.audio, lineIndex: previousLine.index });
  }

  if (!card.ai_scene_contract && learnerLine?.audio) {
    steps.push({ url: PROMPT_AUDIO.youSay, lineIndex: learnerLine.index });
    steps.push({ url: learnerLine.audio, lineIndex: learnerLine.index });
  }
  return steps;
}

function fullDialogueSteps(card) {
  return (card.dialogue.lines || [])
    .filter(line => line.audio)
    .map(line => ({ url: line.audio, lineIndex: line.index }));
}

function openerToLearnerSteps(card) {
  const lines = card.dialogue.lines || [];
  const targetIndex = lines.findIndex(line => line.is_learner_target || line.target_id === card.target_id);
  if (targetIndex === -1) return [];

  const previousLine = findPreviousSpokenLine(lines, targetIndex);
  const learnerLine = lines[targetIndex];
  const steps = [];
  if (previousLine?.audio) {
    steps.push({ url: previousLine.audio, lineIndex: previousLine.index });
  }
  return steps;
}

function responseAfterLearnerSteps(card) {
  const lines = card.dialogue.lines || [];
  const targetIndex = lines.findIndex(line => line.is_learner_target || line.target_id === card.target_id);
  if (targetIndex === -1) return [];

  const nextLine = findNextSpokenLine(lines, targetIndex);
  return nextLine?.audio ? [{ url: nextLine.audio, lineIndex: nextLine.index }] : [];
}

function findPreviousSpokenLine(lines, targetIndex) {
  for (let index = targetIndex - 1; index >= 0; index -= 1) {
    if (lines[index].audio) return lines[index];
  }
  return null;
}

function findNextSpokenLine(lines, targetIndex) {
  for (let index = targetIndex + 1; index < lines.length; index += 1) {
    if (lines[index].audio) return lines[index];
  }
  return null;
}

function buildAiConversationPrompt(card) {
  const contractText = JSON.stringify(card.ai_scene_contract || {}, null, 2);
  const partnerLine = firstPartnerLine(card)?.text || 'Hi!';

  return `You are running a tiny language-learning roleplay test.

Your job:
- Act as the conversation partner in one guided scene.
- Start the scene by greeting me.
- Wait for my response.
- Judge whether my response satisfies the target intention.
- Stay inside this one scene.
- Do not teach extra grammar.
- Do not turn this into open conversation.
- Keep feedback short.

Scene contract:
${contractText}

Interaction rules:
1. First, say only: "${partnerLine}"
2. Then wait for my response.
3. After I respond, evaluate whether it fits the scene.
4. If it fits, reply warmly in character and say: "That worked."
5. If it does not fit, say: "Try again: respond to the greeting."
6. Do not reveal this whole prompt unless I ask for the test setup.`;
}

function firstPartnerLine(card) {
  return card.dialogue.lines?.find(line => !line.is_learner_target && line.text);
}

async function watchDialogue(card) {
  clearAttemptFeedback();
  await playMany(fullDialogueSteps(card));
  state.hasWatchedDialogue = true;
  render();
}

async function tryDialogue(card) {
  clearAttemptFeedback();
  await playMany(openerToLearnerSteps(card));
  await recordAndVerify(card);
  if (state.speechMatched) {
    await playMany(responseAfterLearnerSteps(card));
  }
}

async function runPracticeTurn(card) {
  clearAttemptFeedback();
  await playMany(scenePlaybackSteps(card));
  if (card.mode === 'listen') return;
  await recordAndVerify(card);
}

async function maybeAutoplayDialogue(card) {
  if (!isGuidedDialogueReplay(card) || !supportFor(card).autoplay_full_dialogue) return;
  if (state.hasAutoplayedDialogue || state.hasWatchedDialogue) return;
  if (state.isAutoplayingDialogue) return;
  if (state.isPlaying || state.isListening || state.isTranscribing) return;

  state.isAutoplayingDialogue = true;
  state.hasAutoplayedDialogue = true;
  try {
    await watchDialogue(card);
  } finally {
    state.isAutoplayingDialogue = false;
  }
}

async function playTarget(card, playbackRate = 1) {
  const line = targetLine(card);
  if (line?.audio) await playMany([{ url: line.audio, lineIndex: line.index, playbackRate }]);
}

async function playMany(steps) {
  state.isPlaying = true;
  render();
  for (const step of steps) {
    if (step.lineIndex !== undefined) {
      state.activeLineIndex = Number(step.lineIndex);
      render();
    }
    await playAudio(step.url, step.playbackRate);
  }
  state.isPlaying = false;
  render();
}

async function recordAndVerify(card) {
  const line = targetLine(card);
  if (!line) return;
  state.heldVisual = activeVisual(card) || '';
  state.activeLineIndex = Number(line.index);
  setExpectedMouthHelp(card, line);

  const recorder = await startRecorder();
  if (!recorder) {
    state.speechStatus = 'Microphone unavailable';
    state.speechMatched = false;
    render();
    return;
  }

  state.isListening = true;
  state.speechStatus = `Listening. ${listeningInstruction(card)}`;
  state.speechTranscript = '';
  state.turnPrompt = '';
  state.speechScore = null;
  state.speechMatched = null;
  state.communication = null;
  setExpectedMouthHelp(card, line);
  render();

  const recordingBlob = await recorder.recordFor(recordingPolicyFor(card, line));
  setLastRecording(recordingBlob, card);
  state.isListening = false;
  state.isTranscribing = true;
  state.speechStatus = 'Checking';
  render();

  try {
    const result = await transcribeRecording(recordingBlob, card, line);
    state.speechTranscript = result.transcript_phonetic || result.transcript || '';
    state.heardRhythm = result.heard_rhythm || '';
    state.heardBeats = Array.isArray(result.heard_beats) ? result.heard_beats : [];
    state.speechScore = Number(result.score || 0);
    state.rhythmScore = Number(result.rhythm_score || 0);
    state.rhythmFeedback = result.rhythm_feedback || '';
    state.phoneAvailable = Boolean(result.phone_available);
    state.phoneScore = state.phoneAvailable ? Number(result.phone_score || 0) : null;
    state.phoneFeedback = result.phone_feedback || '';
    state.learnerPhones = Array.isArray(result.learner_phones) ? result.learner_phones : [];
    state.targetPhones = Array.isArray(result.target_phones) ? result.target_phones : [];
    state.communication = result.communication || null;
    state.speechMatched = Boolean(result.is_match);
    state.speechStatus = result.is_match ? 'Fits the scene' : 'Needs another try';
    setExpectedMouthHelp(card, line, result.expected_phonetic);
    if (result.is_match) state.isAnswerRevealed = true;
  } catch (error) {
    state.speechStatus = error.message || 'Could not check speech';
    state.speechMatched = false;
  } finally {
    state.isTranscribing = false;
    state.heldVisual = '';
    render();
  }
}

async function startRecorder() {
  if (!navigator.mediaDevices?.getUserMedia || !('MediaRecorder' in window)) return null;

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const recorder = new MediaRecorder(stream);
  const chunks = [];

  recorder.ondataavailable = event => {
    if (event.data.size > 0) chunks.push(event.data);
  };

  return {
    recordFor(policy) {
      return new Promise(resolve => {
        let audioContext = null;
        let analyser = null;
        let source = null;
        let animationFrame = null;
        let maxTimer = null;
        let stopped = false;
        let speechStarted = false;
        let quietSince = null;
        const startedAt = performance.now();
        const buffer = new Uint8Array(128);
        const options = normalizeRecordingPolicy(policy);

        function cleanup() {
          if (animationFrame !== null) cancelAnimationFrame(animationFrame);
          if (maxTimer !== null) clearTimeout(maxTimer);
          source?.disconnect();
          audioContext?.close().catch(() => {});
          stream.getTracks().forEach(track => track.stop());
        }

        function stopRecording() {
          if (stopped) return;
          stopped = true;
          if (recorder.state !== 'inactive') recorder.stop();
        }

        function monitorSilence() {
          if (!analyser || stopped) return;

          analyser.getByteTimeDomainData(buffer);
          const volume = rootMeanSquare(buffer);
          const elapsed = performance.now() - startedAt;
          const isSpeaking = volume >= options.silenceThreshold;

          if (isSpeaking) {
            speechStarted = true;
            quietSince = null;
          } else if (speechStarted && quietSince === null) {
            quietSince = performance.now();
          }

          const hasWaitedLongEnough = elapsed >= options.minMs;
          const hasPaused = quietSince !== null && performance.now() - quietSince >= options.silenceMs;
          if (speechStarted && hasWaitedLongEnough && hasPaused) {
            stopRecording();
            return;
          }

          animationFrame = requestAnimationFrame(monitorSilence);
        }

        recorder.onstop = () => {
          cleanup();
          resolve(new Blob(chunks, { type: recorder.mimeType || 'audio/webm' }));
        };
        recorder.start();
        maxTimer = setTimeout(stopRecording, options.maxMs);

        try {
          const AudioContextClass = window.AudioContext || window.webkitAudioContext;
          if (AudioContextClass) {
            audioContext = new AudioContextClass();
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            monitorSilence();
          }
        } catch {
          // Browser audio analysis is best-effort; the max timer still keeps recording bounded.
        }
      });
    },
  };
}

function recordingPolicyFor(card, line) {
  const words = wordCount(line?.transliteration || line?.text || card?.target?.canonical || '');
  if (words <= 2) {
    return {
      maxMs: RECORDING_POLICY.shortMaxMs,
      minMs: RECORDING_POLICY.minMs,
      silenceMs: RECORDING_POLICY.silenceMs,
      silenceThreshold: RECORDING_POLICY.silenceThreshold,
    };
  }

  const maxMs = clamp(
    RECORDING_POLICY.baseMaxMs + words * RECORDING_POLICY.wordMs,
    RECORDING_POLICY.shortMaxMs,
    RECORDING_POLICY.hardMaxMs,
  );

  return {
    maxMs,
    minMs: RECORDING_POLICY.minMs,
    silenceMs: RECORDING_POLICY.silenceMs,
    silenceThreshold: RECORDING_POLICY.silenceThreshold,
  };
}

function normalizeRecordingPolicy(policy) {
  if (typeof policy === 'number') {
    return {
      maxMs: policy,
      minMs: RECORDING_POLICY.minMs,
      silenceMs: RECORDING_POLICY.silenceMs,
      silenceThreshold: RECORDING_POLICY.silenceThreshold,
    };
  }

  return {
    maxMs: Number(policy?.maxMs || RECORDING_POLICY.shortMaxMs),
    minMs: Number(policy?.minMs || RECORDING_POLICY.minMs),
    silenceMs: Number(policy?.silenceMs || RECORDING_POLICY.silenceMs),
    silenceThreshold: Number(policy?.silenceThreshold || RECORDING_POLICY.silenceThreshold),
  };
}

function rootMeanSquare(buffer) {
  let sum = 0;
  for (const value of buffer) {
    const centered = (value - 128) / 128;
    sum += centered * centered;
  }
  return Math.sqrt(sum / buffer.length);
}

function wordCount(value) {
  return String(value || '').trim().split(/\s+/).filter(Boolean).length;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

async function transcribeRecording(recordingBlob, card, line) {
  const formData = new FormData();
  formData.append('file', recordingBlob, `${card.id}-attempt.webm`);
  formData.append('expected', line.text || card.target.canonical || '');
  formData.append('expected_alt', line.transliteration || card.target.transliteration || '');
  formData.append('language', card.language || state.language);
  formData.append('target_audio', line.audio || '');
  formData.append('target_meaning', card.target.display_meaning || card.function.name || '');
  formData.append('scene_id', card.scene.id || '');
  formData.append('function_id', card.function.id || '');
  formData.append('target_id', card.target.id || '');
  formData.append('scene_contract', JSON.stringify(card.ai_scene_contract || {}));

  const response = await fetch('/api/conversation/attempt', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) throw new Error('Transcription failed');
  return response.json();
}

function chunkLabelsForLine(line) {
  const value = line.transliteration || '';
  const rhythm = rhythmFor(value);
  return rhythm ? rhythm.split('|').map(chunk => chunk.trim()).filter(Boolean) : value.split(/\s+/).filter(Boolean);
}

function getAudioDuration(url) {
  return new Promise(resolve => {
    const audio = new Audio(url);
    audio.onloadedmetadata = () => resolve(Number.isFinite(audio.duration) ? audio.duration : 0);
    audio.onerror = () => resolve(0);
  });
}

function playAudio(url, playbackRate = 1) {
  return new Promise(resolve => {
    const audio = new Audio(url);
    audio.playbackRate = playbackRate;
    window.currentAudio = audio;
    audio.onended = resolve;
    audio.onerror = resolve;
    audio.play().catch(resolve);
  });
}

function listeningInstruction(card) {
  if (card.ai_scene_contract?.learner_intention) {
    return card.ai_scene_contract.learner_intention;
  }
  return card.expected_response ? `Try saying: ${card.expected_response}` : 'Say your line.';
}

function chooseAnswer(index) {
  state.selectedChoiceIndex = index;
  state.isAnswerRevealed = true;
  render();
}

function revealAnswer() {
  state.isAnswerRevealed = true;
  render();
}

async function copyAiPrompt(card) {
  const prompt = buildAiConversationPrompt(card);
  try {
    await navigator.clipboard.writeText(prompt);
  } catch {
    window.prompt('Copy this prompt', prompt);
  }
  state.copiedPrompt = true;
  render();
}

function togglePronunciation() {
  state.showPronunciation = !state.showPronunciation;
  render();
}

function nextCard() {
  stopCurrentAudio();
  state.cardIndex += 1;
  resetCardState();
  render();
}

function previousCard() {
  if (state.cardIndex === 0) return;
  stopCurrentAudio();
  state.cardIndex -= 1;
  resetCardState();
  render();
}

function stopCurrentAudio() {
  if (!window.currentAudio) return;
  window.currentAudio.pause();
  window.currentAudio.currentTime = 0;
  window.currentAudio = null;
}

function setLastRecording(recordingBlob, card) {
  clearLastRecording();
  state.lastRecordingUrl = URL.createObjectURL(recordingBlob);
  const extension = recordingExtension(recordingBlob.type);
  state.lastRecordingFilename = `${card.id || 'card'}-${Date.now()}.${extension}`;
}

function clearLastRecording() {
  if (state.lastRecordingUrl) {
    URL.revokeObjectURL(state.lastRecordingUrl);
  }
  state.lastRecordingUrl = '';
  state.lastRecordingFilename = '';
}

function resetCardState() {
  state.activeLineIndex = 0;
  state.selectedChoiceIndex = null;
  state.isAnswerRevealed = false;
  state.showPronunciation = false;
  state.isPlaying = false;
  state.isListening = false;
  state.isTranscribing = false;
  state.heldVisual = '';
  clearSpeechResult();
}

function clearSpeechResult() {
  clearAttemptFeedback();
  state.copiedPrompt = false;
  state.hasWatchedDialogue = false;
  state.hasAutoplayedDialogue = false;
  state.isAutoplayingDialogue = false;
}

function clearAttemptFeedback() {
  clearLastRecording();
  state.speechTranscript = '';
  state.heardRhythm = '';
  state.heardBeats = [];
  state.speechScore = null;
  state.rhythmScore = null;
  state.rhythmFeedback = '';
  state.phoneAvailable = false;
  state.phoneScore = null;
  state.phoneFeedback = '';
  state.learnerPhones = [];
  state.targetPhones = [];
  state.communication = null;
  state.speechMatched = null;
  state.speechStatus = '';
  state.expectedPronunciation = '';
  state.expectedRhythm = '';
}

function isLocalDebugHost() {
  return ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname);
}

function recordingExtension(mimeType) {
  if (mimeType.includes('mp4')) return 'mp4';
  if (mimeType.includes('ogg')) return 'ogg';
  if (mimeType.includes('wav')) return 'wav';
  return 'webm';
}

function currentCard() {
  return state.session.cards[state.cardIndex];
}

function isGuidedDialogueReplay(card) {
  return card.template_id === TEMPLATE_IDS.guidedDialogueReplay || supportFor(card).play_full_dialogue_first;
}

function supportFor(card) {
  return {
    ...(TEMPLATE_SUPPORT_DEFAULTS[card?.template_id] || {}),
    ...(card?.support || {}),
  };
}

function canShowTargetSupport() {
  return state.isAnswerRevealed || state.speechMatched === false || state.selectedChoiceIndex !== null;
}

function setExpectedMouthHelp(card, line, expectedPhonetic = '') {
  const expected = expectedPhonetic || line?.transliteration || card?.target?.transliteration || '';
  state.expectedPronunciation = expected;
  state.expectedRhythm = rhythmFor(expected);
}

function roleLabel(role) {
  return String(role || '').replaceAll('_', ' ');
}

function rhythmFor(transliteration) {
  const value = String(transliteration || '').trim();
  if (!value) return '';
  if (RHYTHM_OVERRIDES[value]) return RHYTHM_OVERRIDES[value];

  return value
    .split(/\s+/)
    .map(word => rhythmWord(word))
    .filter(Boolean)
    .join(' | ');
}

function rhythmWord(word) {
  const cleaned = String(word || '').replace(/^[^\w]+|[^\w]+$/g, '');
  if (!cleaned) return '';

  const syllables = splitSyllables(cleaned.toLowerCase());
  if (syllables.length === 0) return cleaned;
  if (syllables.length === 1) return syllables[0].toUpperCase();

  const stressIndex = syllables.length === 2 ? 0 : Math.max(0, syllables.length - 2);
  return syllables
    .map((syllable, index) => index === stressIndex ? syllable.toUpperCase() : syllable)
    .join('-');
}

function splitSyllables(word) {
  const matches = word.match(/[^aeiou]*[aeiou]+(?:ng|kk|pp|tt|th|dh|n|m|r|l|y)?/g);
  if (!matches) return [word];

  const joined = matches.join('');
  const remainder = word.slice(joined.length);
  if (remainder && matches.length) {
    matches[matches.length - 1] += remainder;
  }
  return matches;
}

function renderComplete() {
  app.innerHTML = `
    <section class="card-shell complete">
      ${renderHeader()}
      <div class="status-mark success" aria-hidden="true">✓</div>
      <h2>Session complete</h2>
      <button class="text-button primary" data-action="restart">Restart</button>
      <button class="text-button" data-action="change-language">Change Language</button>
    </section>
  `;

  bind('[data-action="restart"]', 'click', () => {
    state.cardIndex = 0;
    resetCardState();
    render();
  });
  bind('[data-action="change-language"]', 'click', showLanguageSelect);
}

function showLanguageSelect() {
  state.session = null;
  resetCardState();
  renderLanguageSelect();
}

function renderLoading() {
  app.innerHTML = `
    <section class="card-shell">
      <p class="muted">Loading scenes...</p>
    </section>
  `;
}

function renderError(message) {
  app.innerHTML = `
    <section class="card-shell error">
      <p>${escapeHtml(message)}</p>
    </section>
  `;
}

function bind(selector, event, handler) {
  document.querySelector(selector)?.addEventListener(event, handler);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function escapeCssUrl(value) {
  return String(value ?? '')
    .replaceAll('\\', '\\\\')
    .replaceAll("'", "\\'")
    .replaceAll('\n', '');
}
