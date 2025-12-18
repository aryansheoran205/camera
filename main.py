from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
import cv2
import time
import os

app = FastAPI()

camera = None
camera_on = False

CAPTURE_DIR = "captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Server running"}


# 🔘 ON / OFF switch (your existing endpoint)
@app.get("/switch")
def switch():
    global camera, camera_on

    if not camera_on:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            camera = None
            return {"message": "Camera failed to open"}

        camera_on = True
        return {"message": "Camera ON"}

    else:
        camera.release()
        camera = None
        camera_on = False
        return {"message": "Camera OFF"}


# 📸 Capture image
@app.get("/capture")
def capture():
    global camera, camera_on

    if not camera_on:
        return JSONResponse(
            status_code=400,
            content={"message": "Camera is OFF"}
        )

    success, frame = camera.read()
    if not success:
        return {"message": "Failed to capture"}

    filename = f"{CAPTURE_DIR}/img_{int(time.time())}.jpg"
    cv2.imwrite(filename, frame)

    return {"message": "Image saved", "file": filename}


# 🎥 Live video stream
def generate_frames():
    global camera, camera_on

    while camera_on:
        success, frame = camera.read()
        if not success:
            break

        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )


@app.get("/stream")
def stream():
    if not camera_on:
        return JSONResponse(
            status_code=400,
            content={"message": "Camera is OFF"}
        )

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
