import time
import sys

# ========================================================
# KHO DỮ LIỆU HIỆU CHUẨN ĐÃ HOÀN THÀNH CỦA BẠN
# ========================================================
# 1. Gyro Offsets (Sai số tĩnh dps)
WX_OFF, WY_OFF, WZ_OFF = 2.901212, -11.190539, -0.449948

# 2. Accel Coefficients (Hệ số góc m và intercept b)
MX_ACC, BX_ACC = 1.002370, -0.001721
MY_ACC, BY_ACC = 0.999796,  0.002133
MZ_ACC, BZ_ACC = 0.994585,  0.054289

# 3. Magnetometer Offsets (Khử nhiễu sắt từ Hard-iron)
MX_MAG_OFF, MY_MAG_OFF, MZ_MAG_OFF = -26.513672, 31.054688, -27.465820
# ========================================================

# Kết nối phần cứng I2C
start_bool = False
t0 = time.time()
while (time.time() - t0) < 5:
    try:
        from mpu9250_i2c import *
        start_bool = True
        break 
    except:
        continue

if not start_bool:
    print("IMU không khởi động được - Hãy kiểm tra dây nhợ!")
    sys.exit()

def get_calibrated_9dof():
    """Hàm đọc dữ liệu thô và trả về 9 trục ĐÃ HIỆU CHUẨN CHUẨN XÁC"""
    # Đọc dữ liệu gốc từ thư viện phần cứng
    ax_raw, ay_raw, az_raw, wx_raw, wy_raw, wz_raw = mpu6050_conv()
    mx_raw, my_raw, mz_raw = AK8963_conv()
    
    # Áp dụng các bộ lọc hiệu chuẩn tuyến tính đã tính toán
    ax_calib = (MX_ACC * ax_raw) + BX_ACC
    ay_calib = (MY_ACC * ay_raw) + BY_ACC
    az_calib = (MZ_ACC * az_raw) + BZ_ACC
    
    wx_calib = wx_raw - WX_OFF
    wy_calib = wy_raw - WY_OFF
    wz_calib = wz_raw - WZ_OFF
    
    mx_calib = mx_raw - MX_MAG_OFF
    my_calib = my_raw - MY_MAG_OFF
    mz_calib = mz_raw - MZ_MAG_OFF
    
    return [ax_calib, ay_calib, az_calib, wx_calib, wy_calib, wz_calib, mx_calib, my_calib, mz_calib]

if __name__ == '__main__':
    print("=" * 60)
    print("   HỆ THỐNG DỮ LIỆU 9-DOF MPU9250 ĐÃ HIỆU CHUẨN HOÀN TOÀN")
    print("=" * 60)
    print("Dữ liệu xuất ra đã sẵn sàng nạp vào EKF hoặc ROS2. Nhấn Ctrl+C để dừng.\n")
    time.sleep(1)
    
    while True:
        try:
            # Gọi hàm lấy dữ liệu sạch
            data = get_calibrated_9dof()
            
            # In nhanh ra màn hình để đối chứng
            print("-" * 50)
            print(f"ACCEL (g)  | X: {data[0]:6.2f} | Y: {data[1]:6.2f} | Z: {data[2]:6.2f}")
            print(f"GYRO (dps) | X: {data[3]:6.2f} | Y: {data[4]:6.2f} | Z: {data[5]:6.2f}")
            print(f"MAG (uT)   | X: {data[6]:6.2f} | Y: {data[7]:6.2f} | Z: {data[8]:6.2f}")
            
            time.sleep(0.01) # Khóa cứng tần số quét 100Hz thực tế cho xe
            
        except KeyboardInterrupt:
            print("\nĐã dừng chương trình.")
            break
        except:
            continue