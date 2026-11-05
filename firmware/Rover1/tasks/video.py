import cv2 as cv
import numpy as np
import time
import shlex
import subprocess
import math
import threading
import queue
import os
import csv
from datetime import datetime
from picamera2 import Picamera2

# def put_latest_to_queue(q, data):
#     """Mẹo dọn dẹp hàng đợi để luôn giữ ảnh mới nhất, đảm bảo truyền dẫn realtime"""
#     try:
#         q.put_nowait(data)
#     except queue.Full:
#         try: q.get_nowait()
#         except queue.Empty: pass
#         try: q.put_nowait(data)
#         except queue.Full: pass

# def video_writer_task(q, stop_event, process):
#     """Luồng phụ 1: Chuyên đọc ảnh từ queue và bơm vào GStreamer truyền qua mạng"""
#     while not stop_event.is_set():
#         try:
#             frame = q.get() 
#             if frame is None: break
#             process.stdin.write(frame.tobytes())
#             process.stdin.flush()
#         except (BrokenPipeError, OSError): break
#         except Exception: break

# def disk_writer_task(q, stop_event, writer_raw, writer_stab, video_ts_writer):
#     """Luồng phụ 2: Ôm trọn toàn bộ tác vụ I/O nặng (Xoay ảnh, Ghi video, Ghi CSV) chạy ngầm"""
#     while not stop_event.is_set() or not q.empty():
#         try:
#             # Lấy gói dữ liệu tổng hợp từ luồng chính (chờ tối đa 0.1s)
#             item = q.get(timeout=0.1)
#             if item is None: break
            
#             frame, stabilized_frame, count, frame_timestamp = item
            
#             # Thực hiện xoay ảnh 180 độ ngầm ở luồng này, giải phóng luồng chính
#             frame_raw_to_save = cv.rotate(frame, cv.ROTATE_180)
#             frame_stab_to_save = cv.rotate(stabilized_frame, cv.ROTATE_180)
            
#             # Ghi dữ liệu xuống đĩa cứng
#             if writer_raw is not None: writer_raw.write(frame_raw_to_save)
#             if writer_stab is not None: writer_stab.write(frame_stab_to_save)
#             if video_ts_writer is not None:
#                 video_ts_writer.writerow([count, frame_timestamp])
                
#         except queue.Empty:
#             continue
#         except Exception as e:
#             print(f"[DISK WRITER LỖI RUNTIME]: {e}")
#             break

# def video_task(config, stop_event, camera_active_event, q_imu_video):
#     """Luồng truyền và ghi Video thô bất đồng bộ - Phục vụ HIỆU CHUẨN BÀN CỜ tốc độ cao"""
#     vid_config = config["config"]["video"]
#     laptop_ip = vid_config["laptop_ip"]
#     port = vid_config["port"]
#     width = vid_config["width"]
#     height = vid_config["height"]
#     framerate = vid_config["framerate"]
#     rotation = vid_config["rotation"]
    
#     frame_size = width * height * 3
    
#     video_cmd = (
#         f"gst-launch-1.0 fdsrc blocksize={frame_size} do-timestamp=true ! "
#         f"videoparse format=rgb width={width} height={height} framerate={framerate}/1 ! "
#         f"videoconvert ! videoflip method=rotate-{rotation} ! "
#         f"queue leaky=downstream max-size-buffers=1 max-size-bytes=0 max-size-time=0 ! "
#         f"x264enc threads=1 tune=zerolatency speed-preset=ultrafast bitrate=800 ! " # Tăng lên 2 thread và 1500kbps cho nét
#         f"video/x-h264, profile=baseline ! "
#         f"h264parse ! rtph264pay config-interval=1 pt=96 ! "
#         f"udpsink host={laptop_ip} port={port} sync=false buffer-size=2097152"
#     )
#     cmd_list = shlex.split(video_cmd)
    
#     try:
#         print("[VIDEO] Khởi tạo camera OV5647 bằng Picamera2 gốc...")
#         picam2 = Picamera2()
#         video_config = picam2.create_video_configuration(
#             main={"size": (width, height), "format": "RGB888"},
#             controls={"FrameRate": framerate},
#         )
#         picam2.configure(video_config)
#     except Exception as hardware_err:
#         print(f"[VIDEO CRITICAL] Lỗi kết nối Camera: {hardware_err}")
#         return

