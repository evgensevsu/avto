# ChinAuto Service

Сервисный центр для владельцев китайских автомобилей — личный кабинет, история ТО, контроль SIM-карт, отзывные кампании.

---

## Локальная разработка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/ВАШ_ЛОГИН/chinauto-service.git
cd chinauto-service

# 2. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Скопируйте .env и задайте свой SECRET_KEY
cp .env.example .env
# Отредактируйте .env: придумайте SECRET_KEY (минимум 32 случайных символа)

# 5. Запустите
python app.py
# → http://localhost:5000
```

**Демо-администратор:** `admin@autoservice.ru` / `admin123`

---

## Деплой на Render

### Способ 1 — Blueprint (render.yaml, рекомендуется)

1. Создайте репозиторий на GitHub и залейте код:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/ВАШ_ЛОГИН/chinauto-service.git
   git push -u origin main
   ```

2. Зайдите на [render.com](https://render.com) → **New → Blueprint**

3. Подключите GitHub-репозиторий → Render автоматически прочитает `render.yaml`

4. В Dashboard → **Environment** обязательно проверьте:
   - `SECRET_KEY` — Render генерирует автоматически ✓
   - `DATABASE_PATH` — `/data/autoservice.db` ✓

5. Нажмите **Deploy** → деплой займёт 2–4 минуты

> ⚠️ **Persistent Disk** (`/data`) требует плана **Starter ($7/мес)** или выше.  
> На бесплатном плане БД сбрасывается при каждом перезапуске сервиса.  
> Для теста на Free — уберите секцию `disk:` из `render.yaml` и `DATABASE_PATH` из `envVars`.

---

### Способ 2 — Вручную через Dashboard

1. **New → Web Service** → Connect GitHub repo

2. Заполните поля:

   | Поле | Значение |
   |------|----------|
   | **Name** | `chinauto-service` |
   | **Region** | `Frankfurt (EU Central)` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app -c gunicorn.conf.py` |
   | **Plan** | Free / Starter |

3. **Environment Variables** → Add:

   | Key | Value | Примечание |
   |-----|-------|------------|
   | `SECRET_KEY` | *(нажмите Generate)* | Обязательно |
   | `DATABASE_PATH` | `/data/autoservice.db` | Только если есть диск |
   | `FLASK_ENV` | `production` | |
   | `WEB_CONCURRENCY` | `2` | |

4. Если план Starter+: **Add Disk** → Mount Path: `/data`, Size: 1 GB

5. **Create Web Service** → Deploy

---

### Структура URL после деплоя

```
https://chinauto-service.onrender.com/          # Главная
https://chinauto-service.onrender.com/about     # О нас
https://chinauto-service.onrender.com/contacts  # Контакты
https://chinauto-service.onrender.com/login     # Вход
https://chinauto-service.onrender.com/register  # Регистрация
https://chinauto-service.onrender.com/dashboard # Личный кабинет
https://chinauto-service.onrender.com/admin     # Админ-панель
https://chinauto-service.onrender.com/health    # Health-check (для мониторинга)
```

---

## Структура проекта

```
chinauto-service/
├── app.py                  # Основное Flask-приложение
├── gunicorn.conf.py        # Настройки Gunicorn для продакшена
├── Procfile                # Команда запуска (альтернатива render.yaml)
├── render.yaml             # Blueprint для Render
├── requirements.txt        # Python-зависимости
├── .env.example            # Шаблон переменных окружения
├── .gitignore              # Исключения для git
├── README.md               # Эта документация
├── templates/
│   ├── public_base.html    # Базовый шаблон публичного сайта
│   ├── base.html           # Базовый шаблон личного кабинета
│   ├── index.html          # Главная страница
│   ├── about.html          # О нас
│   ├── contacts.html       # Контакты
│   ├── login.html          # Вход
│   ├── register.html       # Регистрация
│   ├── dashboard.html      # Личный кабинет
│   ├── vehicle_detail.html # Страница автомобиля
│   ├── add_vehicle.html    # Добавление авто
│   ├── edit_vehicle.html   # Редактирование авто
│   ├── order_detail.html   # Заказ-наряд
│   ├── profile.html        # Профиль пользователя
│   └── admin/
│       ├── dashboard.html  # Дашборд администратора
│       ├── users.html      # Клиенты
│       ├── vehicles.html   # Автомобили
│       ├── orders.html     # Заказ-наряды
│       ├── new_order.html  # Создание заказа
│       ├── order_detail.html
│       ├── recalls.html    # Отзывные кампании
│       └── schedule.html   # Регламент ТО
└── static/                 # CSS, JS, изображения (при необходимости)
```

---

## Переменные окружения

| Переменная | Обязательна | Описание |
|-----------|-------------|----------|
| `SECRET_KEY` | **Да** | Ключ шифрования сессий. Минимум 32 случайных символа. |
| `DATABASE_PATH` | Нет | Путь к SQLite-файлу. По умолчанию `instance/autoservice.db` |
| `FLASK_ENV` | Нет | `production` или `development` |
| `FLASK_DEBUG` | Нет | `1` для dev-режима (никогда в продакшене) |
| `PORT` | Нет | Порт сервера. Render подставляет автоматически. |
| `WEB_CONCURRENCY` | Нет | Количество gunicorn-воркеров. По умолчанию `2`. |
| `LOG_LEVEL` | Нет | `debug` / `info` / `warning`. По умолчанию `info`. |

---

## Заметки по безопасности

- `SECRET_KEY` никогда не должен быть в коде или git — только через env
- `FLASK_DEBUG=1` запрещён в продакшене
- SQLite подходит для небольших нагрузок; при росте — мигрируйте на PostgreSQL
- Render автоматически обеспечивает HTTPS через Let's Encrypt
