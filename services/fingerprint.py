# services/fingerprint.py - Cleaned Fingerprint Service

import time
import serial
import adafruit_fingerprint
import json
import os
import sqlite3
import tkinter as tk
from tkinter import simpledialog, messagebox

# =================== SETUP ===================
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# File paths
FINGERPRINT_DATA_FILE = "json_folder/fingerprint_database.json"
STUDENT_DB_FILE = "database/students.db"
TIME_TRACKING_DB = "database/time_tracking.db"

# =================== DATABASE FUNCTIONS ===================

def load_fingerprint_database():
    """Load fingerprint database"""
    if os.path.exists(FINGERPRINT_DATA_FILE):
        try:
            with open(FINGERPRINT_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_fingerprint_database(database):
    """Save fingerprint database"""
    with open(FINGERPRINT_DATA_FILE, 'w') as f:
        json.dump(database, f, indent=4)

def get_student_by_id(student_id):
    """Fetch student info by ID"""
    try:
        conn = sqlite3.connect(STUDENT_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT full_name, license_number, expiration_date, course, student_id 
            FROM students 
            WHERE student_id = ?
        ''', (student_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'full_name': result[0],
                'license_number': result[1],
                'expiration_date': result[2],
                'course': result[3],
                'student_id': result[4]
            }
        return None
        
    except sqlite3.Error:
        return None

# =================== TIME TRACKING ===================

def init_time_database():
    """Initialize time tracking database"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS current_status (
                student_id TEXT PRIMARY KEY,
                student_name TEXT NOT NULL,
                current_status TEXT NOT NULL,
                last_update DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

def get_student_time_status(student_id):
    """Get current time status (IN/OUT)"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT current_status FROM current_status WHERE student_id = ?', (student_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'OUT'
        
    except sqlite3.Error:
        return 'OUT'

def record_time_in(student_info):
    """Record student time in"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        current_date = time.strftime('%Y-%m-%d')
        current_time = time.strftime('%H:%M:%S')
        
        cursor.execute('''
            INSERT INTO time_records (student_id, student_name, date, time, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_info['student_id'], student_info['name'], current_date, current_time, 'IN'))
        
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (student_id, student_name, current_status)
            VALUES (?, ?, ?)
        ''', (student_info['student_id'], student_info['name'], 'IN'))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error:
        return False

def record_time_out(student_info):
    """Record student time out"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        current_date = time.strftime('%Y-%m-%d')
        current_time = time.strftime('%H:%M:%S')
        
        cursor.execute('''
            INSERT INTO time_records (student_id, student_name, date, time, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_info['student_id'], student_info['name'], current_date, current_time, 'OUT'))
        
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (student_id, student_name, current_status)
            VALUES (?, ?, ?)
        ''', (student_info['student_id'], student_info['name'], 'OUT'))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error:
        return False

def record_time_attendance(student_info):
    """Auto record time attendance based on current status"""
    current_status = get_student_time_status(student_info['student_id'])
    
    if current_status == 'OUT' or current_status is None:
        if record_time_in(student_info):
            return f"🟢 TIME IN recorded for {student_info['name']} at {time.strftime('%H:%M:%S')}"
        else:
            return "❌ Failed to record TIME IN"
    else:
        if record_time_out(student_info):
            return f"🔴 TIME OUT recorded for {student_info['name']} at {time.strftime('%H:%M:%S')}"
        else:
            return "❌ Failed to record TIME OUT"

def get_all_time_records():
    """Get all time records"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, student_name, date, time, status, timestamp
            FROM time_records
            ORDER BY timestamp DESC
        ''')
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'student_id': row[0],
                'student_name': row[1],
                'date': row[2],
                'time': row[3],
                'status': row[4],
                'timestamp': row[5]
            })
        
        conn.close()
        return records
        
    except sqlite3.Error:
        return []

