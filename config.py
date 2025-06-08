SYSTEM_NAME = "MOTORPASS"
SYSTEM_VERSION = "3.3"
WEBCAM_URL = 'http://192.168.100.235:8080/shot.jpg'

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
