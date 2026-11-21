# Ma trận truy vết Phase 4 (hồi quy cuối)

Repo không có đặc tả mới cho Phase 4 (contract vẫn v1.0). Phần QA của Phase 4 là **hồi quy cuối trước khi nộp**: chạy lại `verify-phase` đầy đủ, kiểm mọi AC của P1–P3 vẫn xanh trong cùng một lần chạy, kiểm điều kiện tính commit. Mã `F4-*` do nhóm đặt.
Bằng chứng chạy trên nhánh `haianh` (Windows, Python 3.10, `PYTHONUTF8=1`); chạy lại `verify-phase` trên `main` sau khi merge, trước khi gắn tag.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| F4-01 Hồi quy Phase 1 (CON, MOVE, INV, OXY, GATH, QUAN, V-1 — xem [phase-1.md](phase-1.md)) | toàn bộ test, cùng một lần chạy | [unittest.log](../proof/phase-4/unittest.log) | đạt |
| F4-02 Hồi quy Phase 2 (V2-01..04 — [phase-2.md](phase-2.md)) | `test_p2_validation` trong cùng lần chạy | [unittest.log](../proof/phase-4/unittest.log) | đạt |
| F4-03 Hồi quy Phase 3 (R3-01..03 — [phase-3.md](phase-3.md)) | `test_p3_robustness` trong cùng lần chạy; 0 `Traceback` trong log | [unittest.log](../proof/phase-4/unittest.log) | đạt |
| F4-04 Tất định: cùng seed chạy 2 lần → JSONL giống từng byte (gather, quan; 3600 tick) | `verify-phase` bước 3 | [determinism.log](../proof/phase-4/determinism.log) | đạt |
| F4-05 Commit được tính: tác giả commit phải có trong `TEAM.md` | `git shortlog -sn --all`, so với `TEAM.md` trên `main` | mục "Số commit" dưới | chưa đạt — xem dưới |
| TEAM Danh sách nhóm | `tools/check_team.py` | [check_team.log](../proof/phase-4/check_team.log) | chưa đạt hẳn — `TEAM.md` còn `member-c`/`member-d` |

## Số commit (khi chạy, `git shortlog -sn`)
| Tác giả | Trên `origin/main` | Mọi nhánh |
|---|---|---|
| Hai Duong | 9 | 9 |
| haianh020505 | 0 | 9 (nhánh `haianh`, chưa merge) |
| k1b1t0 | 6 | 6 |
| Nguyen Thanh Nam | 4 | 4 |
| NguyenLTpk | 0 | 4 |

- Commit của `haianh020505` chỉ được tính khi (1) nhánh `haianh` merge vào `main` bằng **merge commit** (không squash, để giữ tác giả và hash dẫn trong phản tư) và (2) Integrator đổi `member-c` thành `haianh020505` trong `TEAM.md`.

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
  - Mọi AC kỹ thuật P1–P3 xanh cùng lúc; tất định từng byte.
  - Chưa đạt: `TEAM.md` (của Integrator) và việc merge nhánh `haianh` — ngoài phạm vi file của C.
- Điều cần chỉnh nếu làm lại:
  - Đổi `TEAM.md` sang handle thật ngay Phase 0; mở PR sớm từng phase thay vì gom cuối.
  - Bộ quét Phase 3 chỉ phủ ca đã nghĩ ra; thêm luật mới thì thêm ca vào `CASES`.
