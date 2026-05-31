ALTER TABLE orders
    ADD COLUMN completed_at DATETIME NULL
    AFTER note;
