"""Test cho Lát 3 quan: khách đến theo lịch, chọn món nấu được, no_dish, kiên nhẫn, customer_left."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


class TestQuanSlice3(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_customer_arrives_and_reserves_stock(self):
        """Khách đến tại first_customer_tick (120) và giữ chỗ nguyên liệu."""
        sc = {
            "stock": {"ca_loc": 1, "bong_sung": 2},
            "random_customers": True
        }
        s = Session("quan", self.tuning, sc, seed=1)
        inp = InputState((0.0, 0.0), {}, set())
        for _ in range(119):
            s.step(inp)
        self.assertEqual(len(s.sim.customers), 0)
        evs = s.step(inp)  # tick 120
        self.assertIn("customer_arrived", [r["name"] for r in evs])
        self.assertEqual(len(s.sim.customers), 1)
        cust = s.sim.customers[0]
        self.assertEqual(cust["state"], "waiting")
        self.assertIn(cust["dish_id"], ["ca_loc_nuong_trui", "goi_bong_sung"])

    def test_no_dish_when_stock_empty(self):
        """Kho rỗng không có món nấu được -> phát no_dish, khách không ngồi."""
        sc = {
            "stock": {},
            "random_customers": True
        }
        s = Session("quan", self.tuning, sc, seed=1)
        inp = InputState((0.0, 0.0), {}, set())
        for _ in range(119):
            s.step(inp)
        evs = s.step(inp)  # tick 120
        names = [r["name"] for r in evs]
        self.assertIn("no_dish", names)
        self.assertEqual(len(s.sim.customers), 0)

    def test_customer_patience_and_leaves(self):
        """Khách hết kiên nhẫn thì bỏ đi (customer_left) và trừ uy tín."""
        sc = {
            "stock": {"ca_loc": 1},  # v1.1: đơn reserved phải giữ chỗ được trong kho thật
            "customers": [{
                "id": "C1",
                "table_id": "T1",
                "dish_id": "ca_loc_nuong_trui",
                "state": "waiting",
                "patience_ticks_left": 2
            }],
            "random_customers": False
        }
        s = Session("quan", self.tuning, sc, seed=1)
        inp = InputState((0.0, 0.0), {}, set())
        s.step(inp)  # ticks left -> 1
        self.assertEqual(len(s.sim.customers), 1)
        evs = s.step(inp)  # ticks left -> 0 -> leaves
        names = [r["name"] for r in evs]
        self.assertIn("customer_left", names)
        self.assertEqual(len(s.sim.customers), 0)
        self.assertLess(s.sim.reputation, self.tuning["quan"]["reputation_initial"])


if __name__ == "__main__":
    unittest.main()
