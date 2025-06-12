import tkinter as tk
from tkinter import messagebox

def show_message_gui(title, message):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo(title, message)
    root.destroy()

def show_results_gui(title, message):
    """Show results in GUI message box"""
    show_message_gui(title, message)

def get_guest_info_gui(detected_name):
    """Collect guest information through GUI interface"""
    root = tk.Tk()
    root.title("Guest Information")
    root.geometry("400x300")
    root.resizable(False, False)
    
    guest_data = {}
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill='both', expand=True)
    
    # Header
    tk.Label(main_frame, text="👤 Guest Information", 
             font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    # Name field
    tk.Label(main_frame, text="Full Name:", font=("Arial", 10)).pack(anchor='w')
    name_entry = tk.Entry(main_frame, width=40, font=("Arial", 10))
    name_entry.insert(0, detected_name)
    name_entry.pack(pady=(0, 10), fill='x')
    
    # Plate number field
    tk.Label(main_frame, text="Plate Number:", font=("Arial", 10)).pack(anchor='w')
    plate_entry = tk.Entry(main_frame, width=40, font=("Arial", 10))
    plate_entry.pack(pady=(0, 10), fill='x')
    
    # Office selection
    tk.Label(main_frame, text="Office to Visit:", font=("Arial", 10)).pack(anchor='w')
    office_var = tk.StringVar(value="CSS Office")
    office_options = ["CSS Office", "Guidance", "IT Department", "Library", "Registrar", "Other"]
    office_menu = tk.OptionMenu(main_frame, office_var, *office_options)
    office_menu.config(width=35)
    office_menu.pack(pady=(0, 20), fill='x')
    
    def submit_info():
        name = name_entry.get().strip()
        plate = plate_entry.get().strip().upper()
        office = office_var.get()
        
        if not name or not plate:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return
        
        guest_data.update({
            'name': name,
            'plate_number': plate,
            'office': office,
            'submitted': True
        })
        root.quit()
    
    def cancel_info():
        guest_data['submitted'] = False
        root.quit()
    
    # Buttons
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill='x')
    
    tk.Button(button_frame, text="✅ Submit", command=submit_info, 
              bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side='left', padx=(0, 10))
    
    tk.Button(button_frame, text="❌ Cancel", command=cancel_info,
              bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side='right')
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f'+{x}+{y}')
    
    root.mainloop()
    root.destroy()
    
    return guest_data if guest_data.get('submitted', False) else None

def updated_guest_office_gui(guest_name, current_office):
    """Allow a returning guest to update their office location"""
    root = tk.Tk()
    root.title("Select New Office")
    root.geometry("400x300")
    root.resizable(False, False)
    
    guest_data = {}
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill='both', expand=True)
    
    # Header
    tk.Label(main_frame, text=f"👤 {guest_name}'s Return Visit",
             font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    # Office selection
    tk.Label(main_frame, text="Select New Office:", font=("Arial", 10)).pack(anchor='w')
    office_var = tk.StringVar(value=current_office)  # Default to the current office
    office_options = ["CSS Office", "Guidance", "IT Department", "Library", "Registrar", "Other"]
    
    office_menu = tk.OptionMenu(main_frame, office_var, *office_options)
    office_menu.config(width=35)
    office_menu.pack(pady=(0, 20), fill='x')
    
    # Update and Cancel buttons
    def submit_info():
        selected_office = office_var.get()
        
        guest_data.update({
			'name': guest_name, 
            'office': selected_office,
            'updated': True
        })
        root.quit()
    
    def cancel_info():
        guest_data['updated'] = False
        root.quit()
    
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill='x')
    
    tk.Button(button_frame, text="✅ Update", command=submit_info,
              bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side='left', padx=(0, 10))
    
    tk.Button(button_frame, text="❌ Cancel", command=cancel_info,
              bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side='right')
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f'+{x}+{y}')
    
    root.mainloop()
    root.destroy()
    
    return guest_data if guest_data.get('updated', False) else None
