# quick_migration_fix.py - Run this once to fix your database

import sqlite3
import os

def fix_database():
    """Quick fix for existing database"""
    try:
        db_path = "database/time_tracking.db"
        
        if not os.path.exists(db_path):
            print("✅ No existing database - system will create fresh one")
            return
        
        print("🔄 Fixing existing database...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add user_type column to time_records if it doesn't exist
        try:
            cursor.execute("ALTER TABLE time_records ADD COLUMN user_type TEXT NOT NULL DEFAULT 'STUDENT'")
            print("✅ Added user_type column to time_records")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✅ user_type column already exists in time_records")
            else:
                print(f"❌ Error with time_records: {e}")
        
        # Add user_type column to current_status if it doesn't exist
        try:
            cursor.execute("ALTER TABLE current_status ADD COLUMN user_type TEXT NOT NULL DEFAULT 'STUDENT'")
            print("✅ Added user_type column to current_status")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✅ user_type column already exists in current_status")
            else:
                print(f"❌ Error with current_status: {e}")
        
        # Create indexes
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_user_type ON time_records(user_type)')
            print("✅ Created user_type index")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")
        
        conn.commit()
        conn.close()
        
        print("🎉 Database migration completed successfully!")
        print("✅ You can now restart your MotorPass system")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    print("🗄️ MotorPass Database Migration Tool")
    print("=" * 50)
    fix_database()
