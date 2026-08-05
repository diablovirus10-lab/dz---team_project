
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP      -- Дата регистрации
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


-- 5. обход лимита пользователей
CREATE TABLE IF NOT EXISTS search_offsets (
    id SERIAL PRIMARY KEY,                                             -- ID
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,            -- ID пользователя из таблицы users
    offset_value INTEGER DEFAULT 0,                                    -- Сколько человек уже показали
    search_params TEXT,                                                -- Параметры поиска (JSON), {"city":"Москва","age":25,"sex":1}
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                    -- Когда показывали
    UNIQUE(user_id)
);





