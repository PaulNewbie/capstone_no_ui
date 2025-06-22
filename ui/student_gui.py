# ui/student_verification_gui.py - Updated GUI with License Retry Support

import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime

class StudentVerificationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_variables()
        self.create_interface()
        
    def setup_window(self):
        self.root.title("MotorPass - Student Verification")
        self.root.configure(bg='#8B4513')
        self.root.resizable(False, False)
        
        # Force fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Alternative fullscreen methods for different systems
        try:
            self.root.state('zoomed')
        except:
            try:
                self.root.attributes('-zoomed', True)
            except:
                # Fallback to manual fullscreen
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
    
    def create_variables(self):
        self.helmet_status = tk.StringVar(value="PENDING")
        self.fingerprint_status = tk.StringVar(value="PENDING") 
        self.license_status = tk.StringVar(value="PENDING")
        self.current_step = tk.StringVar(value="🪖 Ready to start verification")
        self.student_info = {}
        self.license_retry_count = 0  # Track license retries
        
    def create_interface(self):
        # Header
        header = tk.Frame(self.root, bg='#46230a', height=100)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#46230a')
        header_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Logo
        logo = tk.Label(header_content, text="MP", font=("Arial", 20, "bold"), 
                       fg="#DAA520", bg="#46230a", width=4, height=2)
        logo.pack(side="left", padx=(0, 15))
        
        # Title
        title_frame = tk.Frame(header_content, bg='#46230a')
        title_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(title_frame, text="MotorPass", font=("Arial", 32, "bold"), 
                fg="#DAA520", bg='#46230a').pack(anchor="w")
        tk.Label(title_frame, text="We secure the safeness of your motorcycle inside our campus",
                font=("Arial", 11), fg="#FFFFFF", bg='#46230a').pack(anchor="w")
        
        # Time
        self.time_frame = tk.Frame(header_content, bg='#46230a')
        self.time_frame.pack(side="right")
        self.time_label = tk.Label(self.time_frame, font=("Arial", 14, "bold"), 
                                  fg="#DAA520", bg='#46230a')
        self.time_label.pack()
        self.date_label = tk.Label(self.time_frame, font=("Arial", 10), 
                                  fg="#FFFFFF", bg='#46230a')
        self.date_label.pack()
        self.update_time()
        
        # Main content
        main = tk.Frame(self.root, bg='#8B4513')
        main.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Title
        tk.Label(main, text="STUDENT ENTRY", font=("Arial", 36, "bold"), 
                fg="#FFFFFF", bg='#8B4513').pack(pady=(0, 20))
        
        # Content container
        content = tk.Frame(main, bg='#8B4513')
        content.pack(fill="both", expand=True)
        
        # Left panel - Verification status
        self.create_left_panel(content)
        
        # Right panel - Process Information
        self.create_right_panel(content)
        
        # Footer
        footer = tk.Frame(self.root, bg='#46230a', height=60)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        tk.Label(footer, text="📱 Follow verification steps • 🪖 Full-face helmet required • 🤚 Finger ready • 🆔 License ready • ESC to exit",
                font=("Arial", 12), fg="#FFFFFF", bg='#46230a').pack(expand=True)
    
    def create_left_panel(self, parent):
        left = tk.Frame(parent, bg='#8B4513')
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Status container
        status_container = tk.Frame(left, bg='white', relief='raised', bd=3)
        status_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Status items
        self.create_status_row(status_container, "HELMET TYPE:", self.helmet_status, 0)
        self.create_status_row(status_container, "FINGERPRINT:", self.fingerprint_status, 1)
        self.create_status_row(status_container, "LICENSE EXP:", self.license_status, 2)
        
        # License retry indicator (initially hidden)
        self.retry_frame = tk.Frame(status_container, bg='white')
        self.retry_label = tk.Label(self.retry_frame, text="", font=("Arial", 11, "bold"), 
                                   fg="#ff6600", bg='white')
        self.retry_label.pack()
        
        # Current step
        step_frame = tk.Frame(status_container, bg='white')
        step_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        
        tk.Label(step_frame, text="Current Step:", font=("Arial", 12, "bold"), 
                fg="#333333", bg='white').pack(anchor="w")
        tk.Label(step_frame, textvariable=self.current_step, font=("Arial", 11), 
                fg="#0066CC", bg='white', wraplength=400).pack(anchor="w", pady=(5, 0))
        
        # Buttons
        btn_frame = tk.Frame(status_container, bg='white')
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        
        self.start_btn = tk.Button(btn_frame, text="🚀 START VERIFICATION", 
                                  font=("Arial", 14, "bold"), bg="#DAA520", fg="#333333",
                                  padx=30, pady=15, command=self.start_verification)
        self.start_btn.pack(side="left", padx=(0, 10))
        
        tk.Button(btn_frame, text="❌ CANCEL", font=("Arial", 14, "bold"), 
                 bg="#8B4513", fg="white", padx=30, pady=15, 
                 command=self.close).pack(side="right")
    
    def create_status_row(self, parent, label_text, status_var, row):
        tk.Label(parent, text=label_text, font=("Arial", 16, "bold"), 
                fg="#333333", bg='white').grid(row=row, column=0, sticky="w", padx=20, pady=15)
        
        status_frame = tk.Frame(parent, bg='white')
        status_frame.grid(row=row, column=1, sticky="w", padx=20, pady=15)
        
        button = tk.Label(status_frame, textvariable=status_var, font=("Arial", 14, "bold"), 
                         fg="white", padx=20, pady=8, relief="raised", bd=2)
        button.pack(side="left")
        
        icon = tk.Label(status_frame, text="", font=("Arial", 20), fg="#28a745", bg='white')
        icon.pack(side="left", padx=(10, 0))
        
        # Store references and bind updates
        setattr(self, f"status_btn_{row}", button)
        setattr(self, f"status_icon_{row}", icon)
        status_var.trace_add("write", lambda *args, r=row: self.update_status_display(r, status_var.get()))
        self.update_status_display(row, "PENDING")
    
    def create_right_panel(self, parent):
        right = tk.Frame(parent, bg='#8B4513')
        right.pack(side="right", fill="both", expand=True)
        
        # Process Information container
        process_container = tk.Frame(right, bg='white', relief='raised', bd=3)
        process_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(process_container, text="📋 VERIFICATION STATUS", 
                font=("Arial", 18, "bold"), fg="#333333", bg='white').pack(pady=15)
        
        # Current process details - larger now
        details_frame = tk.Frame(process_container, bg='#f8f9fa', relief='sunken', bd=2)
        details_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(details_frame, text="Current Status:", font=("Arial", 14, "bold"), 
                fg="#333333", bg='#f8f9fa').pack(anchor="w", padx=15, pady=(15, 8))
        
        self.process_details = tk.Label(details_frame, text="Ready to start verification process...", 
                                       font=("Arial", 12), fg="#0066CC", bg='#f8f9fa', 
                                       wraplength=450, justify="left")
        self.process_details.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Authentication details panel (initially hidden)
        self.auth_panel = tk.Frame(process_container, bg='#e3f2fd', relief='ridge', bd=2)
        
        # Student info display (for successful authentication)
        self.student_card = tk.Frame(self.auth_panel, bg='#e3f2fd')
        self.student_card.pack(fill="x", padx=20, pady=15)
        
        # Authentication status
        self.auth_status = tk.Label(self.auth_panel, font=("Arial", 14, "bold"), 
                                   bg='#e3f2fd', pady=8)
        self.auth_status.pack()
        
        # Student details
        self.student_name = tk.Label(self.student_card, font=("Arial", 13, "bold"), 
                                    fg="#1565c0", bg='#e3f2fd')
        self.student_name.pack(anchor="w", pady=3)
        
        self.student_id = tk.Label(self.student_card, font=("Arial", 12), 
                                  fg="#333333", bg='#e3f2fd')
        self.student_id.pack(anchor="w", pady=2)
        
        self.student_course = tk.Label(self.student_card, font=("Arial", 12), 
                                      fg="#333333", bg='#e3f2fd')
        self.student_course.pack(anchor="w", pady=2)
        
        self.confidence_info = tk.Label(self.student_card, font=("Arial", 11), 
                                       fg="#666666", bg='#e3f2fd')
        self.confidence_info.pack(anchor="w", pady=3)
        
        # Verification results panel (initially hidden)
        self.verification_panel = tk.Frame(process_container, bg='#f5f5f5', relief='ridge', bd=2)
        
        tk.Label(self.verification_panel, text="🎯 VERIFICATION SUMMARY", 
                font=("Arial", 15, "bold"), fg="#333333", bg='#f5f5f5').pack(pady=12)
        
        self.verification_grid = tk.Frame(self.verification_panel, bg='#f5f5f5')
        self.verification_grid.pack(fill="x", padx=25, pady=15)
        
        # Final result panel (initially hidden)
        self.result_panel = tk.Frame(process_container, relief='raised', bd=3)
        
        self.result_status = tk.Label(self.result_panel, font=("Arial", 17, "bold"), pady=20)
        self.result_status.pack()
        
        # Final student info for successful verification
        self.final_info = tk.Frame(self.result_panel)
        
        self.name_label = tk.Label(self.final_info, font=("Arial", 13, "bold"))
        self.name_label.pack(anchor="w", pady=3)
        
        self.id_label = tk.Label(self.final_info, font=("Arial", 12))
        self.id_label.pack(anchor="w", pady=2)
        
        self.course_label = tk.Label(self.final_info, font=("Arial", 12))
        self.course_label.pack(anchor="w", pady=2)
        
        self.license_label = tk.Label(self.final_info, font=("Arial", 12))
        self.license_label.pack(anchor="w", pady=2)
        
        self.time_action_label = tk.Label(self.final_info, font=("Arial", 13, "bold"))
        self.time_action_label.pack(anchor="w", pady=8)
    
    def show_authentication_success(self, student_info, confidence):
        """Display student authentication details"""
        self.auth_status.config(text="✅ AUTHENTICATION SUCCESSFUL", fg="#28a745")
        
        # Format name properly
        name = student_info.get('name', 'Unknown Student')
        if ',' in name:  # Handle "LASTNAME, FIRSTNAME" format
            parts = name.split(',')
            if len(parts) == 2:
                name = f"{parts[1].strip()} {parts[0].strip()}"
        
        self.student_name.config(text=f"👤 Welcome, {name}")
        self.student_id.config(text=f"🆔 Student ID: {student_info.get('student_id', 'N/A')}")
        self.student_course.config(text=f"📚 Course: {student_info.get('course', 'N/A')}")
        
        # Show confidence with appropriate color
        confidence_val = int(confidence)
        if confidence_val >= 80:
            conf_color = "#28a745"  # Green
            conf_text = "Excellent"
        elif confidence_val >= 60:
            conf_color = "#ffc107"  # Yellow
            conf_text = "Good"
        else:
            conf_color = "#dc3545"  # Red
            conf_text = "Low"
            
        self.confidence_info.config(text=f"🎯 Match Confidence: {confidence_val}% ({conf_text})", 
                                   fg=conf_color)
        
        self.auth_panel.pack(fill="x", padx=20, pady=15)
    
    def show_verification_results(self, results):
        """Display verification results in a clean grid"""
        # Clear previous results
        for widget in self.verification_grid.winfo_children():
            widget.destroy()
        
        checks = [
            ("🪖 Helmet Check", results.get('helmet', False)),
            ("🔒 Fingerprint", results.get('fingerprint', False)),
            ("📅 License Valid", results.get('license_valid', False)),
            ("🆔 License Detected", results.get('license_detected', False)),
            ("👤 Name Match", results.get('name_match', False))
        ]
        
        for i, (check_name, passed) in enumerate(checks):
            row = i // 2
            col = i % 2
            
            check_frame = tk.Frame(self.verification_grid, bg='#f5f5f5')
            check_frame.grid(row=row, column=col, sticky="w", padx=15, pady=8)
            
            # Status icon - bigger
            icon = "✅" if passed else "❌"
            icon_color = "#28a745" if passed else "#dc3545"
            
            tk.Label(check_frame, text=icon, font=("Arial", 16), 
                    fg=icon_color, bg='#f5f5f5').pack(side="left")
            
            tk.Label(check_frame, text=check_name, font=("Arial", 12), 
                    fg="#333333", bg='#f5f5f5').pack(side="left", padx=(8, 0))
        
        self.verification_panel.pack(fill="x", padx=20, pady=15)
    
    def update_status_display(self, row, status):
        button = getattr(self, f"status_btn_{row}")
        icon = getattr(self, f"status_icon_{row}")
        
        colors = {
            "VERIFIED": ("#28a745", "✓"), "VALID": ("#28a745", "✓"),
            "PROCESSING": ("#FFA500", "⏳"), "FAILED": ("#DC3545", "❌"),
            "PENDING": ("#6C757D", ""), "RETRYING": ("#ff8c00", "🔄")
        }
        
        color, symbol = colors.get(status, ("#6C757D", ""))
        button.config(bg=color, text=status)
        icon.config(text=symbol)
        
        # Special handling for license retries
        if row == 2 and status == "PROCESSING":  # License row
            # Show retry counter if this is a retry
            if hasattr(self, 'license_retry_count') and self.license_retry_count > 0:
                self.show_retry_indicator(self.license_retry_count, 3)
    
    def show_retry_indicator(self, current_retry, max_retries):
        """Show license retry indicator"""
        self.retry_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        retry_text = f"🔄 License Retry: Attempt {current_retry + 1}/{max_retries}"
        
        if current_retry == 0:
            color = "#ff8c00"  # Orange for first retry
        elif current_retry == 1:
            color = "#ff6600"  # Darker orange for second retry
        else:
            color = "#dc3545"  # Red for final retry
            
        self.retry_label.config(text=retry_text, fg=color)
    
    def hide_retry_indicator(self):
        """Hide license retry indicator"""
        self.retry_frame.grid_forget()
        self.license_retry_count = 0
    
    def update_time(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%B %d, %Y"))
        self.root.after(1000, self.update_time)
    
    def start_verification(self):
        # Reset all panels
        self.auth_panel.pack_forget()
        self.verification_panel.pack_forget()
        self.result_panel.pack_forget()
        self.final_info.pack_forget()
        self.hide_retry_indicator()
        
        # Reset status variables
        self.helmet_status.set("PENDING")
        self.fingerprint_status.set("PENDING")
        self.license_status.set("PENDING")
        self.license_retry_count = 0
        
        # Start process
        self.start_btn.config(state="disabled", text="🔄 PROCESSING...")
        self.process_details.config(text="Initializing verification process...", fg="#FFA500")
        threading.Thread(target=self.run_verification, daemon=True).start()
    
    def run_verification(self):
        try:
            from controllers.student import run_verification_steps
            result = run_verification_steps(self.update_status_callback)
            self.root.after(0, lambda: self.show_result(result))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))
    
    def update_status_callback(self, step, status):
        self.root.after(0, lambda: self.update_step_status(step, status))
    
    def update_step_status(self, step, status):
        if step == "helmet":
            self.helmet_status.set(status)
            if status == "PROCESSING":
                self.current_step.set("🪖 Checking helmet...")
                self.process_details.config(text="🪖 Helmet Verification: Please wear your full-face helmet and position yourself in front of the camera.", fg="#FFA500")
            elif status == "VERIFIED":
                self.current_step.set("🪖 Helmet verification complete")
                self.process_details.config(text="✅ Helmet Check Passed: Full-face helmet detected and verified successfully.", fg="#28a745")
            elif status == "FAILED":
                self.current_step.set("🪖 Helmet verification failed")
                self.process_details.config(text="❌ Helmet Check Failed: Please ensure you're wearing a full-face helmet (not nutshell type).", fg="#DC3545")
                
        elif step == "fingerprint":
            self.fingerprint_status.set(status)
            if status == "PROCESSING":
                self.current_step.set("🔒 Place finger on sensor...")
                self.process_details.config(text="🔒 Fingerprint Authentication: Please place your registered finger firmly on the sensor.", fg="#FFA500")
            elif status == "VERIFIED":
                self.current_step.set("🔒 Fingerprint verified")
                self.process_details.config(text="✅ Fingerprint Verified: Identity confirmed successfully.", fg="#28a745")
            elif status == "FAILED":
                self.current_step.set("🔒 Fingerprint authentication failed")
                self.process_details.config(text="❌ Fingerprint Failed: No match found. Please ensure your finger is clean and properly positioned.", fg="#DC3545")
                
        elif step == "license":
            self.license_status.set(status)
            if status == "PROCESSING":
                self.current_step.set("📄 Validating license...")
                self.process_details.config(text="📄 License Validation: Checking license validity, expiration date, and document authenticity.", fg="#FFA500")
            elif status == "VALID":
                self.current_step.set("📄 License validated")
                self.process_details.config(text="✅ License Valid: All license checks passed successfully.", fg="#28a745")
                self.hide_retry_indicator()  # Hide retry indicator on success
            elif status == "FAILED":
                self.current_step.set("📄 License validation failed")
                self.process_details.config(text="❌ License Failed: License validation unsuccessful. Please check your license validity.", fg="#DC3545")
                self.hide_retry_indicator()  # Hide retry indicator on final failure
                
        elif step == "student_info":
            # Special handling for student info display
            if isinstance(status, dict):
                confidence = status.get('confidence', 0)
                self.show_authentication_success(status, confidence)
                
        elif step == "verification_summary":
            # Special handling for verification results
            if isinstance(status, dict):
                self.show_verification_results(status)
                
        elif step == "message":
            # Custom message updates with license retry detection
            self.current_step.set(status)
            
            # Check for license retry in message and update retry counter
            if "License Retry Attempt" in status:
                try:
                    # Extract retry number from message like "🔄 License Retry Attempt 2/3"
                    import re
                    match = re.search(r'Attempt (\d+)/(\d+)', status)
                    if match:
                        current_retry = int(match.group(1)) - 1  # Convert to 0-based
                        max_retries = int(match.group(2))
                        self.license_retry_count = current_retry
                        self.show_retry_indicator(current_retry, max_retries)
                        # Update license status to show retrying
                        self.license_status.set("PROCESSING")
                except:
                    pass
            
            # Smart color coding based on message content
            if any(word in status.lower() for word in ["helmet", "wear", "camera"]):
                color = "#FFA500"
            elif any(word in status.lower() for word in ["finger", "sensor", "place"]):
                color = "#17a2b8"
            elif any(word in status.lower() for word in ["license", "show", "capture", "retry"]):
                color = "#6f42c1"
            elif any(word in status.lower() for word in ["recording", "time", "logging"]):
                color = "#28a745"
            elif any(word in status.lower() for word in ["failed", "error", "denied"]):
                color = "#DC3545"
            elif any(word in status.lower() for word in ["success", "complete", "welcome"]):
                color = "#28a745"
            elif any(word in status.lower() for word in ["warning", "expired", "expiring"]):
                color = "#ff8c00"
            elif any(word in status.lower() for word in ["retry", "retrying"]):
                color = "#ff6600"
            else:
                color = "#0066CC"
                
            self.process_details.config(text=status, fg=color)
    
    def show_result(self, result):
        if result:
            self.student_info = result
            
            # Configure final result panel
            if result.get('verified', False):
                self.result_panel.config(bg='#d4edda')  # Light green background
                self.result_status.config(text="✅ VERIFICATION SUCCESSFUL", 
                                         fg="#155724", bg='#d4edda')
            else:
                self.result_panel.config(bg='#f8d7da')  # Light red background
                self.result_status.config(text="❌ VERIFICATION FAILED", 
                                         fg="#721c24", bg='#f8d7da')
            
            # Show final student information
            name = result.get('name', 'Unknown')
            if ',' in name:  # Format name properly
                parts = name.split(',')
                if len(parts) == 2:
                    name = f"{parts[1].strip()} {parts[0].strip()}"
            
            self.name_label.config(text=f"👤 Student: {name}", 
                                  fg="#333333", bg=self.result_panel['bg'])
            self.id_label.config(text=f"🆔 ID: {result.get('student_id', 'N/A')}", 
                                fg="#333333", bg=self.result_panel['bg'])
            self.course_label.config(text=f"📚 Course: {result.get('course', 'N/A')}", 
                                    fg="#333333", bg=self.result_panel['bg'])
            self.license_label.config(text=f"🪪 License: {result.get('license_number', 'N/A')}", 
                                     fg="#333333", bg=self.result_panel['bg'])
            
            # Show time action with timestamp
            time_action = result.get('time_action', 'UNKNOWN')
            timestamp = result.get('timestamp', 'Unknown time')
            
            if time_action == 'IN':
                action_text = f"🟢 TIME IN recorded at {timestamp}"
                action_color = "#28a745"
                self.process_details.config(text="✅ Welcome to campus! Your entry has been logged successfully.", fg="#28a745")
            elif time_action == 'OUT':
                action_text = f"🔴 TIME OUT recorded at {timestamp}"
                action_color = "#dc3545"
                self.process_details.config(text="✅ Drive safely! Your exit has been logged successfully.", fg="#28a745")
            else:
                action_text = f"⏰ Action: {time_action} at {timestamp}"
                action_color = "#6c757d"
                
            self.time_action_label.config(text=action_text, fg=action_color, bg=self.result_panel['bg'])
            
            # Pack final info and result panel
            self.final_info.pack(fill="x", padx=25, pady=15)
            self.result_panel.pack(fill="x", padx=20, pady=25)
            
            self.current_step.set("✅ All verification steps completed successfully!")
            
        else:
            # Failed result
            self.result_panel.config(bg='#f8d7da')
            self.result_status.config(text="❌ VERIFICATION FAILED", 
                                     fg="#721c24", bg='#f8d7da')
            self.result_panel.pack(fill="x", padx=20, pady=25)
            
            self.current_step.set("❌ Verification process failed. Please try again.")
            self.process_details.config(text="❌ Verification was unsuccessful. Please ensure all requirements are met and try again.", fg="#DC3545")
        
        # Hide retry indicator and re-enable start button
        self.hide_retry_indicator()
        self.start_btn.config(state="normal", text="🔄 START NEW VERIFICATION")
    
    def show_error(self, error):
        self.current_step.set(f"❌ System Error")
        self.process_details.config(text=f"❌ System Error: {error}\n\nPlease contact technical support if this problem persists.", fg="#DC3545")
        
        # Show error in result panel
        self.result_panel.config(bg='#f8d7da')
        self.result_status.config(text="❌ SYSTEM ERROR", fg="#721c24", bg='#f8d7da')
        self.result_panel.pack(fill="x", padx=20, pady=25)
        
        self.hide_retry_indicator()
        self.start_btn.config(state="normal", text="🔄 TRY AGAIN")
    
    def close(self):
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        # Bind ESC key to exit fullscreen
        self.root.bind('<Escape>', lambda e: self.close())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        try:
            self.root.mainloop()
        finally:
            pass
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode with F11"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)


def show_student_verification_gui():
    """Entry point for student verification GUI"""
    gui = StudentVerificationGUI()
    gui.run()


if __name__ == "__main__":
    show_student_verification_gui()
