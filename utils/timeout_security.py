# utils/timeout_security.py - Security verification for guest timeout

import tkinter as tk
from tkinter import messagebox
from database.office_operation import verify_office_code

def timeout_security_verification(guest_info, max_attempts=3):
    """
    Security verification for guest timeout with office code
    
    Args:
        guest_info (dict): Guest information including office
        max_attempts (int): Maximum code entry attempts
        
    Returns:
        bool: True if verification successful, False if failed/intruder
    """
    
    # Create security window
    security_window = tk.Toplevel()
    security_window.title("Security Verification")
    security_window.geometry("400x300")
    security_window.configure(bg="#FFFFFF")
    
    # Center window
    security_window.update_idletasks()
    x = (security_window.winfo_screenwidth() // 2) - (200)
    y = (security_window.winfo_screenheight() // 2) - (150)
    security_window.geometry(f"400x300+{x}+{y}")
    
    # Make window stay on top and modal
    security_window.transient()
    security_window.grab_set()
    security_window.lift()
    security_window.attributes('-topmost', True)
    
    # Main frame
    main_frame = tk.Frame(security_window, bg="#FFFFFF")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = tk.Label(main_frame, text="🔐 SECURITY VERIFICATION", 
                          font=("Arial", 16, "bold"), fg="#E74C3C", bg="#FFFFFF")
    title_label.pack(pady=(0, 10))
    
    # Guest info
    info_label = tk.Label(main_frame, text=f"Guest: {guest_info.get('name', 'Unknown')}", 
                         font=("Arial", 12, "bold"), fg="#333333", bg="#FFFFFF")
    info_label.pack(pady=(0, 5))
    
    office_label = tk.Label(main_frame, text=f"Office: {guest_info.get('office', 'Unknown')}", 
                           font=("Arial", 12), fg="#666666", bg="#FFFFFF")
    office_label.pack(pady=(0, 20))
    
    # Instructions
    instruction_label = tk.Label(main_frame, 
                                text="Enter the 3-digit code provided by\nthe office personnel:", 
                                font=("Arial", 11), fg="#333333", bg="#FFFFFF", justify="center")
    instruction_label.pack(pady=(0, 15))
    
    # Code entry
    code_entry = tk.Entry(main_frame, font=("Arial", 16), width=10, justify="center")
    code_entry.pack(pady=(0, 15))
    
    # Attempts counter
    attempts_left = [max_attempts]
    attempts_label = tk.Label(main_frame, text=f"Attempts remaining: {attempts_left[0]}", 
                             font=("Arial", 10), fg="#666666", bg="#FFFFFF")
    attempts_label.pack(pady=(0, 20))
    
    result = [None]
    
    def verify_code():
        entered_code = code_entry.get().strip()
        office_name = guest_info.get('office', '')
        
        if not entered_code:
            messagebox.showerror("Error", "Please enter the security code!")
            return
        
        if len(entered_code) != 3 or not entered_code.isdigit():
            messagebox.showerror("Error", "Code must be exactly 3 digits!")
            code_entry.delete(0, tk.END)
            return
        
        # Verify code
        if verify_office_code(office_name, entered_code):
            result[0] = True
            messagebox.showinfo("✅ Verified", "Security code verified!\nTimeout successful.")
            security_window.destroy()
        else:
            attempts_left[0] -= 1
            
            if attempts_left[0] > 0:
                attempts_label.config(text=f"Attempts remaining: {attempts_left[0]}")
                messagebox.showerror("❌ Invalid Code", 
                                   f"Incorrect code!\nAttempts remaining: {attempts_left[0]}")
                code_entry.delete(0, tk.END)
                code_entry.focus_set()
            else:
                result[0] = False
                messagebox.showerror("🚨 SECURITY ALERT", 
                                   "Maximum attempts exceeded!\n" +
                                   "Possible intruder detected.\n" +
                                   "Timeout DENIED.")
                security_window.destroy()
    
    def cancel_timeout():
        result[0] = False
        security_window.destroy()
    
    # Buttons
    button_frame = tk.Frame(main_frame, bg="#FFFFFF")
    button_frame.pack(fill="x", pady=(10, 0))
    
    cancel_button = tk.Button(button_frame, text="❌ Cancel", 
                             font=("Arial", 10, "bold"), bg="#FF6B6B", fg="white",
                             padx=20, pady=8, command=cancel_timeout, cursor="hand2")
    cancel_button.pack(side="left")
    
    verify_button = tk.Button(button_frame, text="🔍 Verify Code", 
                             font=("Arial", 10, "bold"), bg="#4CAF50", fg="white",
                             padx=20, pady=8, command=verify_code, cursor="hand2")
    verify_button.pack(side="right")
    
    # Enter key binding
    code_entry.bind('<Return>', lambda event: verify_code())
    
    # Focus on code entry
    code_entry.focus_set()
    
    # Window close handler
    def on_window_close():
        result[0] = False
        security_window.destroy()
    
    security_window.protocol("WM_DELETE_WINDOW", on_window_close)
    
    # Wait for result
    security_window.wait_window()
    
    return result[0] if result[0] is not None else False
