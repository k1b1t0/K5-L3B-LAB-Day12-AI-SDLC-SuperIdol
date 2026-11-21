# Checklist hoàn thành lab — 2026-11-21

Nguồn: HANDOFF-C, README, AGENTS và code contract 1.3. Không có scratchpad/TICKET-04 gốc trong checkout.

## Kế hoạch và quyết định
- Giữ Python stdlib và luật hiện có; chỉ sửa lỗi tái hiện được. Không thêm tính năng.
- Hoàn thiện bản hiện có thay vì viết lại benchmark/bot. Bot không bắt cá là giới hạn công khai.
- Người dùng giữ commit cuối; không tự commit thay khi chưa được yêu cầu rõ hơn.
- Thay đổi README/credits/retro/changelog cần chủ sở hữu Nguyên biết; clarify cần Nam biết; tag/integration cần Đức biết. Agent không tự gửi tin nhắn nhóm.

## Tiến độ
- [x] Đọc handoff, đối chiếu code/lịch sử và kiểm repo public.
- [x] Check team, full regression, tất định gather/quan/day, soak 10 Ngày ×2.
- [x] Bench thật; lưu số đo, không tự đặt ngưỡng AC.
- [x] Clone sạch nhánh P4, live HTTP 200; ghi SHA.
- [x] README, LICENSE có phạm vi đóng góp nhóm, CREDITS, CHANGELOG, release notes.
- [x] Retro, phản tư C, clarify, nhật ký AI, lệnh bench/soak.
- [x] Rà độc lập; sửa lỗi bench launch bằng test đỏ → xanh.
- [x] Merge P2 (#5) và P3 (#6) bằng merge commit; mở PR nháp P4 (#7).
- [x] Chốt log hồi quy sau sửa bench: 93 test đạt; ma trận P4 và số đo mới nhất.
- [x] Verify main từng mốc và đẩy tag phase-1, phase-2, phase-3.
- [ ] User tạo commit cuối, push P4; kiểm CI và chuyển #7 khỏi draft.
- [ ] Merge #7; verify-phase trên main sau merge, kiểm clone sạch bản cuối.
- [ ] Tag phase-4/v1.0.0 cùng SHA, ZIP và GitHub Release.

## Commit cuối của C (PowerShell)
Rà `git diff` và `git status` trước. HANDOFF-C là ghi chú bàn giao chưa track, không đưa vào commit nộp.

```powershell
git add AGENTS.md README.md CHANGELOG.md CREDITS.md LICENSE chonoi/bench.py tests/test_p4_release.py docs
git diff --cached --check
git commit -m "fix(release): finalize v1.0.0 proof, docs and browser launch cleanup"
git push origin phase4-v1.3
```

## Sau commit cuối
Không gắn tag Phase 4 trước khi verify main. Agent có thể tiếp tục phần dưới ngay sau khi user báo đã commit/push:

```powershell
gh pr ready 7
gh pr checks 7
gh pr merge 7 --merge
git fetch origin
```

Checkout main sạch vào clone/worktree riêng, chạy skill verify-phase N=4 và smoke live.
Nếu log mới khác log nhánh, giữ bằng chứng thực tế và ghi SHA nơi lưu; không báo nhánh là main.
Sau khi đạt, gắn hai tag vào SHA main đã kiểm (không dùng main di động làm target release):

```powershell
$releaseSha = git rev-parse origin/main
git tag phase-4 $releaseSha
git tag v1.0.0 $releaseSha
git push origin phase-4 v1.0.0
git archive --format=zip -o "$env:TEMP/chonoi-v1.0.0.zip" phase-4
gh release create v1.0.0 "$env:TEMP/chonoi-v1.0.0.zip" --verify-tag --title "v1.0.0" --notes-file docs/release-notes-v1.0.0.md
```

Không sửa lịch sử, không giả mốc deadline, không ghi tag/release đã tạo khi còn chờ commit cuối.