#     process = None
#     writer_thread = None
#     disk_thread = None
#     writer_raw = None
#     writer_stab = None
#     video_ts_file = None
#     video_ts_writer = None
    
#     frame_queue = queue.Queue(maxsize=1)
#     disk_queue = queue.Queue(maxsize=60) # Hàng đợi đệm chứa tối đa 2 giây video tránh mất khung hình

#     while not stop_event.is_set():
#         if camera_active_event.is_set():
#             if process is None:
#                 try:
#                     picam2.start()
#                     time.sleep(0.5)

#                     process = subprocess.Popen(cmd_list, stdin=subprocess.PIPE)
#                     fourcc = cv.VideoWriter_fourcc(*'MJPG')
#                     writer_raw = cv.VideoWriter('video_raw.avi', fourcc, framerate, (width, height))
#                     writer_stab = cv.VideoWriter('video_stabilized.avi', fourcc, framerate, (width, height))

#                     log_dir = "/app/logs"
#                     os.makedirs(log_dir, exist_ok=True)
#                     timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
#                     ts_filename = f"{log_dir}/video_timestamps_{timestamp_str}.csv"
                    
#                     video_ts_file = open(ts_filename, mode='w', newline='', encoding='utf-8')
#                     video_ts_writer = csv.writer(video_ts_file)
#                     video_ts_writer.writerow(["frame_index", "timestamp"])
#                     print(f"[VIDEO TS] Kích hoạt file ghi mốc thời gian: {ts_filename}")

#                     # Kích hoạt luồng mạng GStreamer
#                     writer_thread = threading.Thread(
#                         target=video_writer_task, 
#                         args=(frame_queue, stop_event, process), 
#                         daemon=True
#                     )
#                     writer_thread.start()

#                     # Kích hoạt luồng ngầm xử lý đĩa cứng độc lập
#                     disk_thread = threading.Thread(
#                         target=disk_writer_task,
#                         args=(disk_queue, stop_event, writer_raw, writer_stab, video_ts_writer),
#                         daemon=True
#                     )
#                     disk_thread.start()
                    
#                     count = 0

#                 except Exception as e:
#                     print(f"[VIDEO LỖI] Khởi động phần cứng thất bại: {e}")
#                     process = None
#                     time.sleep(3)
#                     continue

#             try:
#                 # LUỒNG CHÍNH SIÊU TỐC: Chỉ đọc mảng, chộp thời gian và đẩy vào hàng đợi
#                 # frame_rgb = picam2.capture_array()
#                 # frame_timestamp = time.time() 
                
#                 frame_rgb = picam2.capture_array()
                
#                 # 2. Sử dụng time.monotonic() làm timestamp. 
#                 # Cách này ổn định hơn time.time() rất nhiều và không bị lỗi metadata
#                 frame_timestamp = time.monotonic() 
                
#                 if frame_rgb is None: continue
#                 frame = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)

#                 # if frame_rgb is None: continue
#                 # frame = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)

#                 if q_imu_video is not None:
#                     try:
#                         while not q_imu_video.empty(): q_imu_video.get_nowait()
#                     except queue.Empty: pass

#                 stabilized_frame = frame.copy()

#                 # BƠM KHUNG HÌNH VÀO LUỒNG PHỤ 2 GHI ĐĨA (BẤT ĐỒNG BỘ - KHÔNG CHỜ ĐỢI)
#                 try:
#                     disk_queue.put_nowait((frame, stabilized_frame, count, frame_timestamp))
#                 except queue.Full:
#                     # Nếu đĩa quá chậm dẫn đến tràn queue, bỏ qua log thay vì làm đứng hệ thống
#                     pass

#                 # BƠM KHUNG HÌNH VÀO LUỒNG PHỤ 1 ĐỂ LIVE-STREAM
#                 put_latest_to_queue(frame_queue, stabilized_frame)
#                 count += 1

#             except BrokenPipeError: process = None
#             except Exception as e: print(f"[VIDEO LỖI]: {e}")

