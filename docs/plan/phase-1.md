# Kế hoạch Phase 1 (SuperIdol)

- **Mục tiêu**: Hoàn thiện mô phỏng Phase 1 (PRD-0) cho cả 2 buổi Lặn & Hái (`gather`) và Mở Quán (`quan`), đảm bảo chạy tất định 100% trong chế độ headless và chơi mượt trên live UI.
- **Phân công & Lát cắt (Slices)**:
  - **Đức (`k1b1t0`)**: Phụ trách `sim/gather` (Lát 1: Bơi, oxy, ngạt, ngất; Lát 2: Hái nút, bắt cá, giỏ LIFO, cập bến).
  - **Nam (`n4malias`)**: Phụ trách `sim/quan` (Lát 3: Khách đến theo lịch, chọn món, giữ chỗ nguyên liệu, kiên nhẫn, no_dish; Lát 4: Bếp nấu, bưng món, phục vụ, tính tiền, boa, uy tín).
  - **Hải Anh (`haianh020505`)**: Phụ trách `qa` (Kiểm tra mâu thuẫn scenario, hợp đồng tuning, bộ test hộp đen).
  - **Member D (`member-d`)**: Phụ trách `client/ui` (Giao diện web canvas, hiệu ứng, HUD và tài liệu quy trình).
- **Rủi ro & Biện pháp**:
  - Rủi ro lệch thứ tự xử lý sự kiện trong 1 tick giữa bếp và bàn -> Giải pháp: Tuân thủ nghiêm ngặt PRD mục F: giảm kiên nhẫn/bếp trước, sau đó xử lý tương tác (ưu tiên bếp trước bàn, khoảng cách gần nhất, ID nhỏ nhất).
  - Rủi ro không tất định khi random khách/món -> Giải pháp: Gọi RNG duy nhất qua `self.rng.get(...)`, danh sách món và bàn luôn sắp xếp cố định trước khi chọn.
