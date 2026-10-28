"""
Harmony — Flask-сервер.
Раздаёт фронтенд и API для поиска/стриминга музыки.

Запуск:  python server/app.py
Открыть: http://localhost:5000
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import requests
from flask import Flask, jsonify, request, send_from_directory, Response

import parser as music

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=ROOT, static_url_path='')

# ---------- CORS ----------
# Разрешённые origin для фронтенда, выложенного отдельно (например, GitHub Pages).
# По умолчанию разрешены все — бэкенд отдаёт только публичные данные.
# В проде лучше задать список:
#   set HARMONY_ORIGINS=https://user.github.io,http://localhost:5000
_ORIGINS_ENV = os.environ.get('HARMONY_ORIGINS', '').strip()
ALLOWED_ORIGINS = [o.strip() for o in _ORIGINS_ENV.split(',') if o.strip()] or ['*']


@app.after_request
def add_cors_headers(resp):
    origin = request.headers.get('Origin', '')
    if '*' in ALLOWED_ORIGINS:
        resp.headers['Access-Control-Allow-Origin'] = '*'
    elif origin in ALLOWED_ORIGINS:
        resp.headers['Access-Control-Allow-Origin'] = origin
        resp.headers['Vary'] = 'Origin'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Range, Content-Type'
    resp.headers['Access-Control-Expose-Headers'] = 'Content-Range, Content-Length, Accept-Ranges'
    return resp


@app.errorhandler(music.SourceError)
def source_unavailable(err):
    """Источник (зеркало с музыкой) отклонил запрос — понятный ответ вместо 500."""
    return jsonify({
        'error': 'source_unavailable',
        'detail': str(err),
        'hint': 'Зеркало отклонило запрос с IP этого сервера. Попробуй ещё раз через '
                'несколько секунд; если ошибка постоянная только в интернете — '
                'источник блокирует адреса дата-центров.',
    }), 502


# ---------- Static ----------

@app.route('/')
def index():
    return send_from_directory(ROOT, 'index.html')


# ---------- API ----------

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'tracks': [], 'albums': [], 'artists': [], 'error': 'Пустой запрос'})
    result = music.search(q)
    return jsonify(result)


@app.route('/api/page')
def api_page():
    """Страница альбома или артиста: список треков."""
    url = request.args.get('url', '').strip()
    if not url or not music.host_allowed(url):
        return jsonify({'kind': '', 'title': '', 'cover': '', 'tracks': [], 'error': 'Некорректный URL'})
    result = music.page(url)
    return jsonify(result)


@app.route('/api/stream')
def api_stream():
    """Прокси аудио-потока с поддержкой Range (для перемотки)."""
    url = request.args.get('url', '').strip()
    if not url or not music.host_allowed(url):
        return Response('Forbidden URL', status=403)

    try:
        # Пробрасываем Range, чтобы работала перемотка в плеере
        upstream = music.fetch_resource(url, {'Range': request.headers.get('Range')})
    except music.SourceError as e:
        return Response(f'Источник недоступен: {e}', status=502)
    except requests.RequestException as e:
        return Response(f'Upstream error: {e}', status=502)

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=16384):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    resp_headers = {}
    for h in ('Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges'):
        v = upstream.headers.get(h)
        if v:
            resp_headers[h] = v
    resp_headers['Accept-Ranges'] = 'bytes'
    resp_headers['Cache-Control'] = 'public, max-age=86400'

    status = upstream.status_code if upstream.status_code in (200, 206) else 200
    return Response(generate(), status=status, headers=resp_headers)


@app.route('/api/img')
def api_img():
    """Прокси картинок обложек."""
    url = request.args.get('url', '').strip()
    if not url or not music.host_allowed(url):
        return Response('Forbidden URL', status=403)

    try:
        resp = music.fetch_resource(url)
    except music.SourceError as e:
        return Response(str(e), status=502)
    except requests.RequestException as e:
        return Response(str(e), status=502)

    def generate():
        try:
            for chunk in resp.iter_content(chunk_size=16384):
                if chunk:
                    yield chunk
        finally:
            resp.close()

    ct = resp.headers.get('Content-Type', 'image/jpeg')
    return Response(generate(), status=200, headers={
        'Content-Type': ct,
        'Cache-Control': 'public, max-age=604800',
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('HARMONY_DEBUG', '0') == '1'
    print(f'Harmony запущен: http://localhost:{port}')
    app.run(host='0.0.0.0', port=port, debug=debug)