#         else:
#             # Dọn dẹp an toàn khi tắt lệnh dừng luồng
#             if process is not None:
#                 try:
#                     frame_queue.put(None)
#                     disk_queue.put(None)
#                     if process.stdin: process.stdin.close()
#                     process.wait(timeout=1)
#                 except: pass
#                 process = None
#             if picam2 is not None:
#                 try: picam2.stop()
#                 except: pass
            
#             # Chờ luồng ghi đĩa giải phóng hết dữ liệu tồn đọng trong queue
#             if disk_thread is not None: disk_thread.join(timeout=2)
            
#             if writer_raw is not None: writer_raw.release(); writer_raw = None
#             if writer_stab is not None: writer_stab.release(); writer_stab = None
#             if video_ts_file is not None: video_ts_file.close(); video_ts_file = None
#             time.sleep(0.2)

#     # Giải phóng triệt để khi tắt hệ thống
#     if process is not None:
#         try:
#             frame_queue.put(None)
#             disk_queue.put(None)
#             if process.stdin: process.stdin.close()
#             process.wait(timeout=1)
#         except: pass
#     try: picam2.stop()
#     except: pass
#     if disk_thread is not None: disk_thread.join(timeout=2)
#     if writer_raw is not None: writer_raw.release()
#     if writer_stab is not None: writer_stab.release()
#     if video_ts_file is not None: video_ts_file.close()

