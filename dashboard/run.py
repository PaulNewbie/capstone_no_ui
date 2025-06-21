#!/usr/bin/env python3
# dashboard/run.py - Fixed dashboard startup

import os
import sys
import subprocess

# FIXED: Get correct paths
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(dashboard_dir)

# FIXED: Add both project root and dashboard to path
sys.path.insert(0, project_root)
sys.path.insert(0, dashboard_dir)

# FIXED: Change to project root directory (where main.py is)
os.chdir(project_root)

# Get IP address
def get_ip():
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

print("="*60)
print("🚗 MOTORPASS ADMIN DASHBOARD")
print("="*60)

# FIXED: Show database path being used
try:
    from database.unified_db import DB_FILE
    print(f"📂 Using database: {DB_FILE}")
    
    # Check if database file exists
    if os.path.exists(DB_FILE):
        size_mb = os.path.getsize(DB_FILE) / 1024 / 1024
        print(f"✅ Database found ({size_mb:.2f} MB)")
    else:
        print(f"⚠️  Database will be created at: {DB_FILE}")
        
except Exception as e:
    print(f"❌ Database path error: {e}")

ip_address = get_ip()
print(f"\n📡 Dashboard will be available at:")
print(f"   http://{ip_address}:5000")
print(f"\n🔐 Login: admin / motorpass123")
print(f"\n⚠️  Press Ctrl+C to stop")
print("="*60)

# Run the app directly
try:
    from dashboard.app import app
    app.run(host='0.0.0.0', port=5000, debug=False)
except KeyboardInterrupt:
    print("\n\n🛑 Dashboard stopped")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check if main database exists")
    print("2. Install Flask: pip install flask flask-cors")
    print("3. Run from project root directory")
