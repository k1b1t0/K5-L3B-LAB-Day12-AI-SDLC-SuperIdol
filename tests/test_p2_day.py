"""Phase 2 (v1.1) hộp đen: cá bơi/sinh, Cá Sấu + Máu/ngất, pause, vòng Ngày, Shop, --days, cấm khối day.

Mỗi ca chạy qua headless_cmd (Test Contract), dữ liệu số đọc từ game.contract.json.
"""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)["tuning"]


def run(w, mode, ticks, scenario=None, inputs=None, *extra, name="o.jsonl"):
    args = ["--mode", mode, "--seed", "5", "--ticks", str(ticks), "--out", w.path(name), *extra]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc_" + name + ".json"), scenario)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in_" + name + ".json"), inputs)]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path(name)) if os.path.exists(w.path(name)) else None)


class FishAndMonsters(unittest.TestCase):
    def setUp(self):
        self.t = tuning()["gather"]

    def test_initial_fish_distinct_spawn_points_and_scheduled_spawn(self):
        with Workdir() as w:
            code, err, rows = run(w, "gather", self.t["fish_spawn_ticks"])
            self.assertEqual(code, 0, err)
        fish = snapshots(rows)[0]["fish"]
        self.assertEqual(len(fish), self.t["fish_initial"])
        self.assertEqual(len({tuple(f["pos"]) for f in fish}), len(fish), "8 đàn ở 8 điểm khác nhau")
        for f in fish:
            self.assertIn(f["pos"][0], self.t["fish_spawn_x"])
            self.assertIn(f["pos"][1], self.t["fish_spawn_depths"][f["kind"]])
        spawned = events(rows, "fish_spawned")
        self.assertEqual([e["tick"] for e in spawned], [self.t["fish_spawn_ticks"]])
        last = snapshots(rows)[-1]["fish"]
        self.assertEqual(len(last), self.t["fish_initial"] + 1)
        moved = {f["id"]: f["pos"] for f in last}
        self.assertTrue(any(moved[f["id"]] != f["pos"] for f in fish), "cá phải bơi")

    def test_random_fish_false_fixture_stands_still(self):
        sc = {"gather": {"random_fish": False, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, 10]}]}}
        with Workdir() as w:
            code, err, rows = run(w, "gather", 400, sc)
            self.assertEqual(code, 0, err)
        self.assertEqual(snapshots(rows)[-1]["fish"][0]["pos"], [30, 10])
        self.assertEqual(events(rows, "fish_spawned"), [])

    def _monster_sc(self, hp, hold):
        return {"gather": {"random_fish": False, "hold": hold,
                           "player": {"pos": [60, 20], "hp": hp},
                           "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [61, 20],
                                         "waypoints": [[61, 20], [64, 20]]}]}}

    def test_monster_hit_loses_half_hold_lifo_and_recoils(self):
        with Workdir() as w:
            code, err, rows = run(w, "gather", self.t["monsters"]["invuln_ticks"], self._monster_sc(3, ["ca_loc", "bong_sung", "ca_linh"]),
                                  None, "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
        hits = events(rows, "monster_hit")
        self.assertEqual(len(hits), 1, "bất tử 90 tick: không hit lần hai")
        self.assertEqual(hits[0]["tick"], 1)
        self.assertEqual(hits[0]["data"]["hp"], 2)
        self.assertEqual(hits[0]["data"]["lost"], ["ca_linh"])  # floor(3 × 0.5) = 1, nhặt sau mất trước
        s1 = [s for s in snapshots(rows) if s["tick"] == 1][0]
        self.assertEqual(s1["player"]["invuln_ticks"], self.t["monsters"]["invuln_ticks"])
        self.assertEqual(s1["monsters"][0]["state"], "recoil")
        self.assertEqual(s1["hold"], ["ca_loc", "bong_sung"])

    def test_monster_faint_ends_gather_same_tick(self):
        with Workdir() as w:
            code, err, rows = run(w, "gather", 10, self._monster_sc(1, ["ca_loc", "bong_sung"]))
            self.assertEqual(code, 0, err)
        names = [e["name"] for e in events(rows)]
        self.assertEqual(names, ["monster_hit", "faint", "gather_end"])
        faint = events(rows, "faint")[0]["data"]
        self.assertEqual(faint, {"cause": "monster", "lost": ["ca_loc"], "hp": 0})
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "fainted")
        self.assertEqual(rows[-1]["reason"], "fainted")


