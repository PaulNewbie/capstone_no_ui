# license_reader.py - Philippine Driver's License OCR System

import cv2
import numpy as np
import pytesseract
import re
import difflib 
import urllib.request
from typing import Dict, List
from dataclasses import dataclass

# ============== DATA STRUCTURES & CONFIGURATION ==============

VERIFICATION_KEYWORDS = [
    "REPUBLIC", "PHILIPPINES", "DEPARTMENT", "TRANSPORTATION", 
    "LAND TRANSPORTATION OFFICE", "DRIVER'S LICENSE", "DRIVERS LICENSE",
    "LICENSE", "NON-PROFESSIONAL", "PROFESSIONAL", "Last Name", "First Name", 
    "Middle Name", "Nationality", "Date of Birth", "Address", "License No", 
    "Expiration Date"
]

@dataclass
class NameInfo:
    """Data structure for license verification results"""
    document_type: str
    name: str
    document_verified: str
    formatted_text: str
    fingerprint_info: dict = None

# ============== IMAGE PREPROCESSING FUNCTIONS ==============

def preprocess_image(image_path: str) -> np.ndarray:
    """Apply comprehensive image preprocessing for OCR optimization"""
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
    denoised = cv2.fastNlMeansDenoising(opening, None, 10, 7, 21)
    
    return denoised

def enhance_image(image: np.ndarray) -> np.ndarray:
    """Apply sharpening and contrast enhancement"""
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(image, -1, kernel)
    enhanced = cv2.convertScaleAbs(sharpened, alpha=1.5, beta=10)
    return enhanced

def preprocess_batch(image_path: str) -> List[np.ndarray]:
    """Generate multiple preprocessed versions for better OCR accuracy"""
    img = cv2.imread(image_path)
    if img is None:
        raise Exception(f"Could not read image at {image_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed_images = []
    
    # Standard OTSU thresholding
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    processed_images.append(thresh)
    
    # CLAHE enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)
    thresh2 = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    processed_images.append(thresh2)
    
    # Adaptive thresholding with bilateral filter
    bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
    adaptive_thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 11, 2)
    processed_images.append(adaptive_thresh)
    
    return processed_images

# ============== OCR TEXT EXTRACTION ==============

def extract_text_from_image(image_path: str, config: str = '--psm 11 --oem 3') -> str:
    """Extract text from license image using optimized OCR"""
    try:
        img = preprocess_image(image_path)
        enhanced = enhance_image(img)
        return pytesseract.image_to_string(enhanced, config=config)
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def find_best_line_match(input_name: str, ocr_text: List[str]) -> tuple:
    """Find the best matching line in OCR text for the given name"""
    best_match, best_score = None, 0.0

    for line in ocr_text:
        line_clean = line.strip()
        score = difflib.SequenceMatcher(None, input_name.lower(), line_clean.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = line_clean

    return best_match, best_score

def format_text_output(raw_text: str) -> str:
    """Clean and format extracted text for display"""
    lines = raw_text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        sanitized = re.sub(r"[^a-zA-Z0-9\s,\.]", "", line)
        if len(sanitized) >= 3 and any(c.isalpha() for c in sanitized):
            cleaned.append(sanitized)
    return "\n".join(cleaned)


# =========== LICENSE VERIFICATION & NAME EXTRACTION ==========

def extract_name_from_lines(image_path: str, reference_name: str = "", 
                           best_ocr_match: str = "", match_score: float = 0.0) -> Dict[str, str]:
    """Extract and verify name from license using multiple methods"""
    
    # Process image with multiple preprocessing methods
    preprocessed_images = preprocess_batch(image_path)
    best_text = ""
    max_length = 0

    for img in preprocessed_images:
        text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6')
        if len(text) > max_length:
            best_text = text
            max_length = len(text)

    raw_text = best_text if max_length >= 50 else pytesseract.image_to_string(cv2.imread(image_path))
    full_text = " ".join(raw_text.splitlines()).upper()

    # Verify document authenticity
    matched_keywords = {kw for kw in VERIFICATION_KEYWORDS if kw in full_text}
    is_verified = len(matched_keywords) >= 2
    doc_status = "Driver's License Detected" if is_verified else "Unverified Document"

    name_info = {}
    
    # Priority 1: High confidence fingerprint match
    if reference_name and match_score >= 0.6:
        name_info.update({
            "Name": reference_name,
            "Matched From": "Fingerprint Authentication (High Confidence Match)",
            "Match Confidence": f"{match_score * 100:.1f}%",
            "Document Verified": doc_status
        })
        return name_info
    
    # Priority 2: OCR line match
    if best_ocr_match and match_score > 0.4:
        name_info.update({
            "Name": best_ocr_match,
            "Matched From": "Best OCR Line Match",
            "Match Confidence": f"{match_score * 100:.1f}%",
            "Document Verified": doc_status
        })
        return name_info
    
    # Priority 3: Pattern detection fallback
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    for line in lines:
        clean = re.sub(r"[^A-Z\s,.]", "", line.upper()).strip()
        
        if any(header in clean for header in VERIFICATION_KEYWORDS):
            continue
            
        if 4 < len(clean) < 60 and clean.replace(" ", "").isalpha() and " " in clean:
            name_info.update({
                "Name": clean,
                "Matched From": "Pattern Detection",
                "Document Verified": doc_status
            })
            return name_info
    
    # No name found
    name_info.update({
        "Name": "Not Found",
        "Document Verified": doc_status
    })
    return name_info

def package_name_info(structured_data: Dict[str, str], basic_text: str, 
                     fingerprint_info: dict = None) -> NameInfo:
    """Package extracted data into NameInfo structure"""
    return NameInfo(
        document_type="Driver's License",
        name=structured_data.get('Name', 'Not Found'),
        document_verified=structured_data.get('Document Verified', 'Unverified'),
        formatted_text=format_text_output(basic_text),
        fingerprint_info=fingerprint_info
    )

#============== IP WEBCAM INTEGRATION ==============

class IPWebcam:
    """Handle IP webcam connection and frame capture"""
    
    def __init__(self, url: str):
        self.url = url
        self.last_frame = None
        self.connection_stable = True
    
    def get_frame(self):
        """Capture frame from IP webcam with error handling"""
        try:
            img_resp = urllib.request.urlopen(self.url, timeout=5)
            img_np = np.array(bytearray(img_resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_np, -1)
            
            if frame is not None:
                self.last_frame = frame.copy()
                self.connection_stable = True
                return frame
            else:
                self.connection_stable = False
                return self.last_frame if self.last_frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)
                
        except Exception:
            self.connection_stable = False
            return self.last_frame if self.last_frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)

