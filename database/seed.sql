USE traditional_restaurant;

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Demo admin user.
-- Username: admin
-- Password: admin123
-- Note: the current local login may still read ADMIN_USERNAME / ADMIN_PASSWORD
-- from .env. This record is provided so the demo database has admin seed data.
INSERT INTO admin_users (
    username,
    password_hash,
    display_name,
    role,
    is_active
) VALUES (
    'admin',
    'pbkdf2:sha256:1000000$restaurantseed$de5d11179eb1520bd9c8021ca8f5d725dc93f192a6be0767a0352884e0a28005',
    '系統管理員',
    'owner',
    1
) ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    display_name = VALUES(display_name),
    role = VALUES(role),
    is_active = VALUES(is_active);

-- Real table numbers for QR Code dine-in ordering.
INSERT INTO restaurant_tables (table_number, display_name, floor, is_active) VALUES
('1', '1F-1', '一樓', 1),
('2', '1F-2', '一樓', 1),
('3', '1F-3', '一樓', 1),
('5', '1F-5', '一樓', 1),
('6', '1F-6', '一樓', 1),
('27', '2F-27', '二樓', 1),
('23', '2F-23', '二樓', 1),
('22', '2F-22', '二樓', 1),
('21', '2F-21', '二樓', 1),
('20', '2F-20', '二樓', 1),
('28', '2F-28', '二樓', 1),
('26', '2F-26', '二樓', 1),
('25', '2F-25', '二樓', 1),
('01', '2F-01', '二樓', 1),
('02', '2F-02', '二樓', 1),
('03', '2F-03', '二樓', 1),
('05', '2F-05', '二樓', 1),
('06', '2F-06', '二樓', 1),
('07', '2F-07', '二樓', 1),
('08', '2F-08', '二樓', 1)
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    floor = VALUES(floor),
    is_active = VALUES(is_active);

-- Menu categories. The public menu hides category titles, but menu_items.category_id is required.
INSERT INTO menu_categories (name, description, sort_order, is_active)
SELECT '招牌海鮮', '適合聚餐共享的招牌海鮮料理。', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM menu_categories WHERE name = '招牌海鮮');

INSERT INTO menu_categories (name, description, sort_order, is_active)
SELECT '熱炒料理', '現點現炒，鑊氣香足。', 2, 1
WHERE NOT EXISTS (SELECT 1 FROM menu_categories WHERE name = '熱炒料理');

INSERT INTO menu_categories (name, description, sort_order, is_active)
SELECT '湯品主食', '湯品、米粉湯、飯麵類。', 3, 1
WHERE NOT EXISTS (SELECT 1 FROM menu_categories WHERE name = '湯品主食');

INSERT INTO menu_categories (name, description, sort_order, is_active)
SELECT '炸物點心', '酥炸點心與人氣小菜。', 4, 1
WHERE NOT EXISTS (SELECT 1 FROM menu_categories WHERE name = '炸物點心');

INSERT INTO menu_categories (name, description, sort_order, is_active)
SELECT '燒烤時價', '依每日漁獲與市場價格供應。', 5, 1
WHERE NOT EXISTS (SELECT 1 FROM menu_categories WHERE name = '燒烤時價');

SET @cat_seafood = (SELECT id FROM menu_categories WHERE name = '招牌海鮮' LIMIT 1);
SET @cat_stir_fry = (SELECT id FROM menu_categories WHERE name = '熱炒料理' LIMIT 1);
SET @cat_soup = (SELECT id FROM menu_categories WHERE name = '湯品主食' LIMIT 1);
SET @cat_fried = (SELECT id FROM menu_categories WHERE name = '炸物點心' LIMIT 1);
SET @cat_grill = (SELECT id FROM menu_categories WHERE name = '燒烤時價' LIMIT 1);

