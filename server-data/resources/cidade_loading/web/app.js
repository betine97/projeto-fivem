(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const audio = $('music');
  const inGame = typeof GetParentResourceName === 'function';
  const parentResource = inGame ? GetParentResourceName() : null;
  // FiveM names the special frame "loadingScreen", not the owning resource.
  const resource = parentResource && parentResource !== 'loadingScreen' ? parentResource : 'cidade_loading';
  const interactive = new URLSearchParams(location.search).has('interactive');
  let visible = !interactive;
  let handoffPending = false;
  const preview = !inGame && new URLSearchParams(location.search).has('preview');
  const flag = value => value === true || value === 1;
  const revision = 'entrada-nui-20261009-4';
  const state = { ready: false, entering: false, progress: 0, tracks: [], index: 0, wantsMusic: true, failedTracks: new Set() };
  let statusTimer;
  let retryPending = false;
  let uiReadyTimer;
  let uiReadyPending = false;
  const failureLogs = new Map();
  function diagnostic(stage, extra = {}) {
    const html = document.documentElement;
    const payload = { stage, revision, resource, visible, interactive,
      html_class: html.className, body_class: document.body.className,
      meta_scheme: document.querySelector('meta[name="color-scheme"]')?.content,
      css_scheme: getComputedStyle(html).colorScheme,
      background: getComputedStyle(html).backgroundColor,
      body_visibility: getComputedStyle(document.body).visibility,
      body_opacity: getComputedStyle(document.body).opacity,
      focused: document.hasFocus(), ready: state.ready, entering: state.entering,
      audio_paused: audio.paused, track: state.index, ...extra };
    console.info('[Entrada NUI]', JSON.stringify(payload));
    if (inGame) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 1500);
      fetch(`https://${resource}/loadingLog`, { method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload), signal: controller.signal }).catch(() => {}).finally(() => clearTimeout(timeout));
    }
  }
  const clock = seconds => {
    if (!Number.isFinite(seconds)) return '--:--';
    return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
  };
  function saveAudio() {
    try { localStorage.setItem('cidade.loading.audio', JSON.stringify({ volume: audio.volume, muted: audio.muted })); } catch (_) {}
  }
  try {
    const saved = JSON.parse(localStorage.getItem('cidade.loading.audio') || 'null');
    audio.volume = saved && typeof saved.volume === 'number' ? Math.min(1, Math.max(0, saved.volume)) : .35;
    audio.muted = Boolean(saved && saved.muted);
  } catch (_) { audio.volume = .35; }
  function renderAudio() {
    $('volume').value = Math.round(audio.volume * 100);
    $('volume-value').textContent = `${Math.round(audio.volume * 100)}%`;
    const silent = audio.muted || audio.volume === 0;
    $('mute').setAttribute('aria-pressed', String(silent));
    $('mute').setAttribute('aria-label', silent ? 'Ativar áudio' : 'Silenciar áudio');
    $('play').setAttribute('aria-label', audio.paused ? 'Reproduzir música' : 'Pausar música');
    $('play-icon').innerHTML = audio.paused ? '<path d="m8 5 11 7-11 7z"/>' : '<path d="M8 5v14M16 5v14"/>';
    if (!state.tracks.length) return;
    $('audio-status').textContent = audio.paused ? 'Música pausada · clique em reproduzir' : silent ? 'Tocando · áudio silenciado' : 'Tocando agora';
  }
  async function playAudio() {
    if (!visible || state.entering || !state.tracks.length) return;
    try { await audio.play(); renderAudio(); }
    catch (error) {
      renderAudio();
      $('audio-status').textContent = error.name === 'NotAllowedError' ? 'Clique em reproduzir para ouvir' : 'Não foi possível reproduzir. Escolha outra faixa.';
    }
  }
  function chooseTrack(index, play = true) {
    if (!state.tracks.length || state.entering) return;
    state.index = (index + state.tracks.length) % state.tracks.length;
    const track = state.tracks[state.index];
    audio.src = track.file;
    audio.load();
    $('track-title').textContent = track.title;
    $('track-count').textContent = `${String(state.index + 1).padStart(2, '0')} / ${String(state.tracks.length).padStart(2, '0')}`;
    $('current-time').textContent = '0:00';
    $('duration').textContent = '--:--';
    $('track-progress').style.width = '0%';
    for (const [i, button] of [...$('playlist').children].entries()) button.setAttribute('aria-current', String(i === state.index));
    renderAudio();
    if (play) playAudio();
  }
  $('play').addEventListener('click', () => {
    state.wantsMusic = audio.paused;
    if (state.wantsMusic) playAudio(); else audio.pause();
  });
  $('next').addEventListener('click', () => { state.wantsMusic = true; chooseTrack(state.index + 1); });
  $('previous').addEventListener('click', () => { state.wantsMusic = true; chooseTrack(state.index - 1); });
  $('mute').addEventListener('click', () => {
    const silent = audio.muted || audio.volume === 0;
    if (silent && audio.volume === 0) audio.volume = .35;
    audio.muted = !silent;
    renderAudio(); saveAudio();
  });
  $('volume').addEventListener('input', event => {
    audio.volume = Math.max(0, Math.min(1, Number(event.target.value) / 100));
    if (audio.volume > 0) audio.muted = false;
    renderAudio(); saveAudio();
  });
  $('playlist-toggle').addEventListener('click', () => {
    const open = $('playlist').hidden;
    $('playlist').hidden = !open;
    $('playlist-toggle').setAttribute('aria-expanded', String(open));
  });
  audio.addEventListener('ended', () => chooseTrack(state.index + 1, state.wantsMusic));
  for (const event of ['play', 'pause', 'volumechange']) audio.addEventListener(event, renderAudio);
  audio.addEventListener('loadedmetadata', () => { $('duration').textContent = clock(audio.duration); });
  audio.addEventListener('timeupdate', () => {
    $('current-time').textContent = clock(audio.currentTime);
    $('track-progress').style.width = `${Number.isFinite(audio.duration) && audio.duration > 0 ? Math.min(100, audio.currentTime / audio.duration * 100) : 0}%`;
  });
  audio.addEventListener('error', () => {
    state.failedTracks.add(state.index);
    $('audio-status').textContent = 'Faixa indisponível. Tentando a próxima…';
    if (state.failedTracks.size < state.tracks.length && !state.entering) chooseTrack(state.index + 1, state.wantsMusic);
    else $('audio-status').textContent = 'Áudio indisponível. Você ainda pode entrar no jogo.';
  });

  function setProgress(fraction) {
    if (!Number.isFinite(Number(fraction))) return;
    // Completion is determined by the spawn script, not the engine's percentage.
    state.progress = state.ready ? 100 : Math.max(state.progress, Math.min(95, Math.max(0, Number(fraction) * 95)));
    $('progress-fill').style.width = `${state.progress}%`;
    $('progress-text').textContent = `${Math.round(state.progress)}%`;
    document.querySelector('.progress-track').setAttribute('aria-valuenow', String(Math.round(state.progress)));
    if (!state.ready && state.progress >= 95) $('progress-label').textContent = 'Preparando seu personagem';
  }
  function renderState(data) {
    if (!data || state.entering) return;
    state.ready = flag(data.ready) && flag(data.holding);
    const failed = flag(data.failed);
    $('advance').disabled = !state.ready;
    document.body.classList.toggle('ready', state.ready);
    $('retry').hidden = !failed;
    if (state.ready) {
      $('status-label').textContent = 'CARREGAMENTO CONCLUÍDO';
      $('status-title').textContent = 'Tudo pronto.';
      $('status-detail').textContent = data.detail || 'Clique abaixo para assumir seu personagem.';
      $('progress-label').textContent = 'Mundo e personagem preparados';
      $('advance-label').textContent = 'Assumir personagem';
      $('entry-hint').textContent = 'Seu próximo capítulo começa agora.';
      $('entry-note').textContent = 'A música continua até você decidir entrar.';
      $('connection-label').textContent = 'PRONTO · AGUARDANDO VOCÊ';
      setProgress(1);
    } else {
      $('status-label').textContent = failed ? 'AGUARDANDO PONTO DE ENTRADA' : 'PREPARANDO SEU PERSONAGEM';
      $('status-title').textContent = failed ? 'Quase lá.' : 'Preparando sua chegada.';
      $('status-detail').textContent = data.detail || 'Carregando o mundo e preparando seu personagem.';
      $('advance-label').textContent = 'Aguardando carregamento';
      $('entry-note').textContent = 'O botão será liberado quando tudo estiver pronto.';
      $('connection-label').textContent = 'CARREGAMENTO EM ANDAMENTO';
      state.progress = Math.min(95, state.progress);
      setProgress(state.progress / 95);
    }
    if (flag(data.entering) && state.ready) leaveScreen();
  }
  async function callback(name, payload = {}) {
    if (!inGame) return { ok: true };
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2500);
    try {
      const response = await fetch(`https://${resource}/${name}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: controller.signal });
      if (!response.ok) throw new Error('Resposta indisponível');
      return await response.json();
    } finally { clearTimeout(timeout); }
  }
  function leaveScreen() {
    if (state.entering) return;
    state.entering = true;
    diagnostic('fade_iniciado');
    $('advance').disabled = true;
    document.body.classList.add('entering');
    clearInterval(statusTimer);
    clearInterval(uiReadyTimer);
    const initialVolume = audio.volume;
    const started = performance.now();
    const fade = () => {
      const fraction = Math.min(1, (performance.now() - started) / 500);
      audio.volume = initialVolume * (1 - fraction);
      if (fraction < 1) requestAnimationFrame(fade); else audio.pause();
    };
    requestAnimationFrame(fade);
  }
  function closeScreen() {
    visible = false;
    audio.pause();
    clearInterval(statusTimer);
    document.documentElement.classList.add('interactive');
    document.documentElement.classList.remove('active');
    // Reset the document canvas too, not just computed html/body backgrounds.
    document.querySelector('meta[name="color-scheme"]').content = 'normal';
    diagnostic('interface_fechada');
  }
  function activateScreen(data) {
    if (!interactive || visible) return;
    visible = true;
    clearInterval(uiReadyTimer);
    document.documentElement.classList.add('active');
    const saved = data.audio || {};
    if (Number.isFinite(saved.volume)) audio.volume = Math.min(1, Math.max(0, saved.volume));
    if (typeof saved.muted === 'boolean') audio.muted = saved.muted;
    state.wantsMusic = saved.paused !== true;
    const position = Number.isFinite(saved.time) ? Math.max(0, saved.time) : 0;
    const seek = () => {
      if (Number.isFinite(audio.duration)) audio.currentTime = Math.min(position, Math.max(0, audio.duration - .1));
    };
    audio.addEventListener('loadedmetadata', seek, { once: true });
    chooseTrack(Number.isInteger(saved.index) ? saved.index : 0, state.wantsMusic);
    setProgress(Math.min(95, Math.max(0, Number(data.progress) || 0)) / 95);
    renderState(data.state);
    // Audio decoding or autoplay rejection must not delay mouse focus or entry.
    diagnostic('interface_ativada');
    const acknowledge = async attempt => {
      try {
        const reply = await callback('loadingUiActive');
        if (!flag(reply.ok)) throw new Error('Ativação não aceita');
        diagnostic('foco_confirmado');
      } catch (error) {
        diagnostic('foco_erro', { attempt, error: error.message });
        if (attempt < 3 && visible && !state.entering) setTimeout(() => acknowledge(attempt + 1), 500);
        else $('status-detail').textContent = 'A interface não respondeu. Reconecte para tentar novamente.';
      }
    };
    acknowledge(1);
  }
  $('advance').addEventListener('click', async () => {
    if (!state.ready || state.entering || $('advance').disabled) return;
    $('advance').disabled = true;
    try {
      const result = await callback('loadingAdvance');
      if (result.ok) leaveScreen();
      else { renderState({ ready: false, holding: true, failed: true, detail: result.detail }); }
    } catch (_) {
      $('status-detail').textContent = 'A entrada não respondeu. Clique para tentar novamente.';
      $('advance').disabled = false;
    }
  });
  $('retry').addEventListener('click', async () => {
    if (retryPending) return;
    retryPending = true;
    $('retry').disabled = true;
    try {
      const result = await callback('loadingRetry');
      if (result.ok) renderState({ holding: true, ready: false, failed: false, detail: 'Tentando carregar o ponto de entrada novamente.' });
      else $('status-detail').textContent = result.detail || 'Aguarde alguns segundos antes de tentar novamente.';
    } catch (_) { $('status-detail').textContent = 'Aguardando os recursos do servidor. Tente novamente em instantes.'; }
    finally { retryPending = false; $('retry').disabled = false; }
  });
  window.addEventListener('message', event => {
    const data = event.data;
    if (!data || typeof data !== 'object') return;
    if (data.eventName === 'loadProgress') setProgress(data.loadFraction);
    if (data.eventName === 'cidadeLoadingState') renderState(data.state);
    if (data.eventName === 'cidadeLoadingActivate') activateScreen(data);
    if (data.eventName === 'cidadeLoadingClose') closeScreen();
    if (data.eventName === 'cidadeLoadingDiagnose') diagnostic('diagnostico_solicitado');
    if (data.eventName === 'cidadeLoadingHandoff' && !interactive && !handoffPending) {
      handoffPending = true;
      const snapshot = { index: state.index, time: audio.currentTime, volume: audio.volume, muted: audio.muted, paused: audio.paused };
      callback('loadingHandoff', { audio: snapshot, progress: state.progress }).then(result => {
        if (result.ok) { audio.pause(); clearInterval(statusTimer); }
      }).catch(() => { handoffPending = false; });
    }
  });
  async function pollStatus() {
    if (!inGame || !visible || state.entering || handoffPending) return;
    try { renderState(await callback('loadingStatus')); } catch (error) {
      const now = performance.now();
      if (!failureLogs.has('status') || now - failureLogs.get('status') > 15000) {
        failureLogs.set('status', now); diagnostic('status_erro', { error: error.message });
      }
    }
  }
  statusTimer = setInterval(pollStatus, 3000);
  pollStatus();
  fetch('playlist.json').then(response => {
    if (!response.ok) throw new Error('Playlist indisponível');
    return response.json();
  }).then(tracks => {
    state.tracks = tracks;
    tracks.forEach((track, index) => {
      const button = document.createElement('button');
      const number = document.createElement('span');
      number.textContent = String(index + 1).padStart(2, '0');
      button.textContent = track.title;
      button.prepend(number);
      button.addEventListener('click', () => { state.wantsMusic = true; chooseTrack(index); });
      $('playlist').append(button);
    });
    chooseTrack(0, inGame && visible);
  }).catch(() => { $('track-title').textContent = 'Playlist indisponível'; $('audio-status').textContent = 'O carregamento continua normalmente.'; }).finally(() => {
    if (interactive && inGame) {
      const announceReady = async () => {
        if (visible || uiReadyPending) return;
        uiReadyPending = true;
        try {
          const reply = await callback('loadingUiReady');
          if (flag(reply.ok)) { clearInterval(uiReadyTimer); diagnostic('interface_pronta'); }
          else clearInterval(uiReadyTimer); // An already-entered session needs no loading UI.
        } catch (error) { diagnostic('interface_pronta_erro', { error: error.message }); }
        finally { uiReadyPending = false; }
      };
      uiReadyTimer = setInterval(announceReady, 3000);
      announceReady();
    }
  });
  renderAudio();
  diagnostic('documento_iniciado');
  if (preview) {
    document.title = 'Prévia · Minha Cidade';
    $('connection-label').textContent = 'PRÉVIA DA TELA';
    setProgress(.7);
    // Only browser preview has a simulated state; the game always requires Lua.
    setTimeout(() => renderState({ holding: true, ready: true, detail: 'Tudo pronto. Clique abaixo para assumir seu personagem.' }), 1200);
  }
})();
