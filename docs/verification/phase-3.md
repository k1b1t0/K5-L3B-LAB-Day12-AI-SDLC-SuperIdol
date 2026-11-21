# Ma trận truy vết Phase 3

Repo không có đặc tả mới cho Phase 3 (contract vẫn v1.0). Phần QA của Phase 3 là **chống crash và hồi quy**: biến bộ thử phá dùng ở Phase 2 thành test lâu dài để lỗ hổng không quay lại khi nhóm thêm luật. Mã `R3-*` do nhóm đặt.
Bằng chứng chạy trên nhánh `haianh` (Windows, Python 3.10, `PYTHONUTF8=1`); chạy lại `verify-phase` trên `main` trước khi gắn tag.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| R3-01 32 đầu vào hỏng (scenario 17, inputs 9, kho 6; cả `gather` và `quan`) → mã 2, không Traceback, không ghi `--out` lẫn `--inventory-out` | `test_p3_robustness.test_malformed_inputs_exit_2_no_crash` | [unittest.log](../proof/phase-3/unittest.log) | đạt |
| R3-02 Chạy bình thường (900 tick, có bơi/bắt/tương tác) → mọi dòng JSONL là JSON chuẩn, không NaN/Infinity | `test_p3_robustness.test_outputs_are_strict_json` | [unittest.log](../proof/phase-3/unittest.log) | đạt |
| R3-03 Harness: skill `check-determinism-and-contract` có bước thêm ca hỏng khi thêm trường mới; `AGENTS.md` ghi quy tắc không crash | đọc [SKILL.md](../../.agents/skills/check-determinism-and-contract/SKILL.md), [AGENTS.md](../../AGENTS.md) | git log | đạt |
| Hồi quy Phase 1–2 | toàn bộ test chạy cùng lần | [unittest.log](../proof/phase-3/unittest.log), [determinism.log](../proof/phase-3/determinism.log) | đạt |
| TEAM Danh sách nhóm | `tools/check_team.py` | [check_team.log](../proof/phase-3/check_team.log) | chưa đạt hẳn — `TEAM.md` còn `member-c`/`member-d` |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
  - Không còn đầu vào nào trong bộ quét gây mã 1/Traceback; output JSONL chuẩn.
  - Bộ quét chỉ phủ các ca đã nghĩ ra, không phải fuzz ngẫu nhiên — ca mới phải thêm tay vào `CASES`.
- Điều cần chỉnh cho phase sau:
  - Phase 4: chạy `verify-phase` đầy đủ, kiểm số commit từng người, tổng kết P1–P3.
