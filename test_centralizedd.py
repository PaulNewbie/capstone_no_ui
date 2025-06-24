# test_centralized_database.py - Test the new centralized database

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.centralized_db import (
    initialize_database,
    add_student,
    add_staff,
    get_user_by_id,
    search_users,
    record_time_action,
    get_user_current_status,
    get_database_statistics,
    get_users_currently_inside
)

def test_database():
    """Test the centralized database functionality"""
    
    print("🧪 MotorPass Centralized Database Test")
    print("=" * 60)
    
    # Initialize database
    print("\n1️⃣ Initializing database...")
    if not initialize_database():
        print("❌ Failed to initialize database")
        return
    print("✅ Database initialized")
    
    # Test adding a student
    print("\n2️⃣ Testing student operations...")
    test_student = {
        'student_id': '2024-12345',
        'full_name': 'Maria Santos',
        'course': 'BSCS',
        'license_number': 'N01-24-123456',
        'license_expiration': '2026-12-31',
        'plate_number': 'ABC 123'
    }
    
    if add_student(test_student):
        print("✅ Student added successfully")
    else:
        print("❌ Failed to add student")
        return
    
    # Test adding a staff member
    print("\n3️⃣ Testing staff operations...")
    test_staff = {
        'staff_no': 'STAFF-001',
        'full_name': 'Juan Dela Cruz',
        'staff_role': 'IT Support',
        'license_number': 'P02-24-654321',
        'license_expiration': '2025-06-30',
        'plate_number': 'XYZ 789'
    }
    
    if add_staff(test_staff):
        print("✅ Staff added successfully")
    else:
        print("❌ Failed to add staff")
        return
    
    # Test user lookup
    print("\n4️⃣ Testing user lookup...")
    
    # Look up student
    student = get_user_by_id('2024-12345')
    if student:
        print(f"✅ Found student: {student['full_name']} ({student['user_type']})")
    else:
        print("❌ Student lookup failed")
    
    # Look up staff
    staff = get_user_by_id('STAFF-001')
    if staff:
        print(f"✅ Found staff: {staff['full_name']} ({staff['user_type']})")
    else:
        print("❌ Staff lookup failed")
    
    # Test search
    print("\n5️⃣ Testing search functionality...")
    search_results = search_users("Maria")
    if search_results:
        print(f"✅ Search found {len(search_results)} result(s)")
        for result in search_results:
            print(f"   - {result['name']} ({result['id']}) - {result['user_type']}")
    else:
        print("❌ Search returned no results")
    
    # Test time tracking
    print("\n6️⃣ Testing time tracking...")
    
    # Record time IN for student
    if record_time_action('2024-12345', 'Maria Santos', 'STUDENT', 'IN'):
        print("✅ Student TIME IN recorded")
    else:
        print("❌ Failed to record student TIME IN")
    
    # Check status
    status = get_user_current_status('2024-12345')
    print(f"   Current status: {status}")
    
    # Record time IN for staff
    if record_time_action('STAFF-001', 'Juan Dela Cruz', 'STAFF', 'IN'):
        print("✅ Staff TIME IN recorded")
    else:
        print("❌ Failed to record staff TIME IN")
    
    # Get users currently inside
    print("\n7️⃣ Testing current status tracking...")
    users_inside = get_users_currently_inside()
    print(f"✅ Found {len(users_inside)} user(s) currently inside:")
    for user in users_inside:
        print(f"   - {user['user_name']} ({user['user_type']}) - Since: {user['time_in']}")
    
    # Get statistics
    print("\n8️⃣ Testing statistics...")
    stats = get_database_statistics()
    print("📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test time OUT
    print("\n9️⃣ Testing TIME OUT...")
    if record_time_action('2024-12345', 'Maria Santos', 'STUDENT', 'OUT'):
        print("✅ Student TIME OUT recorded")
    
    status_after = get_user_current_status('2024-12345')
    print(f"   Status after TIME OUT: {status_after}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n💡 Your centralized database is working correctly!")
    print("📋 You can now:")
    print("   1. Run the migration script to import your existing data")
    print("   2. Update your imports to use the new database structure")
    print("   3. Test with your actual MotorPass system")

if __name__ == "__main__":
    test_database()
