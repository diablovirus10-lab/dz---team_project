# Тесты (папка `tests/`)

Юнит-тесты пакета `src/bot` запускаются **без PostgreSQL и без доступа к VK API**:
все внешние зависимости подменены фейками в `conftest.py`.

## Состав файлов

| Файл | Что проверяет |
|---|---|
| `conftest.py` | Общие фикстуры и фейки: `FakeVKClient`, `FakeDatabase`, `make_event`, `make_profile` |
| `test_state_manager.py` | FSM диалога: переходы состояний, данные пользователя, `reset` |
| `test_keyboards.py` | Схема клавиатур VK: тип/цвет кнопок, payload-JSON, наборы команд |
| `test_message_formatter.py` | Тексты: приветствие, карточка анкеты, список лайков, fallback-ссылка |
| `test_bot_logic.py` | Сквозные сценарии диалога: меню → поиск → анкеты → лайки |
| `test_database.py` | Тесты слоя БД — владелец: ответственный за `src/database` |
| `test_vk_api.py` | Тесты VK-обёртки — владелец: ответственный за `src/vk_api` |
| `integration/test_database_integration.py` | Интеграционные тесты с реальной PostgreSQL |

## Запуск

Выполняется из корня проекта:

```bash
pip install -r requirements.txt        # нужен pytest
python -m pytest tests -v              # все тесты
python -m pytest tests/test_bot_logic.py -v   # один файл
python -m pytest tests -k "age" -v     # только тесты с "age" в имени
```

### Запуск интеграционных тестов

Для интеграционных тестов требуется PostgreSQL:

```bash
# Вариант 1: Docker (рекомендуется)
docker run -d --name vk-bot-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=vk_bot_test \
  -p 5432:5432 \
  postgres:15-alpine
sleep 5
pytest tests/integration/test_database_integration.py -v
docker stop vk-bot-postgres && docker rm vk-bot-postgres

# Вариант 2: Только unit-тесты (без БД)
pytest tests -m "not integration" -v
```

Подробности в [tests/integration/README.md](../tests/integration/README.md).

## Контракт и фейки

`BotLogic` общается с чужими модулями через контракт (см. docstring класса):

- `vk_client`: `send_message(user_id, text, keyboard, attachments)`,
  `search_users(sex, age, city) -> list[profile]`;
- `database`: `get_or_create_user`, `add_favorite`, `add_blacklist`,
  `mark_viewed`, `get_favorites`, `get_viewed_vk_ids`.

В тестах вместо них работают ин-мемори `FakeVKClient` и `FakeDatabase`.
Это даёт два бонуса:

1. тесты идут локально и в CI без секретов, БД и сети;
2. фейки — живая документация контракта для владельцев `src/database` и `src/vk_api`.

Хелперы:

- `make_event(user_id, text, cmd)` — событие как `MESSAGE_NEW` из LongPoll:
  `event.obj.message = {"from_id", "text", "payload"}`, payload — JSON-строка
  с ключом `cmd` (как у кнопок клавиатуры);
- `make_profile(vk_id, ...)` — профиль с полями таблицы `candidates`
  из `schema.sql` (`vk_id`, `first_name`, `last_name`, `age`, `city`, `sex`,
  `profile_link`, `photos` с `photo_id` в формате `photo<owner>_<id>`).

## Доступные фикстуры

`logic`, `fake_vk`, `fake_db`, `state_manager`, `event_factory`, `profile_factory`.

## Как добавить свой тест

```python
def test_example(logic, fake_vk, state_manager, event_factory, profile_factory):
    fake_vk.profiles = [profile_factory(111)]
    logic.handle_event(event_factory(cmd="search"))
    # ...шаги диалога...
    assert state_manager.get_state(1) == ...
```

## Что покрыто в `src/bot`

- старт (`start` / «начать») → приветствие + главная клавиатура;
- поиск: пол → возраст → город → показ анкеты с вложениями (до 3 фото);
- параметры поиска уходят в `search_users` (`sex` = 1/2 как в ВК и схеме БД);
- лайк → `favorites`, дизлайк → `blacklist`, показ → `viewed_candidates`;
- просмотренные анкеты повторно не показываются;
- валидация возраста (число 14–99) и повторный запрос при ошибке;
- кнопка «В меню» выходит из любого шага ввода;
- список лайков: пустой и непустой;
- сообщения от чатов/сообществ (`user_id < 0`) игнорируются;
- пользователь регистрируется в `users` при первом обращении.