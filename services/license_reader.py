# services/license_reader.py - Simplified with Clean Logging

import cv2
import numpy as np
import pytesseract
import re
import difflib 
import os
import tempfile
import atexit
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from services.rpi_camera import get_camera

# ============== CONFIGURATION ==============

VERIFICATION_KEYWORDS = [
    "REPUBLIC", "PHILIPPINES", "DEPARTMENT", "TRANSPORTATION", 
    "LAND TRANSPORTATION OFFICE", "DRIVER'S LICENSE", "DRIVERS LICENSE",
    "LICENSE", "NON-PROFESSIONAL", "PROFESSIONAL", "Last Name", "First Name", 
    "Middle Name", "Nationality", "Date of Birth", "Address", "License No", 
    "Expiration Date", "EXPIRATION", "Address", "ADDRESS"
]

# Detection thresholds
DETECTION_THRESHOLD = 2.5
MIN_VERIFICATION_KEYWORDS = 2
MIN_GUEST_KEYWORDS = 1
MIN_GUEST_INDICATORS = 2

# OCR configurations
OCR_CONFIG_STANDARD = '--psm 11 --oem 3'
OCR_CONFIG_QUICK = '--psm 6 --oem 3'
OCR_CONFIG_BATCH = r'--oem 3 --psm 6'

# Match confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.65
MEDIUM_CONFIDENCE_THRESHOLD = 0.50

# Camera display settings
SCREEN_DIMS = {'width': 720, 'height': 600, 'box_width': 600, 'box_height': 350}

@dataclass
class NameInfo:
    document_type: str
    name: str
    document_verified: str
    formatted_text: str
    fingerprint_info: Optional[dict] = None
    match_score: Optional[float] = None

# ============== TEMP FILE MANAGEMENT ==============

_temp_files = []

def register_temp_file(filepath: str) -> None:
    global _temp_files
    if filepath not in _temp_files:
        _temp_files.append(filepath)

def cleanup_all_temp_files() -> None:
    global _temp_files
    for filepath in _temp_files[:]:
        _safe_delete_temp_file(filepath)

def safe_delete_temp_file(filepath: str) -> None:
    _safe_delete_temp_file(filepath)

def _safe_delete_temp_file(filepath: str) -> None:
    global _temp_files
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            if filepath in _temp_files:
                _temp_files.remove(filepath)
    except Exception:
        pass

atexit.register(cleanup_all_temp_files)

# ============== IMAGE PROCESSING ==============

