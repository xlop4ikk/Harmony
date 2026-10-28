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
    const r = await fetch(url(path) + '?' + qs, {
      headers: { Accept: 'application/json' },
    });

    let data = null;
    try {
      data = await r.json();
    } catch (e) {
      data = null;
    }

    if (!r.ok) throw new Error(errorMessage(data, r.status));
    if (data === null) throw new Error('Бэкенд вернул некорректный ответ');

    return data;
  }

  // Текст ошибки: сначала подсказка бэкенда, затем статус
  function errorMessage(data, status) {
    if (data && (data.detail || data.error)) {
      const main = data.detail || data.error;
      return data.hint ? main + ' ' + data.hint : main;
    }
    if (status === 404) return 'Ничего не найдено';
    if (status >= 500) return `Бэкенд не отвечает (${status})`;
    return `Сервер ответил ${status}`;
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
