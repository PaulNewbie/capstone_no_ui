# services/license_reader.py - Enhanced with ROI focus and stability tracking

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
MAX_CACHE_FILES = 10  # Increased from 5

VERIFICATION_KEYWORDS = [
    "REPUBLIC", "PHILIPPINES", "DEPARTMENT", "TRANSPORTATION", 
    "LAND TRANSPORTATION OFFICE", "DRIVER'S LICENSE", "DRIVERS LICENSE",
    "LICENSE", "NON-PROFESSIONAL", "PROFESSIONAL", "Last Name", "First Name", 
    "Middle Name", "Nationality", "Date of Birth", "Address", "License No", 
    "Expiration Date", "EXPIRATION", "ADDRESS"
]

MIN_KEYWORDS_FOR_SUCCESS = 3
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
    try:
        with open(image_path, 'rb') as f:
            start = f.read(1024)
            f.seek(-1024, 2)
            end = f.read(1024)
            return hashlib.md5(start + end).hexdigest()
    except:
        return hashlib.md5(image_path.encode()).hexdigest()

def _get_cached_result(image_path: str, method: str) -> Optional[str]:
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
    try:
        cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.txt')]
        if len(cache_files) > MAX_CACHE_FILES:
            cache_files.sort(key=lambda x: os.path.getmtime(os.path.join(CACHE_DIR, x)))
            for old_file in cache_files[:-MAX_CACHE_FILES]:
                os.remove(os.path.join(CACHE_DIR, old_file))
    except:
        pass

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

# ============== IMAGE QUALITY CHECKS ==============

def _check_image_quality(image: np.ndarray) -> bool:
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        mean_brightness = gray.mean()
        contrast = gray.std()
        
        return sharpness > 100 and 50 < mean_brightness < 200 and contrast > 30
    except:
        return False

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

# ============== MAIN OCR FUNCTIONS ==============

def extract_text_from_image(image_path: str, config: str = OCR_CONFIG_STANDARD) -> str:
    return _extract_text_smart(image_path, is_guest=False)

def find_best_line_match(input_name: str, ocr_lines: List[str]) -> Tuple[Optional[str], float]:
    best_match, best_score = None, 0.0
    
    for line in ocr_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        
        # Skip short names (4 letters or less without spaces/punctuation)
        name_letters_only = line_clean.replace(",", "").replace(".", "").replace(" ", "")
        if len(name_letters_only) <= 4:
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
    lines = raw_text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        sanitized = re.sub(r"[^a-zA-Z0-9\s,\.]", "", line)
        if len(sanitized) >= 3 and any(c.isalpha() for c in sanitized):
            cleaned.append(sanitized)
    return "\n".join(cleaned)

def extract_name_from_lines(image_path: str, reference_name: str = "", best_ocr_match: str = "", match_score: float = 0.0) -> Dict[str, str]:
    if not reference_name:
        return extract_guest_name_from_license_simple(image_path)
    
    raw_text = _extract_text_smart(image_path, is_guest=False)
    full_text = " ".join(raw_text.splitlines()).upper()
    
    keywords_found = _count_verification_keywords(full_text)
    
    # NEW: Check if names match - if they do, always consider license detected
    name_matches = False
    if reference_name and match_score >= 0.65:
        name_matches = True
        print(f"🎯 Name match detected ({match_score*100:.1f}%) - License validation override applied")
    
    # Override license detection if names match
    if name_matches:
        is_verified = True  # Force verification to true when names match
        doc_status = "Driver's License Detected (Name Match Override)"
    else:
        is_verified = keywords_found >= 1
        doc_status = "Driver's License Detected" if is_verified else "Unverified Document"
    
    name_info = {"Document Verified": doc_status}
    
    # Check match confidence levels
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
        detected_name = _detect_name_pattern(raw_text)
        if detected_name:
            name_info.update({"Name": detected_name, "Matched From": "Pattern Detection"})
        else:
            name_info["Name"] = "Not Found"
    
    return name_info

def extract_guest_name_from_license_simple(image_path: str) -> Dict[str, str]:
    raw_text = _extract_text_smart(image_path, is_guest=True)
    full_text = " ".join(raw_text.splitlines()).upper()
    
    keywords_found = _count_verification_keywords(full_text)
    is_verified = keywords_found >= 1
    
    doc_status = "Driver's License Detected" if is_verified else "Document Detected"
    ocr_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    detected_name = extract_guest_name_from_license(ocr_lines)
    
    return {
        "Document Verified": doc_status,
        "Name": detected_name if detected_name and detected_name != "Guest" else "Guest User",
        "Matched From": "Simple Guest Extraction" if detected_name and detected_name != "Guest" else "Default Guest Name"
    }

