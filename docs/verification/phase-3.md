# Ma trận truy vết Phase 3 (TICKET-03, Test Contract v1.2 — kho cá thể + độ tươi)

Bằng chứng tạo bằng lệnh thật trên Windows + Git Bash (Python 3.10, `PYTHONUTF8=1`), chạy lại trên `main` sau merge trước khi gắn tag `phase-3`. Mã `AC-P3-xx` do nhóm đặt theo DoD của TICKET-03. Quyết định schema: [ADR-0001](../adr/0001-instance-inventory.md).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 `contract_version:"1.2"`, `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`; tuning sai → mã 2 | `test_p3_fresh.ContractV12`, `test_scenario_validation.TuningQuan` | [unittest.log](../proof/phase-3/unittest.log) | đạt |
| AC-P3-02 File kho `{"items":[{id,kind,fresh}]}`: kho đếm v1.1, id trùng/rỗng, kind lạ, fresh ngoài [0,100]/NaN/bool → mã 2, không ghi `--out` | `test_p3_fresh.FileHandoff.test_count_format_and_bad_instances_exit_2`, `test_smoke_p1.test_inv_bad_schema_exit_2`, 14 ca kho mới trong `test_p3_robustness` | [unittest.log](../proof/phase-3/unittest.log), [integration.log](../proof/phase-3/integration.log) (kho đếm → `exit 2`) | đạt |
| AC-P3-03 Ngưỡng: mẫu `fresh:30` chạy gather 1 bước → `spoiled {item_id:I1, kind:ca_linh, location:hold}` ở tick 1; phát đúng một lần; kẹp đáy 0 | `test_p3_fresh.Threshold` | [threshold.log](../proof/phase-3/threshold.log) | đạt |
| AC-P3-04 Hao tươi: giỏ 0.5/s, kho quán 0.25/s (kể cả hàng giữ chỗ), bắt đầu từ bước sau; pause dừng hao; Shop/món chín không hao | `Threshold.test_pause_stops_decay`, `test_price_fixed_from_freshness_at_cook`, `test_p1_integration` (fresh tính theo tick nhặt) | [unittest.log](../proof/phase-3/unittest.log), [day.log](../proof/phase-3/day.log) | đạt |
| AC-P3-05 Smoke bàn giao file 2 tiến trình: id/kind khớp chính xác, fresh khớp (file đủ chính xác = `100 − 1/120`; JSONL làm tròn 3 chữ số, dung sai ±0.01) | `FileHandoff.test_smoke_gather_file_to_quan`, `test_smoke_p1.test_inv_01_*` | [integration.log](../proof/phase-3/integration.log) — `KHỚP` | đạt |
| AC-P3-06 Đọc lại file giữ nhánh ở ngưỡng (`30 + 1/240` → chưa ươn ở tick 1, ươn ở tick 2) | `Threshold.test_threshold_branch_survives_file_round_trip` | [unittest.log](../proof/phase-3/unittest.log) | đạt |
| AC-P3-07 Giữ chỗ theo id: lấy cá thể chưa ươn tươi nhất, hòa theo id; hàng giữ vừa ươn → nhả và giữ lại một lần; không đủ → `unfulfillable` | `ReserveAndPrice.test_reserved_item_spoils_then_rereserved_freshest`, `..._no_replacement_unfulfillable`, `test_auto_reserve_skips_spoiled` | [unittest.log](../proof/phase-3/unittest.log) | đạt |
| AC-P3-08 Chốt giá lúc bắt đầu nấu: `base_price = floor(giá × TB fresh / 100)`, `tip = floor(base_price × 0.2)`; món chín giữ giá | `test_price_fixed_from_freshness_at_cook`, `test_quan_slice4` (60 → 59), `test_p1_integration` | [unittest.log](../proof/phase-3/unittest.log) | đạt |
| AC-P3-09 JSONL: snapshot `hold`/`stock` (quán + Shop) là cá thể, `reserved` là mảng id; `cook_started.items` theo kind rồi id; `lost` là cá thể LIFO | `test_p2_day` (lost/faint/hold), `test_quan_slice4`, `ReserveAndPrice` | [unittest.log](../proof/phase-3/unittest.log), [day.log](../proof/phase-3/day.log) | đạt |
| AC-P3-10 Scenario: `gather.hold`/`quan.stock` là mảng cá thể; `reserved` trỏ id có thật, chưa ươn, đủ công thức, không dùng chung → sai là mã 2 | `test_scenario_validation` (13 ca v1.2 mới), `test_p3_robustness` | [unittest.log](../proof/phase-3/unittest.log) | đạt |
| AC-P3-11 Day: bàn giao cùng tick không hao thêm; Ngày 1 giữ id mẫu, Ngày kế cấp id mới | `DayIds.test_day1_keeps_template_ids_next_day_new_ids_and_handoff_same_tick` | [day.log](../proof/phase-3/day.log) (I1,I2 → Ngày 2: I3,I4) | đạt |
| AC-P3-12 HUD hiển thị độ tươi/hàng ươn: vạch tươi dưới mỗi ô giỏ, ✕ đỏ cho hàng ươn, "tươi TB · ươn n" ở giỏ và kho quán, chữ bay khi `spoiled` | chạy `python3 -m chonoi.live --mode day` trên Chrome, console không lỗi | kiểm tay | đạt (kiểm tay; phần vẽ không có test tự động) |
| AC-P3-13 Tất định gather/quan/day | 2 lần cùng seed + `cmp` | [determinism.log](../proof/phase-3/determinism.log) | đạt |
| Hồi quy P1–P2 + chống crash | toàn bộ 84 test cùng lần chạy | [unittest.log](../proof/phase-3/unittest.log) | đạt |
| TEAM | `tools/check_team.py` | [check_team.log](../proof/phase-3/check_team.log) | đạt |

