# 上漁港活海產網站：教授測試快速啟動教學

這份文件是給學校桌機快速展示使用。照順序完成後，就可以測試前台官網、線上訂位、外帶訂餐、QR Code 內用點餐與後台管理系統。

## 1. 下載 GitHub 專案

請先把專案從 GitHub 下載到學校桌機。

方式一：使用 Git Clone

```bash
git clone <你的 GitHub 專案網址>
```

方式二：下載 ZIP

1. 進入 GitHub 專案頁面
2. 點選 `Code`
3. 點選 `Download ZIP`
4. 解壓縮到桌面或指定資料夾

## 2. 進入專案資料夾

打開終端機或 PowerShell，切換到專案根目錄。

範例：

```bash
cd Restaurant
```

## 3. 安裝 Python 套件

請確認電腦已安裝 Python。

在專案根目錄執行：

```bash
pip install -r requirements.txt
```

## 4. 開啟 XAMPP MySQL

1. 打開 XAMPP Control Panel
2. 找到 `MySQL`
3. 按下 `Start`
4. 確認 MySQL 狀態變成綠色或顯示 Running

## 5. 打開 phpMyAdmin

瀏覽器開啟：

```text
http://localhost/phpmyadmin
```

## 6. 匯入 schema.sql

請先匯入資料庫結構。

1. 進入 phpMyAdmin
2. 點選上方 `Import`
3. 選擇檔案：

```text
database/schema.sql
```

4. 按下 `Import` 或 `Go`
5. 等待匯入成功

匯入後會建立資料庫與資料表。

## 7. 再匯入 seed.sql

請接著匯入預設展示資料。

1. 進入 phpMyAdmin
2. 點選資料庫 `traditional_restaurant`
3. 點選上方 `Import`
4. 選擇檔案：

```text
database/seed.sql
```

5. 按下 `Import` 或 `Go`
6. 等待匯入成功

`seed.sql` 會建立展示用資料，包含：

- 後台管理員帳號
- 桌號 QR Code 資料
- 菜單分類
- 菜色資料

## 8. 建立 .env

如果專案根目錄已經有 `.env.example`，請複製一份並改名成 `.env`。

Windows PowerShell 可執行：

```powershell
Copy-Item .env.example .env
```

也可以手動複製：

1. 複製 `.env.example`
2. 貼上到同一層資料夾
3. 重新命名為 `.env`

基本展示時，LINE token 可以不填。

後台管理員帳號請使用專案提供的腳本建立，不要把管理員密碼寫入 README、`.env.example`、Python、SQL 或任何 Git 追蹤檔案。

```powershell
python scripts/create_admin_user.py --username <管理員帳號> --display-name <顯示名稱> --role owner
```

執行後請依照終端機提示輸入密碼；密碼會以 hash 形式儲存在資料庫。

LINE 相關設定可以先空白：

```env
LINE_CHANNEL_ACCESS_TOKEN=
LINE_USER_ID=
LINE_GROUP_ID=
```

如果 LINE token 不填，LINE 通知不會送出，但不影響基本展示。線上訂位、外帶訂餐、內用 QR Code 點餐仍然可以正常測試。

## 9. 啟動 Flask 網站

在專案根目錄執行：

```bash
python run.py
```

看到類似以下訊息代表啟動成功：

```text
Running on http://127.0.0.1:5000
```

## 10. 測試網址

前台網站：

```text
http://127.0.0.1:5000/
```

菜單展示：

```text
http://127.0.0.1:5000/menu
```

線上訂位：

```text
http://127.0.0.1:5000/reservations
```

外帶訂餐：

```text
http://127.0.0.1:5000/orders/takeout
```

內用 QR Code 點餐測試：

```text
http://127.0.0.1:5000/table-order/1
http://127.0.0.1:5000/table-order/2
http://127.0.0.1:5000/table-order/27
http://127.0.0.1:5000/table-order/01
```

後台登入：

```text
http://127.0.0.1:5000/admin/login
```

後台帳號密碼：

```text
請使用 scripts/create_admin_user.py 建立的管理員帳號登入。
密碼不得寫入 README、.env.example 或程式碼。
```

後台常用頁面：

```text
http://127.0.0.1:5000/admin/dashboard
http://127.0.0.1:5000/admin/orders
http://127.0.0.1:5000/admin/dine-in-orders
http://127.0.0.1:5000/admin/kitchen
http://127.0.0.1:5000/admin/completed-orders
http://127.0.0.1:5000/admin/menu-items
http://127.0.0.1:5000/admin/daily-prices
http://127.0.0.1:5000/admin/table-qrcodes
```

## 11. 展示建議流程

1. 打開首頁，展示餐廳官網視覺。
2. 進入 `/menu`，展示菜單列表。
3. 進入 `/reservations`，送出一筆線上訂位。
4. 登入後台，進入 `/admin/reservations`，確認訂位出現在後台。
5. 進入 `/orders/takeout`，建立一筆外帶訂單。
6. 進入 `/table-order/1`，模擬桌號 1 內用點餐。
7. 進入 `/admin/dine-in-orders`，確認內用訂單。
8. 進入 `/admin/kitchen`，展示出餐管理與餐點完成狀態。
9. 進入 `/admin/table-qrcodes`，展示桌號 QR Code 管理。

## 12. LINE 通知說明

LINE token 是選填。

如果 `.env` 沒有填：

```env
LINE_CHANNEL_ACCESS_TOKEN=
LINE_USER_ID=
LINE_GROUP_ID=
```

系統仍然可以正常展示：

- 線上訂位
- 外帶訂餐
- 內用 QR Code 點餐
- 後台管理
- 出餐管理

只是 LINE 不會收到通知。

如果要測試 LINE 通知，才需要填入：

```env
LINE_CHANNEL_ACCESS_TOKEN=你的 LINE Channel Access Token
LINE_USER_ID=你的 LINE User ID
```

## 13. 常見問題

### 問題一：網站打不開

請確認 Flask 是否有啟動：

```bash
python run.py
```

並確認瀏覽器網址是：

```text
http://127.0.0.1:5000/
```

### 問題二：資料庫連線失敗

請確認：

1. XAMPP MySQL 已經 Start
2. 已匯入 `database/schema.sql`
3. 已匯入 `database/seed.sql`
4. `.env` 的資料庫帳密與本機 MySQL 設定一致

### 問題三：後台無法登入

請確認已使用 `scripts/create_admin_user.py` 建立後台管理員，且 `admin_users.password_hash` 內儲存的是密碼 hash，不是明文密碼。

如果修改 `.env`，請重新啟動 Flask：

```bash
python run.py
```

### 問題四：LINE 沒收到通知

基本展示不需要 LINE。

如果要測試 LINE，才需要設定：

```env
LINE_CHANNEL_ACCESS_TOKEN=
LINE_USER_ID=
```

LINE 沒設定時，不會影響訂位、外帶、內用點餐功能。
