# 上漁港活海產餐廳網站專案備忘

> 後續每新增、調整或移除功能時，請同步更新本檔案。

## 重要網址

### 前台

| 功能 | 路徑 |
| --- | --- |
| 首頁 | `/` |
| 菜單展示 | `/menu` |
| 外帶訂餐 | `/orders/takeout` |
| 線上訂位 | `/reservations` |
| 交通資訊 | `/contact` |
| 年菜菜單 | `/newyear-menu.html` |

### 內用 QR Code 點餐

| 桌號 | 點餐路徑 |
| --- | --- |
| 1F-1 | `/table-order/1` |
| 1F-2 | `/table-order/2` |
| 1F-3 | `/table-order/3` |
| 1F-5 | `/table-order/5` |
| 1F-6 | `/table-order/6` |
| 2F-27 | `/table-order/27` |
| 2F-23 | `/table-order/23` |
| 2F-22 | `/table-order/22` |
| 2F-21 | `/table-order/21` |
| 2F-20 | `/table-order/20` |
| 2F-28 | `/table-order/28` |
| 2F-26 | `/table-order/26` |
| 2F-25 | `/table-order/25` |
| 2F-01 | `/table-order/01` |
| 2F-02 | `/table-order/02` |
| 2F-03 | `/table-order/03` |
| 2F-05 | `/table-order/05` |
| 2F-06 | `/table-order/06` |
| 2F-07 | `/table-order/07` |
| 2F-08 | `/table-order/08` |

開發環境完整網址：

```text
http://127.0.0.1:5000/table-order/1
http://127.0.0.1:5000/table-order/2
http://127.0.0.1:5000/table-order/3
http://127.0.0.1:5000/table-order/5
http://127.0.0.1:5000/table-order/6
http://127.0.0.1:5000/table-order/27
http://127.0.0.1:5000/table-order/23
http://127.0.0.1:5000/table-order/22
http://127.0.0.1:5000/table-order/21
http://127.0.0.1:5000/table-order/20
http://127.0.0.1:5000/table-order/28
http://127.0.0.1:5000/table-order/26
http://127.0.0.1:5000/table-order/25
http://127.0.0.1:5000/table-order/01
http://127.0.0.1:5000/table-order/02
http://127.0.0.1:5000/table-order/03
http://127.0.0.1:5000/table-order/05
http://127.0.0.1:5000/table-order/06
http://127.0.0.1:5000/table-order/07
http://127.0.0.1:5000/table-order/08
```

QR Code 網址基底設定：

```env
TABLE_ORDER_BASE_URL=http://127.0.0.1:5000
```

部署到正式網域後，將 `.env` 的 `TABLE_ORDER_BASE_URL` 改成正式網域即可。

### 後台管理

目前程式實際後台 Blueprint prefix 是 `/admin`，也就是目前可用網址為：

| 功能 | 目前實際路徑 |
| --- | --- |
| 後台登入 | `/admin/login` |
| 後台總覽 | `/admin/dashboard` |
| 外帶訂單 | `/admin/orders` |
| 內用訂單 | `/admin/dine-in-orders` |
| 出餐管理 | `/admin/kitchen` |
| 完成訂單 | `/admin/completed-orders` |
| 菜單管理 | `/admin/menu-items` |
| 時價管理 | `/admin/daily-prices` |
| 桌號 QR Code | `/admin/table-qrcodes` |
| 訂位管理 | `/admin/reservations` |
| 營業額統計 | `/admin/revenue` |
| 店家設定 | `/admin/settings` |

預計正式後台網址或使用者指定路徑：

```text
/shanghai-admin/login
/shanghai-admin/orders
/shanghai-admin/dine-in-orders
/shanghai-admin/kitchen
/shanghai-admin/completed-orders
/shanghai-admin/menu-items
/shanghai-admin/daily-prices
/shanghai-admin/table-qrcodes
```

若要讓 `/shanghai-admin/...` 真的可用，需要將 `app/routes/admin_routes.py` 的 `url_prefix` 從 `/admin` 調整為 `/shanghai-admin`，或另外新增相同後台 Blueprint alias。

