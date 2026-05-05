const state = {
  languages: [],
  language: 'ta',
  session: null,
  cardIndex: 0,
  selectedChoiceIndex: null,
  isAnswerRevealed: false,
  isPlaying: false,
};

const app = document.querySelector('#app');

init();

async function init() {
  try {
    state.languages = await fetchJson('/api/languages');
    if (!state.languages.some(language => language.id === state.language)) {
      state.language = state.languages[0]?.id || 'en';
    }
    await loadSession(state.language);
  } catch (error) {
    renderError(error.message);
  }
}

async function loadSession(language) {
  state.language = language;
  state.session = await fetchJson(`/api/languages/${encodeURIComponent(language)}/session`);
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
    renderLoading();
    return;
  }

  if (state.cardIndex >= state.session.cards.length) {
    renderComplete();
    return;
  }

  const card = currentCard();
  app.innerHTML = `
    <section class="card-shell scene-${escapeHtml(card.scene.domain || card.function.domain)}">
      ${renderHeader()}
      ${renderProgress()}
      ${renderScene(card)}
      ${renderCardBody(card)}
      ${renderControls(card)}
    </section>
  `;

  bind('[data-language]', 'change', event => loadSession(event.target.value));
  bind('[data-action="play-dialogue"]', 'click', () => playDialogue(card));
  bind('[data-action="play-target"]', 'click', () => playTarget(card));
  bind('[data-action="reveal"]', 'click', revealAnswer);
  bind('[data-action="next"]', 'click', nextCard);
  bind('[data-action="previous"]', 'click', previousCard);

  document.querySelectorAll('[data-choice-index]').forEach(button => {
    button.addEventListener('click', () => chooseAnswer(Number(button.dataset.choiceIndex)));
  });
}

function renderHeader() {
  return `
    <header class="topbar">
      <div>
        <p class="eyebrow">${escapeHtml(state.session.session.name)}</p>
        <h1>${escapeHtml(state.session.display_name)}</h1>
      </div>
      <label class="language-picker">
        <span>Language</span>
        <select data-language>
          ${state.languages.map(language => `
            <option value="${escapeHtml(language.id)}" ${language.id === state.language ? 'selected' : ''}>
              ${escapeHtml(language.display_name)}
            </option>
          `).join('')}
        </select>
      </label>
    </header>
  `;
}

function renderProgress() {
  return `
    <div class="progress-dots" aria-label="Card progress">
      ${state.session.cards.map((_, index) => {
        const className = index === state.cardIndex ? 'dot current' : index < state.cardIndex ? 'dot done' : 'dot';
        return `<span class="${className}"></span>`;
      }).join('')}
    </div>
  `;
}

function renderScene(card) {
  const imageUrl = firstVisual(card);
  const scene = card.scene;

  if (imageUrl) {
    return `
      <figure class="scene-art scene-frame">
        <img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(scene.description)}">
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
    </figure>
  `;
}

function renderCardBody(card) {
  return `
    <section class="practice-panel">
      <div class="mode-row">
        <span class="mode-pill">${escapeHtml(card.review_mode.name)}</span>
        <span class="stage-pill">${escapeHtml(card.stage.replaceAll('_', ' '))}</span>
      </div>
      <h2>${escapeHtml(card.prompt)}</h2>
      ${renderIntention(card)}
      ${renderTarget(card)}
      ${renderChoices(card)}
      ${renderDetailsDrawer(card)}
      ${renderFeedback(card)}
    </section>
  `;
}

function renderIntention(card) {
  if (!state.isAnswerRevealed && state.selectedChoiceIndex === null) return '';

  return `
    <div class="intention-card">
      <span>Intention</span>
      <strong>${escapeHtml(card.function.name)}</strong>
    </div>
  `;
}

function renderTarget(card) {
  const shouldShowTarget = state.isAnswerRevealed || card.mode === 'listen' || card.mode === 'ai_roleplay_unlock';
  if (!shouldShowTarget) {
    return `
      <div class="target-card hidden-target">
        <span>Target hidden</span>
      </div>
    `;
  }

  return `
    <div class="target-card">
      <div class="target-script">${escapeHtml(card.target.canonical)}</div>
      ${card.target.transliteration ? `<div class="target-translit">${escapeHtml(card.target.transliteration)}</div>` : ''}
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

function renderControls(card) {
  const hasDialogueAudio = card.dialogue.lines?.some(line => line.audio);
  const targetAudio = targetLine(card)?.audio;
  const shouldShowReveal = card.mode !== 'listen' && !state.isAnswerRevealed;

  return `
    <footer class="controls">
      <button class="icon-button" data-action="previous" ${state.cardIndex === 0 ? 'disabled' : ''} aria-label="Previous card">‹</button>
      <button class="text-button" data-action="play-dialogue" ${!hasDialogueAudio || state.isPlaying ? 'disabled' : ''}>Play Scene</button>
      <button class="text-button" data-action="play-target" ${!targetAudio || state.isPlaying ? 'disabled' : ''}>Play Target</button>
      ${shouldShowReveal ? '<button class="text-button primary" data-action="reveal">Reveal</button>' : ''}
      <button class="icon-button" data-action="next" aria-label="Next card">›</button>
    </footer>
  `;
}

function firstVisual(card) {
  return card.dialogue.lines?.find(line => line.visual)?.visual || null;
}

function targetLine(card) {
  return card.dialogue.lines?.find(line => line.is_learner_target || line.target_id === card.target_id);
}

async function playDialogue(card) {
  const audioLines = card.dialogue.lines.filter(line => line.audio);
  await playMany(audioLines.map(line => line.audio));
}

async function playTarget(card) {
  const line = targetLine(card);
  if (line?.audio) await playMany([line.audio]);
}

async function playMany(urls) {
  state.isPlaying = true;
  render();
  for (const url of urls) {
    await playAudio(url);
  }
  state.isPlaying = false;
  render();
}

function playAudio(url) {
  return new Promise(resolve => {
    const audio = new Audio(url);
    window.currentAudio = audio;
    audio.onended = resolve;
    audio.onerror = resolve;
    audio.play().catch(resolve);
  });
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

function nextCard() {
  state.cardIndex += 1;
  resetCardState();
  render();
}

function previousCard() {
  if (state.cardIndex === 0) return;
  state.cardIndex -= 1;
  resetCardState();
  render();
}

function resetCardState() {
  state.selectedChoiceIndex = null;
  state.isAnswerRevealed = false;
  state.isPlaying = false;
}

function currentCard() {
  return state.session.cards[state.cardIndex];
}

function roleLabel(role) {
  return String(role || '').replaceAll('_', ' ');
}

function renderComplete() {
  app.innerHTML = `
    <section class="card-shell complete">
      ${renderHeader()}
      <div class="status-mark success" aria-hidden="true">✓</div>
      <h2>Session complete</h2>
      <button class="text-button primary" data-action="restart">Restart</button>
    </section>
  `;

  bind('[data-language]', 'change', event => loadSession(event.target.value));
  bind('[data-action="restart"]', 'click', () => {
    state.cardIndex = 0;
    resetCardState();
    render();
  });
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
