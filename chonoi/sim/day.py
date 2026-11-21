"""Vòng Ngày (`--mode day`, Ticket-02 mục 2 và 4.5).

day_start -> day_plan -> phase_start(gather) ... gather_end -> phase_start(quan) cùng tick
... quan_end -> phase_start(shop) cùng tick ... shop_end -> days_completed += 1 -> Ngày kế / kết thúc cùng tick.
Pha mới chỉ chạy gameplay từ bước sau. Tiền, earned, uy tín, cấp đã mua và bộ cấp id sống xuyên Ngày.

step() trả list (phase, name, data, day); runner bọc thành dòng event.
"""

from ..inventory import count_kinds
from .common import Wallet
from .gather import GatherSim
from .quan import QuanSim


def plan_for(tuning, overrides, day):
    """Kế hoạch Ngày `day` (1-based). D1–D5 lặp cho Ngày 6+ (soak). Scenario ghi đè theo số Ngày."""
    plans = tuning["day_plan"]
    if day in overrides:
        return overrides[day]
    base = plans[(day - 1) % len(plans)]
    return {"dishes": dict(base["dishes"]), "ingredients": dict(base["ingredients"])}


def ingredients_of(menu, dishes):
    total = {}
    for d, n in dishes.items():
        for k, q in menu[d]["recipe"].items():
            total[k] = total.get(k, 0) + q * n
    return {k: total[k] for k in sorted(total)}


class ShopPhase:
    phase = "shop"

    def __init__(self, tuning, wallet, upgrades, stock_items):
        self.t = tuning["shop"]
        self.wallet = wallet
        self.upgrades = upgrades
        self.stock = stock_items
        self.time_left_ticks = int(self.t["max_ticks"])
        self.phase_tick = 0
        self.done = False

    def snapshot(self):
        return {"stock": count_kinds(i["kind"] for i in self.stock)}

    def step(self, inp):
        ev = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy is not None:
            ev.append(self._buy(inp.buy))
        if inp.pressed("shop_done"):
            self.done = True
            ev.append(("shop_end", {"reason": "done"}))
        elif self.time_left_ticks == 0:
            self.done = True
            ev.append(("shop_end", {"reason": "time"}))
        return ev

    def _buy(self, action):
        levels = self.t["upgrades"].get(action)
        if levels is None:
            return ("buy_failed", {"action": action, "reason": "unknown"})
        cur = self.upgrades.get(action, 0)
        if cur >= len(levels):
            return ("buy_failed", {"action": action, "reason": "max_level"})
        nxt = levels[cur]
        if self.wallet.money < nxt["price"]:
            return ("buy_failed", {"action": action, "reason": "funds"})
        self.wallet.money -= nxt["price"]
        self.upgrades[action] = nxt["level"]
        return ("bought", {"upgrade": action, "level": nxt["level"], "price": nxt["price"],
                           "money": self.wallet.money})


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.streams = streams
        self.ids = ids
        self.days = days
        d = scenario.get("day", {})
        self.wallet = Wallet(tuning, money=d.get("money", 0), earned=d.get("earned", 0),
                             reputation=d.get("reputation"))
        self.upgrades = dict(d.get("upgrades", {}))
        self.active_upgrades = {}
        self.plan_overrides = {p["day"]: {"dishes": dict(p["dishes"]),
                                          "ingredients": ingredients_of(tuning["menu"], p["dishes"])}
                               for p in d.get("day_plan", [])}
        self.gather_tpl = scenario.get("gather", {})
        self.quan_tpl = scenario.get("quan", {})
        self.day = 0
        self.days_completed = 0
        self.cur = None
        self.plan = None
        self.done = False
        self.reason = None
        self.pending = self._start_day()  # sự kiện tick 0

    # --- giao diện cho runner ---------------------------------------------------
    @property
    def phase(self):
        return self.cur.phase

    @property
    def phase_tick(self):
        return self.cur.phase_tick

    @property
    def time_left_ticks(self):
        return self.cur.time_left_ticks

    @property
    def money(self):
        return self.wallet.money

    @property
    def earned(self):
        return self.wallet.earned

    @property
    def reputation(self):
        return self.wallet.reputation

    def snapshot(self):
        s = {"day": self.day, "day_plan": self.plan, "upgrades": dict(sorted(self.upgrades.items())),
             "active_upgrades": dict(sorted(self.active_upgrades.items()))}
        s.update(self.cur.snapshot())
        return s

    def take_initial(self):
        ev, self.pending = self.pending, []
        return ev

    # --- chuyển pha -----------------------------------------------------------------
    def _start_day(self):
        self.day += 1
        self.active_upgrades = dict(self.upgrades)  # chỉ khi dựng Ngày mới
        self.plan = plan_for(self.tuning, self.plan_overrides, self.day)
        self.cur = GatherSim(self.tuning, self.gather_tpl, self.streams, self.ids, wallet=self.wallet,
                             day=self.day, active_upgrades=self.active_upgrades)
        return [("gather", "day_start", {}, self.day),
                ("gather", "day_plan", {"dishes": self.plan["dishes"], "ingredients": self.plan["ingredients"]},
                 self.day),
                ("gather", "phase_start", {}, self.day)]

    def step(self, inp):
        phase = self.cur.phase
        out = [(phase, n, d, self.day) for n, d in self.cur.step(inp)]
        if not self.cur.done:
            return out
        if phase == "gather":
            self.cur = QuanSim(self.tuning, self.quan_tpl, self.streams, self.ids, wallet=self.wallet,
                               stock_items=list(self.cur.hold), dishes=list(self.plan["dishes"]))
            out.append(("quan", "phase_start", {}, self.day))
        elif phase == "quan":
            self.cur = ShopPhase(self.tuning, self.wallet, self.upgrades, self.cur.stock)
            out.append(("shop", "phase_start", {}, self.day))
        else:
            self.days_completed += 1
            if self.days_completed >= self.days:
                self.done, self.reason = True, "days_complete"
            else:
                out += self._start_day()
        return out
