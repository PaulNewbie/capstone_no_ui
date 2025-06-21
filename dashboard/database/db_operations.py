# database/db_operations.py - Updated to use Unified Database

import os
import sqlite3
from datetime import datetime

# Import the new unified database system
from dashboard.database.unified_db import (
    MotorPassDatabase, db,
    initialize_all_databases,
    get_student_by_id,
    get_student_time_status,
    record_time_in,
    record_time_out,
    get_all_time_records,
    clear_all_time_records,
    get_students_currently_in
)

# =================== ENHANCED STUDENT OPERATIONS ===================

def add_student_with_fingerprint(student_id, full_name, course=None, license_number=None, 
                                license_expiration=None, fingerprint_slot=None):
    """Add student with fingerprint slot"""
    return db.add_student(
        student_id=student_id,
        full_name=full_name,
        course=course,
        license_number=license_number,
        license_expiration=license_expiration,
        fingerprint_slot=fingerprint_slot
    )

def get_student_by_fingerprint(fingerprint_slot):
    """Get student by fingerprint slot"""
    return db.get_student(fingerprint_slot=fingerprint_slot)

def update_student_info(student_id, **kwargs):
    """Update student information"""
    return db.update_student(student_id, **kwargs)

def get_all_active_students():
    """Get all active students"""
    return db.get_all_students(active_only=True)

def deactivate_student(student_id):
    """Deactivate student (soft delete)"""
    return db.deactivate_student(student_id)

# =================== ENHANCED ADMIN OPERATIONS ===================

def add_admin_account(username, password, full_name, fingerprint_slot=None):
    """Add admin account with secure password"""
    return db.add_admin(username, password, full_name, fingerprint_slot)

def authenticate_admin_credentials(username, password):
    """Authenticate admin with username/password"""
    return db.authenticate_admin(username, password)

def get_admin_by_fingerprint(fingerprint_slot):
    """Get admin by fingerprint slot"""
    return db.get_admin_by_fingerprint(fingerprint_slot)

# =================== ENHANCED TIME TRACKING ===================

def record_student_time_in(student_info):
    """Record student time in"""
    return db.record_time_action(
        person_id=student_info['student_id'],
        person_name=student_info['name'],
        person_type='STUDENT',
        action='IN'
    )

def record_student_time_out(student_info):
    """Record student time out"""
    return db.record_time_action(
        person_id=student_info['student_id'],
        person_name=student_info['name'],
        person_type='STUDENT',
        action='OUT'
    )

def record_guest_time_in(guest_info):
    """Record guest time in"""
    # Create or update guest record
    guest_id = db.add_or_update_guest(
        full_name=guest_info['name'],
        plate_number=guest_info['plate_number'],
        office_visiting=guest_info.get('office', 'CSS Office'),
        phone_number=guest_info.get('phone', None)
    )
    
    # Record time action
    return db.record_time_action(
        person_id=guest_id,
        person_name=guest_info['name'],
        person_type='GUEST',
        action='IN',
        additional_info=f"Visiting: {guest_info.get('office', 'CSS Office')}"
    )

def record_guest_time_out(guest_info):
    """Record guest time out"""
    guest_id = f"GUEST_{guest_info['plate_number']}"
    
    return db.record_time_action(
        person_id=guest_id,
        person_name=guest_info['name'],
        person_type='GUEST',
        action='OUT'
    )

def record_time_attendance(person_info):
    """Auto record time attendance based on current status"""
    current_status = get_student_time_status(person_info['student_id'])
    
    if current_status == 'OUT' or current_status is None:
        if record_time_in(person_info):
            import time
            return f"🟢 TIME IN recorded for {person_info['name']} at {time.strftime('%H:%M:%S')}"
        else:
            return "❌ Failed to record TIME IN"
    else:
        if record_time_out(person_info):
            import time
            return f"🔴 TIME OUT recorded for {person_info['name']} at {time.strftime('%H:%M:%S')}"
        else:
            return "❌ Failed to record TIME OUT"

# =================== ENHANCED GUEST OPERATIONS ===================

def add_guest(full_name, plate_number, office_visiting, phone_number=None):
    """Add or update guest"""
    return db.add_or_update_guest(full_name, plate_number, office_visiting, phone_number)

def get_guest_by_plate(plate_number):
    """Get guest by plate number"""
    return db.get_guest(plate_number=plate_number)

def get_guest_by_id(guest_id):
    """Get guest by ID"""
    return db.get_guest(guest_id=guest_id)

