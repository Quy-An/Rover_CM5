import subprocess
import os
import signal
import time

def thread_stream_video(laptop_ip, rotation=180, stop_event=None):
    print("🎥 [Luồng Video] Đang kích hoạt libcamerasrc truyền dữ liệu trực tiếp...")
    
    # Định nghĩa chuỗi quay hình dựa trên tham số truyền vào
    flip_method = f"rotate-{rotation}" if rotation in [90, 180, 270] else "none"
    flip_element = f"videoflip method={flip_method} !" if flip_method != "none" else ""

    video_cmd = (
        f"gst-launch-1.0 libcamerasrc ! video/x-raw, width=640, height=480, framerate=30/1, format=I420 ! "
        f"videoconvert ! {flip_element} "
        f"x264enc tune=zerolatency speed-preset=ultrafast ! video/x-h264, profile=baseline ! "
        f"h264parse ! rtph264pay config-interval=1 pt=96 ! "
        f"udpsink host={laptop_ip} port=5600 sync=false"
    )
    
    process = None
    try:
        # preexec_fn=os.setsid giúp gộp Shell và GStreamer vào chung một nhóm tiến trình (Process Group)
        process = subprocess.Popen(video_cmd, shell=True, preexec_fn=os.setsid)
        
        # Thay vì chặn cứng bằng .wait(), ta dùng vòng lặp để kiểm tra tín hiệu dừng từ main
        while True:
            if stop_event and stop_event.is_set():
                print("🎥 [Luồng Video] Nhận tín hiệu dừng, đang hạ rèm GStreamer...")
                break
                
            # Kiểm tra nếu bản thân GStreamer tự đột tử trước
            if process.poll() is not None:
                print("🎥 [Luồng Video] Tiến trình GStreamer đã tự kết thúc.")
                break
                
            time.sleep(0.2)
            
    except Exception as e:
        print(f"❌ Lỗi trong quá trình khởi chạy Stream Video: {e}")
        
    finally:
        if process and process.poll() is None:
            try:
                # Gửi tín hiệu SIGINT (Ctrl+C) tới TOÀN BỘ nhóm tiến trình để GStreamer giải phóng Camera chuẩn bài
                os.killpg(os.getpgid(process.pid), signal.SIGINT)
                process.wait(timeout=3) # Chờ tối đa 3 giây để giải phóng
                print("✅ [Luồng Video] Đã giải phóng Camera an toàn.")
            except subprocess.TimeoutExpired:
                # Nếu cứng đầu không chịu tắt, cưỡng bức diệt tận gốc
                print("⚠️ [Luồng Video] GStreamer treo, tiến hành cưỡng bức tắt (SIGKILL)...")
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except Exception as e:
                print(f"❌ Lỗi khi dọn dẹp luồng video: {e}")