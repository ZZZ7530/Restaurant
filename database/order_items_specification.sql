ALTER TABLE order_items
    ADD COLUMN specification VARCHAR(50)
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    NULL
    AFTER item_name;
