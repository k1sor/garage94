# Garage Vinyl

Интернет-магазин виниловых пластинок на Flask (учебный проект).

## Стек

- Python, Flask
- SQLite + Flask-SQLAlchemy
- Flask-Login, Flask-WTF

## База данных

ER-диаграмма: `docs/er-diagram.png`, SQL-схема: `docs/schema.sql`.

Таблицы: `users`, `products`, `orders`, `order_items`.

## Запуск

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed.py
python run.py
```

Сайт: http://127.0.0.1:5000/

Тестовый сотрудник после `seed.py`: `admin` / `admin12345`.

`seed.py` загружает пластинки из Deezer (нужен интернет), флаг `--no-clear` не удаляет старые товары.

## Настройки

Настройки лежат в `.env` (пример в `.env.example`). Файл `.env` и база `*.db` не загружаются в git.

## Страницы

- `/` - главная
- `/shop/` - каталог
- `/product/<slug>/` - пластинка
- `/artist/<artist_slug>/` - артист
- `/cart/` - корзина
- `/checkout/` - оформление заказа
- `/accounts/register/`, `/accounts/login/`, `/accounts/profile/` - аккаунт
- `/dashboard/products/` - панель сотрудника
