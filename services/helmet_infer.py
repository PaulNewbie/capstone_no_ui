# services/helmet_infer.py - Updated for RPi Camera 3

import cv2
import numpy as np
import onnxruntime as ort
import time
from services.rpi_camera import get_camera

# === Helmet Detection Config ===
MODEL_PATH = "best.onnx"
CONF_THRESHOLD = 0.4
INPUT_SIZE = 320
HELMET_DETECTION_DURATION = 2  # seconds to detect helmet
CLASS_NAMES = ["Nutshell", "full-face helmet"]

# === Load ONNX model ===
try:
    session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    print("✅ Helmet detection model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load helmet detection model: {e}")
    session = None
    input_name = None

def preprocess_helmet(frame):
    """Preprocess frame for helmet detection"""
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    scale = INPUT_SIZE / max(h, w)
    nh, nw = int(h * scale), int(w * scale)
    img_resized = cv2.resize(img, (nw, nh))
    img_padded = np.full((INPUT_SIZE, INPUT_SIZE, 3), 114, dtype=np.uint8)
    img_padded[:nh, :nw] = img_resized
    blob = img_padded.astype(np.float32) / 255.0
    blob = blob.transpose(2, 0, 1)[np.newaxis, :]
    return blob, scale, (h, w)

def postprocess_helmet(predictions, scale, orig_size):
    """Postprocess helmet detection results"""
    h0, w0 = orig_size
    boxes, confidences, class_ids = [], [], []

    for det in predictions:
        scores = det[5:]
        cls_id = np.argmax(scores)
        conf = det[4] * scores[cls_id]

        if conf >= CONF_THRESHOLD:
            x, y, w, h = det[:4]
            x1 = int((x - w / 2) / scale)
            y1 = int((y - h / 2) / scale)
            x2 = int((x + w / 2) / scale)
            y2 = int((y + h / 2) / scale)

            boxes.append([x1, y1, x2 - x1, y2 - y1])
            confidences.append(float(conf))
            class_ids.append(cls_id)

    if not boxes:
        return []

    # Apply NMS
    indices = cv2.dnn.NMSBoxes(boxes, confidences, CONF_THRESHOLD, 0.5)
    
    result = []
    for i in indices:
        i = i[0] if isinstance(i, (list, tuple, np.ndarray)) else i
        x, y, w, h = boxes[i]
        result.append((x, y, x + w, y + h, confidences[i], class_ids[i]))

    return result

