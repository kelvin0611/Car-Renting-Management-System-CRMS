# P2P Car Renting System (CRMS)

## 專案結構

- `backend/`: Flask 後端 API
- `database/`: MySQL 建表與種子資料
- `frondend/`: 純 HTML 前端（已抽出 `config.js`）

## 需求

- Python 3
- MySQL

## 1) 建立資料庫

### 一鍵初始化（推薦，類似簡易 migration）

第一次建議先看這份更詳細的流程文件：`docs/DB_WORKFLOW.md`。

先確認你已經設定好 `backend/.env` 裡的：

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`

然後在專案根目錄執行：

```bash
./scripts/init_db.sh
```

這個腳本會：

- 使用 `backend/.env` 內的連線設定連到 MySQL
- 執行 `database/createTable.sql`
- 執行 `database/insertData.sql`

### 手動執行（備用）

用 MySQL Workbench 或 mysql CLI 依序執行：

- `database/createTable.sql`
- `database/insertData.sql`

（建議在乾淨的環境中執行；如果你已經有舊的 schema，請先自行備份/移除後再重建。）

## 2) 啟動後端

進入 `backend/` 後，先建立環境變數檔：

```bash
cp .env.example .env
```

編輯 `backend/.env`，至少把 `DB_PASSWORD` 改成你本機 MySQL 的密碼。

安裝依賴並啟動：

```bash
python3 -m pip install -r ../requirements.txt
python3 app.py
```

預設會跑在 `http://127.0.0.1:5000`。

## 3) 啟動前端

因為前端有呼叫 API，建議用本機靜態 server 開：

```bash
cd frondend
python3 -m http.server 5500
```

然後開啟 `http://127.0.0.1:5500/index.html`。

### API Base URL

前端統一在 `frondend/config.js` 設定：

- `window.API_BASE` 預設是 `http://127.0.0.1:5000`

如果你要改 port 或部署到別台機器，只要改這裡即可。

## 測試帳號（種子資料）

`database/insertData.sql` 的使用者密碼已改為 **bcrypt 雜湊**，明文密碼仍是：

- **admin**: `admin@gmail.com` / `password`
- 其他使用者也同樣是 `password`