def extract_guest_name_from_license(ocr_lines: List[str]) -> str:
    # Enhanced filter keywords
    filter_keywords = [
        'ROAD', 'STREET', 'AVENUE', 'DISTRICT', 'CITY', 'PROVINCE', 'MARILAO', 'BULACAN',
        'BARANGAY', 'REPUBLIC', 'PHILIPPINES', 'TRANSPORTATION', 
        'DRIVER', 'LICENSE', 'NATIONALITY', 'ADDRESS', 'WEIGHT', 'HEIGHT',
        'LN', 'FNMN'  
    ]
    
    potential_names = []
    
    for line in ocr_lines:
        line_clean = line.strip().upper()
        
        if (not line_clean or len(line_clean) < 5 or len(line_clean) > 50 or
            any(keyword in line_clean for keyword in filter_keywords) or
            any(char.isdigit() for char in line_clean)):
            continue
        
        # Check if it's alphabetic (with spaces and commas allowed)
        if line_clean.replace(" ", "").replace(",", "").isalpha() and " " in line_clean:
            # Additional check: ensure the actual name content (without punctuation) is long enough
            name_content = line_clean.replace(",", "").replace(".", "").strip()
            if len(name_content.replace(" ", "")) <= 4:  # Skip if 4 letters or less
                continue
            
            # Check that each word has minimum length
            words = name_content.split()
            if any(len(word) < 2 for word in words):  # Skip if any word is less than 2 characters
                continue
                
            score = 0
            if "," in line_clean: score += 10  # Last, First format
            word_count = len(line_clean.split())
            if 2 <= word_count <= 4: score += 5
            if 10 <= len(line_clean) <= 30: score += 3
            potential_names.append((line_clean, score))
    
    if potential_names:
        potential_names.sort(key=lambda x: x[1], reverse=True)
        best_name = potential_names[0][0]
        return _format_extracted_name_simple(best_name)
    
    return "Guest"

def _format_extracted_name_simple(name: str) -> str:
    # First check if the name has enough actual letters
    name_letters_only = name.replace(",", "").replace(".", "").replace(" ", "")
    if len(name_letters_only) <= 4:  # Reject names with 4 letters or less
        return "Guest"
    
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            last_name = parts[0].strip().title()
            first_part = parts[1].strip().title()
            # Final check after formatting
            if len(last_name.replace(" ", "")) + len(first_part.replace(" ", "")) <= 4:
                return "Guest"
            return f"{first_part} {last_name}"
    
    # Final check for non-comma names
    if len(name.replace(" ", "")) <= 4:
        return "Guest"
    
    return name.title()

def _detect_name_pattern(raw_text: str) -> Optional[str]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    # Extended filter keywords for better name detection
    filter_keywords = [
        'REPUBLIC', 'PHILIPPINES', 'DEPARTMENT', 'TRANSPORTATION', 
        'LAND TRANSPORTATION OFFICE', 'DRIVER', 'LICENSE', 'DRIVERS LICENSE',
        'NON-PROFESSIONAL', 'PROFESSIONAL', 'NATIONALITY', 'ADDRESS', 
        'DATE OF BIRTH', 'EXPIRATION', 'AGENCY CODE', 'CONDITIONS',
        'EYES COLOR', 'WEIGHT', 'HEIGHT', 'BLOOD TYPE', 'RESTRICTION',
        'SIGNATURE', 'PHOTO', 'FIRST NAME', 'LAST NAME', 'MIDDLE NAME',
        'CITY', 'PROVINCE', 'BARANGAY', 'STREET', 'ROAD', 'AVENUE',
        'LN', 'FNMN', 'RESIDENCIA', 'BLK', 'LOT'  # Added new keywords
    ]
    
    for line in lines:
        line_upper = line.upper().strip()
        
        # Skip empty or very short lines
        if len(line_upper) < 5:
            continue
            
        # Skip lines with numbers (license numbers, dates, etc.)
        if any(char.isdigit() for char in line_upper):
            continue
            
        # Skip lines containing any filter keywords
        if any(keyword in line_upper for keyword in filter_keywords):
            continue
            
        # Clean the line for final check
        clean = re.sub(r"[^A-Z\s,]", "", line_upper).strip()
        
        # Additional check: ensure the actual name content (without punctuation) is long enough
        name_content = clean.replace(",", "").replace(".", "").strip()
        if len(name_content.replace(" ", "")) <= 4:  # Skip if 4 letters or less
            continue
        
        # Check that each word has minimum length
        words = name_content.split()
        if any(len(word) < 2 for word in words):  # Skip if any word is less than 2 characters
            continue
        
        # Check if it looks like a name
        if (5 <= len(clean) <= 50 and 
            clean.replace(" ", "").replace(",", "").isalpha() and 
            " " in clean and 
            len(clean.split()) >= 2):
            return clean.title()  # Return in proper case
    
    return None

