# Harmony

Минималистичный веб-плеер: поиск и прослушивание музыки через собственный бэкенд-парсер.

## Возможности

- Поиск треков, альбомов и исполнителей
- Воспроизведение с перемоткой, громкостью, shuffle и repeat
- Обложки через прокси (без CORS-проблем)
- Любимые треки и история прослушивания (localStorage)
- Очередь воспроизведения
- PWA: установка на устройство, офлайн-доступ к интерфейсу
- Адаптивный дизайн (десктоп + мобильный)

## Архитектура

```
index.html          фронтенд
css/style.css       тёмная тема
js/config.js        адрес бэкенда (для деплоя)
js/api.js           клиент API
js/store.js         реестр треков, лайки, история
js/player.js        HTML5 <audio> движок
js/app.js           роутер, виды, привязка UI
server/parser.py    парсер источника музыки
server/app.py       Flask API
sw.js               service worker
```

## Локальный запуск

Нужен Python 3.10+.

```bash
pip install -r requirements.txt
python server/app.py
```

Открыть http://localhost:5000

## Деплой

Фронтенд и бэкенд деплоятся отдельно, потому что GitHub Pages отдаёт только статику.

### 1. Бэкенд — Render (бесплатно)

1. Зарегистрируй репозиторий на https://render.com (New → Web Service).
2. Настройки:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --dir server`
   - **Root directory:** `server` (или путь к `server/`)
   - **Environment variables:**
     - `HARMONY_ORIGINS=https://<username>.github.io` (чтобы ограничить CORS)
3. После деплоя получишь адрес вида `https://harmony-api.onrender.com`.

Бесплатный тариф «засыпает» без запросов — первый запрос после простоя может занять ~50 секунд.

### 2. Фронтенд — GitHub Pages

1. Впиши адрес бэкенда в `js/config.js`:

   ```js
   window.HARMONY_CONFIG = {
     apiBase: 'https://harmony-api.onrender.com',
   };
   ```

2. Запушь код в ветку `main` (или отдельную ветку `gh-pages`).
3. В репозитории: **Settings → Pages → Source: Deploy from a branch** → выбери ветку и корень `/`.
4. Сайт будет доступен на `https://<username>.github.io/<repo>/`.

### 3. HTTPS-микс

Если фронтенд на HTTPS (github.io), бэкенд тоже должен быть на HTTPS — иначе браузер заблокирует запросы как mixed content. Render выдаёт HTTPS из коробки.

### Файл `.nojekyll`

В репозитории лежит пустой `.nojekyll` — он отключает обработку Jekyll на GitHub Pages, иначе файлы вида `__pycache__` или папки с подчёркиванием не будут отданы.

## API

| Метод | Описание |
|---|---|
| `GET /api/search?q=<запрос>` | Поиск: `{tracks, albums, artists}` |
| `GET /api/page?url=<ссылка>` | Страница альбома/артиста: `{kind, title, cover, tracks}` |
| `GET /api/stream?url=<mp3>` | Прокси аудио с поддержкой `Range` |
| `GET /api/img?url=<картинка>` | Прокси обложек |

## Горячие клавиши

- `Пробел` — играть/пауза
- `Alt + →` — следующий трек
- `Alt + ←` — предыдущий трек
- `Esc` — закрыть панель очереди

## Ограничения

- Парсер зависит от вёрстки источника: если сайт изменит классы, парсинг сломается.
- Бесплатный Render засыпает — первый запрос медленный.
- Flask-сервер (`python server/app.py`) — только для разработки; в проде используйте `gunicorn`.
- Аудио и картинки проксируются через бэкенд, что создаёт трафик на сервере.