def video_task(config, stop_event, camera_active_event, q_imu_video):
    """Luồng truyền và ghi Video thô bất đồng bộ - Bản sửa lỗi giải phóng Driver toàn diện"""
    vid_config = config["config"]["video"]
    laptop_ip = vid_config["laptop_ip"]
    port = vid_config["port"]
    width = vid_config["width"]
    height = vid_config["height"]
    framerate = vid_config["framerate"]
    rotation = vid_config["rotation"]
    
    frame_size = width * height * 3
    
    video_cmd = (
        f"gst-launch-1.0 fdsrc blocksize={frame_size} do-timestamp=true ! "
        f"videoparse format=rgb width={width} height={height} framerate={framerate}/1 ! "
        f"videoconvert ! videoflip method=rotate-{rotation} ! "
        f"queue leaky=downstream max-size-buffers=1 max-size-bytes=0 max-size-time=0 ! "
        f"x264enc threads=2 tune=zerolatency speed-preset=ultrafast bitrate=1500 ! " 
        f"video/x-h264, profile=baseline ! "
        f"h264parse ! rtph264pay config-interval=1 pt=96 ! "
        f"udpsink host={laptop_ip} port={port} sync=false buffer-size=2097152"
    )
    cmd_list = shlex.split(video_cmd)
    
    def cleanup_hardware(p, p_cam, w_raw, w_stab, ts_file, f_q, d_q, d_th):
        """Hủy toàn bộ tài nguyên, giải phóng triệt để driver camera để tránh treo bus I2C/CSI"""
        print("[VIDEO CLEANUP] Bắt đầu giải phóng tài nguyên hệ thống...")
        if f_q is not None:
            try: f_q.put(None)
            except: pass
        if d_q is not None:
            try: d_q.put(None)
            except: pass
            
        if p is not None:
            try:
                if p.stdin: p.stdin.close()
                p.wait(timeout=1)
            except: pass
            
        if p_cam is not None:
            try: 
                p_cam.stop()
                p_cam.close() # Đóng kết nối tầng libcamera
            except: pass
            
        if d_th is not None: 
            try: d_th.join(timeout=1)
            except: pass
            
        if w_raw is not None: 
            try: w_raw.release()
            except: pass
        if w_stab is not None: 
            try: w_stab.release()
            except: pass
        if ts_file is not None: 
            try: ts_file.close()
            except: pass
        print("[VIDEO CLEANUP] Driver phần cứng đã được reset sạch sẽ!")

    process = None
    picam2 = None  # Đẩy biến camera thành None để quản lý vòng đời động
    writer_thread = None
    disk_thread = None
    writer_raw = None
    writer_stab = None
    video_ts_file = None
    video_ts_writer = None
    
    frame_queue = queue.Queue(maxsize=1)
    disk_queue = queue.Queue(maxsize=60)

    while not stop_event.is_set():
        if camera_active_event.is_set():
            if process is None:
                try:
                    print("[VIDEO] Tiến hành khởi tạo MỚI hoàn toàn thực thể Picamera2...")
                    picam2 = Picamera2()
                    video_config = picam2.create_video_configuration(
                        main={"size": (width, height), "format": "RGB888"},
                        controls={"FrameRate": framerate},
                    )
                    picam2.configure(video_config)
                    
                    picam2.start()
                    time.sleep(0.5)

                    process = subprocess.Popen(cmd_list, stdin=subprocess.PIPE)
                    fourcc = cv.VideoWriter_fourcc(*'MJPG')
                    writer_raw = cv.VideoWriter('video_raw.avi', fourcc, framerate, (width, height))
                    writer_stab = cv.VideoWriter('video_stabilized.avi', fourcc, framerate, (width, height))

                    log_dir = "/app/logs"
                    os.makedirs(log_dir, exist_ok=True)
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ts_filename = f"{log_dir}/video_timestamps_{timestamp_str}.csv"
                    
                    video_ts_file = open(ts_filename, mode='w', newline='', encoding='utf-8')
                    video_ts_writer = csv.writer(video_ts_file)
                    video_ts_writer.writerow(["frame_index", "timestamp"])
                    print(f"[VIDEO TS] File timestamp sẵn sàng: {ts_filename}")

                    writer_thread = threading.Thread(
                        target=video_writer_task, 
                        args=(frame_queue, stop_event, process), 
                        daemon=True
                    )
                    writer_thread.start()

                    disk_thread = threading.Thread(
                        target=disk_writer_task,
                        args=(disk_queue, stop_event, writer_raw, writer_stab, video_ts_writer),
                        daemon=True
                    )
                    disk_thread.start()
                    
                    count = 0

                except Exception as e:
                    print(f"[VIDEO LỖI INIT] Lỗi khởi động camera tầng cứng: {e}")
                    cleanup_hardware(process, picam2, writer_raw, writer_stab, video_ts_file, None, None, None)
                    process = None
                    picam2 = None # Hủy thực thể để vòng sau tạo mới hoàn toàn
                    time.sleep(3)
                    continue

            try:
                frame_rgb = picam2.capture_array()
                frame_timestamp = time.monotonic() 
                
                if frame_rgb is None: 
                    continue
                    
                frame = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)

                if q_imu_video is not None:
                    try:
                        while not q_imu_video.empty(): q_imu_video.get_nowait()
                    except queue.Empty: pass

                stabilized_frame = frame.copy()

                try:
                    disk_queue.put_nowait((frame, stabilized_frame, count, frame_timestamp))
                except queue.Full:
                    pass

                put_latest_to_queue(frame_queue, stabilized_frame)
                count += 1

            except BrokenPipeError: 
                print("[VIDEO] GStreamer ngắt kết nối (Broken Pipe).")
                cleanup_hardware(process, picam2, writer_raw, writer_stab, video_ts_file, frame_queue, disk_queue, disk_thread)
                process = None
                picam2 = None
            except Exception as e: 
                print(f"[VIDEO CRITICAL RUNTIME ERROR]: Lỗi Remote I/O hoặc mất kết nối: {e}")
                cleanup_hardware(process, picam2, writer_raw, writer_stab, video_ts_file, frame_queue, disk_queue, disk_thread)
                process = None
                picam2 = None # Ép hủy đối tượng lỗi
                time.sleep(2) # Nghỉ giải lao cho chip điều khiển phần cứng hồi sức

        else:
            if process is not None:
                cleanup_hardware(process, picam2, writer_raw, writer_stab, video_ts_file, frame_queue, disk_queue, disk_thread)
                process = None
                picam2 = None
                writer_raw = None; writer_stab = None; video_ts_file = None
            time.sleep(0.2)

    if process is not None or picam2 is not None:
        cleanup_hardware(process, picam2, writer_raw, writer_stab, video_ts_file, frame_queue, disk_queue, disk_thread)