# ui/student_gui.py - Complete Student GUI with MINIMAL requested changes only

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from datetime import datetime
import os
from PIL import Image, ImageTk
from typing import Dict
import sys
import queue

class SimpleConsole:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.old_stdout = sys.stdout
        sys.stdout = self
        
    def write(self, text):
        if text.strip():
            self.text_widget.after(0, self.add_text, text)
    
    def add_text(self, text):
        self.text_widget.config(state='normal')
        self.text_widget.insert('end', text + '\n')
        self.text_widget.see('end')
        self.text_widget.config(state='disabled')
        
    def flush(self):
        pass


class StudentVerificationGUI:
    def __init__(self, verification_function):
        self.root = tk.Tk()
        self.verification_function = verification_function
        self.verification_complete = False  # Initialize BEFORE other methods
        self.setup_window()
        self.console = SimpleConsole(self.console_text)
        self.create_variables()
        self.create_interface()
        
    def setup_window(self):
        """Setup the main window"""
        self.root.title("MotorPass - Student/Staff Verification")
        self.root.configure(bg='#8B4513')
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size (90% of screen)
        window_width = int(screen_width * 1)
        window_height = int(screen_height * 0.95)
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Console on the right
        console_frame = tk.Frame(self.root, bg='#2d2d2d')
        console_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        
        tk.Label(console_frame, text="System Console", 
                font=('Arial', 14, 'bold'), 
                bg='#2d2d2d', fg='white').pack()
        
        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            width=40, height=25,
            bg='black', fg='lime',
            font=('Courier', 9),
            state='disabled'
        )
        self.console_text.pack(padx=5, pady=5)
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        
    def create_variables(self):
        """Create all tkinter variables"""
        self.helmet_status = tk.StringVar(value="PENDING")
        self.fingerprint_status = tk.StringVar(value="PENDING") 
        self.license_status = tk.StringVar(value="PENDING")
        self.current_step = tk.StringVar(value="🚀 Starting verification process...")
        self.time_string = tk.StringVar()
        self.date_string = tk.StringVar()
        self.update_time()
        
    def update_time(self):
        """Update time display"""
        try:
            if not hasattr(self, 'root') or not self.root.winfo_exists():
                return
                
            now = datetime.now()
            self.time_string.set(now.strftime("%H:%M:%S"))
            self.date_string.set(now.strftime("%A, %B %d, %Y"))
            
            if not self.verification_complete and self.root.winfo_exists():
                self._update_timer = self.root.after(1000, self.update_time)
        except tk.TclError:
            # Widget has been destroyed
            pass
        except Exception as e:
            # Handle any other errors
            pass
    
    def create_interface(self):
        """Create the main interface"""
        # Main container
        main_container = tk.Frame(self.root, bg='#8B4513')
        main_container.pack(fill="both", expand=True)
        
        # Header
        self.create_header(main_container)
        
        # Content area
        content_frame = tk.Frame(main_container, bg='#8B4513')
        content_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Title
        title_label = tk.Label(content_frame, text="STUDENT/STAFF VERIFICATION", 
                              font=("Arial", 36, "bold"), fg="#FFFFFF", bg='#8B4513')
        title_label.pack(pady=(0, 30))
        
        # Main content panels
        panels_container = tk.Frame(content_frame, bg='#8B4513')
        panels_container.pack(fill="both", expand=True)
        
        # Left panel - Status indicators WITH user info
        self.create_left_panel(panels_container)
        
        # Right panel - Camera Feed (empty)
        self.create_right_panel(panels_container)
        
        # Footer
        self.create_footer(main_container)
        
    def create_header(self, parent):
        """Create header with logo and title"""
        header = tk.Frame(parent, bg='#46230a', height=100)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header, bg='#46230a')
        header_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Logo container
        logo_container = tk.Frame(header_content, bg='#46230a')
        logo_container.pack(side="left", padx=(0, 15))
        
        # Try to load logo
        logo_loaded = False
        logo_paths = ["assets/logo.png", "logo.png", "../assets/logo.png"]
        
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path)
                    logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
                    self.logo_photo = ImageTk.PhotoImage(logo_img)
                    logo_label = tk.Label(logo_container, image=self.logo_photo, bg='#46230a')
                    logo_label.pack()
                    logo_loaded = True
                    break
                except:
                    pass
        
        if not logo_loaded:
            # Fallback text logo
            logo_frame = tk.Frame(logo_container, bg='#DAA520', width=80, height=80)
            logo_frame.pack()
            logo_frame.pack_propagate(False)
            tk.Label(logo_frame, text="MP", font=("Arial", 28, "bold"), 
                    fg="#46230a", bg="#DAA520").place(relx=0.5, rely=0.5, anchor="center")
        
        # Title section
        title_frame = tk.Frame(header_content, bg='#46230a')
        title_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(title_frame, text="MotorPass", font=("Arial", 32, "bold"), 
                fg="#DAA520", bg='#46230a').pack(anchor="w")
        tk.Label(title_frame, text="We secure the safeness of your motorcycle inside our campus",
                font=("Arial", 11), fg="#FFFFFF", bg='#46230a').pack(anchor="w")
        
        # Clock
        clock_frame = tk.Frame(header_content, bg='#46230a', bd=2, relief='solid')
        clock_frame.pack(side="right")
        
        tk.Label(clock_frame, textvariable=self.time_string, font=("Arial", 18, "bold"), 
                fg="#DAA520", bg='#46230a').pack(padx=15, pady=(10, 5))
        tk.Label(clock_frame, textvariable=self.date_string, font=("Arial", 11), 
                fg="#FFFFFF", bg='#46230a').pack(padx=15, pady=(0, 10))

    def create_left_panel(self, parent):
        """Create left panel with status indicators AND user info"""
        left_frame = tk.Frame(parent, bg='#8B4513')
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Status container
        status_container = tk.Frame(left_frame, bg='white', relief='raised', bd=3)
        status_container.pack(fill="both", expand=True)
        
        # Title
        tk.Label(status_container, text="VERIFICATION STATUS", 
                font=("Arial", 20, "bold"), fg="#333333", bg='white').pack(pady=20)
        
        # Status items
        status_items_frame = tk.Frame(status_container, bg='white')
        status_items_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        self.create_status_item(status_items_frame, "🪖 HELMET CHECK:", self.helmet_status, 0)
        self.create_status_item(status_items_frame, "👆 FINGERPRINT:", self.fingerprint_status, 1)
        self.create_status_item(status_items_frame, "🪪 LICENSE CHECK:", self.license_status, 2)
        
        # User authenticated section (moved here from right panel)
        self.user_info_panel = tk.Frame(status_container, bg='#e3f2fd', relief='ridge', bd=2)
        
        tk.Label(self.user_info_panel, text="👤 USER AUTHENTICATED", 
                font=("Arial", 16, "bold"), fg="#1565c0", bg='#e3f2fd').pack(pady=15)
        
        self.user_details_frame = tk.Frame(self.user_info_panel, bg='#e3f2fd')
        self.user_details_frame.pack(padx=20, pady=(0, 20))
        
        # Initially hidden
        self.user_info_panel.pack_forget()

    def create_status_item(self, parent, label_text, status_var, row):
        """Create individual status item with improved design"""
        # Container for this item with better spacing
        item_frame = tk.Frame(parent, bg='white')
        item_frame.pack(fill="x", pady=15)
        
        # Label with improved typography
        tk.Label(item_frame, text=label_text, font=("Arial", 16, "bold"), 
                fg="#333333", bg='white').pack(side="left")
        
        # Status badge with better design
        badge = tk.Label(item_frame, text="PENDING", font=("Arial", 12, "bold"), 
                        fg="#FFFFFF", bg="#95a5a6", padx=20, pady=8, relief='flat')
        badge.pack(side="right", padx=(0, 10))
        
        # Status icon with improved size
        icon_label = tk.Label(item_frame, text="⏸", font=("Arial", 18), 
                             fg="#95a5a6", bg='white')
        icon_label.pack(side="right", padx=(0, 15))
        
        # Store references
        setattr(self, f"badge_{row}", badge)
        setattr(self, f"icon_{row}", icon_label)
        
        # Update display when status changes
        status_var.trace_add("write", lambda *args: self.update_status_display(row, status_var.get()))
    
    def update_status_display(self, row, status):
        """Update status display colors and icons with improved styling"""
        badge = getattr(self, f"badge_{row}", None)
        icon = getattr(self, f"icon_{row}", None)
        
        if not badge or not icon:
            return
            
        status_configs = {
            "VERIFIED": ("#27ae60", "✅", "#27ae60"),      # Green
            "VALID": ("#27ae60", "✅", "#27ae60"),
            "PROCESSING": ("#f39c12", "⏳", "#f39c12"),    # Orange
            "CHECKING": ("#3498db", "🔍", "#3498db"),      # Blue
            "FAILED": ("#e74c3c", "❌", "#e74c3c"),        # Red
            "INVALID": ("#e74c3c", "❌", "#e74c3c"),
            "PENDING": ("#95a5a6", "⏸", "#95a5a6"),        # Gray
            "EXPIRED": ("#e74c3c", "⚠️", "#e74c3c")
        }
        
        config = status_configs.get(status.upper(), ("#95a5a6", "⏸", "#95a5a6"))
        
        # Update badge with improved styling
        badge.config(bg=config[0], text=status.upper(), font=("Arial", 12, "bold"))
        icon.config(text=config[1], fg=config[2], font=("Arial", 18))

    def create_right_panel(self, parent):
        """Create right panel - empty with camera feed title"""
        right_frame = tk.Frame(parent, bg='#8B4513')
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Camera feed container (same size as original details container)
        camera_container = tk.Frame(right_frame, bg='white', relief='raised', bd=3)
        camera_container.pack(fill="both", expand=True)
        
        # Camera feed title
        tk.Label(camera_container, text="📹 CAMERA FEED", 
                font=("Arial", 20, "bold"), fg="#333333", bg='white').pack(pady=20)
        
        # Empty space to maintain size
        empty_frame = tk.Frame(camera_container, bg='white')
        empty_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Optional: Simple message
        tk.Label(empty_frame, text="Terminal Camera Active\nCheck terminal for camera operations", 
                font=("Arial", 14), fg="#666666", bg='white', justify="center").pack(expand=True)

    def create_footer(self, parent):
        """Create footer"""
        footer = tk.Frame(parent, bg='#46230a', height=60)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        footer_text = "🪖 Helmet Check → 🔒 Fingerprint Scan → 📄 License Verification | ESC to exit"
        tk.Label(footer, text=footer_text, font=("Arial", 12), 
                fg="#FFFFFF", bg='#46230a').pack(expand=True)

    def show_user_info(self, user_info):
        """Display user information in LEFT panel"""
        try:
            # Clear previous details
            for widget in self.user_details_frame.winfo_children():
                widget.destroy()
            
            # Create info labels
            info_items = [
                ("Name:", user_info.get('name', 'N/A')),
                ("Student ID:", user_info.get('student_id', 'N/A')),
                ("Course:", user_info.get('course', 'N/A')),
                ("User Type:", user_info.get('user_type', 'STUDENT'))
            ]
            
            for label, value in info_items:
                row = tk.Frame(self.user_details_frame, bg='#e3f2fd')
                row.pack(fill="x", pady=3)
                
                tk.Label(row, text=label, font=("Arial", 12, "bold"), 
                        fg="#333333", bg='#e3f2fd', width=12, anchor="w").pack(side="left")
                tk.Label(row, text=value, font=("Arial", 12), 
                        fg="#1565c0", bg='#e3f2fd').pack(side="left", padx=(10, 0))
            
            # Show the user info panel
            self.user_info_panel.pack(fill="x", pady=(20, 0))
        except Exception as e:
            print(f"Error showing user info: {e}")

    def show_final_result(self, result):
        """Show final verification result with improved design"""
        try:
            self.verification_complete = True
            
            # Result box with yellow background and improved styling
            result_box = tk.Frame(self.root, bg='#FFD700', relief='raised', bd=4)
            result_box.place(relx=0.5, rely=0.5, anchor='center')
            
            # Content with improved spacing
            content = tk.Frame(result_box, bg='#FFD700')
            content.pack(padx=50, pady=35)
            
            if result.get('verified', False):
                # Success
                icon_label = tk.Label(content, text="✅", font=("Arial", 50), bg='#FFD700')
                icon_label.pack(pady=(0, 15))
                
                title = tk.Label(content, text="VERIFICATION SUCCESSFUL", 
                               font=("Arial", 24, "bold"), fg="#2E7D32", bg='#FFD700')
                title.pack(pady=(0, 15))
                
                # Format name
                name = result.get('name', 'User')
                if ',' in name:
                    parts = name.split(',')
                    if len(parts) >= 2:
                        name = f"{parts[1].strip()} {parts[0].strip()}"
                
                welcome = tk.Label(content, text=f"Welcome, {name}!", 
                                 font=("Arial", 18, "bold"), fg="#1B5E20", bg='#FFD700')
                welcome.pack(pady=(0, 10))
                
                # Time action
                time_action = result.get('time_action', 'IN')
                action_text = f"Time {time_action}: {result.get('timestamp', 'N/A')}"
                
                action_label = tk.Label(content, text=action_text, 
                                       font=("Arial", 14), fg="#424242", bg='#FFD700')
                action_label.pack(pady=(0, 5))
                
            else:
                # Failure
                icon_label = tk.Label(content, text="❌", font=("Arial", 50), bg='#FFD700')
                icon_label.pack(pady=(0, 15))
                
                title = tk.Label(content, text="VERIFICATION FAILED", 
                               font=("Arial", 24, "bold"), fg="#C62828", bg='#FFD700')
                title.pack(pady=(0, 15))
                
                reason = tk.Label(content, text=result.get('reason', 'Unknown error'), 
                                font=("Arial", 16), fg="#424242", bg='#FFD700', wraplength=400)
                reason.pack(pady=(0, 10))
            
            # Auto close
            self.root.after(5000, self.close)
            
        except Exception as e:
            print(f"Error showing final result: {e}")
            self.close()

    def update_status(self, updates):
        """Update status from verification thread"""
        try:
            for key, value in updates.items():
                if key == 'helmet_status':
                    self.helmet_status.set(value)
                elif key == 'fingerprint_status':
                    self.fingerprint_status.set(value)
                elif key == 'license_status':
                    self.license_status.set(value)
                elif key == 'current_step':
                    self.current_step.set(value)
                elif key == 'user_info':
                    self.show_user_info(value)
                elif key == 'verification_summary':
                    # Remove verification summary - just pass
                    pass
                elif key == 'final_result':
                    self.show_final_result(value)
        except Exception as e:
            print(f"Error updating status: {e}")

    def start_verification(self):
        """Start verification in separate thread"""
        self.current_step.set("🚀 Initializing verification process...")
        
        # Run verification in thread
        thread = threading.Thread(target=self.run_verification_thread, daemon=True)
        thread.start()

    def run_verification_thread(self):
        """Run verification and update GUI"""
        try:
            # Call the verification function with callback
            result = self.verification_function(self.update_status_callback)
            
            # Show final result
            self.root.after(0, lambda: self.update_status({'final_result': result}))
            
        except Exception as e:
            error_result = {
                'verified': False,
                'reason': f'Error: {str(e)}'
            }
            self.root.after(0, lambda: self.update_status({'final_result': error_result}))

    def update_status_callback(self, status_dict):
        """Callback for status updates"""
        try:
            self.root.after(0, lambda: self.update_status(status_dict))
        except Exception as e:
            print(f"Error in callback: {e}")

    def close(self):
        """Close the GUI"""
        try:
            self.verification_complete = True
            
            # Cancel any pending after callbacks
            if hasattr(self, '_update_timer'):
                self.root.after_cancel(self._update_timer)
                
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error closing GUI: {e}")

    def run(self):
        """Run the GUI"""
        try:
            # Bind escape key
            self.root.bind('<Escape>', lambda e: self.close())
            
            # Start verification after GUI loads
            self.root.after(1000, self.start_verification)
            
            # Start main loop
            self.root.mainloop()
        except Exception as e:
            print(f"Error running GUI: {e}")
            self.close()
