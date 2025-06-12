# services/time_tracker.py

import sqlite3
from datetime import datetime

def get_student_time_status(student_id):
    """
    Returns the most recent time status ('IN' or 'OUT') for a given student_id.
    """
    try:
        conn = sqlite3.connect("database/time_tracking.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status FROM time_records
            WHERE student_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (student_id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None
    except Exception as e:
        print(f"❌ Error fetching time status: {e}")
        return None

def record_time_in(student_info):
    """
    Logs a time IN record for the given student.
    """
    try:
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        conn = sqlite3.connect("database/time_tracking.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO time_records (student_id, student_name, date, time, status)
            VALUES (?, ?, ?, ?, ?)
        """, (student_info['student_id'], student_info['name'], date, time, 'IN'))
        conn.commit()
        conn.close()
        print("🟢 Time IN recorded successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to record time IN: {e}")
        return False
        

def record_time_out(student_info):
    """
    Logs a time OUT record for the given student.
    """
    try:
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        conn = sqlite3.connect("database/time_tracking.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO time_records (student_id, student_name, date, time, status)
            VALUES (?, ?, ?, ?, ?)
        """, (student_info['student_id'], student_info['name'], date, time, 'OUT'))
        conn.commit()
        conn.close()
        print("🔴 Time OUT recorded successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to record time OUT: {e}")
        return False
