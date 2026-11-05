# Rover1 Autonomous Ground Vehicle

## Mục tiêu dự án

`Rover1` là một hệ thống rover tự hành trên nền Raspberry Pi/Python, thiết kế để:
- Điều khiển trực tiếp hai động cơ trái/phải qua GPIO.
- Thu thập dữ liệu IMU, GPS và LiDAR để điều hướng và báo cáo trạng thái.
- Truyền video từ camera Pi đến laptop bằng GStreamer.
- Kết nối với QGroundControl qua MAVLink để điều khiển từ xa và lập kế hoạch waypoint.
- Chạy đồng thời nhiều tiến trình và luồng để tách biệt nhiệm vụ cảm biến, điều khiển và liên lạc.

## Kiến trúc tổng quan

Dự án bao gồm các thành phần chính sau:

### 1. `main.py`
- Khởi động ứng dụng và nạp `config.yaml`.
- Tạo `SharedMemory` tên `Lidar_SHM` để chia sẻ dữ liệu quét LiDAR giữa tiến trình LiDAR và luồng MAVLink.
- Khởi tạo các tiến trình (`multiprocessing.Process`) và luồng (`threading.Thread`):
  - `tasks.control.tien_trinh_tinh_toan`
  - `tasks.mavlink.luong_chay_mavlink`
  - `tasks.sensor.lidar_task`
  - `tasks.sensor.imu_task`
  - `tasks.sensor.gps_task`
  - `tasks.video.video_task`
- Thiết lập bắt tín hiệu Ctrl+C và SIGTERM để tắt hệ thống an toàn.

### 2. `config.yaml`
- Chứa cấu hình phần cứng, tham số an toàn, cấu hình video và thông tin kết nối MAVLink.
- Giúp tách cấu hình khỏi mã nguồn để dễ sửa đổi khi triển khai trên thiết bị khác.

### 3. `tasks/control.py`
- Định nghĩa mô hình nghịch đảo (`inverse_kinematics`) để từ vận tốc tiến và góc quay ra tốc độ bánh xe.
- Chuyển đổi tốc độ bánh xe thành mức PWM với `gpiozero.PWMLED` và `LED`.
- Nhận lệnh điều khiển từ QGroundControl thông qua hàng đợi `cmd_queue`.
- Kiểm tra `armed` để đảm bảo chỉ cho xe chạy khi được bật an toàn.

### 4. `tasks/mavlink.py`
- Quản lý giao tiếp MAVLink với QGroundControl bằng `pymavlink`.
- Gửi nhiều gói dữ liệu định kỳ:
  - `HEARTBEAT` (1Hz)
  - `GLOBAL_POSITION_INT` (10Hz)
  - `ATTITUDE` (10Hz)
  - `GPS_RAW_INT` (2.5Hz)
  - `OBSTACLE_DISTANCE` (10Hz)
  - `SYS_STATUS` (1Hz)
  - `BATTERY_STATUS` (1Hz)
- Nhận lệnh từ QGC để:
  - Arm/disarm rover
  - Bật/tắt camera
  - Bật/tắt LiDAR
  - Nhận và lưu waypoint mission
- Cập nhật trạng thái robot từ dữ liệu IMU và GPS.

### 5. `tasks/sensor.py`
- `imu_task`: đọc IMU MPU9250, tính toán quaternion và góc roll/pitch/yaw.
- `gps_task`: kết nối với GPS qua cổng serial, cấu hình GNSS, và đọc dữ liệu NMEA/UBX.
- `lidar_task`: quét LiDAR 180 độ phía trước, chuyển thành mảng khoảng cách 72 phần tử, cập nhật shared memory.
- `put_latest_to_queue`: đảm bảo chỉ giữ dữ liệu mới nhất trong hàng đợi.

### 6. `tasks/video.py`
- Chuyển đổi cấu hình video thành lệnh GStreamer.
- Khởi động/tắt luồng video dựa trên cờ `camera_active_event`.
- Truyền H.264 qua UDP đến laptop theo cấu hình trong `config.yaml`.

## Luồng dữ liệu và trạng thái

### Dữ liệu điều khiển
- QGroundControl gửi `MANUAL_CONTROL` hoặc `COMMAND_LONG`.
- `tasks/mavlink` chuyển đổi lệnh joystick thành vận tốc tiến `vx` và góc quay `wz`.
- Lệnh được đặt vào `cmd_queue` để `tasks/control` đọc.
- `tasks/control` tính PWM và điều khiển GPIO.

### Dữ liệu cảm biến
- IMU: đọc liên tục, gửi vào `q_imu_mavlink` và `q_imu_control`.
- GPS: đọc tọa độ, fix, HDOP/VDOP, gửi vào `q_gps_mavlink` và `q_gps_control`.
- LiDAR: đọc quét, ghi vào `SharedMemory`, luồng MAVLink đọc và gửi `OBSTACLE_DISTANCE`.

### Trạng thái bật/tắt
- `camera_active_event`: điều khiển bật/tắt luồng video.
- `lidar_active_event`: điều khiển bật/tắt quét LiDAR.
- `gps_ready_event`: báo GPS đã nhận đủ fix để Rover sẵn sàng.

## Chi tiết cấu hình (`config.yaml`)

### Hardware
- `motor_left_pwm`: chân PWM điều khiển tốc độ motor trái.
- `motor_left_dir`: chân GPIO điều khiển chiều tiến/lùi motor trái.
- `motor_right_pwm`: chân PWM điều khiển tốc độ motor phải.
- `motor_right_dir`: chân GPIO điều khiển chiều tiến/lùi motor phải.
- `lidar_serial_port`: cổng serial nối LiDAR, thường `/dev/ttyUSB0`.
- `lidar_baudrate`: tốc độ truyền LiDAR (115200).
- `lidar_motor_pwm`: giá trị PWM cho motor LiDAR.
- `gps_serial_port`: cổng GPS, thường `/dev/serial0`.
- `gps_baudrate`: tốc độ truyền GPS (9600).

