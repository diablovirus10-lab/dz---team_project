# VK Bot - Модульный чат-бот для ВКонтакте

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-93%20passed-green.svg)]()

Модульный чат-бот для социальной сети ВКонтакте с архитектурой на основе FSM (Finite State Machine), поддержкой PostgreSQL и полным тестовым покрытием.

## 📋 Содержание

- [О проекте](#о-проекте)
- [Архитектура](#архитектура)
- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Запуск](#запуск)
- [Тестирование](#тестирование)
- [Структура проекта](#структура-проекта)
- [API и Контракты](#api-и-контракты)
- [Контакты](#контакты)
- [Статус проекта](#статус-проекта)

---

## 🤖 О проекте

Проект представляет собой образовательный пример реализации чат-бота для ВКонтакте с использованием:
- **Модульной архитектуры** с четким разделением ответственности
- **FSM (Finite State Machine)** для управления диалогами
- **PostgreSQL** для хранения данных пользователей, диалогов и истории сообщений
- **Asyncio** для асинхронной работы с API и базой данных
- **Полного тестового покрытия** (Unit + Integration тесты)

### Основные возможности
- Регистрация и профили пользователей
- Управление диалогами и историей сообщений
- Система команд и намерений (intents)
- Логирование всех запросов к API
- Машину состояний для сложных сценариев общения

---

## 🏗️ Архитектура

Проект следует принципам чистой архитектуры с разделением на слои:

```
┌─────────────────┐
│   main.py       │  ← Точка входа
└────────┬────────┘
         │
┌────────▼────────┐
│   src/bot/      │  ← Бизнес-логика и FSM
│   bot_logic.py  │
│   state_mgr.py  │
└────────┬────────┘
         │
┌────────▼────────┐     ┌──────────────────┐
│ src/database/   │     │ src/vk_api_bot/  │
│ db_manager.py   │     │ vk_client.py     │
│ async_db_mgr.py │     │ (VK API wrapper) │
└────────┬────────┘     └──────────────────┘
         │
┌────────▼────────┐
│   PostgreSQL    │  ← Хранение данных
└─────────────────┘
```

### Слои ответственности

1. **Presentation Layer (`main.py`)**: Инициализация компонентов, запуск Long Polling
2. **Business Logic Layer (`src/bot/`)**: Обработка команд, управление состояниями диалога
3. **Data Access Layer (`src/database/`)**: CRUD операции, транзакции, пул соединений
4. **External Services (`src/vk_api_bot/`)**: Взаимодействие с VK API
5. **Utilities (`src/utils/`)**: Логгер, валидаторы, хелперы

---

## 📦 Требования

- Python 3.11+
- PostgreSQL 15+
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
VK_TOKEN=your_vk_api_token_here
VK_API_VERSION=5.131

# Database Settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vk_bot
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
```

> ⚠️ **Важно**: Никогда не коммитьте файл `.env` в репозиторий! Он добавлен в `.gitignore`.

---

## 🚀 Запуск

### 1. Подготовка базы данных

#### Вариант A: Docker (рекомендуется)

```bash
docker run -d --name vk-bot-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=vk_bot \
  -p 5432:5432 \
  postgres:15-alpine
```

#### Вариант B: Локальная установка

```bash
createdb vk_bot
psql vk_bot -f data/schema.sql
psql vk_bot -f data/initial_data.sql
```

### 2. Применение схемы БД

```bash
psql -h localhost -U postgres -d vk_bot -f data/schema.sql
psql -h localhost -U postgres -d vk_bot -f data/initial_data.sql
```

### 3. Запуск бота

```bash
python main.py
```

Бот запустится в режиме Long Polling и начнет обрабатывать сообщения.

---

## 🧪 Тестирование

Проект имеет полное тестовое покрытие: **81 Unit-тест** + **12 Integration-тестов**.

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
docker run -d --name vk-bot-test \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=vk_bot_test \
  -p 5432:5432 \
  postgres:15-alpine

sleep 5

# Запустите тесты
pytest tests/integration -v

# Очистка
docker stop vk-bot-test && docker rm vk-bot-test
```

### Покрытие кода

```bash
pytest tests --cov=src --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\\index.html  # Windows
```

### Структура тестов

```
tests/
├── unit/
│   ├── test_bot_logic.py       # 21 тест логики бота
│   ├── test_state_manager.py   # Тесты FSM
│   ├── test_vk_client.py       # 60 тестов VK клиента (моки)
│   ├── test_utils.py           # Тесты утилит
│   └── test_validators.py      # Валидация данных
├── integration/
│   └── test_database_integration.py  # 12 тестов БД
├── conftest.py               # Фикстуры pytest
└── README.md                 # Документация по тестам
```

---

## 📁 Структура проекта

```
vk-bot/
├── main.py                     # Точка входа приложения
├── requirements.txt            # Зависимости Python
├── .env.example                # Шаблон переменных окружения
├── .env                        # Переменные окружения (не в git)
├── .gitignore                  # Игнорируемые файлы
├── pytest.ini                  # Конфигурация pytest
├── README.md                   # Эта документация
│
├── data/                       # Данные и схема БД
│   ├── schema.sql              # DDL схема PostgreSQL
│   └── initial_data.sql        # Начальные данные
│
├── src/                        # Исходный код
│   ├── bot/                    # Бизнес-логика
│   │   ├── bot_logic.py        # Основная логика диалогов
│   │   └── state_mgr.py        # Машина состояний (FSM)
│   │
│   ├── database/               # Работа с БД
│   │   ├── db_manager.py       # Синхронный менеджер (для legacy)
│   │   ├── async_db_manager.py # Асинхронный менеджер
│   │   ├── models.py           # Модели данных
│   │   └── exceptions.py       # Исключения БД
│   │
│   ├── vk_api_bot/             # VK API клиент
│   │   └── vk_client.py        # Обертка над VK API
│   │
│   └── utils/                  # Утилиты
│       ├── logger.py           # Настройка логгера
│       ├── helpers.py          # Вспомогательные функции
│       └── validators.py       # Валидация данных
│
├── tests/                      # Тесты
│   ├── unit/                   # Unit-тесты
│   ├── integration/            # Интеграционные тесты
│   ├── conftest.py             # Фикстуры
│   └── README.md               # Документация тестов
│
└── docs/                       # Документация
    └── TESTING.md              # Руководство по тестированию
```

---

## 🔌 API и Контракты

### Database Manager

```python
class DatabaseManager:
    # Пользователи
    async def get_or_create_user(self, vk_id: int, first_name: str, ...) -> User
    async def get_user_by_vk_id(self, vk_id: int) -> Optional[User]
    
    # Диалоги
    async def create_dialog(self, user_id: int, title: str) -> Dialog
    async def get_dialog_messages(self, dialog_id: int) -> List[Message]
    
    # Сообщения
    async def add_message(self, dialog_id: int, sender_id: int, text: str) -> Message
    
    # FSM States
    async def get_state(self, user_id: int) -> Optional[str]
    async def set_state(self, user_id: int, state: str) -> None
    
    # Команды и намерения
    async def log_command(self, user_id: int, command: str) -> CommandLog
    async def detect_intent(self, text: str) -> Intent
```

### VK Client

```python
class VKClient:
    async def send_message(self, peer_id: int, message: str) -> dict
    async def get_user_info(self, user_id: int) -> dict
    async def get_longpoll_server(self) -> dict
    async def execute_longpoll_request(self, server: str, key: str, ts: int) -> dict
```

### Bot Logic

```python
class BotLogic:
    async def handle_message(self, event: dict) -> None
    async def process_command(self, user_id: int, command: str) -> None
    async def handle_fsm_state(self, user_id: int, message: str) -> None
```

---

## 📞 Контакты

По вопросам обращайтесь через Issues на GitHub.

---

## 🎯 Статус проекта

| Компонент | Статус | Тесты |
|-----------|--------|-------|
| Бизнес-логика (Bot) | ✅ Готово | 21 passed |
| VK API Клиент | ✅ Готово | 60 passed |
| База данных (Sync) | ✅ Готово | Моки |
| База данных (Async) | ✅ Готово | 12 integration |
| Утилиты | ✅ Готово | 6 passed |
| FSM Manager | ✅ Готово | В составе bot |
| **Итого** | **✅ Полностью рабочий** | **93 теста** |

---

*Последнее обновление: 2024*