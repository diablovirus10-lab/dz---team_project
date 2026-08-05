-- тестовые пользователи
INSERT INTO users (vk_id, first_name, last_name, age, city, sex) VALUES
(123456789, 'Иван', 'Петров', 25, 'Москва', 2),      -- Мужчина, 25 лет
(987654321, 'Мария', 'Иванова', 23, 'Санкт-Петербург', 1), -- Женщина, 23 года
(555555555, 'Алексей', 'Сидоров', 30, 'Москва', 2);   -- Мужчина, 30 лет

-- тестовые кандидаты
INSERT INTO candidates (vk_id, first_name, last_name, age, city, profile_link, photo_1, photo_2, photo_3) VALUES
(111111111, 'Анна', 'Смирнова', 24, 'Москва', 'https://vk.com/id111111111', 'photo111_1', 'photo111_2', 'photo111_3'),
(222222222, 'Екатерина', 'Кузнецова', 26, 'Москва', 'https://vk.com/id222222222', 'photo222_1', 'photo222_2', 'photo222_3'),
(333333333, 'Ольга', 'Попова', 22, 'Санкт-Петербург', 'https://vk.com/id333333333', 'photo333_1', 'photo333_2', 'photo333_3'),
(444444444, 'Дмитрий', 'Соколов', 27, 'Москва', 'https://vk.com/id444444444', 'photo444_1', 'photo444_2', 'photo444_3');

-- кто кому понравился
INSERT INTO favorites (user_id, candidate_id) VALUES
(1, 1),
(1, 2),
(2, 4);

-- 4. кого заблокировали
INSERT INTO blacklist (user_id, candidate_id) VALUES
(1, 3),
(2, 1);

-- кто на каком месте поиска
INSERT INTO search_offsets (user_id, offset_value, search_params) VALUES
(1, 50, '{"city":"Москва","age":25,"sex":1}'),
(2, 100, '{"city":"Санкт-Петербург","age":23,"sex":2}');
