# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Duc | Claude 3.5 Sonnet / Antigravity | Sinh khung hàm xử lý oxy, lặn ngoi và va chạm giỏ | ~25,000 | AI quên kiểm tra `_in_dock` trước khi hái và bỏ qua kiểm tra sức chứa khi nhặt nút. |
| Phase 1 | Nam | Claude 3.5 Sonnet / Antigravity | Viết logic đặt chỗ nguyên liệu và vòng đời khách ăn | ~30,000 | AI tính sai nguyên liệu khả dụng khi khách gọi món trùng nhau; quên trừ `reserved`. |
| Phase 1 | C | Claude 3.5 Sonnet | Soạn 2 skills AI và kịch bản test kiểm tra determinism | ~20,000 | AI sinh lệnh test có đường dẫn Linux bash không chạy trực tiếp được trên shell Windows. |
| Phase 1 | Nguyen | Claude 3.5 Sonnet / Antigravity | Thiết kế Canvas HUD hiển thị thực đơn và WebAudio sound effects | ~22,000 | AI dùng AudioContext phát ngay khi load trang bị trình duyệt chặn Autoplay; cần gắn trigger qua phím/tương tác đầu tiên. |
