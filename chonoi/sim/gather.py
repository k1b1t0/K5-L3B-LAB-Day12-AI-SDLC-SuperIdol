"""Buổi sáng — Lặn & Hái (`gather`), Test Contract v1.2.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x hướng đông, d là độ sâu tăng xuống, d = 0 là mặt nước).

Thứ tự một bước (Ticket-02 mục 4.5):
  đồng hồ, cooldown, bất tử, hồi nút, hao tươi giỏ (spoiled theo id) -> bơi, oxy, ngạt -> thủy quái theo id rồi tối đa một hit
  -> tương tác (bến trước hái) -> bắt cá (vị trí cá TRƯỚC khi bơi) -> hết giờ
  -> nếu còn giờ: cá bơi, sinh cá theo lịch.
Máu về 0 (do ngạt hoặc hit) -> faint rồi gather_end(fainted) ngay, bỏ các bước còn lại.
Giỏ: mảng cá thể {id, kind, fresh}; fresh là Fraction, hàng mới = freshness.initial, hao từ bước sau.
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import fresh_in, inventory_payload, items_out
from .common import Wallet, clamp, frac, move_toward, ticks
from .ramp import ramp_velocity

AXES = ("x", "d")


def unit(v):
    n = math.hypot(v[0], v[1])
    return [v[0] / n, v[1] / n] if n > 0 else [1.0, 0.0]


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, wallet=None, day=1, active_upgrades=None,
                 hold_items=None, new_hold_ids=False):
        t = tuning["gather"]
        self.t = t
        self.tuning = tuning
        self.ids = ids
        self.fish_rng = streams.get("fish")
        self.wallet = wallet or Wallet(tuning)
        self.day = day
        up = active_upgrades or {}
        self.oxygen_max = ticks(self._upgrade_value(tuning, "oxygen", up, "oxygen_max_s", t["oxygen_max_s"]))
        self.hp_max = int(self._upgrade_value(tuning, "hp", up, "hp_max", t["hp_max"]))
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = tuple(self.vel)  # vel khai trong scenario là vận tốc đang giữ
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.time_left_ticks = scenario.get("time_left_ticks", ticks(t["duration_s"]))
        self.phase_tick = 0
        fr = tuning["freshness"]
        self.fresh_initial = frac(fr["initial"])
        self.decay = frac(fr["gather_decay_per_s"]) / 60
        self.spoiled_below = frac(fr["spoiled_below"])
        # giỏ: mảng cá thể {id, kind, fresh} theo thứ tự vào giỏ (cuối là mới nhất)
        if hold_items is not None:
            self.hold = hold_items
        else:
            # day: Ngày đầu giữ id trong mẫu, Ngày kế cấp id mới theo thứ tự mảng
            self.hold = [{"id": ids.new("I") if new_hold_ids else h["id"], "kind": h["kind"],
                          "fresh": fresh_in(h["fresh"])} for h in scenario.get("hold", [])]
        for i in self.hold:
            ids.reserve(i["id"])
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.random_fish = scenario.get("random_fish", True)
        self.fish = []
        if "fish" in scenario:
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": float(f.get("heading_deg", 0)), "age_ticks": f.get("age_ticks", 0)}
                         for f in scenario["fish"]]
        for e in self.nodes + self.fish:
            ids.reserve(e["id"])
        if "fish" not in scenario and self.random_fish:
            for _ in range(int(t["fish_initial"])):
                f = self._spawn_fish()
                if f is None:
                    break
        mon = t["monsters"]
        if "monsters" in scenario:
            src_m = scenario["monsters"]
        else:
            src_m = [dict(s, target_idx=1) for s in mon["spawns"] if s.get("from_day", 1) <= day]
        self.monsters = [{"id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                          "waypoints": [[float(c) for c in w] for w in m["waypoints"]],
                          "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                          "state_ticks_left": m.get("state_ticks_left", 0),
                          "recoil_dir": list(m["recoil_dir"]) if m.get("recoil_dir") is not None else None}
                         for m in src_m]
        for m in self.monsters:
            ids.reserve(m["id"])
        self.done = False
        self.reason = None

    @staticmethod
    def _upgrade_value(tuning, kind, active, key, base):
        lvl = active.get(kind, 0)
        if lvl <= 0:
            return base
        return tuning["shop"]["upgrades"][kind][lvl - 1][key]

    # --- giao diện cho runner -------------------------------------------------
    @property
    def money(self):
        return self.wallet.money

    @property
    def earned(self):
        return self.wallet.earned

    @property
    def reputation(self):
        return self.wallet.reputation

    def inventory_payload(self) -> dict:
        return inventory_payload(self.hold)

    def hold_out(self):
        """Loại hàng trong giỏ theo thứ tự vào giỏ (tiện cho test)."""
        return [i["kind"] for i in self.hold]

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "catch_cd_ticks": self.catch_cd_ticks, "invuln_ticks": self.invuln_ticks,
                       "at_surface": self._at_surface()},
            "hold": items_out(self.hold), "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "kind": n["kind"], "pos": n["pos"], "regrow_ticks": n["regrow_ticks"],
                       "ready": n["regrow_ticks"] == 0} for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "kind": f["kind"], "pos": f["pos"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "waypoints": m["waypoints"],
                          "target_idx": m["target_idx"], "state": m["state"],
                          "state_ticks_left": m["state_ticks_left"], "recoil_dir": m["recoil_dir"]}
                         for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        ev = []
        self.phase_tick += 1
        # 1. đồng hồ, cooldown, bất tử, hồi nút
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    ev.append(("node_regrown", {"node_id": n["id"]}))
        self._decay(ev)
        # 2. bơi, dive/surface, oxy, ngạt
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            ev.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            ev.append(("surface", {"pos": list(self.pos)}))
        if now_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
        else:
            prev = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if prev > 0 and self.oxygen_ticks == 0:
                ev.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    ev.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        self._faint("choke", ev)
                        return ev
            else:
                self.zero_oxy_ticks = 0
        # 3. thủy quái theo id, rồi tối đa một hit
        if self._monsters(ev):
            return ev
        # 4. tương tác: bến trước, rồi hái ở mặt nước
        if inp.pressed("interact"):
            if math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]:
                self._finish("docked", ev)
                return ev
            if self._at_surface():
                self._harvest(ev)
        # 5. bắt cá (cá chưa bơi bước này)
        if inp.pressed("catch") and not self._at_surface() and self.catch_cd_ticks == 0:
            self._catch(ev)
        # 6. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", ev)
            return ev
        # 7. cá bơi và sinh thêm
        if self.random_fish:
            for f in sort_by_id(self.fish):
                self._swim_fish(f)
            spawn = int(self.t["fish_spawn_ticks"])
            if self.phase_tick % spawn == 0 and len(self.fish) < int(self.t["fish_max"]):
                f = self._spawn_fish()
                if f is not None:
                    ev.append(("fish_spawned", {"id": f["id"], "kind": f["kind"], "pos": list(f["pos"])}))
        return ev

    # --- độ tươi (v1.2) -----------------------------------------------------------
    def _decay(self, ev):
        for i in sort_by_id(self.hold):
            before = i["fresh"]
            i["fresh"] = max(before - self.decay, 0)
            if before >= self.spoiled_below > i["fresh"]:
                ev.append(("spoiled", {"item_id": i["id"], "kind": i["kind"], "location": "hold"}))

    def _new_item(self, kind):
        return {"id": self.ids.new("I"), "kind": kind, "fresh": self.fresh_initial}

    def _lost_out(self, items):
        return items_out(items)

    # --- hái / bắt ---------------------------------------------------------------
    def _free(self):
        return int(self.t["hold_capacity"]) - len(self.hold)

    def _harvest(self, ev):
        r = self.t["interact_radius"]
        cands = [n for n in self.nodes if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= r]
        if not cands:
            return
        n = min(cands, key=lambda c: (math.dist(self.pos, c["pos"]), id_key(c["id"])))
        need = int(self.t["node_yield"])
        if self._free() < need:
            ev.append(("hold_full", {"action": "gather", "node_id": n["id"], "required": need, "free": self._free()}))
            return
        for _ in range(need):
            self.hold.append(self._new_item(n["kind"]))
        n["regrow_ticks"] = ticks(self.t["regrow_s"])
        ev.append(("gather", {"node_id": n["id"], "kind": n["kind"], "amount": need}))

    def _catch(self, ev):
        r = self.t["catch_radius"]
        cands = [f for f in self.fish if math.dist(self.pos, f["pos"]) <= r]
        if not cands:
            return
        f = min(cands, key=lambda c: (math.dist(self.pos, c["pos"]), id_key(c["id"])))
        need = int(self.t["fish_yield"][f["kind"]])
        if self._free() < need:
            ev.append(("hold_full", {"action": "catch", "fish_id": f["id"], "required": need, "free": self._free()}))
            return
        for _ in range(need):
            self.hold.append(self._new_item(f["kind"]))
        self.fish.remove(f)
        self.catch_cd_ticks = ticks(self.t["catch_cooldown_s"])
        ev.append(("fish_caught", {"fish_id": f["id"], "kind": f["kind"], "yield": need}))

    # --- thủy quái ---------------------------------------------------------------
    def _monsters(self, ev) -> bool:
        """Cập nhật thủy quái theo id rồi xét tối đa một hit. Trả True nếu người chơi ngất."""
        mon = self.t["monsters"]
        bx, bd = self.t["bounds"]["x"], self.t["bounds"]["d"]
        fresh_patrol = set()  # vừa hết recoil: xét phát hiện/chạm từ bước kế
        for m in sort_by_id(self.monsters):
            sp = mon["species"][m["kind"]]
            lo, hi = max(bd[0], sp["depths"][0]), min(bd[1], sp["depths"][1])
            if m["state"] == "recoil":
                step = sp["recoil_dist"] / sp["recoil_ticks"]
                m["pos"] = [m["pos"][0] + m["recoil_dir"][0] * step, m["pos"][1] + m["recoil_dir"][1] * step]
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                    fresh_patrol.add(m["id"])
            else:
                deep = self.pos[1] >= sp["depths"][0]
                dist = math.dist(self.pos, m["pos"])
                if m["state"] == "patrol" and deep and dist <= sp["detect_radius"]:
                    m["state"] = "chase"
                elif m["state"] == "chase" and (dist > sp["exit_radius"] or not deep):
                    m["state"] = "patrol"
                if m["state"] == "chase":
                    m["pos"], _ = move_toward(m["pos"], self.pos, sp["chase_speed"] / 60)
                else:
                    wp = m["waypoints"][m["target_idx"]]
                    m["pos"], arrived = move_toward(m["pos"], wp, sp["patrol_speed"] / 60)
                    if arrived:
                        m["target_idx"] = 1 - m["target_idx"]
            m["pos"] = [clamp(m["pos"][0], bx[0], bx[1]), clamp(m["pos"][1], lo, hi)]
        if self.invuln_ticks > 0:
            return False
        cands = []
        for m in self.monsters:
            sp = mon["species"][m["kind"]]
            if m["state"] in ("recoil", "stunned") or m["id"] in fresh_patrol:
                continue
            d = math.dist(self.pos, m["pos"])
            if d <= sp["hit_radius"] and self.pos[1] >= sp["depths"][0]:
                cands.append((d, id_key(m["id"]), m))
        if not cands:
            return False
        _, _, m = min(cands, key=lambda c: (c[0], c[1]))
        sp = mon["species"][m["kind"]]
        self.hp -= 1
        k = math.floor(len(self.hold) * mon["loss_ratio"])
        lost = [self.hold.pop() for _ in range(k)]
        self.invuln_ticks = int(mon["invuln_ticks"])
        m["state"], m["state_ticks_left"] = "recoil", int(sp["recoil_ticks"])
        m["recoil_dir"] = unit([m["pos"][0] - self.pos[0], m["pos"][1] - self.pos[1]])
        ev.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": self._lost_out(lost),
                                   "pos": list(self.pos)}))
        if self.hp <= 0:
            self._faint("monster", ev)
            return True
        return False

    # --- cá ---------------------------------------------------------------------
    def _spawn_points(self):
        out = []
        for kind in sorted(self.t["fish_spawn_depths"]):
            pts = [(float(x), float(d)) for x in self.t["fish_spawn_x"] for d in self.t["fish_spawn_depths"][kind]]
            ok = [p for p in pts
                  if all(math.dist(p, f["pos"]) > self.t["fish_spawn_clearance"] for f in self.fish)]
            if ok:
                out.append((kind, ok))
        return out

    def _spawn_fish(self):
        options = self._spawn_points()
        if not options:
            return None
        w = self.t["fish_weights"]
        total = sum(w[k] for k, _ in options)
        r = self.fish_rng.random() * total
        kind, pts = options[-1]
        acc = 0.0
        for k, p in options:
            acc += w[k]
            if r < acc:
                kind, pts = k, p
                break
        pos = pts[self.fish_rng.randrange(len(pts))]
        f = {"id": self.ids.new("F"), "kind": kind, "pos": [pos[0], pos[1]],
             "heading_deg": self.fish_rng.random() * 360.0, "age_ticks": 0}
        self.fish.append(f)
        return f

    def _swim_fish(self, f):
        n = f["age_ticks"] + 1
        if n % int(self.t["fish_turn_ticks"]) == 0:
            f["heading_deg"] = self.fish_rng.random() * 360.0
        h = math.radians(f["heading_deg"])
        v = [math.cos(h), math.sin(h)]
        step = self.t["fish_speed"] / 60
        lims = (self.t["fish_x"], self.t["fish_depths"][f["kind"]])
        for i in (0, 1):
            lo, hi = lims[i]
            p = clamp(f["pos"][i], lo, hi) + v[i] * step
            if p > hi:
                p, v[i] = 2 * hi - p, -v[i]
            elif p < lo:
                p, v[i] = 2 * lo - p, -v[i]
            f["pos"][i] = clamp(p, lo, hi)
        f["heading_deg"] = math.degrees(math.atan2(v[1], v[0])) % 360.0
        f["age_ticks"] = n

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _faint(self, cause, ev):
        lost = [self.hold.pop() for _ in range(len(self.hold))]  # LIFO: nhặt sau mất trước
        ev.append(("faint", {"cause": cause, "lost": self._lost_out(lost), "hp": 0}))
        self.hp = 0
        self._finish("fainted", ev)

    def _finish(self, reason, ev):
        self.done = True
        self.reason = reason
        ev.append(("gather_end", {"reason": reason, "inventory": self.inventory_payload()}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / 60
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
