#!/usr/bin/env python3
# check_database.py - Check database status

import os
import sqlite3

def check_database():
    """Check database status and provide info"""
    
    print("🔍 MotorPass Database Check")
    print("="*40)
    
    # Check for database files
    possible_locations = [
        "motorpass.db",
        "database/motorpass.db"
    ]
    
    found_databases = []
    
    for location in possible_locations:
        if os.path.exists(location):
            try:
                size_mb = os.path.getsize(location) / 1024 / 1024
                
                # Check if it has data
                conn = sqlite3.connect(location)
                cursor = conn.cursor()
                
                # Check for time_records table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_records'")
                has_time_records = cursor.fetchone() is not None
                
                record_count = 0
                if has_time_records:
                    cursor.execute("SELECT COUNT(*) FROM time_records")
                    record_count = cursor.fetchone()[0]
                
                conn.close()
                
                found_databases.append({
                    'path': location,
                    'size_mb': size_mb,
                    'has_data': has_time_records,
                    'record_count': record_count
                })
                
            except Exception as e:
                found_databases.append({
                    'path': location,
                    'size_mb': 0,
                    'has_data': False,
                    'record_count': 0,
                    'error': str(e)
                })
    
    if not found_databases:
        print("❌ No database files found")
        print("\n💡 Solutions:")
        print("  1. Run your main system first to create database")
        print("  2. Database will be created automatically when needed")
        return
    
    print(f"📊 Found {len(found_databases)} database(s):")
    print()
    
    for i, db_info in enumerate(found_databases, 1):
        print(f"{i}. {db_info['path']}")
        print(f"   Size: {db_info['size_mb']:.2f} MB")
        print(f"   Records: {db_info['record_count']}")
        
        if 'error' in db_info:
            print(f"   ⚠️  Error: {db_info['error']}")
        elif db_info['has_data']:
            print(f"   ✅ Has data")
        else:
            print(f"   📁 Empty/New")
        print()
    
    # Recommend correct database
    target_db = "database/motorpass.db"
    target_exists = any(db['path'] == target_db for db in found_databases)
    
    if target_exists:
        target_info = next(db for db in found_databases if db['path'] == target_db)
        print(f"✅ Correct database location found: {target_db}")
        print(f"   Records: {target_info['record_count']}")
    else:
        print(f"⚠️  Target location: {target_db} (not found)")
        
        # Find database with most data
        best_db = max(found_databases, key=lambda x: x['record_count'])
        if best_db['record_count'] > 0:
            print(f"💡 Database with most data: {best_db['path']} ({best_db['record_count']} records)")
            print(f"   Consider running: python migrate_database.py")
    
    print("\n🚀 To start dashboard:")
    print("  python start_dashboard.py")

def test_dashboard_connection():
    """Test dashboard database connection"""
    print("\n🔗 Testing dashboard connection...")
    
    try:
        from database.unified_db import db
        stats = db.get_database_stats()
        
        print("✅ Dashboard connection successful")
        print(f"📊 Records: {stats.get('total_time_records', 0)}")
        print(f"👥 Students: {stats.get('total_students', 0)}")
        print(f"🎫 Guests: {stats.get('total_guests', 0)}")
        print(f"📂 Database: {db.db_path}")
        
    except Exception as e:
        print(f"❌ Dashboard connection failed: {e}")

if __name__ == "__main__":
    check_database()
    test_dashboard_connection()
