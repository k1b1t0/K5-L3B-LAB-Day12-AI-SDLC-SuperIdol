"""Soak headless (Contract v1.3): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày (gather -> quan -> shop) trong một tiến trình bằng bot tất định (chỉ đọc snapshot, không RNG/đồng hồ).
Kế hoạch D1–D5 lặp ở Ngày 6+; tiền, uy tín, nâng cấp, id cá thể tiếp tục xuyên suốt (cùng một DaySim).
soak.json: {days, days_completed, crashes, results[{day, earned, reputation, score}] lúc Shop đóng, duration_s}.
Chỉ duration_s là đồng hồ thật (để báo cáo); mọi trường khác tất định theo seed.
"""

import argparse
import json
import math
import sys
import time
import traceback

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState, normalize
from .runner import Session

BUY_ORDER = ("oxygen", "hp")  # Shop: thử mua lần lượt rồi đóng


class Bot:
    """Bot tất định: hái nút trên mặt nước rồi cập bến; ở quán nấu -> bưng -> giao; ở Shop mua rồi đóng."""

    def __init__(self, tuning):
        self.g, self.q = tuning["gather"], tuning["quan"]
        self._held = False  # interact đang giữ -> bước sau nhả để có cạnh lên mới

    def _go(self, pos, target, radius):
        dx, dy = target[0] - pos[0], target[1] - pos[1]
        if math.hypot(dx, dy) <= radius * 0.8:
            return (0.0, 0.0), True
        return normalize([max(-1, min(1, dx)), max(-1, min(1, dy))]), False

    def act(self, s) -> InputState:
        phase, buy, shop_done, move, near = s["phase"], None, False, (0.0, 0.0), False
        if phase == "gather":
            move, near = self._gather(s)
        elif phase == "quan":
            move, near = self._quan(s)
        elif phase == "shop":
            k = s["phase_tick"]
            buy = BUY_ORDER[k] if k < len(BUY_ORDER) else None
            shop_done = k == len(BUY_ORDER)
        press = near and not self._held
        self._held = press
        held = {"interact": press, "shop_done": shop_done}
        edges = {b for b, v in held.items() if v}
        return InputState(move, held, edges, buy)

    def _gather(self, s):
        g, p = self.g, s["player"]["pos"]
        dock = g["dock_pos"]
        back_ticks = math.dist(p, dock) / g["swim_speed"] * 60 + 120
        ready = [n for n in s["nodes"] if n["ready"]]
        if s["hold_count"] >= s["hold_capacity"] or s["time_left_ticks"] <= back_ticks or not ready:
            return self._go(p, dock, g["dock_radius"])
        node = min(ready, key=lambda n: (math.dist(p, n["pos"]), n["id"]))
        return self._go(p, node["pos"], g["interact_radius"])

    def _quan(self, s):
        p, r = s["player"]["pos"], self.q["interact_radius"]
        tables = {t["id"]: t for t in s["tables"]}
        if s["hand"]:
            c = [c for c in s["customers"] if c["id"] == s["hand"]["order_id"]]
            if c:
                return self._go(p, tables[c[0]["table_id"]]["pos"], r)
        ready = [st for st in s["stoves"] if st["state"] == "ready"]
        if ready and not s["hand"]:
            return self._go(p, ready[0]["pos"], r)
        idle = [st for st in s["stoves"] if st["state"] == "idle"]
        if idle and any(c.get("order_status") == "reserved" for c in s["customers"]):
            return self._go(p, min(idle, key=lambda st: (math.dist(p, st["pos"]), st["id"]))["pos"], r)
        return (0.0, 0.0), False


def soak(seed, days, tuning):
    sess = Session("day", tuning, {}, seed, days=days)
    bot = Bot(tuning)
    results, crashes = [], 0
    per_day = sum(tuning[k]["duration_s"] for k in ("gather", "quan")) * 60 + tuning["shop"]["max_ticks"]
    limit = days * per_day * 2  # chặn vòng vô hạn: vượt -> tính là crash
    try:
        while not sess.done:
            if sess.tick >= limit:
                raise RuntimeError(f"quá {limit} tick mà chưa xong {days} Ngày")
            for row in sess.step(bot.act(sess.snapshot())):
                if row["name"] == "shop_end":
                    e = sess.end_row()
                    results.append({"day": row["day"], "earned": e["earned"], "reputation": e["reputation"],
                                    "score": e["score"]})
    except Exception:  # noqa: BLE001 — soak phải đếm crash thay vì chết
        traceback.print_exc()
        crashes = 1
    return {"days": days, "days_completed": sess.sim.days_completed, "crashes": crashes, "results": results}


def main(argv=None) -> int:
    t0 = time.perf_counter()
    p = argparse.ArgumentParser(prog="chonoi.soak", description="Soak headless N Ngày (Contract v1.3).")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    try:
        try:
            a = p.parse_args(argv)
        except SystemExit as e:
            raise BadInput("tham số sai") from e
        if not 1 <= a.days <= 1000:
            raise BadInput("--days phải trong [1, 1000]")
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    out = soak(a.seed, a.days, tuning)
    out["duration_s"] = round(time.perf_counter() - t0, 3)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(json.dumps({k: out[k] for k in ("days", "days_completed", "crashes", "duration_s")}), flush=True)
    return 0 if out["crashes"] == 0 and out["days_completed"] == out["days"] else 1


if __name__ == "__main__":
    sys.exit(main())
