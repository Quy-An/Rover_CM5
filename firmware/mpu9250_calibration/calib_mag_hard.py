import time
import sys
import numpy as np

# Thử kết nối IMU qua I2C
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
    print("IMU không khởi động được - Kiểm tra lại dây nhợ và I2C!")
    sys.exit()

time.sleep(2) # Chờ cảm biến ổn định

def outlier_removal(x_ii, y_ii):
    x_diff = np.append(0.0, np.diff(x_ii))
    stdev_amt = 5.0
    x_outliers = np.where(np.abs(x_diff) > np.abs(np.mean(x_diff)) + (stdev_amt * np.std(x_diff)))
    
    y_diff = np.append(0.0, np.diff(y_ii))
    y_outliers = np.where(np.abs(y_diff) > np.abs(np.mean(y_diff)) + (stdev_amt * np.std(y_diff)))
    
    if len(x_outliers[0]) != 0:
        x_ii[x_outliers] = np.nan
        y_ii[x_outliers] = np.nan
    if len(y_outliers[0]) != 0:
        y_ii[y_outliers] = np.nan
        x_ii[y_outliers] = np.nan
    return x_ii, y_ii

def mag_cal():
    print("=" * 60)
    print("      QUY TRÌNH HIỆU CHUẨN KHỬ NHIỄU TỪ KẾ (HARD IRON)      ")
    print("=" * 60)
    print("Bạn sẽ xoay mạch 360 độ quanh lần lượt 3 trục Z, Y, X.")
    print("Mỗi trục xoay xong, bạn nhấn tổ hợp phím [Ctrl + C] để chuyển trục.")
    
    mag_cal_axes = ['Z', 'Y', 'X']
    cal_rot_indices = [[0, 1], [1, 2], [0, 2]]
    mag_cal_rotation_vec = []
    
    for qq, ax_qq in enumerate(mag_cal_axes):
        print("\n" + "-"*50)
        input(f"👉 [TRỤC {ax_qq}]: Nhấn ENTER rồi BẮT ĐẦU xoay tròn mạch liên tục quanh trục {ax_qq}...")
        print("--> Đang ghi dữ liệu... Khi xoay xong ít nhất 2-3 vòng, hãy nhấn [Ctrl + C] để dừng trục này.")
        
        mag_array = []
        t_start = time.time()
        
        while True:
            try:
                mx, my, mz = AK8963_conv()
                mag_array.append([mx, my, mz])
                time.sleep(0.01) # Đọc ở nhịp 100Hz
            except KeyboardInterrupt:
                print(f"\n-> Đã dừng thu thập dữ liệu trục {ax_qq}.")
                break
            except:
                continue
                
        # Bỏ 20 điểm đầu để tránh buffer bị kẹt dữ liệu cũ
        if len(mag_array) > 20:
            mag_array = mag_array[20:]
            duration = time.time() - t_start
            print(f"Tốc độ đọc thực tế trục này: {len(mag_array)/duration:.2f} Hz")
            mag_cal_rotation_vec.append(mag_array)
        else:
            print("Lỗi: Thu thập quá ít mẫu, vui lòng chạy lại file!")
            sys.exit()
            
    # Tính toán ma trận Offsets
    ak_fit_coeffs = []
    indices_to_save = [0, 0, 1] 
    
    for mag_ii, mags in enumerate(mag_cal_rotation_vec):
        mags = np.array(mags)
        x = mags[:, cal_rot_indices[mag_ii][0]]
        y = mags[:, cal_rot_indices[mag_ii][1]]
        
        x, y = outlier_removal(x, y)
        
        x_0 = (np.nanmax(x) + np.nanmin(x)) / 2.0
        y_0 = (np.nanmax(y) + np.nanmin(y)) / 2.0
        
        ak_fit_coeffs.append([x_0, y_0][indices_to_save[mag_ii]])
        
    return ak_fit_coeffs

if __name__ == '__main__':
    mag_coeffs = mag_cal()
    
    print("\n" + 50 * "=")
    print(" KẾT QUẢ MAGNETOMETER OFFSETS (HARD-IRON):")
    print(50 * "=")
    print(f"  mx_offset = {mag_coeffs[0]:.6f}")
    print(f"  my_offset = {mag_coeffs[1]:.6f}")
    print(f"  mz_offset = {mag_coeffs[2]:.6f}")
    print(50 * "=")
    print("\nCông thức áp dụng: Từ kế chuẩn = Giá trị thô - Mag Offset")