def preprocess_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    if img is None:
        raise Exception(f"Could not read image at {image_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)
    bilateral = cv2.bilateralFilter(equalized, 9, 75, 75)
    thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    return cv2.fastNlMeansDenoising(opening, None, 10, 7, 21)

def enhance_image(image: np.ndarray) -> np.ndarray:
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(image, -1, kernel)
    return cv2.convertScaleAbs(sharpened, alpha=1.5, beta=10)

def preprocess_batch(image_path: str) -> List[np.ndarray]:
    img = cv2.imread(image_path)
    if img is None:
        raise Exception(f"Could not read image at {image_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed = []
    
    # OTSU thresholding
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    processed.append(thresh)
    
    # CLAHE + OTSU
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)
    thresh2 = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    processed.append(thresh2)
    
    # Adaptive thresholding
    bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
    adaptive = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    processed.append(adaptive)
    
    return processed

# ============== OCR FUNCTIONS ==============

def extract_text_from_image(image_path: str, config: str = OCR_CONFIG_STANDARD) -> str:
    try:
        img = preprocess_image(image_path)
        enhanced = enhance_image(img)
        return pytesseract.image_to_string(enhanced, config=config)
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def find_best_line_match(input_name: str, ocr_lines: List[str]) -> Tuple[Optional[str], float]:
    best_match, best_score = None, 0.0
    
    for line in ocr_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Calculate basic similarity
        score = difflib.SequenceMatcher(None, input_name.lower(), line_clean.lower()).ratio()
        
        # Boost for exact matches (case insensitive)
        if input_name.lower() == line_clean.lower():
            score = 1.0
        
        # Boost for substring matches
        elif (input_name.lower() in line_clean.lower() or 
              line_clean.lower() in input_name.lower()):
            score = max(score, 0.85)
        
        # Boost for word-by-word matching
        input_words = set(input_name.lower().split())
        line_words = set(line_clean.lower().split())
        word_overlap = len(input_words.intersection(line_words))
        total_words = len(input_words.union(line_words))
        
        if total_words > 0:
            word_score = word_overlap / total_words
            score = max(score, word_score)
        
        if score > best_score:
            best_score = score
            best_match = line_clean
    
    return best_match, best_score

def format_text_output(raw_text: str) -> str:
    lines = raw_text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        sanitized = re.sub(r"[^a-zA-Z0-9\s,\.]", "", line)
        if len(sanitized) >= 3 and any(c.isalpha() for c in sanitized):
            cleaned.append(sanitized)
    return "\n".join(cleaned)

def _extract_text_batch(image_path: str) -> str:
    """Internal batch OCR processing"""
    processed_images = preprocess_batch(image_path)
    best_text = ""
    max_length = 0

    for img in processed_images:
        text = pytesseract.image_to_string(img, config=OCR_CONFIG_BATCH)
        if len(text) > max_length:
            best_text = text
            max_length = len(text)

    return best_text if max_length >= 50 else pytesseract.image_to_string(cv2.imread(image_path))

# ============== VERIFICATION FUNCTIONS ==============

def _verify_document(full_text: str, strict: bool = True) -> Tuple[bool, int]:
    """Internal document verification"""
    matched_keywords = {kw for kw in VERIFICATION_KEYWORDS if kw in full_text}
    keyword_count = len(matched_keywords)
    
    if strict:
        return keyword_count >= MIN_VERIFICATION_KEYWORDS, keyword_count
    
    # Lenient verification for guests
    has_date = bool(re.search(r'\d{2}[-/]\d{2}[-/]\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', full_text))
    has_license_num = bool(re.search(r'[A-Z]\d{2}-\d{2}-\d{6}|[A-Z]\d{8}|\d{10}', full_text))
    
    is_verified = keyword_count >= MIN_GUEST_KEYWORDS or keyword_count >= MIN_GUEST_INDICATORS or has_date or has_license_num
    return is_verified, keyword_count

def _detect_name_pattern(raw_text: str) -> Optional[str]:
    """Internal name pattern detection"""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    for line in lines:
        clean = re.sub(r"[^A-Z\s,.]", "", line.upper()).strip()
        if any(header in clean for header in VERIFICATION_KEYWORDS):
            continue
        if 4 < len(clean) < 60 and clean.replace(" ", "").isalpha() and " " in clean:
            return clean
    return None

def extract_name_from_lines(image_path: str, reference_name: str = "", best_ocr_match: str = "", match_score: float = 0.0) -> Dict[str, str]:
    raw_text = _extract_text_batch(image_path)
    full_text = " ".join(raw_text.splitlines()).upper()
    
    is_verified, keyword_count = _verify_document(full_text)
    doc_status = "Driver's License Detected" if is_verified else "Unverified Document"
    
    name_info = {"Document Verified": doc_status}
    
    # Priority 1: High confidence fingerprint match
    if reference_name and match_score >= HIGH_CONFIDENCE_THRESHOLD:
        name_info.update({
            "Name": reference_name,
            "Matched From": "Fingerprint Authentication (High Confidence)",
            "Match Confidence": f"{match_score * 100:.1f}%"
        })
        return name_info
    
    # Priority 2: OCR line match
    if best_ocr_match and match_score > MEDIUM_CONFIDENCE_THRESHOLD:
        name_info.update({
            "Name": best_ocr_match,
            "Matched From": "Best OCR Line Match",
            "Match Confidence": f"{match_score * 100:.1f}%"
        })
        return name_info
    
    # Priority 3: Pattern detection
    detected_name = _detect_name_pattern(raw_text)
    if detected_name:
        name_info.update({"Name": detected_name, "Matched From": "Pattern Detection"})
        return name_info
    
    name_info["Name"] = "Not Found"
    return name_info

def package_name_info(structured_data: Dict[str, str], basic_text: str, fingerprint_info: Optional[dict] = None) -> NameInfo:
    return NameInfo(
        document_type="Driver's License",
        name=structured_data.get('Name', 'Not Found'),
        document_verified=structured_data.get('Document Verified', 'Unverified'),
        formatted_text=format_text_output(basic_text),
        fingerprint_info=fingerprint_info
    )

# ============== CAMERA FUNCTIONS ==============

def _create_temp_file(fingerprint_info: Optional[dict] = None) -> str:
    """Internal temp file creation"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"motorpass_license_{fingerprint_info.get('student_id', 'guest')}_{timestamp}" if fingerprint_info else f"motorpass_license_{timestamp}"
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', prefix=prefix, delete=False)
    temp_filename = temp_file.name
    temp_file.close()
    
    register_temp_file(temp_filename)
    return temp_filename

def _process_camera_frame(frame: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int], float]:
    """Internal frame processing for camera"""
    # Brightness and mirror
    brightened = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
    mirrored = cv2.flip(brightened, 1)
    
    # Scale for display
    original_h, original_w = mirrored.shape[:2]
    scale = min(SCREEN_DIMS['width'] / original_w, SCREEN_DIMS['height'] / original_h)
    new_w, new_h = int(original_w * scale), int(original_h * scale)
    display_frame = cv2.resize(mirrored, (new_w, new_h))
    
    # Detection box
    box_width = min(SCREEN_DIMS['box_width'], new_w - 40)
    box_height = min(SCREEN_DIMS['box_height'], new_h - 40)
    center_x, center_y = new_w // 2, new_h // 2
    box_coords = (
        max(0, center_x - box_width // 2),
        max(0, center_y - box_height // 2),
        min(new_w, center_x + box_width // 2),
        min(new_h, center_y + box_height // 2)
    )
    
    return display_frame, box_coords, scale

def _detect_license_in_frame(frame: np.ndarray, box_coords: Tuple[int, int, int, int], scale: float) -> int:
    """Internal license detection in camera frame"""
    box_x1, box_y1, box_x2, box_y2 = box_coords
    orig_box_x1, orig_box_y1 = int(box_x1 / scale), int(box_y1 / scale)
    orig_box_x2, orig_box_y2 = int(box_x2 / scale), int(box_y2 / scale)
    roi = frame[orig_box_y1:orig_box_y2, orig_box_x1:orig_box_x2]
    
    if roi.size == 0:
        return 0
    
    try:
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        thresh_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        quick_text = pytesseract.image_to_string(thresh_roi, config=OCR_CONFIG_QUICK).upper()
        return sum(1 for kw in VERIFICATION_KEYWORDS if kw in quick_text)
    except Exception:
        return 0

def _draw_camera_ui(display_frame: np.ndarray, box_coords: Tuple[int, int, int, int], detections: int, target: str = "", retry_mode: bool = False) -> None:
    """Internal UI drawing for camera"""
    box_x1, box_y1, box_x2, box_y2 = box_coords
    new_h = display_frame.shape[0]
    
    # Detection box
    box_color = (0, 255, 0) if detections > 0 else (0, 0, 255)
    cv2.rectangle(display_frame, (box_x1, box_y1), (box_x2, box_y2), box_color, 3)
    
    # Text overlays
    camera_status = "RETAKE MODE" if retry_mode else "License Capture"
    cv2.putText(display_frame, camera_status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255) if retry_mode else (0, 255, 0), 1)
    
    if target:
        cv2.putText(display_frame, f"Target: {target}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    status = f"Detecting... {detections}/{DETECTION_THRESHOLD}" if detections > 0 else "Position license in box"
    cv2.putText(display_frame, status, (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if detections > 0 else (255, 255, 255), 1)
    cv2.putText(display_frame, "Press 'q' to quit, 's' to capture", (10, new_h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

# ============== UTILITY FUNCTIONS ==============

def print_summary(packaged: NameInfo, fingerprint_info: Optional[dict] = None, structured_data: Optional[Dict[str, str]] = None, 
                 is_guest: bool = False, guest_info: Optional[dict] = None) -> None:
    # Simplified summary - only show confidence if available
    if structured_data and "Match Confidence" in structured_data:
        print(f"📄 License processed - Name match: {structured_data['Match Confidence']}")

def retake_prompt(expected_name: str, detected_name: str) -> bool:
    """Simple retake prompt for name mismatch or not found"""
    print(f"⚠️ Name mismatch: Expected '{expected_name}', found '{detected_name}'")
    choice = input("Retake photo? (y/n): ").strip().lower()
    return choice == 'y'

# ============== COMPLETE VERIFICATION SYSTEM ==============

def complete_verification_flow(image_path: str, fingerprint_info: dict, 
                             helmet_verified: bool = True, 
                             license_expiration_valid: bool = True) -> bool:
    """Complete verification flow - simplified output"""
    
    # Process license with retakes until name matches or user stops
    license_result = licenseRead(image_path, fingerprint_info)
    
    # Extract final results
    final_name = license_result.name
    final_match_score = license_result.match_score or 0.0
    final_document_status = license_result.document_verified
    
    # Determine verification statuses
    fingerprint_verified = fingerprint_info['confidence'] > 50
    license_detected = "Driver's License Detected" in final_document_status
    name_matching_verified = final_match_score > HIGH_CONFIDENCE_THRESHOLD
    
    # Final status check
    all_verified = (helmet_verified and fingerprint_verified and 
                   license_expiration_valid and license_detected and 
                   name_matching_verified)
    
    # Show simplified results
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎯 VERIFICATION RESULTS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🪖 Helmet: {'✅' if helmet_verified else '❌'}")
    print(f"🔒 Fingerprint: {'✅' if fingerprint_verified else '❌'} ({fingerprint_info['confidence']}%)")
    print(f"📅 License Valid: {'✅' if license_expiration_valid else '❌'}")
    print(f"🆔 License Detected: {'✅' if license_detected else '❌'}")
    print(f"👤 Name Match: {'✅' if name_matching_verified else '❌'} ({final_match_score*100:.1f}%)")
    
    if all_verified:
        print("🟢 STATUS: ✅ FULLY VERIFIED")
    else:
        print("🟡 STATUS: ❌ VERIFICATION FAILED")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return all_verified

def complete_guest_verification_flow(image_path: str, guest_info: dict,
                                   helmet_verified: bool = True) -> bool:
    """Complete guest verification flow - simplified"""
    
    license_result = licenseReadGuest(image_path, guest_info)
    final_document_status = license_result.document_verified
    license_detected = "Driver's License Detected" in final_document_status
    
    guest_verified = helmet_verified and license_detected
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎯 GUEST VERIFICATION")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🪖 Helmet: {'✅' if helmet_verified else '❌'}")
    print(f"🆔 License: {'✅' if license_detected else '❌'}")
    print(f"👤 Guest: {guest_info['name']}")
    
    if guest_verified:
        print("🟢 STATUS: ✅ GUEST VERIFIED")
    else:
        print("🟡 STATUS: ❌ GUEST DENIED")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return guest_verified

def auto_capture_license_rpi(reference_name: str = "", fingerprint_info: Optional[dict] = None, retry_mode: bool = False) -> Optional[str]:
    """Auto-capture license using RPi Camera - simplified output"""
    camera = get_camera()
    if not camera.initialized:
        print("❌ Camera not initialized")
        return None
    
    temp_filename = _create_temp_file(fingerprint_info)
    if retry_mode:
        print("📷 RETAKE MODE - Position license in camera view")
    else:
        print("📷 Position license in camera view")
    
    frame_count = consecutive_detections = 0
    captured_frame = None
    
    cv2.namedWindow("MotorPass - License Capture", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("MotorPass - License Capture", 720, 600)
    
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                break
            
            display_frame, box_coords, scale = _process_camera_frame(frame)
            
            # Detection every 10 frames
            frame_count += 1
            if frame_count % 10 == 0:
                brightened = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                matched = _detect_license_in_frame(brightened, box_coords, scale)
                consecutive_detections = consecutive_detections + 1 if matched >= 2 else 0
            
            _draw_camera_ui(display_frame, box_coords, consecutive_detections, reference_name, retry_mode)
            cv2.imshow("MotorPass - License Capture", display_frame)
            
            # Auto capture or manual
            if consecutive_detections >= DETECTION_THRESHOLD:
                print("✅ License detected - capturing...")
                captured_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                break
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                captured_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                break
        
        cv2.destroyAllWindows()
        
        if captured_frame is not None:
            cv2.imwrite(temp_filename, captured_frame)
            print(f"✅ Image saved")
            return temp_filename
        else:
            safe_delete_temp_file(temp_filename)
            return None
            
    except Exception as e:
        print(f"❌ Camera error: {e}")
        cv2.destroyAllWindows()
        safe_delete_temp_file(temp_filename)
        return None

def licenseRead(image_path: str, fingerprint_info: dict) -> NameInfo:
    """Process license with fixed name matching logic"""
    reference_name = fingerprint_info['name']
    current_image_path = image_path
    
    try:
        while True:  # Keep retaking until name matches or user stops
            # Extract and process
            basic_text = extract_text_from_image(current_image_path)
            ocr_lines = [line.strip() for line in basic_text.splitlines() if line.strip()]
            name_from_ocr, sim_score = find_best_line_match(reference_name, ocr_lines)
            
            structured_data = extract_name_from_lines(current_image_path, reference_name, name_from_ocr, sim_score)
            packaged = package_name_info(structured_data, basic_text, fingerprint_info)
            
            # Store the match score for external verification
            packaged.match_score = sim_score
            
            print_summary(packaged, fingerprint_info, structured_data)
            
            # Check if name matches - FIXED LOGIC
            detected_name = packaged.name
            
            # Consider it a match if:
            # 1. Exact match (case insensitive)
            # 2. High similarity score (>= 50%)
            # 3. Substantial word overlap
            exact_match = (detected_name.lower() == reference_name.lower())
            high_similarity = sim_score and sim_score >= HIGH_CONFIDENCE_THRESHOLD
            
            # Additional check for word overlap
            ref_words = set(reference_name.lower().split())
            det_words = set(detected_name.lower().split())
            word_overlap_ratio = len(ref_words.intersection(det_words)) / len(ref_words) if ref_words else 0
            substantial_overlap = word_overlap_ratio >= 0.7
            
            name_matches = (detected_name != "Not Found" and 
                           (exact_match or high_similarity or substantial_overlap))
            
            # Debug output for troubleshooting
            if not name_matches:
                print(f"🔍 Debug - Exact: {exact_match}, Similarity: {sim_score:.3f}, Word overlap: {word_overlap_ratio:.3f}")
            
            # If name matches, return
            if name_matches:
                print("✅ Name verification successful!")
                return packaged
            
            # Name doesn't match - offer retake
            if not retake_prompt(reference_name, detected_name):
                print("⚠️ Proceeding with current result...")
                return packaged
            
            print("📷 Retaking photo...")
            
            # Clean up current temp file if different from original
            if current_image_path != image_path:
                safe_delete_temp_file(current_image_path)
            
            # Retake photo
            retake_image_path = auto_capture_license_rpi(reference_name, fingerprint_info, retry_mode=True)
            
            if retake_image_path:
                current_image_path = retake_image_path
            else:
                print("❌ Retake failed")
                return packaged
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
        error_packaged = package_name_info(
            {"Name": "Not Found", "Document Verified": "Failed"}, 
            "Processing failed", fingerprint_info
        )
        error_packaged.match_score = 0.0
        return error_packaged
    finally:
        # Clean up files
        if current_image_path != image_path:
            safe_delete_temp_file(current_image_path)
        safe_delete_temp_file(image_path)
def licenseReadGuest(image_path: str, guest_info: dict) -> NameInfo:
    """Process license for guest verification - simplified"""
    guest_name = guest_info['name']
    
    try:
        basic_text = extract_text_from_image(image_path)
        full_text = " ".join(basic_text.splitlines()).upper()
        
        is_verified, keyword_count = _verify_document(full_text, strict=False)
        
        packaged = NameInfo(
            document_type="Driver's License",
            name=guest_name,
            document_verified="Driver's License Detected" if is_verified else "Document Detected",
            formatted_text=format_text_output(basic_text),
            fingerprint_info=None
        )

        # If license not properly detected, offer retake
        if not is_verified and retake_prompt("Valid License Document", "Insufficient License Keywords"):
            print("📷 Retaking guest photo...")
            
            retake_image_path = auto_capture_license_rpi("Guest License", None, retry_mode=True)
            
            if retake_image_path:
                # Process retaken image
                retake_text = extract_text_from_image(retake_image_path)
                retake_full_text = " ".join(retake_text.splitlines()).upper()
                retake_is_verified, retake_keyword_count = _verify_document(retake_full_text, strict=False)
                
                retake_packaged = NameInfo(
                    document_type="Driver's License",
                    name=guest_name,
                    document_verified="Driver's License Detected" if retake_is_verified else "Document Detected",
                    formatted_text=format_text_output(retake_text),
                    fingerprint_info=None
                )
                
                safe_delete_temp_file(retake_image_path)
                return retake_packaged
        
        return packaged

    except Exception as e:
        print(f"❌ Processing error: {e}")
        return NameInfo(
            document_type="Driver's License",
            name=guest_name,
            document_verified="Processing Failed",
            formatted_text="Processing failed",
            fingerprint_info=None
        )
    finally:
        safe_delete_temp_file(image_path)
