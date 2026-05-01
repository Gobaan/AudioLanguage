const FIRST_TIME_SEQUENCE = [
  { kind: 'prompt', key: 'opening' },
  { kind: 'dialogue', index: 0 },
  { kind: 'prompt', key: 'first_time' },
  { kind: 'dialogue', index: 1 },
  { kind: 'prompt', key: 'call_to_action' },
  { kind: 'mic', attempt: 1 },
];

const SECOND_TIME_SEQUENCE = [
  { kind: 'prompt', key: 'opening' },
  { kind: 'dialogue', index: 0 },
  { kind: 'prompt', key: 'call_to_action' },
  { kind: 'mic', attempt: 1 },
];

const state = {
  cards: [],
  cardIndex: 0,
  sequence: [],
  stepIndex: 0,
  isRunning: false,
  isListening: false,
  attemptCount: 0,
  completedCount: 0,
};

const app = document.querySelector('#app');

init();

async function init() {
  try {
    const response = await fetch('/api/dialogues');
    if (!response.ok) throw new Error('Could not load dialogue cards');
    state.cards = await response.json();
    renderReadyCard();
  } catch (error) {
    renderError(error.message);
  }
}

function renderReadyCard() {
  if (state.cardIndex >= state.cards.length) {
    renderComplete();
    return;
  }

  const card = currentCard();
  app.innerHTML = `
    <section class="card-shell scene-${escapeHtml(card.category)}" aria-label="Dialogue card ready">
      ${renderProgress()}
      ${renderSceneArt(card)}
      <button class="round-button" data-action="start" aria-label="Start audio card">▶</button>
    </section>
  `;

  bind('start', startCard);
}

async function startCard() {
  if (state.isRunning) return;

  state.isRunning = true;
  state.attemptCount = 0;
  state.sequence = hasSeenCard(currentCard().id) ? [...SECOND_TIME_SEQUENCE] : [...FIRST_TIME_SEQUENCE];
  state.stepIndex = 0;
  renderActiveCard('playing');
  await runSequence();
}

async function runSequence() {
  while (state.stepIndex < state.sequence.length && state.isRunning) {
    const step = state.sequence[state.stepIndex];

    if (step.kind === 'prompt') {
      renderActiveCard('playing');
      await playAudio(promptUrl(step.key));
      state.stepIndex += 1;
      continue;
    }

    if (step.kind === 'dialogue') {
      renderActiveCard('playing');
      await playAudio(dialogueUrl(currentCard().id, step.index));
      state.stepIndex += 1;
      continue;
    }

    if (step.kind === 'mic') {
      const isCorrect = await captureResponse();
      await handleResponse(isCorrect);
      continue;
    }
  }
}

async function handleResponse(isCorrect) {
  state.attemptCount += 1;

  if (!isCorrect && state.attemptCount >= 2) {
    renderActiveCard('failed');
    await playAudio(promptUrl('feedback_failure_2'));
    finishCard(false);
    return;
  }

  if (!isCorrect) {
    renderActiveCard('retry');
    await playAudio(promptUrl('feedback_failure'));

    if (hasSeenCard(currentCard().id)) {
      state.sequence.push(
        { kind: 'prompt', key: 'second_time' },
        { kind: 'dialogue', index: 1 },
        { kind: 'prompt', key: 'call_to_action' },
        { kind: 'mic', attempt: 2 },
      );
    } else {
      state.sequence.push(
        { kind: 'prompt', key: 'call_to_action' },
        { kind: 'mic', attempt: 2 },
      );
    }

    state.stepIndex += 1;
    return;
  }

  if (hasSeenCard(currentCard().id) && state.attemptCount === 1) {
    state.sequence.push(
      { kind: 'prompt', key: 'second_time' },
      { kind: 'dialogue', index: 1 },
      { kind: 'prompt', key: 'call_to_action' },
      { kind: 'mic', attempt: 2 },
    );
    state.stepIndex += 1;
    return;
  }

  renderActiveCard('success');
  await playAudio(promptUrl('feedback_success'));
  await playAudio(promptUrl('closing'));
  await playAudio(dialogueUrl(currentCard().id, 2));
  finishCard(true);
}

