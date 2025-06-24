# config.py - Updated for Students & Staff with Simple Dev Mode

SYSTEM_NAME = "MOTORPASS"
SYSTEM_VERSION = "1.3"  

# =============================================================================
# 🛠️ SIMPLE DEV MODE - Just change True/False
# =============================================================================
ENABLE_BUZZER = True    # Set to False to disable buzzer
ENABLE_LED = True       # Set to False to disable LED

# =============================================================================
# CAMERA CONFIGURATION - RPi Camera 3 Only
# =============================================================================
USE_RPI_CAMERA = True  # Always True - no fallback
RPI_CAMERA_RESOLUTION = (1280, 720)  # HD resolution for RPi Camera 3
RPI_CAMERA_FRAMERATE = 50
RPI_CAMERA_WARMUP_TIME = 1  # seconds

# =============================================================================
# HARDWARE PIN CONFIGURATION
# =============================================================================
HARDWARE_PINS = {
    'LED_RED_PIN': 18,
    'LED_GREEN_PIN': 16,
    'BUZZER_PIN': 22
}

# =============================================================================
# MENU CONFIGURATIONS
# =============================================================================
MAIN_MENU = {
    'title': f"🚗 {SYSTEM_NAME} - VERIFICATION SYSTEM",
    'options': [
        "👨‍💼 1️⃣  ADMIN - Manage System",
        "🎓👔 2️⃣  STUDENT/STAFF - Verify License & Time Tracking", 
        "👤 3️⃣  GUEST - Quick Verification",
        "🚪 4️⃣  EXIT"
    ]
}

ADMIN_MENU = {
    'title': f"🔧 {SYSTEM_NAME} - ADMIN PANEL",
    'options': [
        "1️⃣  Enroll New User (Student/Staff ID + Fingerprint)",
        "2️⃣  View Enrolled Users",
        "3️⃣  Delete User Fingerprint", 
        "4️⃣  Reset All Data",
        "5️⃣  Sync Student/Staff Database",
        "6️⃣  View Time Records",
        "7️⃣  Clear Time Records",
        "8️⃣  Back to Main Menu"
    ]
}
