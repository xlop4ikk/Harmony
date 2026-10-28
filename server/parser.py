"""
Harmony — парсер rus.hitmotop.com.

Поиск: треки, альбомы, исполнители.
Страницы альбома/артиста: список треков со ссылками на MP3.
"""

import json
import re
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://rus.hitmotop.com"

# Хосты, с которых разрешено качать аудио и картинки
ALLOWED_HOSTS = ('hitmotop.com', 'hitmoz.org', 'hitmcdn.com', 'yandex.net', 'yandex.ru')

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': BASE_URL + '/',
})


# ---------------------------------------------------------------- helpers

def _abs(url: str) -> str:
    """Привести URL к абсолютному (протокол-относительные //host тоже)."""
    if not url:
        return ''
    url = url.strip()
    if url.startswith('//'):
        return 'https:' + url
    return urljoin(BASE_URL, url)


def host_allowed(url: str) -> bool:
    host = urlparse(url).hostname or ''
    return any(host == h or host.endswith('.' + h) for h in ALLOWED_HOSTS)


def _parse_duration(text: str):
    """'04:51' -> 291"""
    if not text:
        return None
    parts = [int(p) for p in re.findall(r'\d+', text)]
    if not parts:
        return None
    total = 0
    for p in parts:
        total = total * 60 + p
    return total


def _extract_tracks(soup) -> list:
    """Разобрать все li.tracks__item со страницы."""
    tracks = []
    seen = set()

    for item in soup.find_all('li', class_='tracks__item'):
        musmeta = item.get('data-musmeta')
        if not musmeta:
            continue
        try:
            data = json.loads(musmeta)
        except json.JSONDecodeError:
            continue

        url = _abs(data.get('url', ''))
        if not url or url in seen:
            continue
        seen.add(url)

        title_el = item.find('div', class_='track__title')
        desc_el = item.find('div', class_='track__desc')
        time_el = item.find('div', class_='track__fulltime')

        title = title_el.get_text(strip=True) if title_el else data.get('title', '')
        artist = desc_el.get_text(strip=True) if desc_el else data.get('artist', '')

        tracks.append({
            'id': data.get('id') or ('t-' + str(abs(hash(url)) % 10 ** 12)),
            'title': title or 'Без названия',
            'artist': artist or 'Неизвестный исполнитель',
            'url': url,
            'img': _abs(data.get('img', '')),
            'duration': _parse_duration(time_el.get_text(strip=True)) if time_el else None,
        })

    return tracks


def _extract_album_items(soup, kind: str) -> list:
    """album-item на сайте — это и артисты (/artist/), и альбомы (/album/)."""
    out = []
    seen = set()

    for item in soup.find_all('li', class_='album-item'):
        link = item.find('a', href=True)
        if not link:
            continue
        href = link['href']
        if kind == 'album' and '/album/' not in href:
            continue
        if kind == 'artist' and '/artist/' not in href:
            continue

        url = _abs(href)
        if url in seen:
            continue
        seen.add(url)

        title_el = item.find('span', class_='album-title')
        raw_title = title_el.get_text(' ', strip=True) if title_el else link.get_text(' ', strip=True)
        raw_title = re.sub(r'\s+', ' ', raw_title).strip()

        singer_el = item.find('span', class_='album-singer')
        singer = singer_el.get_text(' ', strip=True) if singer_el else ''

        img = ''
        img_el = item.find('span', class_='album-image')
        if img_el:
            m = re.search(r"url\(['\"]?([^'\")]+)['\"]?\)", img_el.get('style', ''))
            if m:
                img = _abs(m.group(1))
        if not img:
            tag = item.find('img', src=True)
            if tag:
                img = _abs(tag['src'])

        year = None
        m = re.search(r'\((\d{4})\)', raw_title)
        if m:
            year = int(m.group(1))
            raw_title = re.sub(r'\s*\(\d{4}\)\s*', ' ', raw_title).strip()

        out.append({
            'title': raw_title or 'Без названия',
            'artist': singer,
            'url': url,
            'img': img,
            'year': year,
        })

    return out


def _fetch_html(url: str):
    resp = SESSION.get(url, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser')


# ---------------------------------------------------------------- public API

def search(query: str) -> dict:
    """Поиск по сайту. Возвращает треки, альбомы и исполнителей."""
    url = f'{BASE_URL}/search?q={quote(query)}'
    try:
        soup = _fetch_html(url)
    except requests.RequestException as e:
        return {'tracks': [], 'albums': [], 'artists': [], 'error': f'Ошибка сети: {e}'}

    return {
        'tracks': _extract_tracks(soup)[:60],
        'albums': _extract_album_items(soup, 'album')[:20],
        'artists': _extract_album_items(soup, 'artist')[:12],
        'error': None,
    }


def page(url: str) -> dict:
    """Страница альбома или исполнителя: заголовок, обложка, треки."""
    kind = 'artist' if '/artist/' in url else 'album'

    try:
        soup = _fetch_html(url)
    except requests.RequestException as e:
        return {'kind': kind, 'title': '', 'cover': '', 'tracks': [], 'error': f'Ошибка сети: {e}'}

    h1 = soup.find('h1')
    title = h1.get_text(' ', strip=True) if h1 else ''
    title = re.sub(r'\s*[-—–]\s*слушать все песни.*$', '', title, flags=re.I).strip()
    title = re.sub(r'\s+', ' ', title)

    tracks = _extract_tracks(soup)

    cover = ''
    og = soup.select_one('meta[property="og:image"]')
    if og and og.get('content'):
        cover = _abs(og['content'])
    if not cover and tracks:
        cover = tracks[0]['img']

    return {
        'kind': kind,
        'title': title or ('Альбом' if kind == 'album' else 'Исполнитель'),
        'cover': cover,
        'tracks': tracks,
        'error': None,
    }


def proxy_headers(url: str) -> dict:
    """Заголовки для проксирования аудио/картинки."""
    return {'Referer': BASE_URL + '/', 'User-Agent': SESSION.headers['User-Agent']}