function finishCard(wasSuccessful) {
  markSeen(currentCard().id);
  state.isRunning = false;
  state.isListening = false;
  if (wasSuccessful) state.completedCount += 1;

  app.innerHTML = `
    <section class="card-shell scene-${escapeHtml(currentCard().category)}" aria-label="Dialogue card finished">
      ${renderProgress()}
      ${renderSceneArt(currentCard())}
      <div class="status-mark ${wasSuccessful ? 'success' : 'failure'}" aria-hidden="true">${wasSuccessful ? '✓' : '↻'}</div>
      <button class="round-button" data-action="next" aria-label="Next card">›</button>
    </section>
  `;

  bind('next', nextCard);
}

function nextCard() {
  state.cardIndex += 1;
  renderReadyCard();
}

function renderActiveCard(status) {
  const card = currentCard();
  app.innerHTML = `
    <section class="card-shell scene-${escapeHtml(card.category)} ${state.isListening ? 'listening' : ''}" aria-label="Dialogue card active">
      ${renderProgress()}
      ${renderSceneArt(card)}
      <div class="audio-orb ${status}" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <button class="ghost-button" data-action="stop" aria-label="Stop card">■</button>
    </section>
  `;

  bind('stop', stopCard);
}

function stopCard() {
  state.isRunning = false;
  state.isListening = false;
  stopAllAudio();
  renderReadyCard();
}

function captureResponse() {
  return new Promise(resolve => {
    state.isListening = true;
    renderActiveCard('listening');

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setTimeout(() => {
        state.isListening = false;
        resolve(true);
      }, 3000);
      return;
    }

    const recognition = new SpeechRecognition();
    let heardSpeech = false;

    recognition.lang = 'ta-IN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = event => {
      heardSpeech = event.results.length > 0 && event.results[0].length > 0;
    };

    recognition.onerror = () => {
      heardSpeech = false;
    };

    recognition.onend = () => {
      state.isListening = false;
      resolve(heardSpeech);
    };

    recognition.start();
    setTimeout(() => recognition.stop(), 5000);
  });
}

function renderSceneArt(card) {
  return `
    <div class="scene-art" aria-label="Scene image">
      <div class="sun"></div>
      <div class="ground"></div>
      <div class="figure figure-a"></div>
      <div class="figure figure-b"></div>
      <div class="context-object"></div>
    </div>
  `;
}

function renderProgress() {
  return `
    <div class="progress-dots" aria-label="Card progress">
      ${state.cards.slice(0, 12).map((_, index) => {
        const className = index === state.cardIndex ? 'dot current' : index < state.cardIndex ? 'dot done' : 'dot';
        return `<span class="${className}"></span>`;
      }).join('')}
    </div>
  `;
}

function renderComplete() {
  app.innerHTML = `
    <section class="card-shell complete" aria-label="Session complete">
      <div class="status-mark success" aria-hidden="true">✓</div>
      <button class="round-button" data-action="restart" aria-label="Restart session">↻</button>
    </section>
  `;

  bind('restart', restart);
}

function restart() {
  state.cardIndex = 0;
  state.stepIndex = 0;
  state.isRunning = false;
  state.isListening = false;
  state.completedCount = 0;
  renderReadyCard();
}

function currentCard() {
  return state.cards[state.cardIndex];
}

function promptUrl(key) {
  return `/audio/prompts/${key}.mp3`;
}

function dialogueUrl(cardId, lineIndex) {
  return `/audio/${cardId}-${lineIndex}.mp3`;
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

function stopAllAudio() {
  if (window.currentAudio) {
    window.currentAudio.pause();
    window.currentAudio.currentTime = 0;
  }
}

function hasSeenCard(cardId) {
  return localStorage.getItem(seenKey(cardId)) === 'true';
}

function markSeen(cardId) {
  localStorage.setItem(seenKey(cardId), 'true');
}

function seenKey(cardId) {
  return `audio-language-seen-${cardId}`;
}

function bind(action, handler) {
  document.querySelector(`[data-action="${action}"]`)?.addEventListener('click', handler);
}

function renderError(message) {
  app.innerHTML = `
    <section class="card-shell error">
      <p>${escapeHtml(message)}</p>
    </section>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
