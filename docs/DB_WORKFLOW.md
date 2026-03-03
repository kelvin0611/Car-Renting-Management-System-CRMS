# 資料庫工作流程（第一次 vs 之後每天）

這份文件解答兩件事：

1. **第一次**要怎麼把 MySQL 跟專案接起來並把 schema/測試資料建立好
2. **之後每天**開發時應該怎麼啟動（你把 MySQL shutdown 不代表要重建資料庫）

---

## 概念先講清楚

- **MySQL Workbench**：只是「連線/管理/查看資料」的 GUI 工具
- **MySQL Server**：真正存資料、跑在背景的服務（你關掉它叫 *shutdown*）
- **初始化資料庫**（建庫建表塞種子資料）：只在「第一次」或「想重置回初始狀態」時做

所以答案是：

- **你把資料庫 shutdown → 只要重新啟動 MySQL Server 就好，不用重建**  
- 只有在你想把資料清空、回到乾淨狀態時，才需要重建（reset）

---

## 第一次操作（只需要做一次）

### A. 建立 `backend/.env`

在專案根目錄執行：

```bash
cp backend/.env.example backend/.env
```

打開 `backend/.env`，至少填好：

- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`
- `DB_USER=root`
- `DB_PASSWORD=（你在 Workbench 連線成功用的密碼）`

### B. 確認 MySQL Server 有啟動

Mac（官方安裝包）常見作法：

- 系統設定（System Settings）→ MySQL → Start MySQL Server

### C. 初始化 schema + 種子資料

在專案根目錄執行：

```bash
./scripts/init_db.sh --reset
```

- `--reset` 的意思是：先刪掉舊的 `p2p_car_rental`，再重新建立（**會清空資料**）

### D. 用 Workbench 確認

1. 連上你的 connection
2. 左邊 `SCHEMAS` 應該看到 `p2p_car_rental`
3. 展開 `Tables`，右鍵 `User` → **Select Rows – Limit 1000**

看到有資料就表示成功。

---

## 之後每天開發時（常用流程）

### 情境 1：你只是把 MySQL Server 關掉/重開機了

你只需要：

1. **把 MySQL Server 啟動起來**
2. **啟動後端 `python3 app.py`**
3. **啟動前端 static server**

✅ 這種情況 **不需要** 跑 `init_db.sh`。

### 情境 2：你想要把資料清空，回到最初始的測試資料

在專案根目錄執行：

```bash
./scripts/init_db.sh --reset
```

---

## 常見問題

### Q: 我跑 `./scripts/init_db.sh` 出現 database exists 怎麼辦？

代表你已經初始化過了。請改用：

```bash
./scripts/init_db.sh --reset
```

或是不要跑 `init_db.sh`，直接啟動後端/前端即可。

