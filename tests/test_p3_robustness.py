"""Phase 3 — chống crash: quét đầu vào hỏng ở cả scenario, inputs, file kho cho cả hai mode.

Mọi ca phải: mã 2, không ghi --out / --inventory-out, stderr không có Traceback (tức không phải mã 1 do crash).
Chạy bình thường thì mọi dòng JSONL phải là JSON chuẩn (không NaN/Infinity).
"""

import json
import os
import unittest

from helpers import Workdir, read_jsonl, run_headless, write_json

DISH = "ca_loc_nuong_trui"

# (mode, scenario, inputs, inventory) — chuỗi = ghi nguyên văn (để có JSON hỏng / NaN)
CASES = {
    "scenario rỗng": ("gather", "", None, None),
    "scenario là mảng": ("quan", "[1]", None, None),
    "khối là chuỗi": ("gather", {"gather": "x"}, None, None),
    "gather player là mảng": ("gather", {"gather": {"player": []}}, None, None),
    "gather nút thiếu pos": ("gather", {"gather": {"nodes": [{"id": "N1", "kind": "bong_sung"}]}}, None, None),
    "gather cá thiếu kind": ("gather", {"gather": {"fish": [{"id": "F1", "pos": [5, 5]}]}}, None, None),
    "gather hold là chuỗi": ("gather", {"gather": {"hold": "ca_loc"}}, None, None),
    "gather pos NaN": ("gather", '{"gather": {"player": {"pos": [NaN, 1]}}}', None, None),
    "gather hp chuỗi": ("gather", {"gather": {"player": {"hp": "3"}}}, None, None),
    "quan customers là object": ("quan", {"quan": {"customers": {}}}, None, None),
    "quan id khách là số": ("quan", {"quan": {"customers": [{"id": 5, "table_id": "T1", "dish_id": DISH}]}}, None, None),
    "quan bếp lạ": ("quan", {"quan": {"stoves": [{"id": "B9", "state": "idle"}]}}, None, None),
    "quan bàn lạ": ("quan", {"quan": {"tables": [{"id": "T9", "pos": [1, 1]}]}}, None, None),
    "quan stock phần tử là số": ("quan", {"quan": {"stock": [1]}}, None, None),
    "quan reserved phần tử là số": ("quan", {"quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                                                      "reserved": [1]}]}}, None, None),
    "quan pos là chuỗi": ("quan", {"quan": {"player": {"pos": "a"}}}, None, None),
    "quan reputation NaN": ("quan", '{"quan": {"reputation": NaN}}', None, None),
    "inputs rỗng": ("gather", None, "", None),
    "inputs là mảng": ("gather", None, [], None),
    "frames là object": ("quan", None, {"frames": {}}, None),
    "tick giảm dần": ("gather", None, {"frames": [{"tick": 5}, {"tick": 2}]}, None),
    "tick là số thực": ("gather", None, {"frames": [{"tick": 1.5}]}, None),
    "move 3 phần tử": ("quan", None, {"frames": [{"tick": 0, "move": [1, 0, 0]}]}, None),
    "move Infinity": ("gather", None, '{"frames": [{"tick": 0, "move": [Infinity, 0]}]}', None),
    "interact là số": ("quan", None, {"frames": [{"tick": 0, "interact": 1}]}, None),
    "nút của phase sau": ("gather", None, {"frames": [{"tick": 0, "jump": True}]}, None),
    "kho rỗng": ("quan", None, None, ""),
    "kho thiếu items": ("quan", None, None, {}),
    # v1.2: kho cá thể — kho đếm cũ, fresh ngoài miền, id trùng/rỗng, kind lạ đều mã 2
    "kho đếm v1.1": ("quan", None, None, {"items": {"ca_loc": 1}}),
    "kho fresh âm": ("quan", None, None, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -1}]}),
    "kho fresh > 100": ("quan", None, None, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.5}]}),
    "kho fresh NaN": ("quan", None, None, '{"items": [{"id": "I1", "kind": "ca_loc", "fresh": NaN}]}'),
    "kho fresh bool": ("quan", None, None, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": True}]}),
    "kho fresh chuỗi": ("quan", None, None, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": "100"}]}),
    "kho nguyên liệu lạ": ("quan", None, None, {"items": [{"id": "I1", "kind": "thit_bo", "fresh": 100}]}),
    "kho id trùng": ("quan", None, None, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100},
                                                    {"id": "I1", "kind": "ca_loc", "fresh": 90}]}),
    "kho id rỗng": ("quan", None, None, {"items": [{"id": "", "kind": "ca_loc", "fresh": 100}]}),
    "kho id là số": ("quan", None, None, {"items": [{"id": 1, "kind": "ca_loc", "fresh": 100}]}),
    "kho thiếu fresh": ("quan", None, None, {"items": [{"id": "I1", "kind": "ca_loc"}]}),
    "kho trường thừa": ("quan", None, None, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 1, "x": 0}]}),
    "gather hold kiểu v1.1": ("gather", {"gather": {"hold": ["ca_loc"]}}, None, None),
    "gather hold fresh Infinity": ("gather", '{"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": Infinity}]}}',
                                   None, None),
    "quan reserved id không có trong stock": ("quan", {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                                                                "customers": [{"id": "C1", "table_id": "T1",
                                                                               "dish_id": DISH, "reserved": ["I9"]}]}},
                                              None, None),
    "quan reserved hàng ươn": ("quan", {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 29.99}],
                                                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                                                "reserved": ["I1"]}]}}, None, None),
    # v1.1 (Phase 2): trường mới
    "day khối day là mảng": ("day", {"day": []}, None, None),
    "day upgrades là mảng": ("day", {"day": {"upgrades": [1]}}, None, None),
    "day money NaN": ("day", '{"day": {"money": NaN, "earned": 1}}', None, None),
    "day day_plan phần tử là số": ("day", {"day": {"day_plan": [1]}}, None, None),
    "day day_plan dishes là mảng": ("day", {"day": {"day_plan": [{"day": 1, "dishes": []}]}}, None, None),
    "gather monsters là object": ("gather", {"gather": {"monsters": {}}}, None, None),
    "gather monster waypoints chuỗi": ("gather", {"gather": {"monsters": [{"id": "M1", "kind": "ca_sau",
                                                                        "pos": [60, 24], "waypoints": "x"}]}},
                                       None, None),
    "gather monster recoil_dir NaN": ("gather", '{"gather": {"monsters": [{"id": "M1", "kind": "ca_sau", '
                                                '"pos": [60, 24], "waypoints": [[60, 24], [64, 24]], '
                                                '"state": "recoil", "state_ticks_left": 3, "recoil_dir": [NaN, 0]}]}}',
                                      None, None),
    "gather random_fish chuỗi": ("gather", {"gather": {"random_fish": "no"}}, None, None),
    "quan món ở tay là số": ("quan", {"quan": {"hand": 5}}, None, None),
    "quan dish base_price chuỗi": ("quan", {"quan": {"hand": {"order_id": "C1", "dish_id": DISH,
                                                              "base_price": "60"}}}, None, None),
    "buy là số": ("day", None, {"frames": [{"tick": 0, "buy": 1}]}, None),
    "buy rỗng": ("day", None, {"frames": [{"tick": 0, "buy": ""}]}, None),
    "pause là chuỗi": ("gather", None, {"frames": [{"tick": 0, "pause": "yes"}]}, None),
}


