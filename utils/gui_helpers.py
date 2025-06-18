# utils/gui_helpers.py - Fixed GUI Helper Functions
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os

def show_results_gui(title, image=None, text="", success=True, details=None):
    """
    Display results in a GUI window
    
    Args:
        title (str): Window title
        image (np.array or None): Image to display (OpenCV format)
        text (str): Text message to display
        success (bool): Whether the operation was successful
        details (dict or None): Additional details to display
    """
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
    title_color = "#008000" if success else "#FF0000"  # Green for success, red for failure
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
    
    # Details section (if provided)
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
    
    # Buttons frame
    button_frame = tk.Frame(main_frame, bg="#FFFFFF")
    button_frame.pack(fill="x", pady=(20, 0))
    
    # OK button
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
    
    # Wait for window to close
    results_window.wait_window()

def show_error_gui(title, error_message, details=None):
    """
    Display error message in a GUI window
    """
    show_results_gui(
        title=title,
        text=error_message,
        success=False,
        details={"Error Details": details} if details else None
    )

def show_success_gui(title, message, image=None, details=None):
    """
    Display success message in a GUI window
    """
    show_results_gui(
        title=title,
        text=message,
        image=image,
        success=True,
        details=details
    )

def get_guest_info_gui(detected_name=""):
    """
    Get guest information through a GUI form
    
    Args:
        detected_name (str): Pre-detected name from license
        
    Returns:
        dict or None: Guest information or None if cancelled
    """
    # Create input window
    info_window = tk.Toplevel()
    info_window.title("Guest Information")
    info_window.geometry("500x400")
    info_window.configure(bg="#FFFFFF")
    
    # Center the window
    info_window.update_idletasks()
    x = (info_window.winfo_screenwidth() // 2) - (500 // 2)
    y = (info_window.winfo_screenheight() // 2) - (400 // 2)
    info_window.geometry(f"500x400+{x}+{y}")
    
    # Main frame
    main_frame = tk.Frame(info_window, bg="#FFFFFF")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = tk.Label(main_frame,
                          text="Guest Registration",
                          font=("Arial", 16, "bold"),
                          fg="#333333",
                          bg="#FFFFFF")
    title_label.pack(pady=(0, 20))
    
    # Result variable
    result = [None]  # Use list to modify from inner function
    
    # Name field
    tk.Label(main_frame, text="Full Name:", font=("Arial", 10, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
    name_entry = tk.Entry(main_frame, font=("Arial", 10), width=40)
    name_entry.pack(pady=(0, 15), fill="x")
    if detected_name:
        name_entry.insert(0, detected_name)
    
    # Plate number field
    tk.Label(main_frame, text="Plate Number:", font=("Arial", 10, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
    plate_entry = tk.Entry(main_frame, font=("Arial", 10), width=40)
    plate_entry.pack(pady=(0, 15), fill="x")
    
    # Office field
    tk.Label(main_frame, text="Office to Visit:", font=("Arial", 10, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
    office_var = tk.StringVar(value="CSS Office")
    office_combo = ttk.Combobox(main_frame, 
                               textvariable=office_var,
                               font=("Arial", 10),
                               width=37,
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
    
    def submit_info():
        name = name_entry.get().strip()
        plate = plate_entry.get().strip().upper()
        office = office_var.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Name is required!")
            return
        if not plate:
            messagebox.showerror("Error", "Plate number is required!")
            return
        if not office:
            office = "CSS Office"
            
        result[0] = {
            'name': name,
            'plate_number': plate,
            'office': office
        }
        info_window.destroy()
    
    def cancel():
        info_window.destroy()
    
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
                             command=cancel)
    cancel_button.pack(side="left")
    
    submit_button = tk.Button(button_frame,
                             text="Submit",
                             font=("Arial", 10, "bold"),
                             bg="#4CAF50",
                             fg="white",
                             padx=20,
                             pady=8,
                             command=submit_info)
    submit_button.pack(side="right")
    
    # Focus on name field
    name_entry.focus()
    
    # Bind Enter key to submit
    def on_enter(event):
        submit_info()
    
    info_window.bind('<Return>', on_enter)
    
    # Make window modal
    info_window.transient()
    info_window.grab_set()
    info_window.wait_window()
    
    return result[0]

def updated_guest_office_gui(guest_name, current_office):
    """
    Get updated office information for returning guest
    
    Args:
        guest_name (str): Guest name
        current_office (str): Current office on record
        
    Returns:
        dict or None: Updated guest info or None if cancelled
    """
    # Create update window
    update_window = tk.Toplevel()
    update_window.title("Update Guest Office")
    update_window.geometry("400x300")
    update_window.configure(bg="#FFFFFF")
    
    # Center the window
    update_window.update_idletasks()
    x = (update_window.winfo_screenwidth() // 2) - (400 // 2)
    y = (update_window.winfo_screenheight() // 2) - (300 // 2)
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
                             command=cancel)
    cancel_button.pack(side="left")
    
    update_button = tk.Button(button_frame,
                             text="Update",
                             font=("Arial", 10, "bold"),
                             bg="#4CAF50",
                             fg="white",
                             padx=20,
                             pady=8,
                             command=update_info)
    update_button.pack(side="right")
    
    # Focus on office combo
    office_combo.focus()
    
    # Make window modal
    update_window.transient()
    update_window.grab_set()
    update_window.wait_window()
    
    return result[0]

def show_message_gui(message, title="MotorPass", message_type="info"):
    """
    Show a message in a GUI dialog
    
    Args:
        message (str): Message to display
        title (str): Dialog title
        message_type (str): Type of message ('info', 'warning', 'error', 'success')
    """
    if message_type.lower() == "error":
        messagebox.showerror(title, message)
    elif message_type.lower() == "warning":
        messagebox.showwarning(title, message)
    elif message_type.lower() == "success":
        messagebox.showinfo(title, f"✅ {message}")
    else:  # default to info
        messagebox.showinfo(title, message)

def get_user_input_gui(prompt, title="Input Required", default_value=""):
    """
    Get user input through a GUI dialog
    
    Args:
        prompt (str): Prompt message
        title (str): Dialog title
        default_value (str): Default value
        
    Returns:
        str or None: User input or None if cancelled
    """
    return simpledialog.askstring(title, prompt, initialvalue=default_value)

def confirm_action_gui(message, title="Confirm Action"):
    """
    Show a confirmation dialog
    
    Args:
        message (str): Confirmation message
        title (str): Dialog title
        
    Returns:
        bool: True if confirmed, False otherwise
    """
    return messagebox.askyesno(title, message)

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
