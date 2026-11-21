"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
Quán (nhóm thêm): random_customers, reputation, hand, trạng thái bếp nhất quán, khách (state, dish_id,
patience/eat trong dải, reserved đúng schema), khách eating phải có eat_ticks_left/price/tip,
đơn assigned_stove khớp đúng một món ở bếp đang nấu/chín, tổng giữ chỗ không vượt kho
(quan.stock, hoặc kho --inventory qua check_reserved_fits gọi từ headless).
Phase 2: mọi số phải hữu hạn (không NaN/Infinity), bộ đếm gather không vượt mức tối đa theo tuning,
khách đã giao bếp / đang ăn không còn giữ chỗ.
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung")
FISH_KINDS = ("ca_linh", "ca_loc")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
STOVE_STATES = ("idle", "cooking", "ready")
CUSTOMER_STATES = ("waiting", "eating")


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


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _num(v):
    # json.load nhận NaN/Infinity -> chặn ở đây, nếu không JSONL đầu ra sẽ không còn là JSON hợp lệ
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS_P1 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    cd_max = int(round(g["catch_cooldown_s"] * 60))
    if "catch_cd_ticks" in p and p["catch_cd_ticks"] > cd_max:
        raise BadInput(f"player.catch_cd_ticks phải trong [0, {cd_max}]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        zmax = int(g["choke_interval_ticks"]) - 1
        if p["zero_oxy_ticks"] > zmax:
            raise BadInput(f"player.zero_oxy_ticks phải trong [0, {zmax}]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _int_in(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"], 0, int(round(g["regrow_s"] * 60)))
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    q, menu = tuning["quan"], tuning["menu"]
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b and not (_num(b["reputation"])
                                  and q["reputation_min"] <= b["reputation"] <= q["reputation_max"]):
        raise BadInput(f"reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    if b.get("hand") is not None and not (isinstance(b["hand"], str) and b["hand"] in menu):
        raise BadInput("hand phải là null hoặc id món có trong menu")
    for s in b.get("stoves", []):
        _validate_stove(s, menu)
    stoves = {s["id"]: s for s in b.get("stoves", [])}
    assigned, reserved = set(), {}
    pmax = int(round(q["patience_s"] * 60))
    emax = int(round(q["eat_s"] * 60))
    for c in b.get("customers", []):
        name = f"customers.{c['id']}"
        state = c.get("state", "waiting")
        if state not in CUSTOMER_STATES:
            raise BadInput(f"{name}.state phải là một trong {CUSTOMER_STATES}")
        if c.get("dish_id") not in menu:
            raise BadInput(f"{name}.dish_id phải là món có trong menu")
        if state == "waiting" and "patience_ticks_left" in c:
            _int_in(f"{name}.patience_ticks_left", c["patience_ticks_left"], 1, pmax)
        if state == "eating":
            if not {"eat_ticks_left", "price", "tip"} <= set(c):
                raise BadInput(f"{name}: khách đang ăn phải có eat_ticks_left, price, tip")
            _int_in(f"{name}.eat_ticks_left", c["eat_ticks_left"], 1, emax)
            _int_in(f"{name}.price", c["price"], 1, 10**9)
            _nonneg_int(f"{name}.tip", c["tip"])
        if "assigned_stove" in c:
            sid, st = c["assigned_stove"], stoves.get(c["assigned_stove"])
            if state != "waiting" or st is None or st.get("state") not in ("cooking", "ready") \
                    or st.get("dish") != c["dish_id"]:
                raise BadInput(f"{name}: đơn đã giao bếp phải khớp đúng một món đang nấu/chín ở bếp đó")
            if sid in assigned:
                raise BadInput(f"{name}: hai đơn cùng giao một bếp {sid}")
            assigned.add(sid)
        held = validate_items(c.get("reserved", {}))
        # quan.py xóa reserved khi bắt đầu nấu -> đơn đã giao bếp / khách đang ăn không còn giữ chỗ
        if any(held.values()) and (state == "eating" or "assigned_stove" in c):
            raise BadInput(f"{name}: khách đã giao bếp hoặc đang ăn không được giữ chỗ nguyên liệu")
    if "stock" in b:
        check_reserved_fits(b, b["stock"])


def check_reserved_fits(block, stock):
    """Tổng giữ chỗ của khách không vượt kho. Kho từ --inventory: headless gọi sau read_inventory."""
    reserved = {}
    for c in block.get("customers", []):
        for k, v in c.get("reserved", {}).items():
            reserved[k] = reserved.get(k, 0) + v
    over = sorted(k for k, v in reserved.items() if v > stock.get(k, 0))
    if over:
        raise BadInput(f"khách giữ chỗ vượt kho: {over}")


def _int_in(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"{name} phải là số nguyên trong [{lo}, {hi}]")


def _validate_stove(s, menu):
    name = f"stoves.{s['id']}"
    state = s.get("state", "idle")
    if state not in STOVE_STATES:
        raise BadInput(f"{name}.state phải là một trong {STOVE_STATES}")
    for key in ("cook_ticks_left", "ready_ticks"):
        if key in s:
            _nonneg_int(f"{name}.{key}", s[key])
    dish, cook = s.get("dish"), s.get("cook_ticks_left", 0)
    if state == "idle":
        if dish is not None or cook or s.get("ready_ticks", 0):
            raise BadInput(f"{name}: bếp idle không có món và bộ đếm phải bằng 0")
        return
    if dish not in menu:
        raise BadInput(f"{name}.dish phải là món có trong menu khi bếp {state}")
    if state == "cooking":
        _int_in(f"{name}.cook_ticks_left", cook, 1, int(round(menu[dish]["cook_s"] * 60)))
        if s.get("ready_ticks", 0):
            raise BadInput(f"{name}: bếp đang nấu thì ready_ticks phải bằng 0")
    elif cook:
        raise BadInput(f"{name}: bếp ready thì cook_ticks_left phải bằng 0")
