# config.py
SYSTEM_NAME = "MOTORPASS"
SYSTEM_VERSION = "1.2"

# Camera Configuration - RPi Camera 3 Only
USE_RPI_CAMERA = True  # Always True - no fallback
RPI_CAMERA_RESOLUTION = (1280, 720)  # HD resolution for RPi Camera 3
# RPI_CAMERA_RESOLUTION = (640, 780)
RPI_CAMERA_FRAMERATE = 50
RPI_CAMERA_WARMUP_TIME = 1  # seconds

# Camera capture settings
CAPTURE_QUALITY = 65  # JPEG quality (1-100)
CAPTURE_FORMAT = 'JPEG'

MAIN_MENU = {
    'title': f"🚗 {SYSTEM_NAME} - VERIFICATION SYSTEM",
    'options': [
        "👨‍💼 1️⃣  ADMIN - Manage System",
        "🎓 2️⃣  STUDENT - Verify License & Time Tracking", 
        "👤 3️⃣  GUEST - Quick Verification",
        "🚪 4️⃣  EXIT"
    ]
}

ADMIN_MENU = {
    'title': f"🔧 {SYSTEM_NAME} - ADMIN PANEL",
    'options': [
        "1️⃣  Enroll New Student (Student ID + Fingerprint)",
        "2️⃣  View Enrolled Students",
        "3️⃣  Delete Student Fingerprint", 
        "4️⃣  Reset All Data",
        "5️⃣  Sync Student Database",
        "6️⃣  View Time Records",
        "7️⃣  Clear Time Records",
        "8️⃣  Back to Main Menu"
    ]
}