## Route 檔案位置

| 檔案 | 負責功能 |
| --- | --- |
| `app/routes/public_routes.py` | 首頁、菜單展示、聯絡頁、年菜頁、桌號點餐頁 `/table-order/<table_number>` |
| `app/routes/reservation_routes.py` | 前台線上訂位 `/reservations` |
| `app/routes/order_routes.py` | 外帶訂單 `/orders`、外帶頁 `/orders/takeout`、內用送單 `/orders/dine-in` |
| `app/routes/admin_routes.py` | 所有後台頁面、後台登入保護、出餐管理、QR Code 管理 |

## Service / Repository 位置

| 檔案 | 負責功能 |
| --- | --- |
| `app/services/menu_service.py` | 菜單資料、價格對應、前台菜單資料 |
| `app/services/order_service.py` | 外帶訂單、內用訂單、出餐管理、完成訂單 |
| `app/services/reservation_service.py` | 訂位新增、修改、刪除、查詢 |
| `app/services/daily_price_service.py` | 每日時價管理 |
| `app/services/table_service.py` | 桌號資料、桌號 QR Code 頁資料 |
| `app/services/line_service.py` | LINE Messaging API 測試通知、訂位通知、外帶通知、內用通知 |
| `app/repositories/menu_repository.py` | `menu_items`、`menu_categories` 資料存取 |
| `app/repositories/order_repository.py` | `orders`、`order_items` 資料存取 |
| `app/repositories/reservation_repository.py` | `reservations` 資料存取 |
| `app/repositories/daily_price_repository.py` | `daily_menu_prices` 資料存取 |
| `app/repositories/table_repository.py` | `restaurant_tables` 資料存取 |
| `app/repositories/db.py` | MySQL 連線與 cursor 管理 |

## 主要 Template / JS 位置

| 檔案 | 功能 |
| --- | --- |
| `app/templates/index.html` | 首頁 |
| `app/templates/menu.html` | 前台菜單展示 |
| `app/templates/reservation.html` | 前台線上訂位 |
| `app/templates/takeout.html` | 前台外帶訂餐 |
| `app/templates/table_order.html` | 內用 QR Code 點餐 |
| `app/templates/admin/base_admin.html` | 後台共用版型與側邊欄 |
| `app/templates/admin/orders.html` | 外帶訂單管理 |
| `app/templates/admin/dine_in_orders.html` | 內用訂單管理 |
| `app/templates/admin/kitchen.html` | 出餐管理 |
| `app/templates/admin/completed_orders.html` | 完成訂單 |
| `app/templates/admin/menu_items.html` | 菜單管理列表 |
| `app/templates/admin/daily_prices.html` | 時價管理 |
| `app/templates/admin/table_qrcodes.html` | 桌號 QR Code 管理 |
| `app/static/js/takeout.js` | 外帶購物車與送單 |
| `app/static/js/table_order.js` | 內用購物車與送單 |
| `app/static/js/admin_table_qrcodes.js` | 後台產生與下載桌號 QR Code |

## 品牌與圖示

| 檔案 | 用途 |
| --- | --- |
| `app/static/images/logo.png` | 前台 Header、後台側邊欄、後台登入頁 Logo |
| `app/static/images/favicon.png` | 瀏覽器分頁 favicon 與 apple touch icon |
| `app/templates/base.html` | 前台共用 Header、favicon 設定 |
| `app/templates/admin/base_admin.html` | 後台共用品牌區、favicon 設定 |

## 資料表

主要 Schema 位於：

```text
database/schema.sql
```

目前主要資料表：

| 資料表 | 用途 |
| --- | --- |
| `admin_users` | 後台管理員資料，目前登入主要使用環境變數帳密 |
| `menu_categories` | 菜單分類，前台目前不顯示分類標題 |
| `menu_items` | 菜色主資料，是前台菜單與外帶/內用點餐的主要資料來源 |
| `reservations` | 線上訂位資料 |
| `orders` | 外帶與內用訂單主檔 |
| `order_items` | 訂單餐點明細 |
| `restaurant_tables` | 內用桌號資料與 QR Code 對應 |
| `restaurant_settings` | 店家設定資料預留 |
| `daily_menu_prices` | 每日時價資料 |

