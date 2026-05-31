USE traditional_restaurant;

INSERT INTO reservations (
    customer_name, customer_phone, reservation_date,
    reservation_time, party_size, note, status
) VALUES
('王小明', '0912345678', CURDATE(), '18:30:00', 4, '需要兒童椅', 'pending');

INSERT INTO orders (
    order_no, customer_name, customer_phone, pickup_date,
    pickup_time, subtotal, total_amount, note
) VALUES
('TO202605220001', '陳小姐', '0987654321', CURDATE(), '19:00:00', 335, 335, '餐具兩份');

INSERT INTO order_items (
    order_id, menu_item_id, item_name, unit_price, quantity, line_total
) VALUES
(1, 1, '三杯雞', 280, 1, 280),
(1, 3, '滷肉飯', 55, 1, 55);
