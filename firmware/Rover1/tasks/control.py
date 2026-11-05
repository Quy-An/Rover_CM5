import math
import queue
import time
import gc
from gpiozero import LED, PWMLED

R = 0.0205  # Bán kính bánh xe (mét)
B = 0.2  # Khoảng cách giữa tâm 2 dải xích (mét)
MAX_WHEEL_W = 34.56  # Vận tốc góc tối đa (rad/s) ứng với 100% PWM

def control_motor(PWM_L, PWM_R):
    # Motor trái
    if PWM_L >= 0:
        DIR_LEFT.on()
        IN1_LEFT.value = PWM_L
    else:
        DIR_LEFT.off()
        IN1_LEFT.value = abs(PWM_L)

    # Motor phải
    if PWM_R >= 0:
        DIR_RIGHT.on()
        IN1_RIGHT.value = PWM_R
    else:
        DIR_RIGHT.off()
        IN1_RIGHT.value = abs(PWM_R)


def omega_to_pwm(w_l, w_r):
    SCALE_LEFT = 0.96
    SCALE_RIGHT = 1.00
    
    pwm_l = (w_l / MAX_WHEEL_W) * SCALE_LEFT
    pwm_r = (w_r / MAX_WHEEL_W) * SCALE_RIGHT
    pwm_l = max(-1.0, min(1.0, pwm_l))
    pwm_r = max(-1.0, min(1.0, pwm_r))
    return pwm_l, pwm_r


def inverse_kinematics(v_x, w_z):
    V_l = v_x - (B * w_z) / 2.0
    V_r = v_x + (B * w_z) / 2.0
    w_l = V_l / R
    w_r = -V_r / R  
    return w_l, w_r

def lay_du_lieu_moi_nhat(q, du_lieu_hien_tai):
    du_lieu_moi = du_lieu_hien_tai
    try:
        while True:
            du_lieu_moi = q.get_nowait()
    except queue.Empty:
        pass
    return du_lieu_moi

def tien_trinh_tinh_toan(shm_name, lock, q_imu_tinh_toan, q_gps_tinh_toan, q_quy_dao, cmd_queue):
    global IN1_LEFT, DIR_LEFT, IN1_RIGHT, DIR_RIGHT
    
    IN1_LEFT = PWMLED(17)
    DIR_LEFT = LED(27)

    IN1_RIGHT = PWMLED(23)
    DIR_RIGHT = LED(24)

    is_armed = False
    vx_target, wz_target = 0.0, 0.0
    LOOP_DELAY = 0.02  # Chu kỳ quét lệnh 50Hz
    last_cmd_time = time.perf_counter()
    TIMEOUT_SEC = 0.04
    was_armed = False
    try:
        next_time = time.perf_counter() + LOOP_DELAY
        while True:
            try:
                while True:
                    msg = cmd_queue.get_nowait()
                    if msg["type"] == "status":
                        is_armed = msg["armed"]
                    elif msg["type"] == "drive":
                        vx_target = msg["vx"]
                        wz_target = msg["wz"]
                        last_cmd_time = time.perf_counter()
            except queue.Empty:
                pass

            # 6. Điều khiển động cơ dựa trên trạng thái ARM
            if is_armed:
                gc.disable()

                if time.perf_counter() - last_cmd_time > TIMEOUT_SEC:
                    vx_physical = 0.0
                    wz_physical = 0.0
                else:
                    vx_physical = (vx_target / 100.0) * 0.71
                    wz_physical = (wz_target / 100.0) * 7.1

                # Tính toán động học nghịch và xuất xung PWM cho motor
                w_l, w_r = inverse_kinematics(vx_physical, wz_physical)
                pwm_l, pwm_r = omega_to_pwm(w_l, w_r)
                control_motor(pwm_l, pwm_r)
                was_armed = True
            else:
                # Nếu đang DISARM thì lập tức dừng xe an toàn
                control_motor(0, 0)

                if was_armed:
                    gc.enable()
                    gc.collect()
                    gc.disable()
                    was_armed = False
            
            while time.perf_counter() < next_time:
                pass
            
            next_time += LOOP_DELAY

    except Exception as e:
        print(f"\n[Control Task] Lỗi phát sinh: {e}")
    finally:
        control_motor(0, 0)
        gc.enable()