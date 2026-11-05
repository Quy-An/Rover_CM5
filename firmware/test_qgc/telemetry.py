import os
# Ép hệ thống chạy MAVLink 2.0 (bắt buộc đối với gói tin Obstacle Distance)
os.environ['MAVLINK20'] = '1'

import sys
import time
import math
import threading
import smbus
import serial
from pyubx2 import UBXReader  
from pymavlink import mavutil
from imusensor.MPU9250 import MPU9250
from rplidar import RPLidar  # Thư viện điều khiển RPLidar

# --- CẤU HÌNH THÔNG SỐ KẾT NỐI MẠNG ---
LAPTOP_IP = "192.168.1.162"     # Thay bằng IP máy tính chạy QGC của bạn
QGC_PORT = 14550                # Cổng UDP mặc định của QGroundControl

# --- CẤU HÌNH PHẦN CỨNG LIDAR ---
LIDAR_PORT = '/dev/ttyUSB0'
LIDAR_BAUD = 115200


def create_mavlink_connection(laptop_ip, qgc_port):
    return mavutil.mavlink_connection(
        f'udpout:{laptop_ip}:{qgc_port}',
        source_system=1,
        source_component=mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1,
    )


def telemetry_loop(mav_conn,vehicle,stop_event=None,heartbeat_period=1.0,send_lock=None):
    print("📡 [Telemetry] Đang bắn dữ liệu tới QGC...")
    last_heartbeat = 0

    while True:
        if stop_event and stop_event.is_set():
            break

        now = time.time()
        if now - last_heartbeat >= heartbeat_period:
            def send_hb():
                with vehicle.lock:
                    armed = vehicle.armed

                base_mode = (
                    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
                    |
                    mavutil.mavlink.MAV_MODE_FLAG_MANUAL_INPUT_ENABLED
                )

                if armed:
                    base_mode |= mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED

                mav_conn.mav.heartbeat_send(
                    mavutil.mavlink.MAV_TYPE_GROUND_ROVER,
                    mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,  # <--- ĐỔI THÀNH CÁI NÀY
                    base_mode,
                    0,
                    mavutil.mavlink.MAV_STATE_ACTIVE,
                )
            if send_lock:
                with send_lock:
                    send_hb()
            else:
                send_hb()
                
            last_heartbeat = now
            print("💚 [Telemetry] -> Đã gửi gói tin Heartbeat...")

        time.sleep(0.01)


def imu_loop(mav_conn,vehicle,stop_event=None,send_lock=None):
    print("📡 [IMU] Đang khởi động cảm biến MPU9250...")
    
    address = 0x68
    bus = smbus.SMBus(1)
    imu = MPU9250.MPU9250(bus, address)
    imu.begin()

    file_path = "/home/pi/calib_mpu9250.json"
    if os.path.exists(file_path):
        print(f"📦 [IMU] Đang nạp file cấu hình hiệu chuẩn từ: {file_path}")
        imu.loadCalibDataFromFile(file_path)
        print("✅ [IMU] Nạp cấu hình thành công!")
    else:
        print(f"⚠️ [IMU] Cảnh báo: Không tìm thấy file {file_path}. Dữ liệu sẽ có sai số lớn.")

    print("🚀 [IMU] Luồng xử lý và đẩy dữ liệu ATTITUDE lên QGC đã sẵn sàng.")

    try:
        while True:
            if stop_event and stop_event.is_set():
                break

            imu.readSensor()
            imu.computeOrientation()

            roll_rad = math.radians(imu.roll)
            pitch_rad = math.radians(imu.pitch)
            yaw_rad = math.radians(imu.yaw)

            roll_speed = imu.GyroVals[0]
            pitch_speed = imu.GyroVals[1]
            yaw_speed = imu.GyroVals[2]

            with vehicle.lock:

                vehicle.roll = roll_rad
                vehicle.pitch = pitch_rad
                vehicle.yaw = yaw_rad

                vehicle.roll_speed = roll_speed
                vehicle.pitch_speed = pitch_speed
                vehicle.yaw_speed = yaw_speed

                vehicle.heading_deg = (
                    math.degrees(yaw_rad)
                ) % 360

            time_boot_ms = int(time.time() * 1000) & 0xFFFFFFFF

            def send_att():
                mav_conn.mav.attitude_send(
                    time_boot_ms,
                    roll_rad,
                    pitch_rad,
                    yaw_rad,
                    roll_speed,
                    pitch_speed,
                    yaw_speed
                )

            if send_lock:
                with send_lock:
                    send_att()
            else:
                send_att()

            time.sleep(0.05)

    except Exception as e:
        print(f"❌ [IMU] Lỗi trong vòng lặp đọc: {e}")


