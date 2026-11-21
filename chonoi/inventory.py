"""File kho (Contract G, v1.2): {"items": [{"id", "kind", "fresh"}, ...]} — kho cá thể.

Đọc: từ chối kho đếm cũ / sai schema / kind lạ / id trùng / fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: sắp theo id, qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định.
Độ tươi trong bộ nhớ là `Fraction` (so ngưỡng 30 và floor chính xác); xuất float/int.
"""

import json
import math
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .ids import sort_by_id

# 6 nguyên liệu (v1.1): thêm cá kèo và kèo nèo
KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS  # tên cũ, giữ cho mã gọi cũ
ITEM_KEYS = {"id", "kind", "fresh"}


def fresh_in(x) -> Fraction:
    """Số JSON -> Fraction. Khôi phục đúng phân số mẫu nhỏ (vd 7201/240) từ float đã ghi,
    để đọc lại file vẫn giữ giá trị và nhánh ở ngưỡng."""
    if isinstance(x, Fraction):
        return x
    d = Fraction(repr(x)) if isinstance(x, float) else Fraction(x)
    if d.denominator <= 10 ** 6:
        return d
    c = Fraction(x).limit_denominator(10 ** 6)
    return c if float(c) == x else d


def fresh_out(f):
    return int(f) if f.denominator == 1 else float(f)


def item_out(i) -> dict:
    return {"id": i["id"], "kind": i["kind"], "fresh": fresh_out(i["fresh"])}


def items_out(items) -> list:
    return [item_out(i) for i in items]


def validate_items(items, kinds=KINDS, name="items") -> list:
    """Mảng cá thể {id, kind, fresh} -> list cá thể (fresh là Fraction), giữ thứ tự."""
    if not isinstance(items, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}} (kho đếm v1.1 không còn hợp lệ)")
    seen, out = set(), []
    for n, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != ITEM_KEYS:
            raise BadInput(f"{name}[{n}] phải có đúng các khóa id, kind, fresh")
        iid, kind, f = it["id"], it["kind"], it["fresh"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"{name}[{n}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"{name}: id trùng {iid}")
        seen.add(iid)
        if not isinstance(kind, str) or kind not in kinds:
            raise BadInput(f"{name}[{n}]: nguyên liệu lạ {kind!r}")
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not 0 <= f <= 100:
            raise BadInput(f"{name}[{n}].fresh phải là số hữu hạn trong [0, 100]")
        out.append({"id": iid, "kind": kind, "fresh": fresh_in(f)})
    return out


def validate_counts(items, kinds=KINDS) -> dict:
    """Object đếm {kind: n >= 0} (dùng cho day_plan.ingredients) -> bỏ mục 0."""
    if not isinstance(items, dict):
        raise BadInput("ingredients phải là object {kind: số lượng}")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def read_inventory(path: str, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds)


def count_kinds(kinds_list) -> dict:
    """Mảng kind -> object đếm, sắp theo kind, bỏ mục 0."""
    counts = {}
    for k in kinds_list:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def inventory_payload(items) -> dict:
    return {"items": items_out(sort_by_id(items))}


def write_inventory(path: str, payload: dict):
    """Ghi {"items": ...} qua file tạm cùng thư mục rồi thay thế nguyên tử."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
