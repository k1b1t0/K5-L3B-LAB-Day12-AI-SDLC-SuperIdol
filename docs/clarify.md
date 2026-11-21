# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 17:50 | Thứ tự ưu tiên khi bấm tương tác `interact` tại quán ở vị trí gần cả bếp và bàn? | Ưu tiên đối tượng gần nhất; nếu khoảng cách bằng nhau thì ưu tiên Bếp trước Bàn; nếu cùng loại thì ID nhỏ hơn (theo PRD-0 mục F). | Nam (PO) |
| 2 | 2026-11-21 17:52 | Khi khách đến mà không đủ nguyên liệu khả dụng (sau khi trừ lượng đã giữ chỗ)? | Phát sự kiện `no_dish`, khách không ngồi vào bàn và rời đi ngay, không trừ uy tín (PRD-0 mục F). | Nam (PO) |
| 3 | 2026-11-21 17:54 | Quy tắc tính tiền boa (`tip`) khi giao món? | Khách được phục vụ khi tỷ lệ kiên nhẫn còn lại `patience_left / patience_max >= tip_min_patience_ratio` (50%) thì được tip `round(price * tip_rate)` và cộng uy tín `tip_reputation` (+0.2). | Nam (PO) |
| 4 | 2026-11-21 (P2) | Tick đổi pha trong `--mode day` có ghi snapshot dù không trùng `--snapshot-every`? | Có: runner ép một snapshot ở tick đổi pha/đổi Ngày (vẫn tối đa 1 snapshot/tick) để kiểm `phase_tick:0`. | C (QA), báo Đức |
| 5 | 2026-11-21 (P2) | Snapshot quán có thêm trường `available` (kho trừ phần giữ chỗ) có vi phạm contract? | Giữ: là trường bổ sung, test hộp đen không cấm trường thừa; HUD dùng để báo món nấu được. | C (QA) |
| 6 | 2026-11-21 (P2) | `chonoi.live --mode day` mặc định bao nhiêu Ngày? | 5 (D1–D5), cho đổi bằng `--days 1..5`; ngoài miền → mã 2 như headless. | C, báo Nguyên |
