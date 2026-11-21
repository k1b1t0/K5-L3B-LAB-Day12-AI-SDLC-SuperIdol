"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import json
import math
import os
import shlex
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def inst(kinds, fresh=100, start=1):
    """Fixture v1.2: mảng loại -> mảng cá thể {id: I<start+n>, kind, fresh} theo thứ tự."""
    return [{"id": f"I{start + n}", "kind": k, "fresh": fresh} for n, k in enumerate(kinds)]


def assert_items_close(tc, got, want, tol=0.01):
    """So mảng cá thể: id/kind chính xác, fresh trong dung sai quan sát ±0.01 (TICKET-03)."""
    tc.assertEqual([(i["id"], i["kind"]) for i in got], [(i["id"], i["kind"]) for i in want])
    for a, b in zip(got, want):
        tc.assertLessEqual(abs(a["fresh"] - b["fresh"]), tol, (a, b))


def kinds(items):
    return [i["kind"] for i in items]


def counts(items):
    out = {}
    for i in items:
        out[i["kind"]] = out.get(i["kind"], 0) + 1
    return {k: out[k] for k in sorted(out)}


def frames(*fr):
    return {"frames": list(fr)}


def headless_cmd():
    """Lệnh headless khai trong game.contract.json — test chạy qua đây nên dùng được với MỌI ngôn ngữ."""
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["headless_cmd"])


def run_headless(*args, cwd=ROOT):
    """Chạy `<headless_cmd> <args>`; trả (mã thoát, stderr)."""
    p = subprocess.run([*headless_cmd(), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stderr


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def snapshots(rows):
    return [r for r in rows if r["type"] == "snapshot"]


def events(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


def close(a, b, tol=0.1):
    return abs(a - b) <= tol


def dist(p, q):
    return math.dist(p, q)


class Workdir:
    """Thư mục tạm tự dọn: with Workdir() as w: w.path('x.json')."""

    def __enter__(self):
        self._d = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, *a):
        self._d.cleanup()

    def path(self, name):
        return os.path.join(self._d.name, name)
