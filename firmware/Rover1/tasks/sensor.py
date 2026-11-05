# import serial
# import time
# from queue import Queue
# from threading import Thread, Event
# from pyubx2 import UBXReader

# # Cấu hình kết nối Serial
# GPS_PORT = '/dev/serial0'
# GPS_BAUDRATE = 115200

# # Bộ đệm lưu trữ dữ liệu GPS chuẩn hóa
# gps_data = {
#     'time_usec': 0,             # Timestamp hệ thống (Microseconds)
#     'fix_type': 0,              # Loại Fix GPS (Ánh xạ theo chuẩn MAVLink)
#     'lat': 0.0,                 # Vĩ độ nhân 10^7 (degE7)
#     'lon': 0.0,                 # Kinh độ nhân 10^7 (degE7)
#     'alt': 0.0,                 # Độ cao so với mực nước biển (mm)
#     'eph': 65535,               # Sai số vị trí ngang (cm)
#     'epv': 65535,               # Sai số vị trí dọc (cm)
#     'vel': 65535,               # Tốc độ mặt đất (cm/s)
#     'cog': 65535,               # Hướng di chuyển (centidegrees - độ * 100)
#     'satellites_visible': 0     # Số lượng vệ tinh nhìn thấy
# }

# def mapping_nmea_qual_to_mav_fix_type(nmea_qual, gsa_fix_type):
#     if nmea_qual == 0:      
#         return 1                        # GPS_FIX_TYPE_NO_FIX
#     elif nmea_qual == 1:
#         if gsa_fix_type == 2:
#             return 2                    # GPS_FIX_TYPE_2D_FIX
#         elif gsa_fix_type == 3:
#             return 3                    # GPS_FIX_TYPE_3D_FIX
#         else:
#             return 1                    # GPS_FIX_TYPE_NO_FIX
#     elif nmea_qual == 2:
#         return 4                        # GPS_FIX_TYPE_DGPS
#     elif nmea_qual == 4:
#         return 6                        # GPS_FIX_TYPE_RTK_FIXED
#     elif nmea_qual == 5:
#         return 5                        # GPS_FIX_TYPE_RTK_FLOAT
#     elif nmea_qual == 6:
#         return 3                        # GPS_FIX_TYPE_3D_FIX
#     else:
#         return 0                        # GPS_FIX_TYPE_NO_GPS

# # Các hàm bổ trợ an toàn dữ liệu
# def safe_float(val, default=0.0):
#     try:
#         return float(val) if val not in (None, "") else default
#     except (ValueError, TypeError):
#         return default

# def safe_int(val, default=0):
#     try:
#         return int(val) if val not in (None, "") else default
#     except (ValueError, TypeError):
#         return default

# def print_gps_data():
#     """Hàm hiển thị giao diện giám sát thời gian thực"""
#     # Mã ANSI xóa màn hình và đưa con trỏ về góc trái trên
#     print("\033[H\033[J", end="")
#     print("=" * 60)
#     print("       HỆ THỐNG GIÁM SÁT GPS BẤT ĐỒNG BỘ (MULTITHREADED)       ")
#     print("=" * 60)
#     print(f" Thời gian hệ thống:  {gps_data['time_usec']} us")
    
#     fix_names = {
#         0: "0 (NO_GPS)",
#         1: "1 (NO_FIX)",
#         2: "2 (2D_FIX)",
#         3: "3 (3D_FIX)",
#         4: "4 (DGPS)",
#         5: "5 (RTK_FLOAT)",
#         6: "6 (RTK_FIXED)"
#     }
#     fix_str = fix_names.get(gps_data['fix_type'], "Chưa xác định")
    
#     print(f" Trạng thái Fix:      {fix_str}")
#     print(f" Số vệ tinh khả dụng: {gps_data['satellites_visible']}")
#     print("-" * 60)
#     print(f" Vĩ độ (Lat):         {gps_data['lat'] / 1e7:.7f}°  (Raw degE7: {gps_data['lat']})")
#     print(f" Kinh độ (Lon):       {gps_data['lon'] / 1e7:.7f}°  (Raw degE7: {gps_data['lon']})")
#     print(f" Độ cao (Alt MSL):    {gps_data['alt'] / 1000:.3f} m        (Raw mm: {gps_data['alt']})")
#     print("-" * 60)
#     print(f" Vận tốc mặt đất:     {gps_data['vel']} cm/s      ({gps_data['vel'] * 0.036:.2f} km/h)")
#     print(f" Hướng di chuyển:      {gps_data['cog'] / 100:.2f}°       (Raw cdeg: {gps_data['cog']})")
#     print(f" Sai số ngang (EPH):  {gps_data['eph']} cm")
#     print(f" Sai số dọc (EPV):    {gps_data['epv']} cm")
#     print("=" * 60)
#     print(" Nhấn Ctrl+C để dừng chương trình.")

