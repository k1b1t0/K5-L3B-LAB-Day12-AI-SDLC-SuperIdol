# Ma trận truy vết Phase 2 (TICKET-02, Test Contract v1.1)

Bằng chứng tạo bằng lệnh thật trên Windows + Git Bash (Python 3.10, `PYTHONUTF8=1`), chạy lại trên `main` sau merge trước khi gắn tag `phase-2`. Mã `AC-P2-xx` do nhóm đặt theo DoD của TICKET-02.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 `contract_version:"1.1"`, tuning chuẩn, 6 nguyên liệu + 6 món đọc từ dữ liệu | `test_scenario_validation.TuningQuan.test_current_contract_is_valid`, `test_bad_tuning_rejected` | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| AC-P2-02 Cá bơi + sinh theo lịch; `random_fish:false` cho fixture đứng yên | `test_p2_day.FishAndMonsters.test_initial_fish_distinct_spawn_points_and_scheduled_spawn`, `test_random_fish_false_fixture_stands_still` | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| AC-P2-03 Cá Sấu: `monster_hit` mất nửa giỏ LIFO, bất tử, bật lùi; Máu về 0 → `faint` + `gather_end(fainted)` cùng tick | `test_monster_hit_loses_half_hold_lifo_and_recoils`, `test_monster_faint_ends_gather_same_tick` | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| AC-P2-04 2 bếp / 4 bàn nấu song song; đóng ca: khách chờ rời, khách đang ăn trả `closing`, không phạt uy tín | `test_p2_day.QuanTwoStovesAndClosing` | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| AC-P2-05 Pause theo cạnh: `paused`/`resumed`, `sim_tick` và timer đứng yên (cả Shop) | `test_p2_day.Pause`, `DayLoop.test_paused_shop_timer_frozen` | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| AC-P2-06 `--mode day`: `day_start → day_plan → phase_start` ở tick 0, đổi pha cùng tick, snapshot ép ở tick đổi pha, `days_complete` | `DayLoop.test_tick0_events_then_phase_transitions_same_tick`; chạy `--days 1` không input | [unittest.log](../proof/phase-2/unittest.log), [day-smoke.log](../proof/phase-2/day-smoke.log) | đạt |
| AC-P2-07 Kế hoạch D1–D5 công bố đúng; menu quán lọc theo kế hoạch | `day_plan` D1 trong day-smoke; `test_scenario_hold_goes_to_quan_stock` | [day-smoke.log](../proof/phase-2/day-smoke.log) | đạt |
| AC-P2-08 Shop: `bought`/`buy_failed(funds,unknown,max_level)`, hết giờ `shop_end(time)`; cấp đã mua áp từ Ngày kế (`oxygen_max_ticks` 1800→2700, `hp_max` 3→4) | `test_shop_buy_then_upgrade_active_next_day`, `test_buy_max_level_and_shop_timeout`; chạy 2 Ngày có mua | [multiday.log](../proof/phase-2/multiday.log) | đạt |
| AC-P2-09 CLI/scenario day sai → mã 2 (`--days`, `--inventory*` ở day, 17 scenario hỏng) | `test_p2_day.DayCliAndScenarioExit2` (4 test), `test_p3_robustness` (ca v1.1) | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| AC-P2-10 Smoke tích hợp 2 tiến trình: `gather --inventory-out` → `quan --inventory`, stock snapshot tick 0 khớp file kho | script trong [integration.log](../proof/phase-2/integration.log) (in cả lệnh) | [integration.log](../proof/phase-2/integration.log) | đạt — `KHỚP` |
| AC-P2-11 Tất định: gather/quan/day cùng seed giống từng byte | chạy 2 lần + `cmp` | [determinism.log](../proof/phase-2/determinism.log) | đạt |
| AC-P2-12 Chơi trọn vòng ngày trên trình duyệt: menu, intro Ngày/tối, HUD, Shop, pause, tổng kết | `python3 -m chonoi.live --mode day`, chơi thử bằng Chrome (menu → D1 → quán → Shop mua oxy+hp → D2 → Tổng kết); `test_live` | [unittest.log](../proof/phase-2/unittest.log) (`test_live`); kiểm tay | đạt (kiểm tay, không có log tự động cho phần vẽ) |
| Hồi quy P1 với số chuẩn v1.1 | toàn bộ test P1 trong cùng lần chạy (71 test) | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| TEAM | `tools/check_team.py` | [check_team.log](../proof/phase-2/check_team.log) | đạt |

## Test cũ đổi vì luật v1.1 (lý do)
- `test_quan_slice3` (kiên nhẫn): thêm `stock` — v1.1 đơn đã giữ chỗ phải có hàng thật trong kho.
- `test_quan_slice4`: payload món thành `{order_id, dish_id, base_price}`, bỏ `patience_max_ticks` khỏi scenario.
- `test_p1_integration`: menu v1.1 có 6 món nên món của khách đọc từ `customer_arrived`, không cố định; tip dùng `floor`.
- `test_smoke_p1`: số cá ban đầu = `fish_initial`; nút `catch/pause/...` nay hợp lệ nên ca từ chối đổi sang `jump/fly`; `day` là mode hợp lệ.
- `test_gather_slice2`: giỏ là mảng cá thể → đọc qua `hold_out()`.

## Đánh giá ngắn
- Đạt toàn bộ AC lõi Phase 2; không làm mở rộng (nhóm 4 người không bắt buộc).
- Phần vẽ HUD/menu chỉ kiểm tay trên Chrome; giao diện chưa có test tự động.
- Giả định đã ghi `docs/clarify.md` (#4–#6).

## Kiểm lại trước release v1.0.0 (2026-11-21)

Checkout sạch commit main 304d659ebf570c14cbed2f5db41583dae9cb9afd: 71 unittest đạt, check_team đạt, gather/quan seed=1 ticks=3600 giống từng byte. Xem [metadata](../proof/phase-2/release-recheck.json), [unittest](../proof/phase-2/unittest.log), [tất định](../proof/phase-2/determinism.log). Các nhận xét trạng thái nhánh/TEAM cũ phía trên là lịch sử, không phải trạng thái release hiện tại.
