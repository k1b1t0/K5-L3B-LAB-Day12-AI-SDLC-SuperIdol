"""Test cho Lát 4 quan: bếp nấu, chín, bưng món, phục vụ, tính tiền, boa, tăng uy tín."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


class TestQuanSlice4(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_full_service_cycle(self):
        """Khách chờ -> nấu tại bếp B1 -> chín -> bưng -> giao bàn T1 -> ăn -> trả tiền + tip."""
        # B1 ở [2, 8], T1 ở [9, 2]
        sc = {
            "player": {"pos": [2.0, 8.0]},  # đứng sát bếp B1
            "stock": {"ca_loc": 2},
            "customers": [{
                "id": "C1",
                "table_id": "T1",
                "dish_id": "ca_loc_nuong_trui",
                "state": "waiting",
                "patience_ticks_left": 3600,
                "patience_max_ticks": 3600,
                "reserved": {"ca_loc": 1}
            }],
            "random_customers": False
        }
        s = Session("quan", self.tuning, sc, seed=1)

        # 1. Bấm interact tại bếp -> bắt đầu nấu
        evs = s.step(InputState((0.0, 0.0), {}, {"interact"}))
        self.assertIn("cook_started", [r["name"] for r in evs])
        stove = s.sim.stoves[0]
        self.assertEqual(stove["state"], "cooking")
        self.assertEqual(stove["dish"], "ca_loc_nuong_trui")

        # 2. Chờ 6 giây (360 tick) để món chín
        cook_ticks = stove["cook_ticks_left"]
        ready_evs = []
        for _ in range(cook_ticks):
            ready_evs.extend(s.step(InputState((0.0, 0.0), {}, set())))
        self.assertIn("dish_ready", [r["name"] for r in ready_evs])
        self.assertEqual(stove["state"], "ready")

        # 3. Bấm interact tại bếp -> bưng món lên tay
        evs_pick = s.step(InputState((0.0, 0.0), {}, {"interact"}))
        self.assertIn("dish_picked", [r["name"] for r in evs_pick])
        self.assertEqual(s.sim.hand, "ca_loc_nuong_trui")
        self.assertEqual(stove["state"], "idle")

        # 4. Di chuyển lại bàn T1 [9, 2] và giao món
        s.sim.pos = [9.0, 2.0]
        evs_serve = s.step(InputState((0.0, 0.0), {}, {"interact"}))
        self.assertIn("served", [r["name"] for r in evs_serve])
        self.assertIsNone(s.sim.hand)
        cust = s.sim.customers[0]
        self.assertEqual(cust["state"], "eating")
        self.assertGreater(cust["tip"], 0)

        # 5. Chờ ăn xong (10s = 600 tick) -> trả tiền và tăng uy tín
        eat_ticks = cust["eat_ticks_left"]
        paid_evs = []
        for _ in range(eat_ticks):
            paid_evs.extend(s.step(InputState((0.0, 0.0), {}, set())))
        self.assertIn("paid", [r["name"] for r in paid_evs])
        self.assertEqual(len(s.sim.customers), 0)
        self.assertGreater(s.sim.money, 60)
        self.assertGreater(s.sim.reputation, self.tuning["quan"]["reputation_initial"])


if __name__ == "__main__":
    unittest.main()
