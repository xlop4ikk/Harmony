/* ============================================================
   Harmony — клиент API (собственный бэкенд на Flask).

   Базовый адрес берётся из js/config.js (window.HARMONY_CONFIG.apiBase).
   Пустая строка = тот же origin (локальный запуск server/app.py).
   ============================================================ */

'use strict';

const API = (() => {
  const BASE = ((window.HARMONY_CONFIG || {}).apiBase || '').replace(/\/+$/, '');

  function url(path) {
    return BASE + path;
  }

  async function getJSON(path, params) {
    const qs = new URLSearchParams(params).toString();
    const r = await fetch(url(path) + '?' + qs);
    if (!r.ok) throw new Error(`Сервер ответил ${r.status}`);
    return r.json();
  }

  return {
    /** Поиск: треки, альбомы, исполнители. */
    search(q) {
      return getJSON('/api/search', { q });
    },

    /** Страница альбома или исполнителя. */
    page(pageUrl) {
      return getJSON('/api/page', { url: pageUrl });
    },

    /** Аудио через прокси: обходит CORS и поддерживает Range (перемотку). */
    stream(trackUrl) {
      return url('/api/stream?url=' + encodeURIComponent(trackUrl));
    },

    /** Обложка через прокси. */
    img(imgUrl) {
      if (!imgUrl) return '';
      return url('/api/img?url=' + encodeURIComponent(imgUrl));
    },

    /** Базовый адрес бэкенда ('' = тот же origin). */
    get base() { return BASE; },
  };
})();
