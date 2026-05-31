ALTER TABLE restaurant_tables
    ADD COLUMN IF NOT EXISTS floor VARCHAR(20)
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    NULL
    AFTER display_name;

ALTER TABLE restaurant_tables
    MODIFY COLUMN display_name VARCHAR(50)
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    NULL;

DELETE FROM restaurant_tables
WHERE table_number NOT IN (
    '1', '2', '3', '5', '6',
    '27', '23', '22', '21', '20', '28', '26', '25',
    '01', '02', '03', '05', '06', '07', '08'
);

INSERT INTO restaurant_tables (table_number, display_name, floor, is_active)
VALUES
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

UPDATE restaurant_tables
SET floor = CONVERT(UNHEX('E4B880E6A893') USING utf8mb4)
WHERE table_number IN ('1', '2', '3', '5', '6');

UPDATE restaurant_tables
SET floor = CONVERT(UNHEX('E4BA8CE6A893') USING utf8mb4)
WHERE table_number IN ('27', '23', '22', '21', '20', '28', '26', '25', '01', '02', '03', '05', '06', '07', '08');
