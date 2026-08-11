from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / 'config' / 'tour_sources.json'
CITY_KEYWORDS = {
    'Minsk': ('минск', 'minsk'),
    'Moscow': ('москва', 'москвы', 'moscow', 'мск'),
    'Istanbul': ('стамбул', 'istanbul'),
    'Warsaw': ('варшав', 'warsaw'),
    'Vilnius': ('вильнюс', 'vilnius'),
    'Kaunas': ('каунас', 'kaunas'),
    'Riga': ('риг', 'riga'),
}
EXCLUDED_KEYWORDS = {
    'Egypt': ('египет', 'egypt'),
    'Turkey': ('турция', 'turkey'),
    'Bulgaria': ('болгария', 'bulgaria'),
}
MEAL_PATTERNS = {
    'UAI': r'ultra\s+all|ультра\s+все',
    'AI': r'\ball\b|все\s+включено',
    'HB': r'\bhb\b|полупансион',
    'BB': r'\bbb\b|завтрак',
}
RUSSIAN_MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}
OFFER_PATTERN = re.compile(r'(?P<hotel>.+?)\s+(?P<stars>[45])\s*\*\s*(?P<meal>UAI|AI|ALL|HB|BB|RO)?\s*[-–—]\s*(?P<price>[\d\s]+)\s*(?P<currency>USD|EUR|BYN|RUB|\$|€|Br)?\s*$', re.I)
PRICE_LINE = re.compile(r'^\s*[\d\s]+\s*(?:USD|EUR|BYN|RUB|\$|€|Br)\s*$', re.I)
FLEXIBLE_HOTEL_PATTERN = re.compile(r'(?m)^(?P<hotel>[^\n]+?)\s+(?P<stars>[45])\s*(?:\*|☀️|⭐)\s*$')
PRICE_PATTERN = re.compile(r'(?P<price>\d[\d\s]{2,})\s*(?P<currency>USD|EUR|BYN|RUB|\$|€|Br)', re.I)


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))


def yaml_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def normalize_offer_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    normalized, index = [], 0
    while index < len(lines):
        current = lines[index]
        if re.search(r'[45]\s*\*.*[-–—]\s*$', current) and index + 1 < len(lines) and PRICE_LINE.match(lines[index + 1]):
            normalized.append(f'{current} {lines[index + 1]}')
            index += 2
        else:
            normalized.append(current)
            index += 1
    return normalized


def find_departure_city(text: str, allowed: list[str]) -> str | None:
    lowered = text.lower()
    return next((city for city in allowed if city in CITY_KEYWORDS and any(word in lowered for word in CITY_KEYWORDS[city])), None)


def find_nights(text: str) -> int | None:
    match = re.search(r'\b(\d{1,2})\s*(?:ноч(?:ь|и|ей)|nights?)\b', text, re.I)
    return int(match.group(1)) if match else None


def date_for_year(day: int, month: int, year: int | None = None) -> datetime:
    now = datetime.now()
    candidate = datetime(year or now.year, month, day)
    if year is None and candidate.date() < now.date():
        candidate = candidate.replace(year=candidate.year + 1)
    return candidate


def find_date(text: str) -> datetime | None:
    numeric = re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', text)
    if numeric:
        return date_for_year(int(numeric.group(1)), int(numeric.group(2)), int(numeric.group(3)))
    textual = re.search(r'\b(\d{1,2})\s+(' + '|'.join(RUSSIAN_MONTHS) + r')\b', text, re.I)
    if textual:
        return date_for_year(int(textual.group(1)), RUSSIAN_MONTHS[textual.group(2).lower()])
    return None


def find_destination(text: str, destinations: dict[str, list[str]]) -> str | None:
    lowered = text.lower()
    return next((destination for destination, aliases in destinations.items() if any(alias in lowered for alias in aliases)), None)


def find_meal_plan(text: str) -> str | None:
    return next((meal for meal, pattern in MEAL_PATTERNS.items() if re.search(pattern, text, re.I)), None)


def is_excluded(text: str, excluded: list[str]) -> bool:
    lowered = text.lower()
    return any(country in EXCLUDED_KEYWORDS and any(word in lowered for word in EXCLUDED_KEYWORDS[country]) for country in excluded)


