
INSERT INTO users (vk_id, first_name, last_name, age, city, sex) VALUES
(123456789, 'Иван', 'Петров', 25, 'Москва', 2),
(987654321, 'Мария', 'Иванова', 23, 'Санкт-Петербург', 1),
(555555555, 'Алексей', 'Сидоров', 30, 'Москва', 2),
(111111111, 'Екатерина', 'Смирнова', 27, 'Казань', 1),
(999999999, 'Дмитрий', 'Козлов', 22, 'Новосибирск', 2);



INSERT INTO candidates (vk_id, first_name, last_name, age, city, profile_link) VALUES
(111111111, 'Анна', 'Смирнова', 24, 'Москва', 'https://vk.com/id111111111'),
(222222222, 'Екатерина', 'Кузнецова', 26, 'Москва', 'https://vk.com/id222222222'),
(333333333, 'Ольга', 'Попова', 22, 'Санкт-Петербург', 'https://vk.com/id333333333'),
(444444444, 'Дмитрий', 'Соколов', 27, 'Москва', 'https://vk.com/id444444444'),
(555555556, 'Наталья', 'Волкова', 25, 'Москва', 'https://vk.com/id555555556'),
(666666666, 'Сергей', 'Морозов', 28, 'Санкт-Петербург', 'https://vk.com/id666666666'),
(777777777, 'Анастасия', 'Новикова', 23, 'Казань', 'https://vk.com/id777777777'),
(888888888, 'Павел', 'Ковалёв', 26, 'Новосибирск', 'https://vk.com/id888888888'),
(121212121, 'Юлия', 'Зайцева', 24, 'Москва', 'https://vk.com/id121212121'),
(131313131, 'Александр', 'Исаев', 29, 'Санкт-Петербург', 'https://vk.com/id131313131');



INSERT INTO photos (candidate_id, photo_url, photo_id, likes_count, comments_count, is_avatar) VALUES


(1, 'https://sun9-15.userapi.com/impg/photo111_1.jpg', 'photo111_1', 450, 32, TRUE),
(1, 'https://sun9-45.userapi.com/impg/photo111_2.jpg', 'photo111_2', 320, 18, FALSE),
(1, 'https://sun9-22.userapi.com/impg/photo111_3.jpg', 'photo111_3', 280, 15, FALSE),
(1, 'https://sun9-7.userapi.com/impg/photo111_4.jpg', 'photo111_4', 210, 10, FALSE),
(1, 'https://sun9-33.userapi.com/impg/photo111_5.jpg', 'photo111_5', 150, 8, FALSE),


(2, 'https://sun9-12.userapi.com/impg/photo222_1.jpg', 'photo222_1', 380, 25, TRUE),
(2, 'https://sun9-50.userapi.com/impg/photo222_2.jpg', 'photo222_2', 300, 20, FALSE),
(2, 'https://sun9-8.userapi.com/impg/photo222_3.jpg', 'photo222_3', 250, 14, FALSE),
(2, 'https://sun9-30.userapi.com/impg/photo222_4.jpg', 'photo222_4', 180, 9, FALSE),


(3, 'https://sun9-5.userapi.com/impg/photo333_1.jpg', 'photo333_1', 520, 40, TRUE),
(3, 'https://sun9-18.userapi.com/impg/photo333_2.jpg', 'photo333_2', 480, 35, FALSE),
(3, 'https://sun9-25.userapi.com/impg/photo333_3.jpg', 'photo333_3', 400, 28, FALSE),
(3, 'https://sun9-42.userapi.com/impg/photo333_4.jpg', 'photo333_4', 350, 22, FALSE),
(3, 'https://sun9-60.userapi.com/impg/photo333_5.jpg', 'photo333_5', 280, 18, FALSE),
(3, 'https://sun9-10.userapi.com/impg/photo333_6.jpg', 'photo333_6', 200, 12, FALSE),


(4, 'https://sun9-35.userapi.com/impg/photo444_1.jpg', 'photo444_1', 120, 8, TRUE),
(4, 'https://sun9-20.userapi.com/impg/photo444_2.jpg', 'photo444_2', 95, 5, FALSE),
(4, 'https://sun9-55.userapi.com/impg/photo444_3.jpg', 'photo444_3', 70, 3, FALSE),


