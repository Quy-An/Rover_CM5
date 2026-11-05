import threading
import time


class VehicleState:

    def __init__(self):

        self.lock = threading.Lock()

        self.armed = False

        self.vx_cmd = 0.0
        self.wz_cmd = 0.0

        self.last_manual_control = time.time()

        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

        self.roll_speed = 0.0
        self.pitch_speed = 0.0
        self.yaw_speed = 0.0

        self.heading_deg = 0.0

        self.lat = 0
        self.lon = 0
        self.alt = 0

        self.gps_fix_type = 0

        self.eph = 65535
        self.epv = 65535

        self.satellites = 0

        self.mode = 0