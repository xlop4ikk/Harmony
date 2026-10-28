/* ============================================================
   Harmony — real audio player (HTML5 <audio>).
   ============================================================ */

'use strict';

const Player = (() => {
  const audio = new Audio();
  audio.preload = 'none';

  const state = {
    ids: [],
    idx: -1,
    playing: false,
    pos: 0,
    dur: 0,
    volume: parseFloat(localStorage.getItem('harmony_vol')) || 0.8,
    shuffle: false,
    repeat: 'off', // 'off' | 'all' | 'one'
  };

  const _listeners = [];
  let _timer = null;

  function emit() {
    for (const f of _listeners) f(state);
  }

  // ---- audio event wiring ----
  audio.addEventListener('timeupdate', () => {
    state.pos = audio.currentTime;
    emit();
  });

  audio.addEventListener('loadedmetadata', () => {
    state.dur = audio.duration;
    emit();
  });

  audio.addEventListener('ended', () => {
    if (state.repeat === 'one') {
      audio.currentTime = 0;
      audio.play().catch(() => {});
    } else {
      _next(true);
    }
  });

  audio.addEventListener('play', () => { state.playing = true; emit(); });
  audio.addEventListener('pause', () => { state.playing = false; emit(); });
  audio.addEventListener('error', () => {
    // Some upstream streams fail — skip to next
    if (state.playing) {
      state.playing = false;
      _next(true);
    }
  });

  // ---- helpers ----
  function _start() {
    stop();
    _timer = setInterval(() => { state.pos = audio.currentTime; emit(); }, 250);
  }

  function stop() {
    if (_timer) { clearInterval(_timer); _timer = null; }
  }

  function _next(auto) {
    if (state.ids.length === 0) return;
    if (state.shuffle && state.ids.length > 1) {
      let next;
      do { next = Math.floor(Math.random() * state.ids.length); } while (next === state.idx);
      state.idx = next;
    } else {
      state.idx++;
      if (state.idx >= state.ids.length) {
        if (state.repeat === 'all') state.idx = 0;
        else { stop(); state.playing = false; emit(); return; }
      }
    }
    _load(state.idx);
  }

  function _prev() {
    if (audio.currentTime > 3) { audio.currentTime = 0; return; }
    if (state.idx > 0) state.idx--;
    _load(state.idx);
  }

  function _load(i) {
    const t = Store.get(state.ids[i]);
    if (!t) { stop(); state.playing = false; emit(); return; }
    state.idx = i;
    const src = API.stream(t.url);
    audio.src = src;
    audio.load();
    state.dur = 0;
    state.pos = 0;
    state.playing = true;
    audio.play().catch(() => { state.playing = false; emit(); });
    _start();
    _mediaSession(t);
    emit();
  }

  // ---- Media Session API (OS-level playback controls) ----
  function _mediaSession(t) {
    if (!('mediaSession' in navigator)) return;
    navigator.mediaSession.metadata = new MediaMetadata({
      title: t.title,
      artist: t.artist,
    });
    navigator.mediaSession.setActionHandler('play', resume);
    navigator.mediaSession.setActionHandler('pause', pause);
    navigator.mediaSession.setActionHandler('previoustrack', _prev);
    navigator.mediaSession.setActionHandler('nexttrack', () => _next(true));
  }

  // ---- public API ----

  function on(fn) { _listeners.push(fn); }

  function play(ids, i) {
    stop();
    state.ids = ids.slice();
    state.idx = i != null ? Math.max(0, i) : 0;
    if (state.idx >= state.ids.length) state.idx = 0;
    _load(state.idx);
  }

  function toggle() {
    if (!state.ids.length) return;
    if (state.playing) pause();
    else resume();
  }

  function pause() {
    audio.pause();
    stop();
    emit();
  }

  function resume() {
    if (state.playing) return;
    if (!state.ids.length) return;
    if (state.idx < 0) { play(state.ids); return; }
    state.playing = true;
    audio.play().catch(() => { state.playing = false; emit(); });
    _start();
    emit();
  }

  function next() { _next(false); }
  function prev() { _prev(); }

  function seek(sec) {
    sec = Math.max(0, Math.min(sec, state.dur || audio.duration || 0));
    audio.currentTime = sec;
    state.pos = sec;
    emit();
  }

  function seekFrac(f) { seek(Math.max(0, Math.min(f, 1)) * (state.dur || 1)); }

  function setVolume(v) {
    state.volume = Math.max(0, Math.min(1, v));
    audio.volume = state.volume;
    localStorage.setItem('harmony_vol', state.volume);
    emit();
  }

  function setShuffle(v) { state.shuffle = !!v; emit(); }

  function cycleRepeat() {
    state.repeat = state.repeat === 'off' ? 'all' : state.repeat === 'all' ? 'one' : 'off';
    emit();
  }

  return {
    get state() { return state; },
    get audio() { return audio; },
    on, play, toggle, pause, resume, next, prev, seek, seekFrac,
    setVolume, setShuffle, cycleRepeat,
  };
})();
