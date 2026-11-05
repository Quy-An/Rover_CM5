"""
Motor PID Tuner - Entry Point
Ứng dụng tuning PID realtime cho robot STM32 qua UART
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui import MotorPIDTunerApp


def main():
    app = QApplication(sys.argv)
    window = MotorPIDTunerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()