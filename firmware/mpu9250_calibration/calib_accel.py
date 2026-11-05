import time
import sys
import numpy as np
from scipy.optimize import curve_fit

# Thử kết nối IMU
start_bool = False
t0 = time.time()
while time.time() - t0 < 5:
    try: 
        from mpu9250_i2c import *
        start_bool = True
        break
    except:
        continue

if not start_bool:
    print("IMU not Started - Check Wiring and I2C")
    sys.exit()

time.sleep(2)

def accel_fit(x_input, m_x, b):
    return (m_x * x_input) + b

def get_accel():
    ax, ay, az, _, _, _ = mpu6050_conv()
    return ax, ay, az

def accel_cal(cal_size):
    print("=" * 50)
    print("      QUY TRÌNH HIỆU CHUẨN GIA TỐC KẾ (ACCEL)      ")
    print("=" * 50)
    print("Bạn sẽ cần lật mạch IMU theo 3 hướng cho mỗi trục (X, Y, Z).")
    print("Mỗi lần đổi hướng, hãy ĐẶT IMU THẬT YÊN LẶNG rồi nhấn Enter.")
    
    mpu_offsets = [[], [], []]
    axis_vec = ['z', 'y', 'x'] 
    cal_directions = ["HƯỚNG LÊN TRỜI (Upward)", "HƯỚNG XUỐNG ĐẤT (Downward)", "VUÔNG GÓC VỚI TRỌNG LỰC (0g)"]
    cal_indices = [2, 1, 0] # Chỉ số trục trong mảng [ax, ay, az]
    
    for qq, ax_qq in enumerate(axis_vec):
        ax_offsets = [[], [], []]
        print("\n" + "#" * 50)
        print(f" HIỆU CHUẨN CHO TRỤC: --- {ax_qq.upper()} ---")
        print("#" * 50)
        
        for direc_ii, direc in enumerate(cal_directions):
            # Chờ người dùng đặt mạch và nhấn Enter
            input(f"\n[BƯỚC {direc_ii+1}]: Hãy để trục -{ax_qq}- {direc}.\n--> Sau đó nhấn ENTER để lấy mẫu...")
            print("Đang thu thập dữ liệu, vui lòng giữ im mạch...")
            
            # Xóa buffer cũ
            for _ in range(50):
                try: mpu6050_conv()
                except: pass
                
            mpu_array = []
            while len(mpu_array) < cal_size:
                try:
                    ax, ay, az = get_accel()
                    mpu_array.append([ax, ay, az])
                except:
                    continue
            
            # Lấy đúng trục đang cấu hình
            ax_offsets[direc_ii] = np.array(mpu_array)[:, cal_indices[qq]]
            print(f"-> Đã thu thập xong {cal_size} mẫu cho hướng này.")

        # Gom dữ liệu thô của 3 hướng lại để làm tập X
        raw_data = np.append(np.append(ax_offsets[0], ax_offsets[1]), ax_offsets[2])
        
        # Tạo tập Y lý tưởng tương ứng (+1g, -1g, 0g)
        ideal_data = np.append(np.append(1.0 * np.ones(len(ax_offsets[0])), 
                                         -1.0 * np.ones(len(ax_offsets[1]))), 
                               0.0 * np.ones(len(ax_offsets[2])))
        
        # Khớp đường thẳng tìm m và b: Ý tưởng là Calibrated = m * Raw + b
        popts, _ = curve_fit(accel_fit, raw_data, ideal_data, maxfev=10000)
        mpu_offsets[cal_indices[qq]] = popts
        
    print("\n" + "=" * 50)
    print("      QUY TRÌNH HIỆU CHUẨN ACCEL HOÀN TẤT!      ")
    print("=" * 50)
    return mpu_offsets

if __name__ == '__main__':
    CAL_SIZE = 1000 # Lấy 1000 mẫu cho mỗi hướng giống như Gyro cho mịn
    accel_coeffs = accel_cal(CAL_SIZE)
    
    # IN KẾT QUẢ CUỐI CÙNG RA MÀN HÌNH ĐỂ LƯU LẠI
    print("\n" + 50 * "-")
    print(" HỆ SỐ HIỆU CHUẨN ACCEL CỦA BẠN (HÃY COPY LẠI):")
    print(50 * "-")
    print(f"Trục X: m_x = {accel_coeffs[0][0]:.6f}, b_x = {accel_coeffs[0][1]:.6f}")
    print(f"Trục Y: m_y = {accel_coeffs[1][0]:.6f}, b_y = {accel_coeffs[1][1]:.6f}")
    print(f"Trục Z: m_z = {accel_coeffs[2][0]:.6f}, b_z = {accel_coeffs[2][1]:.6f}")
    print(50 * "-")
    print("\nCông thức áp dụng sau này: Giác tốc chuẩn = (m * Giá trị thô) + b")