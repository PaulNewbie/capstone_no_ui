#!/usr/bin/env python3
# test_gui.py - Test the new GUI implementation

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rpi_camera import ensure_camera_cleanup

def test_camera_cleanup():
    """Test camera cleanup functionality"""
    print("🧪 Testing camera cleanup...")
    
    try:
        ensure_camera_cleanup()
        print("✅ Camera cleanup successful")
    except Exception as e:
        print(f"❌ Camera cleanup failed: {e}")

def test_student_gui():
    """Test student GUI independently"""
    print("\n🧪 Testing Student GUI...")
    
    from ui.student_gui import StudentVerificationGUI
    
    def mock_verification(callback):
        """Mock verification process"""
        time.sleep(1)
        callback({'current_step': '🧪 Running test verification...'})
        
        # Simulate helmet check
        callback({'helmet_status': 'CHECKING'})
        time.sleep(2)
        callback({'helmet_status': 'VERIFIED'})
        
        # Simulate fingerprint
        callback({'fingerprint_status': 'PROCESSING'})
        time.sleep(2)
        callback({'fingerprint_status': 'VERIFIED'})
        
        # Simulate user info
        user_info = {
            'name': 'TEST USER',
            'student_id': 'TEST123',
            'course': 'Computer Science',
            'user_type': 'STUDENT',
            'confidence': 95
        }
        callback({'user_info': user_info})
        
        # Simulate license check
        callback({'license_status': 'VALID'})
        time.sleep(1)
        
        # Show summary
        callback({
            'verification_summary': {
                'helmet': True,
                'fingerprint': True,
                'license_valid': True,
                'license_detected': True,
                'name_match': True
            }
        })
        
        time.sleep(1)
        
        # Final result
        return {
            'verified': True,
            'name': 'TEST USER',
            'time_action': 'IN',
            'timestamp': time.strftime('%H:%M:%S')
        }
    
    try:
        gui = StudentVerificationGUI(mock_verification)
        gui.run()
        print("✅ Student GUI test completed")
    except Exception as e:
        print(f"❌ Student GUI test failed: {e}")

def test_guest_gui():
    """Test guest GUI independently"""
    print("\n🧪 Testing Guest GUI...")
    
    from ui.guest_gui import GuestVerificationGUI
    
    def mock_guest_verification(callback):
        """Mock guest verification process"""
        time.sleep(1)
        callback({'current_step': '🧪 Running guest test...'})
        
        # Simulate helmet check
        callback({'helmet_status': 'CHECKING'})
        time.sleep(2)
        callback({'helmet_status': 'VERIFIED'})
        
        # Simulate license check
        callback({'license_status': 'PROCESSING'})
        time.sleep(2)
        callback({'license_status': 'DETECTED'})
        
        # Simulate guest info
        guest_info = {
            'name': 'TEST GUEST',
            'plate_number': 'ABC123',
            'office': 'CSS Office',
            'status': 'NEW GUEST'
        }
        callback({'guest_info': guest_info})
        
        # Show summary
        callback({
            'verification_summary': {
                'helmet': True,
                'license': True
            }
        })
        
        time.sleep(1)
        
        # Final result
        return {
            'verified': True,
            'name': 'TEST GUEST',
            'time_action': 'IN',
            'timestamp': time.strftime('%H:%M:%S'),
            'office': 'CSS Office'
        }
    
    try:
        gui = GuestVerificationGUI(mock_guest_verification)
        gui.run()
        print("✅ Guest GUI test completed")
    except Exception as e:
        print(f"❌ Guest GUI test failed: {e}")

def main():
    """Main test function"""
    print("🚗 MotorPass GUI Test Suite")
    print("="*50)
    
    while True:
        print("\nSelect test:")
        print("1. Test camera cleanup")
        print("2. Test Student GUI")
        print("3. Test Guest GUI")
        print("4. Exit")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == '1':
            test_camera_cleanup()
        elif choice == '2':
            ensure_camera_cleanup()
            test_student_gui()
            ensure_camera_cleanup()
        elif choice == '3':
            ensure_camera_cleanup()
            test_guest_gui()
            ensure_camera_cleanup()
        elif choice == '4':
            print("👋 Exiting test suite")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted")
    finally:
        ensure_camera_cleanup()
        print("✅ Final cleanup complete")
