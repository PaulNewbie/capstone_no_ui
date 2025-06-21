#!/usr/bin/env python3
# dashboard/run.py - Simple dashboard startup

import os
import sys
import subprocess

# Change to dashboard directory
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(dashboard_dir)

# Add parent to path
parent_dir = os.path.dirname(dashboard_dir)
sys.path.insert(0, parent_dir)

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

ip_address = get_ip()
print(f"\n📡 Dashboard will be available at:")
print(f"   http://{ip_address}:5000")
print(f"\n🔐 Login: admin / motorpass123")
print(f"\n⚠️  Press Ctrl+C to stop")
print("="*60)

# Run the app directly
try:
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=False)
except KeyboardInterrupt:
    print("\n\n🛑 Dashboard stopped")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Run: python fix_imports.py")
    print("2. Check if database exists")
    print("3. Install Flask: pip install flask flask-cors")
