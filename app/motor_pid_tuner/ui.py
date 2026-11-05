"""
Giao diện PyQt5 cho ứng dụng PID Tuning
"""

import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGroupBox, QLabel, QSlider, QSpinBox, QLineEdit, QPushButton, 
    QCheckBox, QComboBox, QTextEdit, QTabWidget, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from serial_handler import SerialHandler
from pid_tuner import RobotKinematics, DataRecorder
from config import *


class SignalEmitter(QObject):
    """Emit signals từ thread serial"""
    feedback_received = pyqtSignal(int, int)


class MotorPIDTunerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motor PID Tuner — STM32 Robot Control")
        self.setGeometry(100, 100, 1400, 900)
        
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.feedback_received.connect(self.on_feedback_received)
        
        self.serial = SerialHandler(on_feedback_received=self.signal_emitter.feedback_received.emit)
        self.recorder = DataRecorder(max_points=300)
        
        self.init_ui()
        self.setup_timers()

    def init_ui(self):
        """Tạo giao diện"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # ─── LEFT PANEL: Điều khiển ───
        left_panel = QVBoxLayout()
        
        # Kết nối
        connect_group = QGroupBox("Kết nối Serial")
        connect_layout = QVBoxLayout()
        
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Cổng COM:"))
        self.combo_port = QComboBox()
        self.combo_port.addItems(SerialHandler.get_available_ports())
        h1.addWidget(self.combo_port)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_ports)
        h1.addWidget(self.btn_refresh)
        
        self.btn_connect = QPushButton("Kết nối")
        self.btn_connect.clicked.connect(self.toggle_connect)
        self.btn_connect.setStyleSheet("background-color: lightgreen")
        h1.addWidget(self.btn_connect)
        
        connect_layout.addLayout(h1)
        
        self.label_status = QLabel("Trạng thái: Chưa kết nối")
        self.label_status.setStyleSheet("color: gray")
        connect_layout.addWidget(self.label_status)
        
        connect_group.setLayout(connect_layout)
        left_panel.addWidget(connect_group)
        
        # ─── Điều khiển vx, omega ───
        control_group = QGroupBox("Điều khiển Robot")
        control_layout = QGridLayout()
        
        # vx
        control_layout.addWidget(QLabel("vx (mm/s):"), 0, 0)
        self.slider_vx = QSlider(Qt.Horizontal)
        self.slider_vx.setMinimum(-1000)
        self.slider_vx.setMaximum(1000)
        self.slider_vx.setValue(0)
        self.slider_vx.setTickPosition(QSlider.TicksBelow)
        self.slider_vx.setTickInterval(100)
        self.slider_vx.valueChanged.connect(self.on_slider_vx_changed)
        control_layout.addWidget(self.slider_vx, 0, 1)
        
        self.spin_vx = QSpinBox()
        self.spin_vx.setMinimum(-1000)
        self.spin_vx.setMaximum(1000)
        self.spin_vx.valueChanged.connect(lambda v: self.slider_vx.setValue(v))
        control_layout.addWidget(self.spin_vx, 0, 2)
        
        # omega
        control_layout.addWidget(QLabel("ω (mrad/s):"), 1, 0)
        self.slider_omega = QSlider(Qt.Horizontal)
        self.slider_omega.setMinimum(-700)
        self.slider_omega.setMaximum(700)
        self.slider_omega.setValue(0)
        self.slider_omega.setTickPosition(QSlider.TicksBelow)
        self.slider_omega.setTickInterval(70)
        self.slider_omega.valueChanged.connect(self.on_slider_omega_changed)
        control_layout.addWidget(self.slider_omega, 1, 1)
        
        self.spin_omega = QSpinBox()
        self.spin_omega.setMinimum(-700)
        self.spin_omega.setMaximum(700)
        self.spin_omega.valueChanged.connect(lambda v: self.slider_omega.setValue(v))
        control_layout.addWidget(self.spin_omega, 1, 2)
        
        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)
        
        # ─── Buttons ───
        button_layout = QHBoxLayout()
        
        self.btn_send = QPushButton("Gửi (vx, ω)")
        self.btn_send.clicked.connect(self.send_command)
        button_layout.addWidget(self.btn_send)
        
        self.chk_auto_send = QCheckBox("Auto-send (20ms)")
        self.chk_auto_send.stateChanged.connect(self.on_auto_send_toggled)
        button_layout.addWidget(self.chk_auto_send)
        
        left_panel.addLayout(button_layout)
        
        # ─── PID Tuning ───
        pid_group = QGroupBox("PID Parameters")
        pid_layout = QGridLayout()
        
        # Motor L
        pid_layout.addWidget(QLabel("Motor Trái (L)"), 0, 0, 1, 2)
        
        pid_layout.addWidget(QLabel("Kp:"), 1, 0)
        self.tx_kp_l = QLineEdit(str(DEFAULT_KP))
        pid_layout.addWidget(self.tx_kp_l, 1, 1)
        
        pid_layout.addWidget(QLabel("Ki:"), 2, 0)
        self.tx_ki_l = QLineEdit(str(DEFAULT_KI))
        pid_layout.addWidget(self.tx_ki_l, 2, 1)
        
        pid_layout.addWidget(QLabel("Kd:"), 3, 0)
        self.tx_kd_l = QLineEdit(str(DEFAULT_KD))
        pid_layout.addWidget(self.tx_kd_l, 3, 1)
        
        self.btn_apply_l = QPushButton("Apply Motor L")
        self.btn_apply_l.clicked.connect(lambda: self.apply_pid(0))
        pid_layout.addWidget(self.btn_apply_l, 4, 0, 1, 2)
        
        # Motor R
        pid_layout.addWidget(QLabel("Motor Phải (R)"), 5, 0, 1, 2)
        
        pid_layout.addWidget(QLabel("Kp:"), 6, 0)
        self.tx_kp_r = QLineEdit(str(DEFAULT_KP))
        pid_layout.addWidget(self.tx_kp_r, 6, 1)
        
        pid_layout.addWidget(QLabel("Ki:"), 7, 0)
        self.tx_ki_r = QLineEdit(str(DEFAULT_KI))
        pid_layout.addWidget(self.tx_ki_r, 7, 1)
        
        pid_layout.addWidget(QLabel("Kd:"), 8, 0)
        self.tx_kd_r = QLineEdit(str(DEFAULT_KD))
        pid_layout.addWidget(self.tx_kd_r, 8, 1)
        
        self.btn_apply_r = QPushButton("Apply Motor R")
        self.btn_apply_r.clicked.connect(lambda: self.apply_pid(1))
        pid_layout.addWidget(self.btn_apply_r, 9, 0, 1, 2)
        
        pid_group.setLayout(pid_layout)
        left_panel.addWidget(pid_group)
        
        # ─── Log ───
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setFont(QFont("Courier New", 9))
        self.text_log.setStyleSheet("background-color: black; color: lime")
        log_layout.addWidget(self.text_log)
        
        self.btn_clear_log = QPushButton("Clear Log")
        self.btn_clear_log.clicked.connect(self.text_log.clear)
        log_layout.addWidget(self.btn_clear_log)
        
        log_group.setLayout(log_layout)
        left_panel.addWidget(log_group)
        
        # ─── RIGHT PANEL: Đồ thị ───
        right_panel = QVBoxLayout()
        
        # Tạo 2 đồ thị
        self.fig_l = Figure(figsize=(6, 4), dpi=100)
        self.ax_l = self.fig_l.add_subplot(111)
        self.canvas_l = FigureCanvas(self.fig_l)
        self.ax_l.set_title("Motor Trái (L)")
        self.ax_l.set_xlabel("Time (s)")
        self.ax_l.set_ylabel("Pulse/20ms")
        self.ax_l.grid(True)
        right_panel.addWidget(self.canvas_l)
        
        self.fig_r = Figure(figsize=(6, 4), dpi=100)
        self.ax_r = self.fig_r.add_subplot(111)
        self.canvas_r = FigureCanvas(self.fig_r)
        self.ax_r.set_title("Motor Phải (R)")
        self.ax_r.set_xlabel("Time (s)")
        self.ax_r.set_ylabel("Pulse/20ms")
        self.ax_r.grid(True)
        right_panel.addWidget(self.canvas_r)
        
        # Layout cuối
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 1)

    def setup_timers(self):
        """Thiết lập timer"""
        self.timer_send = QTimer()
        self.timer_send.timeout.connect(self.send_command)
        
        self.timer_graph = QTimer()
        self.timer_graph.timeout.connect(self.update_graphs)
        self.timer_graph.start(200)  # Update đồ thị mỗi 200ms

    def refresh_ports(self):
        """Làm mới danh sách COM port"""
        self.combo_port.clear()
        self.combo_port.addItems(SerialHandler.get_available_ports())
        self.log("Đã cập nhật danh sách cổng COM.")

    def toggle_connect(self):
        """Kết nối / Ngắt"""
        if self.serial.is_connected():
            self.serial.disconnect()
            self.btn_connect.setText("Kết nối")
            self.btn_connect.setStyleSheet("background-color: lightgreen")
            self.label_status.setText("Trạng thái: Chưa kết nối")
            self.label_status.setStyleSheet("color: gray")
            self.timer_send.stop()
            self.log("Đã ngắt kết nối.")
        else:
            port = self.combo_port.currentText()
            if not port:
                self.log("⚠ Chưa chọn cổng COM!")
                return
            
            if self.serial.connect(port):
                self.btn_connect.setText("Ngắt kết nối")
                self.btn_connect.setStyleSheet("background-color: salmon")
                self.label_status.setText(f"Trạng thái: Đã kết nối {port}")
                self.label_status.setStyleSheet("color: darkgreen")
                self.recorder.reset()
                self.log(f"Đã kết nối: {port}")
            else:
                self.log(f"⚠ Kết nối thất bại: {port}")

    def on_slider_vx_changed(self, value):
        """Slider vx thay đổi"""
        self.spin_vx.blockSignals(True)
        self.spin_vx.setValue(value)
        self.spin_vx.blockSignals(False)

    def on_slider_omega_changed(self, value):
        """Slider omega thay đổi"""
        self.spin_omega.blockSignals(True)
        self.spin_omega.setValue(value)
        self.spin_omega.blockSignals(False)

    def send_command(self):
        """Gửi lệnh vx, omega"""
        if not self.serial.is_connected():
            return
        
        vx = self.spin_vx.value()
        omega = self.spin_omega.value()
        
        if self.serial.send_command(vx, omega):
            if not self.chk_auto_send.isChecked():
                self.log(f"→ Gửi: vx={vx}mm/s, ω={omega}mrad/s")
        else:
            self.log("⚠ Lỗi gửi lệnh!")

    def on_auto_send_toggled(self, state):
        """Toggle auto-send"""
        if state:
            if not self.serial.is_connected():
                self.chk_auto_send.setChecked(False)
                self.log("⚠ Chưa kết nối serial!")
                return
            self.timer_send.start(20)
            self.log("Auto-send BẬT (20ms)")
        else:
            self.timer_send.stop()
            self.log("Auto-send TẮT")

    def apply_pid(self, motor_id):
        """Gửi tham số PID xuống STM32"""
        if not self.serial.is_connected():
            self.log("⚠ Chưa kết nối serial!")
            return
        
        if motor_id == 0:
            tx_kp, tx_ki, tx_kd = self.tx_kp_l, self.tx_ki_l, self.tx_kd_l
            name = "Motor Trái"
        else:
            tx_kp, tx_ki, tx_kd = self.tx_kp_r, self.tx_ki_r, self.tx_kd_r
            name = "Motor Phải"
        
        try:
            kp = float(tx_kp.text())
            ki = float(tx_ki.text())
            kd = float(tx_kd.text())
        except ValueError:
            self.log(f"⚠ Giá trị PID không hợp lệ ({name})!")
            return
        
        if self.serial.send_pid_params(motor_id, kp, ki, kd):
            self.log(f"→ Gửi PID {name}: Kp={kp}, Ki={ki}, Kd={kd}")
        else:
            self.log(f"⚠ Lỗi gửi PID {name}!")

    def on_feedback_received(self, speed_l: int, speed_r: int):
        """Callback nhận feedback encoder"""
        vx = int(self.spin_vx.value())
        omega = int(self.spin_omega.value())
        
        setpoint_l, setpoint_r = RobotKinematics.compute_setpoints(vx, omega)
        
        self.recorder.record_feedback(setpoint_l, setpoint_r, speed_l, speed_r)
        
        self.log(f"← Enc: L={speed_l}, R={speed_r} | Target: L={setpoint_l}, R={setpoint_r}")

    def update_graphs(self):
        """Cập nhật đồ thị"""
        # Motor L
        times_l, sp_l, actual_l = self.recorder.get_data_l()
        self.ax_l.clear()
        self.ax_l.plot(times_l, sp_l, 'b-', label='Setpoint', linewidth=2)
        self.ax_l.plot(times_l, actual_l, 'r-', label='Actual', linewidth=2)
        self.ax_l.set_title("Motor Trái (L)")
        self.ax_l.set_xlabel("Time (s)")
        self.ax_l.set_ylabel("Pulse/20ms")
        self.ax_l.legend()
        self.ax_l.grid(True)
        self.canvas_l.draw()
        
        # Motor R
        times_r, sp_r, actual_r = self.recorder.get_data_r()
        self.ax_r.clear()
        self.ax_r.plot(times_r, sp_r, 'b-', label='Setpoint', linewidth=2)
        self.ax_r.plot(times_r, actual_r, 'r-', label='Actual', linewidth=2)
        self.ax_r.set_title("Motor Phải (R)")
        self.ax_r.set_xlabel("Time (s)")
        self.ax_r.set_ylabel("Pulse/20ms")
        self.ax_r.legend()
        self.ax_r.grid(True)
        self.canvas_r.draw()

    def log(self, msg):
        """Ghi log"""
        timestamp = time.strftime("%H:%M:%S")
        self.text_log.append(f"[{timestamp}] {msg}")
        
        # Giữ log dưới 200 dòng
        doc = self.text_log.document()
        if doc.blockCount() > LOG_MAX_LINES:
            cursor = self.text_log.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()

    def closeEvent(self, event):
        """Đóng app"""
        if self.serial.is_connected():
            self.serial.disconnect()
        self.timer_send.stop()
        self.timer_graph.stop()
        event.accept()