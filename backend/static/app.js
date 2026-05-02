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
  { kind: 'prompt', key: 'second_time' },
  { kind: 'mic', attempt: 1 },
];

const LISTENING_LIMIT_MS = 10000;
const MIN_LISTENING_MS = 700;
const SILENCE_LIMIT_MS = 900;
const SPEECH_LEVEL_THRESHOLD = 8;

const state = {
  cards: [],
  cardIndex: 0,
  sequence: [],
  stepIndex: 0,
  isRunning: false,
  isListening: false,
  isTranscribing: false,
  attemptCount: 0,
  completedCount: 0,
  speechStatus: 'idle',
  speechTranscript: '',
  expectedLineIndex: 1,
  visualFrameIndex: 0,
  stopListening: null,
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
      <button class="round-button" data-action="start" aria-label="Start audio card">&#9654;</button>
    </section>
  `;

  bind('start', startCard);
}

async function startCard() {
  if (state.isRunning) return;

  state.isRunning = true;
  state.attemptCount = 0;
  state.visualFrameIndex = 0;
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
      state.visualFrameIndex = step.index;
      renderActiveCard('playing');
      await playAudio(dialogueUrl(currentCard().id, step.index));
      state.stepIndex += 1;
      continue;
    }

    if (step.kind === 'mic') {
      const isCorrect = await captureResponse();
      if (!state.isRunning) return;
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
    state.visualFrameIndex = state.expectedLineIndex;
    renderActiveCard('retry');
    await playAudio(promptUrl('feedback_failure'));
    await playAudio(dialogueUrl(currentCard().id, state.expectedLineIndex));

    state.sequence.push(
      { kind: 'prompt', key: 'call_to_action' },
      { kind: 'mic', attempt: 2 },
    );

    state.stepIndex += 1;
    return;
  }

  state.visualFrameIndex = 2;
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
      <div class="status-mark ${wasSuccessful ? 'success' : 'failure'}" aria-hidden="true">${wasSuccessful ? '&#10003;' : '&#8635;'}</div>
      <button class="round-button" data-action="next" aria-label="Next card">&#8250;</button>
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
      ${renderSpeechDebug()}
      <button class="ghost-button" data-action="stop" aria-label="Stop card">&#9632;</button>
    </section>
  `;

  bind('stop', stopCard);
}

function stopCard() {
  state.isRunning = false;
  state.isListening = false;
  state.visualFrameIndex = 0;
  state.isTranscribing = false;
  state.stopListening?.(false);
  state.stopListening = null;
  stopAllAudio();
  renderReadyCard();
}

async function captureResponse() {
  const recorder = await startRecorder();

  if (!recorder.isAvailable) {
    await delay(350);
    return false;
  }

  return new Promise(resolve => {
    state.isListening = true;
    state.isTranscribing = false;
    state.visualFrameIndex = state.expectedLineIndex;
    state.speechStatus = 'listening';
    state.speechTranscript = '';
    renderActiveCard('listening');

    let heardSpeech = false;
    let stopped = false;
    let silenceStartedAt = null;
    const startedAt = Date.now();
    const timeoutId = setTimeout(() => stopListening(), LISTENING_LIMIT_MS);

    state.stopListening = stopListening;

    function maybeStop(level) {
      const elapsed = Date.now() - startedAt;

      if (stopped || elapsed < MIN_LISTENING_MS) return;

      if (level > SPEECH_LEVEL_THRESHOLD) {
        heardSpeech = true;
        silenceStartedAt = null;
        return;
      }

      if (!heardSpeech) return;

      if (silenceStartedAt === null) {
        silenceStartedAt = Date.now();
        return;
      }

      if (Date.now() - silenceStartedAt >= SILENCE_LIMIT_MS) {
        stopListening();
      }
    }

    async function stopListening(shouldTranscribe = true) {
      if (stopped) return;
      stopped = true;
      clearTimeout(timeoutId);
      state.stopListening = null;
      state.isListening = false;
      state.isTranscribing = shouldTranscribe;
      state.speechStatus = shouldTranscribe ? 'transcribing' : 'stopped';
      const recordingBlob = await recorder.stop();

      if (!shouldTranscribe || !state.isRunning) {
        state.isTranscribing = false;
        state.speechStatus = 'stopped';
        resolve(false);
        return;
      }

      renderActiveCard('ready');
      const isMatch = await transcribeRecording(recordingBlob);
      resolve(isMatch);
    }

    recorder.onLevel(maybeStop);
  });
}

