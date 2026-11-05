import time
import sys

# Thử kết nối với mạch IMU qua I2C trong 5 giây
start_bool = False
t0 = time.time()
while time.time() - t0 < 5:
    try: 
        from mpu9250_i2c import *
        start_bool = True
        break
    except Exception as e:
        continue

if not start_bool:
    print("IMU not Started - Check Wiring and I2C")
    sys.exit()

time.sleep(2) # Chờ MPU ổn định điện áp

def get_gyro():
    _, _, _, wx, wy, wz = mpu6050_conv() # Đọc dữ liệu thô từ gyro
    return wx, wy, wz

def gyro_cal(cal_size):
    print("-" * 50)
    print(f"Đang thu thập {cal_size} mẫu dữ liệu tĩnh ở nhịp 100Hz...")
    print("HÃY GIỮ CẢM BIẾN THẬT YÊN LẶNG TRÊN BÀN...")
    
    # Đọc nháp vài chục lần để xóa dữ liệu cũ còn kẹt trong buffer
    for _ in range(50):
        try: get_gyro()
        except: pass
    
    wx_sum = 0.0
    wy_sum = 0.0
    wz_sum = 0.0
    success_count = 0
    
    while success_count < cal_size:
        try:
            wx, wy, wz = get_gyro()
            wx_sum += wx
            wy_sum += wy
            wz_sum += wz
            success_count += 1
        except:
            # Nếu một mẫu bị lỗi đường truyền I2C thì bỏ qua, đọc lại mẫu khác
            continue
        
        time.sleep(0.01) # Khóa nhịp 10ms (tương đương 100Hz)
            
    print("\nHiệu chuẩn hoàn tất!")
    
    # Tính giá trị trung bình (Offset) bằng toán thuần
    wx_offset = wx_sum / success_count
    wy_offset = wy_sum / success_count
    wz_offset = wz_sum / success_count
    
    return wx_offset, wy_offset, wz_offset

if __name__ == '__main__':
    TOTAL_SAMPLES = 1000 # Chốt lấy 1000 mẫu cho mịn dữ liệu
    
    wx_off, wy_off, wz_off = gyro_cal(TOTAL_SAMPLES)
    
    print("\n" + 45*"=")
    print("   KẾT QUẢ GYRO OFFSETS (CHỈ SỐ THỰC TẾ):")
    print(45*"=")
    print(f"  wx_offset = {wx_off:.6f}")
    print(f"  wy_offset = {wy_off:.6f}")
    print(f"  wz_offset = {wz_off:.6f}")
    print(45*"=")
    print("\nBạn hãy lưu lại 3 số này để trừ vào dữ liệu thô của xe AGV nhé!")