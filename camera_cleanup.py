#!/usr/bin/env python3
# test_camera_diagnostic.py - Diagnose camera issues
''''
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_picamera():
    """Test basic Picamera2 functionality"""
    print("\n🔍 Testing basic Picamera2...")
    
    try:
        from picamera2 import Picamera2
        import cv2
        import numpy as np
        
        # Test 1: Create and destroy camera
        print("\n📷 Test 1: Create and destroy camera")
        cam = Picamera2()
        print("✅ Camera created")
        cam.close()
        print("✅ Camera closed")
        time.sleep(1)
        
        # Test 2: Create, start, capture, stop
        print("\n📷 Test 2: Full camera cycle")
        cam = Picamera2()
        config = cam.create_preview_configuration(main={"size": (640, 480)})
        cam.configure(config)
        print("✅ Camera configured")
        
        cam.start()
        print("✅ Camera started")
        time.sleep(1)
        
        frame = cam.capture_array()
        print(f"✅ Frame captured: shape={frame.shape if frame is not None else 'None'}")
        
        cam.stop()
        cam.close()
        print("✅ Camera stopped and closed")
        time.sleep(1)
        
        # Test 3: Multiple init cycles
        print("\n📷 Test 3: Multiple initialization cycles")
        for i in range(3):
            print(f"\nCycle {i+1}/3...")
            cam = Picamera2()
            cam.configure(cam.create_preview_configuration())
            cam.start()
            time.sleep(0.5)
            frame = cam.capture_array()
            print(f"✅ Cycle {i+1}: Frame captured")
            cam.stop()
            cam.close()
            time.sleep(1)
        
        print("\n✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_cleanup_manager():
    """Test camera with cleanup manager"""
    print("\n🔍 Testing with cleanup manager...")
    
    try:
        from utils.cleanup_manager import deep_cleanup
        from services.rpi_camera import get_camera, force_camera_cleanup
        
        for i in range(2):
            print(f"\n📷 Test iteration {i+1}/2...")
            
            # Deep cleanup first
            deep_cleanup()
            
            # Get camera
            camera = get_camera()
            if camera.initialized:
                print("✅ Camera initialized")
                
                # Try to get frames
                for j in range(5):
                    frame = camera.get_frame()
                    if frame is not None:
                        print(f"✅ Frame {j+1} captured")
                    else:
                        print(f"❌ Frame {j+1} is None")
                    time.sleep(0.2)
            else:
                print("❌ Camera initialization failed")
            
            # Cleanup
            deep_cleanup()
            print("✅ Cleanup completed")
            time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Cleanup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_camera_processes():
    """Check for running camera processes"""
    print("\n🔍 Checking camera processes...")
    
    try:
        import subprocess
        
        # Check for libcamera processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        camera_processes = [line for line in lines if 'libcamera' in line or 'picamera' in line]
        
        if camera_processes:
            print("⚠️ Found camera processes:")
            for proc in camera_processes:
                print(f"  {proc[:100]}...")
        else:
            print("✅ No camera processes found")
            
        return len(camera_processes) == 0
        
    except Exception as e:
        print(f"❌ Process check failed: {e}")
        return False

def main():
    """Run all diagnostics"""
    print("🚗 MotorPass Camera Diagnostic")
    print("="*50)
    
    # Check processes first
    check_camera_processes()
    
    # Run basic test
    if test_basic_picamera():
        print("\n✅ Basic Picamera2 tests passed")
    else:
        print("\n❌ Basic tests failed - camera may be in use")
        
        # Try to kill processes
        print("\n🔄 Attempting to reset camera system...")
        import subprocess
        subprocess.run(['pkill', '-f', 'libcamera'], capture_output=True)
        time.sleep(2)
        
        # Retry
        if test_basic_picamera():
            print("\n✅ Camera recovered after reset")
        else:
            print("\n❌ Camera still not working")
            return
    
    # Test with cleanup manager
    test_with_cleanup_manager()
    
    # Final process check
    print("\n🔍 Final process check...")
    check_camera_processes()
    
    print("\n✅ Diagnostic complete!")

if __name__ == "__main__":
    main()
'''
