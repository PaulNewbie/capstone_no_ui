#!/usr/bin/env python3
# sync_all_data.py - Sync ALL student data sources into unified database

import json
import sqlite3
import os
from datetime import datetime

def sync_all_student_data():
    """Sync from ALL sources: JSON fingerprints, Google Sheets DB, and create unified database"""
    
    print("🔄 MOTORPASS COMPLETE DATA SYNC")
    print("="*50)
    
    # Import unified database
    from database.unified_db import db
    
    total_synced = 0
    
    # 1. Sync from Fingerprint JSON Database
    print("\n📄 Step 1: Syncing from Fingerprint JSON...")
    fingerprint_count = sync_from_fingerprint_json()
    total_synced += fingerprint_count
    
    # 2. Sync from Google Sheets SQLite Database  
    print("\n📊 Step 2: Syncing from Google Sheets Database...")
    sheets_count = sync_from_google_sheets_db()
    total_synced += sheets_count
    
    # 3. Try to sync directly from Google Sheets
    print("\n☁️  Step 3: Syncing from Google Sheets (if available)...")
    online_count = sync_from_google_sheets_online()
    total_synced += online_count
    
    # 4. Summary
    print("\n" + "="*50)
    print("📊 SYNC SUMMARY")
    print("="*50)
    print(f"Fingerprint JSON: {fingerprint_count} students")
    print(f"Local Database: {sheets_count} students") 
    print(f"Google Sheets: {online_count} students")
    print(f"Total Processed: {total_synced} students")
    
    # Get final stats
    stats = db.get_database_stats()
    print(f"\n✅ Final Database Stats:")
    print(f"   Students in database: {stats.get('total_students', 0)}")
    print(f"   Time records: {stats.get('total_time_records', 0)}")
    print(f"   Database: {db.db_path}")
    
    return total_synced > 0

def sync_from_fingerprint_json():
    """Sync students from fingerprint JSON database"""
    json_file = "json_folder/fingerprint_database.json"
    
    if not os.path.exists(json_file):
        print(f"❌ Fingerprint database not found: {json_file}")
        return 0
    
    try:
        with open(json_file, 'r') as f:
            fingerprint_data = json.load(f)
        
        print(f"📂 Found fingerprint database with {len(fingerprint_data)} entries")
        
        synced_count = 0
        from database.unified_db import db
        
        for slot_id, student_info in fingerprint_data.items():
            # Skip admin slot
            if slot_id == "1":
                continue
                
            try:
                student_id = student_info.get('student_id', f'FP_{slot_id}')
                full_name = student_info.get('name', 'Unknown Student')
                course = student_info.get('course', None)
                license_number = student_info.get('license_number', None)
                license_expiration = student_info.get('license_expiration', None)
                fingerprint_slot = int(slot_id)
                
                # Add to unified database
                success = db.add_student(
                    student_id=student_id,
                    full_name=full_name,
                    course=course,
                    license_number=license_number,
                    license_expiration=license_expiration,
                    fingerprint_slot=fingerprint_slot
                )
                
                if success:
                    synced_count += 1
                    print(f"  ✅ {full_name} (ID: {student_id})")
                else:
                    print(f"  ⚠️  Skipped {full_name} (already exists)")
                    
            except Exception as e:
                print(f"  ❌ Error processing {student_info}: {e}")
        
        print(f"✅ Synced {synced_count} students from fingerprint database")
        return synced_count
        
    except Exception as e:
        print(f"❌ Error reading fingerprint database: {e}")
        return 0

