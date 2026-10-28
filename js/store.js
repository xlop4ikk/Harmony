/* ============================================================
   Harmony — хранилище треков и локальных настроек.
   Треки приходят с бэкенда; здесь они лежат в реестре по id,
   а лайки/история сохраняются в localStorage.
   ============================================================ */

'use strict';

const Store = (() => {
  const tracks = new Map();   // id -> track

  function put(list) {
    const ids = [];
    for (const t of list || []) {
      if (!t || !t.url) continue;
      if (!tracks.has(t.id)) tracks.set(t.id, t);
      ids.push(t.id);
    }
    return ids;
  }

  function get(id) { return tracks.get(id); }

  /** Детерминированный градиент — подложка, если обложки нет. */
  function gradientFor(t) {
    const s = (t.artist || '') + (t.title || '');
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    const hue = (h >>> 0) % 360;
    return [`hsl(${hue}, 55%, 45%)`, `hsl(${(hue + 50) % 360}, 60%, 25%)`];
  }

  return { put, get, gradientFor };
})();


/* ---------------- лайки и история ---------------- */

const Prefs = (() => {
  const K_LIKES = 'harmony_likes_v1';
  const K_HIST = 'harmony_history_v1';

  function read(key) {
    try { return JSON.parse(localStorage.getItem(key)) || []; }
    catch { return []; }
  }

  function slim(t) {
    return { id: t.id, title: t.title, artist: t.artist, url: t.url, img: t.img || '', duration: t.duration || null };
  }

  let likes = read(K_LIKES);     // [track]
  let history = read(K_HIST);    // [track]

  function isLiked(id) { return likes.some(t => t.id === id); }

  function toggleLike(t) {
    const i = likes.findIndex(x => x.id === t.id);
    if (i !== -1) likes.splice(i, 1);
    else likes.unshift(slim(t));
    localStorage.setItem(K_LIKES, JSON.stringify(likes));
    return i === -1;
  }

  function likedTracks() {
    // Регистрируем сохранённые треки, чтобы их можно было играть
    Store.put(likes);
    return likes.map(t => t.id);
  }

  function pushHistory(t) {
    const i = history.findIndex(x => x.id === t.id);
    if (i !== -1) history.splice(i, 1);
    history.unshift(slim(t));
    if (history.length > 30) history.length = 30;
    localStorage.setItem(K_HIST, JSON.stringify(history));
  }

  function historyIds() {
    Store.put(history);
    return history.map(t => t.id);
  }

  return { isLiked, toggleLike, likedTracks, pushHistory, historyIds, get likes() { return likes; } };
})();


/* ---------------- форматирование ---------------- */

function fmtTime(sec) {
  if (sec == null || isNaN(sec)) return '--:--';
  sec = Math.max(0, Math.floor(sec));
  return Math.floor(sec / 60) + ':' + String(sec % 60).padStart(2, '0');
}

function fmtCount(n, forms) {
  // forms: ['трек', 'трека', 'треков']
  const mod10 = n % 10, mod100 = n % 100;
  let f = forms[2];
  if (mod10 === 1 && mod100 !== 11) f = forms[0];
  else if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) f = forms[1];
  return `${n} ${f}`;
}
