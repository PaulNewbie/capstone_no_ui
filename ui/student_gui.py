# ui/student_gui.py - Simple Fix

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
        self.current_step = tk.StringVar(value="🚀 Starting verification process...")
        self.student_info = {}
        self.license_retry_count = 0
        
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
        
        # Time - SIMPLIFIED (no auto-update to avoid callback errors)
        self.time_frame = tk.Frame(header_content, bg='#46230a')
        self.time_frame.pack(side="right")
        now = datetime.now()
        tk.Label(self.time_frame, text=now.strftime("%H:%M:%S"), font=("Arial", 14, "bold"), 
                fg="#DAA520", bg='#46230a').pack()
        tk.Label(self.time_frame, text=now.strftime("%B %d, %Y"), font=("Arial", 10), 
                fg="#FFFFFF", bg='#46230a').pack()
        
        # Main content
        main = tk.Frame(self.root, bg='#8B4513')
        main.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Title
        tk.Label(main, text="STUDENT VERIFICATION", font=("Arial", 36, "bold"), 
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
        
        tk.Label(footer, text="🪖 Full-face helmet required • 🤚 Finger ready • 🆔 License ready • ESC to exit",
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
        
        # Cancel button only
        btn_frame = tk.Frame(status_container, bg='white')
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        
        tk.Button(btn_frame, text="❌ CANCEL", font=("Arial", 14, "bold"), 
                 bg="#8B4513", fg="white", padx=30, pady=15, 
                 command=self.close).pack()
    
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
        
        # Current process details
        details_frame = tk.Frame(process_container, bg='#f8f9fa', relief='sunken', bd=2)
        details_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(details_frame, text="Current Status:", font=("Arial", 14, "bold"), 
                fg="#333333", bg='#f8f9fa').pack(anchor="w", padx=15, pady=(15, 8))
        
        self.process_details = tk.Label(details_frame, text="Starting verification process...", 
                                       font=("Arial", 12), fg="#0066CC", bg='#f8f9fa', 
                                       wraplength=450, justify="left")
        self.process_details.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Rest of the panels (keep existing code)
        self.auth_panel = tk.Frame(process_container, bg='#e3f2fd', relief='ridge', bd=2)
        self.student_card = tk.Frame(self.auth_panel, bg='#e3f2fd')
        self.student_card.pack(fill="x", padx=20, pady=15)
        self.auth_status = tk.Label(self.auth_panel, font=("Arial", 14, "bold"), bg='#e3f2fd', pady=8)
        self.auth_status.pack()
        self.student_name = tk.Label(self.student_card, font=("Arial", 13, "bold"), fg="#1565c0", bg='#e3f2fd')
        self.student_name.pack(anchor="w", pady=3)
        self.student_id = tk.Label(self.student_card, font=("Arial", 12), fg="#333333", bg='#e3f2fd')
        self.student_id.pack(anchor="w", pady=2)
        self.student_course = tk.Label(self.student_card, font=("Arial", 12), fg="#333333", bg='#e3f2fd')
        self.student_course.pack(anchor="w", pady=2)
        self.confidence_info = tk.Label(self.student_card, font=("Arial", 11), fg="#666666", bg='#e3f2fd')
        self.confidence_info.pack(anchor="w", pady=3)
        
        self.verification_panel = tk.Frame(process_container, bg='#f5f5f5', relief='ridge', bd=2)
        tk.Label(self.verification_panel, text="🎯 VERIFICATION SUMMARY", 
                font=("Arial", 15, "bold"), fg="#333333", bg='#f5f5f5').pack(pady=12)
        self.verification_grid = tk.Frame(self.verification_panel, bg='#f5f5f5')
        self.verification_grid.pack(fill="x", padx=25, pady=15)
    
    def show_success_floating_message(self, result):
        """Show simple success message"""
        self.floating_message = tk.Frame(self.root, bg='#DAA520', relief='solid', bd=3)
        self.floating_message.place(relx=0.5, rely=0.5, anchor='center')
        
        content = tk.Frame(self.floating_message, bg='#DAA520')
        content.pack(padx=40, pady=30)
        
        tk.Label(content, text="✅", font=("Arial", 40), bg='#DAA520').pack()
        tk.Label(content, text="SUCCESS!", 
                font=("Arial", 24, "bold"), fg="black", bg='#DAA520').pack(pady=(10, 5))
        
        name = result.get('name', 'Student')
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                name = f"{parts[1].strip()} {parts[0].strip()}"
        
        tk.Label(content, text=f"Welcome {name}", 
                font=("Arial", 16), fg="black", bg='#DAA520').pack(pady=5)
        
        time_action = result.get('time_action', 'IN')
        timestamp = result.get('timestamp', 'now')
        action_msg = f"TIME {time_action} at {timestamp}"
        
        tk.Label(content, text=action_msg, 
                font=("Arial", 14, "bold"), fg="#006400" if time_action == 'IN' else "#8B0000", 
                bg='#DAA520').pack(pady=5)
        
        # Auto-close after 3 seconds
        self.root.after(3000, self.close)
    
    def update_status_display(self, row, status):
        try:
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
        except:
            pass
    
    def show_authentication_success(self, student_info, confidence):
        try:
            self.auth_status.config(text="✅ AUTHENTICATION SUCCESSFUL", fg="#28a745")
            
            name = student_info.get('name', 'Unknown Student')
            if ',' in name:
                parts = name.split(',')
                if len(parts) == 2:
                    name = f"{parts[1].strip()} {parts[0].strip()}"
            
            self.student_name.config(text=f"👤 Welcome, {name}")
            self.student_id.config(text=f"🆔 Student ID: {student_info.get('student_id', 'N/A')}")
            self.student_course.config(text=f"📚 Course: {student_info.get('course', 'N/A')}")
            
            confidence_val = int(confidence)
            if confidence_val >= 80:
                conf_color = "#28a745"
                conf_text = "Excellent"
            elif confidence_val >= 60:
                conf_color = "#ffc107"
                conf_text = "Good"
            else:
                conf_color = "#dc3545"
                conf_text = "Low"
                
            self.confidence_info.config(text=f"🎯 Match Confidence: {confidence_val}% ({conf_text})", fg=conf_color)
            self.auth_panel.pack(fill="x", padx=20, pady=15)
        except:
            pass
    
    def show_verification_results(self, results):
        try:
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
                
                icon = "✅" if passed else "❌"
                icon_color = "#28a745" if passed else "#dc3545"
                
                tk.Label(check_frame, text=icon, font=("Arial", 16), 
                        fg=icon_color, bg='#f5f5f5').pack(side="left")
                
                tk.Label(check_frame, text=check_name, font=("Arial", 12), 
                        fg="#333333", bg='#f5f5f5').pack(side="left", padx=(8, 0))
            
            self.verification_panel.pack(fill="x", padx=20, pady=15)
        except:
            pass
    
    def start_verification(self):
        """Start verification"""
        self.auth_panel.pack_forget()
        self.verification_panel.pack_forget()
        
        self.helmet_status.set("PENDING")
        self.fingerprint_status.set("PENDING")
        self.license_status.set("PENDING")
        
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
        try:
            if step == "helmet":
                self.helmet_status.set(status)
            elif step == "fingerprint":
                self.fingerprint_status.set(status)
            elif step == "license":
                self.license_status.set(status)
            elif step == "student_info" and isinstance(status, dict):
                confidence = status.get('confidence', 0)
                self.show_authentication_success(status, confidence)
            elif step == "verification_summary" and isinstance(status, dict):
                self.show_verification_results(status)
            elif step == "message":
                self.current_step.set(status)
                self.process_details.config(text=status, fg="#0066CC")
        except:
            pass
    
    def show_result(self, result):
        if result and result.get('verified', False):
            self.show_success_floating_message(result)
        else:
            self.current_step.set("❌ Verification failed")
            self.root.after(2000, self.close)
    
    def show_error(self, error):
        self.current_step.set(f"❌ Error: {error}")
        self.root.after(3000, self.close)
    
    def close(self):
        """Simple close with camera cleanup"""
        try:
            # Clean up camera
            import cv2
            cv2.destroyAllWindows()
        except:
            pass
        
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
    
    def run(self):
        self.root.bind('<Escape>', lambda e: self.close())
        self.root.after(1000, self.start_verification)
        
        try:
            self.root.mainloop()
        except:
            pass


def show_student_verification_gui():
    """Entry point for student verification GUI"""
    gui = StudentVerificationGUI()
    gui.run()


if __name__ == "__main__":
    show_student_verification_gui()
