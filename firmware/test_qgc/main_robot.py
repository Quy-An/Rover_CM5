import os
# Ép Python đóng gói dữ liệu theo chuẩn MAVLink 2.0
os.environ['MAVLINK20'] = '1'

import threading
import time
from pymavlink import mavutil

from camera import thread_stream_video
from qgc_receiver import qgc_receiver_loop
from telemetry import create_mavlink_connection, imu_loop, telemetry_loop, gps_loop, lidar_loop
from vehicle_state import VehicleState
from rover_controller import motor_control_loop

# --- CẤU HÌNH THÔNG SỐ MẠNG ---

LAPTOP_IP = "192.168.1.19"     
QGC_PORT = 14550              


if __name__ == "__main__":
    print("--------------------------------------------------")
    print("🤖 KHỞI ĐỘNG HỆ THỐNG ĐIỀU KHIỂN TRUNG TÂM")
    print("--------------------------------------------------")
    
    vehicle = VehicleState()
    
    mav_conn = create_mavlink_connection(LAPTOP_IP, QGC_PORT)
    mav_send_lock = threading.Lock()
    stop_event = threading.Event()

    # CHỈNH SỬA: Truyền stop_event qua kwargs cho t_video
    t_video = threading.Thread(
        target=thread_stream_video, 
        args=(LAPTOP_IP, 180), 
        kwargs={"stop_event": stop_event},
        daemon=True
    )
    t_telemetry = threading.Thread(
        target=telemetry_loop,
        args=(mav_conn, vehicle),
        kwargs={"send_lock": mav_send_lock, "stop_event": stop_event},
        daemon=False,
    )
    t_imu = threading.Thread(
        target=imu_loop,
        args=(mav_conn, vehicle),
        kwargs={
            "send_lock": mav_send_lock,
            "stop_event": stop_event
        },
        daemon=False,
    )
    t_gps = threading.Thread(
        target=gps_loop,
        args=(mav_conn, vehicle),
        kwargs={
            "send_lock": mav_send_lock,
            "stop_event": stop_event
        },
        daemon=False,
    )
    t_lidar = threading.Thread(
        target=lidar_loop,
        args=(mav_conn,),
        kwargs={"send_lock": mav_send_lock, "stop_event": stop_event},
        daemon=False,
    )
    t_receiver = threading.Thread(
        target=qgc_receiver_loop,
        args=(mav_conn, vehicle),
        kwargs={"send_lock": mav_send_lock, "stop_event": stop_event},
        daemon=False,
    )
    t_motor = threading.Thread(
        target=motor_control_loop,
        args=(vehicle,),
        kwargs={"stop_event": stop_event},
        daemon=False,
    )
    
    t_video.start()
    t_telemetry.start()
    t_imu.start()
    t_gps.start()
    t_lidar.start()
    t_receiver.start()
    t_motor.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng hệ thống Robot...")
    finally:
        # Kích hoạt sự kiện dừng cho tất cả các luồng cùng biết
        stop_event.set()
        
        # CHỈNH SỬA: Đưa t_video vào danh sách đợi giải phóng chung
        for thread in (t_video, t_telemetry, t_imu, t_gps, t_lidar, t_receiver, t_motor):
            thread.join(timeout=3)
            
        print("🏁 Hệ thống dọn dẹp hoàn tất. Đóng chương trình.")