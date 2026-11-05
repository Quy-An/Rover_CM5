import time
import sys

# Thử kết nối thư viện
try:
    from mpu9250_i2c import *
except:
    print("Không tìm thấy file mpu9250_i2c.py")
    sys.exit()

print("====================================================")
print(" Đang đo tốc độ đọc I2C thực tế trong vòng 5 giây... ")
print("====================================================")

counter = 0
t_start = time.time()

while (time.time() - t_start) < 5.0:
    try:
        # Thử đọc 6 trục Accel/Gyro liên tục không nghỉ
        _, _, _, _, _, _ = mpu6050_conv()
        counter += 1
    except:
        continue

t_end = time.time()
total_time = t_end - t_start
actual_hz = counter / total_time

print(f"Tổng số lần đọc thành công: {counter} lần")
print(f"Thời gian chạy thực tế: {total_time:.4f} giây")
print(f"-> TỐC ĐỘ ĐỌC THỰC TẾ: {actual_hz:.2f} Hz")
print("====================================================")c