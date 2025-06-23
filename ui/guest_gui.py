# ui/guest_gui.py - Fixed Camera Release Issue

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
import time
import cv2

class GuestVerificationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_variables()
        self.create_interface()
        self.verification_started = False
        self.helmet_verified = False
        self.license_scanned = False
        self.detected_name = ""
        
    def setup_window(self):
        self.root.title("MotorPass - Guest Verification")
        self.root.configure(bg='#8B4513')
        self.root.resizable(False, False)
        
        # Force fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Alternative fullscreen methods
        try:
            self.root.state('zoomed')
        except:
            try:
                self.root.attributes('-zoomed', True)
            except:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
    
    def create_variables(self):
        self.helmet_status = tk.StringVar(value="PENDING")
        self.license_status = tk.StringVar(value="PENDING")
        self.current_step = tk.StringVar(value="🚀 Click 'Start Verification' to begin...")
        self.guest_info = {}
        
        # Form variables
        self.name_var = tk.StringVar()
        self.plate_var = tk.StringVar()
        self.office_var = tk.StringVar(value="CSS Office")
        
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
        now = datetime.now()
        tk.Label(self.time_frame, text=now.strftime("%H:%M:%S"), font=("Arial", 14, "bold"), 
                fg="#DAA520", bg='#46230a').pack()
        tk.Label(self.time_frame, text=now.strftime("%B %d, %Y"), font=("Arial", 10), 
                fg="#FFFFFF", bg='#46230a').pack()
        
        # Main content
        main = tk.Frame(self.root, bg='#8B4513')
        main.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Title
        tk.Label(main, text="GUEST VERIFICATION", font=("Arial", 36, "bold"), 
                fg="#FFFFFF", bg='#8B4513').pack(pady=(0, 20))
        
        # Content container
        content = tk.Frame(main, bg='#8B4513')
        content.pack(fill="both", expand=True)
        
        # Left panel - Verification status
        self.create_left_panel(content)
        
        # Right panel - Guest Information Form
        self.create_right_panel(content)
        
        # Footer
        footer = tk.Frame(self.root, bg='#46230a', height=60)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        tk.Label(footer, text="🪖 Full-face helmet required • 🆔 License ready • 🚗 Plate number required • ESC to exit",
                font=("Arial", 12), fg="#FFFFFF", bg='#46230a').pack(expand=True)
    
    def create_left_panel(self, parent):
        left = tk.Frame(parent, bg='#8B4513')
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Status container
        status_container = tk.Frame(left, bg='white', relief='raised', bd=3)
        status_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Status items
        self.create_status_row(status_container, "HELMET TYPE:", self.helmet_status, 0)
        self.create_status_row(status_container, "LICENSE DOC:", self.license_status, 1)
        
        # Current step
        step_frame = tk.Frame(status_container, bg='white')
        step_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        
        tk.Label(step_frame, text="Current Step:", font=("Arial", 12, "bold"), 
                fg="#333333", bg='white').pack(anchor="w")
        tk.Label(step_frame, textvariable=self.current_step, font=("Arial", 11), 
                fg="#0066CC", bg='white', wraplength=400).pack(anchor="w", pady=(5, 0))
        
        # Action buttons frame
        btn_frame = tk.Frame(status_container, bg='white')
        btn_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        
        # Start Verification button
        self.start_btn = tk.Button(btn_frame, text="🚀 START VERIFICATION", font=("Arial", 14, "bold"), 
                                  bg="#007bff", fg="white", padx=30, pady=15, 
                                  command=self.start_verification)
        self.start_btn.pack(side="left", padx=(0, 10))
        
        # Submit button (initially disabled)
        self.submit_btn = tk.Button(btn_frame, text="✅ SUBMIT", font=("Arial", 14, "bold"), 
                                   bg="#28a745", fg="white", padx=30, pady=15, 
                                   command=self.submit_verification, state="disabled")
        self.submit_btn.pack(side="left", padx=(0, 10))
        
        # Retry button (initially disabled)
        self.retry_btn = tk.Button(btn_frame, text="🔄 RETRY", font=("Arial", 14, "bold"), 
                                  bg="#ffc107", fg="white", padx=30, pady=15, 
                                  command=self.retry_license_scan, state="disabled")
        self.retry_btn.pack(side="left", padx=(0, 10))
        
        # Cancel button
        tk.Button(btn_frame, text="❌ CANCEL", font=("Arial", 14, "bold"), 
                 bg="#8B4513", fg="white", padx=30, pady=15, 
                 command=self.close).pack(side="left")
    
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
        
        # Store references
        setattr(self, f"status_btn_{row}", button)
        setattr(self, f"status_icon_{row}", icon)
        status_var.trace_add("write", lambda *args, r=row: self.update_status_display(r, status_var.get()))
        self.update_status_display(row, "PENDING")
    
    def create_right_panel(self, parent):
        right = tk.Frame(parent, bg='#8B4513')
        right.pack(side="right", fill="both", expand=True)
        
        # Guest Information Form container
        form_container = tk.Frame(right, bg='white', relief='raised', bd=3)
        form_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(form_container, text="📋 GUEST INFORMATION", 
                font=("Arial", 18, "bold"), fg="#333333", bg='white').pack(pady=15)
        
        # Instruction label
        self.instruction_label = tk.Label(form_container, 
                                         text="⚠️ Please complete helmet and license verification first",
                                         font=("Arial", 12, "bold"), fg="#ff6600", bg='white')
        self.instruction_label.pack(pady=10)
        
        # Form fields (initially disabled)
        form_frame = tk.Frame(form_container, bg='white')
        form_frame.pack(fill="x", padx=40, pady=20)
        
        # Name field
        tk.Label(form_frame, text="Full Name (from License):", font=("Arial", 14, "bold"), 
                fg="#333333", bg='white').pack(anchor="w", pady=(0, 5))
        self.name_entry = tk.Entry(form_frame, textvariable=self.name_var, 
                                  font=("Arial", 14), width=35, state="disabled")
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Plate number field
        tk.Label(form_frame, text="Plate Number:", font=("Arial", 14, "bold"), 
                fg="#333333", bg='white').pack(anchor="w", pady=(0, 5))
        self.plate_entry = tk.Entry(form_frame, textvariable=self.plate_var, 
                                   font=("Arial", 14), width=35, state="disabled")
        self.plate_entry.pack(fill="x", pady=(0, 15))
        
        # Office dropdown
        tk.Label(form_frame, text="Office to Visit:", font=("Arial", 14, "bold"), 
                fg="#333333", bg='white').pack(anchor="w", pady=(0, 5))
        self.office_combo = ttk.Combobox(form_frame, textvariable=self.office_var,
                                        font=("Arial", 14), width=33, state="disabled",
                                        values=[
                                            "CSS Office",
                                            "Registrar Office", 
                                            "Cashier Office",
                                            "Dean's Office",
                                            "Library",
                                            "IT Office",
                                            "Main Office",
                                            "Other"
                                        ])
        self.office_combo.pack(fill="x", pady=(0, 20))
        
        # Process details
        self.process_frame = tk.Frame(form_container, bg='#f8f9fa', relief='sunken', bd=2)
        self.process_details = tk.Label(self.process_frame, text="Click 'Start Verification' to begin", 
                                       font=("Arial", 12), fg="#0066CC", bg='#f8f9fa', 
                                       wraplength=450, justify="left")
        self.process_details.pack(padx=15, pady=15)
        self.process_frame.pack(fill="x", padx=20, pady=10)
    
    def cleanup_camera_resources(self):
        """Clean up camera resources between steps"""
        try:
            # Destroy all OpenCV windows
            cv2.destroyAllWindows()
            
            # Release camera from rpi_camera module
            from services.rpi_camera import release_camera
            release_camera()
            
            # Small delay to ensure resources are freed
            time.sleep(0.5)
            
            print("✅ Camera resources cleaned up")
        except Exception as e:
            print(f"⚠️ Camera cleanup warning: {e}")
    
    def reinitialize_camera(self):
        """Reinitialize camera for next step"""
        try:
            from services.rpi_camera import get_camera
            camera = get_camera()
            if camera and camera.initialized:
                print("✅ Camera reinitialized successfully")
                return True
            else:
                print("❌ Failed to reinitialize camera")
                return False
        except Exception as e:
            print(f"❌ Camera reinitialization error: {e}")
            return False
    
    def start_verification(self):
        """Start the helmet verification process"""
        if self.verification_started:
            return
            
        self.verification_started = True
        self.start_btn.config(state="disabled")
        self.helmet_status.set("PENDING")
        self.license_status.set("PENDING")
        self.current_step.set("Starting helmet verification...")
        self.process_details.config(text="Initializing helmet verification...", fg="#FFA500")
        
        threading.Thread(target=self.run_helmet_verification, daemon=True).start()
    
    def run_helmet_verification(self):
        """Run helmet verification only"""
        try:
            from services.helmet_infer import verify_helmet
            from services.led_control import set_led_processing, set_led_idle
            from services.buzzer_control import play_processing, play_failure
            
            set_led_processing()
            play_processing()
            
            self.root.after(0, lambda: self.update_step_status("helmet", "PROCESSING"))
            self.root.after(0, lambda: self.update_step_status("message", "🪖 Helmet Verification Starting..."))
            
            if verify_helmet():
                self.helmet_verified = True
                # Clean up camera after helmet verification
                self.cleanup_camera_resources()
                self.root.after(0, lambda: self.handle_helmet_success())
            else:
                self.helmet_verified = False
                self.cleanup_camera_resources()
                self.root.after(0, lambda: self.handle_helmet_failure())
                set_led_idle()
                play_failure()
                
        except Exception as e:
            self.cleanup_camera_resources()
            self.root.after(0, lambda: self.show_error(f"Helmet verification error: {str(e)}"))
        finally:
            self.verification_started = False
    
    def handle_helmet_success(self):
        """Handle successful helmet verification"""
        self.helmet_status.set("VERIFIED")
        self.current_step.set("✅ Helmet verified! Preparing license scan...")
        self.process_details.config(text="Helmet verification successful! Initializing camera for license scan...", fg="#28a745")
        
        # Delay to ensure camera is ready, then reinitialize
        self.root.after(1500, self.prepare_license_scan)
    
    def prepare_license_scan(self):
        """Prepare camera for license scanning"""
        self.current_step.set("Initializing camera for license scan...")
        
        if self.reinitialize_camera():
            self.start_license_scan()
        else:
            self.show_error("Failed to initialize camera for license scan. Please try again.")
            self.start_btn.config(state="normal", text="🔄 RETRY VERIFICATION")
    
    def start_license_scan(self):
        """Start license scanning"""
        self.run_license_scan_direct()
    
    def handle_helmet_failure(self):
        """Handle failed helmet verification"""
        self.helmet_status.set("FAILED")
        self.current_step.set("❌ Helmet verification failed")
        self.process_details.config(text="Please wear a full-face helmet (not nutshell type) and try again.", fg="#dc3545")
        self.start_btn.config(state="normal", text="🔄 RETRY VERIFICATION")
    
    def run_license_scan_direct(self):
        """Run license scan directly without threading to avoid OpenCV issues"""
        try:
            from services.license_reader import auto_capture_license_rpi, extract_guest_name_from_license_simple
            from services.led_control import set_led_processing, set_led_idle
            from services.buzzer_control import play_processing, play_success, play_failure
            
            # Update UI
            self.update_step_status("license", "PROCESSING")
            self.update_step_status("message", "📄 License Scanning...\n📷 Please show your license to the camera")
            self.root.update()
            
            print("🎥 Starting license capture for guest...")
            
            set_led_processing()
            play_processing()
            
            # Capture license image
            image_path = auto_capture_license_rpi(reference_name="", fingerprint_info=None, retry_mode=False)
            
            print(f"📸 Image captured: {image_path}")
            
            if image_path:
                self.update_step_status("message", "🔍 Analyzing license...")
                self.root.update()
                
                try:
                    extraction_result = extract_guest_name_from_license_simple(image_path)
                    print(f"📄 Extraction result: {extraction_result}")
                    
                    doc_verified = "Driver's License Detected" in extraction_result.get('Document Verified', '')
                    detected_name = extraction_result.get('Name', 'Guest')
                    
                    if doc_verified and detected_name and detected_name not in ['Guest', 'Guest User', 'Not Found']:
                        self.detected_name = detected_name
                        self.license_scanned = True
                        self.handle_license_success()
                        play_success()
                    else:
                        self.license_scanned = True
                        self.detected_name = ""
                        self.handle_license_partial_success()
                        play_success()
                        
                except Exception as ocr_error:
                    print(f"OCR Error: {ocr_error}")
                    self.license_scanned = True
                    self.detected_name = ""
                    self.handle_license_partial_success()
                    play_success()
            else:
                print("❌ No image captured from camera")
                self.handle_license_failure()
                play_failure()
                
            set_led_idle()
                
        except Exception as e:
            print(f"❌ License scan error: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"License scan error: {str(e)}")
        finally:
            # Clean up camera after license scan
            self.cleanup_camera_resources()
    
    def handle_license_success(self):
        """Handle successful license scan with name extraction"""
        self.license_status.set("VALID")
        self.current_step.set("✅ License scanned successfully!")
        
        # Enable form fields
        self.name_entry.config(state="normal")
        self.plate_entry.config(state="normal")
        self.office_combo.config(state="readonly")
        
        # Auto-fill name if detected
        if self.detected_name:
            self.name_var.set(self.detected_name)
            self.process_details.config(text=f"License verified! Name detected: {self.detected_name}\nPlease enter plate number and select office.", fg="#28a745")
        else:
            self.process_details.config(text="License verified! Please complete the form below.", fg="#28a745")
        
        self.instruction_label.config(text="✅ Verification complete! Please fill in the remaining information.", fg="#28a745")
        
        # Enable buttons
        self.submit_btn.config(state="normal")
        self.retry_btn.config(state="normal", text="🔄 RESCAN LICENSE")
        self.start_btn.config(state="disabled")
        
        # Focus on plate number field
        self.plate_entry.focus()
    
    def handle_license_partial_success(self):
        """Handle license scan success but no name extracted"""
        self.license_status.set("VALID")
        self.current_step.set("⚠️ License scanned - Manual entry required")
        
        # Enable all form fields
        self.name_entry.config(state="normal")
        self.plate_entry.config(state="normal")
        self.office_combo.config(state="readonly")
        
        self.process_details.config(text="License captured but name not detected. Please enter all information manually.", fg="#ffc107")
        self.instruction_label.config(text="⚠️ Please enter your information manually", fg="#ffc107")
        
        # Enable buttons
        self.submit_btn.config(state="normal")
        self.retry_btn.config(state="normal", text="🔄 RESCAN LICENSE")
        self.start_btn.config(state="disabled")
        
        # Focus on name field
        self.name_entry.focus()
    
    def handle_license_failure(self):
        """Handle failed license scan"""
        self.license_status.set("FAILED")
        self.current_step.set("❌ License scan failed")
        self.process_details.config(text="Could not capture license. Please position your license clearly and try again.", fg="#dc3545")
        
        # Enable retry button
        self.retry_btn.config(state="normal", text="🔄 RETRY LICENSE SCAN")
    
    def retry_license_scan(self):
        """Retry only the license scanning"""
        if not self.helmet_verified:
            messagebox.showwarning("Verification Required", "Please complete helmet verification first!")
            return
            
        self.license_status.set("PENDING")
        self.retry_btn.config(state="disabled")
        self.current_step.set("Retrying license scan...")
        
        # Clear form fields
        self.name_var.set("")
        self.plate_var.set("")
        self.detected_name = ""
        self.license_scanned = False
        
        # Disable form fields during retry
        self.name_entry.config(state="disabled")
        self.plate_entry.config(state="disabled")
        self.office_combo.config(state="disabled")
        
        # Clean up camera and reinitialize
        self.cleanup_camera_resources()
        self.root.after(1000, self.prepare_license_scan)
    
    def validate_form(self):
        """Validate form inputs"""
        name = self.name_var.get().strip()
        plate = self.plate_var.get().strip()
        office = self.office_var.get().strip()
        
        if not name:
            messagebox.showerror("Validation Error", "Please enter guest name!")
            self.name_entry.focus()
            return False
            
        if not plate:
            messagebox.showerror("Validation Error", "Please enter plate number!")
            self.plate_entry.focus()
            return False
            
        if not office:
            messagebox.showerror("Validation Error", "Please select office to visit!")
            self.office_combo.focus()
            return False
            
        return True
    
    def submit_verification(self):
        """Submit the complete verification"""
        if not self.helmet_verified or not self.license_scanned:
            messagebox.showwarning("Incomplete Verification", "Please complete all verification steps first!")
            return
            
        if not self.validate_form():
            return
            
        # Disable all controls
        self.name_entry.config(state="disabled")
        self.plate_entry.config(state="disabled")
        self.office_combo.config(state="disabled")
        self.submit_btn.config(state="disabled")
        self.retry_btn.config(state="disabled")
        
        # Store guest info
        self.guest_info = {
            'name': self.name_var.get().strip(),
            'plate_number': self.plate_var.get().strip().upper(),
            'office': self.office_var.get().strip(),
            'helmet_verified': self.helmet_verified,
            'license_verified': self.license_scanned
        }
        
        self.current_step.set("Processing guest entry...")
        self.process_details.config(text="Recording guest information...", fg="#FFA500")
        
        # Process the guest entry
        threading.Thread(target=self.process_guest_entry, daemon=True).start()
    
    def process_guest_entry(self):
        """Process the guest entry with the collected information"""
        try:
            from controllers.guest import record_guest_time_in, record_guest_time_out
            from database.db_operations import db
            from services.led_control import set_led_success, set_led_idle
            from services.buzzer_control import play_success, play_failure
            import time
            
            # Check current status
            current_status = db.get_current_status(f"GUEST_{self.guest_info['plate_number']}")
            
            # Create guest data
            guest_data = {
                'name': self.guest_info['name'],
                'plate_number': self.guest_info['plate_number'],
                'office': self.guest_info['office'],
                'is_guest': True
            }
            
            # Determine time action
            if current_status == 'OUT' or current_status is None:
                success = record_guest_time_in(guest_data)
                time_action = 'IN'
            else:
                success = record_guest_time_out(guest_data)
                time_action = 'OUT'
            
            if success:
                set_led_success(duration=5.0)
                play_success()
                
                result = {
                    'name': self.guest_info['name'],
                    'plate_number': self.guest_info['plate_number'],
                    'office': self.guest_info['office'],
                    'time_action': time_action,
                    'timestamp': time.strftime('%H:%M:%S'),
                    'verified': True
                }
                
                self.root.after(0, lambda: self.show_success_floating_message(result))
            else:
                self.root.after(0, lambda: self.show_error("Failed to record guest entry"))
                set_led_idle()
                play_failure()
                
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Processing error: {str(e)}"))
    
    def show_success_floating_message(self, result):
        """Show simple success message"""
        self.floating_message = tk.Frame(self.root, bg='#DAA520', relief='solid', bd=3)
        self.floating_message.place(relx=0.5, rely=0.5, anchor='center')
        
        content = tk.Frame(self.floating_message, bg='#DAA520')
        content.pack(padx=40, pady=30)
        
        tk.Label(content, text="✅", font=("Arial", 40), bg='#DAA520').pack()
        tk.Label(content, text="SUCCESS!", 
                font=("Arial", 24, "bold"), fg="black", bg='#DAA520').pack(pady=(10, 5))
        
        tk.Label(content, text=f"Welcome {result.get('name', 'Guest')}", 
                font=("Arial", 16), fg="black", bg='#DAA520').pack(pady=5)
        
        time_action = result.get('time_action', 'IN')
        timestamp = result.get('timestamp', 'now')
        action_msg = f"TIME {time_action} at {timestamp}"
        
        tk.Label(content, text=action_msg, 
                font=("Arial", 14, "bold"), fg="#006400" if time_action == 'IN' else "#8B0000", 
                bg='#DAA520').pack(pady=5)
        
        office = result.get('office', 'CSS Office')
        tk.Label(content, text=f"Visiting: {office}", 
                font=("Arial", 12), fg="black", bg='#DAA520').pack(pady=5)
        
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
    
    def update_step_status(self, step, status):
        try:
            if step == "helmet":
                self.helmet_status.set(status)
            elif step == "license":
                self.license_status.set(status)
            elif step == "message":
                self.current_step.set(status)
                self.process_details.config(text=status, fg="#0066CC")
        except:
            pass
    
    def show_error(self, error):
        self.current_step.set(f"❌ Error: {error}")
        self.process_details.config(text=f"System error: {error}", fg="#dc3545")
        
        # Re-enable appropriate buttons
        if not self.helmet_verified:
            self.start_btn.config(state="normal")
        elif not self.license_scanned:
            self.retry_btn.config(state="normal")
        else:
            self.submit_btn.config(state="normal")
    
    def close(self):
        """Simple close with camera cleanup"""
        try:
            self.cleanup_camera_resources()
        except:
            pass
        
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
    
    def run(self):
        self.root.bind('<Escape>', lambda e: self.close())
        
        # Bind Enter key
        def handle_enter(e):
            if self.start_btn['state'] == 'normal':
                self.start_verification()
            elif self.submit_btn['state'] == 'normal':
                self.submit_verification()
                
        self.root.bind('<Return>', handle_enter)
        
        try:
            self.root.mainloop()
        except:
            pass


def show_guest_verification_gui():
    """Entry point for guest verification GUI"""
    gui = GuestVerificationGUI()
    gui.run()


if __name__ == "__main__":
    show_guest_verification_gui()
