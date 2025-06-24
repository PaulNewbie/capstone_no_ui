#!/usr/bin/env python3
# camera_cleanup.py - Script to clean up camera processes

import subprocess
import time
import os
import signal
import psutil

def kill_camera_processes():
    """Kill processes that might be using the camera"""
    
    print("🔄 Cleaning up camera processes...")
    
    # List of process names that might use camera
    camera_processes = [
        'python3',
        'python',
        'opencv',
        'cheese',
        'guvcview',
        'vlc',
        'ffmpeg',
        'gstreamer'
    ]
    
    killed_processes = []
    
    try:
        # Get all running processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                process_info = proc.info
                process_name = process_info['name'].lower()
                cmdline = ' '.join(process_info['cmdline']) if process_info['cmdline'] else ''
                
                # Check if process might be using camera
                is_camera_process = False
                
                # Check process name
                for cam_proc in camera_processes:
                    if cam_proc in process_name:
                        # Additional check for python processes
                        if 'python' in process_name:
                            if any(keyword in cmdline.lower() for keyword in ['camera', 'cv2', 'opencv', 'motorpass']):
                                is_camera_process = True
                                break
                        else:
                            is_camera_process = True
                            break
                
                if is_camera_process:
                    try:
                        print(f"🔪 Killing process: {process_name} (PID: {process_info['pid']})")
                        proc.kill()
                        killed_processes.append(f"{process_name} (PID: {process_info['pid']})")
                        time.sleep(0.1)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    
    except Exception as e:
        print(f"❌ Error during process cleanup: {e}")
    
    # System-specific camera cleanup
    try:
        # Linux specific - release video devices
        if os.name == 'posix':
            # Try to reset USB video devices
            for i in range(4):
                device_path = f"/dev/video{i}"
                if os.path.exists(device_path):
                    try:
                        # This might help release the device
                        subprocess.run(['fuser', '-k', device_path], 
                                     capture_output=True, timeout=5)
                    except:
                        pass
    except:
        pass
    
    if killed_processes:
        print(f"✅ Killed {len(killed_processes)} camera processes:")
        for proc in killed_processes:
            print(f"   - {proc}")
    else:
        print("ℹ️ No camera processes found to kill")
    
    # Wait for processes to fully terminate
    time.sleep(1)
    
    return len(killed_processes)

def reset_camera_permissions():
    """Reset camera device permissions (Linux only)"""
    if os.name != 'posix':
        return
    
    try:
        print("🔄 Resetting camera permissions...")
        
        for i in range(4):
            device_path = f"/dev/video{i}"
            if os.path.exists(device_path):
                try:
                    # Try to change permissions
                    subprocess.run(['sudo', 'chmod', '666', device_path], 
                                 capture_output=True, timeout=5)
                    print(f"✅ Reset permissions for {device_path}")
                except Exception as e:
                    print(f"⚠️ Could not reset permissions for {device_path}: {e}")
    except Exception as e:
        print(f"❌ Error resetting permissions: {e}")

def main():
    """Main cleanup function"""
    print("🧹 Camera Cleanup Tool")
    print("="*50)
    
    # Kill camera processes
    killed_count = kill_camera_processes()
    
    # Reset permissions (Linux only)
    reset_camera_permissions()
    
    print("="*50)
    print(f"✅ Cleanup completed - {killed_count} processes terminated")
    print("🔄 Camera should now be available for use")

if __name__ == "__main__":
    main()