def parse_valid_until(text: str) -> str | None:
    match = re.search(r'(?:акци\w*|спец\w*|цен\w*|брониров\w*)[^\n]{0,70}?(?:до|по)\s*(\d{1,2}(?:\.\d{1,2}\.\d{4}|\s+(?:' + '|'.join(RUSSIAN_MONTHS) + r')))', text, re.I)
    if not match:
        return None
    value = match.group(1)
    numeric = re.fullmatch(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', value)
    if numeric:
        return date_for_year(int(numeric.group(1)), int(numeric.group(2)), int(numeric.group(3))).date().isoformat()
    textual = re.fullmatch(r'(\d{1,2})\s+(.+)', value, re.I)
    return date_for_year(int(textual.group(1)), RUSSIAN_MONTHS[textual.group(2).lower()]).date().isoformat() if textual else None


def normalize_meal(value: str | None, fallback: str | None) -> str:
    meal = (value or fallback or '').upper()
    if not meal:
        return 'Не указано'
    return 'AI' if meal == 'ALL' else meal


def normalize_currency(value: str | None) -> str:
    return {'$': 'USD', '€': 'EUR', 'BR': 'BYN'}.get((value or 'UNKNOWN').upper(), (value or 'UNKNOWN').upper())


def fetch_posts(channel: str) -> list[dict]:
    response = requests.get(f'https://t.me/s/{channel}', headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = []
    for node in soup.select('.tgme_widget_message[data-post]'):
        ref = node.get('data-post', '')
        if '/' not in ref:
            continue
        _, post_id = ref.rsplit('/', 1)
        text_node = node.select_one('.tgme_widget_message_text')
        text = text_node.get_text('\n', strip=True) if text_node else ''
        date_node = node.select_one('time[datetime]')
        if text:
            posts.append({'channel': channel, 'post_id': post_id, 'text': text, 'published_at': date_node.get('datetime') if date_node else '', 'url': f'https://t.me/{channel}/{post_id}'})
    return posts


def make_flexible_offer(post: dict, city: str, nights: int, departure: datetime, destination: str, valid_until: str | None) -> dict | None:
    hotel_match = FLEXIBLE_HOTEL_PATTERN.search(post['text'])
    prices = list(PRICE_PATTERN.finditer(post['text']))
    if not hotel_match or not prices:
        return None
    first_currency = normalize_currency(prices[0].group('currency'))
    comparable = [match for match in prices if normalize_currency(match.group('currency')) == first_currency]
    selected = min(comparable, key=lambda match: int(re.sub(r'\s+', '', match.group('price'))))
    variants = []
    for match in prices:
        line_start = post['text'].rfind('\n', 0, match.start()) + 1
        line_end = post['text'].find('\n', match.end())
        line = post['text'][line_start:line_end if line_end != -1 else len(post['text'])].strip()
        variants.append(line or f"{match.group('price').strip()} {normalize_currency(match.group('currency'))}")
    group = f"{post['channel'].lower()}-{post['post_id']}"
    return {
        'id': f'{group}-1', 'offer_group_id': group, 'destination_id': destination,
        'hotel': hotel_match.group('hotel').strip(' -–—▫️'), 'stars': int(hotel_match.group('stars')),
        'meal_plan': 'Не указано', 'nights': nights, 'departure_city': city,
        'departure_date': departure.date().isoformat(), 'return_date': (departure + timedelta(days=nights)).date().isoformat(),
        'price': int(re.sub(r'\s+', '', selected.group('price'))), 'currency': first_currency,
        'price_for': 'unknown', 'price_note': 'Варианты стоимости: ' + '; '.join(variants),
        'offer_type': 'special' if valid_until else 'standard', 'special_offer_valid_until': valid_until, 'post': post,
    }


def extract_offers(post: dict, config: dict) -> list[dict]:
    text = post['text']
    city = find_departure_city(text, config['departure_cities'])
    nights = find_nights(text)
    departure = find_date(text)
    destination = find_destination(text, config['destinations'])
    common_meal = find_meal_plan(text)
    if not all((city, nights, departure, destination)) or is_excluded(text, config['excluded_countries']):
        return []
    if not config['nights']['min'] <= nights <= config['nights']['max']:
        return []
    valid_until = parse_valid_until(text)
    price_for = 'per_room' if re.search(r'цен[аы]\s+за\s+(?:номер|dbl)', text, re.I) else 'unknown'
    group, offers = f"{post['channel'].lower()}-{post['post_id']}", []
    for index, line in enumerate(normalize_offer_lines(text), start=1):
        match = OFFER_PATTERN.search(line)
        if not match:
            continue
        stars, meal = int(match.group('stars')), normalize_meal(match.group('meal'), common_meal)
        if stars not in config['hotel_stars'] or (meal != 'Не указано' and meal not in config['meal_plans']):
            continue
        offers.append({'id': f'{group}-{index}', 'offer_group_id': group, 'destination_id': destination, 'hotel': match.group('hotel').strip(' -–—▫️'), 'stars': stars, 'meal_plan': meal, 'nights': nights, 'departure_city': city, 'departure_date': departure.date().isoformat(), 'return_date': (departure + timedelta(days=nights)).date().isoformat(), 'price': int(re.sub(r'\s+', '', match.group('price'))), 'currency': normalize_currency(match.group('currency')), 'price_for': price_for, 'price_note': 'Требуется проверка цены и состава пакета', 'offer_type': 'special' if valid_until else 'standard', 'special_offer_valid_until': valid_until, 'post': post})
    return offers or ([make_flexible_offer(post, city, nights, departure, destination, valid_until)] if make_flexible_offer(post, city, nights, departure, destination, valid_until) else [])


def write_offer(offer: dict, config: dict) -> Path:
    output_dir = ROOT / config['output_directory']
    output_dir.mkdir(parents=True, exist_ok=True)
    post = offer['post']
    filename = output_dir / f"{offer['id']}.md"
    raw_hash = hashlib.sha256(post['text'].encode('utf-8')).hexdigest()[:12]
    lines = ['---', f"id: {yaml_value(offer['id'])}", f"offer_group_id: {yaml_value(offer['offer_group_id'])}", f"destination_id: {yaml_value(offer['destination_id'])}", 'status: draft', f"offer_type: {offer['offer_type']}", f"hotel: {yaml_value(offer['hotel'])}", f"stars: {offer['stars']}", f"meal_plan: {yaml_value(offer['meal_plan'])}", f"nights: {offer['nights']}", f"departure_city: {yaml_value(offer['departure_city'])}", f"departure_date: {offer['departure_date']}", f"return_date: {offer['return_date']}", 'flight: Не указан', f"price: {offer['price']}", f"currency: {offer['currency']}", f"price_for: {offer['price_for']}", f"price_note: {yaml_value(offer['price_note'])}", f"published_at: {post['published_at']}", f"tour_source_url: {post['url']}", f"price_checked_at: {datetime.now(timezone.utc).isoformat()}", f"source_channel: @{post['channel']}", 'passport_country: BY', 'visa_check: manual_review_required', f"source_content_hash: {raw_hash}"]
    if offer['special_offer_valid_until']:
        lines.append(f"special_offer_valid_until: {offer['special_offer_valid_until']}")
    lines.extend(['---', '', '## Исходное предложение', '', post['text'], '', '## Проверка перед публикацией', '', '- [ ] Подтвердить условия въезда для паспорта Беларуси', '- [ ] Проверить цену за двоих и условия пакета', '- [ ] Сменить `status: draft` на `status: active` для публикации'])
    filename.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return filename


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-posts-per-channel', type=int, default=30)
    args = parser.parse_args()
    config, written = load_config(), []
    for channel in config['channels']:
        try:
            posts = fetch_posts(channel)[:args.max_posts_per_channel]
        except requests.RequestException as error:
            print(f'WARNING: @{channel}: {error}')
            continue
        for post in posts:
            written.extend(write_offer(offer, config) for offer in extract_offers(post, config))
    print(f'Created or updated {len(written)} hotel offer drafts')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
