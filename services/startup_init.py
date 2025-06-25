# services/startup_init.py - Initialize camera once at startup

import time
from services.rpi_camera import get_camera

def initialize_camera_at_startup():
    """Initialize camera once when the application starts"""
    print("\n🚀 === STARTUP CAMERA INITIALIZATION ===")
    
    try:
        # Get camera instance - this will initialize it
        camera = get_camera()
        
        if camera.initialized:
            print("✅ Camera initialized at startup")
            
            # Test capture a few frames
            print("📸 Testing camera with a few captures...")
            for i in range(3):
                frame = camera.get_frame()
                if frame is not None:
                    print(f"  ✅ Test frame {i+1} captured successfully")
                else:
                    print(f"  ❌ Test frame {i+1} failed")
                time.sleep(0.5)
            
            print("✅ Camera is ready for use!")
            return True
        else:
            print("❌ Failed to initialize camera at startup")
            return False
            
    except Exception as e:
        print(f"❌ Startup initialization error: {e}")
        return False
