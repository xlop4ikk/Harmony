/* ============================================================
   Harmony — UI: роутер, виды, привязка плеера.
   Данные берутся с собственного бэкенда (/api/*).
   ============================================================ */

'use strict';

const $ = sel => document.querySelector(sel);

/* ---------------- утилиты ---------------- */

function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function icon(name, cls) {
  return `<svg class="${cls || 'ico'}"><use href="#i-${name}"/></svg>`;
}

function grad(c) {
  return `background: linear-gradient(135deg, ${c[0]}, ${c[1]})`;
}

/** Обложка: картинка через прокси, либо градиентная подложка. */
function coverStyle(t) {
  const img = t.img && API.img(t.img);
  if (img) return `background-image:url("${escapeHtml(img)}");background-size:cover;background-position:center`;
  return grad(Store.gradientFor(t));
}

function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove('show'), 2200);
}

/* ---------------- шаблоны ---------------- */

function trackRow(t, n, ctxIds) {
  const liked = Prefs.isLiked(t.id);
  return `
    <li class="track" data-action="play-track" data-id="${escapeHtml(t.id)}" data-ids="${ctxIds.join(',')}">
      <span class="track__idx">
        <span class="idx-num">${n}</span>
        <svg class="idx-play"><use href="#i-play"/></svg>
        <span class="eq"><i></i><i></i><i></i><i></i></span>
      </span>
      <span class="track__cover" style="${coverStyle(t)}"></span>
      <span class="track__meta">
        <div class="track__title">${escapeHtml(t.title)}</div>
        <div class="track__artist">${escapeHtml(t.artist)}</div>
      </span>
      <span class="track__dur">${fmtTime(t.duration)}</span>
      <button class="track__like icon-btn ${liked ? 'liked' : ''}" data-action="like" data-id="${escapeHtml(t.id)}"
              aria-label="${liked ? 'Убрать из любимых' : 'В любимые'}">
        ${icon(liked ? 'heart-fill' : 'heart')}
      </button>
    </li>`;
}

function trackList(ids) {
  const ts = ids.map(Store.get).filter(Boolean);
  if (!ts.length) return '';
  return `<ul class="tracks">${ts.map((t, i) => trackRow(t, i + 1, ids)).join('')}</ul>`;
}

function mediaCard(item, kind) {
  const href = '#/page/' + encodeURIComponent(item.url);
  const bg = item.img
    ? `background-image:url("${escapeHtml(API.img(item.img))}");background-size:cover;background-position:center`
    : grad(kind === 'artist' ? ['#6d3ff0', '#241056'] : ['#2f57c4', '#101f4d']);
  const sub = kind === 'album'
    ? [item.artist, item.year].filter(Boolean).join(' · ')
    : 'Исполнитель';

  return `
    <a class="card" href="${href}">
      <div class="card__cover" style="${bg}">
        ${item.img ? '' : `<span class="card__icon">${icon(kind === 'artist' ? 'mic' : 'disc')}</span>`}
      </div>
      <div class="card__name">${escapeHtml(item.title)}</div>
      <div class="card__desc">${escapeHtml(sub)}</div>
    </a>`;
}

function emptyState(title, text) {
  return `
    <div class="empty">
      ${icon('music')}
      <div class="empty__title">${title}</div>
      <div class="empty__text">${text}</div>
    </div>`;
}

function spinnerBlock(text) {
  return `
    <div class="loading">
      ${icon('spinner', 'ico spinner')}
      <span>${escapeHtml(text)}</span>
    </div>`;
}

/* ---------------- виды ---------------- */

const POPULAR = ['Metallica', 'Nirvana', 'Кино', 'Король и Шут', 'Måneskin', 'Billie Eilish', 'Rammstein', 'Сектор Газа'];

function greeting() {
  const h = new Date().getHours();
  if (h < 5) return 'Доброй ночи';
  if (h < 12) return 'Доброе утро';
  if (h < 18) return 'Добрый день';
  return 'Добрый вечер';
}

