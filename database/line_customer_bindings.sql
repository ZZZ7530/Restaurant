CREATE TABLE IF NOT EXISTS line_customer_bindings (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_phone VARCHAR(30) NOT NULL,
    line_user_id VARCHAR(80) NOT NULL,
    display_name VARCHAR(100) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_interaction_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_line_customer_bindings_phone (customer_phone),
    UNIQUE KEY uq_line_customer_bindings_user_id (line_user_id),
    INDEX idx_line_customer_bindings_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
