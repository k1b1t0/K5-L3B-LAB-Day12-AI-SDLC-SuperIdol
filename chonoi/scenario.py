"""Nạp và kiểm scenario (Contract D + Ticket-02 4.3, v1.1).

gather/quan: trả về khối đúng mode. day: trả {"day":..., "gather":..., "quan":...} (gather/quan là mẫu mỗi Ngày).
Mọi lỗi cú pháp, kiểu, miền, liên kết hay mâu thuẫn -> BadInput (mã 2), kiểm TRƯỚC khi ghi đầu ra.
Kiểm phụ thuộc kho thực (giữ chỗ vượt kho) nằm ở QuanSim lúc dựng: quán độc lập vẫn trước khi ghi đầu ra,
day thì lúc mở quán.
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
STOVE_STATES = ("idle", "cooking", "ready")
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
MONSTER_STATES = ("patrol", "chase", "recoil")


def ticks(s):
    return int(round(s * 60))


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    try:
        return _validate(data, mode, tuning)
    except (TypeError, KeyError, ValueError, AttributeError, IndexError) as e:  # lưới an toàn: không bao giờ Traceback
        raise BadInput(f"scenario sai kiểu/thiếu trường: {e!r}")


def _validate(data, mode, tuning):
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object")
    allowed_roots = {"gather", "quan", "day"} if mode == "day" else {mode}
    extra = set(data) - allowed_roots
    if extra:
        raise BadInput(f"khối sai mode / lạ với --mode {mode}: {sorted(extra)}")
    for k in data:
        if not isinstance(data[k], dict):
            raise BadInput(f"khối {k} phải là object")
    if "gather" in data:
        _validate_gather(data["gather"], tuning)
    if "quan" in data:
        _validate_quan(data["quan"], tuning, day_mode=(mode == "day"))
    if "day" in data:
        _validate_day(data["day"], tuning)
    if mode == "day":
        return {k: data.get(k, {}) for k in ("day", "gather", "quan")}
    return data.get(mode, {})


# --- tiện ích ------------------------------------------------------------------
def _num(v):
    # json.load nhận NaN/Infinity -> chặn ở đây, nếu không JSONL đầu ra sẽ không còn là JSON hợp lệ
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _int_in(name, v, lo, hi):
    if not _is_int(v) or not (lo <= v <= hi):
        raise BadInput(f"{name} phải là số nguyên trong [{lo}, {hi}]")


def _nonneg_int(name, v):
    if not _is_int(v) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _bool(name, v):
    if not isinstance(v, bool):
        raise BadInput(f"{name} phải là boolean")


def _keys(name, obj, allowed):
    if not isinstance(obj, dict):
        raise BadInput(f"{name} phải là object")
    extra = set(obj) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {name}: {sorted(extra)}")


def _vec(name, v):
    if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v)):
        raise BadInput(f"{name} phải là [số, số] hữu hạn")


def _pos(name, pos, bounds, axes):
    _vec(name, pos)
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài miền ({axis} ∈ [{lo}, {hi}])")


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def _time_left(b, dur, name):
    if "time_left_ticks" in b:
        _int_in(f"{name}.time_left_ticks", b["time_left_ticks"], 1, dur)


# --- gather ----------------------------------------------------------------------
def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    _keys("gather", b, GATHER_KEYS)
    _time_left(b, ticks(g["duration_s"]), "gather")
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b:
        _bool("random_fish", b["random_fish"])
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(not isinstance(k, str) or k not in KINDS for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    _keys("gather.player", p, GATHER_PLAYER_KEYS)
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds, ("x", "d"))
    if "vel" in p:
        _vec("player.vel", p["vel"])
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    omax = ticks(g["oxygen_max_s"])
    if "oxygen_ticks" in p:
        _int_in("player.oxygen_ticks", p["oxygen_ticks"], 0, omax)
    if "hp" in p:
        _int_in("player.hp", p["hp"], 1, g["hp_max"])
    _int_in_opt(p, "catch_cd_ticks", 0, ticks(g["catch_cooldown_s"]), "player")
    _int_in_opt(p, "invuln_ticks", 0, int(g["monsters"]["invuln_ticks"]), "player")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        _int_in("player.zero_oxy_ticks", p["zero_oxy_ticks"], 0, int(g["choke_interval_ticks"]) - 1)
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    node_kinds = {n["kind"] for n in g["nodes"]}
    for n in b.get("nodes", []):
        name = f"nodes.{n['id']}"
        _keys(name, n, {"id", "kind", "pos", "regrow_ticks"})
        if n.get("kind") not in node_kinds:
            raise BadInput(f"{name}: kind phải là một trong {sorted(node_kinds)}")
        _pos(f"{name}.pos", n.get("pos"), bounds, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"{name}: nút hái nằm ở mặt nước (d = 0)")
        _int_in_opt(n, "regrow_ticks", 0, ticks(g["regrow_s"]), name)
    for f in b.get("fish", []):
        name = f"fish.{f['id']}"
        _keys(name, f, {"id", "kind", "pos", "heading_deg", "age_ticks"})
        if f.get("kind") not in g["fish_yield"]:
            raise BadInput(f"{name}: kind phải là một trong {sorted(g['fish_yield'])}")
        _pos(f"{name}.pos", f.get("pos"), bounds, ("x", "d"))
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"{name}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"{name}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"{name}.age_ticks", f["age_ticks"])
    mon = g["monsters"]
    for m in b.get("monsters", []):
        name = f"monsters.{m['id']}"
        _keys(name, m, MONSTER_KEYS)
        sp = mon["species"].get(m.get("kind")) if isinstance(m.get("kind"), str) else None
        if sp is None:
            raise BadInput(f"{name}: kind phải là một trong {sorted(mon['species'])}")
        _pos(f"{name}.pos", m.get("pos"), bounds, ("x", "d"))
        wps = m.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"{name}.waypoints phải có đúng 2 điểm")
        for i, w in enumerate(wps):
            _pos(f"{name}.waypoints[{i}]", w, bounds, ("x", "d"))
        if "target_idx" in m and (isinstance(m["target_idx"], bool) or m["target_idx"] not in (0, 1)):
            raise BadInput(f"{name}.target_idx phải là 0 hoặc 1")
        state = m.get("state", "patrol")
        if state not in MONSTER_STATES:
            raise BadInput(f"{name}.state phải là một trong {MONSTER_STATES}")
        left = m.get("state_ticks_left", 0)
        rdir = m.get("recoil_dir")
        if state == "recoil":
            _int_in(f"{name}.state_ticks_left", left, 1, int(sp["recoil_ticks"]))
            _vec(f"{name}.recoil_dir", rdir)
            if abs(math.hypot(*rdir) - 1) > 1e-6:
                raise BadInput(f"{name}.recoil_dir phải là vector đơn vị")
        else:
            _int_in(f"{name}.state_ticks_left", left, 0, 0)
            if rdir is not None:
                raise BadInput(f"{name}.recoil_dir chỉ khai khi recoil")


def _int_in_opt(obj, key, lo, hi, name):
    if key in obj:
        _int_in(f"{name}.{key}", obj[key], lo, hi)


# --- quan --------------------------------------------------------------------------
def _dish_payload(name, d, menu):
    _keys(name, d, {"order_id", "dish_id", "base_price"})
    if set(d) != {"order_id", "dish_id", "base_price"}:
        raise BadInput(f"{name} phải có order_id, dish_id, base_price")
    if not isinstance(d["order_id"], str) or not d["order_id"]:
        raise BadInput(f"{name}.order_id phải là chuỗi khác rỗng")
    if not isinstance(d["dish_id"], str) or d["dish_id"] not in menu:
        raise BadInput(f"{name}.dish_id phải là món trong menu")
    _nonneg_int(f"{name}.base_price", d["base_price"])


def _validate_quan(b, tuning, day_mode=False):
    q, menu = tuning["quan"], tuning["menu"]
    _keys("quan", b, QUAN_KEYS)
    if day_mode:
        for k in ("stock", "reputation"):
            if k in b:
                raise BadInput(f"quan.{k} bị cấm khi chạy day (dùng gather.hold / day.reputation)")
    _time_left(b, ticks(q["duration_s"]), "quan")
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    _keys("quan.player", p, {"pos", "vel"})
    qb = q["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, ("x", "z"))
    if "vel" in p:
        _vec("player.vel", p["vel"])
    if "random_customers" in b:
        _bool("random_customers", b["random_customers"])
    if "reputation" in b and not (_num(b["reputation"])
                                  and q["reputation_min"] <= b["reputation"] <= q["reputation_max"]):
        raise BadInput(f"reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    stove_ids = {s["id"] for s in q["stoves"]}
    table_ids = {t["id"] for t in q["tables"]}
    for tb in b.get("tables", []):
        _keys(f"tables.{tb['id']}", tb, {"id", "pos"})
        if tb["id"] not in table_ids:
            raise BadInput(f"id bàn không tồn tại: {tb['id']}")
        if "pos" in tb:
            _pos(f"tables.{tb['id']}.pos", tb["pos"], qb, ("x", "z"))
    dishes = {}  # order_id -> (nơi, payload)
    hand = b.get("hand")
    if hand is not None:
        _dish_payload("hand", hand, menu)
        dishes[hand["order_id"]] = ("hand", hand)
    for s in b.get("stoves", []):
        name = f"stoves.{s['id']}"
        _keys(name, s, STOVE_KEYS)
        if s["id"] not in stove_ids:
            raise BadInput(f"id bếp không tồn tại: {s['id']}")
        if "pos" in s:
            _pos(f"{name}.pos", s["pos"], qb, ("x", "z"))
        _validate_stove(name, s, menu)
        if s.get("dish") is not None:
            oid = s["dish"]["order_id"]
            if oid in dishes:
                raise BadInput(f"{name}: bếp và tay (hoặc hai bếp) giữ cùng đơn {oid}")
            dishes[oid] = (name, s["dish"])
    customers = b.get("customers", [])
    seats = set()
    pmax, emax = ticks(q["patience_s"]), ticks(q["eat_s"])
    by_id = {}
    for c in customers:
        name = f"customers.{c['id']}"
        _keys(name, c, CUSTOMER_KEYS)
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in table_ids:
            raise BadInput(f"{name}: table_id phải là bàn có thật")
        if c["table_id"] in seats:
            raise BadInput("hai khách cùng bàn")
        seats.add(c["table_id"])
        if not isinstance(c.get("dish_id"), str) or c["dish_id"] not in menu:
            raise BadInput(f"{name}.dish_id phải là món có trong menu")
        state = c.get("state", "waiting")
        if state not in CUSTOMER_STATES:
            raise BadInput(f"{name}.state phải là một trong {CUSTOMER_STATES}")
        status = c.get("order_status", "reserved" if state == "waiting" else "served")
        if status not in ORDER_STATUSES:
            raise BadInput(f"{name}.order_status phải là một trong {ORDER_STATUSES}")
        if "order_tick" in c:
            _nonneg_int(f"{name}.order_tick", c["order_tick"])
        if "patience_ticks_left" in c:
            _int_in(f"{name}.patience_ticks_left", c["patience_ticks_left"], 0 if state == "eating" else 1, pmax)
        for k in ("base_price", "tip"):
            if c.get(k) is not None:
                _nonneg_int(f"{name}.{k}", c[k])
        if state == "eating":
            if status != "served":
                raise BadInput(f"{name}: khách đang ăn phải có order_status served")
            if not {"eat_ticks_left", "base_price", "tip"} <= set(c) or c["base_price"] is None or c["tip"] is None:
                raise BadInput(f"{name}: khách đang ăn phải khai eat_ticks_left, base_price, tip")
            _int_in(f"{name}.eat_ticks_left", c["eat_ticks_left"], 1, emax)
        else:
            if status == "served":
                raise BadInput(f"{name}: đơn served thì khách phải đang ăn")
            if c.get("eat_ticks_left", 0) != 0:
                raise BadInput(f"{name}: khách chờ thì eat_ticks_left phải bằng 0")
        if "reserved" in c and c["reserved"] is not None:
            held = validate_items(c["reserved"])
            if status != "reserved":
                if held:
                    raise BadInput(f"{name}: chỉ đơn reserved mới giữ chỗ nguyên liệu")
            elif held != menu[c["dish_id"]]["recipe"]:
                raise BadInput(f"{name}: reserved phải đúng công thức món {c['dish_id']}")
        has_dish = c["id"] in dishes
        if status == "assigned":
            if not has_dish or dishes[c["id"]][1]["dish_id"] != c["dish_id"]:
                raise BadInput(f"{name}: đơn assigned phải có đúng một món khớp ở bếp hoặc tay")
        elif has_dish:
            raise BadInput(f"{name}: chỉ đơn assigned mới có món ở bếp/tay")
        by_id[c["id"]] = c
    for oid, (where, d) in dishes.items():
        if oid not in by_id:
            raise BadInput(f"{where}: món trỏ tới đơn {oid} không tồn tại")


def _validate_stove(name, s, menu):
    state = s.get("state", "idle")
    if state not in STOVE_STATES:
        raise BadInput(f"{name}.state phải là một trong {STOVE_STATES}")
    for key in ("cook_ticks_left", "ready_ticks"):
        if key in s:
            _nonneg_int(f"{name}.{key}", s[key])
    dish, cook, ready = s.get("dish"), s.get("cook_ticks_left", 0), s.get("ready_ticks", 0)
    if state == "idle":
        if dish is not None or cook or ready:
            raise BadInput(f"{name}: bếp idle không có món và bộ đếm phải bằng 0")
        return
    if dish is None:
        raise BadInput(f"{name}: bếp {state} phải có món")
    _dish_payload(f"{name}.dish", dish, menu)
    if state == "cooking":
        _int_in(f"{name}.cook_ticks_left", cook, 1, ticks(menu[dish["dish_id"]]["cook_s"]))
        if ready:
            raise BadInput(f"{name}: bếp đang nấu thì ready_ticks phải bằng 0")
    elif cook:
        raise BadInput(f"{name}: bếp ready thì cook_ticks_left phải bằng 0")


# --- day -----------------------------------------------------------------------------
def _validate_day(d, tuning):
    _keys("day", d, DAY_KEYS)
    q, menu = tuning["quan"], tuning["menu"]
    for k in ("money", "earned"):
        if k in d:
            _nonneg_int(f"day.{k}", d[k])
    money, earned = d.get("money", 0), d.get("earned", 0)
    if money > 0 and "earned" not in d:
        raise BadInput("day: khai money > 0 thì phải khai cả earned")
    if money > earned:
        raise BadInput("day: cần 0 ≤ money ≤ earned")
    if "reputation" in d and not (_num(d["reputation"])
                                  and q["reputation_min"] <= d["reputation"] <= q["reputation_max"]):
        raise BadInput(f"day.reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    ups = d.get("upgrades", {})
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là object")
    shop = tuning["shop"]["upgrades"]
    for k, v in ups.items():
        if k not in shop:
            raise BadInput(f"day.upgrades: nâng cấp lạ {k}")
        _int_in(f"day.upgrades.{k}", v, 0, len(shop[k]))
    plans = d.get("day_plan", [])
    if not isinstance(plans, list):
        raise BadInput("day.day_plan phải là mảng")
    seen = set()
    for i, p in enumerate(plans):
        name = f"day.day_plan[{i}]"
        _keys(name, p, {"day", "dishes", "ingredients"})
        _int_in(f"{name}.day", p.get("day"), 1, 5)
        if p["day"] in seen:
            raise BadInput(f"{name}: trùng Ngày {p['day']}")
        seen.add(p["day"])
        dishes = p.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"{name}.dishes phải là object không rỗng")
        for dish, n in dishes.items():
            if dish not in menu:
                raise BadInput(f"{name}.dishes: món lạ {dish}")
            _int_in(f"{name}.dishes.{dish}", n, 1, 10**6)
        if "ingredients" in p:
            want = {}
            for dish, n in dishes.items():
                for k, qn in menu[dish]["recipe"].items():
                    want[k] = want.get(k, 0) + qn * n
            if validate_items(p["ingredients"]) != want:
                raise BadInput(f"{name}.ingredients không khớp tổng công thức × số suất")
