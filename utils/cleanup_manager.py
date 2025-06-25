# utils/cleanup_manager.py - Ensures complete cleanup after each verification

import cv2
import time
import gc
import os

def deep_cleanup():
    """Perform deep cleanup of all resources"""
    print("\n🧹 === DEEP CLEANUP INITIATED ===")
    
    # 1. Force garbage collection
    gc.collect()
    
    # 2. Clean up OpenCV windows only
    try:
        # Destroy all windows multiple times to ensure cleanup
        for _ in range(3):
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        print("✅ OpenCV windows cleaned")
    except:
        pass
    
    # 3. DO NOT kill camera - just ensure windows are closed
    try:
        from services.rpi_camera import force_camera_cleanup
        force_camera_cleanup()  # This now only cleans windows
        print("✅ Camera windows cleaned")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    # 4. Clean up any temporary files
    try:
        temp_dir = "/tmp"
        for file in os.listdir(temp_dir):
            if file.startswith("motorpass_") and file.endswith(".jpg"):
                try:
                    os.remove(os.path.join(temp_dir, file))
                except:
                    pass
        print("✅ Temporary files cleaned")
    except:
        pass
    
    # 5. Force LED to idle state
    try:
        from services.led_control import set_led_idle
        set_led_idle()
        print("✅ LED reset to idle")
    except:
        pass
    
    # 6. Final garbage collection
    gc.collect()
    
    # 7. Small wait
    time.sleep(0.5)
    
    print("✅ === DEEP CLEANUP COMPLETED ===\n")
    
    # 4. Clean up any temporary files
    try:
        temp_dir = "/tmp"
        for file in os.listdir(temp_dir):
            if file.startswith("motorpass_") and file.endswith(".jpg"):
                try:
                    os.remove(os.path.join(temp_dir, file))
                except:
                    pass
        print("✅ Temporary files cleaned")
    except:
        pass
    
    # 5. Force LED to idle state
    try:
        from services.led_control import set_led_idle
        set_led_idle()
        print("✅ LED reset to idle")
    except:
        pass
    
    # 6. Final garbage collection
    gc.collect()
    
    # 7. Wait a bit for everything to settle
    time.sleep(1.0)
    
    print("✅ === DEEP CLEANUP COMPLETED ===\n")

def ensure_verification_cleanup(func):
    """Decorator to ensure cleanup after verification"""
    def wrapper(*args, **kwargs):
        try:
            # Run the verification function
            result = func(*args, **kwargs)
            return result
        finally:
            # Always perform deep cleanup
            deep_cleanup()
    return wrapper

class VerificationCleanupContext:
    """Context manager for verification with guaranteed cleanup"""
    def __enter__(self):
        # Initial cleanup before starting
        deep_cleanup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup after verification
        deep_cleanup()
        return False