-- Demo menu items. Prices are numeric base prices for ordering; public display can still use price text mappings.
INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '紅燒魚', '魚肉鮮嫩入味，搭配鹹香醬汁與蔥花，是聚餐桌上經典又下飯的海鮮料理。', 700.00, 'images/background/紅燒魚.jpeg', 1, 1, 1
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '紅燒魚');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '魚翅羹', '濃郁羹湯口感滑順，融合海鮮鮮味與豐富配料，適合多人共享。', 900.00, 'images/background/魚翅羹.jpg', 1, 1, 2
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '魚翅羹');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '蒜蓉龍蝦', '龍蝦肉質鮮甜彈牙，搭配蒜蓉香氣，呈現豪華又有層次的海味。', 1280.00, 'images/background/蒜蓉龍蝦.jpg', 1, 1, 3
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蒜蓉龍蝦');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '三杯小卷', '小卷彈牙鮮甜，搭配九層塔與三杯醬香。', 480.00, 'images/background/菜單-三杯小卷.png', 1, 0, 4
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '三杯小卷');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '三杯錢鰻', '錢鰻吸附醬汁香氣，適合下飯與多人共享。', 720.00, 'images/background/菜單-三杯錢鰻.jpg', 1, 0, 5
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '三杯錢鰻');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '三杯青蛙', '肉質細嫩，三杯香氣濃郁。', 360.00, 'images/background/菜單-三杯青蛙.jpg', 1, 0, 6
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '三杯青蛙');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '三杯龍膽', '龍膽魚肉厚實，醬香入味。', 450.00, 'images/background/菜單-三杯龍腸.jpg', 1, 0, 7
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '三杯龍膽');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '南瓜酥', '外酥內綿的南瓜甜香，適合佐餐分享。', 150.00, 'images/background/菜單-南瓜酥.jpg', 1, 0, 8
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '南瓜酥');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '塔香蛤蜊', '蛤蜊鮮甜多汁，九層塔香氣提味。', 200.00, 'images/background/菜單-塔香蛤蜊.jpg', 1, 0, 9
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '塔香蛤蜊');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '塔香鯊魚皮', '鯊魚皮口感滑嫩，塔香醬汁濃郁。', 360.00, 'images/background/菜單-塔香鯊魚皮.jpg', 1, 0, 10
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '塔香鯊魚皮');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '小卷米粉湯', '鮮甜小卷搭配米粉湯，湯頭清香順口。', 480.00, 'images/background/菜單-小卷米粉湯.jpg', 1, 0, 11
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '小卷米粉湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '小卷酥', '小卷酥炸後外香內嫩，適合下酒。', 360.00, 'images/background/菜單-小卷酥.jpg', 1, 0, 12
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '小卷酥');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '川燙小卷', '簡單川燙保留小卷原味鮮甜。', 300.00, 'images/background/菜單-川燙小卷.jpg', 1, 0, 13
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '川燙小卷');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '川燙白蝦', '白蝦鮮甜爽口，適合全桌共享。', 280.00, 'images/background/菜單-川燙白蝦.png', 1, 0, 14
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '川燙白蝦');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '川燙鳳螺', '鳳螺口感Q彈，原味鮮明。', 350.00, 'images/background/菜單-川燙鳳螺.jpg', 1, 0, 15
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '川燙鳳螺');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '手工蝦捲', '手工製作蝦捲，外皮酥香內餡鮮甜。', 160.00, 'images/background/菜單-手工蝦捲.jpg', 1, 0, 16
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '手工蝦捲');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '月亮蝦餅', '外酥內Q，蝦香濃郁的人氣點心。', 250.00, 'images/background/菜單-月亮蝦餅.jpg', 1, 0, 17
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '月亮蝦餅');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_grill, '活烤干貝', '干貝鮮甜飽滿，簡單炙烤更顯海味。', 150.00, 'images/background/菜單-活烤干貝.jpg', 1, 0, 18
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '活烤干貝');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '涼拌鯊魚皮', '清爽開胃，口感滑嫩。', 360.00, 'images/background/菜單-涼拌鯊魚皮.jpg', 1, 0, 19
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '涼拌鯊魚皮');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '炒丁香', '丁香魚香氣足，適合配飯。', 200.00, 'images/background/菜單-炒丁香.png', 1, 0, 20
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '炒丁香');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '炒小卷', '現炒小卷鮮香彈牙。', 360.00, 'images/background/菜單-炒小卷.jpg', 1, 0, 21
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '炒小卷');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '炒海瓜子', '海瓜子鮮甜入味，是熱炒經典。', 250.00, 'images/background/菜單-炒海瓜子.jpg', 1, 0, 22
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '炒海瓜子');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '炒飯', '粒粒分明的家常炒飯。', 80.00, 'images/background/菜單-炒飯.png', 1, 0, 23
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '炒飯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '炒麵', '鹹香順口的熱炒麵食。', 80.00, 'images/background/菜單-炒麵.jpg', 1, 0, 24
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '炒麵');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '炸冰淇淋', '外熱內冰的餐後甜點。', 150.00, 'images/background/菜單-炸冰淇淋.jpg', 1, 0, 25
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '炸冰淇淋');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_grill, '烤明蝦', '依當日漁獲供應，肉質鮮甜。', 0.00, 'images/background/菜單-烤明蝦.jpg', 1, 0, 26
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '烤明蝦');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_grill, '烤松阪豬', '油脂香氣細緻，炙烤後口感爽脆。', 350.00, 'images/background/菜單-烤松阪豬.jpg', 1, 0, 27
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '烤松阪豬');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_grill, '烤牛小排', '肉香濃郁，適合聚餐加點。', 240.00, 'images/background/菜單-烤牛小排.jpg', 1, 0, 28
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '烤牛小排');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_grill, '烤蚵仔', '蚵仔鮮甜飽滿，炙烤後香氣更明顯。', 200.00, 'images/background/菜單-烤蚵仔.jpg', 1, 0, 29
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '烤蚵仔');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_grill, '烤軟絲', '軟絲Q彈鮮甜，燒烤香氣迷人。', 400.00, 'images/background/菜單-烤軟絲.png', 1, 0, 30
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '烤軟絲');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_grill, '烤鮮魚', '依當日魚貨供應，保留魚肉原味。', 0.00, 'images/background/菜單-烤鮮魚.jpg', 1, 0, 31
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '烤鮮魚');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '白鯧米粉湯', '白鯧鮮味融入米粉湯，溫潤飽足。', 0.00, 'images/background/菜單-白鯧米粉湯.jpg', 1, 0, 32
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '白鯧米粉湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '紅燒青蛙', '醬燒入味，肉質細嫩。', 300.00, 'images/background/菜單-紅燒青蛙.jpg', 1, 0, 33
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '紅燒青蛙');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '綜合生魚片', '多款鮮魚切片，清爽鮮甜。', 250.00, 'images/background/菜單-綜合生魚片.jpg', 1, 0, 34
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '綜合生魚片');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_grill, '胡椒鳳螺', '胡椒香氣濃厚，鳳螺Q彈入味。', 400.00, 'images/background/菜單-胡椒鳳螺.jpg', 1, 0, 35
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '胡椒鳳螺');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '花枝丸', '口感彈牙，海味香甜。', 180.00, 'images/background/菜單-花枝丸.jpg', 1, 0, 36
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '花枝丸');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '蒜泥鮮蚵', '鮮蚵搭配蒜泥，鹹香鮮甜。', 250.00, 'images/background/菜單-蒜泥鮮蚵.png', 1, 0, 37
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蒜泥鮮蚵');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '蔥爆蘭花蚌', '蔥香濃郁，蘭花蚌鮮脆。', 360.00, 'images/background/菜單-蔥爆蘭花蚌.jpg', 1, 0, 38
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蔥爆蘭花蚌');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '蔥爆鴕鳥肉', '肉質紮實，蔥香提味。', 360.00, 'images/background/菜單-蔥爆鴕鳥肉.jpg', 1, 0, 39
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蔥爆鴕鳥肉');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '蔭鼓蚵', '豆鼓鹹香與蚵仔鮮味融合。', 200.00, 'images/background/菜單-蔭鼓蚵.jpg', 1, 0, 40
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蔭鼓蚵');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '蚵仔湯', '鮮蚵湯頭清甜。', 200.00, 'images/background/菜單-蚵仔湯.jpg', 1, 0, 41
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蚵仔湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '蚵仔酥', '酥香外衣包裹鮮嫩蚵仔。', 200.00, 'images/background/菜單-蚵仔酥.jpg', 1, 0, 42
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蚵仔酥');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '蛤蜊湯', '蛤蜊鮮甜，湯頭清爽。', 200.00, 'images/background/菜單-蛤蜊湯.png', 1, 0, 43
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蛤蜊湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '螃蟹白菜湯', '螃蟹鮮味與白菜甜味熬成暖湯。', 0.00, 'images/background/菜單-螃蟹白菜湯.png', 1, 0, 44
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '螃蟹白菜湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '蠔油帆立貝', '帆立貝鮮甜，蠔油醬香濃郁。', 320.00, 'images/background/菜單-蠔油帆立貝.jpg', 1, 0, 45
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蠔油帆立貝');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '蠔油海參', '海參軟嫩，蠔油醬汁厚實。', 360.00, 'images/background/菜單-蠔油海參.png', 1, 0, 46
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '蠔油海參');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '西瓜綿味增湯', '鹹香酸甜的在地湯品。', 0.00, 'images/background/菜單-西瓜綿味增湯.png', 1, 0, 47
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '西瓜綿味增湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '辣炒螺肉', '香辣下飯，螺肉口感紮實。', 200.00, 'images/background/菜單-辣炒螺肉.jpg', 1, 0, 48
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '辣炒螺肉');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '酸菜魚肉', '酸香開胃，魚肉細緻。', 450.00, 'images/background/菜單-酸菜魚肉.jpg', 1, 0, 49
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '酸菜魚肉');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '金莎小卷', '鹹蛋黃金沙香氣包裹鮮甜小卷。', 360.00, 'images/background/菜單-金莎小卷.jpg', 1, 0, 50
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '金莎小卷');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '銀魚', '酥炸銀魚香脆涮嘴。', 250.00, 'images/background/菜單-銀魚.jpg', 1, 0, 51
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '銀魚');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '香酥青蛙', '外酥內嫩，香氣十足。', 300.00, 'images/background/菜單-香酥青蛙.jpg', 1, 0, 52
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '香酥青蛙');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '魚肉米粉湯', '魚肉鮮甜，米粉吸附湯頭。', 480.00, 'images/background/菜單-魚肉米粉湯.jpg', 1, 0, 53
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '魚肉米粉湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_seafood, '魚蛋', '口感細緻，依重量計價。', 45.00, 'images/background/菜單-魚蛋.jpg', 1, 0, 54
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '魚蛋');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '鮮魚味增湯', '鮮魚與味增湯底溫潤順口。', 0.00, 'images/background/菜單-鮮魚味增湯.jpg', 1, 0, 55
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '鮮魚味增湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '鮮魚薑絲湯', '薑絲提香，鮮魚湯頭清爽。', 0.00, 'images/background/菜單-鮮魚薑絲湯.jpg', 1, 0, 56
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '鮮魚薑絲湯');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '鳳梨蝦球', '蝦球鮮彈，搭配鳳梨清甜。', 300.00, 'images/background/菜單-鳳梨蝦球.jpg', 1, 0, 57
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '鳳梨蝦球');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_fried, '鹹酥龍珠', '外酥內Q，鹹香適口。', 250.00, 'images/background/菜單-鹹酥龍珠.jpg', 1, 0, 58
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '鹹酥龍珠');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_stir_fry, '麻油雞佛', '麻油香氣濃厚，口感滑嫩。', 360.00, 'images/background/菜單-麻油雞佛.jpg', 1, 0, 59
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '麻油雞佛');

INSERT INTO menu_items (category_id, name, description, price, image_url, is_available, is_featured, sort_order)
SELECT @cat_soup, '龍蝦味增湯', '龍蝦鮮味融入味增湯底。', 0.00, 'images/background/菜單-龍蝦味增湯.jpg', 1, 0, 60
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = '龍蝦味增湯');

-- Site settings used by public templates.
INSERT INTO restaurant_settings (setting_key, setting_value) VALUES
('restaurant_name', '上漁港活海產'),
('phone', '07 698 9266'),
('address', '852 高雄市茄萣區崎漏里大發路 99 號'),
('business_hours', '週二休；週一、三至六 10:00-21:00；週日 09:30-21:00'),
('google_maps_embed', '')
ON DUPLICATE KEY UPDATE
    setting_value = VALUES(setting_value);
