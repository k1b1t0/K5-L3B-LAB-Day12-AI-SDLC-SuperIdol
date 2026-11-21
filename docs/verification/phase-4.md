# Ma trận kiểm chứng Phase 4 — contract 1.3 / release v1.0.0
## Phạm vi bằng chứng
Bằng chứng mới chạy trên nhánh `phase4-v1.3` (Windows, Python 3.10), base `359abab`; metadata tại [environment.json](../proof/phase-4/environment.json). Working tree gồm sửa cleanup khi bench launch lỗi và hồ sơ release. Đây là proof nhánh trước commit cuối, **chưa phải verify trên main sau merge Phase 4**.

| Mục | Kiểm chứng / bằng chứng | Kết quả |
|---|---|---|
| P4-01 Contract 1.3, bench_cmd/soak_cmd | `test_p4_release.ContractV13`, [unittest.log](../proof/phase-4/unittest.log) | Đạt trong hồi quy nhánh |
| P4-02 Bench render 1280×720, warmup 3 s, seed 42, đo 30 s; đủ 5 trường | [bench.json](../proof/phase-4/bench.json), [bench.log](../proof/phase-4/bench.log); công thức có unit test | Đã đo thật; ngưỡng đạt theo đề gốc chưa xác nhận |
| P4-03 Soak 10 Ngày, 0 crash | [soak.json](../proof/phase-4/soak.json), [lần 1](../proof/phase-4/soak-1.log), [lần 2](../proof/phase-4/soak-2.log) | Cả hai lần days_completed=10, crashes=0 |
| P4-04 Soak tất định cùng seed 7 | [soak-determinism.log](../proof/phase-4/soak-determinism.log), [JSON 1](../proof/phase-4/soak-1.json), [JSON 2](../proof/phase-4/soak-2.json) | Giống sau khi bỏ duration_s |
| P4-05 Oxy thấp và thủy quái gần: chữ/ký hiệu, tương phản cao | [ảnh gather](../proof/phase-4/warnings-hc-gather.jpg), hàm `warn()` trong web client | Đã xem lại ảnh kiểm chứng, thấy cả hai cảnh báo; chưa chạy walkthrough UI mới |
| P4-06 Khách sắp giận: chữ/ký hiệu, tương phản cao | [ảnh quan](../proof/phase-4/warnings-hc-quan.jpg) | Đã xem lại ảnh kiểm chứng; HUD chưa có test UI tự động |
| P4-07 Clone sạch, chơi trong ≤3 lệnh, không pip install | [clean-clone.log](../proof/phase-4/clean-clone.log), [server log](../proof/phase-4/clean-clone-server.log), [README](../../README.md) | Clone P4 tại 359abab, live HTTP 200 và Canvas; chờ retest main bản cuối |
| P4-08 Hồi quy P1–P3 và test release | [unittest.log](../proof/phase-4/unittest.log) | 93/93 test đạt sau sửa bench; exit 0 |
| P4-09 Headless tất định | [determinism.log](../proof/phase-4/determinism.log) | gather/quan 3600 tick và day 30000 tick, seed 1, giống từng byte |
| P4-10 Danh sách nhóm và đóng góp | [check_team.log](../proof/phase-4/check_team.log), [TEAM](../../TEAM.md), git shortlog --no-merges | 4 handle thật; mỗi người ≥3 commit có nội dung trên nhánh P4; kiểm lại main sau merge |
| P4-11 Hồ sơ release | [CHANGELOG](../../CHANGELOG.md), [release notes](../release-notes-v1.0.0.md), [LICENSE](../../LICENSE), [CREDITS](../../CREDITS.md), [retro](../retro.md), [phản tư Hải Anh](../members/haianh020505.md) | Đã bổ sung; giấy phép nhóm chỉ áp phần đóng góp nhóm sở hữu |
| P4-12 Tag/release cùng commit và ZIP | [checklist tích hợp](release-checklist.md), PR #7 | Chờ commit cuối, merge P4, verify main và phát hành |
| P4-13 Bench không Traceback khi browser path sai | `BenchMetrics.test_missing_browser_fails_cleanly_without_output` | Test đỏ trước sửa; xanh sau sửa; không tạo bench.json khi lỗi |

## Đánh giá
- Các log P4 cũ contract 1.0 đã được thay. Các proof P1/P2/P3 cũng được chạy lại trên commit main tương ứng; metadata ghi SHA từng mốc.
- Không dùng doanh thu soak để suy ra chiến thuật bot tốt: bot chưa bắt cá.
- Không dùng avg FPS để bỏ qua 1% low. Giữ cả lần đo đầu và lần đo sau sửa cleanup, ghi kết quả thật; chưa xác nhận ngưỡng hiệu năng chính thức.
- Chưa nhận đủ điều kiện nộp cuối khi P4 chưa merge, chưa verify main và chưa có release. Xem checklist để thực hiện ngay sau commit cuối của Hải Anh.

## Số đo benchmark đã lưu
- Lần đầu: avg 59.37 FPS; 1% low 27.74 FPS; load 1579 ms ([JSON](../proof/phase-4/bench-first-run.json), [log](../proof/phase-4/bench-first-run.log)).
- Sau sửa cleanup và chạy hồi quy: avg 60.01 FPS; 1% low 57.94 FPS; load 1559 ms ([JSON](../proof/phase-4/bench.json)). Cả hai dùng seed 42, warmup 3 s, đo 30 s.
