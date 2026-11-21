# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)
- Kiểm danh sách nhóm: `python3 tools/check_team.py`
- Windows: test hộp đen gọi `headless_cmd` = `python3` → cần lệnh `python3` trong PATH (chép `python.exe` thành `python3.exe` vào một thư mục trong PATH, hoặc chạy trong WSL/Git Bash có python3). KHÔNG đổi `headless_cmd` trong contract (CI Ubuntu dùng `python3`). Đặt thêm `PYTHONUTF8=1` để stderr tiếng Việt không gây `UnicodeDecodeError` trong log test.

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.
- Lỗi đầu vào (contract/scenario/inputs/kho) → `raise BadInput` → mã thoát 2, trước khi ghi `--out`/`--inventory-out`.
- (Phase 2) Kiểm số trong scenario bằng `_num` (chặn NaN/Infinity — `json.load` nhận chúng và làm JSONL hỏng). Bộ đếm có mức tối đa thì lấy mức đó từ tuning (`regrow_s`, `catch_cooldown_s`, `choke_interval_ticks`…), không viết số. Kiểm cần cả kho từ `--inventory` thì gọi từ `headless.py` sau `read_inventory` (ví dụ `check_reserved_fits`).

- (Phase 3) Không được crash với đầu vào hỏng: mọi lỗi đọc/kiểu/giá trị → `BadInput` (mã 2), không bao giờ Traceback/mã 1. Bộ quét `tests/test_p3_robustness.py` — thêm trường mới thì thêm ca hỏng vào `CASES`. Đầu ra JSONL phải là JSON chuẩn (không NaN/Infinity).

## Ai sở hữu file nào (SuperIdol)
| Người (handle) | Module | Sở hữu chính |
|---|---|---|
| Đức (`k1b1t0`) | sim/gather, Integrator | `chonoi/sim/gather.py`, `TEAM.md`, `docs/contracts/`, gắn tag |
| Nam (`n4malias`) | sim/quan, PO | `chonoi/sim/quan.py`, `docs/clarify.md`, `docs/plan/`, `docs/adr/` |
| C (`haianh020505`) | qa, AI harness | `chonoi/scenario.py`, `chonoi/contract.py`, phần kiểm đầu vào trong `chonoi/headless.py`, `tests/test_scenario_validation.py`, `tests/test_p*_*.py`, `docs/verification/`, `docs/proof/`, `AGENTS.md`, `.agents/skills/` |
| D | client/ui, Scrum/Release | `chonoi/web/`, `README.md` (Sáng tạo), `docs/ai-usage-log.md`, `docs/standup.md`, `docs/retro.md`, `CHANGELOG.md`, `CREDITS.md` |

Agent chỉ sửa file thuộc lát được giao; cần sửa file của người khác thì báo người đó.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- [`verify-phase`](.agents/skills/verify-phase/SKILL.md) — trước khi gắn tag `phase-N`: chạy check_team + toàn bộ test + kiểm tất định 2 lần cùng seed, ghi log vào `docs/proof/phase-N/`, cập nhật `docs/verification/phase-N.md`.
- [`check-determinism-and-contract`](.agents/skills/check-determinism-and-contract/SKILL.md) — trước khi commit/PR có sửa `chonoi/sim/*`, `scenario.py`, `contract.py`: rà RNG/đồng hồ, `sort_by_id`, id, số hard-code, `BadInput` → mã 2.
