# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # smoke test
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (tùy chọn)
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Sáng tạo của nhóm (SuperIdol)

Thực hiện bởi: **Lê Thành Nguyên (`NguyenLTpk` / MSSV: `2A202603733`) — Module `client/ui` & Scrum/Release**.

Nhóm đã phát triển và tích hợp các tính năng sáng tạo đặc sắc cho phiên bản trình duyệt trực tiếp (`chonoi.live`), bảo đảm **hoàn toàn tắt ở chế độ headless** để không ảnh hưởng đến bất kỳ chỉ số test tự động ẩn nào:
1. **Âm thanh tổng hợp thời gian thực (Procedural Web Audio API)**:
   - Toàn bộ âm thanh được sinh trực tiếp bằng thuật toán dao động sóng âm (OscillatorNode, GainNode) của Web Audio API thuần, **không dùng file âm thanh bên ngoài, không lo vấn đề bản quyền**.
   - Hiệu ứng âm thanh phong phú: tiếng tùm khi lặn (`dive`), tiếng ngoi lên mặt nước (`surface`), tiếng vợt bắt cá (`fish_caught`), tiếng chuông reo khi món chín tại bếp lò (`dish_ready`), tiếng keng tiền xu khi khách trả tiền và tip (`paid`), tiếng thở dốc ngạt oxy (`choke`).
   - Tích hợp nút bật/tắt âm thanh trên giao diện và phím tắt nhanh `[M]` (Mute/Unmute).
2. **Hiệu ứng chữ nổi bay sinh động (Floating Texts)**:
   - Hiển thị phản hồi trực quan ngay tại vị trí trung tâm khi có sự kiện: `+60k (Tip +18k!)`, `🔔 Món đã chín!`, `⚠ ĐẦY GIỎ!`, `💔 NGẠT OXY! -1 HP`, `🚪 Khách bỏ về!`.
3. **Bảng HUD Thực đơn & Kiểm tra nguyên liệu thời gian thực**:
   - Hiển thị danh sách 3 món ăn Chợ Nổi kèm công thức và tự động kiểm tra kho nguyên liệu `stock` để báo `✔ ĐỦ` hoặc `✖ THIẾU` ngay trên màn hình.
4. **Đồ họa Chợ Nổi miền Tây sông nước**:
   - Tái hiện khung cảnh ghe xuồng neo bến Chợ Nổi với mái bạt che nắng, cọc neo bến, gợn sóng sông nước lăn tăn, vệt tia nắng xuyên qua mặt nước, hiệu ứng viền đỏ cảnh báo khi Út Sen sắp cạn oxy.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