# # =====================================================================
# # LUỒNG ĐỌC SERIAL (Chỉ đọc & quăng vào Queue)
# # =====================================================================
# def io_thread_func(ubr: UBXReader, queue: Queue, stop_event: Event):
#     """
#     Đọc dữ liệu thô liên tục từ cổng Serial và đẩy gói tin đã phân tích vào Queue.
#     Chạy bất đồng bộ, hoàn toàn độc lập với việc in ấn UI.
#     """
#     while not stop_event.is_set():
#         try:
#             # Đọc gói tin từ luồng dữ liệu GPS
#             (raw_data, parsed_data) = ubr.read()
#             if parsed_data:
#                 queue.put(parsed_data)
#         except Exception:
#             # Bỏ qua các lỗi phân tích cú pháp nhỏ (checksum/đứt gói giữa chừng)
#             continue

# # =====================================================================
# # LUỒNG XỬ LÝ DỮ LIỆU & HIỂN THỊ (UI)
# # =====================================================================
# def process_thread_func(queue: Queue, stop_event: Event):
#     """
#     Lấy dữ liệu từ Queue, cập nhật cấu trúc gps_data và hiển thị lên màn hình.
#     """
#     nmea_qual = 0
#     gsa_fix_type = 1
#     last_print_time = 0
#     PRINT_INTERVAL = 0.5  # Tiết chế in tối đa 2 lần/giây (500ms) để không bị nghẽn
    
#     while not stop_event.is_set():
#         # Kiểm tra nếu có gói tin trong Queue
#         if not queue.empty():
#             parsed_data = queue.get()
            
#             # Cập nhật mốc thời gian nhận dữ liệu
#             gps_data['time_usec'] = int(time.time() * 1000000)
            
#             # --- 1. Xử lý gói nhị phân UBX NAV-PVT ---
#             if parsed_data.identity == "NAV-PVT":
#                 if hasattr(parsed_data, "lat") and hasattr(parsed_data, "lon"):
#                     gps_data['lat'] = int(parsed_data.lat * 1e7)
#                     gps_data['lon'] = int(parsed_data.lon * 1e7)
#                 if hasattr(parsed_data, "hMSL"):
#                     gps_data['alt'] = int(parsed_data.hMSL)
#                 if hasattr(parsed_data, "numSV"):
#                     gps_data['satellites_visible'] = parsed_data.numSV
#                 if hasattr(parsed_data, "gSpeed"):
#                     gps_data['vel'] = int(parsed_data.gSpeed / 10)
#                 if hasattr(parsed_data, "headMot"):
#                     cog_val = int(parsed_data.headMot * 100)
#                     gps_data['cog'] = (cog_val % 36000 + 36000) % 36000
#                 if hasattr(parsed_data, "hAcc"):
#                     gps_data['eph'] = min(65535, int(parsed_data.hAcc / 10))
#                 if hasattr(parsed_data, "vAcc"):
#                     gps_data['epv'] = min(65535, int(parsed_data.vAcc / 10))
                
#                 if hasattr(parsed_data, "fixType"):
#                     ubx_fix = parsed_data.fixType
#                     if ubx_fix == 2:
#                         gps_data['fix_type'] = 2
#                     elif ubx_fix in (3, 4):
#                         gps_data['fix_type'] = 3
#                         if hasattr(parsed_data, "carrSoln"):
#                             if parsed_data.carrSoln == 1:
#                                 gps_data['fix_type'] = 5
#                             elif parsed_data.carrSoln == 2:
#                                 gps_data['fix_type'] = 6
#                     else:
#                         gps_data['fix_type'] = 1

#             # --- 2. Xử lý các gói NMEA ---
#             elif parsed_data.identity == "GGA":
#                 lat_val = safe_float(getattr(parsed_data, "lat", 0.0))
#                 lon_val = safe_float(getattr(parsed_data, "lon", 0.0))
#                 if lat_val != 0.0 and lon_val != 0.0:
#                     gps_data['lat'] = int(lat_val * 1e7)
#                     gps_data['lon'] = int(lon_val * 1e7)
                
