# Changelog

All notable changes to this project will be documented in this file.

## [Phase 3] - 2026-11-21 — Test Contract v1.2

### Changed (breaking)
- File kho `{"items":{kind:n}}` → `{"items":[{"id","kind","fresh"}]}` (kho cá thể, sắp theo id). Kho đếm v1.1 → mã 2. Xem [ADR-0001](docs/adr/0001-instance-inventory.md).
- `contract_version:"1.2"`, thêm `tuning.freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`.
- Scenario: `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id.
- JSONL: snapshot `hold`/`stock` (cả Shop) là cá thể, `reserved` là mảng id; `cook_started.items`, `lost` là cá thể.
- Giá: `base_price = floor(giá niêm yết × TB fresh / 100)` chốt lúc bắt đầu nấu.

### Added
- Hao tươi giỏ 0.5/s, kho quán 0.25/s; pause dừng hao; event `spoiled {item_id, kind, location}`.
- Giữ chỗ theo id (tươi nhất, hòa theo id); hàng giữ vừa ươn → nhả, giữ lại một lần, không đủ → `unfulfillable`.
- Day: Ngày 1 giữ id mẫu, Ngày kế cấp id mới.
- HUD: vạch tươi dưới ô giỏ, ✕ hàng ươn, "tươi TB · ươn n", chữ bay khi ươn.
- `tests/test_p3_fresh.py` (13 test), 14 ca kho hỏng mới trong `test_p3_robustness`.

### Cập nhật fixture (migration)
- Mọi fixture kho/giỏ/reserved dùng helper `inst([...])` trong `tests/helpers.py`; lý do từng test đổi ghi ở `docs/verification/phase-3.md`.

## [Phase 2] - 2026-11-21 — Test Contract v1.1

### Changed (breaking)
- `game.contract.json` lên `contract_version:"1.1"`: tuning chuẩn, 6 nguyên liệu, 6 món, `day_plan` D1–D5, `shop`, cá bơi/sinh, Cá Sấu, Máu.
- Giỏ/kho trong sim là cá thể `{id, kind, fresh}` (file kho vẫn dạng đếm ở v1.1); payload món `{order_id, dish_id, base_price}`; `tip = floor(base_price × tip_rate)`.
- `paid.data` có `base_price, tip, amount, reason`.

### Added
- `--mode day` (`chonoi/sim/day.py`): vòng gather → quan → shop, `--days`, Shop mua `oxygen`/`hp`, áp cấp từ Ngày kế, `days_complete`.
- Pause theo cạnh ở mọi mode; 2 bếp / 4 bàn; đóng ca `closing`.
- Live client: menu chính, intro Ngày/tối, HUD Máu/oxy/thủy quái, Shop, tổng kết, tương phản cao `[H]`.
- Test `tests/test_p2_day.py` (15 test), ca v1.1 trong `test_p3_robustness`, `test_scenario_validation`.

### Cập nhật fixture
- Scenario quán: đơn đã giữ chỗ phải có `stock` thật; `dish` trên bếp/tay dùng `dish_id`, `base_price`.

## [Phase 1] - 2026-11-21

### Added
- **Core Gather Simulation (`chonoi/sim/gather.py`)**:
  - Lát 1: Bơi, gia tốc ramp, kiểm soát oxy, các sự kiện `dive`, `surface`, `oxygen_empty`, ngạt thở `choke`, ngất `faint` và kết thúc ca `gather_end`.
  - Lát 2: Hái bông súng / bông điên điển tại mặt nước, thời gian mọc lại `regrow_ticks`, bắt cá lóc / cá linh dưới nước kèm hồi chiêu `catch_cd_ticks`, sức chứa giỏ LIFO `hold_full` và cập bến `docked`.
- **Core Quan Simulation (`chonoi/sim/quan.py`)**:
  - Lát 3: Khách đến theo lịch `first_customer_tick`, chọn món nấu được, giữ chỗ nguyên liệu khả dụng `reserved`, đếm ngược kiên nhẫn, khách bỏ đi `customer_left` và không có món `no_dish`.
  - Lát 4: Bếp lò nấu món `cooking` -> chín `dish_ready`, bưng món trên tay `dish_picked`, phục vụ bàn `served`, khách ăn xong trả tiền + tiền boa `paid`, cập nhật uy tín `reputation` và kết thúc ca `quan_end`.
- **Client & Web UI (`chonoi/web/index.html`)**:
  - Giao diện đồ họa sông nước Chợ Nổi miền Tây: bến ghe xuồng neo đậu, vạch đo độ sâu, tia nắng xuyên nước, viền đỏ cảnh báo cạn oxy.
  - Sàn thuyền nhà hàng, bếp lò đất nung, bàn ăn gỗ, thanh kiên nhẫn khách đổi màu Xanh/Vàng/Đỏ kèm vạch mốc 50% tính tiền boa.
  - Bảng HUD Thực đơn & Kiểm tra kho nguyên liệu thời gian thực.
  - Bộ âm thanh tự tổng hợp bằng Web Audio API thuần (tiếng lặn, ngoi, bắt cá, chuông chín món, keng tiền xu, còi báo ngạt) kèm phím tắt Mute `[M]`.
  - Hiệu ứng chữ nổi bay (`floating text`) phản hồi tức thì sự kiện.
- **AI Harness & Quy trình (`.agents/skills/`, `AGENTS.md`, `docs/`)**:
  - 2 AI skills: `verify-phase` và `check-determinism-and-contract`.
  - Cập nhật quy tắc nhóm và phân quyền file trong `AGENTS.md`.
  - Thiết lập nhật ký sử dụng AI `docs/ai-usage-log.md` và standup `docs/standup.md`.
  - Phản tư cá nhân cho các thành viên trong `docs/members/`.
