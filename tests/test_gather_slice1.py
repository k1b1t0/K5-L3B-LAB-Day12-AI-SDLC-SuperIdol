"""Test cho Lát 1 gather: dive, surface, oxy, choke, faint."""

import unittest

from helpers import inst

from chonoi.contract import load_contract
from chonoi.runner import Session
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestGatherSlice1(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_dive_and_surface_events(self):
        """Bơi xuống vượt qua surface_depth phát dive, bơi lên phát surface."""
        sc = {"gather": {"player": {"pos": [10.0, 0.5]}}}  # surface_depth = 0.5
        s = Session("gather", self.tuning, sc["gather"], seed=1)
        # Bơi xuống: d dương
        from chonoi.inputs import InputState
        evs1 = s.step(InputState((0.0, 1.0), {}, set()))
        self.assertFalse(s.sim._at_surface())
        names1 = [name for name, _ in s.sim.step(InputState((0.0, 1.0), {}, set()))]
        # Bơi lên lại
        names2 = []
        for _ in range(30):
            names2.extend([name for name, _ in s.sim.step(InputState((0.0, -1.0), {}, set()))])
        self.assertIn("surface", names2)

    def test_oxygen_drain_and_empty(self):
        """Dưới nước oxy trừ 1/tick, về 0 phát oxygen_empty."""
        sc = {"gather": {"player": {"pos": [10.0, 5.0], "oxygen_ticks": 2}}}
        s = Session("gather", self.tuning, sc["gather"], seed=1)
        from chonoi.inputs import InputState
        inp = InputState((0.0, 0.0), {}, set())
        evs1 = s.step(inp)
        self.assertEqual(s.sim.oxygen_ticks, 1)
        evs2 = s.step(inp)
        self.assertEqual(s.sim.oxygen_ticks, 0)
        self.assertIn("oxygen_empty", [r["name"] for r in evs2])

    def test_choke_and_faint(self):
        """Hết oxy đủ choke_interval_ticks thì choke trừ HP, HP về 0 thì faint và giỏ rỗng."""
        choke_ticks = self.tuning["gather"]["choke_interval_ticks"]
        sc = {"gather": {
            "player": {"pos": [10.0, 5.0], "oxygen_ticks": 0, "zero_oxy_ticks": choke_ticks - 1, "hp": 1},
            "hold": inst(["ca_loc", "ca_linh"])
        }}
        s = Session("gather", self.tuning, sc["gather"], seed=1)
        from chonoi.inputs import InputState
        inp = InputState((0.0, 0.0), {}, set())
        evs = s.step(inp)
        names = [r["name"] for r in evs]
        self.assertIn("choke", names)
        self.assertIn("faint", names)
        self.assertIn("gather_end", names)
        self.assertTrue(s.done)
        self.assertEqual(s.sim.reason, "fainted")
        self.assertEqual(len(s.sim.hold), 0)


if __name__ == "__main__":
    unittest.main()