def package_name_info(structured_data: Dict[str, str], basic_text: str, fingerprint_info: Optional[dict] = None) -> NameInfo:
    return NameInfo(
        document_type="Driver's License",
        name=structured_data.get('Name', 'Not Found'),
        document_verified=structured_data.get('Document Verified', 'Unverified'),
        formatted_text=format_text_output(basic_text),
        fingerprint_info=fingerprint_info
    )

# ============== CAMERA FUNCTIONS ==============

def auto_capture_license_rpi(reference_name: str = "", fingerprint_info: Optional[dict] = None, retry_mode: bool = False) -> Optional[str]:
    """Auto-capture license using RPi Camera with ROI-only enhancement and stability tracking"""
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
    CAPTURE_DELAY = 1.0
    KEYWORD_CHECK_INTERVAL = 5
    
    # Stability settings for longer green time
    STABILITY_FRAMES = 1  # Need 1 good reading to go green (reduced from 5 for faster response)
    MIN_GREEN_TIME = 2.0  # Stay green for at least 2 seconds
    KEYWORD_HISTORY_SIZE = 8  # Track last 8 readings
    
    frame_count = 0
    captured_frame = None
    ready_time = None
    current_keywords = 0
    keyword_history = []
    good_readings_count = 0
    green_start_time = None
    
    cv2.namedWindow("MotorPass - License Capture", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("MotorPass - License Capture", SCREEN_WIDTH, SCREEN_HEIGHT)
    
    def _enhance_roi_only(roi, keyword_count):
        """Enhance only the ROI based on keyword detection"""
        if keyword_count == 0:
            # Strong enhancement for poor detection
            alpha, beta = 2.0, 50
        elif keyword_count == 1:
            # Medium enhancement
            alpha, beta = 1.6, 35
        elif keyword_count == 2:
            # Light enhancement
            alpha, beta = 1.3, 25
        else:
            # Normal processing
            alpha, beta = 1.1, 15
        
        enhanced_roi = cv2.convertScaleAbs(roi, alpha=alpha, beta=beta)
        
        # Additional processing for very poor detection
        if keyword_count < 2:
            gray = cv2.cvtColor(enhanced_roi, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced_gray = clahe.apply(gray)
            enhanced_roi = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
        
        return enhanced_roi, alpha
    
    def _get_adaptive_threshold(keyword_count, keyword_history, is_currently_green):
        """Stable adaptive threshold with hysteresis"""
        if not keyword_history:
            return 3 if keyword_count == 0 else 2
        
        # Calculate average and stability
        avg_keywords = sum(keyword_history) / len(keyword_history)
        recent_stable = len([k for k in keyword_history[-3:] if k >= 2]) >= 2
        
        if is_currently_green:
            # Hysteresis: Once green, easier to stay green
            return 1 if recent_stable else 2
        else:
            # Need more evidence to go green
            if avg_keywords >= 2.5 and recent_stable:
                return 2
            elif avg_keywords >= 1.5:
                return 2
            else:
                return 3
    
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                break
            
            original_h, original_w = frame.shape[:2]
            scale = min(SCREEN_WIDTH / original_w, SCREEN_HEIGHT / original_h)
            new_w, new_h = int(original_w * scale), int(original_h * scale)
            
            # Keep display frame normal - no global brightness changes
            brightened = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
            mirrored = cv2.flip(brightened, 1)
            display_frame = cv2.resize(mirrored, (new_w, new_h))
            
            center_x, center_y = new_w // 2, new_h // 2
            box_x1 = max(0, center_x - BOX_WIDTH // 2)
            box_y1 = max(0, center_y - BOX_HEIGHT // 2)
            box_x2 = min(new_w, center_x + BOX_WIDTH // 2)
            box_y2 = min(new_h, center_y + BOX_HEIGHT // 2)
            
            frame_count += 1
            roi_enhancement_level = 1.0  # Track current ROI enhancement
            
            # Check for license keywords with stability tracking
            if frame_count % KEYWORD_CHECK_INTERVAL == 0:
                try:
                    orig_box_x1, orig_box_y1 = int(box_x1 / scale), int(box_y1 / scale)
                    orig_box_x2, orig_box_y2 = int(box_x2 / scale), int(box_y2 / scale)
                    
                    # Extract ROI from original brightened frame
                    roi = brightened[orig_box_y1:orig_box_y2, orig_box_x1:orig_box_x2]
                    
                    if roi.size > 0:
                        # Enhance only the ROI based on previous detection
                        enhanced_roi, roi_enhancement_level = _enhance_roi_only(roi, current_keywords)
                        
                        # Perform OCR on enhanced ROI
                        gray_roi = cv2.cvtColor(enhanced_roi, cv2.COLOR_BGR2GRAY)
                        thresh_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                        quick_text = pytesseract.image_to_string(thresh_roi, config=OCR_CONFIG_FAST).upper()
                        
                        current_keywords = sum(1 for keyword in VERIFICATION_KEYWORDS if keyword in quick_text)
                        
                        # Update keyword history for stability
                        keyword_history.append(current_keywords)
                        if len(keyword_history) > KEYWORD_HISTORY_SIZE:
                            keyword_history.pop(0)
                        
                        # Check if currently in green state
                        is_currently_green = ready_time is not None
                        keywords_needed = _get_adaptive_threshold(current_keywords, keyword_history, is_currently_green)
                        
                        # Stability logic for going green
                        if current_keywords >= keywords_needed:
                            good_readings_count += 1
                            
                            # First time going green - need stable readings
                            if not is_currently_green and good_readings_count >= STABILITY_FRAMES:
                                ready_time = time.time()
                                green_start_time = time.time()
                                good_readings_count = 0  # Reset counter
                            # Already green - stay green with hysteresis
                            elif is_currently_green:
                                pass  # Keep ready_time as is
                        else:
                            good_readings_count = 0
                            
                            # Only lose green state if enough time has passed
                            if is_currently_green and green_start_time:
                                time_green = time.time() - green_start_time
                                if time_green >= MIN_GREEN_TIME:
                                    ready_time = None
                                    green_start_time = None
                            elif not is_currently_green:
                                ready_time = None
                                green_start_time = None
                    else:
                        current_keywords = 0
                        good_readings_count = 0
                        ready_time = None
                        green_start_time = None
                        roi_enhancement_level = 1.0
                        
                except Exception:
                    current_keywords = 0
                    good_readings_count = 0
                    ready_time = None
                    green_start_time = None
                    roi_enhancement_level = 1.0
            
            is_currently_green = ready_time is not None
            keywords_needed = _get_adaptive_threshold(current_keywords, keyword_history, is_currently_green)
            ready_to_capture = ready_time is not None
            
            # Show stability progress
            stability_progress = min(100, (good_readings_count / STABILITY_FRAMES) * 100)
            green_time = (time.time() - green_start_time) if green_start_time else 0
            
            # Auto capture after delay - enhance the captured frame based on final ROI enhancement
            if ready_to_capture and (time.time() - ready_time) >= CAPTURE_DELAY:
                # Apply the same enhancement level to the full frame for capture
                if roi_enhancement_level > 1.2:
                    captured_frame = cv2.convertScaleAbs(frame, alpha=roi_enhancement_level, beta=30)
                else:
                    captured_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                break
            
            # Determine colors and status with stability info
            enhancement_info = f" (ROI: {roi_enhancement_level:.1f}x)" if roi_enhancement_level > 1.0 else ""
            
            if ready_to_capture:
                box_color = (0, 255, 0)
                remaining_delay = CAPTURE_DELAY - (time.time() - ready_time) if ready_time else CAPTURE_DELAY
                green_duration = f" [Green: {green_time:.1f}s]" if green_time > 0 else ""
                status_text = f"READY! Capturing in {remaining_delay:.1f}s... ({current_keywords}/{keywords_needed}){enhancement_info}{green_duration}"
                status_color = (0, 255, 0)
            elif good_readings_count > 0:
                box_color = (0, 255, 255)
                progress_text = f" [Stabilizing: {good_readings_count}/{STABILITY_FRAMES}]"
                status_text = f"Stabilizing... Found {current_keywords}/{keywords_needed} keywords{enhancement_info}{progress_text}"
                status_color = (0, 255, 255)
            elif current_keywords >= max(1, keywords_needed - 1):
                box_color = (0, 255, 255)
                avg_text = f" [Avg: {sum(keyword_history)/len(keyword_history):.1f}]" if keyword_history else ""
                status_text = f"Almost ready... Found {current_keywords}/{keywords_needed} keywords{enhancement_info}{avg_text}"
                status_color = (0, 255, 255)
            elif current_keywords >= 1:
                box_color = (0, 165, 255)
                status_text = f"License detected! Found {current_keywords}/{keywords_needed} keywords{enhancement_info}"
                status_color = (0, 165, 255)
            else:
                box_color = (0, 0, 255)
                status_text = f"Position license in box... ({current_keywords} keywords){enhancement_info}"
                status_color = (255, 255, 255)
            
            # Draw UI elements with ROI enhancement visualization
            # Make box color intensity reflect ROI enhancement level
            if roi_enhancement_level > 1.5:
                box_thickness = 4  # Thicker box for high enhancement
            else:
                box_thickness = 3
                
            cv2.rectangle(display_frame, (box_x1, box_y1), (box_x2, box_y2), box_color, box_thickness)
            
            # Optional: Show enhanced ROI preview in corner when enhancement is active
            if roi_enhancement_level > 1.2 and frame_count % KEYWORD_CHECK_INTERVAL == 0:
                try:
                    orig_box_x1, orig_box_y1 = int(box_x1 / scale), int(box_y1 / scale)
                    orig_box_x2, orig_box_y2 = int(box_x2 / scale), int(box_y2 / scale)
                    roi_preview = brightened[orig_box_y1:orig_box_y2, orig_box_x1:orig_box_x2]
                    enhanced_preview, _ = _enhance_roi_only(roi_preview, current_keywords)
                    
                    # Resize preview and place in corner
                    preview_h, preview_w = enhanced_preview.shape[:2]
                    preview_scale = min(150 / preview_w, 100 / preview_h)
                    preview_resized = cv2.resize(enhanced_preview, (int(preview_w * preview_scale), int(preview_h * preview_scale)))
                    
                    # Place in top-right corner
                    y1, y2 = 10, 10 + preview_resized.shape[0]
                    x1, x2 = new_w - preview_resized.shape[1] - 10, new_w - 10
                    
                    if y2 < new_h and x1 > 0:
                        display_frame[y1:y2, x1:x2] = preview_resized
                        cv2.rectangle(display_frame, (x1-1, y1-1), (x2+1, y2+1), (0, 255, 255), 1)
                        cv2.putText(display_frame, "Enhanced", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 255), 1)
                except:
                    pass
            
            camera_status = "RETAKE MODE" if retry_mode else "License Capture [ROI Focus]"
            cv2.putText(display_frame, camera_status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255) if retry_mode else (0, 255, 0), 2)
            
            if reference_name:
                cv2.putText(display_frame, f"Target: {reference_name}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.putText(display_frame, status_text, (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
            cv2.putText(display_frame, "Auto-capture | 's' = manual | 'q' = quit", (10, new_h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
            # Progress bar with stability and ROI enhancement indicator
            if current_keywords >= 0:
                # Show stability progress if working towards green
                if good_readings_count > 0 and not ready_to_capture:
                    progress_width = int((good_readings_count / STABILITY_FRAMES) * 200)
                    progress_color = (0, 255, 255)  # Cyan for stability progress
                    progress_text = f"Stabilizing: {good_readings_count}/{STABILITY_FRAMES} | ROI: {roi_enhancement_level:.1f}x"
                else:
                    # Normal keyword progress
                    progress_width = int((current_keywords / max(keywords_needed, 1)) * 200)
                    
                    # Color based on enhancement level and state
                    if ready_to_capture:
                        progress_color = (0, 255, 0)  # Green when ready
                    elif roi_enhancement_level >= 1.8:
                        progress_color = (0, 100, 255)  # Orange for high enhancement
                    elif roi_enhancement_level >= 1.4:
                        progress_color = (0, 200, 255)  # Yellow for medium enhancement
                    else:
                        progress_color = box_color
                    
                    if ready_to_capture:
                        progress_text = f"READY! Keywords: {current_keywords}/{keywords_needed} | Green Time: {green_time:.1f}s"
                    else:
                        avg_text = f" | Avg: {sum(keyword_history)/len(keyword_history):.1f}" if keyword_history else ""
                        progress_text = f"Keywords: {current_keywords}/{keywords_needed} | ROI: {roi_enhancement_level:.1f}x{avg_text}"
                    
                cv2.rectangle(display_frame, (10, new_h-40), (210, new_h-25), (50, 50, 50), -1)
                cv2.rectangle(display_frame, (10, new_h-40), (10 + progress_width, new_h-25), progress_color, -1)
                cv2.putText(display_frame, progress_text, (10, new_h-45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
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
                # Manual capture with current enhancement level
                if roi_enhancement_level > 1.2:
                    captured_frame = cv2.convertScaleAbs(frame, alpha=roi_enhancement_level, beta=30)
                else:
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

# ============== VERIFICATION FUNCTIONS ==============

def licenseRead(image_path: str, fingerprint_info: dict) -> NameInfo:
    reference_name = fingerprint_info['name']
    current_image_path = image_path
    
    try:
        while True:
            basic_text = extract_text_from_image(current_image_path)
            ocr_lines = [line.strip() for line in basic_text.splitlines() if line.strip()]
            name_from_ocr, sim_score = find_best_line_match(reference_name, ocr_lines)
            
            structured_data = extract_name_from_lines(current_image_path, reference_name, name_from_ocr, sim_score)
            packaged = package_name_info(structured_data, basic_text, fingerprint_info)
            packaged.match_score = sim_score
            
            detected_name = packaged.name
            
            # Check name matching
            exact_match = (detected_name.lower() == reference_name.lower())
            high_similarity = sim_score and sim_score >= 0.65
            
            ref_words = set(reference_name.lower().split())
            det_words = set(detected_name.lower().split())
            word_overlap_ratio = len(ref_words.intersection(det_words)) / len(ref_words) if ref_words else 0
            substantial_overlap = word_overlap_ratio >= 0.7
            
            name_matches = (detected_name != "Not Found" and (exact_match or high_similarity or substantial_overlap))
            
            if name_matches:
                return packaged
            
            if not _retake_prompt(reference_name, detected_name):
                return packaged
            
            if current_image_path != image_path:
                safe_delete_temp_file(current_image_path)
            
            retake_image_path = auto_capture_license_rpi(reference_name, fingerprint_info, retry_mode=True)
            
            if retake_image_path:
                current_image_path = retake_image_path
            else:
                return packaged
        
    except Exception:
        error_packaged = package_name_info(
            {"Name": "Not Found", "Document Verified": "Failed"}, 
            "Processing failed", fingerprint_info
        )
        error_packaged.match_score = 0.0
        return error_packaged
    finally:
        if current_image_path != image_path:
            safe_delete_temp_file(current_image_path)
        safe_delete_temp_file(image_path)

def licenseReadGuest(image_path: str, guest_info: dict) -> NameInfo:
    guest_name = guest_info['name']
    
    try:
        guest_extraction = extract_guest_name_from_license_simple(image_path)
        detected_name = guest_extraction.get('Name', 'Guest User')
        document_status = guest_extraction.get('Document Verified', 'Document Detected')
        
        final_name = guest_name
        
        if detected_name and detected_name != "Guest User" and detected_name != guest_name:
            final_name = guest_name  # Use provided name for consistency
        
        basic_text = _extract_text_smart(image_path, is_guest=True)
        
        packaged = NameInfo(
            document_type="Driver's License",
            name=final_name,
            document_verified=document_status,
            formatted_text=format_text_output(basic_text),
            fingerprint_info=None
        )

        keywords_found = _count_verification_keywords(basic_text.upper())
        is_verified = keywords_found >= 1
        
        if not is_verified and _retake_prompt("Valid License Document", "Insufficient License Keywords"):
            retake_image_path = auto_capture_license_rpi("Guest License", None, retry_mode=True)
            
            if retake_image_path:
                retake_extraction = extract_guest_name_from_license_simple(retake_image_path)
                retake_text = _extract_text_smart(retake_image_path, is_guest=True)
                retake_document_status = retake_extraction.get('Document Verified', 'Document Detected')
                
                retake_packaged = NameInfo(
                    document_type="Driver's License",
                    name=final_name,
                    document_verified=retake_document_status,
                    formatted_text=format_text_output(retake_text),
                    fingerprint_info=None
                )
                
                safe_delete_temp_file(retake_image_path)
                return retake_packaged
        
        return packaged

    except Exception:
        return NameInfo(
            document_type="Driver's License",
            name=guest_name,
            document_verified="Processing Failed",
            formatted_text="Processing failed",
            fingerprint_info=None
        )
    finally:
        safe_delete_temp_file(image_path)

def get_guest_name_from_license_image(image_path: str) -> str:
    try:
        extraction = extract_guest_name_from_license_simple(image_path)
        detected_name = extraction.get('Name', 'Guest')
        return detected_name if detected_name and detected_name != "Guest User" else "Guest"
    except Exception:
        return "Guest"

def _retake_prompt(expected_name: str, detected_name: str) -> bool:
    print(f"⚠️ Name mismatch: Expected '{expected_name}', found '{detected_name}'")
    choice = input("Retake photo? (y/n): ").strip().lower()
    return choice == 'y'

# ============== VERIFICATION FLOWS ==============

def complete_verification_flow(image_path: str, fingerprint_info: dict, 
                             helmet_verified: bool = True, 
                             license_expiration_valid: bool = True) -> bool:
    license_result = licenseRead(image_path, fingerprint_info)
    
    final_name = license_result.name
    final_match_score = license_result.match_score or 0.0
    final_document_status = license_result.document_verified
    
    fingerprint_verified = fingerprint_info['confidence'] > 50
    
    # Check if license is detected (including name match override)
    license_detected = ("Driver's License Detected" in final_document_status or 
                       "Name Match Override" in final_document_status)
    
    name_matching_verified = final_match_score > 0.65
    
    # If names match, force license detection to be true
    if name_matching_verified:
        license_detected = True
        print(f"🎯 Name match override: License detection forced to TRUE")
    
    all_verified = (helmet_verified and fingerprint_verified and 
                   license_expiration_valid and license_detected and 
                   name_matching_verified)
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎯 VERIFICATION RESULTS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🪖 Helmet: {'✅' if helmet_verified else '❌'}")
    print(f"🔒 Fingerprint: {'✅' if fingerprint_verified else '❌'} ({fingerprint_info['confidence']}%)")
    print(f"📅 License Valid: {'✅' if license_expiration_valid else '❌'}")
    print(f"🆔 License Detected: {'✅' if license_detected else '❌'}" + 
          (" (Name Match Override)" if name_matching_verified and license_detected else ""))
    print(f"👤 Name Match: {'✅' if name_matching_verified else '❌'} ({final_match_score*100:.1f}%)")
    print(f"🟢 STATUS: {'✅ FULLY VERIFIED' if all_verified else '❌ VERIFICATION FAILED'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return all_verified

def complete_guest_verification_flow(image_path: str, guest_info: dict,
                                   helmet_verified: bool = True) -> bool:
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
    print(f"🟢 STATUS: {'✅ GUEST VERIFIED' if guest_verified else '❌ GUEST DENIED'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return guest_verified

# ============== UTILITY FUNCTIONS ==============

def print_summary(packaged: NameInfo, fingerprint_info: Optional[dict] = None, structured_data: Optional[Dict[str, str]] = None, 
                 is_guest: bool = False, guest_info: Optional[dict] = None) -> None:
    if structured_data and "Match Confidence" in structured_data:
        print(f"📄 License processed - Name match: {structured_data['Match Confidence']}")

def get_ocr_performance_stats() -> Dict:
    try:
        cache_files = len([f for f in os.listdir(CACHE_DIR) if f.endswith('.txt')])
        return {
            'cache_files': cache_files,
            'cache_directory': CACHE_DIR,
            'status': 'Optimized OCR active'
        }
    except:
        return {'status': 'OCR cache not available'}

def clear_ocr_cache():
    try:
        import shutil
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR)
        print("✅ OCR cache cleared")
    except Exception as e:
        print(f"⚠️ Cache clear failed: {e}")

if __name__ == "__main__":
    print("🚀 Optimized OCR System Ready")
    stats = get_ocr_performance_stats()
    print("📊 Stats:", stats)
