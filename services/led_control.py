# services/led_control.py - Clean LED control with simple config check

import RPi.GPIO as GPIO
import time
import threading
from enum import Enum
from config import ENABLE_LED

# Disable GPIO warnings
GPIO.setwarnings(False)

class LEDState(Enum):
    IDLE = "idle"           # Blinking red
    PROCESSING = "processing"  # Solid red
    SUCCESS = "success"     # Solid green
    OFF = "off"            # All lights off

class LEDController:
    def __init__(self, red_pin=18, green_pin=16, blink_interval=0.5):
        
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blink_interval = blink_interval
        
        self.current_state = LEDState.OFF
        self.blink_thread = None
        self.stop_blink = threading.Event()
        
        if not ENABLE_LED:
            return
        
        # Clean up any existing GPIO setup first
        try:
            GPIO.cleanup([self.red_pin, self.green_pin])
        except:
            pass
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        
        # Initialize LEDs to OFF
        GPIO.output(self.red_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.LOW)
    
    def _blink_red(self):
        """Internal method to handle red LED blinking"""
        if not ENABLE_LED:
            return
        while not self.stop_blink.is_set():
            if self.current_state == LEDState.IDLE:
                GPIO.output(self.red_pin, GPIO.HIGH)
                if self.stop_blink.wait(self.blink_interval):
                    break
                GPIO.output(self.red_pin, GPIO.LOW)
                if self.stop_blink.wait(self.blink_interval):
                    break
            else:
                break
    
    def set_state(self, state: LEDState, duration=None):
        """
        Set LED state
        
        Args:
            state (LEDState): Target LED state
            duration (float, optional): Auto-return to idle after duration (seconds)
        """
        if not ENABLE_LED:
            return
            
        # Stop any ongoing blinking
        self.stop_blink.set()
        if self.blink_thread and self.blink_thread.is_alive():
            self.blink_thread.join(timeout=1.0)
        
        self.current_state = state
        self.stop_blink.clear()
        
        if state == LEDState.IDLE:
            # Start blinking red
            GPIO.output(self.green_pin, GPIO.LOW)
            self.blink_thread = threading.Thread(target=self._blink_red, daemon=True)
            self.blink_thread.start()
            
        elif state == LEDState.PROCESSING:
            # Solid red
            GPIO.output(self.red_pin, GPIO.HIGH)
            GPIO.output(self.green_pin, GPIO.LOW)
            
        elif state == LEDState.SUCCESS:
            # Solid green
            GPIO.output(self.red_pin, GPIO.LOW)
            GPIO.output(self.green_pin, GPIO.HIGH)
            
        elif state == LEDState.OFF:
            # All off
            GPIO.output(self.red_pin, GPIO.LOW)
            GPIO.output(self.green_pin, GPIO.LOW)
        
        # Auto-return to idle after duration
        if duration and state != LEDState.IDLE:
            def auto_return():
                time.sleep(duration)
                if self.current_state == state:  # Only return if state hasn't changed
                    self.set_state(LEDState.IDLE)
            
            threading.Thread(target=auto_return, daemon=True).start()
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if not ENABLE_LED:
            return
        self.stop_blink.set()
        if self.blink_thread and self.blink_thread.is_alive():
            self.blink_thread.join(timeout=1.0)
        
        GPIO.output(self.red_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.LOW)
        GPIO.cleanup([self.red_pin, self.green_pin])

# Global LED controller instance
led_controller = None

def init_led_system(red_pin=18, green_pin=16):
    """Initialize the global LED controller"""
    if not ENABLE_LED:
        return True
        
    global led_controller
    try:
        # Clean up existing controller if it exists
        if led_controller:
            led_controller.cleanup()
        
        led_controller = LEDController(red_pin, green_pin)
        return True
    except Exception as e:
        print(f"LED init error: {e}")
        return False

def set_led_idle():
    """Set LED to idle state (blinking red)"""
    if ENABLE_LED and led_controller:
        led_controller.set_state(LEDState.IDLE)

def set_led_processing():
    """Set LED to processing state (solid red)"""
    if ENABLE_LED and led_controller:
        led_controller.set_state(LEDState.PROCESSING)

def set_led_success(duration=3.0):
    """Set LED to success state (solid green) with auto-return to idle"""
    if ENABLE_LED and led_controller:
        led_controller.set_state(LEDState.SUCCESS, duration)

def set_led_off():
    """Turn off all LEDs"""
    if ENABLE_LED and led_controller:
        led_controller.set_state(LEDState.OFF)

def cleanup_led_system():
    """Clean up LED system resources"""
    if not ENABLE_LED:
        return
    global led_controller
    if led_controller:
        led_controller.cleanup()
        led_controller = None

# Context manager for automatic cleanup
class LEDManager:
    def __init__(self, red_pin=18, green_pin=16):
        self.red_pin = red_pin
        self.green_pin = green_pin
    
    def __enter__(self):
        init_led_system(self.red_pin, self.green_pin)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup_led_system()

# Example usage and testing
if __name__ == "__main__":
    print("🔴🟢 LED Control System Test")
    
    try:
        with LEDManager() as leds:
            print("Testing LED states...")
            
            # Test idle (blinking red)
            print("1. Testing IDLE state (blinking red)...")
            set_led_idle()
            time.sleep(5)
            
            # Test processing (solid red)
            print("2. Testing PROCESSING state (solid red)...")
            set_led_processing()
            time.sleep(3)
            
            # Test success (solid green)
            print("3. Testing SUCCESS state (solid green)...")
            set_led_success(duration=3)
            time.sleep(4)  # Wait for auto-return to idle
            
            # Test manual off
            print("4. Testing OFF state...")
            set_led_off()
            time.sleep(2)
            
            print("✅ LED test completed!")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