(5, 'https://sun9-3.userapi.com/impg/photo555_1.jpg', 'photo555_1', 850, 65, TRUE),
(5, 'https://sun9-28.userapi.com/impg/photo555_2.jpg', 'photo555_2', 720, 50, FALSE),
(5, 'https://sun9-48.userapi.com/impg/photo555_3.jpg', 'photo555_3', 680, 45, FALSE),
(5, 'https://sun9-14.userapi.com/impg/photo555_4.jpg', 'photo555_4', 600, 38, FALSE),
(5, 'https://sun9-38.userapi.com/impg/photo555_5.jpg', 'photo555_5', 520, 30, FALSE),
(5, 'https://sun9-52.userapi.com/impg/photo555_6.jpg', 'photo555_6', 450, 25, FALSE),


(6, 'https://sun9-19.userapi.com/impg/photo666_1.jpg', 'photo666_1', 180, 12, TRUE),
(6, 'https://sun9-40.userapi.com/impg/photo666_2.jpg', 'photo666_2', 140, 8, FALSE),
(6, 'https://sun9-11.userapi.com/impg/photo666_3.jpg', 'photo666_3', 110, 6, FALSE),
(6, 'https://sun9-56.userapi.com/impg/photo666_4.jpg', 'photo666_4', 80, 4, FALSE),


(7, 'https://sun9-16.userapi.com/impg/photo777_1.jpg', 'photo777_1', 310, 20, TRUE),
(7, 'https://sun9-32.userapi.com/impg/photo777_2.jpg', 'photo777_2', 260, 16, FALSE),
(7, 'https://sun9-44.userapi.com/impg/photo777_3.jpg', 'photo777_3', 220, 13, FALSE),


(8, 'https://sun9-26.userapi.com/impg/photo888_1.jpg', 'photo888_1', 90, 5, TRUE),
(8, 'https://sun9-58.userapi.com/impg/photo888_2.jpg', 'photo888_2', 75, 3, FALSE),
(8, 'https://sun9-36.userapi.com/impg/photo888_3.jpg', 'photo888_3', 60, 2, FALSE),


(9, 'https://sun9-1.userapi.com/impg/photo121_1.jpg', 'photo121_1', 350, 22, TRUE),
(9, 'https://sun9-24.userapi.com/impg/photo121_2.jpg', 'photo121_2', 290, 18, FALSE),
(9, 'https://sun9-41.userapi.com/impg/photo121_3.jpg', 'photo121_3', 240, 14, FALSE),
(9, 'https://sun9-53.userapi.com/impg/photo121_4.jpg', 'photo121_4', 190, 10, FALSE),


(10, 'https://sun9-49.userapi.com/impg/photo131_1.jpg', 'photo131_1', 150, 10, TRUE),
(10, 'https://sun9-13.userapi.com/impg/photo131_2.jpg', 'photo131_2', 120, 7, FALSE),
(10, 'https://sun9-37.userapi.com/impg/photo131_3.jpg', 'photo131_3', 95, 5, FALSE);



INSERT INTO favorites (user_id, candidate_id) VALUES

(1, 1),
(1, 2),
(1, 5),
(1, 9),


(2, 4),
(2, 6),
(2, 10),


(3, 1),
(3, 3),
(3, 7),


(4, 4),
(4, 8);


INSERT INTO blacklist (user_id, candidate_id) VALUES

(1, 3),
(1, 7),
(2, 1),
(3, 2),
(4, 6);


INSERT INTO search_offsets (user_id, offset_value, search_params) VALUES
(1, 50, '{"city":"Москва","age":25,"sex":1}'),
(2, 100, '{"city":"Санкт-Петербург","age":23,"sex":2}'),
(3, 25, '{"city":"Москва","age":30,"sex":1}'),
(4, 75, '{"city":"Казань","age":27,"sex":2}'),
(5, 0, '{"city":"Новосибирск","age":22,"sex":1}');
