# Retro nhóm

## Phase 2 (nhanh)
- **Điều tốt**:
  - Phân chia 4 nhánh độc lập theo file checklist (`checklist-duc.md`, `checklist-nam.md`, `checklist-C.md`, `checklist-D.md`) giúp cả nhóm code song song không hề bị xung đột file hay git conflict.
  - Toàn bộ 42 smoke unit tests đều pass 100%.
  - Giao diện Web Client `chonoi.live` được nâng cấp sinh động với đồ họa Chợ Nổi, bảng HUD thực đơn và âm thanh Web Audio trực quan giúp quá trình test thủ công cực kỳ thuận tiện.
- **Điều tệ**:
  - Môi trường Windows ban đầu gặp vấn đề khi gọi `headless_cmd` do alias `python3.exe` của Microsoft Store, cần chép file `python3.exe` vào thư mục Python để chạy mượt mà.
  - Một số chi tiết biên của quy tắc giữ chỗ nguyên liệu `reserved` ban đầu AI xử lý chưa đúng, cần viết test case phát hiện sớm.
- **1 hành động cho Phase 3**:
  - PO (Nam) tiếp tục chốt sớm schema sự kiện và bảng thay đổi của Phase 2, Phase 3 vào `docs/clarify.md` ngay trong 5 phút đầu mốc giờ trước khi cả nhóm bắt tay vào code.

## Phase 3 (nhanh — đổi kho)
- **Điều rút ra từ lần đổi kho**: gom đọc/ghi kho về một chỗ (`chonoi/inventory.py`) nên đổi schema chỉ chạm 1 file lõi + fixture; test hộp đen so nguyên object kho thì đổi schema là đỏ hàng loạt → helper `inst()` giúp chuyển nhanh.
- **Điều tệ**: snapshot JSONL làm tròn còn file không → smoke "so chính xác" dễ hiểu sai; đã ghi clarify #7.

## Phase 4 (cuối)
- **Rà lại hành động Phase 2: đã làm chưa? vì sao?**:
  - Đã thực hiện: PO trích xuất đề và phân tích bảng tác động ngay khi mở phase.
- **Điều tốt / điều tệ toàn dự án**:
  - Điều tốt: Tinh thần phối hợp cao, chia việc rõ ràng, AI harness hỗ trợ sinh code nhanh và chuẩn hóa quy trình.
  - Điều tệ: Cần kiểm tra kỹ các ràng buộc môi trường đa nền tảng (Windows vs Linux) sớm hơn.
- **Số liệu: số commit theo người, cách đọc code của nhau, token theo người**:
  - Đức: 6 commits (lõi gather, integration)
  - Nam: 4 commits (lõi quan, PO docs)
  - C: 1 commit (AI skills, AGENTS.md)
  - Nguyên: 4 commits (Web UI Canvas, WebAudio, Creative, Docs)
  - Review: Review chéo qua PR trước khi gộp vào main.
  - Token ước tính: ~20,000 - 30,000 token/người.
- **Một lần AI sai và cách nhóm phát hiện**:
  - AI khởi tạo AudioContext tự động khi tải trang khiến trình duyệt chặn autoplay. Phát hiện qua console log và sửa thành lazy init khi bấm phím.
- **Nếu làm lại, đổi gì**:
  - Thiết lập sẵn môi trường chuẩn hóa (chạy headless trên Docker hoặc cấu hình alias shell) ngay từ phút 0:00.