## Test cũ đổi vì luật v1.2 (lý do)
- Mọi fixture `gather.hold` / `quan.stock` / `reserved` / file kho → mảng cá thể (`[THAY THẾ]` schema kho, TICKET-03). Thêm helper `inst`, `kinds`, `counts`, `assert_items_close` trong `tests/helpers.py`.
- `test_quan_slice4`: `base_price` 60 → 59 (nấu ở bước 1, fresh `100 − 1/240`).
- `test_p1_integration`: kho có fresh theo tick nhặt; giá/tip tính theo fresh lúc nấu.
- `test_smoke_p1`, `test_p1_integration`: so `gather_end.inventory` và snapshot với file bằng dung sai ±0.01 vì JSONL làm tròn 3 chữ số.
- `test_p2_day`: `lost`/`faint.lost`/`hold` là cá thể; stock so theo đếm kind.
- `test_p3_robustness`, `test_scenario_validation`: ca kho đếm/reserved đếm cũ nay là ca **hỏng** (mã 2).

## Đánh giá ngắn
- Đạt toàn bộ AC lõi; không làm mở rộng (Chợ Chú Sáu, đặt bàn trước) — nhóm 4 người không bắt buộc.
- HUD chỉ kiểm tay. Dung sai ±0.01 chỉ áp cho JSONL; file kho giữ đủ chính xác.

## Kiểm lại trước release v1.0.0 (2026-11-21)

Checkout sạch commit main f1ccf22166fc8edc78e216a6e97020701937ff2b: 84 unittest đạt, check_team đạt, gather/quan seed=1 ticks=3600 giống từng byte. Xem [metadata](../proof/phase-3/release-recheck.json), [unittest](../proof/phase-3/unittest.log), [tất định](../proof/phase-3/determinism.log). Các nhận xét trạng thái nhánh/TEAM cũ phía trên là lịch sử, không phải trạng thái release hiện tại.
