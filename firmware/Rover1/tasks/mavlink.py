import os
os.environ['MAVLINK20'] = '1'
import asyncio
import queue
import time
import math
import numpy as np # Cần thêm numpy để giải mã mảng từ Shared Memory
from pymavlink import mavutil

robot_state = {
    "lat": 0.0, "lon": 0.0, "alt": 0.0,
    "fix": 0, "sats": 0, "hdop": 99.0, "vdop": 99.0,
    "roll": 0.0, "pitch": 0.0, "yaw": 0.0,
    "q": [1.0, 0.0, 0.0, 0.0],
    "roll_speed": 0.0, "pitch_speed": 0.0, "yaw_speed": 0.0,
    "speed": 0.0,
    "armed": False,
    "camera_active": False,
    "lidar_active": False,
    "voltage": 12000,          
    "current": 0,
    "battery_remaining": 100,
    "current_target_wp": 0
}

mission_state = {
    "receiving": False,       
    "total_count": 0,         
    "current_seq": 0,         
    "waypoints": [],          
    "gcs_sys_id": 255,        
    "gcs_comp_id": 190
}

def map_range(value, input_min, input_max, output_min, output_max):
    if value < input_min: value = input_min
    if value > input_max: value = input_max
    if input_max == input_min: return output_min
    return output_min + (value - input_min) * (output_max - output_min) / (input_max - input_min)

def manual_control_to_velocity(x, y):
    vx = map_range(x, -1000, 1000, -100, 100)
    wz = map_range(y, -1000, 1000, 100, -100)
    return vx, wz