def gps_loop(mav_conn, vehicle, stop_event=None, send_lock=None):
    print("📡 [GPS] Đang kết nối cổng Serial cho GPS (pyubx2)...")
    port = "/dev/serial0"
    baud = 9600
    
    gps_data = {
        'lat': 0, 'lon': 0, 'alt': 0, 
        'fix': 0, 'hdop': 9999, 'vdop': 9999, 'sats': 0,
        'speed_cm_s': 0,      
        'cog_cdeg': 65535     
    }
    
    try:
        ser = serial.Serial(port, baudrate=baud, timeout=1)
        ubr = UBXReader(ser)
        print(f"✅ [GPS] Đã mở thành công cổng {port} (Baudrate: {baud})")
    except Exception as e:
        print(f"❌ [GPS] Lỗi khi cấu hình cổng Serial: {e}")
        return

    print("🚀 [GPS] Luồng giải mã pyubx2 và đẩy dữ liệu GPS_RAW_INT đã sẵn sàng.")

    try:
        while True:
            if stop_event and stop_event.is_set():
                break

            try:
                (raw_data, parsed_data) = ubr.read()
            except Exception:
                continue

            if parsed_data:
                if 'RMC' in parsed_data.identity:
                    if hasattr(parsed_data, 'spd') and parsed_data.spd is not None and parsed_data.spd != '':
                        gps_data['speed_cm_s'] = int(float(parsed_data.spd) * 51.4444)
                    else:
                        gps_data['speed_cm_s'] = 0

                    if hasattr(parsed_data, 'cog') and parsed_data.cog is not None and parsed_data.cog != '':
                        gps_data['cog_cdeg'] = int(float(parsed_data.cog) * 100)
                    else:
                        gps_data['cog_cdeg'] = 65535  

                elif 'GSA' in parsed_data.identity:
                    if hasattr(parsed_data, 'HDOP'): 
                        gps_data['hdop'] = parsed_data.HDOP
                    if hasattr(parsed_data, 'VDOP'): 
                        gps_data['vdop'] = parsed_data.VDOP

                elif 'GGA' in parsed_data.identity:
                    gps_data['lat'] = parsed_data.lat
                    gps_data['lon'] = parsed_data.lon
                    gps_data['alt'] = parsed_data.alt
                    gps_data['sats'] = parsed_data.numSV
                    
                    try:
                        nmea_qual = int(parsed_data.quality) if parsed_data.quality else 0
                    except (ValueError, TypeError):
                        nmea_qual = 0

                    if nmea_qual == 0:
                        mav_fix_type = 1  
                    elif nmea_qual == 1:
                        mav_fix_type = 3  
                    elif nmea_qual == 2:
                        mav_fix_type = 4  
                    elif nmea_qual == 4:
                        mav_fix_type = 6  
                    elif nmea_qual == 5:
                        mav_fix_type = 5  
                    elif nmea_qual == 6:
                        mav_fix_type = 3  
                    else:
                        mav_fix_type = 3  
                    
                    gps_data['fix'] = mav_fix_type

                    lat_mav = int(gps_data['lat'] * 1e7)
                    lon_mav = int(gps_data['lon'] * 1e7)
                    alt_mav = int(gps_data['alt'] * 1000)
                    eph = min(int(gps_data['hdop'] * 100), 65535)
                    epv = min(int(gps_data['vdop'] * 100), 65535)
                    time_usec = int(time.time() * 1e6)

                    with vehicle.lock:

                        vehicle.lat = lat_mav
                        vehicle.lon = lon_mav
                        vehicle.alt = alt_mav

                        vehicle.gps_fix_type = gps_data['fix']

                        vehicle.eph = eph
                        vehicle.epv = epv

                        vehicle.satellites = gps_data['sats']

                        if gps_data['cog_cdeg'] != 65535:
                            vehicle.heading_deg = (
                                gps_data['cog_cdeg'] / 100.0
                            )

                    def send_gps():
                        mav_conn.mav.gps_raw_int_send(
                            time_usec,
                            gps_data['fix'],         
                            lat_mav,                 
                            lon_mav,                 
                            alt_mav,                 
                            eph,                     
                            epv,                     
                            gps_data['speed_cm_s'],  
                            gps_data['cog_cdeg'],    
                            gps_data['sats']         
                        )

                    if send_lock:
                        with send_lock:
                            send_gps()
                    else:
                        send_gps()
                        
                    speed_kph = (gps_data['speed_cm_s'] / 100.0) * 3.6
                    cog_deg = gps_data['cog_cdeg'] / 100.0 if gps_data['cog_cdeg'] != 65535 else 0.0
                    print(f"📍 [GPS] -> Gửi tọa độ: {gps_data['lat']:.6f}, {gps_data['lon']:.6f} | "
                          f"Fix: {gps_data['fix']} | Vệ tinh: {gps_data['sats']} | "
                          f"Hướng: {cog_deg}° | Tốc độ: {speed_kph:.1f} km/h")

    except Exception as e:
        print(f"❌ [GPS] Lỗi xảy ra trong vòng lặp đọc: {e}")
    finally:
        ser.close()
        print("Thử kết nối lại trong trong vòng 5 giây")


