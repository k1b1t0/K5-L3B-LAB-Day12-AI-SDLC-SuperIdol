# Quán Ăn Chợ Nổi — v1.0.0

## Điểm mới
- Vòng Ngày: lặn bắt cá, hái rau → nấu ăn, phục vụ khách → mua nâng cấp.
- Cá bơi, Cá Sấu, máu, oxy, hai bếp, pause và Shop (contract 1.1).
- Kho cá thể, hao độ tươi, hàng ươn và giá món theo độ tươi (contract 1.2).
- Contract 1.3 bổ sung benchmark có render và soak headless nhiều Ngày.
- Cảnh báo bằng chữ/ký hiệu cho oxy thấp, thủy quái gần và khách sắp giận; phím H bật tương phản cao.
- Canvas và âm thanh tổng hợp bằng Web Audio; các hiệu ứng chỉ chạy trên live client.

## Chạy
Python 3.10+; game và test chỉ dùng thư viện chuẩn. Xem [README](../README.md) để cài môi trường Windows.

```bash
python3 -m chonoi.live --mode day
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

## Giới hạn đã biết
- Bench cần Chrome, Chromium hoặc Edge; đặt `CHONOI_BROWSER` nếu không tự tìm được. Kết quả phụ thuộc máy, trình duyệt và tải nền. Unit test chỉ kiểm công thức, không thay thế bench thật.
- Bot soak chỉ hái rau, không bắt cá: doanh thu những Ngày sau có thể thấp. Soak kiểm hoàn thành đủ Ngày, không crash và tất định; không chứng minh mọi chiến thuật chơi đều đúng.
- `duration_s` là thời gian thực, phải bỏ trường này khi so kết quả soak cùng seed.
- HUD/cảnh báo có bằng chứng ảnh và kiểm tay; chưa có bộ test giao diện tự động đầy đủ.
- Kho dạng đếm cũ không tương thích contract 1.2/1.3; dùng mảng `{id,kind,fresh}`.

## Bằng chứng và phát hành
Xem [ma trận Phase 4](verification/phase-4.md). Chỉ gắn `phase-4` và `v1.0.0` vào cùng commit sau khi kiểm chứng trên `main`; không dùng báo cáo nhánh thay cho bước này.