def find_guest_by_name_similarity(detected_name, min_similarity=0.6):
    """Find guest by name similarity"""
    try:
        from difflib import SequenceMatcher
        import sqlite3
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get all active guests
        cursor.execute("SELECT * FROM guests WHERE is_active = 1")
        guests = cursor.fetchall()
        
        best_match = None
        highest_similarity = 0.0
        
        for guest in guests:
            guest_dict = dict(guest)
            guest_name = guest_dict['full_name']
            
            # Calculate similarity
            similarity = SequenceMatcher(None, detected_name.upper(), guest_name.upper()).ratio()
            
            # Boost for substring matches
            if (detected_name.upper() in guest_name.upper() or 
                guest_name.upper() in detected_name.upper()):
                similarity = max(similarity, 0.8)
            
            if similarity > highest_similarity and similarity >= min_similarity:
                highest_similarity = similarity
                best_match = guest_dict
                best_match['similarity_score'] = similarity
        
        conn.close()
        return best_match
        
    except Exception as e:
        print(f"❌ Error finding guest by similarity: {e}")
        return None

# =================== REPORTING FUNCTIONS ===================

def get_daily_report(target_date=None):
    """Get daily report"""
    return db.generate_daily_report(target_date)

def get_dashboard_summary():
    """Get dashboard summary for admin"""
    return db.get_dashboard_summary()

def get_time_records_filtered(date_from=None, date_to=None, person_type=None, limit=100):
    """Get filtered time records"""
    return db.get_time_records(date_from, date_to, person_type, limit)

def get_people_currently_inside(person_type=None):
    """Get people currently inside"""
    return db.get_people_currently_inside(person_type)

def get_students_in_timeframe(date_from, date_to):
    """Get students who were active in timeframe"""
    records = db.get_time_records(date_from, date_to, 'STUDENT', limit=1000)
    
    # Get unique students
    unique_students = {}
    for record in records:
        student_id = record['person_id']
        if student_id not in unique_students:
            unique_students[student_id] = {
                'student_id': student_id,
                'student_name': record['person_name'],
                'first_activity': record['timestamp'],
                'last_activity': record['timestamp'],
                'total_visits': 1
            }
        else:
            unique_students[student_id]['last_activity'] = record['timestamp']
            unique_students[student_id]['total_visits'] += 1
    
    return list(unique_students.values())

def get_guest_visit_summary():
    """Get guest visit summary"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                full_name,
                plate_number,
                office_visiting,
                total_visits,
                first_visit_date,
                last_visit_date
            FROM guests 
            WHERE is_active = 1
            ORDER BY last_visit_date DESC
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        print(f"❌ Error getting guest summary: {e}")
        return []
    finally:
        conn.close()

# =================== MAINTENANCE FUNCTIONS ===================

def get_database_stats():
    """Get database statistics"""
    stats = db.get_database_stats()
    
    # Add legacy format for compatibility
    legacy_stats = {
        'total_time_records': stats.get('total_time_records', 0),
        'students_currently_in': len([p for p in db.get_people_currently_inside('STUDENT')]),
        'unique_students': stats.get('total_students', 0),
        'unique_guests': stats.get('total_guests', 0),
        'total_students_registered': stats.get('total_students', 0)
    }
    
    return {**stats, **legacy_stats}

def backup_databases(backup_dir="backups"):
    """Create backup of database"""
    import os
    from datetime import datetime
    
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"motorpass_{timestamp}.db")
    
    return db.backup_database(backup_path)

def archive_old_records(days_old=90):
    """Archive old records"""
    return db.archive_old_records(days_old)

def get_archived_records(table_name=None, limit=100):
    """Get archived records"""
    return db.get_archived_records(table_name, limit)

def cleanup_database():
    """Clean up and optimize database"""
    try:
        conn = db.get_connection()
        
        # Run VACUUM to optimize
        conn.execute("VACUUM")
        
        # Update statistics
        conn.execute("ANALYZE")
        
        conn.close()
        print("✅ Database optimized")
        return True
        
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        return False

# =================== MIGRATION HELPERS ===================

def check_migration_needed():
    """Check if migration from old system is needed"""
    old_files = [
        "database/time_tracking.db",
        "database/students.db",
        "json_folder/fingerprint_database.json",
        "json_folder/admin_database.json"
    ]
    
    return any(os.path.exists(f) for f in old_files)

def run_migration():
    """Run migration from old system"""
    try:
        from migrate_to_unified import run_migration
        return run_migration()
    except ImportError:
        print("❌ Migration script not found")
        return False

# =================== LEGACY COMPATIBILITY ===================

# Keep these for backward compatibility with existing code
def init_time_database():
    """Legacy function - redirects to unified system"""
    return initialize_all_databases()

def init_student_database():
    """Legacy function - redirects to unified system"""
    return initialize_all_databases()

def init_guest_database():
    """Legacy function - redirects to unified system"""
    return initialize_all_databases()

def cleanup_guest_data():
    """Legacy function - no longer needed"""
    print("✅ Guest data cleanup not needed in unified system")
    return True

# Print system info when imported
print("🗄️ MotorPass Unified Database System loaded")
if check_migration_needed():
    print("⚠️ Old database files detected - consider running migration")
    print("   Run: python migrate_to_unified.py")