function renderHome() {
  const histIds = Prefs.historyIds().slice(0, 8);
  const histTracks = histIds.map(Store.get).filter(Boolean);
  const likedIds = Prefs.likedTracks();

  return `
    <div class="greet">${greeting()}</div>

    <a class="hero" href="#/search">
      <div class="hero__text">
        <div class="hero__title">Что послушаем?</div>
        <div class="hero__sub">Найди любой трек, альбом или исполнителя</div>
      </div>
      <div class="hero__icon">${icon('search')}</div>
    </a>

    <div class="chips">
      ${POPULAR.map(c => `<button class="chip" data-action="quick-search">${escapeHtml(c)}</button>`).join('')}
    </div>

    ${histTracks.length ? `
    <section class="section">
      <div class="section__head">
        <h3 class="section__title">Недавно слушали</h3>
        <button class="section__more" data-action="play-all" data-ids="${histIds.join(',')}">Слушать все</button>
      </div>
      <div class="tiles">
        ${histTracks.map(t => `
          <div class="tile" data-action="play-track" data-id="${escapeHtml(t.id)}" data-ids="${histIds.join(',')}">
            <span class="mini-cover" style="${coverStyle(t)}"></span>
            <span class="tile__meta">
              <div class="tile__title">${escapeHtml(t.title)}</div>
              <div class="tile__sub">${escapeHtml(t.artist)}</div>
            </span>
          </div>`).join('')}
      </div>
    </section>` : ''}

    <section class="section">
      <div class="section__head">
        <h3 class="section__title">Моя музыка</h3>
      </div>
      <div class="grid">
        <a class="card" href="#/liked">
          <div class="card__cover" style="background: linear-gradient(135deg, #ff5470, #b15cf7)">
            <span class="card__icon">${icon('heart-fill')}</span>
          </div>
          <div class="card__name">Любимые треки</div>
          <div class="card__desc">${likedIds.length ? fmtCount(likedIds.length, ['трек', 'трека', 'треков']) : 'Пока пусто'}</div>
        </a>
      </div>
    </section>`;
}

function renderSearchShell() {
  return `
    <div class="searchbox">
      ${icon('search')}
      <input type="search" id="searchInput" placeholder="Треки, альбомы или исполнители" autocomplete="off">
      <button class="searchbox__clear icon-btn hidden" id="searchClear" aria-label="Очистить">${icon('close')}</button>
    </div>
    <div class="chips">
      ${POPULAR.map(c => `<button class="chip" data-action="chip">${escapeHtml(c)}</button>`).join('')}
    </div>
    <div id="searchResults">${emptyState('Начни поиск', 'Введи название трека, альбома или имени исполнителя.')}</div>`;
}

let searchTimer = null;
let searchSeq = 0;

function runSearch(q) {
  const box = $('#searchResults');
  if (!box) return;

  q = (q || '').trim();
  const clearBtn = $('#searchClear');
  if (clearBtn) clearBtn.classList.toggle('hidden', !q);

  if (!q) {
    box.innerHTML = emptyState('Начни поиск', 'Введи название трека, альбома или имени исполнителя.');
    return;
  }

  box.innerHTML = spinnerBlock(`Ищем «${q}»…`);
  const seq = ++searchSeq;

  API.search(q)
    .then(res => {
      if (seq !== searchSeq) return;            // устаревший ответ
      if (res.error) {
        box.innerHTML = emptyState('Не получилось', escapeHtml(res.error));
        return;
      }
      const trackIds = Store.put(res.tracks);
      renderSearchResults(res, trackIds, q);
    })
    .catch(err => {
      if (seq !== searchSeq) return;
      box.innerHTML = emptyState('Нет связи с бэкендом',
        `Запусти сервер: <b>python server/app.py</b><br>${escapeHtml(err.message)}`);
    });
}

