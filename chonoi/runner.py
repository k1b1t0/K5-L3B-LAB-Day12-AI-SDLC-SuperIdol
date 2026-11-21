"""Vòng tick (Contract B/E, v1.2).

Thứ tự ghi: [day: sự kiện tick 0] -> snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot
(bội số --snapshot-every, tick đổi pha hoặc tick dừng) -> dòng 'end'. Mỗi tick tối đa một snapshot.

Pause (Ticket-02 4.2): xét cạnh pause trước. Vào pause chỉ tăng tick ngoài và phát `paused`; khi còn pause bỏ
qua mọi cạnh hành động và buy, sim_tick/phase_tick/timer đứng yên; cạnh pause kế phát `resumed` rồi chạy
gameplay ngay trong bước đó.

`Session` dùng chung cho headless (`run`) và cửa sổ chơi (`chonoi.live`): cùng một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import validate_items, write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory=None, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    stock = inventory if inventory is not None else validate_items(scenario.get("stock", []), name="quan.stock")
    return QuanSim(tuning, scenario, streams, ids, stock_items=stock)


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False
        self.phase_changed = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _state(self):
        if self.sim.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def _row(self, phase, name, data, day=None):
        r = {"type": "event", "tick": self.tick, "phase": phase}
        if self.mode == "day":
            r["day"] = day
        r["name"] = name
        r["data"] = data
        return r

    def initial_events(self) -> list:
        """Sự kiện tick 0 (chỉ mode day): day_start, day_plan, phase_start(gather)."""
        if self.mode != "day":
            return []
        return [self._row(p, n, d, day) for p, n, d, day in self.sim.take_initial()]

    def snapshot(self) -> dict:
        sim = self.sim
        mult = self.tuning["score"]["reputation_multiplier"]
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
             "phase": sim.phase, "phase_tick": sim.phase_tick, "state": self._state(),
             "time_left_ticks": sim.time_left_ticks, "money": sim.money, "earned": sim.earned,
             "reputation": sim.reputation, "score": sim.earned + mult * math.floor(sim.wallet.rep)}
        s.update(sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước ngoài với `inp`; trả các dòng event (tick = k + 1)."""
        self.tick += 1
        self.phase_changed = False
        rows = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            if self.paused:
                return [self._row(self.sim.phase, "paused", {}, getattr(self.sim, "day", None))]
            rows.append(self._row(self.sim.phase, "resumed", {}, getattr(self.sim, "day", None)))
        elif self.paused:
            return []
        self.sim_tick += 1
        before = self.sim.phase
        if self.mode == "day":
            day_before = self.sim.day
            for p, n, d, day in self.sim.step(inp):
                rows.append(self._row(p, n, d, day))
            self.phase_changed = self.sim.phase != before or self.sim.day != day_before
        else:
            rows += [self._row(self.sim.phase, n, d) for n, d in self.sim.step(inp)]
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        mult = self.tuning["score"]["reputation_multiplier"]
        r = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
             "state": self._state(), "reason": sim.reason if sim.done else "tick_limit",
             "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
             "score": sim.earned + mult * math.floor(sim.wallet.rep)}
        if self.mode == "day":
            r["days_completed"] = sim.days_completed
        return r

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_payload())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None,
        inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done or sess.phase_changed:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
