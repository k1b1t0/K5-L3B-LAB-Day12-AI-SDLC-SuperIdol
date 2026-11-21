"""Phase 4 (TICKET-04, Contract v1.3): khai bench_cmd/soak_cmd, công thức số đo bench, soak tất định.

Bench thật cần Chrome/Chromium nên chạy tay (docs/proof/phase-4/bench.log); ở đây chỉ kiểm công thức.
"""

import json
import os
import subprocess
import sys
import unittest

from helpers import ROOT, Workdir

from chonoi.bench import metrics


def contract():
    with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
        return json.load(f)


def run_mod(mod, *args):
    p = subprocess.run([sys.executable, "-m", mod, *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"), timeout=600)
    return p.returncode, p.stderr


class ContractV13(unittest.TestCase):
    def test_version_and_commands_at_root(self):
        c = contract()
        self.assertEqual(c["contract_version"], "1.3")
        self.assertEqual((c["bench_cmd"], c["soak_cmd"]), ("python3 -m chonoi.bench", "python3 -m chonoi.soak"))


class BenchMetrics(unittest.TestCase):
    def test_formula(self):
        # 200 khung trong 4 s -> avg 50; k = ceil(1% × 200) = 2 khung chậm nhất 0.05 s, 0.03 s -> 1 / 0.04 = 25
        m = metrics(200, 4.0, [0.03, 0.05, 0.02], 2500.4, 1000.0)
        self.assertEqual(m, {"avg_fps": 50.0, "p1_low_fps": 25.0, "frames": 200, "measured_s": 4.0, "load_ms": 1500})

    def test_k_at_least_one(self):
        self.assertEqual(metrics(10, 1.0, [0.5], 0, 0)["p1_low_fps"], 2.0)

    def test_bad_measurements_rejected(self):
        for args in ((0, 1.0, [0.1]), (100, 1.0, []), (100, 0, [0.1])):
            with self.assertRaises(ValueError):
                metrics(*args, 0, 0)

    def test_bad_args_exit_2(self):
        for args in ([], ["--seed", "1", "--duration", "0", "--out", "x.json"],
                     ["--seed", "x", "--duration", "5", "--out", "x.json"]):
            self.assertEqual(run_mod("chonoi.bench", *args)[0], 2, args)

    def test_missing_browser_fails_cleanly_without_output(self):
        with Workdir() as w:
            out = w.path("bench.json")
            p = subprocess.run([sys.executable, "-m", "chonoi.bench", "--seed", "42",
                                "--duration", "1", "--out", out], cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8", timeout=30,
                               env=dict(os.environ, PYTHONUTF8="1", CHONOI_BROWSER=w.path("missing-browser.exe")))
            self.assertEqual(p.returncode, 1)
            self.assertNotIn("Traceback", p.stderr)
            self.assertFalse(os.path.exists(out))


class Soak(unittest.TestCase):
    def _soak(self, w, name, days="2"):
        out = w.path(name)
        code, err = run_mod("chonoi.soak", "--seed", "7", "--days", days, "--out", out)
        self.assertEqual(code, 0, err)
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def test_days_complete_no_crash_and_deterministic(self):
        with Workdir() as w:
            a, b = self._soak(w, "a.json"), self._soak(w, "b.json")
        self.assertEqual(set(a), {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertEqual((a["days"], a["days_completed"], a["crashes"]), (2, 2, 0))
        self.assertEqual([r["day"] for r in a["results"]], [1, 2])
        self.assertEqual(set(a["results"][0]), {"day", "earned", "reputation", "score"})
        a.pop("duration_s"), b.pop("duration_s")  # bỏ số đo thời gian thực khi so
        self.assertEqual(a, b)

    def test_beyond_five_days_repeats_plan(self):
        with Workdir() as w:
            s = self._soak(w, "s.json", days="6")
        self.assertEqual((s["days_completed"], s["crashes"], len(s["results"])), (6, 0, 6))

    def test_bad_args_exit_2(self):
        for args in ([], ["--seed", "7", "--days", "0", "--out", "x.json"]):
            self.assertEqual(run_mod("chonoi.soak", *args)[0], 2, args)


if __name__ == "__main__":
    unittest.main()
