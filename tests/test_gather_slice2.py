"""Test cho Lát 2 gather: hái nút, bắt cá, cooldown, hold capacity, hold_full."""

import unittest

from chonoi.contract import load_contract
from chonoi.runner import Session
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestGatherSlice2(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_gather_node_and_regrow(self):
        """Hái nút khi ở mặt nước trong interact_radius -> nhận nguyên liệu vào hold, nút đếm lùi regrow."""
        sc = {
            "player": {"pos": [12.0, 0.0]},  # N1 ở [12, 0] là bong_dien_dien
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12.0, 0.0], "regrow_ticks": 0}]
        }
        s = Session("gather", self.tuning, sc, seed=1)
        from chonoi.inputs import InputState
        inp = InputState((0.0, 0.0), {}, {"interact"})
        evs = s.step(inp)
        names = [r["name"] for r in evs]
        self.assertIn("gather", names)
        self.assertEqual(s.sim.hold, ["bong_dien_dien"])
        self.assertGreater(s.sim.nodes[0]["regrow_ticks"], 0)

    def test_gather_hold_full(self):
        """Giỏ đầy không hái được, phát hold_full và nút không mất."""
        cap = self.tuning["gather"]["hold_capacity"]
        sc = {
            "player": {"pos": [12.0, 0.0]},
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12.0, 0.0], "regrow_ticks": 0}],
            "hold": ["ca_loc"] * cap
        }
        s = Session("gather", self.tuning, sc, seed=1)
        from chonoi.inputs import InputState
        inp = InputState((0.0, 0.0), {}, {"interact"})
        evs = s.step(inp)
        names = [r["name"] for r in evs]
        self.assertIn("hold_full", names)
        self.assertEqual(len(s.sim.hold), cap)
        self.assertEqual(s.sim.nodes[0]["regrow_ticks"], 0)

    def test_catch_fish_and_cooldown(self):
        """Bắt cá dưới nước trong catch_radius -> nhận cá vào hold, cá bị xoá khỏi fish, kích hoạt cooldown."""
        sc = {
            "player": {"pos": [15.0, 5.0]},  # F1 ở [15, 5] là ca_linh
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0], "heading_deg": 0}]
        }
        s = Session("gather", self.tuning, sc, seed=1)
        from chonoi.inputs import InputState
        inp = InputState((0.0, 0.0), {}, {"catch"})
        evs = s.step(inp)
        names = [r["name"] for r in evs]
        self.assertIn("fish_caught", names)
        # ca_linh yield 3
        self.assertEqual(s.sim.hold, ["ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(len(s.sim.fish), 0)
        self.assertGreater(s.sim.catch_cd_ticks, 0)


if __name__ == "__main__":
    unittest.main()
