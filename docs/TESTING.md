# 測試指南：從 Renter / Owner / Admin 三個角度驗證系統邏輯

這份文件的目的：**快速檢查系統邏輯是否正常**，而不是只看「有沒有跑起來」。

所有測試都假設：

- DB 已用 `./scripts/init_db.sh --reset` 初始化
- 後端已啟動：在 `backend/` 內

  ```bash
  python3 app.py
  ```

- 前端已啟動：在 `frondend/` 內

  ```bash
  python3 -m http.server 5500
  ```

- 瀏覽器開啟：`http://127.0.0.1:5500/index.html`

---

## 1. Renter（租客）測試流程

### 1.1 登入 & 搜尋車輛

1. 開 `login.html`
2. 使用種子帳號登入：

   - `gmail`: `alexwong@gmail.com`
   - `password`: `password`

3. 成功後會導回 `index.html`，右上角顯示登入狀態。
4. 點「Search」進到 `search.html`，確認能看到多輛車（狀態為 `available`）。

**DB 檢查：**

```sql
SELECT user_id, userType, userStatus, gmail
FROM `User`
WHERE gmail = 'alexwong@gmail.com';
```

應該看到 `userType='renter'`、`userStatus='active'`。

---

### 1.2 完成一次租車流程（含保險）

1. 在 `search.html` 選一台 `available` 的車 → 進入 `insurance.html`
2. 在 `insurance.html` 選一個保險方案（例如「Full Coverage」）→ 按「Continue」
3. 在 `rent.html`：
   - 選擇合理的 `Rental Start/End Time`
   - 填入 `Pickup Location` / `Drop-off Location`
   - 下方會顯示：
     - `Rental Days`
     - `Vehicle Rental` 金額
     - `Insurance Fee`
     - `Total Amount`
   - 按「Confirm Rental」建立訂單，2 秒後導到 `pay.html`

**DB 檢查：**

```sql
SELECT * 
FROM Rental 
ORDER BY rental_id DESC
LIMIT 1;

SELECT status 
FROM Vehicle 
WHERE vehicle_id = <上面那筆 rental 的 vehicle_id>;
```

期望：

- 新增一筆 `Rental`：
  - `pickupLocation` / `dropoffLocation` 有值
  - `orderStatus='pending'`
  - `paymentStatus='unpaid'`
- 該車的 `Vehicle.status='rented'`

---

### 1.3 付款 & 檢查收據

1. 在 `pay.html`：
   - 金額顯示與剛才 `Total Amount` 相同
   - 填入付款方式 & Transaction Number → 按「Pay」
2. 看到 Success 訊息後，系統會導向 `success.html`。

**DB 檢查：**

```sql
SELECT rental_id, orderStatus, paymentStatus, totalAmount
FROM Rental
ORDER BY rental_id DESC
LIMIT 1;

SELECT *
FROM Payment
ORDER BY payment_id DESC
LIMIT 1;
```

期望：

- 該租單：`orderStatus='confirmed'`、`paymentStatus='paid'`
- 新增一筆 `Payment`：
  - `rental_id` 對得上
  - `paymentStatus='paid'`

在前端 `return.html` 的歷史列表中，點「Receipt」應能彈出所有 payment 記錄。

---

### 1.4 還車 & 歷史紀錄

1. 在 `return.html`：
   - 頂部會顯示「Current Rental Order」
   - 顯示內容包含：
     - 車輛資訊
     - 租期
     - `Pickup/Drop-off`
     - 保險資訊
2. 按「Confirm Return」→ 確認 → 返回成功提示。

**DB 檢查：**

```sql
SELECT rental_id, orderStatus, paymentStatus, returnTime
FROM Rental
ORDER BY rental_id DESC
LIMIT 1;

SELECT status 
FROM Vehicle 
WHERE vehicle_id = <同一筆 rental 的 vehicle_id>;
```

期望：

- `orderStatus='completed'`
- `paymentStatus='paid'`（不變）
- `returnTime` 不為 NULL
- 該車 `status='available'`

在 `return.html` 的歷史列表中，該筆租單應顯示：
- 正確的 `Pickup → Drop-off`
- 正確的保險名稱
- `Order Status=completed`

---

## 2. Owner（車主）測試流程

### 2.1 以 Owner 登入 & 開啟 Owner Dashboard

1. 用種子車主帳號登入（例如）：

   ```text
   gmail: michaellam@gmail.com
   password: password
   ```

2. 登入成功後，在瀏覽器直接開：

   ```text
   http://127.0.0.1:5500/ownerDashboard.html
   ```

3. 頁面頂部會顯示 `Owner user_id = ...`，下方「我的車輛」會列出該 owner 所有車輛。

**DB 檢查：**

```sql
SELECT o.owner_id, u.user_id, u.name, o.verificationStatus
FROM Owner o
JOIN `User` u ON o.user_id = u.user_id
WHERE u.gmail = 'michaellam@gmail.com';
```

再查：

```sql
SELECT vehicle_id, owner_id, brand, model, status
FROM Vehicle
WHERE owner_id = <上面查到的 owner_id>;
```

期望：Owner Dashboard 上看到的車輛與 SQL 結果一致。

---

### 2.2 新增車輛 & 狀態切換

在 `ownerDashboard.html` 右側表單：

