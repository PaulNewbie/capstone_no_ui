# ui/guest_gui.py - Guest Verification GUI (Hybrid Approach)

import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime
import os
from PIL import Image, ImageTk

class GuestVerificationGUI:
    def __init__(self, verification_function):
        self.root = tk.Tk()
        self.verification_function = verification_function
        self.verification_complete = False  # Initialize BEFORE other methods
        self.setup_window()
        self.create_variables()
        self.create_interface()
        
    def setup_window(self):
        """Setup the main window"""
        self.root.title("MotorPass - VISITOR Verification")
        self.root.configure(bg='#8B4513')
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = int(screen_width * 1)
        window_height = int(screen_height * 0.95)
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        
    def create_variables(self):
        """Create all tkinter variables"""
        self.helmet_status = tk.StringVar(value="PENDING")
        self.license_status = tk.StringVar(value="PENDING")
        self.current_step = tk.StringVar(value="🚀 Starting visitor verification...")
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
            pass
        except Exception as e:
            # Handle case where GUI is being destroyed
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
        title_label = tk.Label(content_frame, text="VISITOR VERIFICATION", 
                              font=("Arial", 36, "bold"), fg="#FFFFFF", bg='#8B4513')
        title_label.pack(pady=(0, 30))
        
        # Main content panels
        panels_container = tk.Frame(content_frame, bg='#8B4513')
        panels_container.pack(fill="both", expand=True)
        
        # Left panel - Status indicators
        self.create_left_panel(panels_container)
        
        # Right panel - Guest information
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
        tk.Label(title_frame, text="Visitor Access Control System",
                font=("Arial", 11), fg="#FFFFFF", bg='#46230a').pack(anchor="w")
        
        # Clock
        clock_frame = tk.Frame(header_content, bg='#46230a', bd=2, relief='solid')
        clock_frame.pack(side="right")
        
        tk.Label(clock_frame, textvariable=self.time_string, font=("Arial", 18, "bold"), 
                fg="#DAA520", bg='#46230a').pack(padx=15, pady=(10, 5))
        tk.Label(clock_frame, textvariable=self.date_string, font=("Arial", 11), 
                fg="#FFFFFF", bg='#46230a').pack(padx=15, pady=(0, 10))
    
    def create_left_panel(self, parent):
        """Create left panel with status indicators"""
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
        status_items_frame.pack(fill="both", expand=True, padx=30)
        
        self.create_status_item(status_items_frame, "🪖 HELMET CHECK:", self.helmet_status, 0)
        self.create_status_item(status_items_frame, "📄 LICENSE SCAN:", self.license_status, 1)
        
        # Current step
        step_frame = tk.Frame(status_container, bg='#f0f0f0', relief='sunken', bd=1)
        step_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(step_frame, text="Current Process:", font=("Arial", 12, "bold"), 
                fg="#333333", bg='#f0f0f0').pack(anchor="w", padx=15, pady=(15, 5))
        tk.Label(step_frame, textvariable=self.current_step, font=("Arial", 11), 
                fg="#0066CC", bg='#f0f0f0', wraplength=400, justify="left").pack(anchor="w", padx=15, pady=(0, 15))
        
        # Note about camera
        note_frame = tk.Frame(status_container, bg='#fffacd')
        note_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        tk.Label(note_frame, text="📷 Note: Camera operations are shown in terminal window", 
                font=("Arial", 10, "italic"), fg="#666666", bg='#fffacd').pack(padx=10, pady=10)
    
    def create_status_item(self, parent, label, status_var, row):
        """Create a single status item"""
        item_frame = tk.Frame(parent, bg='white')
        item_frame.pack(fill="x", pady=15)
        
        # Label
        tk.Label(item_frame, text=label, font=("Arial", 14, "bold"), 
                fg="#333333", bg='white', width=20, anchor="w").pack(side="left")
        
        # Status badge
        status_frame = tk.Frame(item_frame, bg='white')
        status_frame.pack(side="left", padx=20)
        
        badge = tk.Label(status_frame, textvariable=status_var, font=("Arial", 12, "bold"), 
                        fg="white", bg="#6C757D", padx=20, pady=8, relief="raised", bd=2)
        badge.pack(side="left")
        
        # Icon
        icon_label = tk.Label(status_frame, text="", font=("Arial", 20), bg='white')
        icon_label.pack(side="left", padx=(10, 0))
        
        # Store references
        setattr(self, f"badge_{row}", badge)
        setattr(self, f"icon_{row}", icon_label)
        
        # Update display when status changes
        status_var.trace_add("write", lambda *args: self.update_status_display(row, status_var.get()))
    
    def update_status_display(self, row, status):
        """Update status display colors and icons"""
        badge = getattr(self, f"badge_{row}", None)
        icon = getattr(self, f"icon_{row}", None)
        
        if not badge or not icon:
            return
            
        status_configs = {
            "VERIFIED": ("#28a745", "✓", "#28a745"),
            "DETECTED": ("#28a745", "✓", "#28a745"),
            "PROCESSING": ("#FFA500", "⏳", "#FFA500"),
            "CHECKING": ("#17a2b8", "🔍", "#17a2b8"),
            "FAILED": ("#DC3545", "❌", "#DC3545"),
            "NOT DETECTED": ("#DC3545", "❌", "#DC3545"),
            "PENDING": ("#6C757D", "⏸", "#6C757D")
        }
        
        config = status_configs.get(status.upper(), ("#6C757D", "", "#6C757D"))
        badge.config(bg=config[0])
        icon.config(text=config[1], fg=config[2])
    
    def create_right_panel(self, parent):
        """Create right panel with guest information"""
        right_frame = tk.Frame(parent, bg='#8B4513')
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Details container
        details_container = tk.Frame(right_frame, bg='white', relief='raised', bd=3)
        details_container.pack(fill="both", expand=True)
        
        # Title
        tk.Label(details_container, text="VISITOR INFORMATION", 
                font=("Arial", 20, "bold"), fg="#333333", bg='white').pack(pady=20)
        
        # Details content
        self.details_content = tk.Frame(details_container, bg='white')
        self.details_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Initial message
        self.initial_message = tk.Label(self.details_content, 
                                       text="Starting visitor verification...\nPlease check the terminal window for camera operations.",
                                       font=("Arial", 14), fg="#666666", bg='white', justify="center")
        self.initial_message.pack(expand=True)
        
        # Hidden panels for later use
        self.create_hidden_panels()
    
    def create_hidden_panels(self):
        """Create panels that will be shown later"""
        # Guest info panel
        self.guest_info_panel = tk.Frame(self.details_content, bg='#e8f5e9', relief='ridge', bd=2)
        
        tk.Label(self.guest_info_panel, text="👤 GUEST DETAILS", 
                font=("Arial", 16, "bold"), fg="#2e7d32", bg='#e8f5e9').pack(pady=15)
        
        self.guest_details_frame = tk.Frame(self.guest_info_panel, bg='#e8f5e9')
        self.guest_details_frame.pack(padx=20, pady=(0, 20))
        
        # Verification summary panel
        self.summary_panel = tk.Frame(self.details_content, bg='#f5f5f5', relief='ridge', bd=2)
        
        tk.Label(self.summary_panel, text="🎯 VERIFICATION SUMMARY", 
                font=("Arial", 16, "bold"), fg="#333333", bg='#f5f5f5').pack(pady=15)
        
        self.summary_frame = tk.Frame(self.summary_panel, bg='#f5f5f5')
        self.summary_frame.pack(padx=20, pady=(0, 20))
    
    def create_footer(self, parent):
        """Create footer"""
        footer = tk.Frame(parent, bg='#46230a', height=60)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        footer_text = "🪖 Helmet Required → 📄 License Scan → 📝 Visitor Registration | ESC to exit"
        tk.Label(footer, text=footer_text, font=("Arial", 12), 
                fg="#FFFFFF", bg='#46230a').pack(expand=True)
    
    def show_guest_info(self, guest_info):
        """Display guest information"""
        try:
            self.initial_message.pack_forget()
            
            # Clear previous details
            for widget in self.guest_details_frame.winfo_children():
                widget.destroy()
            
            # Create info labels
            info_items = [
                ("Name:", guest_info.get('name', 'Guest')),
                ("Plate Number:", guest_info.get('plate_number', 'N/A')),
                ("Office Visiting:", guest_info.get('office', 'N/A')),
                ("Status:", guest_info.get('status', 'NEW GUEST'))
            ]
            
            # Add guest number if returning guest
            if 'guest_number' in guest_info:
                info_items.insert(1, ("Guest No:", guest_info.get('guest_number', 'N/A')))
            
            for label, value in info_items:
                row = tk.Frame(self.guest_details_frame, bg='#e8f5e9')
                row.pack(fill="x", pady=3)
                
                tk.Label(row, text=label, font=("Arial", 12, "bold"), 
                        fg="#333333", bg='#e8f5e9', width=15, anchor="w").pack(side="left")
                tk.Label(row, text=value, font=("Arial", 12), 
                        fg="#2e7d32", bg='#e8f5e9').pack(side="left", padx=(10, 0))
            
            self.guest_info_panel.pack(fill="x", pady=10)
        except Exception as e:
            print(f"Error showing guest info: {e}")
    
    def show_verification_summary(self, results):
        """Display verification summary"""
        try:
            # Clear previous summary
            for widget in self.summary_frame.winfo_children():
                widget.destroy()
            
            # Create summary items
            checks = [
                ("Helmet Verification", results.get('helmet', False)),
                ("License Detection", results.get('license', False))
            ]
            
            for check_name, passed in checks:
                row = tk.Frame(self.summary_frame, bg='#f5f5f5')
                row.pack(fill="x", pady=5)
                
                # Icon
                icon = "✅" if passed else "❌"
                color = "#28a745" if passed else "#dc3545"
                
                tk.Label(row, text=icon, font=("Arial", 16), 
                        fg=color, bg='#f5f5f5').pack(side="left")
                
                tk.Label(row, text=check_name, font=("Arial", 12), 
                        fg="#333333", bg='#f5f5f5').pack(side="left", padx=(10, 0))
                
                status_text = "PASSED" if passed else "FAILED"
                tk.Label(row, text=f"[{status_text}]", font=("Arial", 11, "bold"), 
                        fg=color, bg='#f5f5f5').pack(side="right")
            
            self.summary_panel.pack(fill="x", pady=10)
        except Exception as e:
            print(f"Error showing verification summary: {e}")
    
    def show_final_result(self, result):
        """Show final verification result"""
        try:
            self.verification_complete = True
            
            # Create overlay
            overlay = tk.Frame(self.root, bg='#333333')
            overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # Result box
            result_box = tk.Frame(overlay, bg='white', relief='solid', bd=3)
            result_box.place(relx=0.5, rely=0.5, anchor='center')
            
            # Content
            content = tk.Frame(result_box, bg='white')
            content.pack(padx=60, pady=40)
            
            if result.get('verified', False):
                # Success
                icon_label = tk.Label(content, text="✅", font=("Arial", 60), bg='white')
                icon_label.pack()
                
                title = tk.Label(content, text="VISITOR ACCESS GRANTED", 
                               font=("Arial", 28, "bold"), fg="#28a745", bg='white')
                title.pack(pady=(20, 10))
                
                name = result.get('name', 'Guest')
                welcome = tk.Label(content, text=f"Welcome, {name}!", 
                                 font=("Arial", 18), fg="#333333", bg='white')
                welcome.pack(pady=10)
                
                # Time status
                time_action = result.get('time_action', 'IN')
                time_color = "#28a745" if time_action == 'IN' else "#dc3545"
                time_text = f"TIME {time_action} recorded at {result.get('timestamp', 'now')}"
                
                time_label = tk.Label(content, text=time_text, 
                                    font=("Arial", 16, "bold"), fg=time_color, bg='white')
                time_label.pack(pady=10)
                
                # Office info if available
                if 'office' in result:
                    office_label = tk.Label(content, text=f"Visiting: {result['office']}", 
                                          font=("Arial", 14), fg="#666666", bg='white')
                    office_label.pack(pady=5)
                
            else:
                # Failure
                icon_label = tk.Label(content, text="❌", font=("Arial", 60), bg='white')
                icon_label.pack()
                
                title = tk.Label(content, text="ACCESS DENIED", 
                               font=("Arial", 28, "bold"), fg="#dc3545", bg='white')
                title.pack(pady=(20, 10))
                
                reason = result.get('reason', 'Verification requirements not met')
                reason_label = tk.Label(content, text=reason, 
                                      font=("Arial", 14), fg="#666666", bg='white', 
                                      wraplength=400, justify="center")
                reason_label.pack(pady=10)
            
            # Auto close after 3 seconds
            self.root.after(3000, self.close)
        except Exception as e:
            print(f"Error showing final result: {e}")
            self.close()
    
    def update_status(self, updates):
        """Update status from verification thread"""
        try:
            for key, value in updates.items():
                if key == 'helmet_status':
                    self.helmet_status.set(value)
                elif key == 'license_status':
                    self.license_status.set(value)
                elif key == 'current_step':
                    self.current_step.set(value)
                elif key == 'guest_info':
                    self.show_guest_info(value)
                elif key == 'verification_summary':
                    self.show_verification_summary(value)
                elif key == 'final_result':
                    self.show_final_result(value)
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def start_verification(self):
        """Start verification in separate thread"""
        self.current_step.set("🚀 Initializing visitor verification...")
        
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
            
            if hasattr(self, '_update_time'):
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
