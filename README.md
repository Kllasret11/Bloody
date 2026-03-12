# Bloody Shop Bot

Telegram-магазин на aiogram 2 + asyncpg.

## Что есть
- каталог по категориям
- корзина и оформление заказа
- промокоды
- баланс
- SOS поддержка
- админ-панель
- категории и товары
- складской остаток
- реферальная система

## Запуск
1. Скопируй `.env.example` в `.env`
2. Заполни токен и `DATABASE_URL`
3. Установи зависимости: `pip install -r requirements.txt`
4. Запусти: `python app.py`

## Структура
- `handlers/` — обработчики Telegram
- `keyboards/` — клавиатуры
- `states/` — FSM состояния
- `services/` — бизнес-логика
- `repositories/` — слой доступа к данным
- `utils/` — база и утилиты
