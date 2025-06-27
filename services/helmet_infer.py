# services/helmet_infer.py - Fixed with proper camera cleanup

import cv2
import numpy as np
import onnxruntime as ort
import time
from services.rpi_camera import force_camera_cleanup, CameraContext

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
    """Verify full-face helmet using RPi Camera with smart cleanup"""
    if session is None:
        print("❌ Helmet detection model not loaded")
        return False
    
    print("\n🪖 === HELMET VERIFICATION REQUIRED ===")
    print("⚠️ Please wear your FULL-FACE helmet before proceeding")
    print(f"📷 Using RPi Camera for {HELMET_DETECTION_DURATION} seconds...")
    print("📱 Press 'q' or ESC to cancel verification")
    
    # Smart cleanup - only cleans if needed
    force_camera_cleanup()
    
    result = False
    
    try:
        # Use context manager for guaranteed cleanup
        with CameraContext() as camera:
            if not camera.initialized:
                print("❌ Failed to initialize RPi camera")
                return False
            
            detection_start = None
            consecutive_detections = 0
            required_consecutive = 5
            
            print("🔍 Helmet detection started... Please show your full-face helmet to the camera")
            
            # Create window
            cv2.namedWindow("Helmet Verification", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Helmet Verification", 800, 600)
            
            frame_count = 0
            last_frame_time = time.time()
            
            while True:
                current_time = time.time()
                
                # Get frame from RPi camera
                frame = camera.get_frame()
                
                if frame is None:
                    print("❌ Failed to capture frame from RPi camera")
                    # Show error message
                    error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(error_frame, "Camera Connection Failed", (150, 240),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.imshow("Helmet Verification", error_frame)
                    
                    key = cv2.waitKey(1000) & 0xFF
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
                        progress_text = f"Helmet Verified: {elapsed:.1f}/{HELMET_DETECTION_DURATION}s"
                        cv2.putText(frame, progress_text, (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        
                        if elapsed >= HELMET_DETECTION_DURATION:
                            print("✅ Helmet verification successful!")
                            result = True
                            break
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
                        status_color = (0, 165, 255)
                    
                    cv2.putText(frame, status_text, (10, 40),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
                
                # Show frame
                cv2.imshow("Helmet Verification", frame)
                
                # Check for user input
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q') or key == 27:
                    print("❌ Helmet verification cancelled by user")
                    break
    
    except Exception as e:
        print(f"❌ Error during helmet verification: {e}")
    
    finally:
        # Ensure cleanup happens no matter what
        try:
            cv2.destroyWindow("Helmet Verification")
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        except:
            pass
    
    # Context manager handles cleanup automatically
    return result
