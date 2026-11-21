# ADR-0001: Kho cá thể và độ tươi chính xác (Contract v1.2)

- Trạng thái: chấp nhận
- Ngày, người quyết: 2026-11-21, C (haianh020505), báo Đức (gather), Nam (quan), Nguyên (web)

## Bối cảnh
TICKET-03 thay file kho đếm `{"items":{kind:n}}` bằng kho cá thể `{"items":[{id,kind,fresh}]}`. Có thêm độ tươi hao theo tick, ngưỡng ươn 30, giữ chỗ theo id và giá theo độ tươi. Ngưỡng và `floor` phải tính đúng tuyệt đối; JSONL làm tròn 3 chữ số khi xuất.

## Các lựa chọn đã cân nhắc
1. `float`: đơn giản, nhưng `30 − k/120` cộng dồn sai số → nhánh ở ngưỡng/floor có thể lệch.
2. Số nguyên 240 đơn vị/điểm (gợi ý trong ticket): chính xác, nhưng phải đổi đơn vị khi đọc/ghi và mọi fixture fresh tùy ý (vd 29.99) không biểu diễn được.
3. `fractions.Fraction` trong bộ nhớ, đọc file bằng `fresh_in` khôi phục phân số mẫu ≤ 10⁶, ghi `int` nếu tròn, ngược lại `float` đầy đủ.

## Quyết định
Chọn 3. Một chỗ đọc/ghi duy nhất ở `chonoi/inventory.py` (`validate_items`, `read_inventory`, `inventory_payload`, `items_out`). Đọc lại file v1.2 vẫn giữ giá trị và nhánh ở ngưỡng (`test_threshold_branch_survives_file_round_trip`). Kho đếm v1.1 → mã 2, không giữ hai phiên bản.

## Hệ quả
| Module | File | Thay đổi |
|---|---|---|
| Hợp đồng | `game.contract.json`, `chonoi/contract.py` | `1.2`, khối `freshness` + kiểm |
| Kho | `chonoi/inventory.py` | schema cá thể, Fraction |
| Lặn | `chonoi/sim/gather.py` (Đức) | hao giỏ, `spoiled` location hold, `lost` cá thể, id mới cho Ngày kế |
| Quán | `chonoi/sim/quan.py` (Nam) | hao kho, giữ chỗ theo id, giữ lại khi ươn, chốt giá theo fresh |
| Vòng Ngày | `chonoi/sim/day.py`, `chonoi/runner.py` | Shop snapshot cá thể, `new_hold_ids` |
| Scenario | `chonoi/scenario.py` | hold/stock/reserved theo schema mới |
| HUD | `chonoi/web/index.html`, `chonoi/live.py` (Nguyên) | vạch tươi, ✕ ươn, `meta.freshness` |
| Test | `tests/*` | fixture mới; `test_p3_fresh.py` |
