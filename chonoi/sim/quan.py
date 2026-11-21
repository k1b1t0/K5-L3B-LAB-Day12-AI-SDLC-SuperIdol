"""Buổi tối — Mở Quán (`quan`), Test Contract v1.1.

Thứ tự một bước (Contract F + Ticket-02 4.5):
  1. đồng hồ, timer ca, nấu, ăn, kiên nhẫn (ready_ticks chỉ tăng cho món đã ready ở đầu bước)
  2. bếp theo id: nấu xong -> ready, dish_ready
  3. di chuyển rồi tối đa một interact, chọn theo (khoảng cách, bếp trước bàn, id)
  4. theo id bàn: trả tiền / rời bàn (patience khi còn giờ); hết ca -> closing rồi quan_end
  5. còn giờ: lượt khách theo lịch first_customer_tick + interval·k

Kho là mảng cá thể {id, kind, fresh}; khách giữ chỗ theo id cá thể (`reserved` nội bộ là list id).
v1.1 xuất kho / reserved dạng đếm theo loại.
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import count_kinds
from .common import Wallet, frac, ticks
from .ramp import ramp_velocity

ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, wallet=None, stock_items=None, dishes=None):
        t = tuning["quan"]
        self.t = t
        self.tuning = tuning
        self.menu = tuning["menu"]
        self.dish_ids = sorted(dishes if dishes is not None else self.menu)  # day: lọc theo kế hoạch
        self.rng = streams.get("customer")
        self.ids = ids
        self.wallet = wallet or Wallet(tuning, reputation=scenario.get("reputation"))
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = tuple(self.vel)
        self._ramp_left = 0
        self.stock = list(stock_items or [])
        self.hand = dict(scenario["hand"]) if scenario.get("hand") is not None else None
        self.time_left_ticks = scenario.get("time_left_ticks", ticks(t["duration_s"]))
        self.patience_max = ticks(t["patience_s"])
        self.eat_max = ticks(t["eat_s"])
        self.stoves = []
        for s in self._merge(t["stoves"], scenario.get("stoves", [])):
            state = s.get("state", "idle")
            self.stoves.append({"id": s["id"], "pos": [float(c) for c in s["pos"]], "state": state,
                                "dish": dict(s["dish"]) if s.get("dish") else None,
                                "cook_ticks_left": s.get("cook_ticks_left", 0),
                                "ready_ticks": s.get("ready_ticks", 0)})
        self.tables = [{"id": tb["id"], "pos": [float(c) for c in tb["pos"]]}
                       for tb in self._merge(t["tables"], scenario.get("tables", []))]
        for e in self.stock:
            ids.reserve(e["id"])
        self.customers = []
        for c in scenario.get("customers", []):
            status = c.get("order_status", "reserved" if c.get("state", "waiting") == "waiting" else "served")
            self.customers.append({
                "id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                "order_tick": c.get("order_tick", 0), "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", self.patience_max),
                "eat_ticks_left": c.get("eat_ticks_left", 0), "order_status": status,
                "reserved": c.get("reserved"), "base_price": c.get("base_price"), "tip": c.get("tip")})
            ids.reserve(c["id"])
        self._bind_reservations()
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- dựng / kiểm kho thực --------------------------------------------------
    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _bind_reservations(self):
        """Đổi reserved khai trong scenario (đếm theo loại) sang id cá thể; cấp phần thiếu theo order_tick rồi id bàn."""
        taken = set()
        auto = []
        for c in self.customers:
            spec = c["reserved"]
            if c["order_status"] != "reserved":
                c["reserved"] = []
                continue
            if spec is None:
                auto.append(c)
                continue
            c["reserved"] = self._pick(self.menu[c["dish_id"]]["recipe"], taken)  # scenario đã kiểm spec == công thức
            if c["reserved"] is None:
                raise BadInput(f"customers.{c['id']}: giữ chỗ vượt kho")
            taken.update(c["reserved"])
        for c in sorted(auto, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            c["reserved"] = self._pick(self.menu[c["dish_id"]]["recipe"], taken)
            if c["reserved"] is None:
                raise BadInput(f"customers.{c['id']}: kho không đủ để giữ chỗ")
            taken.update(c["reserved"])

    # --- kho ---------------------------------------------------------------------
    def _usable(self, item) -> bool:
        return True  # Phase 3: hàng ươn không dùng nấu

    def _held_ids(self):
        return {i for c in self.customers for i in c["reserved"]}

    def _pick(self, recipe, taken):
        """Mỗi loại lấy các cá thể khả dụng tươi nhất, hòa theo id. Thiếu -> None."""
        out = []
        for kind in sorted(recipe):
            pool = [i for i in self.stock if i["kind"] == kind and i["id"] not in taken and self._usable(i)]
            pool.sort(key=lambda i: (-(i["fresh"] if i["fresh"] is not None else 0), id_key(i["id"])))
            if len(pool) < recipe[kind]:
                return None
            out += [i["id"] for i in pool[:recipe[kind]]]
        return out

    def available(self) -> dict:
        held = self._held_ids()
        return count_kinds(i["kind"] for i in self.stock if i["id"] not in held and self._usable(i))

    # --- giao diện cho runner ------------------------------------------------------
    @property
    def money(self):
        return self.wallet.money

    @property
    def earned(self):
        return self.wallet.earned

    @property
    def reputation(self):
        return self.wallet.reputation

    def stock_out(self):
        return count_kinds(i["kind"] for i in self.stock)

    def _reserved_out(self, ids_):
        by_id = {i["id"]: i for i in self.stock}
        return count_kinds(by_id[i]["kind"] for i in ids_)

    def _items_out(self, items):
        return sorted(i["kind"] for i in items)

    def snapshot(self) -> dict:
        seated = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": self.stock_out(),
            "available": self.available(),
            "hand": self.hand,
            "stoves": [{k: s[k] for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": seated.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": [dict(c, reserved=self._reserved_out(c["reserved"])) for c in sort_by_id(self.customers)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        ev = []
        self.phase_tick += 1
        # 1. đồng hồ và timer
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        was_ready = {s["id"] for s in self.stoves if s["state"] == "ready"}
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            elif s["id"] in was_ready:
                s["ready_ticks"] += 1
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        self._decay(ev)
        # 2. bếp theo id
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                ev.append(("dish_ready", self._dish_ev(s)))
        # 3. di chuyển rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(ev)
        # 4. thanh toán, rời bàn, đóng ca
        closing = self.time_left_ticks <= 0
        for c in self._by_table():
            if c["state"] == "eating" and c["eat_ticks_left"] == 0:
                self._pay(c, "finished_eating", ev)
            elif c["state"] == "waiting" and c["patience_ticks_left"] == 0 and not closing:
                self.wallet.add_rep(self.t["left_reputation_delta"])
                self._leave(c, "patience", ev)
        if closing:
            for c in self._by_table():
                if c["state"] == "eating":
                    self._pay(c, "closing", ev)
                else:
                    self._leave(c, "closing", ev)
            self.done, self.reason = True, "time"
            ev.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                    "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return ev
        # 5. khách mới theo lịch
        if self.random_customers and self._arrival_tick(self.phase_tick):
            self._arrive(ev)
        return ev

    # --- Phase 3: hao tươi ---------------------------------------------------------
    def _decay(self, ev):
        pass

    # --- các bước con --------------------------------------------------------------
    def _by_table(self):
        return sorted(self.customers, key=lambda c: id_key(c["table_id"]))

    def _arrival_tick(self, k) -> bool:
        first = int(self.t["first_customer_tick"])
        interval = ticks(self.t["customer_interval_s"])
        return k >= first and (k - first) % interval == 0

    def _dish_ev(self, s):
        return {"stove_id": s["id"], "order_id": s["dish"]["order_id"], "dish_id": s["dish"]["dish_id"]}

    def _interact(self, ev):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return
        _, _, _, kind, obj = min(cands, key=lambda c: c[:3])
        if kind == "stove":
            if obj["state"] == "idle":
                self._start_cook(obj, ev)
            elif obj["state"] == "ready" and self.hand is None:
                self.hand = obj["dish"]
                ev.append(("dish_picked", self._dish_ev(obj)))
                obj["state"], obj["dish"], obj["ready_ticks"] = "idle", None, 0
        else:
            c = next((c for c in self.customers if c["table_id"] == obj["id"]), None)
            if c and c["state"] == "waiting" and self.hand and self.hand["order_id"] == c["id"]:
                self._serve(c, ev)

    def _start_cook(self, stove, ev):
        orders = [c for c in self.customers if c["order_status"] == "reserved"]
        if not orders:
            return
        c = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        used = [i for i in self.stock if i["id"] in set(c["reserved"])]
        self.stock = [i for i in self.stock if i["id"] not in set(c["reserved"])]
        bp = self._base_price(c["dish_id"], used)
        c["reserved"], c["order_status"], c["base_price"] = [], "assigned", bp
        stove["state"] = "cooking"
        stove["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": bp}
        stove["cook_ticks_left"] = ticks(self.menu[c["dish_id"]]["cook_s"])
        stove["ready_ticks"] = 0
        ev.append(("cook_started", dict(self._dish_ev(stove), items=self._items_out(used), base_price=bp)))

    def _base_price(self, dish_id, used):
        return int(self.menu[dish_id]["price"])

    def _serve(self, c, ev):
        bp = self.hand["base_price"]
        ratio = frac(self.t["tip_min_patience_ratio"])
        tip = math.floor(bp * frac(self.t["tip_rate"])) if c["patience_ticks_left"] >= ratio * self.patience_max else 0
        c.update(state="eating", eat_ticks_left=self.eat_max, order_status="served", base_price=bp, tip=tip)
        self.hand = None
        ev.append(("served", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                              "patience_ticks_left": c["patience_ticks_left"], "base_price": bp, "tip": tip}))

    def _pay(self, c, reason, ev):
        amount = c["base_price"] + c["tip"]
        self.wallet.money += amount
        self.wallet.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self.wallet.add_rep(self.t["tip_reputation"])
        self.customers.remove(c)
        ev.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                            "tip": c["tip"], "amount": amount, "reason": reason}))

    def _leave(self, c, reason, ev):
        """Khách rời: nhả giữ chỗ, bỏ món của đơn (đang nấu, ready hoặc trên tay)."""
        for s in self.stoves:
            if s["dish"] and s["dish"]["order_id"] == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand and self.hand["order_id"] == c["id"]:
            self.hand = None
        self.customers.remove(c)
        ev.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                     "reputation": self.reputation}))

    def _arrive(self, ev):
        seated = {c["table_id"] for c in self.customers}
        free = [tb for tb in sort_by_id(self.tables) if tb["id"] not in seated]
        if not free:
            return
        taken = self._held_ids()
        ok = [d for d in self.dish_ids if self._pick(self.menu[d]["recipe"], taken) is not None]
        if not ok:
            ev.append(("no_dish", {}))
            return
        dish = ok[self.rng.randrange(len(ok))]
        cid = self.ids.new("C")
        self.customers.append({
            "id": cid, "table_id": free[0]["id"], "dish_id": dish, "order_tick": self.phase_tick,
            "state": "waiting", "patience_ticks_left": self.patience_max, "eat_ticks_left": 0,
            "order_status": "reserved", "reserved": self._pick(self.menu[dish]["recipe"], taken),
            "base_price": None, "tip": None})
        ev.append(("customer_arrived", {"order_id": cid, "table_id": free[0]["id"], "dish_id": dish}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t["ramp_max_ticks"]))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / 60
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
