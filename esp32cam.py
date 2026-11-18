#!/usr/bin/env -S uv run --script

# Demo how to capture stream from and ESP32cam

import cv2
import time

# Replace with your ESP32-CAM's IP address
stream_url = "http://192.168.0.131:81"            # Old esp32-cam-webserver
#stream_url = "http://192.168.0.132:81"            # Old esp32-cam-webserver
#stream_url = "http://192.168.0.133:81/stream"
stream_url = "http://192.168.0.133:81"  
#stream_url = "rtsp://192.168.0.133:8554/mjpeg/1"
#stream_url = "rtsp://tapo500:tapo500@192.168.0.127:554/stream1"   # Driveway cam - This works!

cap = cv2.VideoCapture(stream_url)

nframes=0
while True:
    ret, frame = cap.read()
    if nframes==0:
        t1 = time.perf_counter()
        fps=None
    else:
        t2 = time.perf_counter()
        fps = round( nframes/(t2-t1) , 1)
    nframes+=1
    if not ret:
        print("Failed to grab frame :-(")
        break
    else:
        print('Read image',nframes,'\t',frame.shape,'\t',fps,'fps')

    cv2.imshow("ESP32-CAM Live Stream", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
