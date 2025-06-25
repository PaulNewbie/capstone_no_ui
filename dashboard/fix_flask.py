#!/usr/bin/env python3
# dashboard/fix_flask_issue.py - Fix Flask/Werkzeug compatibility issue

import subprocess
import sys

def fix_flask_werkzeug():
    """Fix the Flask/Werkzeug version compatibility issue"""
    print("🔧 Fixing Flask/Werkzeug Compatibility Issue")
    print("="*50)
    
    print("\n📋 Current versions:")
    try:
        import flask
        print(f"Flask: {flask.__version__}")
    except:
        print("Flask: Not installed")
    
    try:
        import werkzeug
        # Try to get version in different ways
        if hasattr(werkzeug, '__version__'):
            print(f"Werkzeug: {werkzeug.__version__}")
        else:
            print("Werkzeug: Installed but version unknown (compatibility issue)")
    except:
        print("Werkzeug: Not installed")
    
    print("\n🔧 Applying fix...")
    print("This will install compatible versions of Flask and Werkzeug")
    
    # Option 1: Try to upgrade to latest compatible versions
    print("\n📦 Option 1: Upgrading to latest compatible versions...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'flask', 'werkzeug', 'flask-cors'])
        print("✅ Packages upgraded successfully")
        
        # Test if it works now
        try:
            import flask
            import werkzeug
            if hasattr(werkzeug, '__version__'):
                print(f"\n✅ Success! Flask {flask.__version__} with Werkzeug {werkzeug.__version__}")
                return True
        except:
            pass
            
    except subprocess.CalledProcessError:
        print("⚠️  Upgrade failed, trying alternative approach...")
    
    # Option 2: Install specific compatible versions
    print("\n📦 Option 2: Installing specific compatible versions...")
    try:
        # Uninstall first to avoid conflicts
        print("Removing old versions...")
        subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'flask', 'werkzeug'], 
                      capture_output=True)
        
        # Install specific versions known to work together
        print("Installing Flask 2.2.5 with Werkzeug 2.2.3...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
                             'flask==2.2.5', 'werkzeug==2.2.3', 'flask-cors'])
        
        print("✅ Specific versions installed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        
    # Option 3: Manual instructions
    print("\n❌ Automatic fix failed. Please try manually:")
    print("\n1. First, uninstall current versions:")
    print("   pip uninstall -y flask werkzeug flask-cors")
    print("\n2. Then install compatible versions:")
    print("   pip install flask==2.2.5 werkzeug==2.2.3 flask-cors")
    print("\nOr try older stable versions:")
    print("   pip install flask==2.0.3 werkzeug==2.0.3 flask-cors")
    
    return False

def test_import():
    """Test if the issue is fixed"""
    print("\n🧪 Testing if issue is fixed...")
    try:
        import flask
        import werkzeug
        from dashboard.app import app
        
        print(f"✅ Flask {flask.__version__} imported successfully")
        if hasattr(werkzeug, '__version__'):
            print(f"✅ Werkzeug {werkzeug.__version__} imported successfully")
        else:
            print("⚠️  Werkzeug imported but version still unknown")
        print("✅ Dashboard app imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚗 MotorPass Dashboard - Flask/Werkzeug Fix")
    print("="*50)
    
    # Apply fix
    if fix_flask_werkzeug():
        # Test if it worked
        if test_import():
            print("\n🎉 Issue fixed! You can now run the dashboard.")
            print("\nNext step:")
            print("   python dashboard/start_dashboard.py")
        else:
            print("\n⚠️  Fix applied but import still failing.")
            print("Try restarting your Python environment.")
    else:
        print("\n❌ Could not fix automatically. Please follow manual instructions above.")
