"""Phase 3 (TICKET-03, Contract v1.2): kho cá thể, độ tươi, ngưỡng ươn, giữ lại khi ươn, chốt giá, bàn giao.

Hộp đen qua headless; số đọc từ game.contract.json.
"""

import json
import math
import os
import unittest
from fractions import Fraction

from helpers import (ROOT, Workdir, assert_items_close, events, frames, inst, read_jsonl, run_headless, snapshots,
                     write_json)

DISH = "ca_loc_nuong_trui"  # công thức 1 cá lóc


def contract():
    with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
        return json.load(f)


def run(w, mode, ticks, scenario=None, inputs=None, *extra, name="o.jsonl"):
    args = ["--mode", mode, "--seed", "3", "--ticks", str(ticks), "--out", w.path(name), *extra]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc_" + name + ".json"), scenario)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in_" + name + ".json"), inputs)]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path(name)) if os.path.exists(w.path(name)) else None)


def threshold_fixture(fresh):
    return {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": fresh}], "random_fish": False,
                       "monsters": []}}


class ContractV12(unittest.TestCase):
    def test_version_and_freshness_tuning(self):
        c = contract()
        self.assertIn(c["contract_version"], ("1.2", "1.3"))  # v1.3 giữ nguyên gameplay/kho/JSONL của v1.2
        self.assertEqual(c["tuning"]["freshness"], {"initial": 100, "gather_decay_per_s": 0.5,
                                                    "quan_decay_per_s": 0.25, "spoiled_below": 30})


class Threshold(unittest.TestCase):
    def test_fresh_30_spoils_on_first_gather_step(self):
        with Workdir() as w:
            code, err, rows = run(w, "gather", 1, threshold_fixture(30))
            self.assertEqual(code, 0, err)
        sp = events(rows, "spoiled")
        self.assertEqual([(e["tick"], e["data"]) for e in sp],
                         [(1, {"item_id": "I1", "kind": "ca_linh", "location": "hold"})])
        hold = snapshots(rows)[-1]["hold"]
        assert_items_close(self, hold, [{"id": "I1", "kind": "ca_linh", "fresh": 30 - 1 / 120}])

    def test_spoiled_emitted_once_and_clamped_at_zero(self):
        with Workdir() as w:
            code, err, rows = run(w, "gather", 10, threshold_fixture(0.02), None, "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "spoiled"), [])  # đã < 30 từ đầu: không phát
        self.assertEqual(snapshots(rows)[-1]["hold"][0]["fresh"], 0)

    def test_threshold_branch_survives_file_round_trip(self):
        # 30 + 1/240 ghi ra file phải đọc lại đúng: quán hao 1/240/tick -> đúng 30 ở tick 1 (chưa ươn), ươn ở tick 2
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": [{"id": "I7", "kind": "ca_loc",
                                                             "fresh": float(30 + Fraction(1, 240))}]})
            code, err, rows = run(w, "quan", 3, None, None, "--inventory", inv)
            self.assertEqual(code, 0, err)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "spoiled")],
                         [(2, {"item_id": "I7", "kind": "ca_loc", "location": "stock"})])

    def test_pause_stops_decay(self):
        inp = frames({"tick": 0, "pause": True}, {"tick": 1, "pause": False})
        with Workdir() as w:
            code, err, rows = run(w, "gather", 50, threshold_fixture(100), inp, "--snapshot-every", "10")
            self.assertEqual(code, 0, err)
        last = snapshots(rows)[-1]
        self.assertEqual((last["state"], last["sim_tick"]), ("paused", 0))
        self.assertEqual(last["hold"][0]["fresh"], 100)


class FileHandoff(unittest.TestCase):
    def test_smoke_gather_file_to_quan(self):
        """Smoke của TICKET-03: mẫu ngưỡng với fresh 100, cập bến ở frame 0, quan --inventory --ticks 0."""
        with Workdir() as w:
            inv = w.path("inv.json")
            code, err, _ = run(w, "gather", 5, threshold_fixture(100), frames({"tick": 0, "interact": True}),
                               "--inventory-out", inv, name="g.jsonl")
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(list(saved), ["items"])
            self.assertEqual(saved["items"], [{"id": "I1", "kind": "ca_linh", "fresh": float(100 - Fraction(1, 120))}])
            code, err, rows = run(w, "quan", 0, None, None, "--inventory", inv, name="q.jsonl")
            self.assertEqual(code, 0, err)
        assert_items_close(self, snapshots(rows)[0]["stock"], saved["items"])

    def test_count_format_and_bad_instances_exit_2(self):
        bad = [{"items": {"ca_loc": 1}},
               {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 101}]},
               {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 1}, {"id": "I1", "kind": "ca_loc", "fresh": 2}]},
               {"items": [{"id": "I1", "kind": "thit_bo", "fresh": 50}]}]
        with Workdir() as w:
            for b in bad:
                inv = write_json(w.path("inv.json"), b)
                code, _, rows = run(w, "quan", 1, None, None, "--inventory", inv)
                self.assertEqual(code, 2, b)
                self.assertIsNone(rows)

    def test_spoiled_items_handed_over_and_kept(self):
        # Kho quán nhận nguyên hàng ươn; hàng ươn vẫn trong stock, không dùng nấu
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 10}]})
            code, err, rows = run(w, "quan", 0, None, None, "--inventory", inv)
            self.assertEqual(code, 0, err)
        self.assertEqual(snapshots(rows)[0]["stock"], [{"id": "I1", "kind": "ca_loc", "fresh": 10}])


