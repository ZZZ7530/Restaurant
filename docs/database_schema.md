# MySQL Table 關聯設計

本專案資料庫以 MySQL 為主，第一版支援官方網站、線上訂位、外帶訂餐與店家後台。

## Tables

- `admin_users`：後台登入帳號與角色。
- `menu_categories`：菜單分類。
- `menu_items`：餐點資料、價格、圖片與供應狀態。
- `reservations`：顧客線上訂位資料。
- `orders`：外帶訂單主檔。
- `order_items`：外帶訂單明細，保留餐點名稱與單價快照。
- `restaurant_settings`：店名、電話、地址、營業時間、Google Maps iframe 與品牌設定。

## Relationships

```text
menu_categories 1 ─── N menu_items
orders 1 ─── N order_items
menu_items 1 ─── N order_items
```

`reservations` 獨立保存訂位資料。第一版不做會員系統與桌位自動分配。

## Status Values

- `reservations.status`：`pending`、`confirmed`、`cancelled`、`completed`、`no_show`
- `orders.status`：`pending`、`accepted`、`preparing`、`ready`、`completed`、`cancelled`

完整 SQL 請見 `database/schema.sql`。
