-- ============================================
-- 1. Очистка таблиц (для перезаполнения)
-- ============================================
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE candidates CASCADE;
TRUNCATE TABLE photos CASCADE;
TRUNCATE TABLE favorites CASCADE;
TRUNCATE TABLE blacklist CASCADE;
TRUNCATE TABLE user_interests CASCADE;
TRUNCATE TABLE interests CASCADE;
TRUNCATE TABLE search_weights CASCADE;
TRUNCATE TABLE viewed_candidates CASCADE;
TRUNCATE TABLE search_offsets CASCADE;

-- ============================================
-- 2. Пользователи бота (5 человек)
-- ============================================
INSERT INTO users (vk_id, first_name, last_name, age, city, sex) VALUES
(123456789, 'Иван', 'Петров', 25, 'Москва', 2),
(987654321, 'Мария', 'Иванова', 23, 'Санкт-Петербург', 1),
(555555555, 'Алексей', 'Сидоров', 30, 'Москва', 2),
(111111111, 'Екатерина', 'Смирнова', 27, 'Казань', 1),
(999999999, 'Дмитрий', 'Козлов', 22, 'Новосибирск', 2);

-- ============================================
-- 3. Кандидаты (10 человек, разные города)
-- ============================================
INSERT INTO candidates (vk_id, first_name, last_name, age, city, sex, profile_link) VALUES
(222222222, 'Анна', 'Смирнова', 24, 'Москва', 1, 'https://vk.com/id222222222'),
(333333333, 'Екатерина', 'Кузнецова', 26, 'Москва', 1, 'https://vk.com/id333333333'),
(444444444, 'Ольга', 'Попова', 22, 'Санкт-Петербург', 1, 'https://vk.com/id444444444'),
(555555556, 'Дмитрий', 'Соколов', 27, 'Москва', 2, 'https://vk.com/id555555556'),
(666666666, 'Наталья', 'Волкова', 25, 'Москва', 1, 'https://vk.com/id666666666'),
(777777777, 'Сергей', 'Морозов', 28, 'Санкт-Петербург', 2, 'https://vk.com/id777777777'),
(888888888, 'Анастасия', 'Новикова', 23, 'Казань', 1, 'https://vk.com/id888888888'),
(121212121, 'Павел', 'Ковалёв', 26, 'Новосибирск', 2, 'https://vk.com/id121212121'),
(131313131, 'Юлия', 'Зайцева', 24, 'Москва', 1, 'https://vk.com/id131313131'),
(141414141, 'Александр', 'Исаев', 29, 'Санкт-Петербург', 2, 'https://vk.com/id141414141');

-- ============================================
-- 4. Фотографии кандидатов (с is_tagged)
-- ============================================
INSERT INTO photos (candidate_id, photo_url, photo_id, likes_count, comments_count, is_avatar, is_tagged) VALUES
-- Анна (candidate_id = 1)
(1, 'https://sun9-15.userapi.com/impg/photo222_1.jpg', 'photo222_1', 450, 32, TRUE, FALSE),
(1, 'https://sun9-45.userapi.com/impg/photo222_2.jpg', 'photo222_2', 320, 18, FALSE, FALSE),
(1, 'https://sun9-22.userapi.com/impg/photo222_3.jpg', 'photo222_3', 280, 15, FALSE, FALSE),
(1, 'https://sun9-7.userapi.com/impg/photo222_4.jpg', 'photo222_4', 210, 10, FALSE, FALSE),
(1, 'https://sun9-33.userapi.com/impg/photo222_5.jpg', 'photo222_5', 150, 8, FALSE, TRUE), -- отмеченное фото

-- Екатерина (candidate_id = 2)
(2, 'https://sun9-12.userapi.com/impg/photo333_1.jpg', 'photo333_1', 380, 25, TRUE, FALSE),
(2, 'https://sun9-50.userapi.com/impg/photo333_2.jpg', 'photo333_2', 300, 20, FALSE, FALSE),
(2, 'https://sun9-8.userapi.com/impg/photo333_3.jpg', 'photo333_3', 250, 14, FALSE, FALSE),
(2, 'https://sun9-30.userapi.com/impg/photo333_4.jpg', 'photo333_4', 180, 9, FALSE, TRUE), -- отмеченное фото

