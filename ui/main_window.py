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
        """Get count of people currently timed in from centralized database"""
        try:
            conn = sqlite3.connect("database/motorpass.db")
            cursor = conn.cursor()
            
            # Get count from current_status table
            cursor.execute("SELECT COUNT(*) FROM current_status WHERE status = 'IN'")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
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
        """Create modern glass-morphism selection interface"""
        # Main overlay container - centered on screen with enhanced styling
        overlay_width = 550
        overlay_height = 500
        
        # Create shadow effect (multiple layers for depth)
        shadow_offsets = [(6, 6, '#404040'), (4, 4, '#505050'), (2, 2, '#606060')]
        for offset_x, offset_y, shadow_color in shadow_offsets:
            shadow_frame = tk.Frame(self.root, bg=shadow_color)
            shadow_frame.place(relx=0.5, rely=0.5, 
                             width=overlay_width, height=overlay_height, 
                             anchor='center', x=offset_x, y=offset_y)
        
        # Main container with glass morphism effect
        self.main_overlay = tk.Frame(self.root, bg='#2c1810', bd=0, relief='flat')
        self.main_overlay.place(relx=0.5, rely=0.5, width=overlay_width, height=overlay_height, anchor='center')
        
        # Add border effect
        border_frame = tk.Frame(self.main_overlay, bg='#D4AF37', height=3)
        border_frame.pack(fill="x", side="top")
        
        # Inner container with padding
        inner_container = tk.Frame(self.main_overlay, bg='#2c1810')
        inner_container.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Title section with enhanced styling
        title_container = tk.Frame(inner_container, bg='#3d2317', height=100)
        title_container.pack(fill="x", padx=15, pady=(15, 0))
        title_container.pack_propagate(False)
        
        # Decorative line above title
        deco_line = tk.Frame(title_container, bg='#D4AF37', height=2)
        deco_line.pack(fill="x", pady=(10, 5))
        
        title_label = tk.Label(title_container, text="YOU ARE A:", 
                              font=("Arial", 22, "bold"), fg="#F5DEB3", bg='#3d2317')
        title_label.pack(expand=True)
        
        # Subtitle for better context
        subtitle_label = tk.Label(title_container, text="Please select your access level", 
                                 font=("Arial", 10), fg="#D4AF37", bg='#3d2317')
        subtitle_label.pack(pady=(0, 10))
        
        # Buttons container with enhanced styling
        buttons_frame = tk.Frame(inner_container, bg='#2c1810')
        buttons_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Create user type buttons with enhanced modern styling
        self.create_enhanced_button(buttons_frame, "👨‍🎓 STUDENT/STAFF", self.student_staff_clicked, "#D4AF37", "#8B7355")
        self.create_enhanced_button(buttons_frame, "👤 GUEST", self.guest_clicked, "#D4AF37", "#8B7355")
        self.create_enhanced_button(buttons_frame, "⚙️ ADMIN", self.admin_clicked, "#CD853F", "#A0522D")
        
        # Separator line
        separator = tk.Frame(buttons_frame, bg='#5c3e28', height=1)
        separator.pack(fill="x", pady=15)
        
        # Exit button with enhanced styling
        exit_frame = tk.Frame(buttons_frame, bg='#2c1810', height=55)
        exit_frame.pack(fill="x", pady=(5, 10))
        exit_frame.pack_propagate(False)
        
        exit_btn = tk.Button(exit_frame, text="🚪 EXIT SYSTEM", 
                           font=("Arial", 12, "bold"), bg="#8B4513", fg="#F5DEB3",
                           bd=0, cursor="hand2", command=self.exit_system, 
                           relief='flat', activebackground="#A0522D", activeforeground="white")
        exit_btn.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Enhanced hover effects for exit button
        def exit_on_enter(e):
            exit_btn.config(bg="#A0522D", relief='raised', bd=1)
        def exit_on_leave(e):
            exit_btn.config(bg="#8B4513", relief='flat', bd=0)
        
        exit_btn.bind("<Enter>", exit_on_enter)
        exit_btn.bind("<Leave>", exit_on_leave)
        
        # Bring overlay to front
        self.main_overlay.lift()
        
    def create_enhanced_button(self, parent, text, command, primary_color, secondary_color):
        """Create enhanced styled button with advanced hover effects and icons"""
        btn_frame = tk.Frame(parent, bg='#2c1810', height=65)
        btn_frame.pack(fill="x", pady=8)
        btn_frame.pack_propagate(False)
        
        # Button container for 3D effect
        btn_container = tk.Frame(btn_frame, bg=secondary_color, bd=0)
        btn_container.pack(fill="both", expand=True, padx=8, pady=3)
        
        # Main button
        btn = tk.Button(btn_container, text=text, font=("Arial", 14, "bold"),
                       bg=primary_color, fg="#2F1B14", bd=0, cursor="hand2",
                       command=command, relief='flat', 
                       activebackground="#F0E68C", activeforeground="#2F1B14",
                       padx=20, pady=15)
        btn.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Advanced hover effects with smooth transitions
        def on_enter(e):
            btn.config(bg="#F0E68C", relief='raised', bd=1)
            btn_container.config(bg="#B8860B")
            # Add subtle scaling effect
            btn.config(font=("Arial", 15, "bold"))
            
        def on_leave(e):
            btn.config(bg=primary_color, relief='flat', bd=0)
            btn_container.config(bg=secondary_color)
            btn.config(font=("Arial", 14, "bold"))
            
        def on_click(e):
            btn.config(bg="#DAA520", relief='sunken')
            parent.after(100, lambda: btn.config(relief='flat'))
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)
        
    def student_staff_clicked(self):
        """Handle student button click"""
        self.run_function(self.student_function, "Student/Staff Verification")
        
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
