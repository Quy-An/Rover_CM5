import time

from pymavlink import mavutil


# ============================================================
# Utility
# ============================================================

def map_range(value, input_min, input_max,
              output_min, output_max):

    if value < input_min:
        value = input_min

    if value > input_max:
        value = input_max

    if input_max == input_min:
        return output_min

    return (
        output_min
        + (value - input_min)
        * (output_max - output_min)
        / (input_max - input_min)
    )


def manual_control_to_velocity(x, r):
    """
    QGC MANUAL_CONTROL

    x = throttle
    r = steering

    Chuyển về:
        vx [m/s]
        wz [rad/s]
    """

    vx = map_range(
        x,
        -1000,
        1000,
        -0.7,
        0.7
    )

    wz = map_range(
        r,
        -1000,
        1000,
        -7.0,
        7.0
    )

    return vx, wz


# ============================================================
# MAVLink ACK
# ============================================================

def send_command_ack(
        mav_conn,
        command,
        result=mavutil.mavlink.MAV_RESULT_ACCEPTED):

    mav_conn.mav.command_ack_send(
        command,
        result
    )


# ============================================================
# Main Receiver Loop
# ============================================================

def qgc_receiver_loop(
        mav_conn,
        vehicle,
        stop_event=None,
        send_lock=None):

    print("📥 [Receiver] Listening QGC...")

    while True:
        if stop_event and stop_event.is_set():
            break

        try:
            msg = mav_conn.recv_match(blocking=False)

            if msg is None:
                time.sleep(0.01)
                continue

            msg_type = msg.get_type()

            # ------------------------------------------------
            # Debug (Bỏ qua PARAM_REQUEST_READ để đỡ spam log)
            # ------------------------------------------------
            if msg_type not in (
                'HEARTBEAT',
                'MANUAL_CONTROL',
                'REQUEST_DATA_STREAM',
                'PARAM_REQUEST_READ'
            ):
                print(f"📩 MAVLink RX: {msg_type}")

            # =================================================
            # PARAM REQUEST (Đồng bộ Parameter giả lập)
            # =================================================
            if msg_type == 'PARAM_REQUEST_LIST':
                print("📦 PARAM_REQUEST_LIST -> Đang nạp danh sách tham số...")
                def send_param_list():
                    mav_conn.mav.param_value_send(
                        b"STARTUP_PARAM",
                        1.0,
                        mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
                        1, # Tổng số lượng param = 1
                        0  # Index = 0
                    )
                if send_lock:
                    with send_lock: send_param_list()
                else: send_param_list()

            elif msg_type == 'PARAM_REQUEST_READ':
                # Phản hồi khi QGC hỏi kiểm tra chi tiết tham số cụ thể
                def send_param_read():
                    param_id = msg.param_id.encode('utf-8') if isinstance(msg.param_id, str) else msg.param_id
                    mav_conn.mav.param_value_send(
                        param_id,
                        1.0,
                        mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
                        1,
                        msg.param_index if msg.param_index != -1 else 0
                    )
                if send_lock:
                    with send_lock: send_param_read()
                else: send_param_read()

            # =================================================
            # COMMAND LONG (Gộp chung ARM/DISARM & BUTTON ACTIONS)
            # =================================================
            elif msg_type == 'COMMAND_LONG':
                
                # --- 1. Xử lý Lệnh ARM / DISARM ---
                if msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                    if msg.param1 == 1:
                        with vehicle.lock:
                            vehicle.armed = True
                        print("🔓 ARM COMMAND")
                    else:
                        with vehicle.lock:
                            vehicle.armed = False
                            vehicle.vx_cmd = 0.0
                            vehicle.wz_cmd = 0.0
                        print("🔒 DISARM COMMAND")

                    if send_lock:
                        with send_lock:
                            send_command_ack(mav_conn, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)
                    else:
                        send_command_ack(mav_conn, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)

                # --- 2. Xử lý nút bấm BẬT CAMERA (Command ID: 2500) ---
                elif msg.command == 2500:
                    print("🎬 [Lệnh từ QGC] -> Yêu cầu BẬT CAMERA!")
                    if send_lock:
                        with send_lock: send_command_ack(mav_conn, 2500)
                    else:
                        send_command_ack(mav_conn, 2500)
                    
                    # [Tùy chọn]: Thêm logic điều khiển thực tế tại đây nếu muốn
                    # Ví dụ: vehicle.camera_active = True

                # --- 3. Xử lý nút bấm TẮT CAMERA (Command ID: 2501) ---
                elif msg.command == 2501:
                    print("🛑 [Lệnh từ QGC] -> Yêu cầu TẮT CAMERA!")
                    if send_lock:
                        with send_lock: send_command_ack(mav_conn, 2501)
                    else:
                        send_command_ack(mav_conn, 2501)
                    
                    # [Tùy chọn]: Thêm logic điều khiển thực tế tại đây nếu muốn
                    # Ví dụ: vehicle.camera_active = False

            # =================================================
            # SET MODE
            # =================================================
            elif msg_type == "SET_MODE":
                with vehicle.lock:
                    vehicle.mode = msg.custom_mode
                print(f"📌 SET_MODE = {msg.custom_mode}")

            # =================================================
            # MANUAL CONTROL
            # =================================================
            elif msg_type == 'MANUAL_CONTROL':
                vx, wz = manual_control_to_velocity(msg.x, msg.r)
                with vehicle.lock:
                    vehicle.vx_cmd = vx
                    vehicle.wz_cmd = wz
                    vehicle.last_manual_control = time.time()
                print(f"🕹️ vx={vx:.2f} m/s wz={wz:.2f} rad/s")

            # =================================================
            # RC OVERRIDE
            # =================================================
            elif msg_type == 'RC_CHANNELS_OVERRIDE':
                print(f"🎮 CH1={msg.chan1_raw} CH3={msg.chan3_raw}")

            # =================================================
            # MISSION UPLOAD & ITEMS (Giữ nguyên logic của bạn)
            # =================================================
            elif msg_type == "MISSION_COUNT":
                print(f"🗺️ Mission Count = {msg.count}")
                with vehicle.lock:
                    vehicle.mission_count = msg.count
                    vehicle.mission_items = []

                if send_lock:
                    with send_lock:
                        mav_conn.mav.mission_request_int_send(msg.get_srcSystem(), msg.get_srcComponent(), 0)
                else:
                    mav_conn.mav.mission_request_int_send(msg.get_srcSystem(), msg.get_srcComponent(), 0)

            elif msg_type == "MISSION_ITEM_INT":
                print(f"📍 Mission Item seq={msg.seq}")
                with vehicle.lock:
                    vehicle.mission_items.append(msg)

                next_seq = msg.seq + 1
                with vehicle.lock:
                    total = vehicle.mission_count

                if next_seq < total:
                    if send_lock:
                        with send_lock:
                            mav_conn.mav.mission_request_int_send(msg.get_srcSystem(), msg.get_srcComponent(), next_seq)
                    else:
                        mav_conn.mav.mission_request_int_send(msg.get_srcSystem(), msg.get_srcComponent(), next_seq)
                else:
                    print("✅ Mission Upload Complete")
                    if send_lock:
                        with send_lock:
                            mav_conn.mav.mission_ack_send(msg.get_srcSystem(), msg.get_srcComponent(), mavutil.mavlink.MAV_MISSION_ACCEPTED)
                    else:
                        mav_conn.mav.mission_ack_send(msg.get_srcSystem(), msg.get_srcComponent(), mavutil.mavlink.MAV_MISSION_ACCEPTED)

            # =================================================
            # CLEAR MISSION
            # =================================================
            elif msg_type == "MISSION_CLEAR_ALL":
                print("🗑️ Mission Clear")
                with vehicle.lock:
                    vehicle.mission_items.clear()
                    vehicle.mission_count = 0

            # =================================================
            # START MISSION
            # =================================================
            elif (msg_type == "COMMAND_LONG" and msg.command == mavutil.mavlink.MAV_CMD_MISSION_START):
                print("🚀 Mission Start")
                with vehicle.lock:
                    vehicle.mission_active = True
                    vehicle.mission_index = 0

                if send_lock:
                    with send_lock:
                        send_command_ack(mav_conn, mavutil.mavlink.MAV_CMD_MISSION_START)
                else:
                    send_command_ack(mav_conn, mavutil.mavlink.MAV_CMD_MISSION_START)

        except Exception as e:
            print(f"❌ Receiver Error: {e}")

        time.sleep(0.01)

    print("🛑 Receiver stopped")