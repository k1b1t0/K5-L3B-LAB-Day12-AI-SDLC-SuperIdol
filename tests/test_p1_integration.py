"""Phase 1 hộp đen xuyên suốt: gather xuất kho -> quan đọc kho, phục vụ trọn một khách; tất định của quan.

Bổ sung cho test_smoke_p1 (đã có INV-01 đọc kho ở tick 0 và CON-02 tất định của gather).
"""

import json
import math
import unittest

from helpers import ROOT, Workdir, events, read_jsonl, run_headless, snapshots, write_json

# Út Sen đứng ngay bếp B1 [2, 8]; khách đầu tiên đến ở first_customer_tick (120).
# Nấu xong -> bưng -> đi sang bàn T1 [9, 2] -> giao món. Thời điểm đã đo bằng chạy thật.
QUAN_FRAMES = {"frames": [
    {"tick": 125, "interact": True}, {"tick": 126, "interact": False},   # cook_started
    {"tick": 500, "interact": True}, {"tick": 501, "interact": False},   # dish_picked
    {"tick": 502, "move": [1, 0]}, {"tick": 610, "move": [0, -1]}, {"tick": 700, "move": [0, 0]},
    {"tick": 720, "interact": True}, {"tick": 721, "interact": False},   # served
]}
SHIFT_TICKS = 1400  # đủ cho khách ăn xong (eat_s) rồi hết ca


def contract_tuning():
    with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


class Phase1EndToEnd(unittest.TestCase):
    def _gather_inventory(self, w):
        sc = write_json(w.path("g_sc.json"), {"gather": {"hold": ["ca_loc"]}})
        inp = write_json(w.path("g_in.json"), {"frames": [{"tick": 0, "interact": True}]})
        inv = w.path("inv.json")
        code, err = run_headless("--mode", "gather", "--seed", "3", "--ticks", "1", "--scenario", sc, "--inputs", inp,
                                 "--inventory-out", inv, "--out", w.path("g.jsonl"))
        self.assertEqual(code, 0, err)
        return inv

    def _run_quan(self, w, inv, out_name, seed="3"):
        sc = write_json(w.path("q_sc.json"), {"quan": {"player": {"pos": [2, 8]}, "time_left_ticks": SHIFT_TICKS}})
        inp = write_json(w.path("q_in.json"), QUAN_FRAMES)
        out = w.path(out_name)
        code, err = run_headless("--mode", "quan", "--seed", seed, "--ticks", str(SHIFT_TICKS + 100),
                                 "--inventory", inv, "--scenario", sc, "--inputs", inp, "--out", out)
        self.assertEqual(code, 0, err)
        return read_jsonl(out)

    def test_gather_to_quan_full_service(self):
        t = contract_tuning()
        q, dish = t["quan"], t["menu"]["ca_loc_nuong_trui"]
        with Workdir() as w:
            inv = self._gather_inventory(w)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_loc": 1}})
            rows = self._run_quan(w, inv, "q.jsonl")

        names = [r["name"] for r in events(rows)]
        flow = ["customer_arrived", "cook_started", "dish_ready", "dish_picked", "served", "paid", "quan_end"]
        self.assertEqual([n for n in names if n in flow], flow)
        self.assertEqual(events(rows, "customer_arrived")[0]["tick"], q["first_customer_tick"])
        self.assertEqual(events(rows, "customer_arrived")[0]["data"]["dish_id"], "ca_loc_nuong_trui")

        start, ready = events(rows, "cook_started")[0], events(rows, "dish_ready")[0]
        self.assertEqual(ready["tick"] - start["tick"], int(round(dish["cook_s"] * 60)))
        served, paid = events(rows, "served")[0], events(rows, "paid")[0]
        self.assertEqual(paid["tick"] - served["tick"], int(round(q["eat_s"] * 60)))

        tip = int(round(dish["price"] * q["tip_rate"]))  # phục vụ sớm -> kiên nhẫn còn > tip_min_patience_ratio
        self.assertEqual((paid["data"]["price"], paid["data"]["tip"]), (dish["price"], tip))
        end_ev = events(rows, "quan_end")[0]["data"]
        self.assertEqual(end_ev["reason"], "time")
        self.assertEqual(end_ev["earned"], dish["price"] + tip)
        self.assertAlmostEqual(end_ev["reputation"], q["reputation_initial"] + q["tip_reputation"])

        end = rows[-1]
        self.assertEqual(end["type"], "end")
        self.assertEqual(end["score"], end["earned"] + 100 * math.floor(end["reputation"]))
        self.assertEqual(snapshots(rows)[-1]["stock"], {})  # nguyên liệu đã dùng hết cho món

    def test_quan_deterministic_bytes(self):
        with Workdir() as w:
            inv = self._gather_inventory(w)
            self._run_quan(w, inv, "q1.jsonl")
            self._run_quan(w, inv, "q2.jsonl")
            with open(w.path("q1.jsonl"), "rb") as a, open(w.path("q2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
