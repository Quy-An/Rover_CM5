"""
Xử lý giao tiếp UART với STM32
"""

import serial
import threading
import struct
from typing import Callable, Optional
from config import *


class SerialHandler:
    def __init__(self, on_feedback_received: Callable):
        """
        on_feedback_received: callback nhận feedback encoder
        Signature: on_feedback_received(speed_l: int16, speed_r: int16)
        """
        self.port = None
        self.on_feedback = on_feedback_received
        self.running = False
        self.rx_thread = None
        
        self.rx_buf = bytearray(FRAME_CMD_LEN)
        self.rx_idx = 0

    def connect(self, port: str, baudrate: int = BAUD_RATE) -> bool:
        """Kết nối tới cổng serial"""
        try:
            self.port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5
            )
            self.running = True
            self.rx_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.rx_thread.start()
            return True
        except Exception as e:
            print(f"[SerialHandler] Lỗi kết nối: {e}")
            return False

    def disconnect(self):
        """Ngắt kết nối"""
        self.running = False
        if self.port and self.port.is_open:
            self.port.close()
        if self.rx_thread:
            self.rx_thread.join(timeout=1)

    def is_connected(self) -> bool:
        return self.port and self.port.is_open

    def send_command(self, vx_mm: int, omega_mrad: int) -> bool:
        """
        Gửi lệnh điều khiển (vx, omega) xuống STM32
        vx_mm: tốc độ tuyến tính (mm/s), int16
        omega_mrad: tốc độ góc (mrad/s), int16
        """
        if not self.is_connected():
            return False

        try:
            # Xây dựng frame
            frame = bytearray(FRAME_CMD_LEN)
            frame[0] = HEADER_CMD
            frame[1:3] = struct.pack('>h', vx_mm)      # Big-endian int16
            frame[3:5] = struct.pack('>h', omega_mrad)
            frame[5] = self._crc8(frame[:5])

            self.port.write(bytes(frame))
            return True
        except Exception as e:
            print(f"[SerialHandler] Lỗi gửi: {e}")
            return False

    def send_pid_params(self, motor_id: int, kp: float, ki: float, kd: float) -> bool:
        """
        Gửi tham số PID xuống STM32
        motor_id: 0=trái, 1=phải
        """
        if not self.is_connected():
            return False

        try:
            frame = bytearray(FRAME_PID_LEN)
            frame[0] = HEADER_PID
            
            # Nhân 10 để gửi dưới dạng int16
            kp10 = int(kp * 10)
            ki10 = int(ki * 10)
            kd10 = int(kd * 10)
            
            frame[1:3] = struct.pack('>h', kp10)
            frame[3:5] = struct.pack('>h', ki10)
            frame[5:7] = struct.pack('>h', kd10)
            frame[7] = motor_id
            frame[8] = self._crc8(frame[:8])

            self.port.write(bytes(frame))
            return True
        except Exception as e:
            print(f"[SerialHandler] Lỗi gửi PID: {e}")
            return False

    def _receive_loop(self):
        """Vòng lặp nhận dữ liệu từ STM32 (chạy trên thread riêng)"""
        while self.running:
            try:
                if self.port.in_waiting > 0:
                    byte = self.port.read(1)[0]
                    self._process_byte(byte)
            except Exception as e:
                print(f"[SerialHandler] Lỗi nhận: {e}")

    def _process_byte(self, byte: int):
        """State machine xử lý từng byte nhận được"""
        if self.rx_idx == 0:
            # Chờ header
            if byte == HEADER_FB:
                self.rx_buf[self.rx_idx] = byte
                self.rx_idx += 1
        else:
            self.rx_buf[self.rx_idx] = byte
            self.rx_idx += 1

            if self.rx_idx >= FRAME_FB_LEN:
                # Frame đã đủ → kiểm CRC
                crc = self._crc8(self.rx_buf[:FRAME_FB_LEN - 1])
                if crc == self.rx_buf[FRAME_FB_LEN - 1]:
                    # CRC đúng → giải mã
                    speed_l = struct.unpack('>h', bytes(self.rx_buf[1:3]))[0]
                    speed_r = struct.unpack('>h', bytes(self.rx_buf[3:5]))[0]
                    self.on_feedback(speed_l, speed_r)

                self.rx_idx = 0

    @staticmethod
    def _crc8(data: bytes) -> int:
        """Tính CRC8 XOR"""
        crc = 0
        for byte in data:
            crc ^= byte
        return crc

    @staticmethod
    def get_available_ports() -> list:
        """Lấy danh sách cổng COM khả dụng"""
        try:
            import serial.tools.list_ports
            ports = []
            for port, desc, hwid in serial.tools.list_ports.comports():
                ports.append(port)
            return ports
        except:
            return []