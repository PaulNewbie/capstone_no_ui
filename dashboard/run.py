#!/usr/bin/env python3
# dashboard/run.py - Simple startup script for new dashboard

import os
import sys
import subprocess

# Add project root to Python path
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(dashboard_dir)
sys.path.insert(0, project_root)

# Change to project root
os.chdir(project_root)

def get_ip_address():
    """Get the system's IP address"""
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            for ip in ips:
                if ip and not ip.startswith('127.'):
                    return ip
    except:
        pass
    return 'localhost'

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_cors
        return True
    except ImportError:
        return False

def main():
    print("="*60)
    print("🚗 MOTORPASS ADMIN DASHBOARD")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Missing required packages!")
        print("📦 Please install:")
        print("   pip install flask flask-cors")
        return
    
    # Check database
    from database.init_database import MOTORPASS_DB, initialize_all_databases
    
    if not os.path.exists(MOTORPASS_DB):
        print("⚠️  Database not found. Initializing...")
        if not initialize_all_databases():
            print("❌ Failed to initialize database!")
            return
    
    # Display info
    print(f"\n📂 Database: {MOTORPASS_DB}")
    if os.path.exists(MOTORPASS_DB):
        size_mb = os.path.getsize(MOTORPASS_DB) / 1024 / 1024
        print(f"✅ Database found ({size_mb:.2f} MB)")
    
    # Get IP address
    ip_address = get_ip_address()
    print(f"\n📡 Dashboard will be available at:")
    print(f"   http://{ip_address}:5000")
    print(f"   http://localhost:5000")
    print(f"\n🔐 Default login: admin / motorpass123")
    print(f"⚠️  Change the password in dashboard/app.py!")
    print(f"\n✋ Press Ctrl+C to stop the dashboard")
    print("="*60)
    
    # Run the dashboard
    try:
        from dashboard.app import app
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
