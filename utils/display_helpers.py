from utils.gui_helpers import show_message_gui
import time

def show_results_gui(title, message):
    """Show results in GUI message box"""
    show_message_gui(title, message)

def get_num(max_number):
    """Get valid numeric input within range"""
    while True:
        try:
            num = int(input(f"Enter slot ID # from 0-{max_number - 1}: "))
            if 0 <= num < max_number:
                return num
        except ValueError:
            pass
        print("❌ Please enter a valid number.")

def display_menu(menu_config):
    """
    Display a formatted menu from config
    
    Args:
        menu_config (dict): Menu configuration with 'title' and 'options'
    """
    display_separator()
    print(f"\n{menu_config['title']}")
    display_separator()
    
    for option in menu_config['options']:
        print(f"  {option}")
    
    display_separator()

def get_user_input(prompt):
    """Get user input with consistent formatting"""
    return input(f"👉 {prompt}: ").strip()

def confirm_action(message, dangerous=False):
    """Get user confirmation for actions"""
    prompt = f"⚠️ {message} (y/N): " if dangerous else f"❓ {message} (y/N): "
    return input(prompt).strip().lower() == 'y'

def display_separator(title=""):
    """Display formatted separator with optional title"""
    if title:
        print(f"\n{'=' * 60}")
        print(f"🎯 {title}")
        print('=' * 60)
    else:
        print('=' * 60)
        
def display_verification_result(user_info, verification_data):
    """Display verification results for both students and guests"""
    display_separator("VERIFICATION RESULT")
    
    # Common verification checks
    checks = verification_data.get('checks', {})
    for check_name, (status, details) in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{check_name}: {status_icon} {details}")
    
    # User information
    print(f"👤 Name: {user_info['name']}")
    if not user_info.get('is_guest', False):
        print(f"🆔 Student ID: {user_info['student_id']}")
        print(f"📚 Course: {user_info['course']}")
    else:
        print(f"🚗 Plate: {user_info['plate_number']}")
        print(f"🏢 Visiting: {user_info['office']}")
    
    # Overall status
    overall_status = verification_data.get('overall_status', 'UNKNOWN')
    status_color = verification_data.get('status_color', '🔴')
    print(f"\n{status_color} FINAL STATUS: {overall_status}")
    display_separator()
    
    # Show GUI result
    show_results_gui("Verification Complete", verification_data.get('gui_message', ''))