def auto_capture_license_ip(ip_webcam_url: str, output_path="license.jpg", 
                           reference_name="", fingerprint_info=None):
    """Auto-capture license using IP webcam with real-time detection"""
    
    webcam = IPWebcam(ip_webcam_url)
    
    # Test connection
    test_frame = webcam.get_frame()
    if test_frame is None:
        return None
    
    # Display setup
    screen_dims = {'width': 720, 'height': 1280, 'box_width': 600, 'box_height': 350}
    frame_count = 0
    detection_threshold = 2
    consecutive_detections = 0
    
    cv2.namedWindow("MotorPass - License Capture", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("MotorPass - License Capture", screen_dims['width'], 600)
    
    while True:
        frame = webcam.get_frame()
        if frame is None:
            break
        
        # Scale frame for display
        original_h, original_w = frame.shape[:2]
        scale = min(screen_dims['width'] / original_w, 600 / original_h)
        new_w, new_h = int(original_w * scale), int(original_h * scale)
        display_frame = cv2.resize(frame, (new_w, new_h))
        
        # Define detection box
        box_width = min(screen_dims['box_width'], new_w - 40)
        box_height = min(screen_dims['box_height'], new_h - 40)
        center_x, center_y = new_w // 2, new_h // 2
        box_x1 = max(0, center_x - box_width // 2)
        box_y1 = max(0, center_y - box_height // 2)
        box_x2 = min(new_w, center_x + box_width // 2)
        box_y2 = min(new_h, center_y + box_height // 2)
        
        # Extract ROI and detect license
        orig_box_x1, orig_box_y1 = int(box_x1 / scale), int(box_y1 / scale)
        orig_box_x2, orig_box_y2 = int(box_x2 / scale), int(box_y2 / scale)
        roi = frame[orig_box_y1:orig_box_y2, orig_box_x1:orig_box_x2]
        
        # License detection every 10 frames
        frame_count += 1
        if frame_count % 10 == 0 and roi.size > 0:
            try:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                thresh_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                quick_text = pytesseract.image_to_string(thresh_roi, config='--psm 6 --oem 3').upper()
                
                matched_keywords = sum(1 for kw in VERIFICATION_KEYWORDS if kw in quick_text)
                consecutive_detections = consecutive_detections + 1 if matched_keywords >= 2 else 0
                    
            except Exception:
                consecutive_detections = 0
        
        # Draw UI
        box_color = (0, 255, 0) if consecutive_detections > 0 else (0, 0, 255)
        connection_color = (0, 255, 0) if webcam.connection_stable else (0, 0, 255)
        
        cv2.rectangle(display_frame, (box_x1, box_y1), (box_x2, box_y2), box_color, 3)
        
        # Status text
        font_scale, font_thickness = 0.5, 1
        cv2.putText(display_frame, "Connected" if webcam.connection_stable else "Connection Issues", 
                   (10, 25), cv2.FONT_HERSHEY_SIMPLEX, font_scale, connection_color, font_thickness)
        
        if reference_name:
            cv2.putText(display_frame, f"Target: {reference_name}", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), font_thickness)
        
        status_text = f"Detecting... {consecutive_detections}/{detection_threshold}" if consecutive_detections > 0 else "Position license in green box"
        cv2.putText(display_frame, status_text, (10, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0) if consecutive_detections > 0 else (255, 255, 255), font_thickness)
        
        cv2.putText(display_frame, "Press 'q' to quit, 's' to capture", (10, new_h-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale-0.1, (200, 200, 200), 1)
        
        cv2.imshow("MotorPass - License Capture", display_frame)
        
        # Auto capture or manual controls
        if consecutive_detections >= detection_threshold:
            cv2.imwrite(output_path, frame)
            break
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite(output_path, frame)
            break
    
    cv2.destroyAllWindows()
    return output_path if (consecutive_detections >= detection_threshold or key == ord("s")) else None

# ============== MAIN LICENSE READING FUNCTIONS ==============

def licenseRead(image_path: str, fingerprint_info: dict):
    """Process license with fingerprint authentication"""
    reference_name = fingerprint_info['name']

    basic_text = extract_text_from_image(image_path)
    ocr_lines = [line.strip() for line in basic_text.splitlines() if line.strip()]
    name_from_ocr, sim_score = find_best_line_match(reference_name, ocr_lines)

    structured_data = extract_name_from_lines(image_path, reference_name=reference_name, 
                                            best_ocr_match=name_from_ocr, match_score=sim_score)

    packaged = package_name_info(structured_data, basic_text, fingerprint_info)

    # Verification summary
    auth_success = fingerprint_info['confidence'] > 50
    license_match = sim_score > 0.5 if sim_score else False
    overall_status = "VERIFIED" if auth_success and license_match else "PARTIAL VERIFICATION"
    
    print(f"\n===== MOTORPASS VERIFICATION SUMMARY =====")
    print(f"Fingerprint Auth  : {fingerprint_info['name']} (ID: {fingerprint_info['finger_id']})")
    print(f"Document Type     : {packaged.document_type}")
    print(f"Detected Name     : {packaged.name}")
    print(f"Verification      : {packaged.document_verified}")
    if "Match Confidence" in structured_data:
        print(f"Match Confidence  : {structured_data['Match Confidence']}")
    print(f"Overall Status    : {overall_status}")
    print("==========================================\n")

    return packaged
    
def licenseReadGuest(image_path: str, guest_info: dict):
    """Process license for guest verification (no fingerprint required) - IMPROVED VERSION"""
    guest_name = guest_info['name']

    basic_text = extract_text_from_image(image_path)
    full_text = " ".join(basic_text.splitlines()).upper()
    
    # IMPROVED: More flexible document authenticity check
    matched_keywords = {kw for kw in VERIFICATION_KEYWORDS if kw in full_text}
    
    # CHANGED: Reduced threshold from 2 to 1 keyword for guest verification
    # Also check for common license indicators
    license_indicators = [
        "LICENSE", "DRIVER", "REPUBLIC", "PHILIPPINES", 
        "TRANSPORTATION", "EXPIRATION", "DATE OF BIRTH"
    ]
    
    indicator_matches = sum(1 for indicator in license_indicators if indicator in full_text)
    
    # More lenient verification: either 1 verification keyword OR 2 license indicators
    is_verified = len(matched_keywords) >= 1 or indicator_matches >= 2
    
    # Additional check: look for typical license patterns
    has_date_pattern = bool(re.search(r'\d{2}[-/]\d{2}[-/]\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', full_text))
    has_license_number = bool(re.search(r'[A-Z]\d{2}-\d{2}-\d{6}|[A-Z]\d{8}|\d{10}', full_text))
    
    # Final verification decision
    if not is_verified:
        is_verified = has_date_pattern or has_license_number
    
    structured_data = {
        "Name": guest_name,
        "Document Verified": "Driver's License Detected" if is_verified else "Document Detected",  # Changed fallback text
        "Matched From": "Guest Information Provided",
        "Keywords Found": len(matched_keywords),
        "Indicators Found": indicator_matches
    }
    
    packaged = NameInfo(
        document_type="Driver's License",
        name=guest_name,
        document_verified=structured_data["Document Verified"],
        formatted_text=format_text_output(basic_text),
        fingerprint_info=None
    )

    # IMPROVED: More positive guest verification summary
    overall_status = "VERIFIED" if is_verified else "DOCUMENT DETECTED"
    
    print(f"\n===== MOTORPASS GUEST VERIFICATION SUMMARY =====")
    print(f"Guest Name        : {guest_name}")
    print(f"Plate Number      : {guest_info['plate_number']}")
    print(f"Visiting          : {guest_info['office']}")
    print(f"Document Type     : {packaged.document_type}")
    print(f"Verification      : {packaged.document_verified}")
    print(f"Keywords Found    : {len(matched_keywords)}")
    print(f"Indicators Found  : {indicator_matches}")
    print(f"Overall Status    : {overall_status}")
    print("===============================================\n")

    return packaged
