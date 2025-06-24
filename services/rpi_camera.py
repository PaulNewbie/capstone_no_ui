# services/rpi_camera.py - Fixed with proper cleanup

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
    
# Global camera instance - singleton pattern
_camera_instance = None
_camera_lock = False  # Prevent multiple camera access

def get_camera():
    """Get global camera instance (singleton)"""
    global _camera_instance, _camera_lock
    
    # Wait if camera is locked
    timeout = 10  # 10 second timeout
    start_time = time.time()
    while _camera_lock and (time.time() - start_time < timeout):
        time.sleep(0.1)
    
    if _camera_lock:
        print("⚠️ Camera is locked by another process")
        return None
        
    _camera_lock = True
    
    if _camera_instance is None:
        _camera_instance = RPiCameraService()
    return _camera_instance

def release_camera():
    """Release global camera instance"""
    global _camera_instance, _camera_lock
    if _camera_instance:
        _camera_instance.release()
        _camera_instance = None
    _camera_lock = False

class RPiCameraService:
    def __init__(self):
        self.camera = None
        self.initialized = False
        self.in_use = False
        if RPI_CAMERA_AVAILABLE:
            self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize RPi Camera with suppressed libcamera logs"""
        if not RPI_CAMERA_AVAILABLE:
            raise Exception("RPi Camera not available - picamera2 not installed")
        
        if self.in_use:
            print("⚠️ Camera already in use")
            return False
            
        try:
            # Suppress libcamera verbose logging
            os.environ['LIBCAMERA_LOG_LEVELS'] = 'ERROR'
            
            # Clean up any existing camera instances
            self._force_cleanup()
            
            self.camera = Picamera2()
            
            # Use default configuration
            config = self.camera.create_preview_configuration(
                main={"size": RPI_CAMERA_RESOLUTION}
            )
            
            self.camera.configure(config)
            self.camera.start()
            time.sleep(RPI_CAMERA_WARMUP_TIME)
            
            # Add auto-focus control silently
            try:
                from libcamera import controls
                self.camera.set_controls({
                    "AfMode": controls.AfModeEnum.Continuous,
                    "AfSpeed": controls.AfSpeedEnum.Fast,
                })
                time.sleep(2)
            except Exception:
                pass  # Ignore auto-focus errors silently
            
            self.initialized = True
            self.in_use = True
            return True
            
        except Exception as e:
            self.initialized = False
            self.in_use = False
            self._force_cleanup()
            raise e
    
    def _force_cleanup(self):
        """Force cleanup of any existing camera resources"""
        try:
            # Try to find and stop any existing Picamera2 instances
            if hasattr(self, 'camera') and self.camera:
                try:
                    self.camera.stop()
                    self.camera.close()
                except:
                    pass
            
            # Small delay to ensure resources are freed
            time.sleep(0.5)
        except:
            pass
    
    def get_frame(self):
        """Get current frame from camera"""
        if not self.initialized or not self.camera:
            print("⚠️ Camera not initialized")
            return None
        
        try:
            frame = self.camera.capture_array()
            
            # Convert format appropriately
            if len(frame.shape) == 3:
                if frame.shape[2] == 4:  # RGBA/XRGB format
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                elif frame.shape[2] == 3:  # RGB format
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            return frame
        except Exception as e:
            print(f"⚠️ Error getting frame: {e}")
            return None
    
    def trigger_autofocus(self):
        """Manually trigger auto-focus when needed"""
        if not self.initialized:
            return False
        
        try:
            from libcamera import controls
            self.camera.set_controls({"AfTrigger": controls.AfTriggerEnum.Start})
            time.sleep(1.5)
            return True
        except Exception:
            return False
    
    def capture_image(self, filename=None, with_focus=True):
        """Capture and save image to file"""
        if not self.initialized:
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
        
        try:
            if with_focus:
                self.trigger_autofocus()
            
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
            self.camera.capture_file(filename)
            return filename
            
        except Exception:
            return None
    
    def test_camera(self):
        """Simple camera test"""
        if not self.initialized:
            return False
        
        try:
            frame = self.get_frame()
            return frame is not None
        except Exception:
            return False
    
    def release(self):
        """Release camera resources"""
        self.in_use = False
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                self.camera = None
            except Exception as e:
                print(f"⚠️ Error releasing camera: {e}")
        self.initialized = False
    
    def __del__(self):
        """Destructor to ensure camera is released"""
        self.release()

# Context manager for camera operations
class CameraContext:
    """Context manager for safe camera operations"""
    def __enter__(self):
        self.camera = get_camera()
        return self.camera
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        release_camera()
        # Force cleanup of OpenCV windows
        try:
            cv2.destroyAllWindows()
        except:
            pass
        return False

# Helper function to ensure camera cleanup
def ensure_camera_cleanup():
    """Force cleanup of all camera resources"""
    global _camera_instance, _camera_lock
    
    # Release camera
    release_camera()
    
    # Force OpenCV cleanup
    try:
        cv2.destroyAllWindows()
        # Wait a bit for cleanup
        cv2.waitKey(1)
    except:
        pass
    
    # Reset lock
    _camera_lock = False
    
    print("✅ Camera cleanup completed")
