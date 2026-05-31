# 傳統餐廳官方網站

本專案是傳統餐廳官方網站第一階段骨架，包含前台頁面、線上訂位、外帶訂餐、後台管理入口與 MySQL schema。

## 技術棧

- Frontend：HTML5、SCSS、Vanilla JavaScript、Bootstrap
- Backend：Python Flask
- Database：MySQL

## 啟動方式

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

## 資料庫初始化

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
mysql -u root -p < database/sample_data.sql
```

## 主要路由

- `/`：首頁
- `/menu`：菜單展示
- `/reservations`：線上訂位
- `/orders/takeout`：外帶訂餐
- `/contact`：聯絡我們
- `/admin`：後台總覽
