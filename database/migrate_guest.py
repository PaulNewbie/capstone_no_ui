# database/migrate_to_motorpass.py - Migrate from existing database structure

import sqlite3
import os
from datetime import datetime
import shutil

# Database paths
OLD_TIME_DB = "database/time_tracking.db"
OLD_STUDENT_DB = "database/students.db"
NEW_MOTORPASS_DB = "database/motorpass.db"

def check_existing_databases():
    """Check what databases currently exist"""
    print("🔍 Checking existing databases...")
    
    databases_found = []
    
    if os.path.exists(OLD_TIME_DB):
        databases_found.append(f"✅ Found: {OLD_TIME_DB}")
    else:
        databases_found.append(f"❌ Missing: {OLD_TIME_DB}")
    
    if os.path.exists(OLD_STUDENT_DB):
        databases_found.append(f"✅ Found: {OLD_STUDENT_DB}")
    else:
        databases_found.append(f"❌ Missing: {OLD_STUDENT_DB}")
    
    if os.path.exists(NEW_MOTORPASS_DB):
        databases_found.append(f"⚠️  Already exists: {NEW_MOTORPASS_DB}")
    else:
        databases_found.append(f"📝 Will create: {NEW_MOTORPASS_DB}")
    
    for db in databases_found:
        print(f"   {db}")
    
    return os.path.exists(OLD_TIME_DB) or os.path.exists(OLD_STUDENT_DB)

