-- таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,                              -- ID
    vk_id BIGINT UNIQUE NOT NULL,                       -- ID VK
    first_name VARCHAR(100),                            -- Имя
    last_name VARCHAR(100),                             -- Фамилия
    age INTEGER,                                        -- Возраст
    city VARCHAR(100),                                  -- Город
    sex INTEGER,                                        -- Пол: 1 - женский, 2 - мужской
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- Дата регистрации в боте
);

-- таблица кандидатов
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,                              -- ID
    vk_id BIGINT UNIQUE NOT NULL,                       -- ID VK
    first_name VARCHAR(100),                            -- Имя
    last_name VARCHAR(100),                             -- Фамилия
    age INTEGER,                                        -- Возраст
    city VARCHAR(100),                                  -- Город
    sex INTEGER,                                        -- Пол: 1 - женский, 2 - мужской
    profile_link VARCHAR(255),                          -- Ссылка на профиль VK
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP      -- Дата регистрации в боте
);

-- таблица фотографий
CREATE TABLE IF NOT EXISTS photos (
    id SERIAL PRIMARY KEY,                                               -- ID
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,    --ID в таблице candidates
    photo_url VARCHAR(255) NOT NULL,                                     -- Ссылка на фото
    photo_id VARCHAR(100) NOT NULL,                                      -- ID фото в VK
    likes_count INTEGER DEFAULT 0,                                       -- Количество лайков
    comments_count INTEGER DEFAULT 0,                                    -- Количество комментариев (Можно использовать для определения популярности: likes + comments)
    is_avatar BOOLEAN DEFAULT FALSE,                                     -- Это аватарка, (Если у пользователя нет других фото, показываем аватарку)
    is_tagged BOOLEAN DEFAULT FALSE,                                     -- Отмеченные фото
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                      --Дата и время добавления фото
    UNIQUE(candidate_id, photo_id)
);

-- таблица найденных людей
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,                                              -- ID
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,             -- ID пользователя из таблицы users
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,   -- ID кандидата из таблицы candidates
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                       -- Когда добавили в избранное
    UNIQUE(user_id, candidate_id)                                       -- Не дает добавить кандимдата дважды
);

-- таблица черного списка
CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,                                              -- ID
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,             -- ID пользователя из таблицы users
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,   -- ID кандидата из таблицы candidates
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                       -- Когда заблокировал
    UNIQUE(user_id, candidate_id)                                       -- Не дает добавить кандимдата
);

-- интересы пользователя бота
CREATE TABLE IF NOT EXISTS user_interests (
    id SERIAL PRIMARY KEY,                                              -- ID
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,             -- ID пользователя из таблицы users
    type VARCHAR(20) NOT NULL,                                          -- Тип интереса
    value VARCHAR(255) NOT NULL,                                        -- название исполнителя/книги/группы
    vk_entity_id VARCHAR(50),                                           -- ID группы по интересам или аудиозаписи или кнги  в ВК
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                     -- Когда добавлен интерес в бот
    UNIQUE(user_id, type, value)                                        -- Не даёт добавить один и тот же интерес дважды
);

-- интересы кандидатов
CREATE TABLE IF NOT EXISTS interests (
    id SERIAL PRIMARY KEY,                                             -- ID
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,  -- ID кандидата из таблицы candidates
    type VARCHAR(20) NOT NULL,                                         -- Тип интереса
    value VARCHAR(255) NOT NULL,                                       -- название исполнителя/книги/группы
    vk_entity_id VARCHAR(50),                                          -- ID группы по интересам или аудиозаписи или кнги  в ВК
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                    -- Когда добавлен интерес в бот
    UNIQUE(candidate_id, type, value)                                  -- чтобы не дублировать интересы
);

-- критерии поиска
CREATE TABLE IF NOT EXISTS search_weights (
    id SERIAL PRIMARY KEY,                                              -- ID
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,             -- ID пользователя из таблицы users
    criterion_name VARCHAR(50) NOT NULL,                                -- Название критерия поиска age, common_friends, music, books, groups
    weight DECIMAL(3,2) DEFAULT 1.00,                                   -- Вес критерия от 0.00 до 1.00
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                     -- Дата последнего обновления веса
    UNIQUE(user_id, criterion_name)                                     -- У одного пользователя не может быть двух весов для одного критерия
);

-- просмотренные кандидаты
CREATE TABLE IF NOT EXISTS viewed_candidates (
    id SERIAL PRIMARY KEY,                                             -- ID
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,            -- ID пользователя из таблицы users
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,  --ID в таблице candidates
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                     -- Дата и время просмотра
    UNIQUE(user_id, candidate_id)                                      -- Не даёт записать один просмотр дважды
);

-- обход лимита пользователей
CREATE TABLE IF NOT EXISTS search_offsets (
    id SERIAL PRIMARY KEY,                                             -- ID
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,            -- ID пользователя из таблицы users
    offset_value INTEGER DEFAULT 0,                                    -- Текущий сдвиг при поиске
    batch_size INTEGER DEFAULT 20,                                     -- сколько загружаем за раз
    search_params TEXT,                                                -- параметры поиска (JSON)
    total_found INTEGER DEFAULT 0,                                     -- сколько всего найдено
    last_search_timestamp TIMESTAMP,                                   -- когда последний раз искали
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                    -- Время последненго обновления
    UNIQUE(user_id)                                                    -- У одного пользователя может быть только одна запись с параметрами поиска
);

-- =========================
-- Индексы для ускорения запросов
-- =========================

-- Внешние ключи (по user_id)
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_blacklist_user_id ON blacklist(user_id);
CREATE INDEX IF NOT EXISTS idx_viewed_candidates_user_id ON viewed_candidates(user_id);
CREATE INDEX IF NOT EXISTS idx_search_weights_user_id ON search_weights(user_id);

-- Поля candidate_id
CREATE INDEX IF NOT EXISTS idx_photos_candidate_id ON photos(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interests_candidate_id ON interests(candidate_id);
CREATE INDEX IF NOT EXISTS idx_favorites_candidate_id ON favorites(candidate_id);
CREATE INDEX IF NOT EXISTS idx_blacklist_candidate_id ON blacklist(candidate_id);
CREATE INDEX IF NOT EXISTS idx_viewed_candidates_candidate_id ON viewed_candidates(candidate_id);

-- =========================
-- Триггер для автоматического обновления поля updated_at
-- =========================

-- Универсальная функция, устанавливающая updated_at при UPDATE
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для таблиц со столбцом updated_at
DROP TRIGGER IF EXISTS trg_search_weights_updated_at ON search_weights;
CREATE TRIGGER trg_search_weights_updated_at
BEFORE UPDATE ON search_weights
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_search_offsets_updated_at ON search_offsets;
CREATE TRIGGER trg_search_offsets_updated_at
BEFORE UPDATE ON search_offsets
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
