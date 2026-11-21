"""Phase 1 hộp đen xuyên suốt: gather chơi thật xuất kho -> quan đọc kho, phục vụ trọn một khách; tất định cả hai.

Bổ sung cho test_smoke_p1 (đã có INV-01 đọc kho ở tick 0 và CON-02 tất định của gather).
"""

import json
import math
import unittest

from helpers import ROOT, Workdir, events, read_jsonl, run_headless, snapshots, write_json

# v1.1: cá bơi và sinh thêm -> dựng scenario cố định (random_fish: false, một đàn F2 đứng sẵn cạnh Út Sen).
# Út Sen ở [12, 3] dưới nước: bắt F2 (cá lóc) -> ngoi lên -> hái N1 [12, 0] -> bơi về bến cập bến.
# Thời điểm đã đo bằng chạy thật (vị trí lấy từ contract).
GATHER_SCENARIO = {"gather": {"player": {"pos": [12, 3]}, "random_fish": False,
                              "fish": [{"id": "F2", "kind": "ca_loc", "pos": [12, 3]}]}}
GATHER_FRAMES = {"frames": [
    {"tick": 0, "catch": True}, {"tick": 1, "catch": False, "move": [0, -1]}, {"tick": 100, "move": [0, 0]},
    {"tick": 110, "interact": True}, {"tick": 111, "interact": False},   # gather N1
    {"tick": 115, "move": [-1, 0]}, {"tick": 280, "move": [0, 0]},
    {"tick": 300, "interact": True}, {"tick": 301, "interact": False},   # docked
]}
GATHER_TICKS = 2000
INVENTORY = {"bong_dien_dien": 1, "ca_loc": 1}  # v1.1: đủ nấu ca_loc_nuong_trui hoặc canh_chua_ca_loc (seed chọn)

# Út Sen đứng ngay bếp B1 [2, 8]; khách đầu tiên đến ở first_customer_tick (120).
# Nấu xong (món lâu nhất 8 s) -> bưng -> đi sang bàn T1 [9, 2] -> giao món. Thời điểm đã đo bằng chạy thật.
QUAN_FRAMES = {"frames": [
    {"tick": 125, "interact": True}, {"tick": 126, "interact": False},   # cook_started
    {"tick": 700, "interact": True}, {"tick": 701, "interact": False},   # dish_picked
    {"tick": 702, "move": [1, 0]}, {"tick": 810, "move": [0, -1]}, {"tick": 900, "move": [0, 0]},
    {"tick": 920, "interact": True}, {"tick": 921, "interact": False},   # served
]}
SHIFT_TICKS = 1700  # đủ cho khách ăn xong (eat_s) rồi hết ca


def contract_tuning():
    with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


class Phase1EndToEnd(unittest.TestCase):
    def _gather_inventory(self, w, out_name="g.jsonl"):
        inp = write_json(w.path("g_in.json"), GATHER_FRAMES)
        sc = write_json(w.path("g_sc.json"), GATHER_SCENARIO)
        inv = w.path("inv.json")
        code, err = run_headless("--mode", "gather", "--seed", "3", "--ticks", str(GATHER_TICKS), "--inputs", inp,
                                 "--scenario", sc,
                                 "--inventory-out", inv, "--out", w.path(out_name))
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
        q = t["quan"]
        with Workdir() as w:
            inv = self._gather_inventory(w)
            g_rows = read_jsonl(w.path("g.jsonl"))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": INVENTORY})
            rows = self._run_quan(w, inv, "q.jsonl")

        g_flow = [(e["name"], e["data"].get("node_id") or e["data"].get("fish_id")) for e in events(g_rows)]
        self.assertEqual(g_flow, [("fish_caught", "F2"), ("surface", None), ("gather", "N1"), ("gather_end", None)])
        g_end = events(g_rows, "gather_end")[0]["data"]
        self.assertEqual(g_end, {"reason": "docked", "inventory": {"items": INVENTORY}})
        self.assertEqual(g_rows[-1]["reason"], "docked")

        names = [r["name"] for r in events(rows)]
        flow = ["customer_arrived", "cook_started", "dish_ready", "dish_picked", "served", "paid", "quan_end"]
        self.assertEqual([n for n in names if n in flow], flow)
        self.assertEqual(events(rows, "customer_arrived")[0]["tick"], q["first_customer_tick"])
        dish_id = events(rows, "customer_arrived")[0]["data"]["dish_id"]
        self.assertIn(dish_id, ("ca_loc_nuong_trui", "canh_chua_ca_loc"))  # chỉ hai món nấu được từ kho
        dish = t["menu"][dish_id]

        start, ready = events(rows, "cook_started")[0], events(rows, "dish_ready")[0]
        self.assertEqual(ready["tick"] - start["tick"], int(round(dish["cook_s"] * 60)))
        served, paid = events(rows, "served")[0], events(rows, "paid")[0]
        self.assertEqual(paid["tick"] - served["tick"], int(round(q["eat_s"] * 60)))

        tip = math.floor(dish["price"] * q["tip_rate"])  # v1.1: tip = floor(base_price × tip_rate)
        self.assertEqual((paid["data"]["base_price"], paid["data"]["tip"]), (dish["price"], tip))
        end_ev = events(rows, "quan_end")[0]["data"]
        self.assertEqual(end_ev["reason"], "time")
        self.assertEqual(end_ev["earned"], dish["price"] + tip)
        self.assertAlmostEqual(end_ev["reputation"], q["reputation_initial"] + q["tip_reputation"])

        end = rows[-1]
        self.assertEqual(end["type"], "end")
        self.assertEqual(end["score"], end["earned"] + 100 * math.floor(end["reputation"]))
        used = dish["recipe"]
        left = {k: n - used.get(k, 0) for k, n in INVENTORY.items() if n - used.get(k, 0) > 0}
        self.assertEqual(snapshots(rows)[-1]["stock"], left)  # nguyên liệu đã dùng cho món

    def test_dock_checked_before_harvest(self):
        # Nút đặt ngay tại bến: interact phải cập bến (gather_end docked), không hái
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [2, 0]}]}})
            inp = write_json(w.path("in.json"), {"frames": [{"tick": 0, "interact": True}]})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc,
                                     "--inputs", inp, "--inventory-out", inv, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})
        self.assertEqual([e["name"] for e in events(rows)], ["gather_end"])
        self.assertEqual(rows[-1]["reason"], "docked")

    def test_gather_and_quan_deterministic_bytes(self):
        with Workdir() as w:
            inv = self._gather_inventory(w, "g1.jsonl")
            self._gather_inventory(w, "g2.jsonl")
            self._run_quan(w, inv, "q1.jsonl")
            self._run_quan(w, inv, "q2.jsonl")
            for a_name, b_name in (("g1.jsonl", "g2.jsonl"), ("q1.jsonl", "q2.jsonl")):
                with open(w.path(a_name), "rb") as a, open(w.path(b_name), "rb") as b:
                    self.assertEqual(a.read(), b.read(), a_name)


if __name__ == "__main__":
    unittest.main()