def backup_existing_databases():
    """Create backups of existing databases"""
    print("\n💾 Creating backups...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"database/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    backups_created = []
    
    if os.path.exists(OLD_TIME_DB):
        backup_path = os.path.join(backup_dir, "time_tracking.db")
        shutil.copy2(OLD_TIME_DB, backup_path)
        backups_created.append(backup_path)
        print(f"   ✅ Backed up: {backup_path}")
    
    if os.path.exists(OLD_STUDENT_DB):
        backup_path = os.path.join(backup_dir, "students.db")
        shutil.copy2(OLD_STUDENT_DB, backup_path)
        backups_created.append(backup_path)
        print(f"   ✅ Backed up: {backup_path}")
    
    if os.path.exists(NEW_MOTORPASS_DB):
        backup_path = os.path.join(backup_dir, "motorpass.db")
        shutil.copy2(NEW_MOTORPASS_DB, backup_path)
        backups_created.append(backup_path)
        print(f"   ✅ Backed up: {backup_path}")
    
    return len(backups_created) > 0

def create_new_database_schema():
    """Create the new centralized database schema"""
    print("\n🏗️  Creating new database schema...")
    
    try:
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(NEW_MOTORPASS_DB)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Create students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                course TEXT NOT NULL,
                license_number TEXT,
                license_expiration DATE,
                plate_number TEXT,
                fingerprint_slot INTEGER UNIQUE,
                enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create staff table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                staff_no TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                staff_role TEXT NOT NULL,
                license_number TEXT,
                license_expiration DATE,
                plate_number TEXT,
                fingerprint_slot INTEGER UNIQUE,
                enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create guests table (simplified - no course, license fields)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                plate_number TEXT NOT NULL,
                office_visiting TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create unified time tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('STUDENT', 'STAFF', 'GUEST')),
                action TEXT NOT NULL CHECK(action IN ('IN', 'OUT')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date DATE NOT NULL,
                time TIME NOT NULL
            )
        ''')
        
        # Create current status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS current_status (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('STUDENT', 'STAFF', 'GUEST')),
                status TEXT NOT NULL CHECK(status IN ('IN', 'OUT')),
                last_action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_name ON students(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_staff_name ON staff(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guests_name ON guests(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guests_plate ON guests(plate_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_user ON time_tracking(user_id, user_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_date ON time_tracking(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_status_type ON current_status(user_type)')
        
        conn.commit()
        conn.close()
        
        print("   ✅ Database schema created successfully")
        return True
        
    except sqlite3.Error as e:
        print(f"   ❌ Error creating schema: {e}")
        return False

def migrate_students_data():
    """Migrate student data from old database"""
    if not os.path.exists(OLD_STUDENT_DB):
        print("\n⏭️  No students database found, skipping student migration")
        return True
    
    print("\n👥 Migrating students data...")
    
    try:
        # Connect to old database
        old_conn = sqlite3.connect(OLD_STUDENT_DB)
        old_cursor = old_conn.cursor()
        
        # Connect to new database
        new_conn = sqlite3.connect(NEW_MOTORPASS_DB)
        new_cursor = new_conn.cursor()
        
        # Get students data
        old_cursor.execute('SELECT * FROM students')
        students = old_cursor.fetchall()
        
        # Get column info to understand structure
        old_cursor.execute('PRAGMA table_info(students)')
        columns_info = old_cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        print(f"   📋 Found {len(students)} student records")
        print(f"   📋 Old database columns: {column_names}")
        
        migrated_count = 0
        for student in students:
            try:
                # Map old structure to new - adjust based on your actual structure
                if len(student) >= 8:  # Adjust based on your column count
                    # Assuming structure: full_name, license_number, expiration, plate, course, student_id, staff_role, staff_no, user_type
                    if student[8] == 'STUDENT':  # user_type
                        new_cursor.execute('''
                            INSERT OR REPLACE INTO students 
                            (student_id, full_name, course, license_number, license_expiration, plate_number)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            student[5],  # student_id
                            student[0],  # full_name
                            student[4],  # course
                            student[1],  # license_number
                            student[2],  # license_expiration
                            student[3]   # plate_number
                        ))
                        migrated_count += 1
                    elif student[8] == 'STAFF':  # user_type
                        new_cursor.execute('''
                            INSERT OR REPLACE INTO staff 
                            (staff_no, full_name, staff_role, license_number, license_expiration, plate_number)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            student[7],  # staff_no
                            student[0],  # full_name
                            student[6],  # staff_role
                            student[1],  # license_number
                            student[2],  # license_expiration
                            student[3]   # plate_number
                        ))
                        migrated_count += 1
            except Exception as e:
                print(f"   ⚠️  Error migrating student record: {e}")
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"   ✅ Migrated {migrated_count} student/staff records")
        return True
        
    except Exception as e:
        print(f"   ❌ Error migrating students: {e}")
        return False

def migrate_time_tracking_data():
    """Migrate time tracking data from old database"""
    if not os.path.exists(OLD_TIME_DB):
        print("\n⏭️  No time tracking database found, skipping time migration")
        return True
    
    print("\n⏰ Migrating time tracking data...")
    
    try:
        # Connect to old database
        old_conn = sqlite3.connect(OLD_TIME_DB)
        old_cursor = old_conn.cursor()
        
        # Connect to new database
        new_conn = sqlite3.connect(NEW_MOTORPASS_DB)
        new_cursor = new_conn.cursor()
        
        # Get time records
        old_cursor.execute('SELECT * FROM time_records ORDER BY date DESC, time DESC')
        time_records = old_cursor.fetchall()
        
        print(f"   📋 Found {len(time_records)} time records")
        
        migrated_count = 0
        current_status = {}  # Track current status for each user
        
        for record in reversed(time_records):  # Process oldest first
            try:
                # Assuming structure: student_id, student_name, course, date, time, status, license_number, timestamp
                user_id = record[0]
                user_name = record[1]
                date = record[3]
                time = record[4]
                status = record[5]
                
                # Determine user type
                if user_id.startswith('GUEST_'):
                    user_type = 'GUEST'
                elif user_id.startswith('STAFF_') or user_id.startswith('STF'):
                    user_type = 'STAFF'
                else:
                    user_type = 'STUDENT'
                
                # Insert into new time_tracking table
                new_cursor.execute('''
                    INSERT INTO time_tracking 
                    (user_id, user_name, user_type, action, date, time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, user_name, user_type, status, date, time))
                
                # Track current status (last action wins)
                current_status[user_id] = {
                    'user_name': user_name,
                    'user_type': user_type,
                    'status': status
                }
                
                migrated_count += 1
                
            except Exception as e:
                print(f"   ⚠️  Error migrating time record: {e}")
        
        # Insert current status
        for user_id, status_info in current_status.items():
            new_cursor.execute('''
                INSERT OR REPLACE INTO current_status 
                (user_id, user_name, user_type, status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, status_info['user_name'], status_info['user_type'], status_info['status']))
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"   ✅ Migrated {migrated_count} time records")
        print(f"   ✅ Set current status for {len(current_status)} users")
        return True
        
    except Exception as e:
        print(f"   ❌ Error migrating time tracking: {e}")
        return False

def extract_guest_data_from_time_records():
    """Extract unique guest data from time records to populate guests table"""
    print("\n🎫 Extracting guest data...")
    
    try:
        conn = sqlite3.connect(NEW_MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Get unique guest records from time_tracking
        cursor.execute('''
            SELECT DISTINCT user_id, user_name
            FROM time_tracking 
            WHERE user_type = 'GUEST'
        ''')
        
        guest_records = cursor.fetchall()
        print(f"   📋 Found {len(guest_records)} unique guests")
        
        migrated_guests = 0
        for guest_record in guest_records:
            user_id = guest_record[0]  # GUEST_PLATENUM format
            user_name = guest_record[1]
            plate_number = user_id.replace('GUEST_', '')
            
            # Insert into guests table
            cursor.execute('''
                INSERT OR IGNORE INTO guests 
                (full_name, plate_number, office_visiting)
                VALUES (?, ?, ?)
            ''', (user_name, plate_number, 'Previous Visit'))
            
            migrated_guests += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Created {migrated_guests} guest records")
        return True
        
    except Exception as e:
        print(f"   ❌ Error extracting guest data: {e}")
        return False

def verify_migration():
    """Verify the migration was successful"""
    print("\n✅ Verifying migration...")
    
    try:
        conn = sqlite3.connect(NEW_MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Count records in each table
        cursor.execute('SELECT COUNT(*) FROM students')
        student_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM staff')
        staff_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM guests')
        guest_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM time_tracking')
        time_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM current_status')
        status_count = cursor.fetchone()[0]
        
        print(f"   👥 Students: {student_count}")
        print(f"   👔 Staff: {staff_count}")
        print(f"   🎫 Guests: {guest_count}")
        print(f"   ⏰ Time records: {time_count}")
        print(f"   📊 Current status: {status_count}")
        
        # Show sample data
        if guest_count > 0:
            cursor.execute('SELECT plate_number, full_name, office_visiting FROM guests LIMIT 3')
            sample_guests = cursor.fetchall()
            print(f"\n   📋 Sample guests:")
            for guest in sample_guests:
                print(f"      Guest No: {guest[0]}, Name: {guest[1]}, Office: {guest[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

def main():
    """Run the complete migration process"""
    print("🚀 MotorPass Database Migration")
    print("=" * 50)
    print("Migrating from old database structure to new centralized database")
    
    # Step 1: Check existing databases
    if not check_existing_databases():
        print("\n❌ No existing databases found to migrate from.")
        print("If this is a fresh install, just run your system to create the new database.")
        return False
    
    # Step 2: Create backups
    print("\n" + "="*50)
    if not backup_existing_databases():
        print("❌ Failed to create backups")
        return False
    
    # Step 3: Create new database schema
    print("\n" + "="*50)
    if not create_new_database_schema():
        print("❌ Failed to create new database schema")
        return False
    
    # Step 4: Migrate students/staff data
    print("\n" + "="*50)
    if not migrate_students_data():
        print("❌ Failed to migrate students data")
        return False
    
    # Step 5: Migrate time tracking data
    print("\n" + "="*50)
    if not migrate_time_tracking_data():
        print("❌ Failed to migrate time tracking data")
        return False
    
    # Step 6: Extract guest data
    print("\n" + "="*50)
    if not extract_guest_data_from_time_records():
        print("❌ Failed to extract guest data")
        return False
    
    # Step 7: Verify migration
    print("\n" + "="*50)
    if not verify_migration():
        print("❌ Migration verification failed")
        return False
    
    print("\n" + "="*50)
    print("🎉 Migration completed successfully!")
    print("\nNext steps:")
    print("1. Update your code to use the new database structure")
    print("2. Test the guest registration and time tracking")
    print("3. Your old databases are backed up in case you need to rollback")
    
    return True

if __name__ == "__main__":
    main()
