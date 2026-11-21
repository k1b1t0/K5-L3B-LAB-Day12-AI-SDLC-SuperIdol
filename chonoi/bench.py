"""Benchmark có render (Contract v1.3): python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng (gather) lõi với độ tươi, cá bơi, Cá Sấu và hiệu ứng mặc định; Út Sen đứng yên ở bến.
Chạy máy chủ `chonoi.live` trong tiến trình + Chrome/Chromium/Edge headless của máy (cửa sổ 1280×720) mở đúng
client web với `?bench`. Trang làm nóng 3 s từ khung đầu của cảnh, đo `--duration` s bằng requestAnimationFrame
rồi gửi số đo về `/bench`. Chỉ dùng thư viện chuẩn; đồng hồ thật chỉ dùng để đo, không đi vào luật.

Trình duyệt: biến môi trường CHONOI_BROWSER (đường dẫn) hoặc tự dò google-chrome/chromium/msedge.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

T0_EPOCH_MS = time.time() * 1000  # mốc "khởi chạy" cho load_ms

from .contract import load_contract  # noqa: E402
from .errors import BadInput  # noqa: E402
from .live import LiveGame, LiveServer  # noqa: E402

WINDOW = (1280, 720)
WARMUP_S = 3
# Giỏ mẫu để HUD độ tươi có mặt trong cảnh đo (một món đã ươn)
BENCH_SCENARIO = {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 64},
                           {"id": "I3", "kind": "ca_linh", "fresh": 25}]}
BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge",
            "microsoft-edge", "microsoft-edge-stable")
BROWSER_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)


def find_browser():
    env = os.environ.get("CHONOI_BROWSER")
    if env:
        return env
    for name in BROWSERS:
        p = shutil.which(name)
        if p:
            return p
    return next((p for p in BROWSER_PATHS if os.path.exists(p)), None)


def metrics(frames, measured_s, slowest_s, first_frame_epoch_ms, start_epoch_ms) -> dict:
    """avg_fps = frames / measured_s; p1_low_fps = 1 / trung bình max(1, ceil(1% frames)) khung chậm nhất (giây)."""
    k = max(1, math.ceil(0.01 * frames))
    slow = sorted(slowest_s, reverse=True)[:k]
    if frames <= 0 or measured_s <= 0 or len(slow) < k or min(slow) <= 0:
        raise ValueError("số đo từ trang không hợp lệ")
    return {"avg_fps": round(frames / measured_s, 2), "p1_low_fps": round(len(slow) / sum(slow), 2),
            "frames": frames, "measured_s": round(measured_s, 3),
            "load_ms": int(round(first_frame_epoch_ms - start_epoch_ms))}


def _args(argv):
    p = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark cảnh lặn có render (Contract v1.3).")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True, help="giây đo sau 3 s làm nóng")
    p.add_argument("--out", required=True)
    try:
        a = p.parse_args(argv)
    except SystemExit as e:
        raise BadInput("tham số sai") from e
    if not (math.isfinite(a.duration) and 0 < a.duration <= 150):
        raise BadInput("--duration phải trong (0, 150] giây (buổi sáng dài 180 s)")
    return a


def main(argv=None) -> int:
    try:
        a = _args(argv)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    browser = find_browser()
    if not browser:
        sys.stderr.write("không tìm thấy Chrome/Chromium/Edge; đặt CHONOI_BROWSER=<đường dẫn trình duyệt>\n")
        return 1
    tuning = load_contract()["tuning"]
    game = LiveGame("gather", tuning, {"gather": BENCH_SCENARIO}, a.seed)
    server = LiveServer(game, port=0)
    server.httpd.handle_error = lambda *_: None  # tắt trình duyệt sẽ reset kết nối poll; không phải lỗi bench
    server.start()
    profile = tempfile.mkdtemp(prefix="chonoi-bench-")
    url = f"{server.url}?bench=1&warmup={WARMUP_S}&duration={a.duration}"
    cmd = [browser, "--headless=new", f"--window-size={WINDOW[0]},{WINDOW[1]}", f"--user-data-dir={profile}",
           "--no-first-run", "--no-default-browser-check", "--mute-audio", "--disable-extensions",
           "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
           "--disable-backgrounding-occluded-windows", url]
    proc = None
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not game.bench_done.wait(WARMUP_S + a.duration + 60):
            sys.stderr.write("hết giờ chờ số đo từ trình duyệt\n")
            return 1
        r = game.bench_result
        out = metrics(r.get("frames"), r.get("measured_s"), r.get("slowest_s") or [],
                      r.get("first_frame_epoch_ms"), T0_EPOCH_MS)
    except OSError as e:
        sys.stderr.write(f"không khởi chạy được trình duyệt: {e}\n")
        return 1
    except (TypeError, ValueError) as e:
        sys.stderr.write(f"số đo sai: {e}\n")
        return 1
    finally:
        if proc is not None:
            proc.kill()
            proc.wait(timeout=10)
        server.stop()
        shutil.rmtree(profile, ignore_errors=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, separators=(",", ":"))
        f.write("\n")
    print(json.dumps(out), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
