"""
Logic tính toán động học và xử lý PID tuning
"""

import math
import time
from collections import deque
from config import *


class RobotKinematics:
    """Tính toán động học robot vi sai"""
    
    @staticmethod
    def inverse_kinematics(vx_mm: float, omega_mrad: float) -> tuple:
        """
        Tính động học nghịch: (vx, omega) → (v_left, v_right)
        
        Input:
            vx_mm: tốc độ tuyến tính (mm/s)
            omega_mrad: tốc độ góc (mrad/s)
        
        Output:
            (v_left, v_right): tốc độ từng bánh (mm/s)
        """
        vx = vx_mm / 1000.0  # chuyển sang m/s
        omega = omega_mrad / 1000.0  # chuyển sang rad/s
        
        v_left = vx - omega * (TRACK_WIDTH / 2.0)
        v_right = vx + omega * (TRACK_WIDTH / 2.0)
        
        return v_left, v_right

    @staticmethod
    def speed_to_setpoint(v_ms: float) -> int:
        """
        Chuyển tốc độ (m/s) → setpoint (pulse/20ms)
        """
        omega_rad_s = v_ms / WHEEL_RADIUS
        pulse = omega_rad_s * KINEMATICS_SCALE
        
        # Clamp to max speed
        pulse = max(-MAX_PULSE_20MS, min(MAX_PULSE_20MS, pulse))
        
        return int(pulse)

    @staticmethod
    def compute_setpoints(vx_mm: int, omega_mrad: int) -> tuple:
        """
        Tính setpoint cho 2 bánh từ (vx, omega)
        
        Output:
            (setpoint_l, setpoint_r): int16 pulse/20ms
        """
        v_left, v_right = RobotKinematics.inverse_kinematics(vx_mm, omega_mrad)
        
        setpoint_l = RobotKinematics.speed_to_setpoint(v_left)
        setpoint_r = RobotKinematics.speed_to_setpoint(v_right)
        
        return setpoint_l, setpoint_r


class DataRecorder:
    """Lưu trữ lịch sử dữ liệu để vẽ đồ thị"""
    
    def __init__(self, max_points: int = 300):
        self.max_points = max_points
        self.time_start = None
        
        # Dữ liệu Motor L: (time, setpoint, actual)
        self.data_l = deque(maxlen=max_points)
        # Dữ liệu Motor R
        self.data_r = deque(maxlen=max_points)
        
        self.last_setpoint_l = 0
        self.last_setpoint_r = 0

    def reset(self):
        """Reset lịch sử"""
        self.data_l.clear()
        self.data_r.clear()
        self.time_start = time.time()

    def record_feedback(self, setpoint_l: int, setpoint_r: int, actual_l: int, actual_r: int):
        """
        Ghi nhận feedback encoder
        
        setpoint_l/r: giá trị mong muốn
        actual_l/r: giá trị đo được từ encoder
        """
        if self.time_start is None:
            self.time_start = time.time()
        
        elapsed = time.time() - self.time_start
        
        self.data_l.append((elapsed, setpoint_l, actual_l))
        self.data_r.append((elapsed, setpoint_r, actual_r))
        
        self.last_setpoint_l = setpoint_l
        self.last_setpoint_r = setpoint_r

    def get_data_l(self) -> list:
        """Trả về dữ liệu motor L dưới dạng 3 list (time, setpoint, actual)"""
        if not self.data_l:
            return [], [], []
        
        times, setpoints, actuals = zip(*self.data_l)
        return list(times), list(setpoints), list(actuals)

    def get_data_r(self) -> list:
        """Trả về dữ liệu motor R"""
        if not self.data_r:
            return [], [], []
        
        times, setpoints, actuals = zip(*self.data_r)
        return list(times), list(setpoints), list(actuals)