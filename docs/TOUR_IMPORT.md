# Импорт туров

## Хранение карточек

Каждый тур хранится отдельным Markdown-файлом в `docs/.vitepress/content/tours/`. Загрузчик `tours.data.ts` считывает frontmatter всех файлов по маске `.vitepress/content/tours/*.md`.

Название файла должно быть стабильным и строиться из идентификатора предложения, например `toursmsk-maldives-2026-12-10-7.md`.

## Обязательный frontmatter

```md
---
id: toursmsk-maldives-2026-12-10-7
offer_group_id: toursmsk-example-resort-minsk-2026-12-10-7
destination_id: maldives
status: draft
hotel: Example Resort
stars: 5
meal_plan: AI
nights: 7
departure_city: Minsk
departure_date: '2026-12-10'
return_date: '2026-12-17'
flight: Не указан
price: 5400
currency: EUR
price_for: per_two
price_note: Стоимость за двоих
published_at: '2026-08-09T20:30:00+03:00'
tour_source_url: https://t.me/toursmsk/123
---

Краткое описание предложения.
```

## Источники

- Telegram-каналы: `@LTCB2B`, `@toursmsk`, канал «Ростинг».
- Каждая карточка должна содержать постоянную ссылку на исходный пост в `tour_source_url`.

## Правила публикации

Тур получает статус `active`, если выполнены все условия:

- Вылет из Minsk, Moscow или Istanbul.
- Длительность от 5 до 10 ночей включительно.
- Отель 4 или 5 звёзд.
- Страна не Egypt, Turkey или Bulgaria.
- Для паспорта путешественника не требуется виза; проверка выполняется по справочнику направлений.
- Питание: AI, UAI, BB или HB.
- Цена за двоих: до 6 000 EUR для AI/UAI либо до 4 000 EUR для BB/HB.

Если обязательные данные не распознаны, создаётся запись `draft` для ручной проверки.

## Цена и дедупликация

`price` хранит исходную цену, `currency` — валюту, а `price_for` указывает базу цены: `per_person`, `per_two`, `per_room` или `unknown`. Бюджетный фильтр применяется только после достоверного приведения суммы к стоимости за двоих.

`offer_group_id` формируется из источника, отеля, города вылета, даты вылета и количества ночей. При изменении цены обновляется существующий Markdown-файл и `price_checked_at`, а не создаётся дубль.
