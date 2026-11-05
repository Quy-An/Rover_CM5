# Motor PID Tuner — STM32 Robot Control App

Ứng dụng Python + PyQt5 để tuning PID realtime cho robot vi sai điều khiển bằng STM32.

## Tính năng

- ✅ Giao diện PyQt5 hiện đại
- ✅ Điều khiển realtime: vx (tốc độ tuyến tính), ω (tốc độ góc)
- ✅ Tuning PID: thay đổi Kp, Ki, Kd cho mỗi motor
- ✅ Đồ thị realtime: setpoint vs tốc độ thực tế (2 subplot)
- ✅ Auto-send: gửi lệnh định kỳ 100ms
- ✅ Log chi tiết: ghi lại mọi lệnh & phản hồi

## Yêu cầu

- Python 3.10+
- STM32 chạy firmware có hỗ trợ UART protocol (vx, omega)

## Cài đặt

### 1. Clone hoặc tải source code

```bash
git clone <repo> motor_pid_tuner
cd motor_pid_tuner
```

### 2. Tạo virtual environment (khuyên dùng)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài thư viện

```bash
pip install -r requirements.txt
```

Hoặc cài thủ công:
```bash
pip install pyserial matplotlib PyQt5 numpy
```

## Chạy ứng dụng

```bash
python main.py
```

Hoặc qua VS Code:
```
Press F5 hoặc Ctrl+F5
```

## Hướng dẫn sử dụng

### 1. Kết nối STM32

1. Chọn cổng COM từ dropdown
2. Nhấn nút "Kết nối"
3. Nếu thành công → trạng thái chuyển sang xanh "Đã kết nối"

### 2. Điều khiển Robot

- **vx slider (mm/s):** -200 đến +200 (dương = tiến)
- **ω slider (mrad/s):** -300 đến +300 (dương = quay trái)
- Nhấn "Gửi (vx, ω)" để gửi lệnh
- Tick "Auto-send (100ms)" để gửi định kỳ

### 3. Tuning PID

1. Nhập giá trị Kp, Ki, Kd cho Motor Trái
2. Nhấn "Apply Motor L"
3. Lặp lại cho Motor Phải
4. Quan sát đồ thị realtime để kiểm tra đáp ứng

**Hướng dẫn chỉnh tham số:**

- **Kp (tỉ lệ):** Tăng để motor bám target nhanh hơn, nhưng cẩn thận không để dao động
- **Ki (tích phân):** Triệt sai số steady-state, nhưng tăng quá sẽ gây overshoot
- **Kd (vi phân):** Chống overshoot, nhưng tăng quá sẽ gây rung động

### 4. Quan sát đồ thị

- **Xanh:** Setpoint (mong muốn)
- **Đỏ:** Actual (tốc độ thực tế từ encoder)
- Mục tiêu: Đường đỏ theo sát đường xanh, mịn không rung động

## Cấu trúc file

```
motor_pid_tuner/
├── main.py                # Entry point
├── ui.py                  # Giao diện PyQt5
├── serial_handler.py      # Xử lý UART
├── pid_tuner.py           # Logic kinematics + data recorder
├── config.py              # Cấu hình protocol & thông số
├── requirements.txt       # Danh sách thư viện
└── README.md             # Hướng dẫn này
```

## Protocol UART

### Frame điều khiển (PC → STM32)
```
[0xAA] [vx_H] [vx_L] [omega_H] [omega_L] [CRC]
  Byte  int16         int16
```

### Frame PID params (PC → STM32)
```
[0xAC] [Kp×10_H] [Kp×10_L] [Ki×10_H] [Ki×10_L] [Kd×10_H] [Kd×10_L] [motor_id] [CRC]
  Byte   int16               int16               int16              0/1
```

### Frame feedback (STM32 → PC)
```
[0xBB] [E1H] [E1L] [E2H] [E2L] [CRC]
  Byte  int16       int16
```

## Cấu hình (config.py)

Chỉnh các thông số sau nếu cần:

```python
WHEEL_RADIUS = 0.0225    # Bán kính bánh xe (mét) — ĐO LẠI THỰC TẾ
TRACK_WIDTH = 0.15       # Khoảng cách 2 bánh (mét) — ĐO LẠI THỰC TẾ
PPR = 330.0              # Xung encoder / vòng
MAX_PULSE_20MS = 154.0   # Tốc độ max (xung/20ms)

DEFAULT_KP = 1.5         # Giá trị PID mặc định
DEFAULT_KI = 0.1
DEFAULT_KD = 0.05
```

## Troubleshooting

### Lỗi: "ModuleNotFoundError: No module named 'PyQt5'"

→ Chưa cài PyQt5:
```bash
pip install PyQt5
```

### Lỗi: "Could not open port COM3"

→ STM32 chưa kết nối hoặc driver UART thiếu
- Kiểm tra kết nối USB
- Cài driver CH340/CP2102 nếu cần
- Thử refresh danh sách port

### Đồ thị không cập nhật

→ Không nhận được feedback từ STM32
- Kiểm tra STM32 có gửi frame [0xBB] không
- Kiểm tra baud rate (mặc định 115200)

### Hộp thoại "The requested serial port does not exist" khi kết nối

→ Port đã đóng hoặc số COM sai
- Tắt app
- Rút USB-UART, chắc chắn device offline
- Cắm lại USB
- Chọn port mới trong app

## Phát triển tiếp

### Các tính năng có thể thêm:

1. **PID Auto-tuning:** Tự tính Kp/Ki/Kd dựa trên đáp ứng
2. **Save/Load Profile:** Lưu tập hợp PID params vào file
3. **Multi-motor sync:** Tuning đồng thời 2 motor
4. **Data export:** Xuất dữ liệu đồ thị ra CSV/PNG
5. **Hardware sync:** Đảm bảo đủ 20ms tính toán động học

## Giấy phép

MIT

## Liên hệ

Có vấn đề? Tạo Issue hoặc Pull Request!