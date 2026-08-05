
-- таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,                              -- ID
    vk_id BIGINT UNIQUE NOT NULL,                       -- ID VK
    first_name VARCHAR(100),                            -- Имя
    last_name VARCHAR(100),                             -- Фамилия
    age INTEGER,                                        -- Возраст
    city VARCHAR(100),                                  -- Город
    sex INTEGER,                                        -- Пол: 1 - женский, 2 - мужской
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- Дата регистрации
);

-- таблица кандидатов
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,                              -- ID
    vk_id BIGINT UNIQUE NOT NULL,                       -- ID VK
    first_name VARCHAR(100),                            -- Имя
    last_name VARCHAR(100),                             -- Фамилия
    age INTEGER,                                        -- Возраст
    city VARCHAR(100),                                  -- Город
    profile_link VARCHAR(255),                          -- Ссылка на профиль VK
    photo_1 VARCHAR(255),                               -- ID первого фото
    photo_2 VARCHAR(255),                               -- ID второго фото
    photo_3 VARCHAR(255),                               -- ID третьего фото
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP      -- Дата регистрации
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


-- 5. обход лимита пользователей
CREATE TABLE IF NOT EXISTS search_offsets (
    id SERIAL PRIMARY KEY,                                             -- ID
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,            -- ID пользователя из таблицы users
    offset_value INTEGER DEFAULT 0,                                    -- Сколько человек уже показали
    search_params TEXT,                                                -- Параметры поиска (JSON), {"city":"Москва","age":25,"sex":1}
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                    -- Когда показывали
    UNIQUE(user_id)
);





