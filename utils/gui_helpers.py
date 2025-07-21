# utils/gui_helpers.py - Fixed GUI Helper Functions
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os

def show_results_gui(title, image=None, text="", success=True, details=None):
    """Display results in a GUI window"""
    # Create results window
    results_window = tk.Toplevel()
    results_window.title(title)
    results_window.geometry("800x600")
    results_window.configure(bg="#FFFFFF")
    
    # Center the window
    results_window.update_idletasks()
    x = (results_window.winfo_screenwidth() // 2) - (800 // 2)
    y = (results_window.winfo_screenheight() // 2) - (600 // 2)
    results_window.geometry(f"800x600+{x}+{y}")
    
    # Main frame
    main_frame = tk.Frame(results_window, bg="#FFFFFF")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title label
    title_color = "#008000" if success else "#FF0000"
    title_label = tk.Label(main_frame, 
                          text=title,
                          font=("Arial", 18, "bold"),
                          fg=title_color,
                          bg="#FFFFFF")
    title_label.pack(pady=(0, 20))
    
    # Text message
    if text:
        text_label = tk.Label(main_frame,
                             text=text,
                             font=("Arial", 12),
                             fg="#333333",
                             bg="#FFFFFF",
                             wraplength=700,
                             justify="center")
        text_label.pack(pady=(0, 20))
    
    # Details section
    if details:
        details_frame = tk.LabelFrame(main_frame, 
                                    text="Details",
                                    font=("Arial", 12, "bold"),
                                    fg="#333333",
                                    bg="#FFFFFF")
        details_frame.pack(fill="x", pady=(0, 20))
        
        for key, value in details.items():
            detail_text = f"{key}: {value}"
            detail_label = tk.Label(details_frame,
                                  text=detail_text,
                                  font=("Arial", 10),
                                  fg="#333333",
                                  bg="#FFFFFF",
                                  anchor="w")
            detail_label.pack(fill="x", padx=10, pady=2)
    
    # OK button
    button_frame = tk.Frame(main_frame, bg="#FFFFFF")
    button_frame.pack(fill="x", pady=(20, 0))
    
    ok_button = tk.Button(button_frame,
                         text="OK",
                         font=("Arial", 12, "bold"),
                         bg="#4CAF50",
                         fg="white",
                         padx=30,
                         pady=10,
                         command=results_window.destroy)
    ok_button.pack(side="right", padx=(10, 0))
    
    # Make window modal
    results_window.transient()
    results_window.grab_set()
    results_window.wait_window()

def get_guest_info_gui(detected_name=""):
    """Enhanced guest info GUI with office buttons, mouse support, AND retake functionality"""
    # Try to import office operations
    try:
        from database.office_operation import get_all_offices
        offices_data = get_all_offices()
        use_office_buttons = True
    except ImportError:
        offices_data = []
        use_office_buttons = False
    
    # Create window
    info_window = tk.Toplevel()
    info_window.title("Guest Registration")
    
    if use_office_buttons and offices_data:
        info_window.geometry("600x500")
    else:
        info_window.geometry("500x400")
    
    info_window.configure(bg="#FFFFFF")
    
    # Center window
    info_window.update_idletasks()
    x = (info_window.winfo_screenwidth() // 2) - (300 if use_office_buttons else 250)
    y = (info_window.winfo_screenheight() // 2) - (250 if use_office_buttons else 200)
    
    if use_office_buttons and offices_data:
        info_window.geometry(f"600x500+{x}+{y}")
    else:
        info_window.geometry(f"500x400+{x}+{y}")
    
    # Main frame
    main_frame = tk.Frame(info_window, bg="#FFFFFF")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = tk.Label(main_frame, text="🎫 GUEST REGISTRATION", 
                          font=("Arial", 18, "bold"), fg="#333333", bg="#FFFFFF")
    title_label.pack(pady=(0, 20))
    
    # Name field
    tk.Label(main_frame, text="Full Name:", font=("Arial", 10, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
    name_entry = tk.Entry(main_frame, font=("Arial", 12), width=50)
    name_entry.pack(pady=(0, 15), fill="x")
    if detected_name:
        name_entry.insert(0, detected_name)
    
    # Plate number field
    tk.Label(main_frame, text="Plate Number:", font=("Arial", 10, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
    plate_entry = tk.Entry(main_frame, font=("Arial", 12), width=50)
    plate_entry.pack(pady=(0, 20), fill="x")
    
    # Office selection
    tk.Label(main_frame, text="Select Office to Visit:", font=("Arial", 10, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 10))
    
    selected_office = tk.StringVar()
    
    if use_office_buttons and offices_data:
        # OFFICE BUTTONS (Enhanced with mouse support)
        office_frame = tk.Frame(main_frame, bg="#FFFFFF")
        office_frame.pack(fill="x", pady=(0, 20))
        
        # Create buttons in grid layout
        buttons_per_row = 3
        button_widgets = []
        
        for i, office in enumerate(offices_data):
            row = i // buttons_per_row
            col = i % buttons_per_row
            
            def make_select_office(office_name):
                def select_office():
                    selected_office.set(office_name)
                    # Update button colors
                    for btn_widget in button_widgets:
                        if btn_widget['text'] == office_name:
                            btn_widget.config(bg="#4CAF50", fg="white")
                        else:
                            btn_widget.config(bg="#f0f0f0", fg="black")
                return select_office
            
            btn = tk.Button(office_frame, text=office['office_name'], 
                           font=("Arial", 9), width=18, height=2,
                           bg="#f0f0f0", fg="black", relief="raised", bd=2,
                           cursor="hand2",  # Add cursor
                           command=make_select_office(office['office_name']))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            button_widgets.append(btn)
            
            # Add hover effects
            def on_enter(e, button=btn):
                if button['bg'] != "#4CAF50":  # Don't change if selected
                    button.config(bg="#e0e0e0")
            
            def on_leave(e, button=btn):
                if button['bg'] != "#4CAF50":  # Don't change if selected
                    button.config(bg="#f0f0f0")
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # Configure grid weights
        for i in range(buttons_per_row):
            office_frame.grid_columnconfigure(i, weight=1)
    
    else:
        # FALLBACK DROPDOWN (if office buttons not available)
        office_var = tk.StringVar(value="CSS Office")
        office_combo = ttk.Combobox(main_frame, 
                                   textvariable=office_var,
                                   font=("Arial", 10),
                                   width=47,
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
        office_combo.pack(pady=(0, 20), fill="x")
        selected_office = office_var  # Use the same variable
    
    result = [None]
    
    def submit_info():
        name = name_entry.get().strip()
        plate = plate_entry.get().strip().upper()
        office = selected_office.get()
        
        if not name:
            messagebox.showerror("Error", "Name is required!")
            name_entry.focus()
            return
        if not plate:
            messagebox.showerror("Error", "Plate number is required!")
            plate_entry.focus()
            return
        if not office:
            messagebox.showerror("Error", "Please select an office to visit!")
            return
            
        result[0] = {
            'name': name,
            'plate_number': plate,
            'office': office
        }
        info_window.destroy()
    
    def cancel():
        result[0] = None
        info_window.destroy()
    
    def retake():
        """RESTORED retake function"""
        result[0] = 'retake'
        info_window.destroy()
    
    # Bottom buttons
    button_frame = tk.Frame(main_frame, bg="#FFFFFF")
    button_frame.pack(fill="x", pady=(20, 0))
    
    # Cancel button (left)
    cancel_button = tk.Button(button_frame, text="❌ Cancel", 
                             font=("Arial", 10, "bold"), bg="#FF6B6B", fg="white",
                             padx=20, pady=8, command=cancel, cursor="hand2")
    cancel_button.pack(side="left")
    
    # RESTORED RETAKE BUTTON (center)
    retake_button = tk.Button(button_frame, text="📷 Retake License", 
                             font=("Arial", 10, "bold"), bg="#3498DB", fg="white",
                             padx=20, pady=8, command=retake, cursor="hand2")
    retake_button.pack(side="left", padx=(10, 0))
    
    # Submit button (right)
    submit_button = tk.Button(button_frame, text="✅ Register Guest", 
                             font=("Arial", 10, "bold"), bg="#4CAF50", fg="white",
                             padx=20, pady=8, command=submit_info, cursor="hand2")
    submit_button.pack(side="right")
    
    # Keyboard support
    def on_key_press(event):
        if event.keysym == 'Return':
            submit_info()
        elif event.keysym == 'Escape':
            cancel()
    
    info_window.bind('<Key>', on_key_press)
    info_window.focus_set()
    
    # Tab navigation
    name_entry.bind('<Tab>', lambda e: plate_entry.focus())
    plate_entry.bind('<Tab>', lambda e: submit_button.focus())
    
    # Window close handler
    def on_window_close():
        result[0] = None
        info_window.destroy()
    
    info_window.protocol("WM_DELETE_WINDOW", on_window_close)
    
    # Make window modal
    info_window.transient()
    info_window.grab_set()
    
    # Focus on name entry
    name_entry.focus()
    
    info_window.wait_window()
    
    return result[0]
     
def updated_guest_office_gui(guest_name, current_office):
    """Get updated office information for returning guest"""
    # Create update window
    update_window = tk.Toplevel()
    update_window.title("Update Guest Office")
    update_window.geometry("400x300")
    update_window.configure(bg="#FFFFFF")
    
    # Center the window
    update_window.update_idletasks()
    x = (update_window.winfo_screenwidth() // 2) - (200)
    y = (update_window.winfo_screenheight() // 2) - (150)
    update_window.geometry(f"400x300+{x}+{y}")
    
    # Main frame
    main_frame = tk.Frame(update_window, bg="#FFFFFF")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = tk.Label(main_frame,
                          text="Update Office Visit",
                          font=("Arial", 16, "bold"),
                          fg="#333333",
                          bg="#FFFFFF")
    title_label.pack(pady=(0, 20))
    
    # Guest info
    info_label = tk.Label(main_frame,
                         text=f"Returning Guest: {guest_name}",
                         font=("Arial", 12, "bold"),
                         fg="#0066CC",
                         bg="#FFFFFF")
    info_label.pack(pady=(0, 10))
    
    current_label = tk.Label(main_frame,
                           text=f"Previous Office: {current_office}",
                           font=("Arial", 10),
                           fg="#666666",
                           bg="#FFFFFF")
    current_label.pack(pady=(0, 20))
    
    # Office selection
    tk.Label(main_frame, text="Select Office to Visit:", font=("Arial", 10, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
    
    office_var = tk.StringVar(value=current_office)
    office_combo = ttk.Combobox(main_frame, 
                               textvariable=office_var,
                               font=("Arial", 10),
                               width=35,
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
    office_combo.pack(pady=(0, 20), fill="x")
    
    result = [None]
    
    def update_info():
        office = office_var.get().strip()
        if not office:
            office = current_office
            
        result[0] = {
            'name': guest_name,
            'office': office
        }
        update_window.destroy()
    
    def cancel():
        update_window.destroy()
    
    # Buttons
    button_frame = tk.Frame(main_frame, bg="#FFFFFF")
    button_frame.pack(fill="x", pady=(10, 0))
    
    cancel_button = tk.Button(button_frame,
                             text="Cancel",
                             font=("Arial", 10, "bold"),
                             bg="#FF6B6B",
                             fg="white",
                             padx=20,
                             pady=8,
                             cursor="hand2",
                             command=cancel)
    cancel_button.pack(side="left")
    
    update_button = tk.Button(button_frame,
                             text="Update",
                             font=("Arial", 10, "bold"),
                             bg="#4CAF50",
                             fg="white",
                             padx=20,
                             pady=8,
                             cursor="hand2",
                             command=update_info)
    update_button.pack(side="right")
    
    # Focus on office combo
    office_combo.focus()
    
    # Keyboard support
    def on_key_press(event):
        if event.keysym == 'Return':
            update_info()
        elif event.keysym == 'Escape':
            cancel()
    
    update_window.bind('<Key>', on_key_press)
    
    # Make window modal
    update_window.transient()
    update_window.grab_set()
    update_window.wait_window()
    
    return result[0]

# Add other helper functions (same as before)
def show_error_gui(title, error_message, details=None):
    """Display error message in a GUI window"""
    show_results_gui(
        title=title,
        text=error_message,
        success=False,
        details={"Error Details": details} if details else None
    )

def show_success_gui(title, message, image=None, details=None):
    """Display success message in a GUI window"""
    show_results_gui(
        title=title,
        text=message,
        image=image,
        success=True,
        details=details
    )

def show_message_gui(message, title="MotorPass", message_type="info"):
    """Show a message in a GUI dialog"""
    if message_type.lower() == "error":
        messagebox.showerror(title, message)
    elif message_type.lower() == "warning":
        messagebox.showwarning(title, message)
    elif message_type.lower() == "success":
        messagebox.showinfo(title, f"✅ {message}")
    else:
        messagebox.showinfo(title, message)

def get_user_input_gui(prompt, title="Input Required", default_value=""):
    """Get user input through a GUI dialog"""
    return simpledialog.askstring(title, prompt, initialvalue=default_value)

def confirm_action_gui(message, title="Confirm Action"):
    """Show a confirmation dialog"""
    return messagebox.askyesno(title, message)
    
def guest_timeout_confirmation_dialog(guest_info):
    """
    Show confirmation dialog for guest time-out
    
    Args:
        guest_info (dict): Guest information found in database
        
    Returns:
        str: 'timeout' to proceed, 'new_guest' for new registration, 'retake' for retake, 'cancel' to cancel
    """
    # Create dialog window
    dialog_window = tk.Toplevel()
    dialog_window.title("Guest Found - Confirm Action")
    dialog_window.geometry("600x450")
    dialog_window.configure(bg="#FFFFFF")
    dialog_window.resizable(False, False)
    
    # Center the window
    dialog_window.update_idletasks()
    x = (dialog_window.winfo_screenwidth() // 2) - (600 // 2)
    y = (dialog_window.winfo_screenheight() // 2) - (450 // 2)
    dialog_window.geometry(f"600x450+{x}+{y}")
    
    # Make window modal and stay on top
    dialog_window.transient()
    dialog_window.grab_set()
    dialog_window.attributes('-topmost', True)
    
    # Main container
    main_frame = tk.Frame(dialog_window, bg="#FFFFFF", padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)
    
    # Title with icon
    title_frame = tk.Frame(main_frame, bg="#FFFFFF")
    title_frame.pack(fill="x", pady=(0, 20))
    
    title_label = tk.Label(title_frame,
                          text="🔍 Guest Found in System",
                          font=("Arial", 18, "bold"),
                          fg="#E67E22",
                          bg="#FFFFFF")
    title_label.pack()
    
    subtitle_label = tk.Label(title_frame,
                             text="We found a matching guest who is currently timed IN",
                             font=("Arial", 11),
                             fg="#7F8C8D",
                             bg="#FFFFFF")
    subtitle_label.pack(pady=(5, 0))
    
    # Guest info display
    info_frame = tk.LabelFrame(main_frame, 
                              text=" Guest Information ",
                              font=("Arial", 12, "bold"),
                              fg="#2C3E50",
                              bg="#FFFFFF",
                              padx=20,
                              pady=15)
    info_frame.pack(fill="x", pady=(0, 20))
    
    # Display guest details
    info_items = [
        ("👤 Name:", guest_info.get('name', 'N/A')),
        ("🆔 Guest No:", guest_info.get('guest_number', 'N/A')),
        ("🚗 Plate Number:", guest_info.get('plate_number', 'N/A')),
        ("🏢 Office Visiting:", guest_info.get('office', 'N/A')),
        ("📅 Time IN:", f"{guest_info.get('last_date', 'N/A')} at {guest_info.get('last_time', 'N/A')}")
    ]
    
    for label_text, value_text in info_items:
        row = tk.Frame(info_frame, bg="#FFFFFF")
        row.pack(fill="x", pady=3)
        
        tk.Label(row, 
                text=label_text,
                font=("Arial", 11, "bold"),
                fg="#34495E",
                bg="#FFFFFF",
                width=18,
                anchor="w").pack(side="left")
        
        tk.Label(row,
                text=value_text,
                font=("Arial", 11),
                fg="#2C3E50",
                bg="#FFFFFF").pack(side="left", padx=(10, 0))
    
    # Question section
    question_frame = tk.Frame(main_frame, bg="#E8F4FD", relief="solid", bd=1)
    question_frame.pack(fill="x", pady=(0, 25))
    
    question_content = tk.Frame(question_frame, bg="#E8F4FD")
    question_content.pack(fill="x", padx=15, pady=12)
    
    tk.Label(question_content,
            text="❓ Is this you? What would you like to do?",
            font=("Arial", 12, "bold"),
            fg="#2980B9",
            bg="#E8F4FD").pack()
    
    # Store result
    result = [None]
    
    def proceed_timeout():
        result[0] = 'timeout'
        dialog_window.destroy()
    
    def register_new_guest():
        result[0] = 'new_guest'
        dialog_window.destroy()
    
    def retake_license():
        result[0] = 'retake'
        dialog_window.destroy()
    
    def cancel_action():
        result[0] = 'cancel'
        dialog_window.destroy()
    
    # Buttons frame with 2 rows
    button_container = tk.Frame(main_frame, bg="#FFFFFF")
    button_container.pack(fill="x", pady=(15, 0))
    
    # First row of buttons
    button_frame1 = tk.Frame(button_container, bg="#FFFFFF")
    button_frame1.pack(fill="x", pady=(0, 10))
    
    # Cancel button (left)
    cancel_button = tk.Button(button_frame1,
                             text="❌ Cancel",
                             font=("Arial", 11, "bold"),
                             bg="#95A5A6",
                             fg="white",
                             padx=20,
                             pady=12,
                             relief="flat",
                             cursor="hand2",
                             command=cancel_action)
    cancel_button.pack(side="left")
    
    # Retake License button (center) - RESTORED RETAKE FUNCTIONALITY
    retake_button = tk.Button(button_frame1,
                             text="📷 Retake License",
                             font=("Arial", 11, "bold"),
                             bg="#3498DB",
                             fg="white",
                             padx=20,
                             pady=12,
                             relief="flat",
                             cursor="hand2",
                             command=retake_license)
    retake_button.pack(side="left", padx=(15, 0))
    
    # Time Out button (right) - Primary action
    timeout_button = tk.Button(button_frame1,
                              text="🚪 Yes, Time Me OUT",
                              font=("Arial", 11, "bold"),
                              bg="#E74C3C",
                              fg="white",
                              padx=20,
                              pady=12,
                              relief="flat",
                              cursor="hand2",
                              command=proceed_timeout)
    timeout_button.pack(side="right")
    
    # Second row of buttons
    button_frame2 = tk.Frame(button_container, bg="#FFFFFF")
    button_frame2.pack(fill="x")
    
    # New Guest button (centered in second row)
    new_guest_button = tk.Button(button_frame2,
                                text="👤 Register as New Guest Instead",
                                font=("Arial", 11, "bold"),
                                bg="#F39C12",
                                fg="white",
                                padx=30,
                                pady=12,
                                relief="flat",
                                cursor="hand2",
                                command=register_new_guest)
    new_guest_button.pack()
    
    # Add hover effects
    def on_enter_cancel(e):
        cancel_button.config(bg="#7F8C8D")
    def on_leave_cancel(e):
        cancel_button.config(bg="#95A5A6")
        
    def on_enter_retake(e):
        retake_button.config(bg="#2980B9")
    def on_leave_retake(e):
        retake_button.config(bg="#3498DB")
        
    def on_enter_timeout(e):
        timeout_button.config(bg="#C0392B")
    def on_leave_timeout(e):
        timeout_button.config(bg="#E74C3C")
        
    def on_enter_new_guest(e):
        new_guest_button.config(bg="#E67E22")
    def on_leave_new_guest(e):
        new_guest_button.config(bg="#F39C12")
    
    # Bind hover effects
    cancel_button.bind("<Enter>", on_enter_cancel)
    cancel_button.bind("<Leave>", on_leave_cancel)
    retake_button.bind("<Enter>", on_enter_retake)
    retake_button.bind("<Leave>", on_leave_retake)
    timeout_button.bind("<Enter>", on_enter_timeout)
    timeout_button.bind("<Leave>", on_leave_timeout)
    new_guest_button.bind("<Enter>", on_enter_new_guest)
    new_guest_button.bind("<Leave>", on_leave_new_guest)
    
    # Keyboard shortcuts
    def on_key_press(event):
        if event.keysym == 'Return':  # Enter key = Time Out
            proceed_timeout()
        elif event.keysym == 'Escape':  # Escape key = Cancel
            cancel_action()
        elif event.char.lower() == 'r':  # R key = Retake
            retake_license()
        elif event.char.lower() == 'n':  # N key = New Guest
            register_new_guest()
        elif event.char.lower() == 't':  # T key = Time Out
            proceed_timeout()
    
    dialog_window.bind('<Key>', on_key_press)
    dialog_window.focus_set()
    
    # Handle window close button (X)
    def on_window_close():
        result[0] = 'cancel'
        dialog_window.destroy()
    
    dialog_window.protocol("WM_DELETE_WINDOW", on_window_close)
    
    # Wait for user choice
    dialog_window.wait_window()
    
    return result[0]
    
# -------------------- STUDENT HELPERS -----------------

def show_student_verification_gui(student_info, verification_data):
    """
    Show student verification results
    
    Args:
        student_info (dict): Student information
        verification_data (dict): Verification results
    """
    message = verification_data.get('gui_message', '')
    success = 'SUCCESSFUL' in verification_data.get('overall_status', '')
    
    details = {}
    if 'checks' in verification_data:
        for check_name, (status, message) in verification_data['checks'].items():
            details[check_name] = f"{'✅' if status else '❌'} {message}"
    
    show_results_gui(
        title="Student Verification Results",
        text=message,
        success=success,
        details=details
    )

def show_guest_verification_gui(guest_info, verification_data):
    """
    Show guest verification results
    
    Args:
        guest_info (dict): Guest information
        verification_data (dict): Verification results
    """
    message = verification_data.get('gui_message', '')
    success = 'SUCCESSFUL' in verification_data.get('overall_status', '')
    
    details = {}
    if 'checks' in verification_data:
        for check_name, (status, message) in verification_data['checks'].items():
            details[check_name] = f"{'✅' if status else '❌'} {message}"
    
    show_results_gui(
        title="Guest Verification Results",
        text=message,
        success=success,
        details=details
    )

def create_loading_dialog(title="Processing...", message="Please wait..."):
    """
    Create a loading dialog window
    
    Args:
        title (str): Dialog title
        message (str): Loading message
        
    Returns:
        tk.Toplevel: The loading window (call destroy() when done)
    """
    loading_window = tk.Toplevel()
    loading_window.title(title)
    loading_window.geometry("300x150")
    loading_window.configure(bg="#FFFFFF")
    
    # Center the window
    loading_window.update_idletasks()
    x = (loading_window.winfo_screenwidth() // 2) - (300 // 2)
    y = (loading_window.winfo_screenheight() // 2) - (150 // 2)
    loading_window.geometry(f"300x150+{x}+{y}")
    
    # Remove window decorations
    loading_window.overrideredirect(True)
    
    # Main frame with border
    main_frame = tk.Frame(loading_window, bg="#FFFFFF", bd=2, relief="raised")
    main_frame.pack(fill="both", expand=True)
    
    # Loading message
    message_label = tk.Label(main_frame,
                           text=message,
                           font=("Arial", 12, "bold"),
                           fg="#333333",
                           bg="#FFFFFF")
    message_label.pack(pady=20)
    
    # Progress bar
    progress = ttk.Progressbar(main_frame, mode='indeterminate', length=200)
    progress.pack(pady=10)
    progress.start()
    
    # Make window stay on top
    loading_window.lift()
    loading_window.attributes('-topmost', True)
    
    return loading_window