-- Ольга (candidate_id = 3)
(3, 'https://sun9-5.userapi.com/impg/photo444_1.jpg', 'photo444_1', 520, 40, TRUE, FALSE),
(3, 'https://sun9-18.userapi.com/impg/photo444_2.jpg', 'photo444_2', 480, 35, FALSE, FALSE),
(3, 'https://sun9-25.userapi.com/impg/photo444_3.jpg', 'photo444_3', 400, 28, FALSE, FALSE),
(3, 'https://sun9-42.userapi.com/impg/photo444_4.jpg', 'photo444_4', 350, 22, FALSE, FALSE),
(3, 'https://sun9-60.userapi.com/impg/photo444_5.jpg', 'photo444_5', 280, 18, FALSE, TRUE), -- отмеченное

-- Дмитрий (candidate_id = 4)
(4, 'https://sun9-35.userapi.com/impg/photo555_1.jpg', 'photo555_1', 120, 8, TRUE, FALSE),
(4, 'https://sun9-20.userapi.com/impg/photo555_2.jpg', 'photo555_2', 95, 5, FALSE, FALSE),
(4, 'https://sun9-55.userapi.com/impg/photo555_3.jpg', 'photo555_3', 70, 3, FALSE, TRUE), -- отмеченное

-- Наталья (candidate_id = 5)
(5, 'https://sun9-3.userapi.com/impg/photo666_1.jpg', 'photo666_1', 850, 65, TRUE, FALSE),
(5, 'https://sun9-28.userapi.com/impg/photo666_2.jpg', 'photo666_2', 720, 50, FALSE, FALSE),
(5, 'https://sun9-48.userapi.com/impg/photo666_3.jpg', 'photo666_3', 680, 45, FALSE, FALSE),
(5, 'https://sun9-14.userapi.com/impg/photo666_4.jpg', 'photo666_4', 600, 38, FALSE, TRUE), -- отмеченное
(5, 'https://sun9-38.userapi.com/impg/photo666_5.jpg', 'photo666_5', 520, 30, FALSE, FALSE),
(5, 'https://sun9-52.userapi.com/impg/photo666_6.jpg', 'photo666_6', 450, 25, FALSE, FALSE),

-- Сергей (candidate_id = 6)
(6, 'https://sun9-19.userapi.com/impg/photo777_1.jpg', 'photo777_1', 180, 12, TRUE, FALSE),
(6, 'https://sun9-40.userapi.com/impg/photo777_2.jpg', 'photo777_2', 140, 8, FALSE, FALSE),
(6, 'https://sun9-11.userapi.com/impg/photo777_3.jpg', 'photo777_3', 110, 6, FALSE, TRUE), -- отмеченное
(6, 'https://sun9-56.userapi.com/impg/photo777_4.jpg', 'photo777_4', 80, 4, FALSE, FALSE),

-- Анастасия (candidate_id = 7)
(7, 'https://sun9-16.userapi.com/impg/photo888_1.jpg', 'photo888_1', 310, 20, TRUE, FALSE),
(7, 'https://sun9-32.userapi.com/impg/photo888_2.jpg', 'photo888_2', 260, 16, FALSE, FALSE),
(7, 'https://sun9-44.userapi.com/impg/photo888_3.jpg', 'photo888_3', 220, 13, FALSE, TRUE), -- отмеченное

-- Павел (candidate_id = 8)
(8, 'https://sun9-26.userapi.com/impg/photo121_1.jpg', 'photo121_1', 90, 5, TRUE, FALSE),
(8, 'https://sun9-58.userapi.com/impg/photo121_2.jpg', 'photo121_2', 75, 3, FALSE, TRUE), -- отмеченное
(8, 'https://sun9-36.userapi.com/impg/photo121_3.jpg', 'photo121_3', 60, 2, FALSE, FALSE),

-- Юлия (candidate_id = 9)
(9, 'https://sun9-1.userapi.com/impg/photo131_1.jpg', 'photo131_1', 350, 22, TRUE, FALSE),
(9, 'https://sun9-24.userapi.com/impg/photo131_2.jpg', 'photo131_2', 290, 18, FALSE, FALSE),
(9, 'https://sun9-41.userapi.com/impg/photo131_3.jpg', 'photo131_3', 240, 14, FALSE, FALSE),
(9, 'https://sun9-53.userapi.com/impg/photo131_4.jpg', 'photo131_4', 190, 10, FALSE, TRUE), -- отмеченное

