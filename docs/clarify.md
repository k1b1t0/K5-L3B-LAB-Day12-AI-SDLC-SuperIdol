# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 17:50 | Thứ tự ưu tiên khi bấm tương tác `interact` tại quán ở vị trí gần cả bếp và bàn? | Ưu tiên đối tượng gần nhất; nếu khoảng cách bằng nhau thì ưu tiên Bếp trước Bàn; nếu cùng loại thì ID nhỏ hơn (theo PRD-0 mục F). | Nam (PO) |
| 2 | 2026-11-21 17:52 | Khi khách đến mà không đủ nguyên liệu khả dụng (sau khi trừ lượng đã giữ chỗ)? | Phát sự kiện `no_dish`, khách không ngồi vào bàn và rời đi ngay, không trừ uy tín (PRD-0 mục F). | Nam (PO) |
| 3 | 2026-11-21 17:54 | Quy tắc tính tiền boa (`tip`) khi giao món? | Khách được phục vụ khi tỷ lệ kiên nhẫn còn lại `patience_left / patience_max >= tip_min_patience_ratio` (50%) thì được tip `round(price * tip_rate)` và cộng uy tín `tip_reputation` (+0.2). | Nam (PO) |
| 4 | 2026-11-21 (P2) | Tick đổi pha trong `--mode day` có ghi snapshot dù không trùng `--snapshot-every`? | Có: runner ép một snapshot ở tick đổi pha/đổi Ngày (vẫn tối đa 1 snapshot/tick) để kiểm `phase_tick:0`. | C (QA), báo Đức |
| 5 | 2026-11-21 (P2) | Snapshot quán có thêm trường `available` (kho trừ phần giữ chỗ) có vi phạm contract? | Giữ: là trường bổ sung, test hộp đen không cấm trường thừa; HUD dùng để báo món nấu được. | C (QA) |
| 6 | 2026-11-21 (P2) | `chonoi.live --mode day` mặc định bao nhiêu Ngày? | 5 (D1–D5), cho đổi bằng `--days 1..5`; ngoài miền → mã 2 như headless. | C, báo Nguyên |
| 7 | 2026-11-21 (P3) | Snapshot JSONL làm tròn fresh 3 chữ số, file kho thì không — smoke "so chính xác độ tươi" so thế nào? | File kho ghi đủ chính xác (`fresh_out`); so snapshot/`gather_end.inventory` với file theo dung sai quan sát ±0.01 của TICKET-03, id/kind so chính xác. | C (QA) |
| 8 | 2026-11-21 (P3) | Hàng trong giỏ đã < 30 từ scenario có phát `spoiled` không? | Không: chỉ phát khi đi từ ≥ 30 xuống < 30. | C (QA) |
| 9 | 2026-11-21 (P3) | HUD lấy ngưỡng ươn ở đâu? | `live` gắn `meta.freshness` từ contract; client không hard-code (mặc định 30 chỉ khi thiếu). | C, báo Nguyên |
| 10 | 2026-11-21 (P4) | Bench cần cài thư viện Python ngoài không? | Không. Dùng trình duyệt Chrome/Chromium/Edge có sẵn; `CHONOI_BROWSER` chỉ đường dẫn trình duyệt. Warmup 3 s, cửa sổ 1280×720. | C, đối chiếu `bench.py` |
| 11 | 2026-11-21 (P4) | Soak chứng minh điều gì? | Bot chỉ hái rau, không bắt cá; kiểm đủ Ngày, 0 crash và kết quả tất định sau khi bỏ `duration_s`, không dùng doanh thu làm tiêu chí độ bền. | C, đối chiếu `soak.py` |
| 12 | 2026-11-21 (P4) | TICKET-04 gốc ở đâu? | HANDOFF-C nhắc scratchpad nhưng checkout không có scratchpad; GitHub repo tắt Issues. Ma trận P4 dùng checklist bàn giao và ghi rõ nguồn, không tự nhận mã AC chính thức hoặc tự đặt ngưỡng FPS. | C (giới hạn bằng chứng) |
