# services/license_reader.py - Cleaned and Simplified

import cv2
import numpy as np
import pytesseract
import re
import difflib 
import os
import tempfile
import atexit
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from services.rpi_camera import get_camera

# ============== CONFIGURATION ==============

OCR_CONFIG_FAST = '--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789., '
OCR_CONFIG_STANDARD = '--psm 11 --oem 3'
OCR_CONFIG_DETAILED = '--psm 4 --oem 3'

OPTIMAL_WIDTH, OPTIMAL_HEIGHT = 1280, 960
MIN_WIDTH, MIN_HEIGHT = 640, 480
CACHE_DIR = "cache/ocr"
MAX_CACHE_FILES = 10

VERIFICATION_KEYWORDS = [
    "REPUBLIC", "PHILIPPINES", "DEPARTMENT", "TRANSPORTATION", 
    "LAND TRANSPORTATION OFFICE", "DRIVER'S LICENSE", "DRIVERS LICENSE",
    "LICENSE", "NON-PROFESSIONAL", "PROFESSIONAL", "LAST NAME", "FIRST NAME", 
    "MIDDLE NAME", "NATIONALITY", "DATE OF BIRTH", "ADDRESS", "LICENSE NO", 
    "EXPIRATION DATE", "CONDITIONS", "EYES COLOR", "AGENCY CODE", "WEIGHT", 
    "HEIGHT", "BLOOD TYPE", "RESTRICTION", "SIGNATURE"
]

FILTER_KEYWORDS = [
    'REPUBLIC', 'PHILIPPINES', 'TRANSPORTATION', 'DRIVER', 'LICENSE', 
    'NATIONALITY', 'ADDRESS', 'DATE', 'EXPIRATION', 'WEIGHT', 'HEIGHT',
    'CITY', 'PROVINCE', 'STREET', 'ROAD', 'BARANGAY', 'BLOCK', 'LOT', 
    'BLK', 'PH', 'RESIDENCIA', 'MARILAO', 'BULACAN'
]

MIN_KEYWORDS_FOR_SUCCESS = 2
MIN_CONFIDENCE_SCORE = 60

@dataclass
class NameInfo:
    document_type: str
    name: str
    document_verified: str
    formatted_text: str
    fingerprint_info: Optional[dict] = None
    match_score: Optional[float] = None

# ============== CACHING SYSTEM ==============

def _get_cache_key(image_path: str) -> str:
    """Generate cache key from image file"""
    try:
        with open(image_path, 'rb') as f:
            start = f.read(1024)
            f.seek(-1024, 2)
            end = f.read(1024)
            return hashlib.md5(start + end).hexdigest()
    except:
        return hashlib.md5(image_path.encode()).hexdigest()

def _get_cached_result(image_path: str, method: str) -> Optional[str]:
    """Get cached OCR result if available"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_key = f"{_get_cache_key(image_path)}_{method}"
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.txt")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
    except:
        pass
    return None

def _cache_result(image_path: str, method: str, text: str):
    """Cache OCR result for future use"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_key = f"{_get_cache_key(image_path)}_{method}"
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.txt")
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(text)
        _cleanup_old_cache()
    except:
        pass

def _cleanup_old_cache():
    """Remove old cache files to save space (limit to 10 files)"""
    try:
        cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.txt')]
        if len(cache_files) > MAX_CACHE_FILES:
            cache_files.sort(key=lambda x: os.path.getmtime(os.path.join(CACHE_DIR, x)))
            for old_file in cache_files[:-MAX_CACHE_FILES]:
                os.remove(os.path.join(CACHE_DIR, old_file))
    except:
        pass

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
    except:
        pass

atexit.register(cleanup_all_temp_files)

# ============== IMAGE PROCESSING ==============