def verify_helmet():
    """Verify full-face helmet using RPi Camera 3"""
    if session is None:
        print("❌ Helmet detection model not loaded")
        return False
    
    print("\n🪖 === HELMET VERIFICATION REQUIRED ===")
    print("⚠️ Please wear your FULL-FACE helmet before proceeding")
    print(f"📷 Using RPi Camera 3 for {HELMET_DETECTION_DURATION} seconds...")
    print("📱 Press 'q' or ESC to cancel verification")
    
    # Get camera instance
    camera = get_camera()
    if not camera.initialized:
        print("❌ Failed to initialize RPi camera")
        return False
    
    detection_start = None
    consecutive_detections = 0
    required_consecutive = 5  # Require 5 consecutive detections for stability
    
    print("🔍 Helmet detection started... Please show your full-face helmet to the camera")
    
    # Create window
    cv2.namedWindow("Helmet Verification", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Helmet Verification", 800, 600)
    
    frame_count = 0
    last_frame_time = time.time()
    
    try:
        while True:
            current_time = time.time()
            
            # Get frame from RPi camera
            frame = camera.get_frame()
            
            if frame is None:
                print("❌ Failed to capture frame from RPi camera")
                # Show error message on a blank frame
                error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(error_frame, "Camera Connection Failed", (150, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(error_frame, "Check RPi camera connection", (120, 280),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow("Helmet Verification", error_frame)
                
                key = cv2.waitKey(1000) & 0xFF  # Wait 1 second
                if key == ord('q') or key == 27:
                    break
                continue
            
            frame_count += 1
            
            # Process frame for helmet detection
            try:
                blob, scale, orig_size = preprocess_helmet(frame)
                predictions = session.run(None, {input_name: blob})[0]
                detections = postprocess_helmet(predictions[0], scale, orig_size)
            except Exception as e:
                print(f"❌ Error in helmet detection: {e}")
                detections = []
            
            full_face_detected = False
            nutshell_detected = False
            
            # Check for helmets
            for x1, y1, x2, y2, conf, cls_id in detections:
                if cls_id == 1:  # full-face helmet
                    full_face_detected = True
                    label = f"Full-Face Helmet ({conf:.2f})"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    cv2.putText(frame, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                elif cls_id == 0:  # nutshell
                    nutshell_detected = True
                    label = f"Nutshell Helmet - NOT ALLOWED ({conf:.2f})"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(frame, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Update detection logic
            if full_face_detected and not nutshell_detected:
                consecutive_detections += 1
                
                if detection_start is None and consecutive_detections >= required_consecutive:
                    detection_start = current_time
                    print("✅ Full-face helmet consistently detected! Starting timer...")
                
                if detection_start is not None:
                    elapsed = current_time - detection_start
                    
                    # Show countdown on frame
                    progress_bar_width = 400
                    progress_bar_height = 30
                    progress_x = (frame.shape[1] - progress_bar_width) // 2
                    progress_y = 50
                    
                    # Draw progress bar background
                    cv2.rectangle(frame, (progress_x, progress_y), 
                                 (progress_x + progress_bar_width, progress_y + progress_bar_height), 
                                 (50, 50, 50), -1)
                    
                    # Draw progress
                    progress_width = int((elapsed / HELMET_DETECTION_DURATION) * progress_bar_width)
                    cv2.rectangle(frame, (progress_x, progress_y), 
                                 (progress_x + progress_width, progress_y + progress_bar_height), 
                                 (0, 255, 0), -1)
                    
                    # Progress text
                    progress_text = f"Helmet Verified: {elapsed:.1f}/{HELMET_DETECTION_DURATION}s"
                    text_size = cv2.getTextSize(progress_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                    text_x = (frame.shape[1] - text_size[0]) // 2
                    cv2.putText(frame, progress_text, (text_x, progress_y + 95),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    print(f"⏱️ Helmet verified for {elapsed:.1f}/{HELMET_DETECTION_DURATION} seconds")
                    
                    if elapsed >= HELMET_DETECTION_DURATION:
                        print("✅ Helmet verification successful!")
                        
                        # Show success message for 2 seconds
                        success_frame = frame.copy()
                        cv2.rectangle(success_frame, (50, 200), (frame.shape[1] - 50, 350), (0, 255, 0), -1)
                        cv2.putText(success_frame, "HELMET VERIFICATION", (text_x - 50, 250),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                        cv2.putText(success_frame, "SUCCESSFUL!", (text_x + 20, 300),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                        cv2.putText(success_frame, "Proceeding to fingerprint...", (text_x - 80, 330),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        
                        cv2.imshow("Helmet Verification", success_frame)
                        cv2.waitKey(2000)  # Show success for 2 seconds
                        
                        cv2.destroyAllWindows()
                        return True
            else:
                consecutive_detections = 0
                if detection_start is not None:
                    print("⚠️ Full-face helmet lost! Please keep helmet visible...")
                detection_start = None
                
                # Show status on frame
                if nutshell_detected:
                    status_text = "NUTSHELL HELMET NOT ALLOWED"
                    status_color = (0, 0, 255)
                else:
                    status_text = "Please wear FULL-FACE HELMET"
                    status_color = (0, 165, 255)  # Orange
                
                text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = (frame.shape[1] - text_size[0]) // 2
                cv2.putText(frame, status_text, (text_x, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            
            # Add frame info
            fps = 1.0 / (current_time - last_frame_time) if (current_time - last_frame_time) > 0 else 0
            last_frame_time = current_time
            
            cv2.putText(frame, f"Frame: {frame_count} | FPS: {fps:.1f}", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Instructions
            cv2.putText(frame, "Press 'q' or ESC to cancel", (10, frame.shape[0] - 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Show frame
            cv2.imshow("Helmet Verification", frame)
            
            # Check for user input
            key = cv2.waitKey(30) & 0xFF  # 30ms delay for smoother video
            if key == ord('q') or key == 27:  # 'q' or ESC
                print("❌ Helmet verification cancelled by user")
                break
    
    finally:
        cv2.destroyAllWindows()
    
    return False