#                 gps_data['satellites_visible'] = safe_int(getattr(parsed_data, "numSV", 0))
#                 gps_data['alt'] = int(safe_float(getattr(parsed_data, "alt", 0.0)) * 1000)
#                 gps_data['eph'] = min(65535, int(safe_float(getattr(parsed_data, "HDOP", 0.0)) * 100))
                
#                 nmea_qual = safe_int(getattr(parsed_data, "quality", 0))
#                 gps_data['fix_type'] = mapping_nmea_qual_to_mav_fix_type(nmea_qual, gsa_fix_type)

#             elif parsed_data.identity == "GSA":
#                 gsa_fix_type = safe_int(getattr(parsed_data, "navMode", 1))
#                 gps_data['fix_type'] = mapping_nmea_qual_to_mav_fix_type(nmea_qual, gsa_fix_type)
#                 gps_data['epv'] = min(65535, int(safe_float(getattr(parsed_data, "VDOP", 0.0)) * 100))

#             elif parsed_data.identity == "RMC":
#                 gps_data['vel'] = int(safe_float(getattr(parsed_data, "spd", 0.0)) * 51.4444)
#                 cog_val = safe_float(getattr(parsed_data, "cog", 0.0))
#                 gps_data['cog'] = int(cog_val * 100)

#             queue.task_done()

#         # In thông tin theo chu kỳ kiểm soát (không in liên tục gây nghẽn)
#         current_time = time.time()
#         if current_time - last_print_time >= PRINT_INTERVAL:
#             print_gps_data()
#             last_print_time = current_time

#         # Nghỉ nhẹ 10ms để giải phóng CPU khi Queue trống
#         time.sleep(0.01)

# # =====================================================================
# # HÀM CHẠY CHÍNH (MAIN)
# # =====================================================================
# def main():
#     print(f"Đang kết nối tới module GPS qua {GPS_PORT} ({GPS_BAUDRATE})...")
#     try:
#         # Sử dụng timeout ngắn (0.1s) để luồng đọc nhạy bén hơn
#         ser = serial.Serial(GPS_PORT, GPS_BAUDRATE, timeout=0.1)
#     except Exception as e:
#         print(f"Lỗi: Không thể mở cổng Serial {GPS_PORT}. Chi tiết: {e}")
#         return

#     # Khởi tạo thư viện đọc GPS
#     ubr = UBXReader(ser)
    
#     # Thiết lập hàng đợi (Queue) và cờ dừng luồng (Event)
#     data_queue = Queue()
#     stop_event = Event()
    
#     # Tạo các luồng xử lý
#     io_thread = Thread(target=io_thread_func, args=(ubr, data_queue, stop_event), daemon=True)
#     process_thread = Thread(target=process_thread_func, args=(data_queue, stop_event), daemon=True)
    
#     # Kích hoạt luồng chạy ngầm
#     stop_event.clear()
#     io_thread.start()
#     process_thread.start()
    
#     print("Hệ thống đa luồng đã khởi chạy thành công.")
    
#     try:
#         while True:
#             # Giữ luồng chính (Main Thread) chạy ngầm để đón sự kiện ngắt Ctrl+C
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\nĐang gửi tín hiệu dừng các luồng...")
#         stop_event.set()
        
#         # Chờ các luồng ngầm dừng hẳn tối đa trong 1 giây trước khi thoát
#         io_thread.join(timeout=1.0)
#         process_thread.join(timeout=1.0)
#     finally:
#         ser.close()
#         print("Đã đóng kết nối Serial an toàn.")

# if __name__ == "__main__":
#     main()

import os
import time
import struct
import queue
import numpy as np 
import smbus
import math
from pyrplidar import PyRPlidar
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, SET
from imusensor.MPU9250 import MPU9250
from datetime import datetime, timezone
import requests
import sys
import csv
from imusensor.filters import madgwick
def put_latest_to_queue(q, data):
    try:
        q.put_nowait(data)
    except queue.Full:
        try:
            q.get_nowait()  
        except queue.Empty:
            pass
        try:
            q.put_nowait(data)  
        except queue.Full:
            pass

