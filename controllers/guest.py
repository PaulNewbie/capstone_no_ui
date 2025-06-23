# Add this function to controllers/guest.py

def run_guest_verification_steps(guest_info, status_callback=None):
    """
    This is a simplified version for the new sequential GUI
    The actual verification happens in the GUI step by step
    """
    # This function is called by the original GUI design
    # But in the new sequential flow, verification is already done
    # So we just process the time in/out
    try:
        from database.db_operations import db
        from services.led_control import set_led_success, set_led_idle
        from services.buzzer_control import play_success, play_failure
        import time
        
        # Check current status
        current_status = db.get_current_status(f"GUEST_{guest_info['plate_number']}")
        
        # Determine time action and record
        if current_status == 'OUT' or current_status is None:
            # TIME IN
            success = record_guest_time_in(guest_info)
            time_action = 'IN'
        else:
            # TIME OUT
            success = record_guest_time_out(guest_info)
            time_action = 'OUT'
        
        if success:
            set_led_success(duration=5.0)
            play_success()
            
            return {
                'name': guest_info['name'],
                'plate_number': guest_info['plate_number'],
                'office': guest_info['office'],
                'time_action': time_action,
                'timestamp': time.strftime('%H:%M:%S'),
                'verified': True
            }
        else:
            set_led_idle()
            play_failure()
            return None
            
    except Exception as e:
        if status_callback:
            status_callback("message", f"❌ System Error: {str(e)}")
        set_led_idle()
        play_failure()
        return None
        
# Update the main guest_verification function to use GUI
def guest_verification():
    """Main guest verification workflow with GUI"""
    try:
        from ui.guest_gui import show_guest_verification_gui
        print("🎫 Starting Guest Verification GUI...")
        show_guest_verification_gui()
    except ImportError as e:
        print(f"❌ GUI not available ({e}), using console mode")
        console_guest_verification()
    except Exception as e:
        print(f"❌ GUI Error: {e}")
        console_guest_verification()
    finally:
        cleanup_camera()
        
def record_guest_time_in(guest_data):
    """
    Record guest time in - wrapper for database function
    guest_data should contain: name, plate_number, office, is_guest=True
    """
    try:
        from database.db_operations import db
        
        # First create/update guest record
        success = db.create_guest_record(
            name=guest_data['name'],
            plate_number=guest_data['plate_number'],
            office=guest_data['office']
        )
        
        if success:
            # Then record time in with GUEST_ prefix
            return db.record_time_in({
                'name': guest_data['name'],
                'student_id': f"GUEST_{guest_data['plate_number']}",
                'is_guest': True
            })
        return False
        
    except Exception as e:
        print(f"Error recording guest time in: {e}")
        return False

def record_guest_time_out(guest_data):
    """
    Record guest time out - wrapper for database function
    """
    try:
        from database.db_operations import db
        
        # Record time out with GUEST_ prefix
        return db.record_time_out({
            'name': guest_data['name'],
            'student_id': f"GUEST_{guest_data['plate_number']}",
            'is_guest': True
        })
        
    except Exception as e:
        print(f"Error recording guest time out: {e}")
        return False

def cleanup_camera():
    """Simple camera cleanup"""
    try:
        import cv2
        cv2.destroyAllWindows()
        
        # Release any camera that might be in use
        for i in range(3):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cap.release()
            except:
                pass
    except:
        pass
        
# Rename the existing guest_verification to console_guest_verification
def console_guest_verification():
    """Console-based guest verification (your existing implementation)"""
    # ... (keep your existing console implementation here)
