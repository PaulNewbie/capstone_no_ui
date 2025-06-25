#!/usr/bin/env python3
# test_admin_gui.py - Test the admin GUI independently

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.admin_gui import AdminPanelGUI
import json

def test_admin_gui():
    """Test admin GUI with mock functions"""
    print("🧪 Testing Admin GUI...")
    
    # Mock functions for testing
    mock_functions = {
        'authenticate': lambda: True,  # Always authenticate for testing
        'enroll': lambda: print("Mock: Enrolling new user..."),
        'view_users': lambda: print("Mock: Viewing users..."),
        'delete_fingerprint': lambda slot: print(f"Mock: Deleting slot {slot}..."),
        'sync': lambda: print("Mock: Syncing database..."),
        'get_time_records': lambda: [
            {
                'date': '2024-01-01', 
                'time': '08:00:00', 
                'student_id': '2021-001', 
                'student_name': 'Juan Dela Cruz', 
                'user_type': 'STUDENT', 
                'status': 'IN'
            },
            {
                'date': '2024-01-01', 
                'time': '17:00:00', 
                'student_id': '2021-001', 
                'student_name': 'Juan Dela Cruz', 
                'user_type': 'STUDENT', 
                'status': 'OUT'
            },
            {
                'date': '2024-01-01', 
                'time': '08:30:00', 
                'student_id': 'STAFF001', 
                'student_name': 'Dr. Jose Rizal', 
                'user_type': 'STAFF', 
                'status': 'IN'
            }
        ],
        'clear_records': lambda: print("Mock: Clearing time records..."),
        'get_stats': lambda: {
            'total_students': 150,
            'total_staff': 25,
            'total_guests': 50,
            'students_currently_in': 45,
            'staff_currently_in': 10,
            'guests_currently_in': 5,
            'users_currently_in': 60,
            'todays_activity': 120,
            'todays_student_activity': 80,
            'todays_staff_activity': 20,
            'todays_guest_activity': 20
        },
        'change_admin': lambda: print("Mock: Changing admin fingerprint..."),
        'reset': lambda: print("Mock: Resetting system...")
    }
    
    # Create test fingerprint database
    test_database = {
        "2": {
            "name": "Juan Dela Cruz",
            "user_type": "STUDENT",
            "student_id": "2021-001",
            "course": "BSCS",
            "license_number": "N03-12-123456",
            "license_expiration": "2025-12-31",
            "plate_number": "ABC123",
            "enrolled_date": "2024-01-01 08:00:00"
        },
        "3": {
            "name": "Maria Santos",
            "user_type": "STUDENT",
            "student_id": "2021-002",
            "course": "BSIT",
            "license_number": "N03-12-654321",
            "license_expiration": "2025-06-30",
            "plate_number": "XYZ789",
            "enrolled_date": "2024-01-01 09:00:00"
        },
        "4": {
            "name": "Dr. Jose Rizal",
            "user_type": "STAFF",
            "staff_no": "STAFF001",
            "staff_role": "Professor",
            "license_number": "P03-12-111111",
            "license_expiration": "2026-01-01",
            "plate_number": "PROF001",
            "enrolled_date": "2024-01-01 10:00:00"
        }
    }
    
    # Save test database
    os.makedirs("json_folder", exist_ok=True)
    with open("json_folder/fingerprint_database.json", "w") as f:
        json.dump(test_database, f, indent=4)
    
    try:
        # Create and run GUI (skip auth for testing)
        app = AdminPanelGUI(mock_functions, skip_auth=True)
        app.run()
        print("✅ Admin GUI test completed")
    except Exception as e:
        print(f"❌ Admin GUI test failed: {e}")

def main():
    """Main test function"""
    print("🚗 MotorPass Admin GUI Test")
    print("="*50)
    print("This will test the admin GUI with mock data")
    print("Authentication is skipped for testing - goes directly to admin panel")
    print("="*50)
    
    test_admin_gui()

if __name__ == "__main__":
    main()
