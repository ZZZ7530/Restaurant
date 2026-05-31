CREATE TABLE IF NOT EXISTS restaurant_tables (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    table_number VARCHAR(20) NOT NULL UNIQUE,
    display_name VARCHAR(50),
    floor VARCHAR(20),
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS table_number VARCHAR(20)
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    NULL
    AFTER order_type;

INSERT INTO restaurant_tables (table_number, display_name)
VALUES
    ('1', '1 桌'),
    ('2', '2 桌'),
    ('3', '3 桌'),
    ('4', '4 桌'),
    ('5', '5 桌'),
    ('6', '6 桌')
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    is_active = 1;
