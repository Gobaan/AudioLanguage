const app = document.querySelector('#traveller-lesson-app');

const state = {
  language: 'en',
  lesson: null,
  activeStepIndex: 0,
  activeFrameId: '',
  selectedChoiceByStep: {},
  revealedSteps: {},
  playingStepId: '',
  listeningStepId: '',
};

const componentRenderers = {
  SceneFrame: renderSceneFrameStep,
  AudioButton: renderAudioButtonStep,
  ChoicePrompt: renderChoicePromptStep,
  TranslationReveal: renderTranslationRevealStep,
  MicPrompt: renderMicPromptStep,
  BackwardBuild: renderBackwardBuildStep,
  ProductionPrompt: renderProductionPromptStep,
  MiniRoleplay: renderMiniRoleplayStep,
  AudioOnlyRecognition: renderAudioOnlyRecognitionStep,
  SimilarPhraseContrast: renderSimilarPhraseContrastStep,
  ProgressCard: renderProgressCardStep,
};

init();

async function init() {
  try {
    const payload = await fetchJson(`/api/languages/${encodeURIComponent(state.language)}/lessons`);
    state.lesson = firstTravellerLesson(payload.lessons);
    state.activeFrameId = state.lesson.frames[0]?.id || '';
    render();
  } catch (error) {
    app.innerHTML = `<section class="traveller-shell error"><p>${escapeHtml(error.message)}</p></section>`;
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load ${url}`);
  return response.json();
}

function firstTravellerLesson(lessons) {
  const lesson = lessons.find(item => item.player_component === 'TravellerLessonPlayer') || lessons[0];
  if (!lesson) throw new Error('No lessons returned from the API.');
  return lesson;
}

function render() {
  const lesson = state.lesson;
  const step = lesson.steps[state.activeStepIndex] || lesson.steps[0];
  const renderer = componentRenderers[step.component] || renderUnknownStep;
  const activeFrame = frameById(state.activeFrameId) || lesson.frames[0];

  app.innerHTML = `
    <article class="traveller-shell">
      <header class="traveller-header">
        <div>
          <span>${escapeHtml(lesson.language.toUpperCase())} traveller lesson</span>
          <h1>${escapeHtml(lesson.title)}</h1>
        </div>
        <strong>${state.activeStepIndex + 1} / ${lesson.steps.length}</strong>
      </header>

      <section class="traveller-stage" aria-label="Current scene frame">
        ${renderSceneFrame(activeFrame, true)}
        ${renderFrameStrip(lesson.frames)}
      </section>

      <section class="traveller-step-card" aria-live="polite">
        <div class="traveller-step-title">
          <span>${escapeHtml(step.type.replaceAll('_', ' '))}</span>
          <strong>${escapeHtml(step.component)}</strong>
        </div>
        ${renderer(step)}
      </section>

      ${renderStepRail(lesson.steps)}
      ${renderControls()}
    </article>
  `;

  bindControls();
}

function renderSceneFrameStep(step) {
  const props = step.props || {};
  const frameId = props.initialFrameId || state.activeFrameId;
  const frame = frameById(frameId) || state.lesson.frames[0];
  return `
    <div class="traveller-component traveller-scene-frame">
      ${renderSceneFrame(frame, true)}
    </div>
  `;
}

function renderSceneFrame(frame, isActive = false) {
  return `
    <figure class="scene-frame-card ${isActive ? 'active' : ''}">
      ${frame?.imageUrl ? `
        <img src="${escapeHtml(frame.imageUrl)}" alt="${escapeHtml(frame.title || 'Lesson frame')}">
      ` : `
        <div class="scene-frame-placeholder" aria-label="Lesson frame placeholder"></div>
      `}
      <figcaption>
        <strong>${escapeHtml(frame?.title || 'Scene frame')}</strong>
        ${frame?.speaker ? `<span>${escapeHtml(frame.speaker)}</span>` : ''}
      </figcaption>
    </figure>
  `;
}

function renderFrameStrip(frames) {
  return `
    <nav class="traveller-frame-strip" aria-label="Lesson frames">
      ${frames.map(frame => `
        <button type="button" class="${frame.id === state.activeFrameId ? 'active' : ''}" data-frame-id="${escapeHtml(frame.id)}">
          ${frame.imageUrl ? `<img src="${escapeHtml(frame.imageUrl)}" alt="">` : '<span class="thumb-placeholder"></span>'}
          <span>${escapeHtml(frame.title || frame.id)}</span>
        </button>
      `).join('')}
    </nav>
  `;
}

function renderAudioButtonStep(step) {
  const props = step.props || {};
  return `
    <div class="traveller-component">
      ${renderAudioButton(step.id, props.audioUrl, props.text)}
    </div>
  `;
}

function renderAudioButton(stepId, audioUrl, text = {}) {
  const isPlaying = state.playingStepId === stepId;
  return `
    <button type="button" class="lesson-action audio-button ${isPlaying ? 'playing' : ''}" data-audio-step-id="${escapeHtml(stepId)}" data-audio-url="${escapeHtml(audioUrl || '')}" ${audioUrl ? '' : 'disabled'}>
      ${escapeHtml(isPlaying ? text.playingLabel || 'Playing' : text.playLabel || 'Play audio')}
    </button>
  `;
}

function renderChoicePromptStep(step) {
  const props = step.props || {};
  return renderChoicePrompt(step.id, props.question, props.choices || []);
}

function renderChoicePrompt(stepId, question, choices) {
  const selectedId = state.selectedChoiceByStep[stepId];
  return `
    <fieldset class="traveller-choice-prompt">
      <legend>${escapeHtml(question || 'Choose the best response')}</legend>
      ${choices.map(choice => `
        <button type="button" class="${choice.id === selectedId ? 'selected' : ''}" data-choice-step-id="${escapeHtml(stepId)}" data-choice-id="${escapeHtml(choice.id)}">
          <span>${escapeHtml(choice.label)}</span>
          ${choice.id === selectedId && choice.isCorrect !== undefined ? `<small>${choice.isCorrect ? 'Fits this lesson' : 'Try a different option'}</small>` : ''}
        </button>
      `).join('')}
    </fieldset>
  `;
}

function renderTranslationRevealStep(step) {
  const isRevealed = Boolean(state.revealedSteps[step.id]);
  const translation = step.props?.translation || '';
  return `
    <div class="traveller-component">
      ${isRevealed ? `
        <p class="translation-card">${escapeHtml(translation)}</p>
      ` : `
        <button type="button" class="lesson-action" data-reveal-step-id="${escapeHtml(step.id)}">Reveal</button>
      `}
    </div>
  `;
}

function renderMicPromptStep(step) {
  return renderMicPrompt(step.id, step.props?.text, step.props?.expectedText);
}

function renderMicPrompt(stepId, text = {}, expectedText = '') {
  const isListening = state.listeningStepId === stepId;
  return `
    <section class="traveller-mic-prompt ${isListening ? 'listening' : ''}">
      <p>${escapeHtml(isListening ? text.listeningLabel || 'Listening...' : text.prompt || 'Try saying it')}</p>
      ${expectedText ? `<strong>${escapeHtml(expectedText)}</strong>` : ''}
      <button type="button" class="lesson-action" data-mic-step-id="${escapeHtml(stepId)}" ${isListening ? 'disabled' : ''}>
        ${escapeHtml(text.startLabel || 'Start')}
      </button>
    </section>
  `;
}

function renderBackwardBuildStep(step) {
  const chunks = step.props?.chunks || [];
  return `
    <section class="traveller-component traveller-build">
      <h2>${escapeHtml(step.props?.targetPhrase || state.lesson.target.text || 'Target phrase')}</h2>
      <dl>
        ${chunks.map(chunk => `
          <div>
            <dt>${escapeHtml(chunk.text)}</dt>
            <dd>${escapeHtml(chunk.meaning || '')}</dd>
          </div>
        `).join('')}
      </dl>
    </section>
  `;
}

function renderProductionPromptStep(step) {
  const props = step.props || {};
  return `
    <section class="traveller-component traveller-production">
      <p>${escapeHtml(props.cue || 'Respond to the prompt')}</p>
      <small>${escapeHtml(props.targetMeaning || '')}</small>
      ${renderMicPrompt(`${step.id}-mic`, props.micText)}
    </section>
  `;
}

function renderMiniRoleplayStep(step) {
  return `
    <section class="traveller-component traveller-roleplay">
      <p>${escapeHtml(step.props?.scenario || 'Practice the same line in a new moment.')}</p>
      <strong>${escapeHtml(step.props?.targetMeaning || state.lesson.target.meaning)}</strong>
    </section>
  `;
}

function renderAudioOnlyRecognitionStep(step) {
  const props = step.props || {};
  return `
    <section class="traveller-component traveller-audio-only">
      <p>${escapeHtml(props.prompt || 'Listen, then repeat.')}</p>
      ${renderAudioButton(`${step.id}-audio`, targetFrameAudio(), props.audioText)}
      ${renderMicPrompt(`${step.id}-mic`, props.micText)}
    </section>
  `;
}

function renderSimilarPhraseContrastStep(step) {
  const props = step.props || {};
  return `
    <section class="traveller-component">
      <p class="muted">${escapeHtml(props.explanation || '')}</p>
      ${renderChoicePrompt(step.id, 'Similar phrases', props.choices || [])}
    </section>
  `;
}

function renderProgressCardStep(step) {
  const metrics = step.props?.metrics || [];
  return `
    <section class="traveller-component traveller-progress">
      <h2>${escapeHtml(step.props?.title || 'Progress')}</h2>
      <ul>
        ${metrics.map(metric => `
          <li><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong></li>
        `).join('')}
      </ul>
    </section>
  `;
}

function renderUnknownStep(step) {
  return `
    <pre class="traveller-json">${escapeHtml(JSON.stringify(step.props || {}, null, 2))}</pre>
  `;
}

function renderStepRail(steps) {
  return `
    <nav class="traveller-step-rail" aria-label="Lesson steps">
      ${steps.map((step, index) => `
        <button type="button" class="${index === state.activeStepIndex ? 'active' : ''}" data-step-index="${index}">
          ${index + 1}
        </button>
      `).join('')}
    </nav>
  `;
}

function renderControls() {
  const isFirst = state.activeStepIndex === 0;
  const isLast = state.activeStepIndex >= state.lesson.steps.length - 1;
  return `
    <footer class="traveller-controls">
      <button type="button" class="lesson-action" data-action="previous-step" ${isFirst ? 'disabled' : ''}>Previous</button>
      <button type="button" class="lesson-action primary" data-action="next-step">${isLast ? 'Restart' : 'Next'}</button>
    </footer>
  `;
}

function bindControls() {
  document.querySelectorAll('[data-frame-id]').forEach(button => {
    button.addEventListener('click', () => {
      state.activeFrameId = button.dataset.frameId;
      render();
    });
  });

  document.querySelectorAll('[data-step-index]').forEach(button => {
    button.addEventListener('click', () => {
      state.activeStepIndex = Number(button.dataset.stepIndex);
      syncFrameToStep();
      render();
    });
  });

  document.querySelector('[data-action="previous-step"]')?.addEventListener('click', () => {
    state.activeStepIndex = Math.max(0, state.activeStepIndex - 1);
    syncFrameToStep();
    render();
  });

  document.querySelector('[data-action="next-step"]')?.addEventListener('click', () => {
    state.activeStepIndex = state.activeStepIndex >= state.lesson.steps.length - 1 ? 0 : state.activeStepIndex + 1;
    syncFrameToStep();
    render();
  });

  document.querySelectorAll('[data-choice-step-id]').forEach(button => {
    button.addEventListener('click', () => {
      state.selectedChoiceByStep[button.dataset.choiceStepId] = button.dataset.choiceId;
      render();
    });
  });

  document.querySelectorAll('[data-reveal-step-id]').forEach(button => {
    button.addEventListener('click', () => {
      state.revealedSteps[button.dataset.revealStepId] = true;
      render();
    });
  });

  document.querySelectorAll('[data-audio-step-id]').forEach(button => {
    button.addEventListener('click', () => playAudioForButton(button));
  });

  document.querySelectorAll('[data-mic-step-id]').forEach(button => {
    button.addEventListener('click', () => fakeListen(button.dataset.micStepId));
  });
}

function syncFrameToStep() {
  const step = state.lesson.steps[state.activeStepIndex];
  const frameId = step?.props?.initialFrameId;
  if (frameId) state.activeFrameId = frameId;
}

async function playAudioForButton(button) {
  const url = button.dataset.audioUrl;
  if (!url) return;

  state.playingStepId = button.dataset.audioStepId;
  render();

  await new Promise(resolve => {
    const audio = new Audio(url);
    audio.onended = resolve;
    audio.onerror = resolve;
    audio.play().catch(resolve);
  });

  state.playingStepId = '';
  render();
}

function fakeListen(stepId) {
  state.listeningStepId = stepId;
  render();
  window.setTimeout(() => {
    state.listeningStepId = '';
    render();
  }, 1200);
}

function frameById(frameId) {
  return state.lesson?.frames.find(frame => frame.id === frameId);
}

function targetFrameAudio() {
  const targetText = state.lesson.target.text;
  return state.lesson.frames.find(frame => frame.text === targetText)?.audioUrl || state.lesson.frames[0]?.audioUrl || '';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