class ReserveAndPrice(unittest.TestCase):
    def _quan(self, stock, **extra):
        q = {"stock": stock, "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "reserved": ["I1"]}]}
        q.update(extra)
        return {"quan": q}

    def test_reserved_item_spoils_then_rereserved_freshest(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "ca_loc", "fresh": 60},
                 {"id": "I3", "kind": "ca_loc", "fresh": 80}]
        with Workdir() as w:
            code, err, rows = run(w, "quan", 1, self._quan(stock), None, "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
        self.assertEqual([(e["tick"], e["data"]["item_id"]) for e in events(rows, "spoiled")], [(1, "I1")])
        s0, s1 = snapshots(rows)[0], snapshots(rows)[-1]
        self.assertEqual(s0["customers"][0]["reserved"], ["I1"])
        c = s1["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I3"]))  # tươi nhất
        self.assertEqual(len(s1["stock"]), 3)  # hàng ươn vẫn chiếm ô

    def test_reserved_item_spoils_no_replacement_unfulfillable(self):
        with Workdir() as w:
            code, err, rows = run(w, "quan", 1, self._quan([{"id": "I1", "kind": "ca_loc", "fresh": 30}]))
            self.assertEqual(code, 0, err)
        c = snapshots(rows)[-1]["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("unfulfillable", []))

    def test_price_fixed_from_freshness_at_cook(self):
        t = contract()["tuning"]
        price = t["menu"][DISH]["price"]
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 50}]
        sc = self._quan(stock, player={"pos": [2, 8]})
        with Workdir() as w:
            code, err, rows = run(w, "quan", 60, sc, frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}),
                                  "--snapshot-every", "30")
            self.assertEqual(code, 0, err)
        cook = events(rows, "cook_started")[0]
        fresh = 50 - Fraction(cook["tick"], 240)  # hao quán 0.25/s trước tương tác cùng bước
        base = math.floor(Fraction(price) * fresh / 100)
        self.assertLess(base, price)
        self.assertEqual(cook["data"]["base_price"], base)
        self.assertEqual([(i["id"], i["kind"]) for i in cook["data"]["items"]], [("I1", "ca_loc")])
        stove = [s for s in snapshots(rows)[-1]["stoves"] if s["id"] == "B1"][0]
        self.assertEqual(stove["dish"]["base_price"], base)  # món chín không hao, giá đã chốt
        self.assertEqual(snapshots(rows)[-1]["stock"], [])

    def test_auto_reserve_skips_spoiled(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 29}, {"id": "I2", "kind": "ca_loc", "fresh": 40}]
        sc = {"quan": {"stock": stock, "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH}]}}
        with Workdir() as w:
            code, err, rows = run(w, "quan", 0, sc)
            self.assertEqual(code, 0, err)
        self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], ["I2"])


class DayIds(unittest.TestCase):
    def test_day1_keeps_template_ids_next_day_new_ids_and_handoff_same_tick(self):
        sc = {"gather": {"hold": inst(["ca_loc", "bong_sung"])}, "quan": {"time_left_ticks": 1}}
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": 2, "shop_done": True})
        with Workdir() as w:
            code, err, rows = run(w, "day", 4, sc, inp, "--days", "2", "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
        snaps = snapshots(rows)
        d1 = snaps[0]
        self.assertEqual([i["id"] for i in d1["hold"]], ["I1", "I2"])
        q = [s for s in snaps if s["phase"] == "quan"][0]
        # bàn giao trong cùng tick chuyển pha: không hao thêm (chỉ một bước gather)
        assert_items_close(self, q["stock"], inst(["ca_loc", "bong_sung"], fresh=100 - 1 / 120))
        d2 = [s for s in snaps if s["day"] == 2 and s["phase"] == "gather"][0]
        ids2 = [i["id"] for i in d2["hold"]]
        self.assertEqual([(i["kind"], i["fresh"]) for i in d2["hold"]], [("ca_loc", 100), ("bong_sung", 100)])
        self.assertFalse(set(ids2) & {"I1", "I2"})
        self.assertEqual(len(set(ids2)), 2)


if __name__ == "__main__":
    unittest.main()