-- Александр (candidate_id = 10)
(10, 'https://sun9-49.userapi.com/impg/photo141_1.jpg', 'photo141_1', 150, 10, TRUE, FALSE),
(10, 'https://sun9-13.userapi.com/impg/photo141_2.jpg', 'photo141_2', 120, 7, FALSE, FALSE),
(10, 'https://sun9-37.userapi.com/impg/photo141_3.jpg', 'photo141_3', 95, 5, FALSE, TRUE); -- отмеченное

-- ============================================
-- 5. Избранное (favorites)
-- ============================================
INSERT INTO favorites (user_id, candidate_id) VALUES
(1, 1), (1, 2), (1, 5), (1, 9),
(2, 4), (2, 6), (2, 10),
(3, 1), (3, 3), (3, 7),
(4, 4), (4, 8);

-- ============================================
-- 6. Чёрный список (blacklist)
-- ============================================
INSERT INTO blacklist (user_id, candidate_id) VALUES
(1, 3), (1, 7),
(2, 1), (2, 5),
(3, 2), (3, 6),
(4, 6), (4, 9);

-- ============================================
-- 7. Интересы пользователей (user_interests)
-- ============================================
INSERT INTO user_interests (user_id, type, value, vk_entity_id) VALUES
-- Иван (id=1) любит рок, читает фантастику, состоит в IT-группах
(1, 'music', 'Rock', 'audio123'),
(1, 'music', 'Metallica', 'audio456'),
(1, 'books', 'Фантастика', 'book789'),
(1, 'books', 'Стивен Кинг', 'book012'),
(1, 'groups', 'IT-специалисты', 'group345'),

-- Мария (id=2) любит поп, читает детективы
(2, 'music', 'Pop', 'audio678'),
(2, 'music', 'Taylor Swift', 'audio901'),
(2, 'books', 'Детективы', 'book234'),
(2, 'groups', 'Книголюбы', 'group567'),

-- Алексей (id=3) любит рок, читает научную литературу
(3, 'music', 'Rock', 'audio890'),
(3, 'music', 'Nirvana', 'audio1234'),
(3, 'books', 'Научная литература', 'book5678'),
(3, 'groups', 'Наука и технологии', 'group9012'),

-- Екатерина (id=4) любит классику, читает романы
(4, 'music', 'Classical', 'audio3456'),
(4, 'music', 'Моцарт', 'audio7890'),
(4, 'books', 'Романы', 'book1234'),
(4, 'groups', 'Искусство', 'group5678'),

-- Дмитрий (id=5) любит хип-хоп, читает комиксы
(5, 'music', 'Hip-Hop', 'audio9012'),
(5, 'music', 'Eminem', 'audio3456'),
(5, 'books', 'Комиксы', 'book7890'),
(5, 'groups', 'Геймеры', 'group1234');

-- ============================================
-- 8. Интересы кандидатов (interests)
-- ============================================
INSERT INTO interests (candidate_id, type, value, vk_entity_id) VALUES
-- Анна (id=1) — любит рок, читает фантастику
(1, 'music', 'Rock', 'audio123'),
(1, 'music', 'Metallica', 'audio456'),
(1, 'books', 'Фантастика', 'book789'),
(1, 'groups', 'IT-специалисты', 'group345'),

-- Екатерина (id=2) — любит рок, читает фантастику
(2, 'music', 'Rock', 'audio123'),
(2, 'music', 'Nirvana', 'audio890'),
(2, 'books', 'Фантастика', 'book789'),
(2, 'groups', 'Книголюбы', 'group567'),

-- Ольга (id=3) — любит поп, читает детективы
(3, 'music', 'Pop', 'audio678'),
(3, 'music', 'Taylor Swift', 'audio901'),
(3, 'books', 'Детективы', 'book234'),
(3, 'groups', 'Книголюбы', 'group567'),

-- Дмитрий (id=4) — любит классику, читает романы
(4, 'music', 'Classical', 'audio3456'),
(4, 'music', 'Моцарт', 'audio7890'),
(4, 'books', 'Романы', 'book1234'),
(4, 'groups', 'Искусство', 'group5678'),

-- Наталья (id=5) — любит поп, читает романы
(5, 'music', 'Pop', 'audio678'),
(5, 'music', 'Taylor Swift', 'audio901'),
(5, 'books', 'Романы', 'book1234'),
(5, 'groups', 'Искусство', 'group5678'),

