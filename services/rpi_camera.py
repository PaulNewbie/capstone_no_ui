# services/rpi_camera.py - Simple fix that reuses camera instance

import cv2
import numpy as np
import time
import os
from datetime import datetime
from config import RPI_CAMERA_RESOLUTION, RPI_CAMERA_FRAMERATE, RPI_CAMERA_WARMUP_TIME

try:
    from picamera2 import Picamera2
    RPI_CAMERA_AVAILABLE = True
except ImportError:
    RPI_CAMERA_AVAILABLE = False

# Global camera instance - keep it alive
_camera_instance = None
_picamera2_instance = None  # Keep the actual Picamera2 object

def get_camera():
    """Get global camera instance (singleton)"""
    global _camera_instance
    
    if _camera_instance is None:
        _camera_instance = RPiCameraService()
    elif not _camera_instance.initialized:
        # Try to reinitialize if not initialized
        _camera_instance._initialize_camera()
    
    return _camera_instance

def force_camera_cleanup():
    """Only cleanup OpenCV windows, keep camera running"""
    print("🧹 Cleaning up OpenCV windows...")
    
    # Destroy any OpenCV windows
    for _ in range(3):
        try:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        except:
            pass
    
    print("✅ OpenCV cleanup completed")

def release_camera():
    """Don't actually release - just cleanup windows"""
    force_camera_cleanup()

class RPiCameraService:
    def __init__(self):
        self.camera = None
        self.initialized = False
        if RPI_CAMERA_AVAILABLE:
            self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize RPi Camera - reuse existing if possible"""
        global _picamera2_instance
        
        if not RPI_CAMERA_AVAILABLE:
            return False
            
        try:
            # Suppress libcamera logs
            os.environ['LIBCAMERA_LOG_LEVELS'] = 'ERROR'
            
            # Reuse existing camera if available
            if _picamera2_instance is not None:
                print("📷 Reusing existing camera instance...")
                self.camera = _picamera2_instance
                self.initialized = True
                return True
            
            print("📷 Creating new camera instance...")
            
            # Create new camera instance
            self.camera = Picamera2()
            _picamera2_instance = self.camera  # Store globally
            
            # Configure
            config = self.camera.create_preview_configuration(
                main={"size": RPI_CAMERA_RESOLUTION, "format": "RGB888"}
            )
            self.camera.configure(config)
            
            # Start camera
            self.camera.start()
            time.sleep(RPI_CAMERA_WARMUP_TIME)
            
            # Try to set autofocus
            try:
                from libcamera import controls
                self.camera.set_controls({
                    "AfMode": controls.AfModeEnum.Continuous,
                    "AfSpeed": controls.AfSpeedEnum.Fast,
                })
            except:
                pass
            
            self.initialized = True
            print("✅ Camera initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            self.initialized = False
            return False
    
    def get_frame(self):
        """Get current frame from camera"""
        if not self.initialized or not self.camera:
            return None
        
        try:
            frame = self.camera.capture_array()
            
            # Convert format if needed
            if frame is not None and len(frame.shape) == 3:
                if frame.shape[2] == 4:  # RGBA format
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                elif frame.shape[2] == 3:  # RGB format
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            return frame
        except Exception as e:
            print(f"⚠️ Error getting frame: {e}")
            # Try to reinitialize
            self._initialize_camera()
            return None
    
    def release(self):
        """Don't actually release - keep camera running"""
        pass

# Context manager for safe camera operations
class CameraContext:
    """Context manager that only cleans OpenCV windows"""
    def __enter__(self):
        force_camera_cleanup()  # Clean windows before use
        self.camera = get_camera()
        return self.camera
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        force_camera_cleanup()  # Clean windows after use
        return False

# Helper to ensure cleanup
def ensure_camera_cleanup():
    """Just cleanup OpenCV windows"""
    force_camera_cleanup()

# Emergency reset function
def emergency_camera_reset():
    """Force reset camera if really needed"""
    global _camera_instance, _picamera2_instance
    
    print("🚨 Emergency camera reset!")
    
    # Try to stop camera
    if _picamera2_instance:
        try:
            _picamera2_instance.stop()
            _picamera2_instance.close()
        except:
            pass
    
    # Reset instances
    _camera_instance = None
    _picamera2_instance = None
    
    # Kill processes
    try:
        import subprocess
        subprocess.run(['pkill', '-f', 'libcamera'], capture_output=True)
    except:
        pass
    
    time.sleep(2)
    print("✅ Emergency reset complete")