async def qgc_receiver_task(master, cmd_queue, camera_active_event, lidar_active_event, q_path):
    print("[Receiver] Lắng nghe yêu cầu từ QGC...")
    while True:
        try:
            # Lấy gói tin ở chế độ không chặn (blocking=False) để không làm treo event loop
            msg = master.recv_match(blocking=False)
            if msg:
                msg_type = msg.get_type()

                if msg_type == 'PARAM_REQUEST_LIST':
                    master.mav.param_value_send(b"STARTUP_PARAM", 1.0, mavutil.mavlink.MAV_PARAM_TYPE_REAL32, 1, 0)

                elif msg_type == 'COMMAND_LONG':
                    if msg.command == 400:
                        if msg.param1 == 1.0:
                            robot_state["armed"] = True
                            cmd_queue.put_nowait({"type": "status", "armed": True})
                        elif msg.param1 == 0.0:
                            robot_state["armed"] = False
                            cmd_queue.put_nowait({"type": "status", "armed": False})
                        
                        master.mav.command_ack_send(
                            msg.command, mavutil.mavlink.MAV_RESULT_ACCEPTED, 
                            0, 0, msg.get_srcSystem(), msg.get_srcComponent()
                        )
                    
                    # 2. Nút bấm BẬT CAMERA (Command ID: 2500)
                    elif msg.command == 2500:
                        print("[Lệnh từ QGC] -> Yêu cầu BẬT CAMERA!")
                        robot_state["camera_active"] = not robot_state["camera_active"]
                        status_str = "Camera ON" if robot_state["camera_active"] else "Camera OFF"
                        if robot_state["camera_active"]: camera_active_event.set()
                        else: camera_active_event.clear()
                        master.mav.statustext_send(mavutil.mavlink.MAV_SEVERITY_INFO, status_str.encode('utf-8'))
                        master.mav.command_ack_send(msg.command, mavutil.mavlink.MAV_RESULT_ACCEPTED, 0, 0, msg.get_srcSystem(), msg.get_srcComponent())

                    # 4. Nút bấm BẬT LIDAR (Command ID: 2510)
                    elif msg.command == 2510:
                        robot_state["lidar_active"] = not robot_state["lidar_active"]
                        status_str = "LiDAR ON" if robot_state["lidar_active"] else "LiDAR OFF"
                        if robot_state["lidar_active"]: lidar_active_event.set()
                        else: lidar_active_event.clear()
                        master.mav.statustext_send(mavutil.mavlink.MAV_SEVERITY_INFO, status_str.encode('utf-8'))
                        master.mav.command_ack_send(msg.command, mavutil.mavlink.MAV_RESULT_ACCEPTED, 0, 0, msg.get_srcSystem(), msg.get_srcComponent())

                elif msg_type == 'MANUAL_CONTROL':
                    vx, wz = manual_control_to_velocity(msg.x, msg.y)
                    # Đóng gói tọa độ dịch chuyển gửi qua cmd_queue cho tiến trình điều khiển động cơ
                    lenh_joystick = {"type": "drive", "vx": vx, "wz": wz}
                    # print(lenh_joystick)
                    try:
                        cmd_queue.put_nowait(lenh_joystick)
                    except queue.Full:
                        pass

                elif msg_type == 'MISSION_REQUEST_LIST':
                    master.mav.mission_count_send(
                        msg.get_srcSystem(), msg.get_srcComponent(),
                        len(mission_state["waypoints"]), mavutil.mavlink.MAV_MISSION_TYPE_MISSION
                    )

                elif msg_type == 'MISSION_REQUEST_INT':
                    req_seq = msg.seq
                    if req_seq < len(mission_state["waypoints"]):
                        wp = mission_state["waypoints"][req_seq]
                        master.mav.mission_item_int_send(
                            msg.get_srcSystem(), msg.get_srcComponent(), req_seq,
                            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, wp["command"],
                            1 if req_seq == robot_state["current_target_wp"] else 0,
                            1, 0, 0, 0, 0,
                            int(wp["lat"] * 1e7), int(wp["lon"] * 1e7), 10.0,
                            mavutil.mavlink.MAV_MISSION_TYPE_MISSION
                        )

                elif msg_type == 'MISSION_COUNT':
                    mission_state["gcs_sys_id"] = msg.get_srcSystem()
                    mission_state["gcs_comp_id"] = msg.get_srcComponent()
                    incoming_mission_type = getattr(msg, 'mission_type', mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
                    
                    if incoming_mission_type != mavutil.mavlink.MAV_MISSION_TYPE_MISSION:
                        master.mav.mission_ack_send(
                            mission_state["gcs_sys_id"], mission_state["gcs_comp_id"],
                            mavutil.mavlink.MAV_MISSION_ACCEPTED, incoming_mission_type
                        )
                        continue
                    
                    mission_state["total_count"] = msg.count
                    mission_state["current_seq"] = 0
                    
                    if msg.count == 0:
                        print("\n[Mission] QGC yêu cầu XÓA SẠCH bản đồ lộ trình.")
                        master.mav.mission_ack_send(mission_state["gcs_sys_id"], mission_state["gcs_comp_id"], mavutil.mavlink.MAV_MISSION_ACCEPTED, mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
                        mission_state["waypoints"] = []
                        robot_state["current_target_wp"] = 0
                        mission_state["receiving"] = False
                        try: q_path.put_nowait([])
                        except queue.Full: pass
                    else:
                        mission_state["receiving"] = True
                        mission_state["waypoints"] = [] 
                        print(f"\n[Mission] QGC yêu cầu nạp {msg.count} Waypoints mới.")
                        master.mav.mission_request_int_send(mission_state["gcs_sys_id"], mission_state["gcs_comp_id"], 0, mavutil.mavlink.MAV_MISSION_TYPE_MISSION)

                elif msg_type == 'MISSION_ITEM_INT' and mission_state["receiving"]:
                    if msg.seq == mission_state["current_seq"]:
                        mission_state["waypoints"].append({
                            "seq": msg.seq, "lat": msg.x / 1e7, "lon": msg.y / 1e7, "command": msg.command
                        })
                        print(f" -> Đã nhận WP {msg.seq}: Lat={msg.x / 1e7}, Lon={msg.y / 1e7}")
                        mission_state["current_seq"] += 1
                        
                        if mission_state["current_seq"] < mission_state["total_count"]:
                            master.mav.mission_request_int_send(mission_state["gcs_sys_id"], mission_state["gcs_comp_id"], mission_state["current_seq"], mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
                        else:
                            master.mav.mission_ack_send(mission_state["gcs_sys_id"], mission_state["gcs_comp_id"], mavutil.mavlink.MAV_MISSION_ACCEPTED, mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
                            print(">>> [XONG] NẠP LỘ TRÌNH LÊN XE THÀNH CÔNG! <<<")
                            robot_state["current_target_wp"] = 0 
                            robot_state["armed"] = True  
                            mission_state["receiving"] = False
                            
                            try:
                                q_path.put_nowait(mission_state["waypoints"])
                            except queue.Full:
                                print("[Cảnh báo] Hàng đợi q_path bị đầy, không thể đẩy lộ trình!")
        except Exception as e:
            print(f"Lỗi trong vòng lặp nhận MAVLink: {e}")

        await asyncio.sleep(0.0166) # Nhịp quét nhận lệnh 60Hz nhạy bén

async def update_robot_state_task(q_imu_mavlink, q_gps_mavlink):
    while True:
        try:
            while True:
                imu_data = q_imu_mavlink.get_nowait()
                robot_state["roll"] = imu_data.get("roll", 0.0)
                robot_state["pitch"] = imu_data.get("pitch", 0.0)
                robot_state["yaw"] = imu_data.get("yaw", 0.0)
                robot_state["q"] = imu_data.get("quaternion", [1.0, 0.0, 0.0, 0.0])

                gyro = imu_data.get("gyro", [0.0, 0.0, 0.0])
                robot_state["roll_speed"] = gyro[0]
                robot_state["pitch_speed"] = gyro[1]
                robot_state["yaw_speed"] = gyro[2]
        except queue.Empty:
            pass

        try:
            while True:
                gps_data = q_gps_mavlink.get_nowait()
                robot_state["lat"] = gps_data.get("lat", 0.0)
                robot_state["lon"] = gps_data.get("lon", 0.0)
                robot_state["alt"] = gps_data.get("alt", 0.0)
                robot_state["fix"] = gps_data.get("fix", 0)
                robot_state["sats"] = gps_data.get("sats", 0)
                robot_state["hdop"] = gps_data.get("hdop", 99.0)
                robot_state["vdop"] = gps_data.get("vdop", 99.0)
                robot_state["speed"] = gps_data.get("speed", 0.0)
        except queue.Empty:
            pass
        await asyncio.sleep(0.05)

async def send_sys_status(master):
    """Tác vụ phát gói tin SYS_STATUS với tần suất 1Hz"""
    while True:
        try:
            master.mav.sys_status_send(
                0, 0, 0, 0,
                robot_state["voltage"],             # Điện áp pin (mV)
                robot_state["current"],             # Dòng điện pin (mA)
                robot_state["battery_remaining"],    # Phần trăm pin (%)
                0, 0, 0, 0, 0, 0
            )
        except Exception as e:
            print(f"Lỗi gửi SYS_STATUS: {e}")
        await asyncio.sleep(1.0)                     # Chu kỳ 1Hz

async def send_battery_status(master):
    """Tác vụ phát gói tin BATTERY_STATUS với tần suất 1Hz"""
    while True:
        try:
            voltages = [65535] * 10
            cell_voltage = int(robot_state["voltage"] / 3) # Giả lập 3 cell pin từ file test
            voltages[0] = cell_voltage
            voltages[1] = cell_voltage
            voltages[2] = cell_voltage

            # MAVLink BATTERY_STATUS yêu cầu dòng điện tính bằng centi-amperes (10mA)
            current_ca = int(robot_state["current"] / 10)

            master.mav.battery_status_send(
                0,
                mavutil.mavlink.MAV_BATTERY_FUNCTION_ALL,
                mavutil.mavlink.MAV_BATTERY_TYPE_LIPO,
                2500,                                # Nhiệt độ tạm tính 25°C
                voltages,
                current_ca,
                -1, -1,
                robot_state["battery_remaining"]
            )
        except Exception as e:
            print(f"Lỗi gửi BATTERY_STATUS: {e}")
        await asyncio.sleep(1.0)

async def send_heartbeat(master):
    """Tác vụ 1: Phát Heartbeat độc lập với tần suất 1Hz"""
    while True:
        try:
            base_mode = (
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
                | mavutil.mavlink.MAV_MODE_FLAG_MANUAL_INPUT_ENABLED
            )
            
            if robot_state["armed"]:
                base_mode |= mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
            
            master.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GROUND_ROVER,
                mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
                base_mode,
                0,
                mavutil.mavlink.MAV_STATE_ACTIVE,
            )
        except Exception as e:
            print(f"Lỗi gửi Heartbeat: {e}")
        await asyncio.sleep(1) 

async def send_lidar(master, shm, lock):
    """Tác vụ 2: Đọc dữ liệu từ Shared Memory và bắn gói tin né vật cản (10Hz)"""
    MIN_DISTANCE_CM = 20
    MAX_DISTANCE_CM = 1200 
    UNKNOWN = 65535
    while True:
        try:
            with lock:
                byte_lidar = shm.buf[8:152]
            
            distances_bins = np.frombuffer(byte_lidar, dtype=np.uint16).tolist()
            
            # 4. Đóng gói và gửi qua MAVLink
            master.mav.obstacle_distance_send(
                time_usec=int(time.time() * 1e6),
                sensor_type=mavutil.mavlink.MAV_DISTANCE_SENSOR_LASER,
                distances=distances_bins,
                increment=2,          
                min_distance=MIN_DISTANCE_CM,
                max_distance=MAX_DISTANCE_CM,
                increment_f=2.5,
                angle_offset=-90.0,
                frame=mavutil.mavlink.MAV_FRAME_BODY_FRD, # Hệ tọa độ chuẩn thân xe
            )
            
        except Exception as e:
            print(f"Lỗi xử lý/gửi dữ liệu LiDAR qua MAVLink: {e}")
            
        await asyncio.sleep(0.1) # Giữ nhịp 10Hz ổn định

async def send_attitude(master):
    """Tác vụ 3: Phát gói tin ATTITUDE_QUATERNION (ID 31) với tần suất 10Hz"""
    while True:
        try:
            q = robot_state["q"]
            master.mav.attitude_send(
                int(time.time() * 1000) & 0xFFFFFFFF,  # time_boot_ms
                robot_state["roll"],                  # roll: Góc nghiêng ngang (rad)
                robot_state["pitch"],                 # pitch: Góc nghiêng dọc (rad)
                robot_state["yaw"],
                robot_state["roll_speed"],             # rollspeed (rad/s)
                robot_state["pitch_speed"],            # pitchspeed (rad/s)
                robot_state["yaw_speed"],              # yawspeed (rad/s)
            )
        except Exception as e:
            print(f"Lỗi gửi ATTITUDE: {e}")
        await asyncio.sleep(0.034)

async def send_global_position(master):
    """Tác vụ phát gói tin GLOBAL_POSITION_INT (ID 33) lên GCS với tần suất 10Hz"""
    last_sync_time = 0
    while True:
        try:
            # 1. Chuyển đổi tọa độ sang số nguyên (degE7)
            lat_mav = int(robot_state["lat"] * 1e7)
            lon_mav = int(robot_state["lon"] * 1e7)
            alt_mav = int(robot_state["alt"] * 1000) # Đổi từ mét sang milimét
            
            # 2. Chuyển đổi góc Yaw từ Radian sang Centidegrees (cdeg)
            yaw_deg = math.degrees(robot_state["yaw"])
            # Đảm bảo góc luôn dương (0 đến 359.99 độ)
            if yaw_deg < 0:
                yaw_deg += 360
            hdg_mav = int(yaw_deg * 100)

            vel_cm_s = int(robot_state["speed"] * 100)
            # 3. Gửi gói tin qua MAVLink
            master.mav.global_position_int_send(
                int(time.time() * 1000) & 0xFFFFFFFF,  # time_boot_ms
                lat_mav,                      # lat
                lon_mav,                      # lon
                alt_mav,                      # alt (MSL)
                0,                            # relative_alt
                vel_cm_s, 0, 0,               # vx, vy, vz (chưa dùng vận tốc)
                hdg_mav                       # hdg
            )

            now = time.time()
            if now - last_sync_time > 1.0:
                if len(mission_state["waypoints"]) > 0:
                    master.mav.mission_current_send(robot_state["current_target_wp"])
                last_sync_time = now

        except Exception as e:
            print(f"Lỗi gửi GLOBAL_POSITION_INT: {e}")
            
        await asyncio.sleep(0.2) # Chu kỳ 5Hz

async def send_gps_raw(master):
    """Tác vụ phát gói tin GPS_RAW_INT (ID 24) lên GCS với tần suất 1Hz"""
    while True:
        try:
            # 1. Chuyển đổi tọa độ và sai số sang chuẩn số nguyên MAVLink
            lat_mav = int(robot_state["lat"] * 1e7)
            lon_mav = int(robot_state["lon"] * 1e7)
            alt_mav = int(robot_state["alt"] * 1000)
            eph_mav = min(int(robot_state["hdop"] * 100), 65535)
            epv_mav = min(int(robot_state["vdop"] * 100), 65535)
            vel_cm_s = min(int(robot_state["speed"] * 100), 65535)

            # 2. Gửi gói tin thô qua MAVLink
            master.mav.gps_raw_int_send(
                int(time.time() * 1e6),         # time_usec
                robot_state["fix"],             # fix_type
                lat_mav,                        # lat
                lon_mav,                        # lon
                alt_mav,                        # alt
                eph_mav,                        # HDOP
                epv_mav,                        # VDOP
                vel_cm_s, 0xFFFF,                 # vel, cog (chưa dùng)
                robot_state["sats"]             # satellites_visible
            )
        except Exception as e:
            print(f"Lỗi gửi GPS_RAW_INT: {e}")
            
        await asyncio.sleep(0.2) # Chu kỳ 5Hz ổn định

async def simulated_rover_movement_task(master):
    """Tác vụ giả lập (Chỉ kích hoạt nếu bạn test offline không có robot thật)"""
    R_ACCEPTANCE = 2.0       
    MAX_SPEED_MS = 4.0       
    while True:
        if robot_state["armed"] and len(mission_state["waypoints"]) > 0:
            target_idx = robot_state["current_target_wp"]
            if target_idx >= len(mission_state["waypoints"]):
                print("\n[Simulation] Hết lộ trình! Dừng xe.")
                robot_state["speed"] = 0.0
                robot_state["armed"] = False
                continue
                
            target_wp = mission_state["waypoints"][target_idx]
            d_lat_m = (target_wp["lat"] - robot_state["lat"]) * 111139
            d_lon_m = (target_wp["lon"] - robot_state["lon"]) * 111139 * math.cos(math.radians(robot_state["lat"]))
            distance = math.sqrt(d_lat_m**2 + d_lon_m**2)
            
            robot_state["speed"] = MAX_SPEED_MS
            if distance <= R_ACCEPTANCE:
                print(f"\n[Simulation] Cán mốc WP {target_idx}!")
                master.mav.mission_item_reached_send(target_idx)
                robot_state["current_target_wp"] = target_idx + 1
            else:
                step = MAX_SPEED_MS * 0.1
                robot_state["lat"] += (d_lat_m / distance) * step / 111139
                robot_state["lon"] += (d_lon_m / distance) * step / (111139 * math.cos(math.radians(robot_state["lat"])))
                robot_state["yaw"] = math.atan2(d_lon_m, d_lat_m)
        await asyncio.sleep(0.1)

async def real_vehicle_waypoint_tracker_task(master):
    """Tác vụ chạy nền: Đo khoảng cách GPS thật để tự động chuyển điểm trên QGC"""
    R_ACCEPTANCE = 2.0  # Bán kính chấp nhận điểm (2 mét)
    
    while True:
        try:
            # Chỉ kiểm tra khi xe đã ARM và có danh sách Waypoint
            if robot_state["armed"] and len(mission_state["waypoints"]) > 0:
                target_idx = robot_state["current_target_wp"]
                
                if target_idx < len(mission_state["waypoints"]):
                    target_wp = mission_state["waypoints"][target_idx]
                    
                    # Tính khoảng cách từ GPS THẬT của xe đến Waypoint mục tiêu
                    d_lat_m = (target_wp["lat"] - robot_state["lat"]) * 111139
                    d_lon_m = (target_wp["lon"] - robot_state["lon"]) * 111139 * math.cos(math.radians(robot_state["lat"]))
                    distance = math.sqrt(d_lat_m**2 + d_lon_m**2)
                    
                    if distance <= R_ACCEPTANCE:
                        print(f"\n[Xe Thật] Đã cán mốc hành trình WP {target_idx}!")
                        
                        # 1. Bắn gói tin báo cho QGC biết xe đã đạt tới điểm này (QGC sẽ tắt highlight điểm này)
                        master.mav.mission_item_reached_send(target_idx)
                        
                        # 2. Chuyển mục tiêu sang điểm tiếp theo trong bộ nhớ xe
                        robot_state["current_target_wp"] = target_idx + 1
                        
                        # 3. Ép gửi ngay lập tức lệnh cập nhật điểm mới lên QGC (Điểm tiếp theo sẽ sáng tròn lên)
                        if robot_state["current_target_wp"] < len(mission_state["waypoints"]):
                            master.mav.mission_current_send(robot_state["current_target_wp"])
        except Exception as e:
            print(f"Lỗi theo dõi hành trình xe thật: {e}")
            
        await asyncio.sleep(0.2)

async def luong_mavlink_async(q_imu_mavlink, q_gps_mavlink, q_path, config, shm, lock, cmd_queue, camera_active_event, lidar_active_event):
    """Vòng lặp async chính quản lý các kết nối và hàng đợi"""
    mavlink_config = config["config"]["mavlink_qgc"]
    QGC_IP = mavlink_config["laptop_ip"]
    QGC_PORT = mavlink_config["udp_port"]
    
    master = mavutil.mavlink_connection(f'udpout:{QGC_IP}:{QGC_PORT}', source_system=1, source_component=mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1)
    
    # KÍCH HOẠT SONG SONG 2 TÁC VỤ NỀN: Heartbeat (1Hz) và LiDAR Obstacle (10Hz)
    asyncio.create_task(send_heartbeat(master))
    asyncio.create_task(send_lidar(master, shm, lock))
    asyncio.create_task(update_robot_state_task(q_imu_mavlink, q_gps_mavlink))
    asyncio.create_task(send_attitude(master))
    asyncio.create_task(send_global_position(master))
    asyncio.create_task(send_gps_raw(master))
    asyncio.create_task(qgc_receiver_task(master, cmd_queue, camera_active_event, lidar_active_event, q_path))
    asyncio.create_task(send_sys_status(master))
    asyncio.create_task(send_battery_status(master))
    #asyncio.create_task(simulated_rover_movement_task(master))
    asyncio.create_task(real_vehicle_waypoint_tracker_task(master))
    while True:
        await asyncio.sleep(1.0)

def luong_chay_mavlink(q_imu_mavlink, q_gps_mavlink, q_path, config, shm, lock, cmd_queue, camera_active_event, lidar_active_event):
    """Bệ phóng đồng bộ để kích hoạt tiến trình Asyncio (Đã thêm shm và lock)"""
    asyncio.run(luong_mavlink_async(q_imu_mavlink, q_gps_mavlink, q_path, config, shm, lock, cmd_queue, camera_active_event, lidar_active_event))