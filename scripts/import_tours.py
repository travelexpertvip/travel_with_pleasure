from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / 'config' / 'tour_sources.json'

CITY_KEYWORDS = {
    'Minsk': ('минск', 'minsk'),
    'Moscow': ('москва', 'moscow', 'мск'),
    'Istanbul': ('стамбул', 'istanbul'),
    'Warsaw': ('варшвава', 'warsaw'),
    'Vilnius': ('вильнюс', 'vilnius'),
    'Kaunas': ('каунас', 'kaunas'),
    'Riga': ('рига', 'riga'),
}
EXCLUDED_KEYWORDS = {
    'Egypt': ('египет', 'egypt'),
    'Turkey': ('турция', 'turkey'),
    'Bulgaria': ('болгария', 'bulgaria'),
}
MEAL_PATTERNS = {
    'UAI': r'ultra\s+all|ультра\s+все',
    'AI': r'all\s*inclusive|все\s+включено',
    'HB': r'\bhb\b|полупансион',
    'BB': r'\bbb\b|завтрак',
}

def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))

def slug(value: str) -> str:
    value = re.sub(r'[^a-z0-9]+', '-', value.lower())
    return value.strip('-') or 'post'

def find_departure_city(text: str, allowed: list[str]) -> str | None:
    lowered = text.lower()
    for city in allowed:
        if any(keyword in lowered for keyword in CITY_KEYWORDS.get(city, ())):
            return city
    return None

def find_nights(text: str) -> int | None:
    match = re.search(r'\b(\d{1,2})\s*(?:ноч(?:ь|и|ей)|nights?)\b', text, re.I)
    return int(match.group(1)) if match else None

def find_stars(text: str) -> int | None:
    match = re.search(r'\b([1-5])\s*(?:\*|зв(?:езд|ёзд))', text, re.I)
    return int(match.group(1)) if match else None

def find_meal_plan(text: str) -> str | None:
    for meal_plan, pattern in MEAL_PATTERNS.items():
        if re.search(pattern, text, re.I):
            return meal_plan
    return None

def has_excluded_country(text: str, excluded: list[str]) -> bool:
    lowered = text.lower()
    return any(any(keyword in lowered for keyword in EXCLUDED_KEYWORDS.get(country, ())) for country in excluded)

def fetch_posts(channel: str) -> list[dict]:
    url = f'https://t.me/s/{channel}'
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = []
    for node in soup.select('.tgme_widget_message[data-post]'):
        post_ref = node.get('data-post', '')
        if '/' not in post_ref:
            continue
        _, post_id = post_ref.rsplit('/', 1)
        text_node = node.select_one('.tgme_widget_message_text')
        text = text_node.get_text('\n', strip=True) if text_node else ''
        date_node = node.select_one('time[datetime]')
        published_at = date_node.get('datetime') if date_node else None
        if text:
            posts.append({'channel': channel, 'post_id': post_id, 'text': text, 'published_at': published_at, 'url': f'https://t.me/{channel}/{post_id}'})
    return posts

def write_draft(post: dict, config: dict) -> Path | None:
    text = post['text']
    city = find_departure_city(text, config['departure_cities'])
    nights = find_nights(text)
    stars = find_stars(text)
    meal_plan = find_meal_plan(text)
    if not city or not nights or not stars or not meal_plan:
        return None
    if not config['nights']['min'] <= nights <= config['nights']['max']:
        return None
    if stars not in config['hotel_stars'] or has_excluded_country(text, config['excluded_countries']):
        return None

    output_dir = ROOT / config['output_directory']
    output_dir.mkdir(parents=True, exist_ok=True)
    record_id = f"{post['channel'].lower()}-{post['post_id']}"
    filename = output_dir / f'{slug(record_id)}.md'
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]
    body = f"""---
id: {record_id}
status: draft
source_channel: @{post['channel']}
tour_source_url: {post['url']}
published_at: {post['published_at'] or ''}
collected_at: {datetime.now(timezone.utc).isoformat()}
departure_city_detected: {city}
nights_detected: {nights}
stars_detected: {stars}
meal_plan_detected: {meal_plan}
passport_country: {config['passport_country']}
visa_check: manual_review_required
content_hash: {digest}
---

## Исходный пост

{escape(text)}

## Проверка перед публикацией

- [ ] Подтвердить страну и `destination_id`
- [ ] Подтвердить безвизовый въезд для паспорта Беларуси
- [ ] Подтвердить даты вылета и возврата
- [ ] Подтвердить отель, категорию, питание и цену за двоих
- [ ] Перенести в `.vitepress/content/tours/` и заполнить обязательный frontmatter
"""
    filename.write_text(body, encoding='utf-8')
    return filename

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-posts-per-channel', type=int, default=30)
    args = parser.parse_args()
    config = load_config()
    created = []
    for channel in config['channels']:
        try:
            posts = fetch_posts(channel)[:args.max_posts_per_channel]
        except requests.RequestException as error:
            print(f'WARNING: @{channel}: {error}')
            continue
        for post in posts:
            try:
                draft = write_draft(post, config)
            except OSError as error:
                print(f'WARNING: {post["url"]}: {error}')
                continue
            if draft:
                created.append(draft)
    print(f'Created or updated {len(created)} draft files')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
