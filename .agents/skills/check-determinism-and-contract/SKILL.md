---
name: check-determinism-and-contract
description: Rà code trước khi commit/PR để giữ headless tất định và đúng hợp đồng — RNG chỉ qua Streams, không đồng hồ hệ thống, duyệt thực thể qua sort_by_id, id qua IdAllocator, số liệu đọc từ game.contract.json, lỗi đầu vào raise BadInput (mã 2) trước khi ghi file, không crash với đầu vào hỏng. Dùng khi sửa chonoi/sim/*, scenario.py, contract.py, inputs.py, inventory.py, headless.py, runner.py hoặc khi review PR.
---

# check-determinism-and-contract

Chạy từng mục, báo kết quả dạng `ĐẠT` / `LỖI file:dòng — lý do`. Không tự sửa luật chơi; nếu nghi sai luật thì báo người sở hữu module.

## 1. Ngẫu nhiên và thời gian
```bash
# Phải chỉ ra đúng 1 dòng: chonoi/rng.py
grep -rnE "^\s*(import random|from random)" chonoi --include=*.py
# Phải rỗng
grep -rnE "time\.(time|monotonic|perf_counter)|datetime\.now" chonoi/sim chonoi/runner.py chonoi/headless.py
```
- Số ngẫu nhiên mới phải gọi `self.rng.get("<tên luồng>")`; tên luồng đúng như PRD và ghi vào AGENTS.md.

## 2. Thứ tự duyệt và id
```bash
grep -nE "for .* in self\.(nodes|fish|stoves|tables|customers)\b" chonoi/sim/*.py
```
- Mỗi vòng duyệt thực thể (có thể sinh sự kiện) phải qua `sort_by_id(...)`; chọn "gần nhất" phải phá hòa bằng `id_key`.
- Id mới: `self.ids.new("<prefix>")`; id có sẵn từ scenario phải `ids.reserve(...)` trước.
- Không duyệt `set`/`dict` không sắp khi kết quả ảnh hưởng sự kiện hoặc snapshot.

## 3. Không hard-code số liệu
```bash
git diff main -- chonoi/sim | grep -nE "^\+.*[^A-Za-z_\"'][0-9]+(\.[0-9]+)?"
```
- Mỗi hằng số mới phải đối chiếu `game.contract.json` (`tuning.*`, `menu`). Trùng giá trị tuning → đọc từ `self.t[...]`/`self.menu`.
- Đổi giây → tick dùng `int(round(s * 60))` thống nhất.

## 4. Lỗi đầu vào → mã 2, không để lại file
- Kiểm mới phải `raise BadInput(...)` trong `contract.py` / `scenario.py` / `__init__` của sim — không `sys.exit`, không `print`.
- Thử nhanh một đầu vào sai:
```bash
T=$(mktemp -d); echo '{"quan": {"customers": [{"id": "C1", "table_id": "T9"}]}}' > "$T/sc.json"
python3 -m chonoi.headless --mode quan --seed 1 --ticks 10 --scenario "$T/sc.json" --out "$T/o.jsonl"; echo "exit $?"
ls "$T"   # không được có o.jsonl
```
- Số đọc từ JSON phải qua `_num` (chặn NaN/Infinity); bộ đếm có mức tối đa thì so với tuning, không viết số.
- Thêm trường/nút/khóa mới (inputs, scenario, kho) → thêm ca hỏng vào `CASES` trong `tests/test_p3_robustness.py`; ca nào ra mã 1 hoặc có `Traceback` là crash, phải chặn bằng `BadInput`.

## 5. Cuối cùng
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` phải xanh; dán dòng tổng kết vào mô tả commit/PR.
