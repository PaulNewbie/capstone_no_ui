# ui/main_window.py - Enhanced MotorPass GUI Interface with Time-In Count

import tkinter as tk
from tkinter import messagebox
import os
import sqlite3
from PIL import Image, ImageTk
from datetime import datetime
import threading
import time

class MotorPassGUI:
    def __init__(self, system_name, system_version, admin_function, student_function, guest_function):
        self.system_name = system_name
        self.system_version = system_version
        self.admin_function = admin_function
        self.student_function = student_function
        self.guest_function = guest_function
        
        self.root = tk.Tk()
        self.root.title(f"{system_name} System v{system_version}")
        self.root.geometry("1366x768")  # Full HD resolution
        self.root.resizable(False, False)
        self.root.configure(bg='black')
        
        # Make window fullscreen-like (cross-platform)
        try:
            # Try Windows method first
            self.root.state('zoomed')
        except:
            # Fallback for other platforms
            self.root.attributes('-zoomed', True)
        
        # Remove topmost for better usability
        # self.root.attributes('-topmost', True)
        
        self.setup_window()
        self.start_clock()
        self.start_time_in_counter()
        
    def setup_window(self):
        """Setup main window"""
        self.center_window()
        self.setup_background()
        self.create_header()
        self.create_clock()
        self.create_time_in_counter()
        self.create_selection_interface()
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        
    def setup_background(self):
        """Setup fullscreen background image"""
        # Try to load the background image
        background_paths = [
            "assets/background.jpg",
            "assets/background.png",
            "background.jpg",
            "background.png"
        ]
        
        background_loaded = False
        for bg_path in background_paths:
            if os.path.exists(bg_path):
                try:
                    # Get screen dimensions
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    
                    image = Image.open(bg_path)
                    # Resize to fill screen while maintaining aspect ratio
                    image = image.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
                    self.background_image = ImageTk.PhotoImage(image)
                    
                    background_label = tk.Label(self.root, image=self.background_image)
                    background_label.place(x=0, y=0, relwidth=1, relheight=1)
                    background_loaded = True
                    break
                except Exception as e:
                    print(f"Could not load background {bg_path}: {e}")
                    continue
        
        if not background_loaded:
            # Create a gradient background as fallback
            self.create_gradient_background()
    
    def create_gradient_background(self):
        """Create gradient background as fallback"""
        canvas = tk.Canvas(self.root, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        screen_height = self.root.winfo_screenheight()
        screen_width = self.root.winfo_screenwidth()
        
        for i in range(screen_height):
            # Create a brown to darker brown gradient
            intensity = int(139 - (i / screen_height) * 50)  # From 139 to 89
            color = f"#{intensity:02x}{int(intensity*0.6):02x}{int(intensity*0.4):02x}"
            canvas.create_line(0, i, screen_width, i, fill=color)
    
    def create_header(self):
        """Create modern header with logo and title"""
        # Header overlay with transparency effect
        header_frame = tk.Frame(self.root, bg='#46230a', height=100)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Add some transparency effect with a subtle border
        header_frame.configure(relief='flat', bd=0)
        
        # Logo and title container
        content_frame = tk.Frame(header_frame, bg='#46230a')
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Logo section
        logo_frame = tk.Frame(content_frame, bg='#46230a', width= 90, height=80)
        logo_frame.pack(side="left", padx=(0, 15), pady=5)
        logo_frame.pack_propagate(False)
        
        # Try to load logo
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((90, 80), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(logo_img)
                
                logo_label = tk.Label(logo_frame, image=self.logo_image, bg='#46230a')
                logo_label.place(relx=0.5, rely=0.5, anchor="center")
            except:
                # Fallback text logo
                logo_text = tk.Label(logo_frame, text="MP", font=("Arial", 20, "bold"), 
                                   fg="#46230a", bg="#DAA520")
                logo_text.place(relx=0.5, rely=0.5, anchor="center")
        else:
            logo_text = tk.Label(logo_frame, text="MP", font=("Arial", 20, "bold"), 
                               fg="#8B4513", bg="#DAA520")
            logo_text.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title section
        title_frame = tk.Frame(content_frame, bg='#46230a')
        title_frame.pack(side="left", fill="both", expand=True)
        
        title_label = tk.Label(title_frame, text=self.system_name, 
                              font=("Arial", 32, "bold"), fg="#DAA520", bg='#46230a')
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(title_frame, 
                                 text="We secure the safeness of your motorcycle inside our campus",
                                 font=("Arial", 11), fg="#FFFFFF", bg='#46230a')
        subtitle_label.pack(anchor="w")
    
    def create_clock(self):
        """Create real-time clock display"""
        # Clock container in top right - use relative positioning
        self.clock_frame = tk.Frame(self.root, bg='#46230a', bd=2, relief='solid')
        self.clock_frame.place(relx=0.98, rely=0.02, width=230, height=80, anchor='ne')
        
        # Time display
        self.time_label = tk.Label(self.clock_frame, text="", font=("Arial", 18, "bold"), 
                                  fg="#DAA520", bg='#46230a')
        self.time_label.pack(pady=5)
        
        # Date display
        self.date_label = tk.Label(self.clock_frame, text="", font=("Arial", 11), 
                                  fg="#FFFFFF", bg='#46230a')
        self.date_label.pack()
    
    def create_time_in_counter(self):
        """Create time-in counter display in bottom right"""
        # Counter container in bottom right
        self.counter_frame = tk.Frame(self.root, bg='#46230a', bd=2, relief='solid')
        self.counter_frame.place(relx=0.98, rely=0.98, width=200, height=70, anchor='se')
        
        # Title display
        counter_title = tk.Label(self.counter_frame, text="Currently Inside", 
                               font=("Arial", 11, "bold"), fg="#FFFFFF", bg='#46230a')
        counter_title.pack(pady=(5, 0))
        
        # Count display
        self.count_label = tk.Label(self.counter_frame, text="0", 
                                  font=("Arial", 20, "bold"), fg="#DAA520", bg='#46230a')
        self.count_label.pack()
    
    def get_current_time_in_count(self):
        """Get count of people currently timed in"""
        try:
            conn = sqlite3.connect("database/time_tracking.db")
            cursor = conn.cursor()
            
            # Get the latest status for each person
            cursor.execute("""
                SELECT student_id, status, 
                       ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY timestamp DESC) as row_num
                FROM time_records
            """)
            
            all_records = cursor.fetchall()
            conn.close()
            
            # Count people with status 'IN' in their latest record
            in_count = 0
            for record in all_records:
                if record[2] == 1 and record[1] == 'IN':  # Latest record and status is IN
                    in_count += 1
            
            return in_count
            
        except Exception as e:
            print(f"Error getting time-in count: {e}")
            return 0
        
    def start_clock(self):
        """Start the clock update thread"""
        def update_clock():
            while True:
                try:
                    now = datetime.now()
                    time_str = now.strftime("%H:%M:%S")
                    date_str = now.strftime("%A, %B %d, %Y")
                    
                    self.time_label.config(text=time_str)
                    self.date_label.config(text=date_str)
                    
                    time.sleep(1)
                except:
                    break
        
        clock_thread = threading.Thread(target=update_clock, daemon=True)
        clock_thread.start()
    
    def start_time_in_counter(self):
        """Start the time-in counter update thread"""
        def update_counter():
            while True:
                try:
                    count = self.get_current_time_in_count()
                    self.count_label.config(text=str(count))
                    time.sleep(5)  # Update every 5 seconds
                except:
                    break
        
        counter_thread = threading.Thread(target=update_counter, daemon=True)
        counter_thread.start()

    def create_selection_interface(self):
        """Create modern transparent selection interface"""
        # Main overlay container - centered on screen
        overlay_width = 500
        overlay_height = 450
        
        # Use relative positioning for better cross-platform compatibility
        self.main_overlay = tk.Frame(self.root, bg='white', bd=0, relief='flat')
        self.main_overlay.place(relx=0.5, rely=0.5, width=overlay_width, height=overlay_height, anchor='center')
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(self.root, bg='#666666')
        shadow_frame.place(relx=0.5, rely=0.5, width=overlay_width, height=overlay_height, anchor='center')
        shadow_frame.lower()  # Put shadow behind main overlay
        
        # Bring overlay to front
        self.main_overlay.lift()
        
        # Title section
        title_frame = tk.Frame(self.main_overlay, bg='white', height=80)
        title_frame.pack(fill="x", padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="YOU ARE A:", 
                              font=("Arial", 20, "bold"), fg="#333333", bg='white')
        title_label.pack(expand=True)
        
        # Buttons container
        buttons_frame = tk.Frame(self.main_overlay, bg='white')
        buttons_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Create user type buttons with modern styling
        self.create_modern_button(buttons_frame, "STUDENT", self.student_clicked, "#DAA520")
        self.create_modern_button(buttons_frame, "GUEST", self.guest_clicked, "#DAA520")
        self.create_modern_button(buttons_frame, "ADMIN", self.admin_clicked, "#DAA520")
        
        # Exit button
        exit_frame = tk.Frame(self.main_overlay, bg='white', height=60)
        exit_frame.pack(fill="x", padx=40, pady=(10, 20))
        exit_frame.pack_propagate(False)
        
        exit_btn = tk.Button(exit_frame, text="EXIT SYSTEM", 
                           font=("Arial", 12, "bold"), bg="#8B4513", fg="white",
                           bd=0, padx=30, pady=10, cursor="hand2",
                           command=self.exit_system, relief='flat')
        exit_btn.pack(expand=True)
        
        # Hover effects for exit button
        def exit_on_enter(e):
            exit_btn.config(bg="#A0522D")
        def exit_on_leave(e):
            exit_btn.config(bg="#8B4513")
        
        exit_btn.bind("<Enter>", exit_on_enter)
        exit_btn.bind("<Leave>", exit_on_leave)
        
    def create_modern_button(self, parent, text, command, color):
        """Create modern styled button with hover effects"""
        btn_frame = tk.Frame(parent, bg='white', height=60)
        btn_frame.pack(fill="x", pady=8)
        btn_frame.pack_propagate(False)
        
        btn = tk.Button(btn_frame, text=text, font=("Arial", 16, "bold"),
                       bg=color, fg="#333333", bd=0, cursor="hand2",
                       command=command, relief='flat')
        btn.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Hover effects
        def on_enter(e):
            btn.config(bg="#F0E68C")  # Lighter gold on hover
            
        def on_leave(e):
            btn.config(bg=color)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
    def student_clicked(self):
        """Handle student button click"""
        self.run_function(self.student_function, "Student Verification")
        
    def admin_clicked(self):
        """Handle admin button click"""
        self.run_function(self.admin_function, "Admin Panel")
        
    def guest_clicked(self):
        """Handle guest button click"""
        self.run_function(self.guest_function, "Guest Verification")
        
    def run_function(self, function, title):
        """Hide GUI and run specified function"""
        try:
            self.root.withdraw()
            print(f"\n{'='*50}")
            print(f"🚗 {title} Started")
            print(f"{'='*50}")
            function()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.root.deiconify()
            
    def exit_system(self):
        """Exit the system with confirmation"""
        if messagebox.askyesno("Exit System", "Are you sure you want to exit MotorPass?"):
            self.root.quit()
            
    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        finally:
            try:
                self.root.destroy()
            except:
                pass
