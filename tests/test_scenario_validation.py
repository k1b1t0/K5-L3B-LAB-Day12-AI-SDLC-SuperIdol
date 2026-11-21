"""Kiểm đầu vào sai -> mã 2, không để lại file --out (scenario quán) và BadInput (tuning quán/menu)."""

import copy
import os
import unittest

from helpers import Workdir, run_headless, write_json

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput

DISH = "ca_loc_nuong_trui"  # cook_s = 6 -> 360 tick

BAD_QUAN = {
    "random_customers không phải bool": {"random_customers": 1},
    "reputation ngoài dải": {"reputation": 99},
    "reputation không phải số": {"reputation": "3"},
    "bếp state lạ": {"stoves": [{"id": "B1", "state": "burning"}]},
    "bếp idle mà có món": {"stoves": [{"id": "B1", "state": "idle", "dish": DISH}]},
    "bếp idle mà còn bộ đếm": {"stoves": [{"id": "B1", "state": "idle", "cook_ticks_left": 5}]},
    "bếp cooking không có món": {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 10}]},
    "bếp cooking món lạ": {"stoves": [{"id": "B1", "state": "cooking", "dish": "pho", "cook_ticks_left": 10}]},
    "bếp cooking hết bộ đếm": {"stoves": [{"id": "B1", "state": "cooking", "dish": DISH, "cook_ticks_left": 0}]},
    "bếp cooking quá cook_s": {"stoves": [{"id": "B1", "state": "cooking", "dish": DISH, "cook_ticks_left": 361}]},
    "bếp ready còn cook_ticks": {"stoves": [{"id": "B1", "state": "ready", "dish": DISH, "cook_ticks_left": 3}]},
    "bếp ready_ticks âm": {"stoves": [{"id": "B1", "state": "ready", "dish": DISH, "ready_ticks": -1}]},
    "khách state lạ": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "angry"}]},
    "khách thiếu dish_id": {"customers": [{"id": "C1", "table_id": "T1"}]},
    "khách món lạ": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "pho"}]},
    "khách chờ hết kiên nhẫn": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                               "patience_ticks_left": 0}]},
    "khách chờ quá patience_s": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                                "patience_ticks_left": 3601}]},
    "khách ăn bộ đếm 0": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                         "eat_ticks_left": 0}]},
    "khách ăn quá eat_s": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "eating",
                                          "eat_ticks_left": 601}]},
    "reserved nguyên liệu lạ": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                               "reserved": {"thit_bo": 1}}]},
    "reserved số âm": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH,
                                      "reserved": {"ca_loc": -1}}]},
}

GOOD_QUAN = {
    "stock": {"ca_loc": 2},
    "reputation": 4.5,
    "random_customers": False,
    "stoves": [{"id": "B1", "state": "cooking", "dish": DISH, "cook_ticks_left": 360}],
    "customers": [{"id": "C1", "table_id": "T1", "dish_id": DISH, "state": "waiting",
                   "patience_ticks_left": 3600, "reserved": {"ca_loc": 1}}],
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
                                "eat_ticks_left": 600, "price": 60, "tip": 12}]}
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
