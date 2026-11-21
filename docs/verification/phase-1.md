# Ma trận truy vết Phase 1

Mã `CON-*`, `MOVE-*`, `INV-*` lấy theo tên test smoke của giảng viên. `OXY-*`, `GATH-*`, `QUAN-*`, `V-*` là mã nhóm đặt theo checklist QA và các lát công việc — **chưa đối chiếu với danh sách AC trong PRD-0** (nhóm không có bản PRD-0 đầy đủ; đối chiếu lại khi PO có).
Bằng chứng chạy trên nhánh `haianh` (Windows, Python 3.10, `PYTHONUTF8=1`); chạy lại skill `verify-phase` trên `main` sau khi gộp, trước khi gắn tag.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| CON-01 Ticks 0 có snapshot đầu + đúng một dòng `end` | `test_smoke_p1.Contract.test_con_01_ticks_zero_and_end_line` | [unittest.log](../proof/phase-1/unittest.log) | đạt |
| CON-02 Tất định từng byte cùng seed | `test_con_02_deterministic_bytes` (gather), `test_p1_integration.test_gather_and_quan_deterministic_bytes` (gather chơi thật + quan), chạy 2 lần + `cmp` cả hai mode | [unittest.log](../proof/phase-1/unittest.log), [determinism.log](../proof/phase-1/determinism.log) | đạt |
| CON-03 Đầu vào sai → mã 2, không ghi `--out` | `test_con_03_*`, `test_scenario_out_of_domain_exit_2`, `ScenarioModes.*`, `test_scenario_validation.*` (32 scenario quán sai, 12 tuning sai) | [unittest.log](../proof/phase-1/unittest.log) | đạt (giữ chỗ vượt kho mới so với `quan.stock`, chưa so với `--inventory` — xem dưới) |
| MOVE-01..03 Tốc độ sau ramp, heading dương = xuống, chặn mép | `test_move_01_*`, `test_move_02_*`, `test_move_03_*`, `test_move_ramp_doi_huong_trong_tran`, `test_move_mep_vel_ve_0` | [unittest.log](../proof/phase-1/unittest.log) | đạt |
| INV-01 Gather ghi kho, quan đọc kho; không ghi khi hết `--ticks` trước | `Integration.test_inv_01_*`, `test_inv_bad_schema_exit_2`, `test_inventory_and_scenario_stock_conflict`, `test_inventory_flags_mode_mismatch_exit_2` | [unittest.log](../proof/phase-1/unittest.log), [e2e-summary.md](../proof/phase-1/e2e-summary.md) | đạt |
| OXY-01 Lặn/ngoi theo `surface_depth` → `dive` / `surface` | `test_gather_slice1.test_dive_and_surface_events`, `test_p1_integration.test_gather_to_quan_full_service` | [unittest.log](../proof/phase-1/unittest.log), [e2e-summary.md](../proof/phase-1/e2e-summary.md) | đạt |
| OXY-02 Dưới nước oxy −1/tick, mặt nước hồi `oxygen_refill_per_tick`, kẹp [0, max], `oxygen_empty` | `test_gather_slice1.test_oxygen_drain_and_empty` | [unittest.log](../proof/phase-1/unittest.log) | đạt |
| OXY-03 Oxy = 0 dưới nước: đủ `choke_interval_ticks` → `choke` −1 Máu; Máu 0 → `faint`, mất giỏ, `gather_end` `fainted` | `test_gather_slice1.test_choke_and_faint` | [unittest.log](../proof/phase-1/unittest.log) | đạt |
| GATH-01 Hái nút ở mặt nước trong `interact_radius`, nút mọc lại sau `regrow_s` (`node_regrown`) | `test_gather_slice2.test_gather_node_and_regrow`, e2e (hái N1) | [unittest.log](../proof/phase-1/unittest.log), [e2e-summary.md](../proof/phase-1/e2e-summary.md) | đạt |
| GATH-02 Bắt cá dưới nước (`fish_yield`, hồi chiêu `catch_cooldown_s`), giỏ theo thứ tự nhặt, `hold_full` khi vượt `hold_capacity` | `test_gather_slice2.test_catch_fish_and_cooldown`, `test_gather_slice2.test_gather_hold_full`, e2e (bắt F2) | [unittest.log](../proof/phase-1/unittest.log), [e2e-summary.md](../proof/phase-1/e2e-summary.md) | đạt |
| GATH-03 Cập bến xét trước hái → `gather_end` `docked` + xuất kho; hết giờ kết thúc và giữ giỏ | `test_p1_integration.test_dock_checked_before_harvest`, e2e (cập bến), `Movement.test_time_ends_gather_and_keeps_hold` | [unittest.log](../proof/phase-1/unittest.log), [e2e-summary.md](../proof/phase-1/e2e-summary.md) | đạt |
| QUAN-01 Khách đến ở `first_customer_tick`, chọn món nấu được, giữ chỗ nguyên liệu | `test_quan_slice3.test_customer_arrives_and_reserves_stock`, e2e | [unittest.log](../proof/phase-1/unittest.log), [e2e-summary.md](../proof/phase-1/e2e-summary.md) | đạt |
| QUAN-02 Không món nấu được → `no_dish`; hết kiên nhẫn → `customer_left`, trả giữ chỗ, uy tín giảm | `test_quan_slice3.test_no_dish_when_stock_empty`, `test_quan_slice3.test_customer_patience_and_leaves` | [unittest.log](../proof/phase-1/unittest.log) | đạt |
| QUAN-03 Nấu (`cook_s`) → `dish_ready` → bưng `dish_picked` → giao `served` | `test_quan_slice4.test_full_service_cycle`, `test_p1_integration.test_gather_to_quan_full_service` | [unittest.log](../proof/phase-1/unittest.log), [e2e-summary.md](../proof/phase-1/e2e-summary.md) | đạt |
| QUAN-04 Ăn `eat_s` → `paid` giá + tip, uy tín +`tip_reputation`; hết ca `quan_end`, `score = earned + 100 × floor(reputation)` | `test_p1_integration.test_gather_to_quan_full_service` | [e2e-summary.md](../proof/phase-1/e2e-summary.md) | đạt |
| V-1 Tuning quán/menu hợp lệ (bếp/bàn trong biên, uy tín, carry_limit, công thức) | `test_scenario_validation.TuningQuan.*` | [unittest.log](../proof/phase-1/unittest.log) | đạt |
| UI Cửa sổ live phục vụ `/`, `/state`, `/input` | `test_live.*` | [unittest.log](../proof/phase-1/unittest.log) | đạt (chỉ kiểm server, chưa kiểm giao diện bằng mắt) |
| TEAM Danh sách nhóm hợp lệ | `tools/check_team.py` | [check_team.log](../proof/phase-1/check_team.log) | chưa đạt hẳn — script pass nhưng `TEAM.md` trên nhánh này còn `member-c`/`member-d` |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
  - 51/51 test xanh; gather và quan tất định từng byte (seed 1, 3600 tick). Test e2e chạy gather thật (hái + lặn bắt cá + cập bến) rồi đưa kho sang quan.
  - Bốn luật mâu thuẫn theo gợi ý `TODO` của starter đã làm theo cách nhóm hiểu: `hand` là null hoặc id món; khách `eating` phải có `eat_ticks_left`, `price`, `tip`; đơn `assigned_stove` phải trỏ tới bếp đang nấu/chín đúng món của khách, mỗi bếp một đơn; tổng `reserved` không vượt `quan.stock`.
  - Chưa đạt: giữ chỗ vượt kho khi kho đến từ `--inventory` (load_scenario không thấy file kho; cần thêm lời gọi sau `read_inventory`, chạm `headless.py` của khung hoặc `quan.py`).
  - Còn là giả định của nhóm, chưa đối chiếu PRD: làm tròn tip bằng `round()`, không phát sự kiện khi khách đến mà hết bàn, trường `data` của các sự kiện quán.
- Điều cần chỉnh cho phase sau:
  - PO chép mục D và danh sách AC của PRD vào `docs/clarify.md` ngay đầu phase để QA đặt đúng mã AC.
  - Trên Windows chạy test với `python3` trong PATH và `PYTHONUTF8=1` (nếu không, stderr tiếng Việt gây `UnicodeDecodeError` trong log dù test vẫn pass).
