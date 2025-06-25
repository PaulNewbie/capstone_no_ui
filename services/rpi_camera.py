# services/rpi_camera.py - Fixed with guaranteed cleanup between operations

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

# Global camera instance
_camera_instance = None

def force_camera_cleanup():
    """Force cleanup of camera resources"""
    global _camera_instance
    
    print("🧹 Forcing camera cleanup...")
    
    # Destroy any OpenCV windows
    try:
        cv2.destroyAllWindows()
        cv2.waitKey(1)
    except:
        pass
    
    # Release camera instance
    if _camera_instance is not None:
        try:
            if hasattr(_camera_instance, 'camera') and _camera_instance.camera:
                try:
                    _camera_instance.camera.stop()
                except:
                    pass
                try:
                    _camera_instance.camera.close()
                except:
                    pass
            _camera_instance = None
        except:
            pass
    
    # Wait a bit for resources to be freed
    time.sleep(0.5)
    print("✅ Camera cleanup completed")

def get_camera():
    """Get camera instance with auto-cleanup"""
    global _camera_instance
    
    # Always force cleanup first to ensure fresh start
    if _camera_instance is None:
        _camera_instance = RPiCameraService()
    
    return _camera_instance

def release_camera():
    """Release camera instance"""
    force_camera_cleanup()

class RPiCameraService:
    def __init__(self):
        self.camera = None
        self.initialized = False
        if RPI_CAMERA_AVAILABLE:
            self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize RPi Camera"""
        if not RPI_CAMERA_AVAILABLE:
            print("❌ RPi Camera not available")
            return False
            
        try:
            # Suppress libcamera logs
            os.environ['LIBCAMERA_LOG_LEVELS'] = 'ERROR'
            
            print("📷 Initializing camera...")
            self.camera = Picamera2()
            
            # Simple configuration
            config = self.camera.create_preview_configuration(
                main={"size": RPI_CAMERA_RESOLUTION}
            )
            
            self.camera.configure(config)
            self.camera.start()
            time.sleep(RPI_CAMERA_WARMUP_TIME)
            
            # Try to set autofocus silently
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
            if len(frame.shape) == 3:
                if frame.shape[2] == 4:  # RGBA format
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                elif frame.shape[2] == 3:  # RGB format
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            return frame
        except Exception as e:
            print(f"⚠️ Error getting frame: {e}")
            return None
    
    def release(self):
        """Release camera resources"""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except:
                pass
        self.initialized = False

# Context manager for safe camera operations
class CameraContext:
    """Context manager that guarantees camera cleanup"""
    def __enter__(self):
        force_camera_cleanup()  # Clean before use
        self.camera = get_camera()
        return self.camera
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        force_camera_cleanup()  # Clean after use
        return False

# Helper to ensure cleanup (simplified)
def ensure_camera_cleanup():
    """Wrapper for force cleanup"""
    force_camera_cleanup()
