# Changelog

All notable changes to this project will be documented in this file.

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