def lidar_task(config, shm, lock, stop_event, lidar_active_event):
    lidar_config = config["config"]["hardware"]
    port = lidar_config["lidar_serial_port"]
    baudrate = lidar_config["lidar_baudrate"]
    pwm = lidar_config["lidar_motor_pwm"]

    lidar = None
    
    while not stop_event.is_set():
        if lidar_active_event.is_set():
            try:
                print("[LiDAR Task] Nhận lệnh BẬT -> Khởi động phần cứng...")
                lidar = PyRPlidar()
                lidar.connect(port=port, baudrate=baudrate, timeout=3)
                
                lidar.set_motor_pwm(pwm)
                time.sleep(2.0) # Chờ motor đạt tốc độ ổn định
                try:
                    if hasattr(lidar, '_port'): lidar._port.reset_input_buffer()
                    elif hasattr(lidar, '_backend'): lidar._backend._serial.reset_input_buffer()
                except: pass
                
                lidar_data_new = np.full(72, 65535, dtype=np.uint16)
                scan_generator = lidar.start_scan_express(4)

                for point in scan_generator():
                    if stop_event.is_set() or not lidar_active_event.is_set():
                        break
                        
                    angle = point.angle
                    distance = point.distance / 10
                    quality = point.quality
                    now = time.time()
                    
                    if point.start_flag:
                        byte_timestamp = struct.pack('d', now)
                        byte_lidar = lidar_data_new.tobytes()
                        
                        with lock:
                            shm.buf[0:8] = byte_timestamp
                            shm.buf[8:152] = byte_lidar
                        
                        lidar_data_new.fill(65535)

                    if 270 <= angle <= 360:
                        relative_angle = angle - 270    
                    elif 0 <= angle <= 90:
                        relative_angle = angle + 90     
                    else:
                        continue

                    sector_index = int(relative_angle / 2.5)
                    index = max(0, min(71, sector_index))
                    
                    if quality > 0 and distance > 0 and distance <= 1200:
                        lidar_data_new[index] = min(lidar_data_new[index], distance)
                    
            except Exception as e:
                print(f"Lỗi hệ thống LiDAR: {e}")
                time.sleep(1.0)
                
            finally:
                if lidar is not None:
                    try:
                        lidar.stop()
                        lidar.set_motor_pwm(0)
                        lidar.disconnect()
                        print("[LiDAR Thread] Đã ngắt kết nối và dừng motor LiDAR an toàn.")
                    except Exception as ex:
                        print(f"[LiDAR Thread] Lỗi khi giải phóng tài nguyên: {ex}")
                    
                    lidar = None # Giải phóng biến để vòng lặp sau khởi tạo lại từ đầu
        else:
            try:
                clear_data = np.full(72, 65535, dtype=np.uint16).tobytes()
                with lock:
                    shm.buf[8:152] = clear_data
            except: pass
            
            time.sleep(0.2) # Nghỉ 200ms để tránh vòng lặp while cắn full CPU khi đang tắt thiết bị

    if lidar is not None:
        try:
            lidar.stop()
            lidar.set_motor_pwm(0)
            lidar.disconnect()
        except: pass

    if lidar is not None:
        try:
            lidar.stop()
            lidar.set_motor_pwm(0)
            lidar.disconnect()
        except: pass

