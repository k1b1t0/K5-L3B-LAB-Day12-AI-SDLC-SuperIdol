# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Duc | Claude 3.5 Sonnet / Antigravity | Sinh khung hàm xử lý oxy, lặn ngoi và va chạm giỏ | ~25,000 | AI quên kiểm tra `_in_dock` trước khi hái và bỏ qua kiểm tra sức chứa khi nhặt nút. |
| Phase 1 | Nam | Claude 3.5 Sonnet / Antigravity | Viết logic đặt chỗ nguyên liệu và vòng đời khách ăn | ~30,000 | AI tính sai nguyên liệu khả dụng khi khách gọi món trùng nhau; quên trừ `reserved`. |
| Phase 1 | C | Claude 3.5 Sonnet | Soạn 2 skills AI và kịch bản test kiểm tra determinism | ~20,000 | AI sinh lệnh test có đường dẫn Linux bash không chạy trực tiếp được trên shell Windows. |
| Phase 1 | Nguyen | Claude 3.5 Sonnet / Antigravity | Thiết kế Canvas HUD hiển thị thực đơn và WebAudio sound effects | ~22,000 | AI dùng AudioContext phát ngay khi load trang bị trình duyệt chặn Autoplay; cần gắn trigger qua phím/tương tác đầu tiên. |
| Phase 2 | C (haianh020505) | Claude Code | Thử phá headless bằng ~50 đầu vào sai; chặn NaN/Infinity, giới hạn bộ đếm theo tuning, giữ chỗ vượt kho `--inventory` | không đo | Test AI viết theo spec đều xanh nhưng không bắt được `Infinity` lọt vào JSONL; chỉ thử phá bằng đầu vào lạ mới thấy. |
| Phase 3 | C (haianh020505) | Claude Code | Bộ quét 32 đầu vào hỏng `test_p3_robustness`, kiểm JSONL là JSON chuẩn | không đo | Test JSON chuẩn do AI viết chỉ kiểm file kho khi có điều kiện → có thể xanh mà không kiểm gì; đã bỏ nhánh đó. |
| Phase 4 | C (haianh020505) | Claude Code | Chạy lại `verify-phase` trên `main` sau merge, kiểm số commit theo `TEAM.md` | không đo | Bảng số commit bản trước gộp cả merge commit (k1b1t0 = 6); đếm lại bằng `--no-merges` → 4 + 2 merge PR. |
| Phase 2 | C (haianh020505) | Claude Code (Opus) | Hiện thực v1.1 theo TICKET-02: `sim/day.py`, cá/Cá Sấu/Máu, 2 bếp, pause, Shop, live day + HUD; viết `test_p2_day` | không đo | AI tính sai bước Shop trong test (quên snapshot chỉ ghi theo `--snapshot-every`) và đọc sai thời điểm intro Ngày 2 do lấy state giữa 2 lần poll; xác minh lại bằng headless `--snapshot-every 1` và chạy lại trên Chrome. |
