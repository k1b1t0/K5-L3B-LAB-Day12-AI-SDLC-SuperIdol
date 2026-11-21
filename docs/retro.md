# Retro nhóm

## Phase 2 (nhanh)
- **Điều tốt**:
  - Phân chia 4 nhánh độc lập theo checklist của từng thành viên giúp cả nhóm code song song không hề bị xung đột file hay git conflict.
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

## Phase 4 (release contract 1.3)
- Rà hành động P2: đã có clarify cho chuyển pha, kho cá thể và độ tươi; đối chiếu yêu cầu với contract và test, không tự đặt ngưỡng hiệu năng hoặc mã AC chính thức.
- Điều tốt: giữ luật trong contract, gom validation kho, có test migration và JSONL tất định; kiểm chứng lại thay vì dùng log cũ.
- Điều cần sửa: hồ sơ P4 còn ghi contract 1.0 và số thành viên mẫu dù code đã lên 1.3; phải ghi SHA/môi trường cùng mỗi lượt proof.
- AI sai: thử khởi chạy bench bằng CHONOI_BROWSER không tồn tại làm Traceback vì Popen nằm ngoài try/finally. Test tái hiện đỏ trước, đưa launch vào try/finally rồi test xanh; server và profile được dọn khi lỗi.
- Số liệu release: xem unittest.log, bench.json và soak.json tại docs/proof/phase-4. Token/chi phí phiên Codex: không đo.
- Review: rà độc lập bench/soak và hồ sơ release; phát hiện phạm vi giấy phép starter chưa xác minh và lỗi launch bench nói trên.
- Hành động tiếp: mỗi phase mở PR sớm, chạy verify-phase trên main trước tag; lưu nguồn ticket và SHA bằng chứng; giữ ngưỡng FPS chính thức trong checklist khi có đề gốc.
