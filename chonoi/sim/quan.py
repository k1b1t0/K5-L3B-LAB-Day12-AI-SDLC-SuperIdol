"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        for c in scenario.get("customers", []):
            cust = dict(c)
            cust.setdefault("state", "waiting")
            cust.setdefault("patience_ticks_left", int(round(t["patience_s"] * 60)))
            cust.setdefault("reserved", {})
            self.customers.append(cust)
            ids.reserve(cust["id"])
        self.random_customers = scenario.get("random_customers", True)
        self.tick_count = 0
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _get_reserved_total(self) -> dict:
        total = {}
        for c in self.customers:
            for k, v in c.get("reserved", {}).items():
                total[k] = total.get(k, 0) + v
        return total

    def _get_available_stock(self) -> dict:
        reserved = self._get_reserved_total()
        avail = {}
        for k, v in self.stock.items():
            avail[k] = max(0, v - reserved.get(k, 0))
        return avail

    def _can_cook(self, dish_id: str, avail: dict) -> bool:
        recipe = self.menu[dish_id]["recipe"]
        return all(avail.get(item, 0) >= qty for item, qty in recipe.items())

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.tick_count += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Bếp: giảm cook_ticks_left, chuyển sang ready
        for st in sort_by_id(self.stoves):
            if st["state"] == "cooking":
                st["cook_ticks_left"] = max(0, st["cook_ticks_left"] - 1)
                if st["cook_ticks_left"] == 0:
                    st["state"] = "ready"
                    st["ready_ticks"] = 0
                    events.append(("dish_ready", {"stove_id": st["id"], "dish_id": st["dish"]}))
            elif st["state"] == "ready":
                st["ready_ticks"] += 1

        # 2. Khách: giảm kiên nhẫn (waiting) hoặc tiến trình ăn (eating)
        remaining_customers = []
        for c in sort_by_id(self.customers):
            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
                if c["patience_ticks_left"] == 0:
                    delta = float(self.t["left_reputation_delta"])
                    self.reputation = max(self.t["reputation_min"], min(self.t["reputation_max"], self.reputation + delta))
                    events.append(("customer_left", {
                        "customer_id": c["id"],
                        "table_id": c["table_id"],
                        "dish_id": c.get("dish_id"),
                        "reputation": self.reputation
                    }))
                    continue
            elif c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
                if c["eat_ticks_left"] == 0:
                    price = int(c.get("price", self.menu[c["dish_id"]]["price"]))
                    tip = int(c.get("tip", 0))
                    total = price + tip
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    if tip > 0:
                        rep_inc = float(self.t["tip_reputation"])
                        self.reputation = max(self.t["reputation_min"], min(self.t["reputation_max"], self.reputation + rep_inc))
                    events.append(("paid", {
                        "customer_id": c["id"],
                        "table_id": c["table_id"],
                        "dish_id": c["dish_id"],
                        "price": price,
                        "tip": tip,
                        "money": self.money,
                        "reputation": self.reputation
                    }))
                    continue
            remaining_customers.append(c)
        self.customers = remaining_customers

        # 3. Người chơi di chuyển
        self._move(inp)

        # 4. Tương tác interact (Bếp / Bàn)
        if inp.pressed("interact"):
            radius = float(self.t["interact_radius"])
            # Tìm bếp trong tầm
            stoves_in_range = [st for st in self.stoves if math.dist(self.pos, st["pos"]) <= radius]
            # Tìm bàn trong tầm
            tables_in_range = [tb for tb in self.tables if math.dist(self.pos, tb["pos"]) <= radius]

            # Gom ứng viên: (khoảng_cách, loại_ưu_tiên [0: bếp, 1: bàn], id_key, obj_type, obj)
            candidates = []
            for st in stoves_in_range:
                d = math.dist(self.pos, st["pos"])
                candidates.append((d, 0, id_key(st["id"]), "stove", st))
            for tb in tables_in_range:
                d = math.dist(self.pos, tb["pos"])
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))

            if candidates:
                candidates.sort(key=lambda x: (x[0], x[1], x[2]))
                _, _, _, obj_type, target = candidates[0]

                if obj_type == "stove":
                    # Bếp idle: bắt đầu nấu món khách đang chờ
                    if target["state"] == "idle" and self.hand is None:
                        # Tìm khách waiting chưa được nấu món
                        waiting_custs = [c for c in sort_by_id(self.customers) if c["state"] == "waiting" and not c.get("assigned_stove")]
                        if waiting_custs:
                            cust = waiting_custs[0]
                            d_id = cust["dish_id"]
                            recipe = self.menu[d_id]["recipe"]
                            # Trừ kho và giải phóng giữ chỗ của khách
                            for item, qty in recipe.items():
                                self.stock[item] = max(0, self.stock.get(item, 0) - qty)
                            cust["reserved"] = {}
                            cust["assigned_stove"] = target["id"]
                            target["state"] = "cooking"
                            target["dish"] = d_id
                            target["cook_ticks_left"] = int(round(self.menu[d_id]["cook_s"] * 60))
                            target["ready_ticks"] = 0
                            events.append(("cook_started", {
                                "stove_id": target["id"],
                                "dish_id": d_id,
                                "customer_id": cust["id"]
                            }))
                    # Bếp ready: bưng món lên tay
                    elif target["state"] == "ready" and self.hand is None:
                        self.hand = target["dish"]
                        dish_picked = target["dish"]
                        target["state"] = "idle"
                        target["dish"] = None
                        target["cook_ticks_left"] = 0
                        target["ready_ticks"] = 0
                        events.append(("dish_picked", {
                            "stove_id": target["id"],
                            "dish_id": dish_picked
                        }))

                elif obj_type == "table":
                    # Bàn có khách waiting: giao món
                    cust = next((c for c in self.customers if c["table_id"] == target["id"] and c["state"] == "waiting"), None)
                    if cust and self.hand is not None and self.hand == cust["dish_id"]:
                        d_id = self.hand
                        self.hand = None
                        cust["state"] = "eating"
                        cust["eat_ticks_left"] = int(round(self.t["eat_s"] * 60))
                        price = int(self.menu[d_id]["price"])
                        # Tính tip
                        p_ratio = cust["patience_ticks_left"] / cust.get("patience_max_ticks", round(self.t["patience_s"] * 60))
                        tip = 0
                        if p_ratio >= float(self.t["tip_min_patience_ratio"]):
                            tip = int(round(price * float(self.t["tip_rate"])))
                        cust["price"] = price
                        cust["tip"] = tip
                        events.append(("served", {
                            "table_id": target["id"],
                            "customer_id": cust["id"],
                            "dish_id": d_id,
                            "price": price,
                            "tip": tip
                        }))

        # 5. Khách mới theo lịch
        first_tick = int(self.t["first_customer_tick"])
        interval = int(round(self.t["customer_interval_s"] * 60))
        is_spawn_tick = (self.tick_count == first_tick) or (self.tick_count > first_tick and (self.tick_count - first_tick) % interval == 0)

        if self.random_customers and is_spawn_tick:
            occupied_tables = {c["table_id"] for c in self.customers}
            free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied_tables]
            if free_tables:
                avail = self._get_available_stock()
                cookable_dishes = [d_id for d_id in sorted(self.menu.keys()) if self._can_cook(d_id, avail)]
                if not cookable_dishes:
                    events.append(("no_dish", {"table_id": free_tables[0]["id"]}))
                else:
                    cust_rng = self.rng.get("customer")
                    chosen_dish = cust_rng.choice(cookable_dishes)
                    chosen_table = free_tables[0]
                    cust_id = self.ids.new("C")
                    recipe = dict(self.menu[chosen_dish]["recipe"])
                    patience_ticks = int(round(self.t["patience_s"] * 60))
                    new_cust = {
                        "id": cust_id,
                        "table_id": chosen_table["id"],
                        "dish_id": chosen_dish,
                        "state": "waiting",
                        "patience_ticks_left": patience_ticks,
                        "patience_max_ticks": patience_ticks,
                        "reserved": recipe
                    }
                    self.customers.append(new_cust)
                    events.append(("customer_arrived", {
                        "customer_id": cust_id,
                        "table_id": chosen_table["id"],
                        "dish_id": chosen_dish
                    }))

        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
