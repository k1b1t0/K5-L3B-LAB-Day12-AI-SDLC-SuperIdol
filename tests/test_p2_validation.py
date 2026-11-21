"""Phase 2 — siết kiểm đầu vào: các lỗ hổng tìm ra khi thử phá headless (trước đây chạy mã 0).

Mỗi ca sai phải thoát mã 2 và không để lại --out.
"""

import os
import unittest

from helpers import Workdir, run_headless, write_json

DISH = "ca_loc_nuong_trui"
WAITING = {"id": "C1", "table_id": "T1", "dish_id": DISH}
ITEM1 = [{"id": "I1", "kind": "ca_loc", "fresh": 100}]  # v1.2: kho cá thể

# Ghi file .json dạng chuỗi để đưa được NaN / Infinity (json.load của Python chấp nhận chúng).
BAD_RAW = {
    "gather vel Infinity": ("gather", '{"gather": {"player": {"vel": [Infinity, 1]}}}'),
    "gather heading NaN": ("gather", '{"gather": {"player": {"heading_deg": NaN}}}'),
    "gather fish heading Infinity": ("gather", '{"gather": {"fish": [{"id": "F1", "kind": "ca_loc", "pos": [5, 5], '
                                                '"heading_deg": -Infinity}]}}'),
    "quan vel NaN": ("quan", '{"quan": {"player": {"vel": [NaN, 0]}}}'),
}

BAD = {
    "regrow_ticks quá regrow_s": ("gather", {"gather": {"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [5, 0],
                                                                    "regrow_ticks": 1201}]}}),
    "catch_cd_ticks quá hồi chiêu": ("gather", {"gather": {"player": {"catch_cd_ticks": 31}}}),
    "zero_oxy_ticks = choke_interval": ("gather", {"gather": {"player": {"pos": [10, 5], "oxygen_ticks": 0,
                                                                         "zero_oxy_ticks": 60}}}),
    "khách đang ăn còn giữ chỗ": ("quan", {"quan": {"stock": ITEM1, "customers": [dict(
        WAITING, state="eating", eat_ticks_left=10, base_price=60, tip=0, reserved=["I1"])]}}),
    "đơn đã giao bếp còn giữ chỗ": ("quan", {"quan": {
        "stock": ITEM1,
        "stoves": [{"id": "B1", "state": "cooking", "dish": {"order_id": "C1", "dish_id": DISH, "base_price": 60},
                    "cook_ticks_left": 10}],
        "customers": [dict(WAITING, order_status="assigned", reserved=["I1"])]}}),
}


class Phase2Validation(unittest.TestCase):
    def _run(self, mode, scenario, inventory=None):
        with Workdir() as w:
            sc = w.path("sc.json")
            if isinstance(scenario, str):
                with open(sc, "w", encoding="utf-8") as f:
                    f.write(scenario)
            else:
                write_json(sc, scenario)
            args = ["--mode", mode, "--seed", "1", "--ticks", "5", "--scenario", sc, "--out", w.path("o.jsonl")]
            if inventory is not None:
                args += ["--inventory", write_json(w.path("inv.json"), {"items": inventory})]
            code, err = run_headless(*args)
            return code, err, os.path.exists(w.path("o.jsonl"))

    def test_bad_exit_2_without_output(self):
        cases = dict(BAD)
        cases.update(BAD_RAW)
        for label, (mode, scenario) in cases.items():
            with self.subTest(label):
                code, err, wrote = self._run(mode, scenario)
                self.assertEqual(code, 2, err)
                self.assertFalse(wrote)

    def test_reserved_over_inventory_file_exit_2(self):
        sc = {"quan": {"customers": [dict(WAITING, reserved=["I2"])]}}  # v1.2: id không có trong file kho
        code, err, wrote = self._run("quan", sc, inventory=ITEM1)
        self.assertEqual(code, 2, err)
        self.assertFalse(wrote)

    def test_valid_edges_still_run(self):
        ok = {
            "regrow_ticks = regrow_s": ("gather", {"gather": {"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [5, 0],
                                                                         "regrow_ticks": 1200}]}}),
            "catch_cd_ticks = hồi chiêu": ("gather", {"gather": {"player": {"catch_cd_ticks": 30}}}),
            "zero_oxy_ticks = choke_interval - 1": ("gather", {"gather": {"player": {
                "pos": [10, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59}}}),
        }
        for label, (mode, scenario) in ok.items():
            with self.subTest(label):
                self.assertEqual(self._run(mode, scenario)[0], 0)
        sc = {"quan": {"customers": [dict(WAITING, reserved=["I1"])]}}
        self.assertEqual(self._run("quan", sc, inventory=ITEM1)[0], 0)


if __name__ == "__main__":
    unittest.main()
