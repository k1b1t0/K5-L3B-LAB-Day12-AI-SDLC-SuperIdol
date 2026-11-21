---
name: verify-phase
description: Kiểm chứng trước khi gắn tag phase-N — chạy check_team, toàn bộ unittest, kiểm tất định headless, ghi bằng chứng vào docs/proof/phase-N/ và cập nhật docs/verification/phase-N.md. Dùng khi chuẩn bị gắn tag hoặc khi được yêu cầu "verify phase N".
---

# verify-phase

Mục tiêu: trước mỗi tag `phase-N`, có bằng chứng THẬT (log chạy lệnh) và ma trận truy vết trung thực.

## Đầu vào
- `N`: số phase (1..4). Hỏi lại nếu chưa rõ.
- Đang ở nhánh đã gộp đủ code của cả nhóm (thường là `main` mới pull).

## Các bước (bash; trên Windows cần lệnh `python3` có trong PATH — xem AGENTS.md)

```bash
N=1
P=docs/proof/phase-$N
mkdir -p "$P"

# 1. Danh sách nhóm
python3 tools/check_team.py > "$P/check_team.log" 2>&1; echo "exit $?" >> "$P/check_team.log"

# 2. Toàn bộ test (hộp đen + unit), giữ nguyên đầu ra
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v > "$P/unittest.log" 2>&1; echo "exit $?" >> "$P/unittest.log"

# 3. Tất định: cùng seed chạy 2 lần phải giống nhau từng byte
T=$(mktemp -d)
for m in gather quan; do
  for i in 1 2; do python3 -m chonoi.headless --mode $m --seed 1 --ticks 3600 --out "$T/${m}_$i.jsonl"; done
  if cmp -s "$T/${m}_1.jsonl" "$T/${m}_2.jsonl"; then echo "$m seed=1 ticks=3600: GIỐNG từng byte"; else echo "$m: KHÁC — KHÔNG ĐẠT"; fi
done > "$P/determinism.log" 2>&1
rm -rf "$T"
```

4. Mở `docs/verification/phase-N.md`, mỗi AC của PRD phase đó một dòng:

   | AC | Cách kiểm chứng | Bằng chứng | Kết quả |
   |---|---|---|---|
   | CON-02 | `test_smoke_p1.Contract.test_con_02_deterministic_bytes` + chạy 2 lần cmp | `docs/proof/phase-N/unittest.log`, `determinism.log` | đạt |

5. Điền mục "Đánh giá ngắn": AC nào chưa đạt / còn là giả định (ghi rõ đã hỏi PO trong `docs/clarify.md` chưa).

## Quy tắc
- Log phải là đầu ra thật của lệnh, không tự viết tay, không sửa log.
- `.gitignore` chặn `*.jsonl` → bằng chứng dùng đuôi `.log` / `.md` / `.txt`.
- Test đỏ: KHÔNG sửa test cho xanh, KHÔNG gắn tag. Báo người sở hữu module (xem bảng trong AGENTS.md) và Integrator; ghi trung thực "chưa đạt" vào verification nếu hết giờ.
- Kết quả "đạt" chỉ ghi khi có test hoặc log chứng minh.