def _strict(line):
    def no_const(name):
        raise ValueError(f"hằng số không chuẩn JSON: {name}")
    return json.loads(line, parse_constant=no_const)


class Phase3Robustness(unittest.TestCase):
    def _write(self, w, name, obj):
        if isinstance(obj, str):
            with open(w.path(name), "w", encoding="utf-8") as f:
                f.write(obj)
            return w.path(name)
        return write_json(w.path(name), obj)

    def test_malformed_inputs_exit_2_no_crash(self):
        for label, (mode, sc, inp, inv) in CASES.items():
            with self.subTest(label), Workdir() as w:
                out = w.path("o.jsonl")
                args = ["--mode", mode, "--seed", "1", "--ticks", "30", "--out", out]
                for flag, obj, name in (("--scenario", sc, "sc.json"), ("--inputs", inp, "in.json"),
                                        ("--inventory", inv, "inv.json")):
                    if obj is not None:
                        args += [flag, self._write(w, name, obj)]
                if mode == "gather":
                    args += ["--inventory-out", w.path("kho.json")]
                code, err = run_headless(*args)
                self.assertEqual(code, 2, err)
                self.assertNotIn("Traceback", err)
                self.assertFalse(os.path.exists(out))
                self.assertFalse(os.path.exists(w.path("kho.json")))

    def test_outputs_are_strict_json(self):
        frames = {"frames": [{"tick": 0, "move": [1, 1]}, {"tick": 200, "catch": True}, {"tick": 201, "catch": False},
                             {"tick": 300, "move": [-1, -1]}, {"tick": 500, "interact": True}]}
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames)
            for mode in ("gather", "quan", "day"):
                out = w.path(f"{mode}.jsonl")
                code, err = run_headless("--mode", mode, "--seed", "7", "--ticks", "900", "--inputs", inp, "--out", out)
                self.assertEqual(code, 0, err)
                with open(out, encoding="utf-8") as f:
                    for line in f:
                        _strict(line)
                self.assertTrue(read_jsonl(out))


if __name__ == "__main__":
    unittest.main()
