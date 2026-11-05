import time
import sys

# 1. BỘ HẰNG SỐ HIỆU CHUẨN CỦA BẠN
WX_OFF, WY_OFF, WZ_OFF = 2.901212, -11.190539, -0.449948
MX, BX = 1.002370, -0.001721
MY, BY = 0.999796,  0.002133
MZ, BZ = 0.994585,  0.054289

start_bool = False
t0 = time.time()
while (time.time()-t0)<5:
    try:
        from mpu9250_i2c import *
        start_bool = True
        break 
    except:
        continue

if not start_bool:
    print("IMU không khởi động được!")
    sys.exit()

print("="*60)
print("  BẮT ĐẦU THEO DÕI GÓC QUAY YAW (HƯỚNG XE AGV) THỜI GIAN THỰC ")
print("="*60)
print("Đặt im mạch, sau đó thử xoay ngang mạch 90 độ hoặc 180 độ xem góc thay đổi.")
print("Nhấn Ctrl + C để thoát.\n")
time.sleep(2)

# Khởi tạo các biến tính tích phân
yaw_angle = 0.0
last_time = time.time()

while True:
    try:
        current_time = time.time()
        dt = current_time - last_time  # Tính delta_t thực tế giữa 2 lần đọc
        last_time = current_time
        
        # Đọc dữ liệu thô
        _, _, _, _, _, wz_raw = mpu6050_conv() 
        
        # Hiệu chuẩn riêng trục Z để tính Yaw
        wz_calib = wz_raw - WZ_OFF
        
        # Tích phân số hình thang đơn giản: Góc = Góc_cũ + (Vận_tốc_góc * dt)
        # Chỉ cộng dồn nếu vận tốc góc đủ lớn để lọc bớt nhiễu sương mù (Deadzone)
        if abs(wz_calib) > 0.2: 
            yaw_angle += wz_calib * dt
            
        # In góc quay hiện tại ra màn hình (đơn vị: Độ)
        print(f"Tốc độ quay Z: {wz_calib:6.2f} °/s | ---> GÓC HƯỚNG YAW HIỆN TẠI: {yaw_angle:7.2f} °", end="\r")
        
    except KeyboardInterrupt:
        print("\n\nĐã dừng chương trình theo dõi góc.")
        break
    except:
        continue
        
    time.sleep(0.01) # Khóa nhịp vòng lặp ở 100Hz