async function startRecorder() {
  if (!navigator.mediaDevices?.getUserMedia || !('MediaRecorder' in window)) {
    state.speechStatus = 'recording unavailable';
    return createEmptyRecorder();
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks = [];
    const recorder = new MediaRecorder(stream);
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    const samples = new Uint8Array(analyser.fftSize);
    let frameId = null;
    let levelCallback = () => {};

    source.connect(analyser);

    recorder.ondataavailable = event => {
      if (event.data.size > 0) chunks.push(event.data);
    };

    recorder.start();

    function readLevel() {
      analyser.getByteTimeDomainData(samples);
      let total = 0;

      for (const sample of samples) {
        const normalized = sample - 128;
        total += normalized * normalized;
      }

      levelCallback(Math.sqrt(total / samples.length));
      frameId = requestAnimationFrame(readLevel);
    }

    readLevel();

    return {
      isAvailable: true,
      onLevel(callback) {
        levelCallback = callback;
      },
      stop() {
        return new Promise(resolve => {
          recorder.onstop = () => {
            if (frameId) cancelAnimationFrame(frameId);
            stream.getTracks().forEach(track => track.stop());
            audioContext.close();

            if (chunks.length === 0) {
              resolve(null);
              return;
            }

            resolve(new Blob(chunks, { type: recorder.mimeType || 'audio/webm' }));
          };

          recorder.stop();
        });
      },
    };
  } catch (error) {
    state.speechStatus = `recording error: ${error.name}`;
    return createEmptyRecorder();
  }
}

function createEmptyRecorder() {
  return {
    isAvailable: false,
    onLevel() {},
    stop: async () => null,
  };
}

async function transcribeRecording(recordingBlob) {
  if (!recordingBlob) {
    state.speechStatus = 'no recording captured';
    state.isTranscribing = false;
    renderActiveCard('ready');
    return false;
  }

  let isMatch = false;

  try {
    const formData = new FormData();
    formData.append('file', recordingBlob, `${currentCard().id}-attempt-${state.attemptCount + 1}.webm`);
    formData.append('expected', expectedLineText());

    const response = await fetch('/api/transcribe', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error('transcription failed');

    const result = await response.json();
    state.speechTranscript = result.transcript || '';
    isMatch = Boolean(result.is_match);
    state.speechStatus = result.is_match ? `matched (${Math.round(result.score * 100)}%)` : `did not match (${Math.round(result.score * 100)}%)`;
  } catch (error) {
    state.speechTranscript = '';
    isMatch = false;
    state.speechStatus = error.message;
  }

  renderActiveCard('ready');
  await delay(350);
  state.isTranscribing = false;
  state.speechStatus = 'done';
  return isMatch;
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function renderSpeechDebug() {
  if (!state.isListening && !state.isTranscribing) return '';

  return `
    <div class="speech-debug" aria-live="polite">
      <div class="speech-debug-label">API heard</div>
      <div class="speech-debug-status" data-debug="status">${escapeHtml(state.speechStatus)}</div>
      <div class="speech-debug-transcript" data-debug="transcript">${escapeHtml(state.speechTranscript || '...')}</div>
    </div>
  `;
}

function renderSceneArt(card) {
  const frameUrl = sceneFrameUrl(card);

  if (frameUrl) {
    return `
      <figure class="scene-art scene-frame">
        <img src="${escapeHtml(frameUrl)}" alt="${escapeHtml(frameAltText(card))}">
      </figure>
    `;
  }

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

function sceneFrameUrl(card) {
  if (card.id !== 'ta-greeting-hello') return null;

  return `/visuals/${card.id}/frame-${state.visualFrameIndex}.png`;
}

function frameAltText(card) {
  const line = card.lines?.[state.visualFrameIndex];
  if (!line) return card.situation || 'Dialogue scene';

  return `${card.situation} ${line.speaker} says: ${line.text}`;
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
      <div class="status-mark success" aria-hidden="true">&#10003;</div>
      <button class="round-button" data-action="restart" aria-label="Restart session">&#8635;</button>
    </section>
  `;

  bind('restart', restart);
}

function restart() {
  state.cardIndex = 0;
  state.stepIndex = 0;
  state.isRunning = false;
  state.isListening = false;
  state.visualFrameIndex = 0;
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

function expectedLineText() {
  return currentCard().lines[state.expectedLineIndex]?.text || '';
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