### Safety
- `obstacle_threshold_min_mm`: khoảng cách tối thiểu phát hiện vật cản (200).
- `obstacle_threshold_max_mm`: ngưỡng cho điểm cuối mission (1200).
- `obstacle_threshold_unknown`: giá trị khi LiDAR không đo được khoảng cách (65535).

### Video
- `laptop_ip`: IP máy laptop nhận luồng video.
- `port`: cổng UDP của video stream.
- `width`, `height`: độ phân giải video.
- `framerate`: tốc độ khung hình.
- `rotation`: xoay camera.
- `format`: định dạng ảnh đầu vào cho GStreamer.

### MAVLink
- `laptop_ip`: IP laptop chạy QGroundControl.
- `udp_port`: cổng MAVLink, thường 14550.

## Phụ thuộc và cài đặt

### Python
Các thư viện yêu cầu trong `requirements.txt`:
- `pyyaml`
- `numpy`
- `pymavlink`
- `pyrplidar`
- `pyserial`
- `pyubx2`
- `imusensor`
- `requests`
- `gpiozero`
- `easydict`

### Hệ thống
`Dockerfile` cài đặt các gói hệ thống cần thiết cho Raspberry Pi / Debian:
- `python3`, `python3-pip`, `python3-dev`
- `python3-smbus`, `python3-lgpio`
- GStreamer và plugin cho encoding/streaming
- `libcamera-tools`, `gstreamer1.0-libcamera`
- `gpiod`, `libgpiod-dev`, `i2c-tools`, `libi2c-dev`
- `swig`

## Chạy dự án

### 1. Dùng Docker Compose
```bash
cd /home/pi/kltn/Rover1
docker compose build
docker compose up -d
```

### 2. Chạy trực tiếp (nếu không dùng Docker)
```bash
cd /home/pi/kltn/Rover1
python3 main.py
```

### 3. Kiểm tra trạng thái
- QGroundControl nên kết nối tới `udp://<laptop_ip>:14550`
- Luồng video đến laptop ở `udp://<laptop_ip>:5600`

## Kết nối qua Tailscale
- Kết nối an toàn giữa máy trạm và Pi5 qua Internet hoặc mạng khác lớp, dùng Tailscale để gán địa chỉ IP nội bộ riêng cho mỗi thiết bị.
- Cài đặt Tailscale trên cả Raspberry Pi 5 và máy laptop/PC/Phone.
- Khởi động Tailscale trên mỗi thiết bị và đăng nhập bằng cùng một tài khoản hoặc mạng Tailscale.
- Dùng địa chỉ Tailnet IP của laptop làm `laptop_ip` hoặc `phone_ip` trong `config.yaml` để QGroundControl và video stream tới đúng thiết bị.
- Ví dụ: `laptop_ip: "100.x.y.z"` khi đó Raspberry Pi sẽ gửi MAVLink và video qua UDP tới IP Tailscale của laptop.
- Tailscale đảm bảo kết nối mã hóa và có thể hoạt động trên các mạng NAT khác nhau mà không cần cấu hình port forwarding.

## Kết nối phần cứng chính

### GPIO motor
- Motor trái PWM: GPIO 0
- Motor trái DIR: GPIO 1
- Motor phải PWM: GPIO 2
- Motor phải DIR: GPIO 3

### GPS
- Kết nối GPS vào `/dev/serial0`.
- GPS được cấu hình ở 9600 baud.

### LiDAR
- Kết nối LiDAR vào `/dev/ttyUSB0`.
- Dữ liệu quét LiDAR được lưu vào shared memory 152 bytes.

### Camera
- Sử dụng `libcamera` qua GStreamer để xuất video UDP.

## Hành vi điều khiển

- Khi rover nhận lệnh arm, `tasks/control` cho phép truyền lệnh `vx`/`wz` vào hàm `inverse_kinematics`.
- Nếu QGC không gửi lệnh trong 0.04 giây, xe sẽ tự động dừng.
- Khi disarm, hệ thống lập tức dừng cả hai động cơ.

## MAVLink command IDs quan trọng

- `400` + `param1 = 1.0`: arm
- `400` + `param1 = 0.0`: disarm
- `2500`: bật camera
- `2501`: tắt camera
- `2510`: bật LiDAR
- `2511`: tắt LiDAR

## Ghi chú vận hành

- Cần có file hiệu chuẩn IMU tại `/home/pi/calib_mpu9250.json` nếu muốn dùng góc chính xác.
- QGroundControl phải dùng cùng `laptop_ip` và `udp_port` trong `config.yaml`.
- Container hoặc hệ thống cần quyền truy cập `/dev` và thiết bị GPIO.
- `docker-compose.yml` mount `/dev` và `/run/udev` để container nhận thiết bị vật lý.

## Cấu trúc thư mục

- `main.py`: entrypoint chính
- `config.yaml`: cấu hình dự án
- `requirements.txt`: thư viện Python
- `Dockerfile`: xây dựng container
- `docker-compose.yml`: chạy Docker Compose
- `tasks/`: mã nhiệm vụ xử lý cảm biến, điều khiển và truyền thông

## Tương lai mở rộng
- Thêm xử lý ảnh để tận dụng module Camera.
- Thêm xử lý luồng autowaypoint và tránh vật cản và bám quỹ đạo thông minh.
- Giám sát trạng thái hệ thống qua web dashboard.