1. 填入：
   - `carType`: `SUV`
   - `lisenceNum`: `TEST123`
   - `year`: `2024`
   - `seatNum`: `5`
   - `location`: `Kowloon`
   - `dailyPrice`: `399`
   - `brand/model/photoURL/description` 可隨意填
2. 按「儲存」：
   - 下方訊息顯示「已新增車輛 #...（等待審核）」。
   - 左側列表會多出新的一筆，`status=available`、`verificationStatus=pending`。

**DB 檢查：**

```sql
SELECT vehicle_id, owner_id, carType, lisenceNum, status, verificationStatus
FROM Vehicle
WHERE lisenceNum = 'TEST123';
```

期望：

- 新車 `status='available'`
- `verificationStatus='pending'`
- `owner_id` 對得上該 owner

接著在列表按「切換維修」：
- `status` 會在 `available` / `maintenance` 間切換  
- 再跑一次上面 SQL，確認 status 有更新。

---

### 2.3 車主查看自己的租單 & 收入

在 `ownerDashboard.html` 下半部：

1. 按「載入我的租單」：
   - 上方說明區會顯示：租單總數、已付款數量。
2. 按「載入月收入」：
   - 顯示最近幾個月的收入，例如：
     - `2024-01: $xxxx (N orders) | 2024-02: ...`

**DB 檢查：**

```sql
SELECT r.rental_id, r.totalAmount, r.paymentStatus, v.owner_id
FROM Rental r
JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
WHERE v.owner_id = <owner_id> AND r.paymentStatus = 'paid';
```

Owner Dashboard 顯示的「月收入總額」加起來，應該等於上述查詢的 `SUM(totalAmount)`（按月分組後的總和），誤差只可能來自小數點顯示格式，不應差很多。

---

## 3. Admin（管理員）測試流程

### 3.1 登入 Admin & 查看總覽

1. 開 `adminlogin.html`
2. 使用種子 admin 帳號：

   ```text
   gmail: admin@gmail.com
   password: password
   ```

3. 登入成功後進 `adminDashboard.html`：
   - Dashboard 區塊顯示：
     - `total_orders / today_orders / total_revenue / total_users / active_orders / available_vehicles`

**DB 檢查（對照幾個關鍵數字）：**

```sql
SELECT COUNT(*) AS total_orders FROM Rental;

SELECT COUNT(*) AS total_users FROM `User`;

SELECT COUNT(*) AS active_orders 
FROM Rental 
WHERE orderStatus IN ('confirmed', 'active');

SELECT COUNT(*) AS available_vehicles 
FROM Vehicle 
WHERE status = 'available';
```

管理員儀表板上的數字應該和這幾個查詢一致或非常接近（`today_orders` 取決於 `createTime` 是否是今天，這個可以選擇性檢查）。

---

### 3.2 User Management：搜尋 / 停用 / 匯出

1. 進入「User Management」分頁。
2. 使用上方篩選：
   - `userType=renter`
   - `userStatus=active`
   - Email filter 輸入 `alexwong`
   - 按 `Apply`
3. 只會看到該筆 renter 資料。
4. 按該列上的「Disable」：
   - 狀態欄應變成 `disabled`

**DB 檢查：**

```sql
SELECT userStatus 
FROM `User` 
WHERE gmail = 'alexwong@gmail.com';
```

期望：`userStatus='disabled'`。  
此時再嘗試用 `alexwong@gmail.com / password` 登入前端，應收到 `User is disabled` 的錯誤訊息。

5. 測試匯出：
   - 在 User Management 右側點「Export CSV」
   - 瀏覽器會下載 `users.csv`
   - 開啟檔案，能看到與畫面一致的 user 列表。

---

### 3.3 Vehicle Management：篩選 / 審核

1. 進入「Vehicle Management」分頁。
2. 篩選：
   - `status=available`
   - `verification=pending`
3. 應只看到尚未審核的車輛（包含你剛剛用 owner 新增的）。
4. 點該列的「Verify」按鈕 → 在 prompt 輸入 `approved`：
   - 該列的 verification 欄位應更新為 `approved`。

**DB 檢查：**

```sql
SELECT verificationStatus 
FROM Vehicle 
WHERE lisenceNum = 'TEST123';
```

期望：`verificationStatus='approved'`。

同樣可以測試「Export CSV」，下載 `vehicles.csv` 對照畫面。

---

### 3.4 Rental Management：篩選 & 匯出

1. 進入「Rental Management」分頁。
2. 使用篩選：
   - `orderStatus=completed`
   - `paymentStatus=paid`
3. 表格應只顯示「已完成且已付款」的訂單。

**DB 檢查：**

```sql
SELECT rental_id, orderStatus, paymentStatus
FROM Rental
WHERE orderStatus = 'completed' AND paymentStatus = 'paid';
```

表格內容應與此查詢結果相符。  
點「Export CSV」後，`rentals.csv` 裡應只包含篩選後的訂單（目前是全部匯出，你可以再決定是否要做「只匯出篩選後」的版本）。

---

這三組測試（Renter / Owner / Admin），如果都能通過，而且 DB 查詢結果與前端畫面一致，就代表你現在的「流程邏輯」在技術上是正常運作的。  
之後如果你再新增功能，建議依照這個格式把新功能追加測試案例，方便自己或同學/老師複驗。*** End Patch***}"""
} -->
