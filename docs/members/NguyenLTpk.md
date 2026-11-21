# NguyenLTpk (Lê Thành Nguyên - 2A202603733) — phản tư cá nhân (Phase 1)

- **Tôi đã làm (kèm link commit)**:
  - Cập nhật thông tin thành viên D (`NguyenLTpk`) trong `TEAM.md`, khởi tạo nhật ký `docs/standup.md` và `docs/ai-usage-log.md` cho Phase 1: commit [c787e0c](https://github.com/k1b1t0/K5-L3B-LAB-Day12-AI-SDLC-SuperIdol/commit/c787e0c)
  - Nâng cấp giao diện Canvas trong `chonoi/web/index.html`: vẽ bến ghe Chợ Nổi, vạch độ sâu, hiệu ứng bọt nước, cảnh báo viền đỏ khi hết oxy; vẽ bàn ăn, biểu cảm khách hàng, thanh kiên nhẫn đổi màu và thanh tiến trình bếp lò: commit [f62474b](https://github.com/k1b1t0/K5-L3B-LAB-Day12-AI-SDLC-SuperIdol/commit/f62474b)
  - Bổ sung bảng Thực đơn & Công thức HUD góc màn hình (hiển thị 3 món chính và kiểm tra sẵn sàng từ kho `stock`): commit [f62474b](https://github.com/k1b1t0/K5-L3B-LAB-Day12-AI-SDLC-SuperIdol/commit/f62474b)
  - Triển khai tính năng Tự do Sáng tạo bằng Web Audio API thuần (tiếng lặn tùm, tiếng chuông chín món, tiếng xu trả tiền, còi báo ngạt) kèm phím tắt Mute `[M]`, hiệu ứng chữ bay (+60k, +Tip!) và tài liệu hóa vào `README.md`, `CREDITS.md`: commit [6993a0c](https://github.com/k1b1t0/K5-L3B-LAB-Day12-AI-SDLC-SuperIdol/commit/6993a0c)
  - Hoàn thiện tài liệu Phase 1: `docs/retro.md` (khung Phase 2 & Phase 4) và `CHANGELOG.md`.
- **Tôi đã review (kèm link)**:
  - Kiểm tra `test_live.py` để đảm bảo thẻ `<canvas id="c"></canvas>` và các API `/state`, `/input` của `chonoi/live.py` hoạt động mượt mà không bị lỗi.
  - Rà soát giao diện `gather` và `quan` để các trường dữ liệu hiển thị đúng 100% theo snapshot mà không ảnh hưởng tới chế độ headless.
- **AI sai ở đâu và tôi phát hiện thế nào**:
  - AI khởi tạo Web Audio API ngay khi file HTML tải xong, dẫn đến cảnh báo `The AudioContext was not allowed to start` trên Chrome/Edge do chính sách Autoplay. Tôi phát hiện qua Console log của trình duyệt và đã sửa thành khởi tạo Lazy khi người chơi bấm phím tương tác đầu tiên.
- **Điều tôi học được**:
  - Cách thiết kế Client UI độc lập hoàn toàn với Simulation Engine (chỉ tiêu thụ dữ liệu snapshot từ server), vừa tăng trải nghiệm người dùng vừa bảo toàn 100% tính tất định của hệ thống headless.
