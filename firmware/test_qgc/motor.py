import math
from gpiozero import PWMLED, LED
from time import sleep

# ==============================================================================
# Cấu hình GPIO (Raspberry Pi 5 - gpiozero)
# ==============================================================================
IN1_LEFT = PWMLED(17)
DIR_LEFT = LED(27)

IN1_RIGHT = PWMLED(23)
DIR_RIGHT = LED(24)

# ==============================================================================
# Thông số Robot bánh xích / vi sai
# ==============================================================================
R = 0.0205          # Bán kính bánh răng chủ động/bánh xe (mét)
B = 0.2                 # Khoảng cách giữa tâm 2 dải xích (mét)
MAX_WHEEL_W = 34.56     # Vận tốc góc tối đa của bánh xe (rad/s) ứng với 100% PWM

# ==============================================================================
# Điều khiển Motor xuất xung
# ==============================================================================
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

# ==============================================================================
# Hàm chuyển đổi Vận tốc góc -> PWM [-1; 1]
# ==============================================================================
def omega_to_pwm(w_l, w_r):
    pwm_l = w_l / MAX_WHEEL_W
    pwm_r = w_r / MAX_WHEEL_W
    
    # Giới hạn giá trị PWM trong khoảng [-1, 1] để tránh lỗi
    pwm_l = max(-1.0, min(1.0, pwm_l))
    pwm_r = max(-1.0, min(1.0, pwm_r))
    
    return pwm_l, pwm_r

# ==============================================================================
# Hàm Động học Thuận / Nghịch (Đã sửa lỗi ngược Trái/Phải)
# ==============================================================================
def forward_kinematics(w_l, w_r):
    """
    Tính vận tốc robot từ vận tốc góc thực tế của 2 bánh xe.
    """
    V_l = w_l * R
    V_r = -w_r * R  # Thêm dấu trừ để đồng bộ với việc đảo chiều phần cứng của bánh phải
    
    v_x = (V_r + V_l) / 2.0
    v_y = 0.0
    w_z = (V_r - V_l) / B  # w_z > 0 là quay trái, w_z < 0 là quay phải
    
    return v_x, v_y, w_z

def inverse_kinematics(v_x, w_z):
    """
    Tính vận tốc góc cần thiết của 2 bánh từ vận tốc mong muốn của robot.
    Quy ước toán học: w_z > 0 -> Quay TRÁI (Bánh phải tiến, bánh trái lùi)
    """
    # Đảo lại dấu ở đây để khi w_z > 0 thì V_r lớn hơn V_l (Robot rẽ trái)
    V_l = v_x - (B * w_z) / 2.0
    V_r = v_x + (B * w_z) / 2.0
    
    # Chuyển đổi sang vận tốc góc (rad/s)
    w_l = V_l / R
    w_r = -V_r / R  # Giữ nguyên dấu trừ do thiết kế đối xứng của động cơ phải
    
    return w_l, w_r


if __name__ == "__main__":
    print("🚀 Bắt đầu thử nghiệm điều khiển Robot bánh xích...")
    
    try:
        # THỬ NGHIỆM: Quay TRÁI tại chỗ với vận tốc góc 5 rad/s
        v_x = 0.5  # m/s
        w_z = 0  # rad/s (Dấu dương = Quay TRÁI)
        
        w_l, w_r = inverse_kinematics(v_x, w_z)
        pwm_l, pwm_r = omega_to_pwm(w_l, w_r)
        
        print(f"Kiểm tra tính toán cho lệnh QUAY TRÁI:")
        print(f"  -> Vận tốc góc tính ra: Bánh trái: {w_l:.2f} rad/s, Bánh phải: {w_r:.2f} rad/s")
        print(f"  -> PWM xuất ra: Bánh trái: {pwm_l:.2f}, Bánh phải: {pwm_r:.2f}")
        
        control_motor(pwm_l, pwm_r)
        sleep(5)  # Chạy thử trong 5 giây
        control_motor(0, 0)

        vx, vy, wz = forward_kinematics(w_l, w_r)
        print(f"Kiểm tra động học thuận:")
        print(f"  -> Vận tốc thực tế từ động học thuận: v_x: {vx:.2f} m/s, v_y: {vy:.2f} m/s, w_z: {wz:.2f} rad/s")
        
    except KeyboardInterrupt:
        print("\n🛑 Dừng điều khiển Robot...")
    finally:
        control_motor(0, 0)  # Dừng an toàn tất cả động cơ