# services/buzzer_control.py - Clean and Simple Buzzer Control with Config Check
import RPi.GPIO as GPIO
import time
import threading
from config import ENABLE_BUZZER

# Disable GPIO warnings
GPIO.setwarnings(False)

class BuzzerController:
    def __init__(self, buzzer_pin=22):
        self.buzzer_pin = buzzer_pin
        self.is_playing = False
        
        if not ENABLE_BUZZER:
            return
        
        # Clean up any existing GPIO setup
        try:
            GPIO.cleanup([self.buzzer_pin])
        except:
            pass
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.buzzer_pin, GPIO.OUT)
        GPIO.output(self.buzzer_pin, GPIO.LOW)
    
    def simple_beep(self, duration=0.2):
        """Simple clean beep - no PWM, just on/off"""
        if not ENABLE_BUZZER:
            return
        try:
            GPIO.output(self.buzzer_pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
        except Exception as e:
            print(f"⚠️ Buzzer error: {e}")
    
    def play_pattern(self, pattern_name):
        """Play simple patterns without threading complications"""
        if not ENABLE_BUZZER or self.is_playing:
            return
        
        self.is_playing = True
        
        try:
            if pattern_name == "processing":
                # Two quick beeps
                self.simple_beep(0.1)
                time.sleep(0.1)
                self.simple_beep(0.1)
                
            elif pattern_name == "success":
                # Three ascending beeps
                self.simple_beep(0.1)
                time.sleep(0.05)
                self.simple_beep(0.1)
                time.sleep(0.05)
                self.simple_beep(0.15)
                
            elif pattern_name == "failure":
                # One longer beep
                self.simple_beep(2)
                
        except Exception as e:
            print(f"⚠️ Pattern error: {e}")
        finally:
            self.is_playing = False
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if not ENABLE_BUZZER:
            return
        try:
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            GPIO.cleanup([self.buzzer_pin])
        except:
            pass

# Global buzzer controller instance
buzzer_controller = None

def init_buzzer(pin=22):
    """Initialize the buzzer controller"""
    if not ENABLE_BUZZER:
        return True
        
    global buzzer_controller
    try:
        if buzzer_controller:
            buzzer_controller.cleanup()
        
        buzzer_controller = BuzzerController(pin)
        
        # Test with simple beep
        buzzer_controller.simple_beep(0.1)
        
        print(f"✅ Buzzer initialized on pin {pin}")
        return True
    except Exception as e:
        print(f"❌ Buzzer init error: {e}")
        return False

# Simple functions - only the 3 you need
def play_processing():
    """Start/processing sound"""
    if ENABLE_BUZZER and buzzer_controller:
        buzzer_controller.play_pattern("processing")

def play_success():
    """Success sound"""
    if ENABLE_BUZZER and buzzer_controller:
        buzzer_controller.play_pattern("success")

def play_failure():
    """Failure sound"""
    if ENABLE_BUZZER and buzzer_controller:
        buzzer_controller.play_pattern("failure")

# Aliases for convenience
def play_ready():
    """System ready - same as processing"""
    play_processing()

def cleanup_buzzer():
    """Clean up buzzer system resources"""
    if not ENABLE_BUZZER:
        return
    global buzzer_controller
    if buzzer_controller:
        buzzer_controller.cleanup()
        buzzer_controller = None

# Test function
if __name__ == "__main__":
    print("🔊 Simple Buzzer Test")
    
    if init_buzzer():
        print("Testing sounds...")
        
        print("1. Processing...")
        play_processing()
        time.sleep(2)
        
        print("2. Success...")
        play_success()
        time.sleep(2)
        
        print("3. Failure...")
        play_failure()
        time.sleep(2)
        
        print("✅ Test complete!")
        cleanup_buzzer()
    else:
        print("❌ Buzzer test failed!")
