def init_guest_database():
    """Initialize clean guest database structure"""
    try:
        import sqlite3
        
        # Only use time_tracking.db for all guest operations
        conn = sqlite3.connect("time_tracking.db")
        cursor = conn.cursor()
        
        # Ensure tables exist with correct schema
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
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_student_id ON time_records(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_status ON time_records(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_status_status ON current_status(current_status)')
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize guest database: {e}")
        return False

def cleanup_guest_data():
    """Clean up any orphaned guest data"""
    try:
        import sqlite3
        import os
        
        # Remove old guest_info.db if it exists
        if os.path.exists("guest_info.db"):
            os.remove("guest_info.db")
            print("✅ Removed old guest_info.db")
        
        # Clean up any malformed guest records in time_tracking.db
        conn = sqlite3.connect("time_tracking.db")
        cursor = conn.cursor()
        
        # Remove any guest records with invalid student_id format
        cursor.execute("DELETE FROM time_records WHERE student_id LIKE 'GUEST_%' AND LENGTH(student_id) < 7")
        cursor.execute("DELETE FROM current_status WHERE student_id LIKE 'GUEST_%' AND LENGTH(student_id) < 7")
        
        conn.commit()
        conn.close()
        
        print("✅ Guest data cleanup completed")
        return True
        
    except Exception as e:
        print(f"⚠️ Guest data cleanup warning: {e}")
        return False
