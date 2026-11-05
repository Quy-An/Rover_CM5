"""
Cấu hình protocol UART và tham số vật lý robot
"""

# ── Protocol ──────────────────────────────────────
HEADER_CMD = 0xAA      # Frame lệnh điều khiển (vx, omega)
HEADER_PID = 0xAC      # Frame PID params
HEADER_FB = 0xBB       # Frame feedback encoder

FRAME_CMD_LEN = 6      # AA | vx_H | vx_L | omega_H | omega_L | CRC
FRAME_PID_LEN = 9      # AC | Kp10_H | Kp10_L | Ki10_H | Ki10_L | Kd10_H | Kd10_L | motor_id | CRC
FRAME_FB_LEN = 6       # BB | E1H | E1L | E2H | E2L | CRC

BAUD_RATE = 115200

# ── Thông số vật lý robot ──────────────────────
WHEEL_RADIUS = 0.0225  # mét (bán kính bánh)
TRACK_WIDTH = 0.2     # mét (khoảng cách 2 bánh) — CẦN ĐO LẠI THỰC TẾ
PPR = 1320.0            # Xung/vòng encoder
MAX_PULSE_20MS = 154.0 # Tốc độ max (xung/20ms)

# ── Kinematics ────────────────────────────────────
import math
KINEMATICS_SCALE = (PPR / (2.0 * math.pi)) * 0.02  # Hệ số quy đổi từ m/s → pulse/20ms

# ── PID mặc định ───────────────────────────────────
DEFAULT_KP = 1.5
DEFAULT_KI = 0.1
DEFAULT_KD = 0.05

# ── Logging ────────────────────────────────────────
LOG_MAX_LINES = 200