重要欄位：

| 資料表 | 欄位 | 說明 |
| --- | --- | --- |
| `orders` | `order_type` | `takeout` 外帶、`dine_in` 內用 |
| `orders` | `table_number` | 內用桌號 |
| `orders` | `completed_at` | 訂單完成時間 |
| `order_items` | `specification` | 餐點規格，例如小、中、大 |
| `order_items` | `item_status` | 單品狀態，例如 pending、completed |
| `restaurant_tables` | `table_number` | 桌號 |
| `restaurant_tables` | `display_name` | 後台與內用頁顯示名稱，例如 `2F-27` |
| `restaurant_tables` | `floor` | 樓層，例如 `一樓`、`二樓` |
| `restaurant_tables` | `is_active` | 是否啟用 |
| `daily_menu_prices` | `price_text` | 今日時價文字 |

## Migration / SQL 檔案

| 檔案 | 用途 |
| --- | --- |
| `database/dine_in_order_fields.sql` | 建立 `restaurant_tables`、新增 `orders.table_number` 的初始 SQL |
| `database/restaurant_tables_actual.sql` | 新增 `restaurant_tables.floor`，同步實際一樓/二樓桌號 |
| `database/kitchen_board_fields.sql` | 出餐管理相關欄位 |
| `database/orders_completed_at.sql` | 完成訂單歸檔時間欄位 |
| `database/order_items_specification.sql` | 訂單明細規格欄位 |
| `database/daily_menu_prices.sql` | 每日時價資料表 |
| `database/utf8mb4_fix.sql` | 中文 utf8mb4 編碼修正 SQL |

## 管理頁功能對照

| 管理頁 | 用途 |
| --- | --- |
| `/admin/reservations` | 訂位新增、編輯、刪除、狀態管理 |
| `/admin/orders` | 外帶訂單管理，只顯示 `order_type = takeout` |
| `/admin/dine-in-orders` | 內用訂單管理，只顯示 `order_type = dine_in` |
| `/admin/kitchen` | 出餐管理，看所有未完成外帶與內用訂單，可標記單品完成 |
| `/admin/completed-orders` | 已完成訂單查詢與永久刪除 |
| `/admin/menu-items` | 菜單菜色管理，上架才顯示到前台 |
| `/admin/daily-prices` | 每日時價管理，優先覆蓋固定價格 |
| `/admin/table-qrcodes` | 產生並下載每桌 QR Code |

## LINE 通知

使用 LINE 官方帳號 Messaging API，不使用 LINE Notify。

設定檔：

```env
LINE_CHANNEL_ACCESS_TOKEN=
LINE_USER_ID=
LINE_GROUP_ID=
```

目前通知時機：

| 事件 | 通知 |
| --- | --- |
| 前台線上訂位成功 | 發送「新訂位」 |
| 前台外帶訂單成功 | 發送「新外帶訂單」 |
| 內用 QR Code 點餐成功 | 發送「新內用訂單」 |

通知失敗只寫 log，不影響訂位或訂單成立。後台手動新增訂單不發送通知。

## QR Code 點餐流程

```text
桌上 QR Code
↓
客人掃描
↓
進入 /table-order/<table_number>
↓
選餐點、規格、數量、備註
↓
送出到 POST /orders/dine-in
↓
寫入 orders + order_items
↓
後台 /admin/dine-in-orders 看得到
↓
後台 /admin/kitchen 出餐管理看得到桌號與餐點
↓
員工標記單品完成或整筆訂單完成
```

## 開發注意事項

- `run.py` 本地開發階段維持：

```python
if __name__ == "__main__":
    app.run(debug=True)
```

- 不要把 `run.py` 改回讀取 config 的版本。
- 後台頁面需要套用 `admin_required`，不能只靠隱藏按鈕。
- 前台菜單、外帶訂餐、內用點餐應以 `menu_items` 作為主要資料來源。
- `menu_items.is_available = 1` 才顯示在前台。
- 每新增功能、route、資料表、管理頁，請同步更新本檔案。
