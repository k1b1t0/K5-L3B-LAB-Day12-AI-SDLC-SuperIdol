"""Kiểm đầu vào sai -> mã 2, không để lại file --out (scenario quán) và BadInput (tuning quán/menu)."""

import copy
import os
import unittest

from helpers import Workdir, run_headless, write_json

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput

DISH = "ca_loc_nuong_trui"  # cook_s = 6 -> 360 tick

PAY = {"order_id": "C1", "dish_id": DISH, "base_price": 60}  # v1.1: món ở bếp/tay mang đơn
C1_ASSIGNED = {"id": "C1", "table_id": "T1", "dish_id": DISH, "order_status": "assigned"}


def _stove(**kw):
    return {"stoves": [dict({"id": "B1"}, **kw)], "customers": [C1_ASSIGNED]}


BAD_QUAN = {
    "random_customers không phải bool": {"random_customers": 1},
    "reputation ngoài dải": {"reputation": 99},
    "reputation không phải số": {"reputation": "3"},
    "bếp state lạ": {"stoves": [{"id": "B1", "state": "burning"}]},
    "bếp id không tồn tại": {"stoves": [{"id": "B9", "state": "idle"}]},
    "bếp idle mà có món": _stove(state="idle", dish=PAY),
    "bếp idle mà còn bộ đếm": {"stoves": [{"id": "B1", "state": "idle", "cook_ticks_left": 5}]},
    "bếp cooking không có món": {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 10}]},
    "bếp cooking món lạ": _stove(state="cooking", dish=dict(PAY, dish_id="pho"), cook_ticks_left=10),
    "bếp món là chuỗi (schema v1.0)": _stove(state="cooking", dish=DISH, cook_ticks_left=10),
    "bếp món thiếu base_price": _stove(state="cooking", dish={"order_id": "C1", "dish_id": DISH},
                                        cook_ticks_left=10),
    "bếp cooking hết bộ đếm": _stove(state="cooking", dish=PAY, cook_ticks_left=0),
    "bếp cooking quá cook_s": _stove(state="cooking", dish=PAY, cook_ticks_left=361),
    "bếp ready còn cook_ticks": _stove(state="ready", dish=PAY, cook_ticks_left=3),
    "bếp ready_ticks âm": _stove(state="ready", dish=PAY, ready_ticks=-1),
    "bàn id không tồn tại": {"tables": [{"id": "T9"}]},
    "khách state lạ": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "angry"}]},
    "khách order_status lạ": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "order_status": "x"}]},
    "khách thiếu dish_id": {"customers": [{"id": "C1", "table_id": "T1"}]},
    "khách món lạ": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "pho"}]},
    "khách bàn không tồn tại": {"customers": [{"id": "C1", "table_id": "T9", "dish_id": DISH}]},
    "hai khách cùng bàn": {"stock": {"ca_loc": 2},
                           "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH},
                                         {"id": "C2", "table_id": "T1", "dish_id": DISH}]},
    "khách chờ hết kiên nhẫn": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                               "patience_ticks_left": 0}]},
    "khách chờ quá patience_s": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                                "patience_ticks_left": 3601}]},
    "khách ăn bộ đếm 0": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                         "eat_ticks_left": 0, "base_price": 60, "tip": 0}]},
    "khách ăn quá eat_s": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                          "eat_ticks_left": 601, "base_price": 60, "tip": 0}]},
    "khách ăn mà đơn reserved": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                                "order_status": "reserved", "eat_ticks_left": 100,
                                                "base_price": 60, "tip": 0}]},
    "khách chờ mà đơn served": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                               "order_status": "served"}]},
    "reserved nguyên liệu lạ": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                               "reserved": {"thit_bo": 1}}]},
    "reserved số âm": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                      "reserved": {"ca_loc": -1}}]},
    "reserved lệch công thức": {"stock": {"ca_loc": 2},
                                "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                               "reserved": {"ca_loc": 2}}]},
    "đơn unfulfillable vẫn giữ chỗ": {"stock": {"ca_loc": 1},
                                      "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                                     "order_status": "unfulfillable", "reserved": {"ca_loc": 1}}]},
    "hand món lạ": {"hand": dict(PAY, dish_id="pho"), "customers": [C1_ASSIGNED]},
    "hand là chuỗi (schema v1.0)": {"hand": DISH},
    "hand thiếu order_id": {"hand": {"dish_id": DISH, "base_price": 60}},
    "khách ăn thiếu base_price/tip": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                                     "eat_ticks_left": 100}]},
    "khách ăn thiếu eat_ticks_left": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                                     "state": "eating", "base_price": 60, "tip": 0}]},
    "khách ăn tip âm": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                       "eat_ticks_left": 100, "base_price": 60, "tip": -1}]},
    "khách trường v1.0 price": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                               "eat_ticks_left": 100, "price": 60, "tip": 0}]},
    "giữ chỗ vượt kho": {"stock": {"ca_loc": 1},
                         "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "reserved": {"ca_loc": 1}},
                                       {"id": "C2", "table_id": "T2", "dish_id": DISH, "reserved": {"ca_loc": 1}}]},
    "giữ chỗ khi kho rỗng": {"stock": {},
                             "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "reserved": {"ca_loc": 1}}]},
    "tự giữ chỗ khi kho thiếu": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH}]},
    "đơn assigned không có món": {"customers": [C1_ASSIGNED]},
    "món trỏ đơn không tồn tại": {"stoves": [{"id": "B1", "state": "ready", "dish": dict(PAY, order_id="C9")}]},
    "món ở bếp khác món khách gọi": _stove(state="cooking", dish=dict(PAY, dish_id="goi_bong_sung"),
                                           cook_ticks_left=10),
    "bếp và tay giữ cùng đơn": dict(_stove(state="ready", dish=PAY), hand=PAY),
    "khách đang ăn vẫn có món ở bếp": {
        "stoves": [{"id": "B1", "state": "ready", "dish": PAY}],
        "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating", "eat_ticks_left": 10,
                       "base_price": 60, "tip": 0}]},
}