def clear_all_time_records():
    """Clear all time records"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM time_records')
        cursor.execute('DELETE FROM current_status')
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error:
        return False

def get_students_currently_in():
    """Get students currently timed in"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, student_name, last_update
            FROM current_status
            WHERE current_status = 'IN'
            ORDER BY last_update DESC
        ''')
        
        students = []
        for row in cursor.fetchall():
            students.append({
                'student_id': row[0],
                'student_name': row[1],
                'time_in': row[2]
            })
        
        conn.close()
        return students
        
    except sqlite3.Error:
        return []

# =================== GUI FUNCTIONS ===================

def get_student_id_gui():
    """Get student ID via GUI and fetch info"""
    root = tk.Tk()
    root.withdraw()
    
    while True:
        student_id = simpledialog.askstring("Student Enrollment", "Enter Student Number:")
        
        if not student_id:
            root.destroy()
            return None
        
        student_id = student_id.strip()
        student_info = get_student_by_id(student_id)
        
        if student_info:
            confirmation_message = f"""
Student Information Found:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {student_info['full_name']}
🆔 Student No.: {student_info['student_id']}
📚 Course: {student_info['course']}
🪪 License No.: {student_info['license_number']}
📅 License Exp.: {student_info['expiration_date']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Proceed with fingerprint enrollment?
            """
            
            if messagebox.askyesno("Confirm Student Information", confirmation_message):
                root.destroy()
                return student_info
        else:
            if not messagebox.askyesno("Student Not Found", 
                f"Student ID '{student_id}' not found.\n\nTry again?"):
                root.destroy()
                return None

def show_message_gui(title, message):
    """Show message dialog"""
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()

def display_student_info(student_info):
    """Display student info in console"""
    print(f"\n{'='*50}")
    print("📋 STUDENT INFORMATION")
    print(f"{'='*50}")
    print(f"👤 Name: {student_info['full_name']}")
    print(f"🆔 Student No.: {student_info['student_id']}")
    print(f"📚 Course: {student_info['course']}")
    print(f"🪪 License: {student_info['license_number']}")
    print(f"📅 Expiration: {student_info['expiration_date']}")
    print(f"{'='*50}")

# =================== FINGERPRINT FUNCTIONS ===================

def enroll_finger_with_student_info(location):
    """Enhanced enrollment using Student ID"""
    print(f"\n🔒 Starting enrollment for slot #{location}")
    
    student_info = get_student_id_gui()
    if not student_info:
        print("❌ No student selected.")
        return False
    
    display_student_info(student_info)
    print(f"👤 Enrolling: {student_info['full_name']}")
    
    # Fingerprint enrollment process
    for fingerimg in range(1, 3):
        print(f"👆 Place finger {'(first time)' if fingerimg == 1 else '(again)'}...", end="")

        while finger.get_image() != adafruit_fingerprint.OK:
            print(".", end="")
        print("✅")

        print("🔄 Processing...", end="")
        if finger.image_2_tz(fingerimg) != adafruit_fingerprint.OK:
            print("❌ Failed")
            return False
        print("✅")

        if fingerimg == 1:
            print("✋ Remove finger")
            time.sleep(1)
            while finger.get_image() != adafruit_fingerprint.NOFINGER:
                pass

    print("🗝️ Creating model...", end="")
    if finger.create_model() != adafruit_fingerprint.OK:
        print("❌ Failed")
        return False
    print("✅")

    print(f"💾 Storing model #{location}...", end="")
    if finger.store_model(location) == adafruit_fingerprint.OK:
        print("✅")
        
        # Save student info
        database = load_fingerprint_database()
        database[str(location)] = {
            "name": student_info['full_name'],
            "student_id": student_info['student_id'],
            "course": student_info['course'],
            "license_number": student_info['license_number'],
            "license_expiration": student_info['expiration_date'],
            "enrolled_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_fingerprint_database(database)
        
        print(f"🎉 Successfully enrolled {student_info['full_name']} at slot #{location}")
        
        success_message = f"""
Enrollment Successful! ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Student: {student_info['full_name']}
🆔 Student No.: {student_info['student_id']}
📚 Course: {student_info['course']}
🪪 License: {student_info['license_number']}
🔒 Fingerprint Slot: #{location}
📅 Enrolled: {time.strftime("%Y-%m-%d %H:%M:%S")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        show_message_gui("Enrollment Complete", success_message)
        return True
    else:
        print("❌ Storage failed")
        return False

def authenticate_fingerprint():
    """Authenticate fingerprint and return student info"""
    print("\n🔒 Place finger on sensor...")
    
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    
    print("🔄 Processing...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("❌ Failed to process")
        return None
    
    print("🔍 Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        print("❌ No match found")
        return None
    
    database = load_fingerprint_database()
    finger_id = str(finger.finger_id)
    
    if finger_id in database:
        student_info = database[finger_id]
        print(f"✅ Authentication successful!")
        print(f"👤 Welcome: {student_info['name']}")
        print(f"🆔 ID: {student_info.get('student_id', 'N/A')}")
        print(f"📚 Course: {student_info.get('course', 'N/A')}")
        print(f"🎯 Confidence: {finger.confidence}")
        
        return {
            "name": student_info['name'],
            "student_id": student_info.get('student_id', 'N/A'),
            "course": student_info.get('course', 'N/A'),
            "license_number": student_info.get('license_number', 'N/A'),
            "license_expiration": student_info.get('license_expiration', 'N/A'),
            "finger_id": finger.finger_id,
            "confidence": finger.confidence,
            "enrolled_date": student_info.get('enrolled_date', 'Unknown')
        }
    else:
        print(f"⚠️ Fingerprint recognized (ID: {finger.finger_id}) but no student data found")
        return {
            "name": f"Unknown User (ID: {finger.finger_id})",
            "student_id": "N/A",
            "course": "N/A",
            "license_number": "N/A",
            "license_expiration": "N/A",
            "finger_id": finger.finger_id,
            "confidence": finger.confidence,
            "enrolled_date": "Unknown"
        }

def authenticate_fingerprint_with_time_tracking():
    """Authenticate fingerprint and auto handle time in/out"""
    student_info = authenticate_fingerprint()
    
    if not student_info or student_info['student_id'] == 'N/A':
        return student_info
    
    time_status = record_time_attendance(student_info)
    print(f"🕒 {time_status}")
    
    return student_info

# =================== LEGACY SUPPORT ===================
def enroll_finger_with_name(location):
    """Legacy function - redirects to new enrollment"""
    print("⚠️ Using legacy enrollment. Consider using enroll_finger_with_student_info().")
    return enroll_finger_with_student_info(location)
