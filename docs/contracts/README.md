# Hợp đồng tích hợp (SuperIdol)

1. **Schema file kho** (`inventory.json`):
   - Cấu trúc: `{"items": {<kind>: <count>}}`
   - Chỉ chứa các nguyên liệu có số lượng `> 0`. Sắp xếp các khóa `items` theo thứ tự chữ cái.
   - Nguyên liệu P1: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
   - File mẫu chuẩn: [inventory.sample.json](inventory.sample.json).
   - Ghi kho: do runner/gather thực hiện nguyên tử khi kết thúc buổi sáng (`gather_end`).

2. **Giao diện giữa `sim/*` và `client/ui`**:
   - UI (`chonoi/web/index.html`) chỉ đọc snapshot qua `GET /state` (bao gồm `player`, `hold`, `nodes`, `fish`, `stoves`, `tables`, `customers`, `events`, `meta`...).
   - UI gửi tín hiệu điều khiển qua `POST /input` (`{"move": [dx, dy], "interact": bool, "catch": bool}`).
   - Phím chơi: WASD / Phím mũi tên (di chuyển), `E` (tương tác `interact`), `Space` (bắt cá `catch`), `R` (chơi lại).

3. **Danh sách sự kiện (`events`)**:
   - `gather`:
     - `dive`: khi người chơi bơi từ mặt nước xuống dưới nước (`pos`).
     - `surface`: khi người chơi bơi từ dưới nước lên mặt nước (`pos`).
     - `oxygen_empty`: khi oxy chạm 0 ở dưới nước.
     - `choke`: khi ngạt đủ `choke_interval_ticks` dưới nước (`hp`).
     - `faint`: khi HP về 0 do ngạt.
     - `gather`: khi hái thành công nút trên mặt nước (`node_id`, `kind`).
     - `node_regrown`: khi nút mọc lại (`node_id`).
     - `fish_caught`: khi bắt thành công đàn cá (`fish_id`, `kind`).
     - `hold_full`: khi bấm hái/bắt nhưng khoang chứa đầy.
     - `gather_end`: khi kết thúc lượt lặn hái (`reason`: `docked` / `time` / `fainted`, kèm `inventory`).
   - `quan`:
     - `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, `customer_left`, `no_dish`, `quan_end`.