def imu_task(q_imu_control, q_imu_mavlink, q_imu_video, stop_event):
    # 1. NẠP THƯ VIỆN VÀ KHỞI TẠO PHẦN CỨNG
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append("/app")
    try:
        from mpu9250_i2c import mpu6050_conv, AK8963_conv
        print("====== [IMU INFO] KHỞI TẠO MPU9250 (MAKER PORTAL) THÀNH CÔNG! ======")
    except Exception as init_err:
        print(f"[IMU Task] Lỗi import hoặc khởi tạo phần cứng: {init_err}")
        return
    
    # 2. BỘ HẰNG SỐ HIỆU CHUẨN ĐÃ ĐƯỢC CHỨNG THỰC CỦA BẠN
    # Gyro Bias Offsets (đơn vị: dps)
    WX_OFF, WY_OFF, WZ_OFF = 2.901212, -11.190539, -0.449948
    
    # Accel Coefficients (m, b)
    MX_ACC, BX_ACC = 1.002370, -0.001721
    MY_ACC, BY_ACC = 0.999796,  0.002133
    MZ_ACC, BZ_ACC = 0.994585,  0.054289

    # Mag Offsets (Hard-iron uT)
    MX_MAG_OFF, MY_MAG_OFF, MZ_MAG_OFF = -26.513672, 31.054688, -27.465820

    LOOP_DELAY = 0.005
    
    # Khởi tạo bộ lọc Madgwick (beta = 0.1)
    madgwick_filter = madgwick.Madgwick(0.000158)

    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True) # Tự tạo thư mục logs nếu chưa có
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{log_dir}/imu_data_200hz_{timestamp_str}.csv"

    csv_file = open(csv_filename, mode='w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    
    # Ghi tiêu đề (Header) theo chuẩn dữ liệu của Kalibr / OpenICC
    csv_writer.writerow([
        "timestamp", 
        "roll_rad", "pitch_rad", "yaw_rad", 
        "q_w", "q_x", "q_y", "q_z", 
        "gx_rad", "gy_rad", "gz_rad", 
        "ax_g", "ay_g", "az_g", 
        "mx", "my", "mz"
    ])

    # Chờ 5 giây để điện áp cảm biến ổn định hẳn
    time.sleep(5)
    last_time = time.perf_counter()
    last_print_time = time.perf_counter()
    packet_timestamp = time.monotonic()
    PRINT_INTERVAL = 0.5
    try:
        next_time = time.perf_counter() + LOOP_DELAY

        while not stop_event.is_set():
            try:
                # Ghi nhận mốc thời gian thực tế để tính toán tích phân động
                current_time = time.perf_counter()
                dt = current_time - last_time
                if dt > 0.05: dt = 0.005
                last_time = current_time

                # 3. ĐỌC DỮ LIỆU THÔ TỪ CẢM BIẾN
                ax_raw, ay_raw, az_raw, wx_raw, wy_raw, wz_raw = mpu6050_conv()
                mx_raw, my_raw, mz_raw = AK8963_conv()

                # 4. ÁP DỤNG CÔNG THỨC HIỆU CHUẨN TUYẾN TÍNH
                ax_calib = (MX_ACC * ax_raw) + BX_ACC
                ay_calib = (MY_ACC * ay_raw) + BY_ACC
                az_calib = (MZ_ACC * az_raw) + BZ_ACC

                wx_calib_dps = wx_raw - WX_OFF
                wy_calib_dps = wy_raw - WY_OFF
                wz_calib_dps = wz_raw - WZ_OFF
                
                mx_calib = mx_raw - MX_MAG_OFF
                my_calib = my_raw - MY_MAG_OFF
                mz_calib = mz_raw - MZ_MAG_OFF

                # 5. ĐỒNG BỘ TRỤC TỌA ĐỘ (COORDINATE ALIGNMENT)
                # Đưa hệ trục AK8963 về cùng hệ ENU (hoặc NED) với MPU6500
                mx_aligned = my_calib
                my_aligned = mx_calib
                mz_aligned = -mz_calib

                # Đổi Gyro sang Radian/giây cho bộ lọc
                wx_rad = math.radians(wx_calib_dps)
                wy_rad = math.radians(wy_calib_dps)
                wz_rad = math.radians(wz_calib_dps)
                
                # print(f"Gyro Calib (dps) | X: {wx_calib_dps:.4f} | Y: {wy_calib_dps:.4f} | Z: {wz_calib_dps:.4f}")
                # 6. CẬP NHẬT BỘ LỌC MADGWICK 9-DOF
                sub_dt = dt / 5.0
                
                for _ in range(5):
                    madgwick_filter.updateRollAndPitch(
                        ax_calib, ay_calib, az_calib,
                        wx_calib_dps, wy_calib_dps, wz_calib_dps,
                        # mx_aligned, my_aligned, mz_aligned,
                        sub_dt  # Sử dụng sub_dt đã chia nhỏ ở đây
                    )

                # 7. TRÍCH XUẤT GÓC EULER
                roll_rad = math.radians(madgwick_filter.roll)
                pitch_rad = math.radians(madgwick_filter.pitch)
                yaw_rad = math.radians(madgwick_filter.yaw)
                
                # Lấy dữ liệu số phức Quaternion [w, x, y, z] từ thư viện gốc
                w, x, y, z = madgwick_filter.q

                packet_timestamp = time.monotonic()

                csv_writer.writerow([
                    packet_timestamp,
                    roll_rad, pitch_rad, yaw_rad,
                    w, x, y, z,
                    wx_rad, wy_rad, wz_rad,
                    ax_calib, ay_calib, az_calib,
                    mx_aligned, my_aligned, mz_aligned
                ])

                new_data = {
                    "timestamp": packet_timestamp,
                    "roll": roll_rad,          
                    "pitch": pitch_rad,        
                    "yaw": yaw_rad,            
                    "quaternion": [w, x, y, z],
                    "gyro": [wx_rad, wy_rad, wz_rad],
                    "accel": [ax_calib, ay_calib, az_calib],
                    "mag": [mx_aligned, my_aligned, mz_aligned]
                }
                
                put_latest_to_queue(q_imu_control, new_data)
                put_latest_to_queue(q_imu_mavlink, new_data)

                if q_imu_video is not None:
                    imu_packet = {
                        "timestamp": packet_timestamp,
                        "gyro_raw": [wz_rad]
                    }
                    put_latest_to_queue(q_imu_video, imu_packet)

                # ========================================================
                # CƠ CHẾ LOG ĐÁNH GIÁ HỆ THỐNG (CHẠY NGẦM SAU MỖI 0.5 GIÂY)
                # ========================================================
                if (current_time - last_print_time) >= PRINT_INTERVAL:
                    last_print_time = current_time
                    
                    r_deg = madgwick_filter.roll
                    p_deg = madgwick_filter.pitch
                    y_deg = madgwick_filter.yaw
                    
                    # print("\n" + "="*65)
                    # print(f" [LOG IMU EVALUATION] - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                    # print("="*65)
                    # print(f" GÓC EULER (Độ)   | Roll: {r_deg:6.1f}° | Pitch: {p_deg:6.1f}° | Yaw: {y_deg:6.1f}°")
                    # print(f" QUATERNION       | W: {w:5.2f} | X: {x:5.2f} | Y: {y:5.2f} | Z: {z:5.2f}")
                    # print(f" GIA TỐC KẾ (g)   | ax: {ax_calib:5.2f} | ay: {ay_calib:5.2f} | az: {az_calib:5.2f}")
                    # print(f" TỪ KẾ (aligned)  | mx: {mx_aligned:5.1f} | my: {my_aligned:5.1f} | mz: {mz_aligned:5.1f}")
                    # print("="*65)
            except Exception as loop_err:
                print(f"[IMU LOOP ERROR] Phát hiện lỗi: {loop_err}")
                time.sleep(0.002)
                continue

            while time.perf_counter() < next_time:
                time.sleep(0.0005)

            next_time += LOOP_DELAY
            
    except Exception as e:
        print(f"[IMU] Lỗi nghiêm trọng trong vòng lặp đọc: {e}")


def set_gps_baud(ser):
    # UBX-CFG-PRT set 115200
    cmd = bytes([
        0xB5,0x62,0x06,0x00,0x14,0x00,
        0x01,0x00,0x00,0x00,
        0xD0,0x08,0x00,0x00,
        0x00,0xC2,0x01,0x00,  # 115200
        0x07,0x00,0x03,0x00,
        0x00,0x00,0x00,0x00,
        0xC0,0x7E
    ])
    ser.write(cmd)
    time.sleep(0.5)

def gps_task(config, q_gps_control, q_gps_mavlink, stop_event, gps_ready_event):
    # Lấy cấu hình từ file config
    gps_config = config["config"]["hardware"]
    port = gps_config["gps_serial_port"]  
    baudrate = gps_config["gps_baudrate"]

    # Chu kỳ đo mục tiêu (200ms tương ứng với 5Hz như bạn đã test mượt)
    TARGET_MEAS_RATE = 200 

    # Khởi tạo bộ đệm dữ liệu GPS
    gps_data = {
        "lat": 0.0,
        "lon": 0.0,
        "alt": 0.0,
        "fix": 1,
        "hdop": 99.99,
        "vdop": 99.99,
        "sats": 0,
        "speed": 0.0,
        "cog_cdeg": 65535
    }

    try:
        print(f"[GPS Thread] Đang kết nối tới cổng {port} tại {baudrate} baud...")
        stream = Serial(port, 9600, timeout=0.1)
        set_gps_baud(stream)
        stream.close()
        time.sleep(0.5)

        with Serial(port, baudrate, timeout=0.1) as stream:
            # =================================================================
            # TẦNG 1: CẤU HÌNH GPS (CHẠY DUY NHẤT 1 LẦN KHI KHỞI ĐỘNG LUỒNG)
            # =================================================================
            print(f"--- [M10 SETUP] Đang nạp cấu hình tối ưu 5Hz cho AGV ---")
            
            # 1. Cấu hình hệ thống vệ tinh (GPS + BeiDou)
            msg_gnss = UBXMessage(
                "CFG", "CFG-GNSS", SET,
                msgVer=0, numConfigBlocks=5,
                gnssId_01=0, resTrkCh_01=8, maxTrkCh_01=16, flags_01=0x00010001,
                gnssId_02=1, resTrkCh_02=1, maxTrkCh_02=3,  flags_02=0x00010001,
                gnssId_03=2, resTrkCh_03=4, maxTrkCh_03=8,  flags_03=0x00010001, 
                gnssId_04=3, resTrkCh_04=8, maxTrkCh_04=16, flags_04=0x00010001,
                gnssId_05=6, resTrkCh_05=3, maxTrkCh_05=3,  flags_05=0x00010001
            )
            stream.write(msg_gnss.serialize())
            time.sleep(0.1)

            # 2. Ép góc ngẩng 10° và chuyển chế độ Automotive
            msg_nav5 = UBXMessage(
                "CFG", "CFG-NAV5", SET,
                mask=0x0003, dynModel=4, fixMode=3, fixedAlt=0, fixedAltVar=0,
                minElev=10, drLimit=0, pDop=250, tDop=250, pAcc=100, tAcc=350,
                staticHoldThresh=0, dgnsTimeout=0, cnoThreshNumSats=0, cnoThresh=0,
                res=0, staticHoldMaxDist=0, utcStandard=0
            )
            stream.write(msg_nav5.serialize())
            time.sleep(0.1)

            # 3. Thay đổi chu kỳ đo thành 200ms (5Hz)
            msg_rate = UBXMessage(
                "CFG", "CFG-RATE", SET,
                measRate=TARGET_MEAS_RATE, 
                navRate=1, 
                timeRef=1
            )
            stream.write(msg_rate.serialize())
            time.sleep(0.1)

            # 4. Bộ lọc bản tin NMEA tinh gọn: Tắt GSV, VTG, GLL
            msg_disable_gsv = UBXMessage("CFG", "CFG-MSG", SET, msgClass=240, msgID=3, rateUART1=0)
            msg_disable_vtg = UBXMessage("CFG", "CFG-MSG", SET, msgClass=240, msgID=5, rateUART1=0)
            msg_disable_gll = UBXMessage("CFG", "CFG-MSG", SET, msgClass=240, msgID=1, rateUART1=0)
            stream.write(msg_disable_gsv.serialize())
            stream.write(msg_disable_vtg.serialize())
            stream.write(msg_disable_gll.serialize())
            
            # Giữ lại GGA, RMC ở chu kỳ gốc, hạ tần số gói GSA xuống chu kỳ 4 để tránh nghẽn
            msg_enable_gga = UBXMessage("CFG", "CFG-MSG", SET, msgClass=240, msgID=0, rateUART1=1)  
            msg_enable_rmc = UBXMessage("CFG", "CFG-MSG", SET, msgClass=240, msgID=4, rateUART1=1)  
            msg_rate_gsa = UBXMessage("CFG", "CFG-MSG", SET, msgClass=240, msgID=2, rateUART1=5)    
            stream.write(msg_enable_gga.serialize())
            stream.write(msg_enable_rmc.serialize())
            stream.write(msg_rate_gsa.serialize())
            time.sleep(0.1)

            # 5. Lưu cấu hình vào RAM BBR dự phòng
            save_msg = UBXMessage(
                "CFG", "CFG-CFG", SET,
                clearMask=b"\x00\x00\x00\x00", saveMask=b"\xff\xff\x00\x00",  
                loadMask=b"\x00\x00\x00\x00", deviceMask=b"\x01"              
            )
            stream.write(save_msg.serialize())
            time.sleep(0.3) # Dành thời gian cho chip lưu trạng thái ổn định
            
            print(f"--- [SETUP OK] GPS đã chạy ở {1000 / TARGET_MEAS_RATE:.1f}Hz. Bắt đầu luồng đọc... ---")
            # # =================================================================
            # TẦNG 2: LUỒNG ĐỌC DỮ LIỆU CHÍNH (VÒNG LẶP CHẠY LIÊN TỤC)
            # =================================================================
            ubr = UBXReader(stream)
            last_log_time = 0.0
            
            gga_count = 0
            hz_start_time = time.time()
            actual_hz = 0.0

            while not stop_event.is_set():
                try:
                    (raw_data, parsed_data) = ubr.read()

                    if not parsed_data:
                        time.sleep(0.001)
                        continue

                    identity = parsed_data.identity

                    # 1. Trích xuất vận tốc và hướng từ gói RMC
                    if 'RMC' in identity:
                        if hasattr(parsed_data, 'spd') and parsed_data.spd is not None and parsed_data.spd != '':
                            try: gps_data['speed'] = int(float(parsed_data.spd) * 0.514444)
                            except (ValueError, TypeError): gps_data['speed'] = 0
                        
                        if hasattr(parsed_data, 'cog') and parsed_data.cog is not None and parsed_data.cog != '':
                            try: gps_data['cog_cdeg'] = int(float(parsed_data.cog) * 100)
                            except (ValueError, TypeError): gps_data['cog_cdeg'] = 65535

                    # 2. Trích xuất chỉ số sai số hình học từ gói GSA
                    elif 'GSA' in identity:
                        if hasattr(parsed_data, 'HDOP') and parsed_data.HDOP is not None and parsed_data.HDOP != '':
                            try: gps_data['hdop'] = float(parsed_data.HDOP)
                            except (ValueError, TypeError): gps_data['hdop'] = 99.99
                        if hasattr(parsed_data, 'VDOP') and parsed_data.VDOP is not None and parsed_data.VDOP != '':
                            try: gps_data['vdop'] = float(parsed_data.VDOP)
                            except (ValueError, TypeError): gps_data['vdop'] = 99.99

                    # 3. Lấy tọa độ cốt lõi từ gói GGA và kích hoạt đẩy dữ liệu đi
                    elif 'GGA' in identity:
                        gga_count += 1
                        now = time.time()
                        time_delta = now - hz_start_time
                        if time_delta >= 2.0:  # Cứ mỗi 2 giây, tính toán tần số trung bình một lần
                            actual_hz = gga_count / time_delta
                            gga_count = 0
                            hz_start_time = now

                        try:
                            gps_data['lat'] = float(parsed_data.lat) if parsed_data.lat and parsed_data.lat != '' else 0.0
                            gps_data['lon'] = float(parsed_data.lon) if parsed_data.lon and parsed_data.lon != '' else 0.0
                            gps_data['alt'] = float(parsed_data.alt) if parsed_data.alt and parsed_data.alt != '' else 0.0
                        except (ValueError, TypeError):
                            gps_data['lat'], gps_data['lon'], gps_data['alt'] = 0.0, 0.0, 0.0

                        try: gps_data['sats'] = int(parsed_data.numSV) if parsed_data.numSV else 0
                        except (ValueError, TypeError): gps_data['sats'] = 0
                        
                        try: nmea_qual = int(parsed_data.quality) if parsed_data.quality else 0
                        except (ValueError, TypeError): nmea_qual = 0

                        # Map trạng thái Fix chuẩn MAVLink cho Ground Control Station
                        if nmea_qual == 0:   mav_fix_type = 1
                        elif nmea_qual == 1: mav_fix_type = 3
                        elif nmea_qual == 2: mav_fix_type = 4
                        elif nmea_qual == 4: mav_fix_type = 6
                        elif nmea_qual == 5: mav_fix_type = 5
                        else:                mav_fix_type = 3
                        gps_data['fix'] = mav_fix_type

                        # Bật cờ thông báo GPS sẵn sàng khi có tọa độ và fix >= 3D
                        if gps_data['lat'] != 0.0 and gps_data['lon'] != 0.0 and mav_fix_type >= 3:
                            if not gps_ready_event.is_set():
                                gps_ready_event.set()

                        # Copy dữ liệu để tránh xung đột luồng (Thread-safe)
                        gps_data_send = gps_data.copy()
                        
                        # In log kiểm tra trạng thái định kỳ mỗi 2 giây
                        current_time = time.time()
                        if current_time - last_log_time >= 2.0:
                            fix_labels = {1: "NO FIX", 3: "3D FIX", 4: "DGPS", 5: "RTK Flo", 6: "RTK Fix"}
                            fix_text = fix_labels.get(gps_data['fix'], "UNKNOWN")
                            # print(f"[AGV GPS] TẦN SỐ THỰC: {actual_hz:.2f} Hz | [AGV GPS] Vệ tinh: {gps_data['sats']:02d} | Trạng thái: {fix_text:<7} | HDOP: {gps_data['hdop']:.2f}")
                            last_log_time = current_time

                        # Đẩy vào các Queue định tuyến hệ thống xe tự hành
                        put_latest_to_queue(q_gps_control, gps_data_send)
                        put_latest_to_queue(q_gps_mavlink, gps_data_send)

                except Exception as loop_err:
                    # Gặp gói tin lỗi hoặc nhiễu đường truyền thì bỏ qua để tránh sập luồng
                    continue
                time.sleep(0.001)

    except Exception as e:
        print(f"Lỗi hệ thống GPS: {e}")
    finally:
        print("[GPS Thread] Đã dừng luồng đọc GPS an toàn.")