GOOD_QUAN = {
    "stock": {"ca_loc": 2},
    "reputation": 4.5,
    "random_customers": False,
    "stoves": [{"id": "B1", "state": "cooking", "dish": dict(PAY, order_id="C2"), "cook_ticks_left": 360}],
    "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "waiting",
                   "patience_ticks_left": 3600, "reserved": {"ca_loc": 1}},
                  {"id": "C2", "table_id": "T2", "dish_id": DISH, "order_status": "assigned"}],
}


class ScenarioQuanExit2(unittest.TestCase):
    def _run(self, block):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": block})
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5", "--scenario", sc, "--out", out)
            return code, err, os.path.exists(out)

    def test_bad_blocks_exit_2_without_output(self):
        for label, block in BAD_QUAN.items():
            with self.subTest(label):
                code, err, wrote = self._run(block)
                self.assertEqual(code, 2, err)
                self.assertFalse(wrote, "không được ghi --out khi đầu vào sai")

    def test_valid_block_runs(self):
        code, err, wrote = self._run(GOOD_QUAN)
        self.assertEqual(code, 0, err)
        self.assertTrue(wrote)

    def test_eating_customer_valid(self):
        block = {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                "eat_ticks_left": 600, "base_price": 60, "tip": 12}]}
        self.assertEqual(self._run(block)[0], 0)

    def test_assigned_order_and_hand_valid(self):
        block = {"hand": PAY, "stock": {"ca_loc": 1},
                 "stoves": [{"id": "B1", "state": "ready", "dish": dict(PAY, order_id="C2"), "ready_ticks": 5}],
                 "customers": [dict(C1_ASSIGNED, reserved={}),
                               {"id": "C2", "table_id": "T2", "dish_id": DISH, "order_status": "assigned"},
                               {"id": "C3", "table_id": "T3", "dish_id": DISH, "order_status": "unfulfillable"}]}
        self.assertEqual(self._run(block)[0], 0)


class TuningQuan(unittest.TestCase):
    def setUp(self):
        self.t = load_contract()["tuning"]

    def _bad(self, mutate):
        t = copy.deepcopy(self.t)
        mutate(t)
        with self.assertRaises(BadInput):
            validate_tuning(t)

    def test_current_contract_is_valid(self):
        validate_tuning(copy.deepcopy(self.t))

    def test_bad_tuning_rejected(self):
        cases = {
            "start_pos ngoài biên": lambda t: t["quan"].update(start_pos=[99, 5]),
            "stoves rỗng": lambda t: t["quan"].update(stoves=[]),
            "tables rỗng": lambda t: t["quan"].update(tables=[]),
            "id bàn trùng": lambda t: t["quan"].update(tables=[{"id": "T1", "pos": [1, 1]},
                                                              {"id": "T1", "pos": [2, 2]}]),
            "bếp ngoài biên": lambda t: t["quan"].update(stoves=[{"id": "B1", "pos": [2, 50]}]),
            "carry_limit = 0": lambda t: t["quan"].update(carry_limit=0),
            "reputation_min >= max": lambda t: t["quan"].update(reputation_min=5, reputation_max=5),
            "reputation_initial ngoài dải": lambda t: t["quan"].update(reputation_initial=6),
            "menu rỗng": lambda t: t.update(menu={}),
            "recipe rỗng": lambda t: t["menu"][DISH].update(recipe={}),
            "recipe nguyên liệu lạ": lambda t: t["menu"][DISH].update(recipe={"thit_bo": 1}),
            "recipe số lượng 0": lambda t: t["menu"][DISH].update(recipe={"ca_loc": 0}),
        }
        for label, mutate in cases.items():
            with self.subTest(label):
                self._bad(mutate)


if __name__ == "__main__":
    unittest.main()
