# Phase 1 — tóm tắt chạy xuyên suốt gather → kho → quan

Kịch bản giống `tests/test_p1_integration.py::test_gather_to_quan_full_service`
(đầu ra thật, chỉ bỏ các dòng `meta`/snapshot; đường dẫn tạm đã rút gọn).

- gather (chơi thật, không scenario): từ bến [2, 0] bơi tới nút N1 [12, 0] hái điên điển → bơi tới trên đàn F2 (cá lóc) [30, 10]
  → lặn xuống bắt → ngoi lên → bơi về bến, bấm `interact` → cập bến, xuất kho.
- quan: đọc kho đó (chỉ đủ nấu `ca_loc_nuong_trui`), Út Sen đứng ở bếp B1, ca dài 1400 tick;
  khách đến tick 120 → nấu → bưng → sang bàn T1 → giao.
- Kỳ vọng: tip = round(60 × 0.2) = 12 (phục vụ khi kiên nhẫn còn > 50%), uy tín 3.0 + 0.2 = 3.2,
  score = earned + 100 × floor(reputation) = 72 + 300 = 372; kho cuối còn `{"bong_dien_dien": 1}`.

```text
$ python3 -m chonoi.headless --mode gather --seed 3 --ticks 2000 --inputs g_in.json --inventory-out inv.json --out g.jsonl
$ python3 -m chonoi.headless --mode quan --seed 3 --ticks 1500 --inventory inv.json --scenario q_sc.json --inputs q_in.json --out q.jsonl
```

**Sự kiện gather + dòng end** (g.jsonl):
```json
{"type":"event","tick":161,"phase":"gather","name":"gather","data":{"node_id":"N1","kind":"bong_dien_dien","count":1,"hold_count":1}}
{"type":"event","tick":446,"phase":"gather","name":"dive","data":{"pos":[30.2,0.567]}}
{"type":"event","tick":596,"phase":"gather","name":"fish_caught","data":{"fish_id":"F2","kind":"ca_loc","count":1,"hold_count":2}}
{"type":"event","tick":746,"phase":"gather","name":"surface","data":{"pos":[30.2,0.433]}}
{"type":"event","tick":1211,"phase":"gather","name":"gather_end","data":{"reason":"docked","inventory":{"items":{"bong_dien_dien":1,"ca_loc":1}}}}
{"type":"end","ticks":1211,"sim_tick":1211,"mode":"gather","state":"finished","reason":"docked","money":0,"earned":0,"reputation":3.0,"score":300}
```

**inv.json**:
```json
{"items":{"bong_dien_dien":1,"ca_loc":1}}
```

**Sự kiện quán + dòng end** (q.jsonl):
```json
{"type":"event","tick":120,"phase":"quan","name":"customer_arrived","data":{"customer_id":"C1","table_id":"T1","dish_id":"ca_loc_nuong_trui"}}
{"type":"event","tick":126,"phase":"quan","name":"cook_started","data":{"stove_id":"B1","dish_id":"ca_loc_nuong_trui","customer_id":"C1"}}
{"type":"event","tick":486,"phase":"quan","name":"dish_ready","data":{"stove_id":"B1","dish_id":"ca_loc_nuong_trui"}}
{"type":"event","tick":501,"phase":"quan","name":"dish_picked","data":{"stove_id":"B1","dish_id":"ca_loc_nuong_trui"}}
{"type":"event","tick":721,"phase":"quan","name":"served","data":{"table_id":"T1","customer_id":"C1","dish_id":"ca_loc_nuong_trui","price":60,"tip":12}}
{"type":"event","tick":1321,"phase":"quan","name":"paid","data":{"customer_id":"C1","table_id":"T1","dish_id":"ca_loc_nuong_trui","price":60,"tip":12,"money":72,"reputation":3.2}}
{"type":"event","tick":1400,"phase":"quan","name":"quan_end","data":{"reason":"time","money":72,"earned":72,"shift_earned":72,"reputation":3.2}}
{"type":"end","ticks":1400,"sim_tick":1400,"mode":"quan","state":"finished","reason":"time","money":72,"earned":72,"reputation":3.2,"score":372}
```
