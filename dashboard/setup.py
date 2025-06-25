#!/usr/bin/env python3
# dashboard/setup.py - Quick setup script for MotorPass Dashboard

import os
import sys
import shutil
import subprocess

def check_python_version():
    """Check if Python version is 3.7+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required. You have:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    packages = ['flask', 'flask-cors']
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} already installed")
        except ImportError:
            print(f"📥 Installing {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                print("   Try manually: pip install", package)
                return False
    
    return True

def check_project_structure():
    """Check if we're in the right directory"""
    print("\n📁 Checking project structure...")
    
    # Check if we're in MotorPass root
    required_files = ['main.py', 'config.py']
    required_dirs = ['database', 'controllers', 'services']
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing file: {file}")
            print("   Make sure you're in the MotorPass root directory!")
            return False
    
    for dir in required_dirs:
        if not os.path.exists(dir):
            print(f"❌ Missing directory: {dir}")
            return False
    
    print("✅ Project structure verified")
    return True

def create_dashboard_structure():
    """Create dashboard directory structure"""
    print("\n📁 Setting up dashboard directories...")
    
    # Create directories
    dirs = [
        'dashboard',
        'dashboard/templates',
        'dashboard/static'  # For future use
    ]
    
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)
        print(f"✅ Created {dir}/")
    
    return True

def check_database():
    """Check if database exists and is accessible"""
    print("\n🗄️ Checking database...")
    
    db_path = 'database/motorpass.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        print("   Please run main.py first to initialize the database")
        return False
    
    size_mb = os.path.getsize(db_path) / 1024 / 1024
    print(f"✅ Database found ({size_mb:.2f} MB)")
    
    # Test database access
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['students', 'staff', 'guests', 'time_tracking', 'current_status']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            print(f"❌ Missing tables: {', '.join(missing)}")
            return False
        
        print(f"✅ All required tables found")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def create_default_config():
    """Create a default configuration file"""
    print("\n⚙️ Creating dashboard configuration...")
    
    config_content = '''# dashboard/config.py - Dashboard Configuration

# Change these values for production!
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'motorpass123'  # CHANGE THIS!
SECRET_KEY = 'motorpass-secret-key-change-this-in-production'

# Dashboard settings
AUTO_REFRESH_SECONDS = 5
MAX_RECORDS_DISPLAY = 100
ENABLE_DEBUG = False

# Network settings
DASHBOARD_HOST = '0.0.0.0'
DASHBOARD_PORT = 5000
'''
    
    config_path = 'dashboard/config.py'
    
    if os.path.exists(config_path):
        print("⚠️  Dashboard config already exists")
        response = input("   Overwrite? (y/N): ").lower()
        if response != 'y':
            return True
    
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print("✅ Dashboard configuration created")
    print("⚠️  Remember to change the admin password!")
    return True

def create_run_script():
    """Create a simple run script"""
    print("\n📝 Creating run script...")
    
    run_content = '''#!/bin/bash
# Simple script to run MotorPass Dashboard

echo "Starting MotorPass Dashboard..."
cd "$(dirname "$0")/.."
python dashboard/start_dashboard.py
'''
    
    run_path = 'dashboard/run.sh'
    
    with open(run_path, 'w') as f:
        f.write(run_content)
    
    # Make executable
    try:
        os.chmod(run_path, 0o755)
        print("✅ Run script created: dashboard/run.sh")
    except:
        print("✅ Run script created (set executable manually)")
    
    return True

def main():
    """Main setup function"""
    print("="*60)
    print("🚗 MOTORPASS DASHBOARD SETUP")
    print("="*60)
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Dashboard Directories", create_dashboard_structure),
        ("Database", check_database),
        ("Dependencies", install_dependencies),
        ("Configuration", create_default_config),
        ("Run Script", create_run_script)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
                print(f"\n❌ Setup failed at: {check_name}")
                break
        except Exception as e:
            print(f"\n❌ Error during {check_name}: {e}")
            all_passed = False
            break
    
    # Final instructions
    if all_passed:
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("\n📝 Next steps:")
        print("\n1. Copy the dashboard files:")
        print("   - app.py")
        print("   - templates/*.html")
        print("   - start_dashboard.py")
        print("\n2. Test the setup:")
        print("   python dashboard/test_dashboard.py")
        print("\n3. Start the dashboard:")
        print("   python dashboard/start_dashboard.py")
        print("\n4. Access dashboard:")
        print("   http://localhost:5000")
        print("   Login: admin / motorpass123")
        print("\n⚠️  Important reminders:")
        print("   - Change the admin password in dashboard/config.py")
        print("   - Run from MotorPass root directory")
        print("   - Ensure main system is working first")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("❌ Error: This script must be run from the MotorPass root directory!")
        print("   Current directory:", os.getcwd())
        print("   Please cd to your MotorPass directory and try again.")
        sys.exit(1)
    
    main()
