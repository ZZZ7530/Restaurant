ALTER TABLE orders
    ADD COLUMN order_type VARCHAR(20)
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    NOT NULL
    DEFAULT 'takeout'
    AFTER customer_phone;

ALTER TABLE order_items
    ADD COLUMN item_status VARCHAR(20)
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    NOT NULL
    DEFAULT 'pending'
    AFTER specification;