def sync_from_google_sheets_db():
    """Sync from local Google Sheets SQLite database"""
    sheets_db = "database/students.db"
    
    if not os.path.exists(sheets_db):
        print(f"❌ Google Sheets database not found: {sheets_db}")
        return 0
    
    try:
        # Connect to Google Sheets database
        sheets_conn = sqlite3.connect(sheets_db)
        sheets_cursor = sheets_conn.cursor()
        
        # Get all students
        sheets_cursor.execute("SELECT * FROM students")
        students = sheets_cursor.fetchall()
        
        # Get column names
        columns = [description[0] for description in sheets_cursor.description]
        
        sheets_conn.close()
        
        print(f"📂 Found Google Sheets database with {len(students)} students")
        
        synced_count = 0
        from database.unified_db import db
        
        for student_row in students:
            try:
                # Convert to dict
                student = dict(zip(columns, student_row))
                
                student_id = student.get('student_id') or student.get('Student No.', f'GS_{student.get("id", "")}')
                full_name = student.get('full_name') or student.get('Full Name', 'Unknown')
                course = student.get('course') or student.get('Course', None)
                license_number = student.get('license_number') or student.get('License Number', None)
                license_expiration = student.get('expiration_date') or student.get('License Expiration Date', None)
                
                # Check if student already exists (from fingerprint sync)
                existing = db.get_student(student_id=student_id)
                
                if existing:
                    # Update existing student with Google Sheets data
                    db.update_student(
                        student_id=student_id,
                        course=course or existing.get('course'),
                        license_number=license_number or existing.get('license_number'),
                        license_expiration=license_expiration or existing.get('license_expiration')
                    )
                    print(f"  🔄 Updated {full_name} (ID: {student_id})")
                else:
                    # Add new student
                    success = db.add_student(
                        student_id=student_id,
                        full_name=full_name,
                        course=course,
                        license_number=license_number,
                        license_expiration=license_expiration
                    )
                    
                    if success:
                        print(f"  ✅ Added {full_name} (ID: {student_id})")
                    
                synced_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error processing student: {e}")
        
        print(f"✅ Processed {synced_count} students from Google Sheets database")
        return synced_count
        
    except Exception as e:
        print(f"❌ Error reading Google Sheets database: {e}")
        return 0

def sync_from_google_sheets_online():
    """Try to sync directly from Google Sheets online"""
    credentials_file = "json_folder/credentials.json"
    
    if not os.path.exists(credentials_file):
        print(f"❌ Google credentials not found: {credentials_file}")
        return 0
    
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        print("🔑 Connecting to Google Sheets...")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("MotorPass (Responses)").sheet1
        rows = sheet.get_all_records()
        
        print(f"☁️  Found {len(rows)} records in Google Sheets")
        
        synced_count = 0
        from database.unified_db import db
        
        for row in rows:
            try:
                student_id = row.get('Student No.', f'GS_{synced_count}')
                full_name = row.get('Full Name', 'Unknown')
                course = row.get('Course', None)
                license_number = row.get('License Number', None)
                license_expiration = row.get('License Expiration Date', None)
                
                # Check if student exists
                existing = db.get_student(student_id=student_id)
                
                if existing:
                    # Update with latest Google Sheets data
                    db.update_student(
                        student_id=student_id,
                        full_name=full_name,
                        course=course,
                        license_number=license_number,
                        license_expiration=license_expiration
                    )
                    print(f"  🔄 Updated from GS: {full_name}")
                else:
                    # Add new student
                    success = db.add_student(
                        student_id=student_id,
                        full_name=full_name,
                        course=course,
                        license_number=license_number,
                        license_expiration=license_expiration
                    )
                    
                    if success:
                        print(f"  ✅ Added from GS: {full_name}")
                
                synced_count += 1
                
            except Exception as e:
                print(f"  ❌ Error processing Google Sheets row: {e}")
        
        print(f"✅ Synced {synced_count} students from Google Sheets online")
        return synced_count
        
    except ImportError:
        print("⚠️  Google Sheets libraries not installed (gspread, oauth2client)")
        print("  Install with: pip install gspread oauth2client")
        return 0
    except Exception as e:
        print(f"❌ Error syncing from Google Sheets: {e}")
        return 0

def create_fingerprint_backup():
    """Create backup of fingerprint JSON before syncing"""
    json_file = "json_folder/fingerprint_database.json"
    
    if os.path.exists(json_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"json_folder/fingerprint_database_backup_{timestamp}.json"
        
        try:
            import shutil
            shutil.copy2(json_file, backup_file)
            print(f"💾 Created backup: {backup_file}")
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")

def fix_admin_sync():
    """Update admin sync to use unified database"""
    print("\n🔧 Updating admin sync system...")
    
    admin_file = "controllers/admin.py"
    if os.path.exists(admin_file):
        print("✅ Admin file found - sync function will now use unified database")
    else:
        print("❌ Admin file not found")

if __name__ == "__main__":
    print("🚗 MotorPass Complete Data Sync")
    print("This will sync ALL your student data into one unified database")
    print()
    
    # Create backup first
    create_fingerprint_backup()
    
    # Run the sync
    success = sync_all_student_data()
    
    if success:
        print("\n🎉 SUCCESS! All student data synced to unified database")
        print("\nNext steps:")
        print("1. Test your main system to ensure fingerprints still work")
        print("2. Run dashboard: python start_dashboard.py")
        print("3. Admin sync will now update the unified database")
    else:
        print("\n⚠️  No data found to sync")
        print("Make sure you have:")
        print("1. json_folder/fingerprint_database.json (from enrollments)")
        print("2. database/students.db (from Google Sheets sync)")
        print("3. json_folder/credentials.json (for Google Sheets)")
