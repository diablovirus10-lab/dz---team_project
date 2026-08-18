# 🚀 VKinder — VK Dating Bot

Бот для знакомств ВКонтакте, который подбирает пары на основе возраста, пола, города, интересов и других критериев с весовыми коэффициентами.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-166%20passed-green.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)]()

## 📋 Содержание

- [О проекте](#о-проекте)
- [Архитектура](#архитектура)
- [Возможности](#возможности)
- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Запуск](#запуск)
- [Тестирование](#тестирование)
- [Структура проекта](#структура-проекта)
- [API и Контракты](#api-и-контракты)
- [База данных](#база-данных)
- [Статус проекта](#статус-проекта)

---

## 🤖 О проекте

VKinder — это умный бот для знакомств ВКонтакте, который:

- **Анализирует профиль пользователя** (возраст, пол, город, интересы)
- **Подбирает кандидатов** по сложным алгоритмам с весовыми коэффициентами
- **Показывает популярные фотографии** и фото с отметками
- **Позволяет лайкать фото**, добавлять в избранное и чёрный список
- **Обходит ограничение VK** на выдачу в 1000 человек

### Основные возможности

**Основной функционал:**
- Поиск пользователей по возрасту, полу и городу
- Получение 3 самых популярных фотографий (по лайкам)
- Просмотр кандидатов с навигацией "Далее"
- Добавление в избранное и просмотр списка избранных
- Чёрный список для исключения неподходящих кандидатов

**Дополнительный функционал:**
- Лайки на фотографии кандидатов
- Просмотр фотографий с отметками пользователя
- Поиск по интересам (группы, книги, музыка) с анализом текста
- Весовые коэффициенты критериев поиска
- Обход лимита в 1000 человек через пагинацию и смещение параметров
- Интерактивные кнопки для управления

### Технологии

- Python 3.11+
- PostgreSQL 15+
- VK API 5.131
- SQLAlchemy (ORM)
- asyncpg (асинхронная БД)
- pytest (тестирование)
- Docker (опционально)

---

## 🏗️ Архитектура

Проект построен по модульному принципу с чётким разделением ответственности:

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                    (Точка входа / Entry Point)                   │
│                                                                  │
│  VkApi → VkLongPoll → event loop → bot.handle_event(event)      │
└────────────────┬──────────────────────┬─────────────────────────┘
                 │                      │
    ┌────────────▼────────┐   ┌─────────▼──────────────────────┐
    │   src/bot/          │   │    src/vk_api_bot/             │
    │   (Управление       │   │    (VK API Client)             │
    │    диалогом)        │   │                                │
    │                     │   │  • VKClient                    │
    │  • BotLogic         │   │    - search_users()            │
    │    Маршрутизатор    │   │    - send_message()            │
    │    FSM-состояний    │   │    - get_user_profile()        │
    │                     │   │    - get_user_photos()         │
    │  • StateManager     │   │    - get_user_interests()      │
    │    FSM (5 состояний)│   │    - get_common_friends()      │
    │    IDLE, WAIT_*,    │   │                                │
    │    BROWSING         │   │  • api_utils                   │
    │                     │   │    - batch_request             │
    │  • keyboards.py     │   │    - handle_vk_api_error       │
    │    VK Keyboard JSON │   │    - retry_on_rate_limit       │
    │                     │   │    - parse_vk_*(parsers)       │
    │  • message_formatter│   │                                │
    │    Форматирование   │   │  • exceptions                  │
    │    сообщений        │   │    - VKAuthError               │
    │                     │   │    - VKAccessDeniedError       │
    │                     │   │    - VKUserNotFoundError       │
    └─────────┬───────────┘   └────────────────────────────────┘
              │
              │  зависит от (через интерфейсы)
              │
    ┌─────────▼──────────────────────────────────┐
    │           src/database/                    │
    │           (Хранение данных)                 │
    │                                            │
    │  • Database (db_manager.py)                │
    │    CRUD операции, транзакции               │
    │    - get_or_create_user()                  │
    │    - add_favorite() / remove_from_favorites│
    │    - add_blacklist() / remove_from_bl      │
    │    - mark_viewed()                         │
    │    - get_favorites() / get_blacklist()     │
    │    - get_viewed_vk_ids()                   │
    │    - save_candidate_interests()            │
    │    - get_search_weights()                  │
    │                                            │
    │  • DatabaseAdapter (adapter.py)            │
    │    Адаптер-декоратор, приводит интерфейс   │
    │    Database к контракту, ожидаемому        │
    │    BotLogic (add_favorite(profile) и т.д.) │
    │                                            │
    │  • models.py                               │
    │    ORM-модели (SQLAlchemy)                 │
    │                                            │
    │  • async_db_manager.py                     │
    │    Асинхронная версия БД                   │
    │                                            │
    │  • config.py                               │
    │    Конфигурация подключения (PG)           │
    │                                            │
    │  • exceptions.py                           │
    │    DatabaseError                           │
    └────────────────────────────────────────────┘
              │
    ┌─────────▼───────────────┐   ┌─────────────────────────┐
    │   src/utils/            │   │   tests/                │
    │   (Утилиты)             │   │   (pytest)              │
    │                         │   │   - test_db.py          │
    │  • logger.py            │   │   - test_bot_logic.py   │
    │    Настройка логгера    │   │   - test_state_manager  │
    │                         │   │   - test_formatter      │
    │  • validators.py        │   │   - test_keyboards      │
    │    Валидация данных     │   │   - test_vk_api/        │
    │                         │   │   - test_database_int.  │
    │  • helpers.py           │   │   - conftest.py         │
    │    Вспомогательные      │   │                         │
    │    функции              │   └─────────────────────────┘
    └─────────────────────────┘
```

### Описание компонентов

#### **main.py** — Точка входа
Инициализирует подключение к VK API через `VkLongPoll`, запускает цикл обработки событий и передаёт их в `BotLogic`.

#### **src/bot/** — Логика диалога
- **BotLogic**: Маршрутизатор событий, управляет FSM-состояниями пользователя
- **StateManager**: Машина состояний (IDLE, WAIT_AGE, WAIT_SEX, WAIT_CITY, BROWSING)
- **keyboards.py**: Генерация inline-клавиатур для VK (Далее, В избранное, В чёрный список, Лайк)
- **message_formatter**: Форматирование сообщений с кандидатами

#### **src/vk_api_bot/** — Клиент VK API
- **VKClient**: Обёртка над VK API методы:
  - `search_users()` — поиск кандидатов с учётом весовых коэффициентов
  - `get_user_photos()` — получение фото с сортировкой по лайкам
  - `get_photos_with_tags()` — фото с отметками пользователя
  - `get_user_interests()` — анализ интересов (группы, книги, музыка)
  - `like_photo()` — постановка/снятие лайка
  - `analyze_interests_similarity()` — анализ схожести интересов с весами
- **api_utils**: Утилиты для работы с API (batch requests, retry logic, parsers)
- **exceptions**: Специфичные исключения VK API

#### **src/database/** — Работа с данными
- **Database (db_manager.py)**: CRUD операции, транзакции
  - `add_to_favorites()`, `remove_from_favorites()`
  - `add_to_blacklist()`, `remove_from_blacklist()`
  - `mark_viewed()`, `get_viewed_vk_ids()`
  - `save_candidate_interests()`, `get_search_weights()`
  - `like_photo()`, `get_photos_with_tags()`
- **DatabaseAdapter**: Адаптер для приведения интерфейса БД к контракту бота
- **models.py**: SQLAlchemy ORM модели (12 таблиц)
- **async_db_manager.py**: Асинхронная версия для интеграционных тестов
- **config.py**: Конфигурация подключения к PostgreSQL

#### **src/utils/** — Утилиты
- **logger.py**: Настройка логгера
- **validators.py**: Валидация входных данных
- **helpers.py**: Вспомогательные функции

#### **tests/** — Тестирование
- Unit-тесты логики, БД, VK API, клавиатур, форматтера
- Интеграционные тесты с реальной БД (166 тестов всего)
- Покрытие кода: 92%

---

## 📦 Требования

- Python 3.11+
- PostgreSQL 15+
- Токен VK API с правами: `messages`, `photos`, `users`, `groups`, `friends`
- Docker (опционально, для тестирования)

### Зависимости Python

Все зависимости указаны в `requirements.txt`:

```txt
vk-api==11.9.9
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.0
pytest-cov==4.1.0
asyncpg==0.29.0
sqlalchemy==2.0.23
```

Установка:
```bash
pip install -r requirements.txt
```

---

## ⚙️ Конфигурация

### Переменные окружения

Создайте файл `.env` в корне проекта на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните файл `.env`:

```env
# VK API Settings
VK_TOKEN=your_vk_service_token
VK_API_VERSION=5.131

# Database Settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vkinder
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development

# Search Settings (optional)
DEFAULT_CITY_ID=1
DEFAULT_AGE_FROM=18
DEFAULT_AGE_TO=35
DEFAULT_SEX=1
```

> ⚠️ **Важно**: Никогда не коммитьте файл `.env` в репозиторий! Он добавлен в `.gitignore`.

---

## 🚀 Запуск

### 1. Подготовка базы данных

#### Вариант A: Docker (рекомендуется)

```bash
docker run -d --name vkinder-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=vkinder \
  -p 5432:5432 \
  postgres:15-alpine
```

#### Вариант B: Локальная установка

```bash
createdb vkinder
psql vkinder -f data/schema.sql
psql vkinder -f data/seed.sql
```

### 2. Применение схемы БД

```bash
psql -h localhost -U postgres -d vkinder -f data/schema.sql
psql -h localhost -U postgres -d vkinder -f data/seed.sql
```

### 3. Запуск бота

```bash
python main.py
```

Бот запустится в режиме Long Polling и начнет обрабатывать сообщения.

---

## 🧪 Тестирование

Проект имеет полное тестовое покрытие: **166 тестов** (Unit + Integration).

### Запуск всех тестов

```bash
# Требуется запущенный PostgreSQL для интеграционных тестов
pytest tests -v
```

### Запуск только Unit-тестов (без БД)

```bash
pytest tests -m "not integration" -v
```

### Запуск только Integration-тестов

```bash
# Сначала поднимите БД
docker run -d --name vkinder-test \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=vkinder_test \
  -p 5432:5432 \
  postgres:15-alpine

sleep 5

# Запустите тесты
pytest tests/integration -v

# Очистка
docker stop vkinder-test && docker rm vkinder-test
```

### Покрытие кода

```bash
pytest tests --cov=src --cov-report=html --cov-report=term-missing
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\\index.html  # Windows
```

Покрытие кода: **92%**

### Структура тестов

```
tests/
├── unit/
│   ├── test_bot_logic.py       # 39 тестов логики бота
│   ├── test_state_manager.py   # Тесты FSM
│   ├── test_vk_client.py       # 76 тестов VK клиента (моки)
│   ├── test_keyboards.py       # Тесты клавиатур
│   ├── test_formatter.py       # Тесты форматирования
│   └── test_utils.py           # Тесты утилит
├── integration/
│   └── test_database_integration.py  # 17 тестов БД
├── conftest.py               # Фикстуры pytest
└── README.md                 # Документация по тестам
```

---

## 📁 Структура проекта

```
vkinder/
├── main.py                     # Точка входа приложения
├── requirements.txt            # Зависимости Python
├── .env.example                # Шаблон переменных окружения
├── .env                        # Переменные окружения (не в git)
├── .gitignore                  # Игнорируемые файлы
├── pytest.ini                  # Конфигурация pytest
├── README.md                   # Эта документация
│
├── data/                       # Данные и схема БД
│   ├── schema.sql              # DDL схема PostgreSQL (12 таблиц)
│   └── seed.sql                # Начальные данные (веса поиска)
│
├── src/                        # Исходный код
│   ├── bot/                    # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── bot_logic.py        # Основная логика диалогов
│   │   ├── state_manager.py    # Машина состояний (FSM)
│   │   ├── keyboards.py        # Inline-клавиатуры VK
│   │   └── message_formatter.py # Форматирование сообщений
│   │
│   ├── database/               # Работа с БД
│   │   ├── __init__.py
│   │   ├── db_manager.py       # Синхронный менеджер БД
│   │   ├── async_db_manager.py # Асинхронный менеджер
│   │   ├── adapter.py          # Адаптер интерфейсов
│   │   ├── models.py           # SQLAlchemy ORM модели
│   │   ├── config.py           # Конфигурация подключения
│   │   └── exceptions.py       # Исключения БД
│   │
│   ├── vk_api_bot/             # VK API клиент
│   │   ├── __init__.py
│   │   ├── vk_client.py        # Обертка над VK API
│   │   ├── api_utils.py        # Утилиты API (batch, retry)
│   │   └── exceptions.py       # Исключения VK API
│   │
│   └── utils/                  # Утилиты
│       ├── __init__.py
│       ├── logger.py           # Настройка логгера
│       ├── helpers.py          # Вспомогательные функции
│       └── validators.py       # Валидация данных
│
├── tests/                      # Тесты
│   ├── unit/                   # Unit-тесты
│   │   ├── test_bot_logic.py
│   │   ├── test_state_manager.py
│   │   ├── test_vk_client.py
│   │   ├── test_keyboards.py
│   │   └── test_formatter.py
│   ├── integration/            # Интеграционные тесты
│   │   ├── test_database_integration.py
│   │   └── README.md
│   ├── conftest.py             # Фикстуры pytest
│   └── __init__.py
│
├── docs/                       # Документация
│   ├── TESTING.md              # Руководство по тестированию
│   └── ARCHITECTURE.md         # Детали архитектуры
│
└── logs/                       # Логи бота
    └── vkinder.log
```

---

## 🔌 API и Контракты

### VKClient

```python
class VKClient:
    # Поиск и профили
    async def search_users(self, age_from: int, age_to: int, sex: int, 
                          city: str, offset: int = 0) -> List[User]
    async def search_users_weighted(self, user_profile: dict, 
                                   weights: dict) -> List[User]
    async def get_user_profile(self, user_id: int) -> User
    async def get_user_photos(self, user_id: int, count: int = 3) -> List[Photo]
    async def get_photos_with_tags(self, user_id: int) -> List[Photo]
    
    # Интересы
    async def get_user_interests(self, user_id: int) -> Interests
    async def analyze_interests_similarity(self, user1: Interests, 
                                          user2: Interests) -> float
    
    # Взаимодействия
    async def like_photo(self, owner_id: int, photo_id: int, 
                        unmark: bool = False) -> bool
    async def send_message(self, peer_id: int, message: str, 
                          attachments: list = None) -> bool
    
    # Утилиты
    async def get_common_friends(self, user1_id: int, 
                                user2_id: int) -> List[int]
    async def batch_request(self, requests: list) -> List[dict]
```

### DatabaseManager

```python
class DatabaseManager:
    # Пользователи
    async def get_or_create_user(self, vk_id: int, first_name: str, 
                                last_name: str, age: int, ...) -> User
    async def get_user_by_vk_id(self, vk_id: int) -> Optional[User]
    
    # Избранное и чёрный список
    async def add_to_favorites(self, user_id: int, 
                              candidate_vk_id: int) -> bool
    async def remove_from_favorites(self, user_id: int, 
                                   favorite_id: int) -> bool
    async def get_favorites(self, user_id: int) -> List[Candidate]
    
    async def add_to_blacklist(self, user_id: int, 
                              candidate_vk_id: int) -> bool
    async def remove_from_blacklist(self, user_id: int, 
                                   blacklist_id: int) -> bool
    async def get_blacklist(self, user_id: int) -> List[Candidate]
    
    # Просмотренные
    async def mark_viewed(self, user_id: int, candidate_vk_id: int) -> bool
    async def get_viewed_vk_ids(self, user_id: int) -> Set[int]
    
    # Интересы и веса
    async def save_candidate_interests(self, candidate_vk_id: int, 
                                      interests: dict) -> bool
    async def get_search_weights(self, user_id: int) -> SearchWeights
    
    # Лайки
    async def like_photo(self, user_id: int, photo_url: str, 
                        is_like: bool) -> bool
    async def get_liked_photos(self, user_id: int) -> List[Photo]
```

### BotLogic

```python
class BotLogic:
    async def handle_start(self, user_id: int) -> None
    async def handle_search_command(self, user_id: int, 
                                   params: dict) -> Candidate
    async def handle_next(self, user_id: int) -> Candidate
    async def handle_favorite(self, user_id: int, 
                             candidate: Candidate) -> bool
    async def handle_blacklist(self, user_id: int, 
                              candidate: Candidate) -> bool
    async def handle_like(self, user_id: int, photo: Photo) -> bool
    async def handle_show_favorites(self, user_id: int) -> List[Candidate]
```

---

## 💾 База данных

### Схема БД (12 таблиц)

| Таблица | Описание |
|---------|----------|
| `users` | Пользователи бота (VK ID, имя, возраст, пол, город) |
| `candidates` | Кандидаты на знакомство |
| `favorites` | Избранные кандидаты |
| `blacklist` | Чёрный список |
| `viewed_profiles` | Просмотренные профили |
| `likes` | Лайки на фотографии |
| `user_interests` | Интересы пользователей (группы, книги, музыка) |
| `search_weights` | Весовые коэффициенты критериев поиска |
| `dialogues` | Диалоги с ботом |
| `messages` | История сообщений |
| `fsm_states` | Состояния FSM |
| `api_logs` | Логирование запросов к VK API |

Схема БД находится в файле [`data/schema.sql`](data/schema.sql).

---

## 📞 Контакты

По вопросам обращайтесь через Issues на GitHub.

---

## 🎯 Статус проекта

| Компонент | Статус | Тесты | Покрытие |
|-----------|--------|-------|----------|
| Бизнес-логика (Bot) | ✅ Готово | 39 passed | 94% |
| VK API Клиент | ✅ Готово | 76 passed | 91% |
| База данных (Sync) | ✅ Готово | Моки | - |
| База данных (Async) | ✅ Готово | 17 integration | 88% |
| Утилиты | ✅ Готово | 12 passed | 95% |
| FSM Manager | ✅ Готово | В составе bot | 93% |
| Клавиатуры | ✅ Готово | 8 passed | 100% |
| Форматтер | ✅ Готово | 14 passed | 97% |
| **Итого** | **✅ Полностью рабочий** | **166 тестов** | **92%** |

### Основные возможности

| Функция | Статус |
|---------|--------|
| Поиск по возрасту, полу, городу | ✅ Реализовано |
| Получение 3 популярных фото | ✅ Реализовано |
| Навигация "Далее" | ✅ Реализовано |
| Избранное | ✅ Реализовано |
| Чёрный список | ✅ Реализовано |
| Лайки на фото | ✅ Реализовано |
| Фото с отметками | ✅ Реализовано |
| Поиск по интересам | ✅ Реализовано |
| Весовые коэффициенты | ✅ Реализовано |
| Обход лимита 1000 | ✅ Реализовано |
| Интерактивные кнопки | ✅ Реализовано |

---

*Последнее обновление: 2024*