function renderSearchResults(res, trackIds, q) {
  const box = $('#searchResults');
  if (!box) return;

  if (!trackIds.length && !res.albums.length && !res.artists.length) {
    box.innerHTML = emptyState('Ничего не нашлось', `По запросу «${escapeHtml(q)}» результатов нет. Попробуй иначе.`);
    return;
  }

  box.innerHTML = `
    ${res.artists.length ? `
    <section class="section">
      <div class="section__head">
        <h3 class="section__title">Исполнители</h3>
      </div>
      <div class="grid grid--small">${res.artists.map(a => mediaCard(a, 'artist')).join('')}</div>
    </section>` : ''}

    ${res.albums.length ? `
    <section class="section">
      <div class="section__head">
        <h3 class="section__title">Альбомы</h3>
      </div>
      <div class="grid grid--small">${res.albums.map(a => mediaCard(a, 'album')).join('')}</div>
    </section>` : ''}

    ${trackIds.length ? `
    <section class="section">
      <div class="section__head">
        <h3 class="section__title">Треки</h3>
        <button class="section__more" data-action="play-all" data-ids="${trackIds.join(',')}">Слушать все</button>
      </div>
      ${trackList(trackIds)}
    </section>` : ''}`;

  syncRows();
}

function detailHead({ kind, title, stats, img, c, iconId }) {
  const bg = img
    ? `background-image:url("${escapeHtml(API.img(img))}");background-size:cover;background-position:center`
    : grad(c);
  return `
    <div class="detail-head" style="--dc1:${c[0]};--dc2:${c[1]}">
      <div class="detail-head__cover" style="${bg}">
        ${img ? '' : `<span class="card__icon">${icon(iconId)}</span>`}
      </div>
      <div>
        <div class="detail-head__kind">${kind}</div>
        <h1 class="detail-head__title">${escapeHtml(title)}</h1>
        <div class="detail-head__stats">${stats}</div>
      </div>
    </div>`;
}

function detailActions(ids) {
  return `
    <div class="detail-actions">
      <button class="btn-circle" data-action="play-all" data-ids="${ids.join(',')}" aria-label="Слушать">${icon('play')}</button>
      <button class="icon-btn" style="width:46px;height:46px" data-action="shuffle-play" data-ids="${ids.join(',')}" aria-label="Перемешать и слушать">${icon('shuffle')}</button>
    </div>`;
}

function statsFor(tracks) {
  const total = tracks.reduce((s, t) => s + (t.duration || 0), 0);
  const parts = [fmtCount(tracks.length, ['трек', 'трека', 'треков'])];
  if (total) parts.push(Math.round(total / 60) + ' мин');
  return `<b>${parts.join(' · ')}</b>`;
}

let pageSeq = 0;

function renderPage(url) {
  const view = $('#view');
  view.innerHTML = spinnerBlock('Загружаем…');
  const seq = ++pageSeq;

  API.page(url)
    .then(res => {
      if (seq !== pageSeq) return;
      if (res.error) {
        view.innerHTML = emptyState('Ошибка загрузки', escapeHtml(res.error));
        return;
      }
      const ids = Store.put(res.tracks);
      const isArtist = res.kind === 'artist';
      const c = isArtist ? ['#7b2fd6', '#2b1055'] : ['#3547b8', '#101a4d'];

      $('#topTitle').textContent = res.title;
      document.title = res.title + ' — Harmony';

      view.innerHTML = `
        ${detailHead({
          kind: isArtist ? 'Исполнитель' : 'Альбом',
          title: res.title,
          stats: ids.length ? statsFor(res.tracks) : '',
          img: res.cover,
          c,
          iconId: isArtist ? 'mic' : 'disc',
        })}
        ${ids.length ? detailActions(ids) : ''}
        ${ids.length ? trackList(ids) : emptyState('Нет треков', 'На этой странице ничего не нашлось.')}`;
      syncRows();
      syncLikes();
    })
    .catch(err => {
      if (seq !== pageSeq) return;
      view.innerHTML = emptyState('Нет связи с бэкендом', escapeHtml(err.message));
    });
}