class Pause(unittest.TestCase):
    def test_pause_freezes_sim_and_resume_runs_same_step(self):
        inp = frames({"tick": 0, "pause": True}, {"tick": 1, "pause": False, "move": [1, 0]},
                     {"tick": 4, "pause": True})
        with Workdir() as w:
            code, err, rows = run(w, "gather", 6, None, inp, "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
        ev = [(e["tick"], e["name"]) for e in events(rows)]
        self.assertEqual(ev, [(1, "paused"), (5, "resumed")])
        snaps = {s["tick"]: s for s in snapshots(rows)}
        for k in (1, 2, 3, 4):
            self.assertEqual(snaps[k]["state"], "paused")
            self.assertEqual(snaps[k]["sim_tick"], 0)
            self.assertEqual(snaps[k]["player"]["pos"], [2, 0])
        self.assertEqual((snaps[5]["state"], snaps[5]["sim_tick"]), ("playing", 1))
        self.assertGreater(snaps[5]["player"]["pos"][0], 2)  # move vẫn giữ trong pause, chạy ngay bước resume
        self.assertEqual(rows[-1]["sim_tick"], 2)


class DayLoop(unittest.TestCase):
    def setUp(self):
        self.t = tuning()

    # Cập bến ngay tick 0 -> quán 1 tick -> Shop
    def _fast_day(self, day=None, shop_frames=(), days=1):
        sc = {"quan": {"time_left_ticks": 1}}
        if day is not None:
            sc["day"] = day
        fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, *shop_frames]
        return sc, frames(*fr), ("--days", str(days))

    def test_tick0_events_then_phase_transitions_same_tick(self):
        sc, inp, extra = self._fast_day(shop_frames=[{"tick": 2, "shop_done": True}])
        with Workdir() as w:
            code, err, rows = run(w, "day", 100, sc, inp, *extra)
            self.assertEqual(code, 0, err)
        d1 = self.t["day_plan"][0]
        self.assertEqual([r["type"] for r in rows[:4]], ["event", "event", "event", "snapshot"])
        self.assertEqual([(r["tick"], r["phase"], r["day"], r["name"]) for r in rows[:3]],
                         [(0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"), (0, "gather", 1, "phase_start")])
        self.assertEqual(rows[1]["data"], {"dishes": d1["dishes"], "ingredients": d1["ingredients"]})
        s0 = rows[3]
        self.assertEqual((s0["mode"], s0["phase"], s0["day"], s0["upgrades"], s0["active_upgrades"]),
                         ("day", "gather", 1, {}, {}))
        self.assertEqual(s0["day_plan"], {"dishes": d1["dishes"], "ingredients": d1["ingredients"]})
        ev = [(e["tick"], e["phase"], e["name"]) for e in events(rows)][3:]
        self.assertEqual(ev, [(1, "gather", "gather_end"), (1, "quan", "phase_start"),
                              (2, "quan", "quan_end"), (2, "shop", "phase_start"),
                              (3, "shop", "shop_end")])
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual((snaps[1]["phase"], snaps[1]["phase_tick"]), ("quan", 0))  # snapshot đổi pha
        self.assertEqual((snaps[2]["phase"], snaps[2]["phase_tick"]), ("shop", 0))
        self.assertEqual(snaps[2]["time_left_ticks"], self.t["shop"]["max_ticks"])
        end = rows[-1]
        self.assertEqual((end["reason"], end["days_completed"], end["ticks"]), ("days_complete", 1, 3))

    def test_shop_buy_then_upgrade_active_next_day(self):
        up = self.t["shop"]["upgrades"]
        price = up["oxygen"][0]["price"]
        day = {"money": price, "earned": price}
        shop = [{"tick": 2, "buy": "oxygen"}, {"tick": 3, "buy": "hp"}, {"tick": 4, "buy": "laser"},
                {"tick": 5, "shop_done": True}]
        sc, inp, extra = self._fast_day(day, shop, days=2)
        with Workdir() as w:
            code, err, rows = run(w, "day", 7, sc, inp, *extra, "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
        shop_ev = [(e["tick"], e["name"], e["data"]) for e in events(rows) if e["phase"] == "shop"][1:]
        self.assertEqual(shop_ev, [
            (3, "bought", {"upgrade": "oxygen", "level": 1, "price": price, "money": 0}),
            (4, "buy_failed", {"action": "hp", "reason": "funds"}),
            (5, "buy_failed", {"action": "laser", "reason": "unknown"}),
            (6, "shop_end", {"reason": "done"})])
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual((snaps[3]["upgrades"], snaps[3]["active_upgrades"]), ({"oxygen": 1}, {}))  # mua: hiện ngay
        day2 = snaps[6]
        self.assertEqual((day2["day"], day2["phase"], day2["phase_tick"]), (2, "gather", 0))
        self.assertEqual(day2["active_upgrades"], {"oxygen": 1})
        self.assertEqual(day2["player"]["oxygen_max_ticks"], int(round(up["oxygen"][0]["oxygen_max_s"] * 60)))
        self.assertEqual((day2["money"], day2["earned"]), (0, price))  # mua trừ money, giữ earned
        d2 = [e for e in events(rows) if e["tick"] == 6 and e["day"] == 2]
        self.assertEqual([e["name"] for e in d2], ["day_start", "day_plan", "phase_start"])
        self.assertEqual(d2[1]["data"]["dishes"], self.t["day_plan"][1]["dishes"])

    def test_buy_max_level_and_shop_timeout(self):
        sc, inp, extra = self._fast_day({"upgrades": {"oxygen": len(self.t["shop"]["upgrades"]["oxygen"])}},
                                        [{"tick": 2, "buy": "oxygen"}])
        with Workdir() as w:
            code, err, rows = run(w, "day", 5000, sc, inp, *extra)
            self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "buy_failed")[0]["data"], {"action": "oxygen", "reason": "max_level"})
        end_ev = events(rows, "shop_end")[0]
        self.assertEqual(end_ev["data"], {"reason": "time"})
        self.assertEqual(end_ev["tick"], 2 + self.t["shop"]["max_ticks"])

    def test_paused_shop_timer_frozen(self):
        sc, inp, extra = self._fast_day(shop_frames=[{"tick": 2, "pause": True}, {"tick": 3, "pause": False},
                                                     {"tick": 50, "pause": True}])
        with Workdir() as w:
            code, err, rows = run(w, "day", 5000, sc, inp, *extra)
            self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "shop_end")[0]["tick"], 2 + self.t["shop"]["max_ticks"] + 48)

    def test_scenario_hold_goes_to_quan_stock(self):
        sc = {"day": {"money": 200, "earned": 200},
              "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}
        with Workdir() as w:
            code, err, rows = run(w, "day", 2, sc, frames({"tick": 0, "interact": True}))
            self.assertEqual(code, 0, err)
        s1 = [s for s in snapshots(rows) if s["tick"] == 1][0]
        self.assertEqual((s1["phase"], s1["stock"], s1["money"]), ("quan", {"bong_sung": 2, "ca_loc": 1}, 200))


class DayCliAndScenarioExit2(unittest.TestCase):
    def _code(self, *args, scenario=None, inventory=None):
        with Workdir() as w:
            out = w.path("o.jsonl")
            a = ["--seed", "1", "--ticks", "5", "--out", out, *args]
            if scenario is not None:
                a += ["--scenario", write_json(w.path("sc.json"), scenario)]
            if inventory is not None:
                a += ["--inventory", write_json(w.path("inv.json"), inventory)]
            code, err = run_headless(*a)
            return code, err, os.path.exists(out)

    def test_days_flag_rules(self):
        for args in (("--mode", "day", "--days", "0"), ("--mode", "day", "--days", "6"),
                     ("--mode", "day", "--days", "x"), ("--mode", "gather", "--days", "1"),
                     ("--mode", "quan", "--days", "2")):
            with self.subTest(args):
                code, err, wrote = self._code(*args)
                self.assertEqual(code, 2, err)
                self.assertFalse(wrote)
        self.assertEqual(self._code("--mode", "day", "--days", "5")[0], 0)

    def test_day_rejects_file_inventory_flags(self):
        self.assertEqual(self._code("--mode", "day", inventory={"items": {}})[0], 2)
        self.assertEqual(self._code("--mode", "day", "--inventory-out", "x.json")[0], 2)

    def test_bad_day_scenarios(self):
        bad = {
            "quan.stock bị cấm": {"quan": {"stock": {"ca_loc": 1}}},
            "quan.reputation bị cấm": {"quan": {"reputation": 3}},
            "money > earned": {"day": {"money": 10, "earned": 5}},
            "money không kèm earned": {"day": {"money": 10}},
            "earned âm": {"day": {"earned": -1}},
            "uy tín ngoài dải": {"day": {"reputation": 9}},
            "nâng cấp lạ": {"day": {"upgrades": {"laser": 1}}},
            "cấp vượt tối đa": {"day": {"upgrades": {"oxygen": 3}}},
            "day_plan Ngày 6": {"day": {"day_plan": [{"day": 6, "dishes": {"goi_bong_sung": 1}}]}},
            "day_plan món lạ": {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}},
            "day_plan ingredients sai": {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1},
                                                               "ingredients": {"bong_sung": 1}}]}},
            "day_plan trùng Ngày": {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}},
                                                         {"day": 1, "dishes": {"goi_bong_sung": 2}}]}},
            "khối lạ": {"river": {}},
            "monster recoil thiếu dir": {"gather": {"monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24],
                                                                  "waypoints": [[60, 24], [64, 24]],
                                                                  "state": "recoil", "state_ticks_left": 5}]}},
            "monster target_idx 2": {"gather": {"monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24],
                                                              "waypoints": [[60, 24], [64, 24]], "target_idx": 2}]}},
            "invuln vượt tuning": {"gather": {"player": {"invuln_ticks": 91}}},
            "fish age âm": {"gather": {"fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, 10], "age_ticks": -1}]}},
        }
        for label, sc in bad.items():
            with self.subTest(label):
                code, err, wrote = self._code("--mode", "day", scenario=sc)
                self.assertEqual(code, 2, err)
                self.assertFalse(wrote)

    def test_good_day_scenario(self):
        sc = {"day": {"money": 100, "earned": 300, "reputation": 4, "upgrades": {"hp": 1},
                      "day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 2}}]}}
        self.assertEqual(self._code("--mode", "day", scenario=sc)[0], 0)


class QuanTwoStovesAndClosing(unittest.TestCase):
    def test_two_stoves_cook_in_parallel_and_closing_rules(self):
        t = tuning()
        q = t["quan"]
        sc = {"quan": {"random_customers": False, "player": {"pos": [3.5, 8]}, "time_left_ticks": 400,
                       "stock": {"ca_loc": 2},
                       "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
                                     {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui"},
                                     {"id": "C3", "table_id": "T3", "dish_id": "ca_loc_nuong_trui",
                                      "state": "eating", "eat_ticks_left": 600, "base_price": 60, "tip": 12}]}}
        # [3.5, 8] cách B1 [2,8] và B2 [5,8] đều 1.5 m -> hòa: bếp id nhỏ trước. Đứng giữa rồi bấm hai lần.
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                     {"tick": 2, "move": [1, 0]}, {"tick": 3, "move": [0, 0]},
                     {"tick": 10, "interact": True}, {"tick": 11, "interact": False})
        with Workdir() as w:
            code, err, rows = run(w, "quan", 500, sc, inp)
            self.assertEqual(code, 0, err)
        cooks = [(e["data"]["stove_id"], e["data"]["order_id"]) for e in events(rows, "cook_started")]
        self.assertEqual(cooks, [("B1", "C1"), ("B2", "C2")])
        self.assertEqual(len(events(rows, "dish_ready")), 2)
        closing = [(e["name"], e["data"]["order_id"], e["data"]["reason"]) for e in events(rows)
                   if e["tick"] == 400 and e["name"] in ("paid", "customer_left")]
        self.assertEqual(closing, [("customer_left", "C1", "closing"), ("customer_left", "C2", "closing"),
                                   ("paid", "C3", "closing")])
        end = events(rows, "quan_end")[0]["data"]
        self.assertEqual(end["earned"], 72)
        self.assertAlmostEqual(end["reputation"], q["reputation_initial"] + q["tip_reputation"])  # không trừ khi đóng
        snaps = snapshots(rows)
        self.assertTrue(all(s["stoves"][0]["dish"] is None for s in snaps[-1:]), "đóng ca dọn món của đơn")


if __name__ == "__main__":
    unittest.main()
