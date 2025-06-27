# services/rpi_camera.py - Updated with Smart Cleanup Strategy

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

# Global camera instance and state tracking
_camera_instance = None
_camera_state = 'IDLE'  # IDLE, INITIALIZING, ACTIVE, CLEANING
_last_cleanup_time = 0
_cleanup_cooldown = 1.0  # Minimum seconds between cleanups

def force_camera_cleanup():
    """Smart cleanup of camera resources - only cleans when necessary"""
    global _camera_instance, _camera_state, _last_cleanup_time
    
    # Check if cleanup is needed
    current_time = time.time()
    if _camera_state == 'IDLE':
        print("✅ Camera already clean (IDLE state)")
        return
    
    if _camera_state == 'CLEANING':
        print("⏳ Camera cleanup already in progress...")
        return
        
    # Check cooldown period
    if current_time - _last_cleanup_time < _cleanup_cooldown:
        wait_time = _cleanup_cooldown - (current_time - _last_cleanup_time)
        print(f"⏳ Waiting {wait_time:.1f}s before cleanup (cooldown period)")
        time.sleep(wait_time)
    
    # Proceed with cleanup
    _camera_state = 'CLEANING'
    print("🧹 Smart camera cleanup...")
    
    # Destroy any OpenCV windows
    try:
        cv2.destroyAllWindows()
        cv2.waitKey(1)
    except:
        pass
    
    # Release camera instance if it exists
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
    
    # Brief pause for resources to be freed
    time.sleep(0.5)
    
    # Update state
    _camera_state = 'IDLE'
    _last_cleanup_time = time.time()
    print("✅ Camera cleanup completed")

def get_camera():
    """Get camera instance with state tracking"""
    global _camera_instance, _camera_state
    
    # If camera is already active, return it
    if _camera_instance is not None and _camera_state == 'ACTIVE':
        return _camera_instance
    
    # If we're in a bad state, clean up first
    if _camera_state not in ['IDLE', 'ACTIVE']:
        force_camera_cleanup()
    
    # Initialize new camera instance
    if _camera_instance is None:
        _camera_state = 'INITIALIZING'
        _camera_instance = RPiCameraService()
        if _camera_instance.initialized:
            _camera_state = 'ACTIVE'
        else:
            _camera_state = 'IDLE'
            _camera_instance = None
    
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

# Context manager for safe camera operations with smart cleanup
class CameraContext:
    """Context manager that guarantees smart camera cleanup"""
    def __enter__(self):
        # No need to clean before if camera is idle
        if _camera_state != 'IDLE':
            force_camera_cleanup()
        self.camera = get_camera()
        return self.camera
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        force_camera_cleanup()
        return False

# Helper to ensure cleanup
def ensure_camera_cleanup():
    """Wrapper for smart cleanup"""
    force_camera_cleanup()