function renderLiked() {
  const ids = Prefs.likedTracks();
  if (!ids.length) {
    return emptyState('Пока пусто', 'Нажимай на сердечко рядом с треком — он появится здесь.');
  }
  const tracks = ids.map(Store.get).filter(Boolean);
  return `
    ${detailHead({ kind: 'Коллекция', title: 'Любимые треки', stats: statsFor(tracks), c: ['#ff5470', '#b15cf7'], iconId: 'heart-fill' })}
    ${detailActions(ids)}
    ${trackList(ids)}`;
}

/* ---------------- роутер ---------------- */

const TITLES = { home: 'Главная', search: 'Поиск', liked: 'Любимые треки' };

function route() {
  const raw = location.hash.replace(/^#\/?/, '');
  const slash = raw.indexOf('/');
  const name = slash === -1 ? raw : raw.slice(0, slash);
  const param = slash === -1 ? '' : raw.slice(slash + 1);

  const view = $('#view');
  let title = TITLES[name] || 'Harmony';
  let html = '';
  let active = name;

  switch (name) {
    case 'search':
      html = renderSearchShell();
      break;
    case 'liked':
      html = renderLiked();
      break;
    case 'page':
      title = 'Загрузка…';
      break;
    default:
      html = renderHome();
      active = 'home';
  }

  view.innerHTML = html;
  view.classList.remove('view-anim');
  void view.offsetWidth;
  view.classList.add('view-anim');
  view.scrollTop = 0;

  $('#topTitle').textContent = title;
  if (name !== 'page') document.title = (name === 'home' ? '' : title + ' — ') + 'Harmony';

  document.querySelectorAll('[data-nav]').forEach(a => {
    a.classList.toggle('active', a.dataset.nav === active);
  });

  if (name === 'search') {
    const input = $('#searchInput');
    input.focus();
    input.addEventListener('input', () => {
      clearTimeout(searchTimer);
      const v = input.value;
      searchTimer = setTimeout(() => runSearch(v), 450);
    });
    $('#searchClear').addEventListener('click', () => {
      input.value = '';
      input.focus();
      runSearch('');
    });

    // Поддержка ссылки вида #/search/кино
    const initial = param ? decodeURIComponent(param) : '';
    if (initial) {
      input.value = initial;
      runSearch(initial);
    }
  }

  if (name === 'page') {
    renderPage(decodeURIComponent(param));
  }

  syncRows();
  syncLikes();
}

/* ---------------- лайки ---------------- */

function toggleLikeById(id) {
  const t = Store.get(id);
  if (!t) return;
  const added = Prefs.toggleLike(t);
  toast(added ? `«${t.title}» в любимых` : `«${t.title}» убран из любимых`);
  syncLikes();
  if (location.hash.startsWith('#/liked')) route();
}

function syncLikes() {
  document.querySelectorAll('[data-action="like"]').forEach(btn => {
    const liked = Prefs.isLiked(btn.dataset.id);
    btn.classList.toggle('liked', liked);
    btn.innerHTML = icon(liked ? 'heart-fill' : 'heart');
  });

  const cur = currentTrack();
  const liked = cur ? Prefs.isLiked(cur.id) : false;
  const pb = $('#pbLike');
  pb.classList.toggle('liked', liked);
  pb.innerHTML = icon(liked ? 'heart-fill' : 'heart');
}

/* ---------------- синхронизация плеера и UI ---------------- */

function currentTrack() {
  const st = Player.state;
  return st.idx >= 0 ? Store.get(st.ids[st.idx]) : null;
}

function syncRows() {
  const st = Player.state;
  const cur = currentTrack();
  document.querySelectorAll('.track').forEach(row => {
    const isCur = !!cur && row.dataset.id === cur.id;
    row.classList.toggle('is-current', isCur);
    row.classList.toggle('is-playing', isCur && st.playing);
  });
}

function syncQueuePanel() {
  const st = Player.state;
  const cur = currentTrack();
  const nowEl = $('#queueNow');
  const listEl = $('#queueList');
  const caption = $('#queueNextCaption');

  if (!cur) {
    nowEl.innerHTML = '';
    caption.classList.add('hidden');
    listEl.innerHTML = `<li class="queue__empty">Очередь пуста — включи любой трек.</li>`;
    return;
  }

  caption.classList.remove('hidden');
  nowEl.innerHTML = `
    <div class="queue__now ${st.playing ? 'is-playing' : ''}">
      <span class="mini-cover" style="${coverStyle(cur)}"></span>
      <span class="queue__item-meta">
        <div class="queue__item-title">${escapeHtml(cur.title)}</div>
        <div class="queue__item-artist">${escapeHtml(cur.artist)}</div>
      </span>
      <span class="eq" style="display:flex;margin-left:auto"><i></i><i></i><i></i><i></i></span>
    </div>`;

  const upcoming = st.ids.slice(st.idx + 1);
  listEl.innerHTML = upcoming.map((id, i) => {
    const t = Store.get(id);
    if (!t) return '';
    return `
      <li class="queue__item" data-action="queue-jump" data-index="${st.idx + 1 + i}">
        <span class="mini-cover" style="${coverStyle(t)}"></span>
        <span class="queue__item-meta">
          <div class="queue__item-title">${escapeHtml(t.title)}</div>
          <div class="queue__item-artist">${escapeHtml(t.artist)}</div>
        </span>
        <span class="queue__item-dur">${fmtTime(t.duration)}</span>
      </li>`;
  }).join('') || `<li class="queue__empty">Это последний трек в очереди.</li>`;
}

let lastVolume = 0.8;
let dragging = false;

function syncUI() {
  const st = Player.state;
  const cur = currentTrack();

  $('#btnPlay').innerHTML = icon(st.playing ? 'pause' : 'play');
  $('#btnPlay').setAttribute('aria-label', st.playing ? 'Пауза' : 'Играть');
  $('#btnShuffle').classList.toggle('active', st.shuffle);
  $('#btnRepeat').classList.toggle('active', st.repeat !== 'off');
  $('#btnRepeat').innerHTML = icon(st.repeat === 'one' ? 'repeat-1' : 'repeat');

  const volPct = Math.round(st.volume * 100);
  const vol = $('#volume');
  vol.value = volPct;
  vol.style.setProperty('--p', volPct + '%');
  $('#btnMute').innerHTML = icon(st.volume === 0 ? 'volume-x' : 'volume');

  if (!cur) {
    $('#pbTitle').textContent = 'Не выбран трек';
    $('#pbArtist').textContent = 'Найди музыку через поиск';
    $('#pbCover').style.cssText = '';
    $('#pbCover').classList.remove('has-art');
    $('#curTime').textContent = '0:00';
    $('#durTime').textContent = '0:00';
    $('#progress').value = 0;
    $('#progress').style.setProperty('--p', '0%');
    syncRows();
    syncQueuePanel();
    return;
  }

  $('#pbTitle').textContent = cur.title;
  $('#pbArtist').textContent = cur.artist;

  const cover = $('#pbCover');
  cover.setAttribute('style', coverStyle(cur));
  cover.classList.add('has-art');

  const dur = st.dur || cur.duration || 0;
  const prog = $('#progress');
  prog.max = Math.round(dur) || 100;
  if (!dragging) {
    prog.value = Math.floor(st.pos);
    prog.style.setProperty('--p', (dur ? (st.pos / dur) * 100 : 0) + '%');
    $('#curTime').textContent = fmtTime(st.pos);
  }
  $('#durTime').textContent = fmtTime(dur);

  syncLikes();
  syncRows();
  syncQueuePanel();
}

/* ---------------- действия ---------------- */

function playFrom(ids, index) {
  if (!ids.length) return;
  const i = index || 0;
  Player.play(ids, i);
  const t = Store.get(ids[i]);
  if (t) Prefs.pushHistory(t);
}

document.addEventListener('click', e => {
  const el = e.target.closest('[data-action]');
  if (!el) return;

  const ids = (el.dataset.ids || '').split(',').filter(Boolean);
  const id = el.dataset.id;

  switch (el.dataset.action) {
    case 'play-track': {
      const queue = ids.length ? ids : [id];
      playFrom(queue, Math.max(0, queue.indexOf(id)));
      break;
    }
    case 'play-all':
      e.preventDefault();
      playFrom(ids, 0);
      break;
    case 'shuffle-play':
      Player.setShuffle(true);
      playFrom(ids, Math.floor(Math.random() * ids.length));
      break;
    case 'like':
      e.preventDefault();
      e.stopPropagation();
      toggleLikeById(id);
      break;
    case 'queue-jump':
      playFrom(Player.state.ids, parseInt(el.dataset.index, 10));
      break;
    case 'chip': {
      const input = $('#searchInput');
      if (!input) break;
      input.value = el.textContent;
      document.querySelectorAll('.chip').forEach(c => c.classList.toggle('active', c === el));
      runSearch(input.value);
      break;
    }
    case 'quick-search': {
      const query = el.textContent;
      location.hash = '#/search';
      setTimeout(() => {
        const input = $('#searchInput');
        if (input) { input.value = query; runSearch(query); }
      }, 80);
      break;
    }
  }
});

/* ---------------- элементы управления ---------------- */

$('#btnPlay').addEventListener('click', () => Player.toggle());
$('#btnNext').addEventListener('click', () => Player.next());
$('#btnPrev').addEventListener('click', () => Player.prev());
$('#btnShuffle').addEventListener('click', () => Player.setShuffle(!Player.state.shuffle));
$('#btnRepeat').addEventListener('click', () => Player.cycleRepeat());
$('#pbLike').addEventListener('click', () => {
  const cur = currentTrack();
  if (cur) toggleLikeById(cur.id);
});

const progressEl = $('#progress');
progressEl.addEventListener('input', () => {
  dragging = true;
  progressEl.style.setProperty('--p', (progressEl.value / (progressEl.max || 1)) * 100 + '%');
  $('#curTime').textContent = fmtTime(progressEl.value);
});
progressEl.addEventListener('change', () => {
  Player.seek(parseInt(progressEl.value, 10));
  dragging = false;
});

$('#volume').addEventListener('input', e => Player.setVolume(e.target.value / 100));
$('#btnMute').addEventListener('click', () => {
  if (Player.state.volume > 0) { lastVolume = Player.state.volume; Player.setVolume(0); }
  else Player.setVolume(lastVolume || 0.8);
});

const queuePanel = $('#queuePanel');
$('#btnQueue').addEventListener('click', () => queuePanel.classList.toggle('open'));
$('#btnQueueClose').addEventListener('click', () => queuePanel.classList.remove('open'));

document.addEventListener('keydown', e => {
  const tag = e.target.tagName;
  if (e.code === 'Escape') { queuePanel.classList.remove('open'); return; }
  if (tag === 'INPUT' || tag === 'BUTTON' || tag === 'A' || tag === 'TEXTAREA') return;
  if (e.code === 'Space') { e.preventDefault(); Player.toggle(); }
  else if (e.code === 'ArrowRight' && e.altKey) Player.next();
  else if (e.code === 'ArrowLeft' && e.altKey) Player.prev();
});

window.addEventListener('hashchange', route);

/* ---------------- запуск ---------------- */

(function boot() {
  Player.setVolume(Player.state.volume);
  Player.on(syncUI);
  route();
  syncUI();

  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();
