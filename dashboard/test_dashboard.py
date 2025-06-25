#!/usr/bin/env python3
# dashboard/test_dashboard.py - Test script to verify dashboard compatibility

import os
import sys
import sqlite3
from datetime import datetime

# Add project root to path
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(dashboard_dir)
sys.path.insert(0, project_root)

def test_database_structure():
    """Test if database has the expected structure"""
    print("🧪 Testing Database Structure...")
    
    from database.init_database import MOTORPASS_DB
    
    if not os.path.exists(MOTORPASS_DB):
        print("❌ Database not found at:", MOTORPASS_DB)
        return False
    
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Check required tables
        required_tables = {
            'students': ['student_id', 'full_name', 'course'],
            'staff': ['staff_no', 'full_name', 'staff_role'],
            'guests': ['guest_id', 'full_name', 'plate_number', 'office_visiting'],
            'time_tracking': ['user_id', 'user_name', 'user_type', 'action', 'date', 'time'],
            'current_status': ['user_id', 'user_name', 'user_type', 'status']
        }
        
        all_good = True
        
        for table, required_columns in required_tables.items():
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if not columns:
                print(f"❌ Table '{table}' not found")
                all_good = False
                continue
            
            print(f"✅ Table '{table}' exists")
            
            # Check required columns
            for col in required_columns:
                if col not in columns:
                    print(f"  ❌ Missing column '{col}' in {table}")
                    all_good = False
                else:
                    print(f"  ✅ Column '{col}' found")
        
        conn.close()
        return all_good
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_data_retrieval():
    """Test if we can retrieve data correctly"""
    print("\n🧪 Testing Data Retrieval...")
    
    try:
        from database.db_operations import (
            get_all_students,
            get_all_staff,
            get_all_guests,
            get_students_currently_in
        )
        
        # Test getting all users
        students = get_all_students()
        print(f"✅ Retrieved {len(students)} students")
        
        staff = get_all_staff()
        print(f"✅ Retrieved {len(staff)} staff members")
        
        guests = get_all_guests()
        print(f"✅ Retrieved {len(guests)} guests")
        
        # Test current status
        currently_in = get_students_currently_in()
        print(f"✅ {len(currently_in)} people currently inside")
        
        return True
        
    except Exception as e:
        print(f"❌ Data retrieval error: {e}")
        return False

def test_dashboard_imports():
    """Test if dashboard can import required modules"""
    print("\n🧪 Testing Dashboard Imports...")
    
    try:
        # Test Flask
        import flask
        print("✅ Flask installed")
        
        import flask_cors
        print("✅ Flask-CORS installed")
        
        # Test dashboard app
        from dashboard.app import app
        print("✅ Dashboard app imports successfully")
        
        # Test routes exist
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required_routes = ['/', '/login', '/api/dashboard-data', '/reports', '/time-records']
        
        for route in required_routes:
            if route in routes:
                print(f"✅ Route '{route}' exists")
            else:
                print(f"❌ Route '{route}' missing")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Install missing packages: pip install flask flask-cors")
        return False
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return False

def create_test_data():
    """Create some test data if database is empty"""
    print("\n🧪 Checking for Test Data...")
    
    from database.init_database import MOTORPASS_DB
    
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Check if we have any time tracking data
        cursor.execute("SELECT COUNT(*) FROM time_tracking")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📝 Creating test data...")
            
            # Add test time records
            test_date = datetime.now().strftime('%Y-%m-%d')
            test_time = datetime.now().strftime('%H:%M:%S')
            
            test_records = [
                ('2021-0001', 'Juan Dela Cruz', 'STUDENT', 'IN'),
                ('2021-0002', 'Maria Santos', 'STUDENT', 'IN'),
                ('STAFF001', 'Dr. Jose Rizal', 'STAFF', 'IN'),
                ('GUEST_ABC123', 'Pedro Penduko', 'GUEST', 'IN'),
            ]
            
            for user_id, name, user_type, action in test_records:
                cursor.execute('''
                    INSERT INTO time_tracking (user_id, user_name, user_type, action, date, time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, name, user_type, action, test_date, test_time))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO current_status (user_id, user_name, user_type, status)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, name, user_type, 'IN'))
            
            conn.commit()
            print("✅ Test data created")
        else:
            print(f"✅ Database has {count} time records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Test data error: {e}")
        return False

def test_api_endpoints():
    """Test if API endpoints work"""
    print("\n🧪 Testing API Endpoints...")
    
    try:
        from dashboard.app import app
        
        # Create test client
        client = app.test_client()
        
        # Test dashboard data endpoint
        response = client.get('/api/dashboard-data')
        if response.status_code == 302:  # Redirect to login
            print("✅ API requires authentication (as expected)")
        else:
            print(f"⚠️  API returned status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🚗 MOTORPASS DASHBOARD TEST SUITE")
    print("="*60)
    
    tests = [
        ("Database Structure", test_database_structure),
        ("Data Retrieval", test_data_retrieval),
        ("Dashboard Imports", test_dashboard_imports),
        ("Test Data", create_test_data),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Dashboard is ready to use.")
        print("\n📝 Next steps:")
        print("1. Run: python dashboard/start_dashboard.py")
        print("2. Open browser to: http://localhost:5000")
        print("3. Login with: admin / motorpass123")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()
