"""Đọc game.contract.json và kiểm dải hợp lệ của tuning (Test Contract v1.0 mục A + v1.1 mục 4.1)."""

import json
import math
import os

from .errors import BadInput
from .inventory import KINDS

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    if not isinstance(c, dict):
        raise BadInput("game.contract.json phải là object")
    try:
        validate_tuning(c.get("tuning"))
    except (TypeError, KeyError, ValueError, AttributeError, IndexError) as e:
        raise BadInput(f"tuning sai kiểu/thiếu khóa: {e!r}")
    return c


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if (not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos)):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_gather(g):
    """Dải hợp lệ P1 theo PRD mục 13.2."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or set(fy) != {"ca_linh", "ca_loc", "ca_keo"}:
        raise BadInput("tuning.gather.fish_yield phải có đủ ca_linh, ca_loc, ca_keo")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    plants = ("bong_dien_dien", "bong_sung", "keo_neo")
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in plants:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {plants}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != set(plants):
        raise BadInput(f"tuning.gather.nodes phải có ít nhất một nút mỗi loại {plants}")
    # v1.1: cá bơi/sinh theo dữ liệu
    _int_between("gather.fish_initial", g.get("fish_initial"), 0, 30)
    _int_between("gather.fish_max", g.get("fish_max"), 1, 30)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_speed", g.get("fish_speed"), 0, 10)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    _range("gather.fish_x", g.get("fish_x"), b["x"])
    sx = g.get("fish_spawn_x")
    if not isinstance(sx, list) or not sx or not all(_num(x) and b["x"][0] <= x <= b["x"][1] for x in sx):
        raise BadInput("tuning.gather.fish_spawn_x phải là mảng x trong vùng nước")
    for key in ("fish_depths", "fish_spawn_depths", "fish_weights"):
        m = g.get(key)
        if not isinstance(m, dict) or set(m) != set(fy):
            raise BadInput(f"tuning.gather.{key} phải có đủ các loài trong fish_yield")
    for k in fy:
        _range(f"gather.fish_depths.{k}", g["fish_depths"][k], b["d"])
        ds = g["fish_spawn_depths"][k]
        if not isinstance(ds, list) or not ds or not all(_num(d) and b["d"][0] <= d <= b["d"][1] for d in ds):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là mảng độ sâu trong vùng nước")
        _between(f"gather.fish_weights.{k}", g["fish_weights"][k], 0, 1)
    _validate_monsters(g.get("monsters"), b)


def _range(name, r, outer):
    if not (isinstance(r, list) and len(r) == 2 and all(_num(c) for c in r) and r[0] <= r[1]
            and outer[0] <= r[0] and r[1] <= outer[1]):
        raise BadInput(f"tuning.{name} phải là [lo, hi] trong {outer}")


def _validate_monsters(mon, b):
    if not isinstance(mon, dict) or not isinstance(mon.get("species"), dict) or not isinstance(mon.get("spawns"), list):
        raise BadInput("tuning.gather.monsters phải có species và spawns")
    for k, sp in mon["species"].items():
        if not isinstance(sp, dict):
            raise BadInput(f"tuning.gather.monsters.species.{k} phải là object")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"gather.monsters.species.{k}.{key}", sp.get(key), 0, 100)
        _int_between(f"gather.monsters.species.{k}.recoil_ticks", sp.get("recoil_ticks"), 1, 100_000)
        _range(f"gather.monsters.species.{k}.depths", sp.get("depths"), b["d"])
    seen = set()
    for m in mon["spawns"]:
        if not isinstance(m, dict) or not isinstance(m.get("id"), str) or m["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi con cần id duy nhất")
        seen.add(m["id"])
        if m.get("kind") not in mon["species"]:
            raise BadInput(f"tuning.gather.monsters.spawns.{m['id']}: kind lạ")
        _pos_in(f"gather.monsters.{m['id']}.pos", m.get("pos"), b, ("x", "d"))
        wps = m.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"tuning.gather.monsters.spawns.{m['id']}.waypoints phải có 2 điểm")
        for w in wps:
            _pos_in(f"gather.monsters.{m['id']}.waypoints", w, b, ("x", "d"))
        _int_between(f"gather.monsters.{m['id']}.from_day", m.get("from_day"), 1, 100)
    _int_between("gather.monsters.invuln_ticks", mon.get("invuln_ticks"), 0, 100_000)
    _between("gather.monsters.loss_ratio", mon.get("loss_ratio"), 0, 1)


def _validate_day_shop(t):
    menu = t["menu"]
    plans = t.get("day_plan")
    if not isinstance(plans, list) or len(plans) != 5:
        raise BadInput("tuning.day_plan phải là mảng 5 Ngày")
    for i, p in enumerate(plans):
        if not isinstance(p, dict) or p.get("day") != i + 1:
            raise BadInput(f"tuning.day_plan[{i}].day phải là {i + 1}")
        dishes, ingr = p.get("dishes"), p.get("ingredients")
        if not isinstance(dishes, dict) or not dishes or not isinstance(ingr, dict):
            raise BadInput(f"tuning.day_plan[{i}] cần dishes và ingredients")
        want = {}
        for d, n in dishes.items():
            if d not in menu:
                raise BadInput(f"tuning.day_plan[{i}]: món lạ {d}")
            _int_between(f"day_plan[{i}].dishes.{d}", n, 1, 100)
            for k, q in menu[d]["recipe"].items():
                want[k] = want.get(k, 0) + q * n
        if ingr != want:
            raise BadInput(f"tuning.day_plan[{i}].ingredients phải bằng tổng công thức × số suất")
    shop = t.get("shop")
    if not isinstance(shop, dict) or not isinstance(shop.get("upgrades"), dict):
        raise BadInput("tuning.shop phải có upgrades")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 100_000)
    value_key = {"oxygen": "oxygen_max_s", "hp": "hp_max"}
    if set(shop["upgrades"]) != set(value_key):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    for k, levels in shop["upgrades"].items():
        if not isinstance(levels, list) or not levels:
            raise BadInput(f"tuning.shop.upgrades.{k} phải là mảng cấp")
        for i, lv in enumerate(levels):
            if not isinstance(lv, dict) or lv.get("level") != i + 1:
                raise BadInput(f"tuning.shop.upgrades.{k}[{i}].level phải là {i + 1}")
            _int_between(f"shop.upgrades.{k}[{i}].price", lv.get("price"), 1, 10**9)
            v = lv.get(value_key[k])
            if k == "hp":
                _int_between(f"shop.upgrades.hp[{i}].hp_max", v, 1, 99)
            else:
                _between(f"shop.upgrades.oxygen[{i}].oxygen_max_s", v, 10, 120)


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ P1 (PRD mục 13.2)
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null (mở rộng burn chưa bật)")
    qb = q["bounds"]
    _pos_in("quan.start_pos", q.get("start_pos"), qb, ("x", "z"))
    for name in ("stoves", "tables"):
        arr = q.get(name)
        if not isinstance(arr, list) or not arr:
            raise BadInput(f"tuning.quan.{name} phải là mảng không rỗng")
        seen = set()
        for e in arr:
            if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"] or e["id"] in seen:
                raise BadInput(f"tuning.quan.{name}: mỗi phần tử cần id duy nhất (chuỗi khác rỗng)")
            seen.add(e["id"])
            _pos_in(f"quan.{name}.{e['id']}.pos", e.get("pos"), qb, ("x", "z"))
    _int_between("quan.carry_limit", q.get("carry_limit"), 1, 99)
    rmin, rmax = q.get("reputation_min"), q.get("reputation_max")
    if not (_num(rmin) and _num(rmax) and rmin < rmax):
        raise BadInput("tuning.quan.reputation_min phải < reputation_max")
    _between("quan.reputation_initial", q.get("reputation_initial"), rmin, rmax)
    if not menu:
        raise BadInput("tuning.menu không được rỗng")
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        recipe = d.get("recipe")
        if not isinstance(recipe, dict) or not recipe:
            raise BadInput(f"menu.{dish_id}.recipe phải là object không rỗng")
        for k, v in recipe.items():
            if k not in KINDS or isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                raise BadInput(f"menu.{dish_id}.recipe.{k}: nguyên liệu trong danh mục, số lượng nguyên > 0")
    _validate_day_shop(t)
