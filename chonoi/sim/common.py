"""Phần dùng chung giữa các pha: số chính xác, ví (tiền/uy tín), cá thể nguyên liệu, khoảng cách/di chuyển.

Uy tín, tỷ lệ boa, độ tươi tính bằng `Fraction` để `floor` và so ngưỡng không lệch do số thực
(ví dụ 3.0 + 0.2 × 5 phải đúng bằng 4). Chỉ đổi sang float khi xuất JSON.
"""

import math
from fractions import Fraction

TICK = 60


def frac(x) -> Fraction:
    """Số JSON (int/float) -> Fraction đúng giá trị thập phân đã viết (0.2 -> 1/5)."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, float):
        return Fraction(repr(x))
    return Fraction(x)


def ticks(seconds) -> int:
    return int(round(seconds * TICK))


def num_out(x):
    """Fraction -> số xuất JSON (int nếu nguyên, ngược lại float)."""
    if isinstance(x, Fraction):
        return int(x) if x.denominator == 1 else float(x)
    return x


def rep_out(x) -> float:
    return float(x)


class Wallet:
    """Tiền, tổng thu, uy tín — sống xuyên pha và xuyên Ngày trong mode day."""

    def __init__(self, tuning, money=0, earned=0, reputation=None):
        q = tuning["quan"]
        self.money = money
        self.earned = earned
        self.rep = frac(q["reputation_initial"] if reputation is None else reputation)
        self.rep_min = frac(q["reputation_min"])
        self.rep_max = frac(q["reputation_max"])

    def add_rep(self, delta):
        self.rep = min(self.rep_max, max(self.rep_min, self.rep + frac(delta)))

    @property
    def reputation(self) -> float:
        return float(self.rep)

    def score(self, mult) -> int:
        return self.earned + mult * math.floor(self.rep)


def move_toward(pos, target, step):
    """Đi tới `target` tối đa `step` mét. Trả (pos mới, đã tới chưa)."""
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    d = math.hypot(dx, dy)
    if d <= step:
        return [float(target[0]), float(target[1])], True
    return [pos[0] + dx / d * step, pos[1] + dy / d * step], False


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v