-- Сергей (id=6) — любит хип-хоп, читает комиксы
(6, 'music', 'Hip-Hop', 'audio9012'),
(6, 'music', 'Eminem', 'audio3456'),
(6, 'books', 'Комиксы', 'book7890'),
(6, 'groups', 'Геймеры', 'group1234'),

-- Анастасия (id=7) — любит рок, читает фантастику
(7, 'music', 'Rock', 'audio123'),
(7, 'music', 'Metallica', 'audio456'),
(7, 'books', 'Фантастика', 'book789'),
(7, 'groups', 'IT-специалисты', 'group345'),

-- Павел (id=8) — любит классику, читает научную литературу
(8, 'music', 'Classical', 'audio3456'),
(8, 'music', 'Моцарт', 'audio7890'),
(8, 'books', 'Научная литература', 'book5678'),
(8, 'groups', 'Наука и технологии', 'group9012'),

-- Юлия (id=9) — любит поп, читает детективы
(9, 'music', 'Pop', 'audio678'),
(9, 'music', 'Taylor Swift', 'audio901'),
(9, 'books', 'Детективы', 'book234'),
(9, 'groups', 'Книголюбы', 'group567'),

-- Александр (id=10) — любит рок, читает комиксы
(10, 'music', 'Rock', 'audio123'),
(10, 'music', 'Nirvana', 'audio890'),
(10, 'books', 'Комиксы', 'book7890'),
(10, 'groups', 'Геймеры', 'group1234');

-- ============================================
-- 9. Веса критериев (search_weights) — дефолтные значения
-- ============================================
INSERT INTO search_weights (user_id, criterion_name, weight) VALUES
-- Иван (id=1)
(1, 'age', 0.40),
(1, 'common_friends', 0.30),
(1, 'music', 0.15),
(1, 'books', 0.10),
(1, 'groups', 0.05),

-- Мария (id=2)
(2, 'age', 0.35),
(2, 'common_friends', 0.25),
(2, 'music', 0.20),
(2, 'books', 0.15),
(2, 'groups', 0.05),

-- Алексей (id=3)
(3, 'age', 0.45),
(3, 'common_friends', 0.20),
(3, 'music', 0.15),
(3, 'books', 0.15),
(3, 'groups', 0.05),

-- Екатерина (id=4)
(4, 'age', 0.30),
(4, 'common_friends', 0.30),
(4, 'music', 0.15),
(4, 'books', 0.10),
(4, 'groups', 0.15),

-- Дмитрий (id=5)
(5, 'age', 0.40),
(5, 'common_friends', 0.25),
(5, 'music', 0.20),
(5, 'books', 0.10),
(5, 'groups', 0.05);

-- ============================================
-- 10. Просмотренные кандидаты (viewed_candidates)
-- ============================================
INSERT INTO viewed_candidates (user_id, candidate_id) VALUES
-- Иван уже посмотрел
(1, 1), (1, 2), (1, 3), (1, 4),
-- Мария уже посмотрела
(2, 1), (2, 2), (2, 3),
-- Алексей уже посмотрел
(3, 1), (3, 2),
-- Екатерина уже посмотрела
(4, 1), (4, 2), (4, 3), (4, 4), (4, 5),
-- Дмитрий уже посмотрел
(5, 1);

-- ============================================
-- 11. Обход лимита (search_offsets)
-- ============================================
INSERT INTO search_offsets (user_id, offset_value, batch_size, search_params, total_found, last_search_timestamp) VALUES
(1, 50, 20, '{"city":"Москва","age":25,"sex":1,"offset":50}', 150, CURRENT_TIMESTAMP),
(2, 100, 20, '{"city":"Санкт-Петербург","age":23,"sex":2,"offset":100}', 200, CURRENT_TIMESTAMP),
(3, 25, 20, '{"city":"Москва","age":30,"sex":1,"offset":25}', 80, CURRENT_TIMESTAMP),
(4, 75, 20, '{"city":"Казань","age":27,"sex":2,"offset":75}', 120, CURRENT_TIMESTAMP),
(5, 0, 20, '{"city":"Новосибирск","age":22,"sex":1,"offset":0}', 45, CURRENT_TIMESTAMP);