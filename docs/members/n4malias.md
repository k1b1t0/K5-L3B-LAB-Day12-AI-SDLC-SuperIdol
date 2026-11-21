# n4malias (Nguyen Thanh Nam) — phản tư cá nhân (Phase 1)

- **Tôi đã làm (kèm link commit)**:
  - Cập nhật thông tin PO trong `TEAM.md`, xây dựng kế hoạch Phase 1 tại `docs/plan/phase-1.md` và ghi nhận clarify tại `docs/clarify.md`: [46bdb85](https://github.com/k1b1t0/K5-L3B-LAB-Day12-AI-SDLC-SuperIdol/commit/46bdb85)
  - Cài đặt Lát 3 quán (`sim/quan.py`): lịch khách đến, giữ chỗ nguyên liệu khả dụng, đếm kiên nhẫn, no_dish và khách bỏ đi trừ uy tín: [bb82d67](https://github.com/k1b1t0/K5-L3B-LAB-Day12-AI-SDLC-SuperIdol/commit/bb82d67)
  - Cài đặt Lát 4 quán (`sim/quan.py`): tiến trình bếp nấu, chín, tương tác bưng món và phục vụ bàn, thu tiền, tính tip và cập nhật uy tín: [0e8ddf9](https://github.com/k1b1t0/K5-L3B-LAB-Day12-AI-SDLC-SuperIdol/commit/0e8ddf9)
- **Tôi đã review**:
  - Review chéo logic xuất kho của `gather.py` (do Đức phụ trách) để đảm bảo kho nguyên liệu khớp hoàn hảo với đầu vào `stock` của `quan.py`.
- **AI sai ở đâu và tôi phát hiện thế nào**:
  - AI ban đầu tính toán nguyên liệu khả dụng mà quên trừ đi các món khách đã ngồi trước đó đang giữ chỗ (`reserved`). Tôi phát hiện qua ca kiểm thử 2 khách liên tiếp gọi cùng món khi kho chỉ còn đủ cho 1 món và đã bổ sung hàm `_get_available_stock()`.
- **Điều tôi học được**:
  - Tầm quan trọng của việc chốt quy tắc xử lý tương tác theo thứ tự ưu tiên (bếp trước bàn, cự ly gần nhất, ID nhỏ nhất) để tránh lỗi trạng thái tranh chấp trong simulation.