def _resize_image_optimal(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    
    if (MIN_WIDTH <= w <= OPTIMAL_WIDTH and MIN_HEIGHT <= h <= OPTIMAL_HEIGHT):
        return image
    
    if w > OPTIMAL_WIDTH or h > OPTIMAL_HEIGHT:
        scale = min(OPTIMAL_WIDTH / w, OPTIMAL_HEIGHT / h)
    else:
        scale = min(MIN_WIDTH / w, MIN_HEIGHT / h)
    
    new_w, new_h = int(w * scale), int(h * scale)
    interpolation = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_LANCZOS4
    
    return cv2.resize(image, (new_w, new_h), interpolation=interpolation)

def _preprocess_image(image: np.ndarray, method: str) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    if method == "fast":
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
    
    elif method == "standard":
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.bilateralFilter(enhanced, 5, 50, 50)
        return cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    else:  # detailed
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
        return cv2.adaptiveThreshold(morph, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4)

# ============== OCR PROCESSING ==============

def _count_verification_keywords(text: str) -> int:
    text_upper = text.upper()
    return sum(1 for keyword in VERIFICATION_KEYWORDS if keyword in text_upper)

def _calculate_confidence_score(text: str, keywords_found: int) -> int:
    base_score = min(90, max(30, (keywords_found / len(VERIFICATION_KEYWORDS)) * 100))
    
    if len(text.strip()) > 50:
        base_score += 10
    if re.search(r'[A-Z]\d{2}-\d{2}-\d{6}|[A-Z]\d{8}|\d{10}', text):
        base_score += 5
    if re.search(r'\d{2}[-/]\d{2}[-/]\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text):
        base_score += 5
    
    return min(100, int(base_score))

def _extract_text_smart(image_path: str, is_guest: bool = False) -> str:
    """Smart OCR extraction with caching"""
    cache_method = "guest" if is_guest else "smart"
    cached_result = _get_cached_result(image_path, cache_method)
    if cached_result:
        return cached_result
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        image = _resize_image_optimal(image)
        start_time = time.time()
        
        methods = [
            ("fast", OCR_CONFIG_FAST),
            ("standard", OCR_CONFIG_STANDARD),
            ("detailed", OCR_CONFIG_DETAILED)
        ]
        
        if is_guest:
            methods = methods[:2]  # Skip detailed for guests
            min_keywords_needed, min_confidence_needed = 1, 40
        else:
            min_keywords_needed, min_confidence_needed = MIN_KEYWORDS_FOR_SUCCESS, MIN_CONFIDENCE_SCORE
        
        best_text, best_score = "", 0
        
        for method_name, ocr_config in methods:
            try:
                processed = _preprocess_image(image, method_name)
                text = pytesseract.image_to_string(processed, config=ocr_config)
                
                keywords_found = _count_verification_keywords(text)
                confidence = _calculate_confidence_score(text, keywords_found)
                
                if confidence > best_score:
                    best_score = confidence
                    best_text = text
                
                if keywords_found >= min_keywords_needed and confidence >= min_confidence_needed:
                    break
                
                timeout = 6 if is_guest else 8
                if time.time() - start_time > timeout:
                    break
                    
            except Exception:
                continue
        
        _cache_result(image_path, cache_method, best_text)
        return best_text
        
    except Exception as e:
        return f"Error extracting text: {str(e)}"

# ============== NAME EXTRACTION ==============

def _format_name(name: str) -> str:
    """Format extracted name to proper case"""
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            last_name = parts[0].strip().title()
            first_part = parts[1].strip().title()
            return f"{first_part} {last_name}"
    
    return name.title()

def _detect_name_from_ocr(raw_text: str, is_guest: bool = False) -> Optional[str]:
    """Simple and reliable name detection"""
    import re
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    if is_guest:
        # Check first 15 lines only
        for line in lines[:15]:
            original_line = line.strip()
            line_upper = line.upper().strip()
            
            # Remove common OCR artifacts: leading numbers, dots, special chars
            line_clean = re.sub(r'^[\d\.\-\s]+', '', line_upper)
            
            # Skip empty or too short lines
            if not line_clean or len(line_clean) < 7:
                continue
            
            # Must have exactly one comma
            if line_clean.count(',') != 1:
                continue
            
            # Skip if line is too long (likely not a name)
            if len(line_clean) > 50:
                continue
            
            # ADDRESS PATTERNS TO SKIP - More comprehensive list
            address_indicators = [
                'BLK', 'BLOCK', 'LOT', 'PHASE', 'PH', 
                'STREET', 'ST', 'ROAD', 'RD', 'AVENUE', 'AVE',
                'BARANGAY', 'BRGY', 'CITY', 'PROVINCE',
                'UNIT', 'BLDG', 'BUILDING', 'FLOOR', 'FLR',
                'SUBDIVISION', 'SUBD', 'VILLAGE', 'VILL',
                'RESIDENCIA', 'RESIDENCE', 'APARTMENT', 'APT',
                'CONDO', 'CONDOMINIUM', 'TOWNHOUSE',
                'ZIP', 'POSTAL', 'PUROK', 'SITIO'
            ]
            
            # Check if line contains address indicators (check individual words)
            line_words = line_clean.split()
            if any(word in address_indicators for word in line_words):
                continue
            
            # Skip obvious document keywords
            skip_words = [
                'REPUBLIC', 'PHILIPPINES', 'DEPARTMENT', 'TRANSPORTATION', 
                'LICENSE', 'DRIVER', 'ADDRESS', 'NATIONALITY', 'OFFICE',
                'EXPIRATION', 'REGISTRATION', 'HEIGHT', 'WEIGHT',
                'RESTRICTION', 'CONDITION', 'BLOOD', 'TYPE'
            ]
            if any(word in line_clean for word in skip_words):
                continue
            
            # Skip lines with multi-digit numbers (common in addresses)
            if re.search(r'\b\d{2,}\b', line_clean):
                continue
            
            # Split and validate
            try:
                lastname, firstname = line_clean.split(',')
                lastname = lastname.strip()
                firstname = firstname.strip()
                
                # Clean names - remove any non-letter characters except spaces
                lastname_clean = re.sub(r'[^A-Z\s]', '', lastname).strip()
                firstname_clean = re.sub(r'[^A-Z\s]', '', firstname).strip()
                
                # Basic validation
                if (lastname_clean and firstname_clean and
                    len(lastname_clean) >= 2 and len(lastname_clean) <= 20 and
                    len(firstname_clean) >= 2 and len(firstname_clean) <= 30 and
                    lastname_clean.replace(' ', '').isalpha() and
                    firstname_clean.replace(' ', '').isalpha()):
                    
                    # Check word count (names typically don't have too many words)
                    if (len(lastname_clean.split()) <= 3 and 
                        len(firstname_clean.split()) <= 4):
                        # Keep original format: "SURNAME, FIRSTNAME MIDDLENAME"
                        return f"{lastname_clean}, {firstname_clean}"
                        
            except:
                continue
    
    # For students (existing logic)
    else:
        for line in lines:
            clean = re.sub(r"[^A-Z\s,.]", "", line.upper()).strip()
            if any(header in clean for header in VERIFICATION_KEYWORDS):
                continue
            if 4 < len(clean) < 60 and clean.replace(" ", "").isalpha() and " " in clean:
                return clean.title()
    
    return None
    
# ============== MAIN API FUNCTIONS ==============

def extract_text_from_image(image_path: str, config: str = OCR_CONFIG_STANDARD) -> str:
    """Extract text from license image"""
    return _extract_text_smart(image_path, is_guest=False)

def extract_guest_name_from_license(ocr_lines: List[str]) -> str:
    """Extract guest name from OCR lines"""
    # Convert lines to text for unified processing
    raw_text = '\n'.join(ocr_lines)
    detected_name = _detect_name_from_ocr(raw_text, is_guest=True)
    
    # Debug output
    if detected_name:
        print(f"Debug: Successfully extracted name: {detected_name}")
    else:
        print("Debug: No name found, using 'Guest'")
        print("Debug: First 10 OCR lines:")
        for i, line in enumerate(ocr_lines[:10]):
            print(f"  {i}: {line}")
    
    return detected_name if detected_name else "Guest"

def find_best_line_match(input_name: str, ocr_lines: List[str]) -> Tuple[Optional[str], float]:
    """Find best matching line for given name"""
    best_match, best_score = None, 0.0
    
    for line in ocr_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        score = difflib.SequenceMatcher(None, input_name.lower(), line_clean.lower()).ratio()
        
        if input_name.lower() == line_clean.lower():
            score = 1.0
        elif (input_name.lower() in line_clean.lower() or line_clean.lower() in input_name.lower()):
            score = max(score, 0.85)
        
        # Word overlap check
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
    """Format OCR text output"""
    lines = raw_text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        sanitized = re.sub(r"[^a-zA-Z0-9\s,\.]", "", line)
        if len(sanitized) >= 3 and any(c.isalpha() for c in sanitized):
            cleaned.append(sanitized)
    return "\n".join(cleaned)

def package_name_info(structured_data: Dict[str, str], basic_text: str, fingerprint_info: Optional[dict] = None) -> NameInfo:
    """Package name information"""
    return NameInfo(
        document_type="Driver's License",
        name=structured_data.get('Name', 'Not Found'),
        document_verified=structured_data.get('Document Verified', 'Unverified'),
        formatted_text=format_text_output(basic_text),
        fingerprint_info=fingerprint_info
    )

# ============== CAMERA FUNCTIONS ==============

def auto_capture_license_rpi(reference_name: str = "", fingerprint_info: Optional[dict] = None, retry_mode: bool = False) -> Optional[str]:
    """Auto-capture license using RPi Camera"""
    camera = get_camera()
    if not camera.initialized:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"motorpass_license_{fingerprint_info.get('student_id', 'guest')}_{timestamp}" if fingerprint_info else f"motorpass_license_{timestamp}"
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', prefix=prefix, delete=False)
    temp_filename = temp_file.name
    temp_file.close()
    register_temp_file(temp_filename)
    
    SCREEN_WIDTH, SCREEN_HEIGHT = 720, 600
    BOX_WIDTH, BOX_HEIGHT = 600, 350
    KEYWORDS_NEEDED = 3
    CAPTURE_DELAY = 1.0
    KEYWORD_CHECK_INTERVAL = 5
    
    frame_count = 0
    captured_frame = None
    ready_time = None
    current_keywords = 0
    
    cv2.namedWindow("MotorPass - License Capture", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("MotorPass - License Capture", SCREEN_WIDTH, SCREEN_HEIGHT)
    
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                break
            
            original_h, original_w = frame.shape[:2]
            scale = min(SCREEN_WIDTH / original_w, SCREEN_HEIGHT / original_h)
            new_w, new_h = int(original_w * scale), int(original_h * scale)
            
            brightened = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
            mirrored = cv2.flip(brightened, 1)
            display_frame = cv2.resize(mirrored, (new_w, new_h))
            
            center_x, center_y = new_w // 2, new_h // 2
            box_x1 = max(0, center_x - BOX_WIDTH // 2)
            box_y1 = max(0, center_y - BOX_HEIGHT // 2)
            box_x2 = min(new_w, center_x + BOX_WIDTH // 2)
            box_y2 = min(new_h, center_y + BOX_HEIGHT // 2)
            
            frame_count += 1
            
            # Check for license keywords periodically
            if frame_count % KEYWORD_CHECK_INTERVAL == 0:
                try:
                    orig_box_x1, orig_box_y1 = int(box_x1 / scale), int(box_y1 / scale)
                    orig_box_x2, orig_box_y2 = int(box_x2 / scale), int(box_y2 / scale)
                    roi = brightened[orig_box_y1:orig_box_y2, orig_box_x1:orig_box_x2]
                    
                    if roi.size > 0:
                        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                        thresh_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                        quick_text = pytesseract.image_to_string(thresh_roi, config=OCR_CONFIG_FAST).upper()
                        current_keywords = sum(1 for keyword in VERIFICATION_KEYWORDS if keyword in quick_text)
                        
                        if current_keywords >= KEYWORDS_NEEDED:
                            if ready_time is None:
                                ready_time = time.time()
                        else:
                            ready_time = None
                    else:
                        current_keywords = 0
                        ready_time = None
                        
                except Exception:
                    current_keywords = 0
                    ready_time = None
            
            ready_to_capture = current_keywords >= KEYWORDS_NEEDED and ready_time is not None
            
            # Auto capture after delay
            if ready_to_capture and (time.time() - ready_time) >= CAPTURE_DELAY:
                captured_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                break
            
            # Determine colors and status
            if ready_to_capture:
                box_color = (0, 255, 0)
                remaining_delay = CAPTURE_DELAY - (time.time() - ready_time) if ready_time else CAPTURE_DELAY
                status_text = f"READY! Capturing in {remaining_delay:.1f}s... ({current_keywords} keywords)"
                status_color = (0, 255, 0)
            elif current_keywords >= 2:
                box_color = (0, 255, 255)
                status_text = f"Almost ready... Found {current_keywords}/{KEYWORDS_NEEDED} keywords"
                status_color = (0, 255, 255)
            elif current_keywords >= 1:
                box_color = (0, 165, 255)
                status_text = f"License detected! Found {current_keywords}/{KEYWORDS_NEEDED} keywords"
                status_color = (0, 165, 255)
            else:
                box_color = (0, 0, 255)
                status_text = f"Position license in box... ({current_keywords} keywords found)"
                status_color = (255, 255, 255)
            
            # Draw UI elements
            cv2.rectangle(display_frame, (box_x1, box_y1), (box_x2, box_y2), box_color, 3)
            
            camera_status = "RETAKE MODE" if retry_mode else "License Capture"
            cv2.putText(display_frame, camera_status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255) if retry_mode else (0, 255, 0), 2)
            
            if reference_name:
                cv2.putText(display_frame, f"Target: {reference_name}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.putText(display_frame, status_text, (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
            cv2.putText(display_frame, "Auto-capture | 's' = manual | 'q' = quit", (10, new_h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
            # Progress bar
            if current_keywords > 0:
                progress_width = int((current_keywords / KEYWORDS_NEEDED) * 200)
                cv2.rectangle(display_frame, (10, new_h-40), (210, new_h-25), (50, 50, 50), -1)
                cv2.rectangle(display_frame, (10, new_h-40), (10 + progress_width, new_h-25), box_color, -1)
                cv2.putText(display_frame, f"Keywords: {current_keywords}/{KEYWORDS_NEEDED}", (10, new_h-45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Countdown
            if ready_to_capture and ready_time:
                remaining = CAPTURE_DELAY - (time.time() - ready_time)
                if remaining > 0:
                    countdown_text = f"{remaining:.1f}"
                    text_size = cv2.getTextSize(countdown_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0]
                    text_x = (new_w - text_size[0]) // 2
                    text_y = (new_h + text_size[1]) // 2
                    cv2.putText(display_frame, countdown_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
            
            cv2.imshow("MotorPass - License Capture", display_frame)
            
            key = cv2.waitKey(30) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                captured_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                break
        
        cv2.destroyAllWindows()
        
        if captured_frame is not None:
            optimized_frame = _resize_image_optimal(captured_frame)
            cv2.imwrite(temp_filename, optimized_frame)
            return temp_filename
        else:
            safe_delete_temp_file(temp_filename)
            return None
            
    except Exception:
        cv2.destroyAllWindows()
        safe_delete_temp_file(temp_filename)
        return None

# ============== VERIFICATION WORKFLOWS ==============

def _retake_prompt(expected_name: str, detected_name: str) -> bool:
    """Simple retake prompt"""
    print(f"⚠️ Name mismatch: Expected '{expected_name}', found '{detected_name}'")
    choice = input("Retake photo? (y/n): ").strip().lower()
    return choice == 'y'

def complete_verification_flow(image_path: str, fingerprint_info: dict, 
                             helmet_verified: bool = True, 
                             license_expiration_valid: bool = True) -> bool:
    """Complete student verification flow"""
    try:
        # Extract and process with OCR
        basic_text = extract_text_from_image(image_path)
        ocr_lines = [line.strip() for line in basic_text.splitlines() if line.strip()]
        name_from_ocr, sim_score = find_best_line_match(fingerprint_info['name'], ocr_lines)
        
        # Check license document verification
        keywords_found = _count_verification_keywords(basic_text.upper())
        license_detected = keywords_found >= 2
        
        # Check name matching
        detected_name = name_from_ocr if name_from_ocr else _detect_name_from_ocr(basic_text, is_guest=False)
        name_matching_verified = sim_score and sim_score > 0.65 if sim_score else False
        
        # Final verification
        fingerprint_verified = fingerprint_info['confidence'] > 50
        all_verified = (helmet_verified and fingerprint_verified and 
                       license_expiration_valid and license_detected and 
                       name_matching_verified)
        
        # Show results
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🎯 VERIFICATION RESULTS")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🪖 Helmet: {'✅' if helmet_verified else '❌'}")
        print(f"🔒 Fingerprint: {'✅' if fingerprint_verified else '❌'} ({fingerprint_info['confidence']}%)")
        print(f"📅 License Valid: {'✅' if license_expiration_valid else '❌'}")
        print(f"🆔 License Detected: {'✅' if license_detected else '❌'}")
        print(f"👤 Name Match: {'✅' if name_matching_verified else '❌'} ({(sim_score or 0)*100:.1f}%)")
        print(f"🟢 STATUS: {'✅ FULLY VERIFIED' if all_verified else '❌ VERIFICATION FAILED'}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return all_verified
        
    except Exception:
        return False
    finally:
        safe_delete_temp_file(image_path)

def complete_guest_verification_flow(image_path: str, guest_info: dict,
                                   helmet_verified: bool = True) -> bool:
    """Complete guest verification flow"""
    try:
        # Extract text and check for license verification
        basic_text = _extract_text_smart(image_path, is_guest=True)
        keywords_found = _count_verification_keywords(basic_text.upper())
        license_detected = keywords_found >= 1
        
        guest_verified = helmet_verified and license_detected
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🎯 GUEST VERIFICATION")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🪖 Helmet: {'✅' if helmet_verified else '❌'}")
        print(f"🆔 License: {'✅' if license_detected else '❌'}")
        print(f"👤 Guest: {guest_info['name']}")
        print(f"🟢 STATUS: {'✅ GUEST VERIFIED' if guest_verified else '❌ GUEST DENIED'}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return guest_verified
        
    except Exception:
        return False
    finally:
        safe_delete_temp_file(image_path)

# ============== LEGACY SUPPORT FUNCTIONS ==============
# These functions maintain compatibility with existing code

def extract_name_from_lines(image_path: str, reference_name: str = "", best_ocr_match: str = "", match_score: float = 0.0) -> Dict[str, str]:
    """Legacy function for backwards compatibility"""
    if not reference_name:
        raw_text = _extract_text_smart(image_path, is_guest=True)
        keywords_found = _count_verification_keywords(raw_text.upper())
        doc_status = "Driver's License Detected" if keywords_found >= 1 else "Document Detected"
        detected_name = _detect_name_from_ocr(raw_text, is_guest=True)
        
        return {
            "Document Verified": doc_status,
            "Name": detected_name if detected_name else "Guest User",
            "Matched From": "Simple Guest Extraction"
        }
    
    raw_text = _extract_text_smart(image_path, is_guest=False)
    keywords_found = _count_verification_keywords(raw_text.upper())
    doc_status = "Driver's License Detected" if keywords_found >= 2 else "Unverified Document"
    
    name_info = {"Document Verified": doc_status}
    
    if reference_name and match_score >= 0.65:
        name_info.update({
            "Name": reference_name,
            "Matched From": "Fingerprint Authentication (High Confidence)",
            "Match Confidence": f"{match_score * 100:.1f}%"
        })
    elif best_ocr_match and match_score > 0.50:
        name_info.update({
            "Name": best_ocr_match,
            "Matched From": "Best OCR Line Match",
            "Match Confidence": f"{match_score * 100:.1f}%"
        })
    else:
        detected_name = _detect_name_from_ocr(raw_text, is_guest=False)
        if detected_name:
            name_info.update({"Name": detected_name, "Matched From": "Pattern Detection"})
        else:
            name_info["Name"] = "Not Found"
    
    return name_info

def extract_guest_name_from_license_simple(image_path: str) -> Dict[str, str]:
    """Legacy function for backwards compatibility"""
    return extract_name_from_lines(image_path)

def licenseRead(image_path: str, fingerprint_info: dict) -> NameInfo:
    """Legacy function for backwards compatibility"""
    reference_name = fingerprint_info['name']
    
    try:
        basic_text = extract_text_from_image(image_path)
        ocr_lines = [line.strip() for line in basic_text.splitlines() if line.strip()]
        name_from_ocr, sim_score = find_best_line_match(reference_name, ocr_lines)
        
        structured_data = extract_name_from_lines(image_path, reference_name, name_from_ocr, sim_score)
        packaged = package_name_info(structured_data, basic_text, fingerprint_info)
        packaged.match_score = sim_score
        
        return packaged
        
    except Exception:
        error_packaged = package_name_info(
            {"Name": "Not Found", "Document Verified": "Failed"}, 
            "Processing failed", fingerprint_info
        )
        error_packaged.match_score = 0.0
        return error_packaged
    finally:
        safe_delete_temp_file(image_path)

def licenseReadGuest(image_path: str, guest_info: dict) -> NameInfo:
    """Legacy function for backwards compatibility"""
    try:
        basic_text = _extract_text_smart(image_path, is_guest=True)
        keywords_found = _count_verification_keywords(basic_text.upper())
        document_status = "Driver's License Detected" if keywords_found >= 1 else "Document Detected"
        
        return NameInfo(
            document_type="Driver's License",
            name=guest_info['name'],
            document_verified=document_status,
            formatted_text=format_text_output(basic_text),
            fingerprint_info=None
        )

    except Exception:
        return NameInfo(
            document_type="Driver's License",
            name=guest_info['name'],
            document_verified="Processing Failed",
            formatted_text="Processing failed",
            fingerprint_info=None
        )
    finally:
        safe_delete_temp_file(image_path)

def get_guest_name_from_license_image(image_path: str) -> str:
    """Legacy function for backwards compatibility"""
    try:
        raw_text = _extract_text_smart(image_path, is_guest=True)
        detected_name = _detect_name_from_ocr(raw_text, is_guest=True)
        return detected_name if detected_name else "Guest"
    except Exception:
        return "Guest"

if __name__ == "__main__":
    print("🚀 OCR System Ready")

# ============== CACHE UTILITY FUNCTIONS ==============

def get_ocr_performance_stats() -> Dict:
    """Get OCR performance statistics"""
    try:
        cache_files = len([f for f in os.listdir(CACHE_DIR) if f.endswith('.txt')])
        return {
            'cache_files': cache_files,
            'cache_directory': CACHE_DIR,
            'max_cache_files': MAX_CACHE_FILES,
            'status': 'Cache system active'
        }
    except:
        return {'status': 'Cache not available'}

def clear_ocr_cache():
    """Clear OCR cache"""
    try:
        import shutil
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR)
        print("✅ OCR cache cleared")
    except Exception as e:
        print(f"⚠️ Cache clear failed: {e}")
