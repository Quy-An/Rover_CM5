import multiprocessing
from multiprocessing import shared_memory
import threading
import time
import yaml
import queue
import signal
import sys
import os
# Import trực tiếp từ các file cùng thư mục
from tasks.sensor import lidar_task, imu_task, gps_task
from tasks.control import tien_trinh_tinh_toan
from tasks.mavlink import luong_chay_mavlink
from tasks.video import video_task

# Khai báo biến toàn cục để bộ xử lý tín hiệu có thể tiếp cận dọn dẹp
shm = None
processes = []
stop_event = None
stop_event_process = None
MAIN_PID = os.getpid()

def graceful_shutdown(signum, frame):
    """Hàm xử lý tối hậu: Đảm bảo dọn sạch phần cứng khi Docker Compose Down"""
    if os.getpid() != MAIN_PID:
        sys.exit(0)

    signame = signal.Signals(signum).name
    print(f"\n[SYSTEM] Nhận tín hiệu dừng {signame} từ hệ thống. Đang hạ cánh an toàn...")
    
    if stop_event:
        stop_event.set()
    if stop_event_process:
        stop_event_process.set()

    print("[SYSTEM] Đang chờ các tiến trình tự đóng phần cứng an toàn...")
    for p in processes:
        try:
            p.join(timeout=1.5) 
            
            if p.is_alive():
                print(f"[SYSTEM] Tiến trình {p.name} không tự đóng kịp thời. Buộc phải ép chết!")
                p.terminate()
                p.join(timeout=0.5)
                if p.is_alive(): 
                    p.kill()
        except Exception as e:
            print(f"[SYSTEM] Lỗi khi đóng tiến trình {p.name}: {e}")

    global shm
    if shm:
        print("[SYSTEM] Đang dọn dẹp vùng nhớ Shared Memory LiDAR...")
        try:
            shm.close()
            shm.unlink()
            print("[SYSTEM] -> Đã xóa liên kết Lidar_SHM thành công!")
        except Exception as e:
            print(f"[SYSTEM] Lỗi xóa SHM: {e}")

    print("[SYSTEM] Hệ thống Rover đã dừng hoạt động hoàn toàn an toàn!")
    sys.exit(0)

def main():
    global shm, stop_event, stop_event_process, processes
    
    # ĐĂNG KÝ BỘ ĐÁNH CHẶN TÍN HIỆU (Bắt cả Ctrl+C và Docker Compose Down)
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        print("Đã nạp cấu hình từ file config.yaml thành công!")
    except Exception as e:
        print(f"Lỗi đọc file cấu hình: {e}")
        return
    
    # Khóa và các Hàng đợi      
    lock = multiprocessing.Lock()
    q_imu_control = multiprocessing.Queue(maxsize=15)
    q_gps_control = multiprocessing.Queue(maxsize=15)
    q_imu_mavlink = multiprocessing.Queue(maxsize=15)
    q_gps_mavlink = multiprocessing.Queue(maxsize=15)
    q_imu_video = multiprocessing.Queue(maxsize=100)
    q_path = multiprocessing.Queue(maxsize=15)   
    cmd_queue = multiprocessing.Queue(maxsize=5)  

    stop_event = threading.Event()
    stop_event_process = multiprocessing.Event()
    camera_active_event = multiprocessing.Event()
    lidar_active_event = multiprocessing.Event()
    gps_ready_event = multiprocessing.Event()
    
    # Khởi tạo vùng nhớ chung Lidar_SHM an toàn
    try:
        shm = shared_memory.SharedMemory(create=True, size=152, name="Lidar_SHM")
    except FileExistsError:
        try:
            shm_temp = shared_memory.SharedMemory(name="Lidar_SHM")
            shm_temp.unlink()
        except Exception:
            pass
        shm = shared_memory.SharedMemory(create=True, size=152, name="Lidar_SHM")

    # Khởi tạo các Tiến trình (Processes)
    p_tinh_toan = multiprocessing.Process(
        target=tien_trinh_tinh_toan, 
        args=(shm.name, lock, q_imu_control, q_gps_control, q_path, cmd_queue),
        daemon=True
    )

    p_mavlink = multiprocessing.Process(
        target=luong_chay_mavlink, 
        args=(q_imu_mavlink, q_gps_mavlink, q_path, {"config": config}, shm, lock, cmd_queue, camera_active_event, lidar_active_event), 
        daemon=True
    )

    p_lidar = multiprocessing.Process(
        target=lidar_task, 
        args=({"config": config}, shm, lock, stop_event_process, lidar_active_event), 
        daemon=True
    )

    p_video = multiprocessing.Process(
        target=video_task, 
        args=({"config": config}, stop_event, camera_active_event, q_imu_video), 
        daemon=True
    )

    # Đưa vào danh sách quản lý tập trung
    processes = [p_lidar, p_mavlink, p_tinh_toan, p_video]

    # Khởi tạo các Luồng (Threads)
    t_imu = threading.Thread(target=imu_task, args=(q_imu_control, q_imu_mavlink, q_imu_video, stop_event), daemon=True)
    t_gps = threading.Thread(target=gps_task, args=({"config": config}, q_gps_control, q_gps_mavlink, stop_event, gps_ready_event), daemon=True)

    # Kích hoạt toàn bộ hệ thống hành trình
    t_imu.start()
    t_gps.start()
    
    p_video.start()
    p_lidar.start()
    p_mavlink.start()
    p_tinh_toan.start()

    # Chờ tín hiệu Fix từ GPS để xác nhận Rover sẵn sàng vào vị trí
    while not gps_ready_event.wait(timeout=1.0):
        if stop_event.is_set():
            break

    print("Toàn bộ luồng và tiến trình đã hoạt động ổn định. Hệ thống đang chạy...")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()