def lidar_loop(mav_conn, stop_event=None, send_lock=None):
    """
    SỬA ĐỔI CHUẨN: Sử dụng iter_scans() để thu thập trọn vẹn 1 vòng quét 360 độ
    trước khi đóng gói đồng bộ mảng 72 phần tử gửi lên QGC.
    """
    print("📡 [LIDAR] Đang kết nối với cảm biến RPLIDAR A2M8...")
    lidar = None
    
    try:
        lidar = RPLidar(LIDAR_PORT, baudrate=LIDAR_BAUD)
        lidar.motor_speed = 400  # Điều chỉnh tốc độ quay của Lidar (tùy chọn)
        print("🚀 [LIDAR] Luồng giải mã bằng iter_scans() đã sẵn sàng.")
        
        # iter_scans() trả về một list chứa tất cả các tia đo trúng của 1 vòng xoay toàn vẹn
        for scan in lidar.iter_scans():
            if stop_event and stop_event.is_set():
                break
                
            # Khởi tạo mảng 72 phần tử tương ứng 72 phân vùng (mỗi vùng 5 độ)
            # Mã số 65535 (UINT16_MAX) báo hiệu phân vùng trống / không có vật cản
            distances = [65535] * 72 
            
            # Giải nén cấu trúc 3 phần tử chuẩn của hàm iter_scans()
            for quality, angle, distance in scan:
                if distance > 0:
                    dist_cm = int(distance / 10) # Quy đổi mm (Lidar) sang cm (MAVLink)
                    
                    # Lọc khoảng cách an toàn trong tầm đo của thiết bị
                    if 15 <= dist_cm <= 1200:
                        # Xác định index phân vùng dựa trên góc quét (360 độ / 5 độ = 72 vùng)
                        sector_idx = int(angle / 5) % 72
                        
                        # Logic né vật cản: Lưu giữ khoảng cách GẦN NHẤT phát hiện được trong phân vùng đó
                        if distances[sector_idx] == 65535 or dist_cm < distances[sector_idx]:
                            distances[sector_idx] = dist_cm
            
            # --- ĐÓNG GÓI VÀ BẮN TIN ĐỒNG BỘ SAU KHI ĐÃ CÓ ĐỦ DỮ LIỆU 1 VÒNG QUÉT ---
            time_usec = int(time.time() * 1000000)
            
            def send_lidar():
                mav_conn.mav.obstacle_distance_send(
                    time_usec=time_usec,
                    sensor_type=mavutil.mavlink.MAV_DISTANCE_SENSOR_LASER,          # 0: MAV_DISTANCE_SENSOR_LASER
                    distances=distances,     # Mảng khoảng cách chuẩn 72 phần tử (cm)
                    increment=5,            # Độ rộng phân vùng (5 độ)
                    min_distance=15,        # Tầm đo nhỏ nhất (15 cm)
                    max_distance=1200,      # Tầm đo lớn nhất (1200 cm)
                    increment_f=5.0,        
                    angle_offset=0.0,       # Hướng lệch phân vùng 0 so với mũi xe (0 = thẳng trước)
                    frame=12                # 12: MAV_FRAME_BODY_FRD (Góc hệ tọa độ gắn trên thân robot)
                )
            
            if send_lock:
                with send_lock: send_lidar()
                print(f"📡 [LIDAR] -> Gửi dữ liệu Obstacle Distance (72 vùng) lên QGC.")
            else:
                send_lidar()

    except Exception as e:
        print(f"❌ [LIDAR] Lỗi xảy ra trong vòng lặp đọc: {e}")
    finally:
        print("\n--- [LIDAR] Đang dừng động cơ và giải phóng cổng Lidar ---")
        if lidar:
            try:
                lidar.stop()
                lidar.stop_motor()  
                lidar.disconnect()
                print("✅ [LIDAR] Đã giải phóng thiết bị an toàn.")
            except Exception:
                pass