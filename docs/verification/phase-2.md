# Ma trận truy vết Phase 2

Repo không có đặc tả mới cho Phase 2 (contract vẫn v1.0, `--mode day` và `burn_s` còn khóa). Phần QA của Phase 2 là **siết kiểm đầu vào**: thử phá headless bằng ~50 đầu vào sai, mọi ca chạy mã 0 thay vì mã 2 được sửa ở đây. Mã `V2-*` do nhóm đặt.
Bằng chứng chạy trên nhánh `haianh` (Windows, Python 3.10, `PYTHONUTF8=1`); chạy lại `verify-phase` trên `main` trước khi gắn tag.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| V2-01 Số trong scenario phải hữu hạn: `vel`, `heading_deg` (người chơi, đàn cá), `reputation` không được NaN/±Infinity (trước đây ghi `Infinity` vào JSONL → không còn là JSON hợp lệ) | `test_p2_validation.test_bad_exit_2_without_output` (4 ca NaN/Infinity) | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| V2-02 Bộ đếm gather không vượt mức tối đa theo tuning: `regrow_ticks ≤ regrow_s×60`, `catch_cd_ticks ≤ catch_cooldown_s×60`, `zero_oxy_ticks ≤ choke_interval_ticks−1` (bỏ số 59 hard-code) | cùng test (3 ca sai) + `test_valid_edges_still_run` (đúng biên vẫn chạy) | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| V2-03 Khách đang ăn / đơn đã giao bếp không còn giữ chỗ (khớp `quan.py`: bắt đầu nấu thì xóa `reserved`) | cùng test (2 ca) | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| V2-04 Giữ chỗ không vượt kho đọc từ `--inventory` (đóng lỗ hổng ghi ở Phase 1) | `test_reserved_over_inventory_file_exit_2`, ca hợp lệ trong `test_valid_edges_still_run` | [unittest.log](../proof/phase-2/unittest.log) | đạt |
| Hồi quy Phase 1 | toàn bộ test Phase 1 vẫn chạy trong cùng lần chạy | [unittest.log](../proof/phase-2/unittest.log), [determinism.log](../proof/phase-2/determinism.log) | đạt |
| TEAM Danh sách nhóm | `tools/check_team.py` | [check_team.log](../proof/phase-2/check_team.log) | chưa đạt hẳn — `TEAM.md` còn `member-c`/`member-d` |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
  - Cả 9 ca sai mới đều **đỏ khi chưa sửa** (git stash) và xanh sau khi sửa; toàn bộ test xanh, gather/quan tất định từng byte.
  - V2-04 phải sửa `chonoi/headless.py` (khung) thêm 2 dòng gọi `check_reserved_fits` sau `read_inventory` — lý do: `load_scenario` không thấy file kho. Đã báo nhóm qua commit/PR.
  - Không đổi `game.contract.json`, không đụng `sim/*`.
- Điều cần chỉnh cho phase sau:
  - Biến bộ thử phá thành test lâu dài để lỗ hổng không quay lại (Phase 3).
