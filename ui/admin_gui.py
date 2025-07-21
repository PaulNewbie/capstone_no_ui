# ui/admin_gui.py - Complete Fixed Admin Panel GUI with Office Management

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from datetime import datetime
import os
from PIL import Image, ImageTk
import json

class AdminPanelGUI:
    def __init__(self, admin_functions, skip_auth=False):
        self.root = tk.Tk()
        self.admin_functions = admin_functions
        self.authenticated = skip_auth
        
        self.colors = {
            'primary': '#2C3E50',      # Dark blue-gray
            'secondary': '#34495E',     # Lighter blue-gray
            'accent': '#E74C3C',        # Red accent
            'success': '#27AE60',       # Green
            'warning': '#F39C12',       # Orange
            'info': '#3498DB',          # Blue
            'light': '#ECF0F1',         # Light gray
            'dark': '#1A252F',          # Very dark
            'gold': '#F1C40F',          # Gold
            'white': '#FFFFFF'
        }
        
        self.setup_window()
        self.create_variables()
        
        if skip_auth:
            self.show_admin_panel()
        else:
            self.create_authentication_screen()
        
    # Menu Action Functions
    def enroll_user(self):
        """Enroll new user - SIMPLE FIX"""
        result = messagebox.askquestion("Enroll User", 
                                   "This will start the enrollment process.\n\n" +
                                   "You will need:\n" +
                                   "• Student/Staff ID\n" +
                                   "• User's fingerprint\n\n" +
                                   "Continue?",
                                   icon='info')
        if result == 'yes':
            # Show loading message
            messagebox.showinfo("Enrollment Started", 
                          "Enrollment process starting...\n\n" +
                          "Please check the terminal for instructions.",
                          icon='info')
        
            # Run enrollment in background without complex threading
            try:
                self.admin_functions['enroll']()
            except Exception as e:
                messagebox.showerror("Enrollment Error", 
                               f"Enrollment failed:\n\n{str(e)}",
                               icon='error')
    
    def view_users(self):
        """View enrolled users"""
        thread = threading.Thread(target=self.load_and_display_users, daemon=True)
        thread.start()
    
    def load_and_display_users(self):
        """Load and display users in a new window"""
        try:
            # Load fingerprint database
            database_path = "json_folder/fingerprint_database.json"
            if os.path.exists(database_path):
                with open(database_path, 'r') as f:
                    database = json.load(f)
            else:
                database = {}
            
            self.root.after(0, lambda: self.display_users_window(database))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load users: {str(e)}"))
    
    def display_users_window(self, database):
        """Display users in a modern window"""
        # Create new window
        users_window = tk.Toplevel(self.root)
        users_window.title("Enrolled Users Database")
        users_window.geometry("1000x700")
        users_window.configure(bg=self.colors['light'])
        
        # Header
        header = tk.Frame(users_window, bg=self.colors['primary'], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="👥 ENROLLED USERS DATABASE", 
                font=("Arial", 22, "bold"), fg=self.colors['white'], 
                bg=self.colors['primary']).pack(expand=True)
        
        # Stats bar
        stats_bar = tk.Frame(users_window, bg=self.colors['secondary'])
        stats_bar.pack(fill="x")
        
        student_count = sum(1 for info in database.values() if info.get('user_type') == 'STUDENT')
        staff_count = sum(1 for info in database.values() if info.get('user_type') == 'STAFF')
        
        stats_content = tk.Frame(stats_bar, bg=self.colors['secondary'])
        stats_content.pack(pady=15)
        
        for label, value, color in [
            ("Total Users", len(database) - 1, self.colors['gold']),  # -1 to exclude admin
            ("Students", student_count, self.colors['success']),
            ("Staff", staff_count, self.colors['info'])
        ]:
            stat_item = tk.Frame(stats_content, bg=self.colors['secondary'])
            stat_item.pack(side="left", padx=30)
            tk.Label(stat_item, text=label, font=("Arial", 11), 
                    fg=self.colors['light'], bg=self.colors['secondary']).pack()
            tk.Label(stat_item, text=str(value), font=("Arial", 20, "bold"), 
                    fg=color, bg=self.colors['secondary']).pack()
        
        # Create scrollable frame
        container = tk.Frame(users_window, bg=self.colors['white'])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        canvas = tk.Canvas(container, bg=self.colors['white'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['white'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind keyboard arrow keys for scrolling
        def _on_key_press(event):
            if event.keysym == 'Up':
                canvas.yview_scroll(-3, "units")
            elif event.keysym == 'Down':
                canvas.yview_scroll(3, "units")
            elif event.keysym == 'Page_Up':
                canvas.yview_scroll(-10, "units")
            elif event.keysym == 'Page_Down':
                canvas.yview_scroll(10, "units")
        
        # Bind events
        canvas.bind("<MouseWheel>", _on_mousewheel)
        container.bind("<MouseWheel>", _on_mousewheel)
        users_window.bind("<MouseWheel>", _on_mousewheel)
        
        # Make window focusable and bind arrow keys
        users_window.focus_set()
        users_window.bind("<Key>", _on_key_press)
        users_window.bind("<Up>", _on_key_press)
        users_window.bind("<Down>", _on_key_press)
        users_window.bind("<Page_Up>", _on_key_press)
        users_window.bind("<Page_Down>", _on_key_press)
        
        # User cards
        for slot_id, info in sorted(database.items(), key=lambda x: x[0]):
            if slot_id == "1":  # Skip admin
                continue
            self.create_modern_user_card(scrollable_frame, slot_id, info)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update scroll region after adding all cards
        users_window.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Close button
        close_btn = tk.Button(users_window, text="CLOSE", 
                             font=("Arial", 12, "bold"), 
                             bg=self.colors['accent'], fg=self.colors['white'],
                             relief='flat', bd=0, cursor="hand2",
                             padx=40, pady=12, command=users_window.destroy)
        close_btn.pack(pady=20)
    
    def create_modern_user_card(self, parent, slot_id, info):
        """Create a modern user information card"""
        # Card container with shadow
        card_container = tk.Frame(parent, bg=self.colors['white'])
        card_container.pack(fill="x", padx=10, pady=10)
        
        # Card
        card = tk.Frame(card_container, bg=self.colors['light'], relief='flat', bd=0)
        card.pack(fill="x", padx=2, pady=2)
        
        # Type indicator
        type_color = self.colors['success'] if info.get('user_type') == 'STUDENT' else self.colors['info']
        type_bar = tk.Frame(card, bg=type_color, width=5)
        type_bar.pack(side="left", fill="y")
        
        # Content
        content = tk.Frame(card, bg=self.colors['light'])
        content.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        
        # Header row
        header_row = tk.Frame(content, bg=self.colors['light'])
        header_row.pack(fill="x", pady=(0, 10))
        
        # Name and type
        name_frame = tk.Frame(header_row, bg=self.colors['light'])
        name_frame.pack(side="left")
        
        tk.Label(name_frame, text=info.get('name', 'N/A'), 
                font=("Arial", 14, "bold"), fg=self.colors['dark'], 
                bg=self.colors['light']).pack(anchor="w")
        
        type_text = f"{info.get('user_type', 'UNKNOWN')} • Slot #{slot_id}"
        tk.Label(name_frame, text=type_text, 
                font=("Arial", 10), fg=type_color, 
                bg=self.colors['light']).pack(anchor="w")
        
        # Details grid
        details_frame = tk.Frame(content, bg=self.colors['light'])
        details_frame.pack(fill="x")
        
        # Create two columns
        col1 = tk.Frame(details_frame, bg=self.colors['light'])
        col1.pack(side="left", fill="both", expand=True)
        
        col2 = tk.Frame(details_frame, bg=self.colors['light'])
        col2.pack(side="left", fill="both", expand=True)
        
        # Column 1 details
        if info.get('user_type') == 'STUDENT':
            self.add_detail_row(col1, "ID:", info.get('student_id', 'N/A'))
            self.add_detail_row(col1, "Course:", info.get('course', 'N/A'))
        else:
            self.add_detail_row(col1, "ID:", info.get('staff_no', 'N/A'))
            self.add_detail_row(col1, "Role:", info.get('staff_role', 'N/A'))
        
        # Column 2 details
        self.add_detail_row(col2, "License:", info.get('license_number', 'N/A'))
        self.add_detail_row(col2, "Plate:", info.get('plate_number', 'N/A'))
    
    def add_detail_row(self, parent, label, value):
        """Add a detail row"""
        row = tk.Frame(parent, bg=self.colors['light'])
        row.pack(fill="x", pady=2)
        
        tk.Label(row, text=label, font=("Arial", 10), 
                fg=self.colors['secondary'], bg=self.colors['light'], 
                width=10, anchor="w").pack(side="left")
        tk.Label(row, text=value, font=("Arial", 10, "bold"), 
                fg=self.colors['dark'], bg=self.colors['light']).pack(side="left")
    
    def delete_user(self):
        """Delete user fingerprint - FIXED"""
        slot_id = simpledialog.askstring("Delete User", 
                                       "Enter Slot ID to delete:",
                                       parent=self.root)
        
        if slot_id:
            if slot_id == "1":
                messagebox.showerror("Error", "Cannot delete admin slot!")
                return
            
            if messagebox.askyesno("Confirm Delete", 
                                 f"Delete user at slot #{slot_id}?\n\nThis cannot be undone!",
                                 icon='warning'):
                thread = threading.Thread(target=lambda: self.run_delete(slot_id), daemon=True)
                thread.start()
    
    def run_delete(self, slot_id):
        """Run delete operation"""
        try:
            # Call delete function with slot_id
            self.admin_functions['delete_fingerprint'](slot_id)
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                                                          f"User at slot #{slot_id} deleted successfully!",
                                                          icon='info'))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Delete failed: {str(e)}"))
    
    def sync_database(self):
        """Sync database from Google Sheets"""
        result = messagebox.askyesno("Sync Database", 
                                    "Sync student/staff data from Google Sheets?\n\n" +
                                    "This will update the database with latest registrations.",
                                    icon='question')
        if result:
            thread = threading.Thread(target=lambda: self.run_function('sync'), daemon=True)
            thread.start()
    
    def view_time_records(self):
        """View time records"""
        thread = threading.Thread(target=self.load_and_display_time_records, daemon=True)
        thread.start()
    
    def load_and_display_time_records(self):
        """Load and display time records"""
        try:
            records = self.admin_functions['get_time_records']()
            self.root.after(0, lambda: self.display_time_records_window(records))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load records: {str(e)}"))
    
    def display_time_records_window(self, records):
        """Display time records in a modern window"""
        # Create new window
        records_window = tk.Toplevel(self.root)
        records_window.title("Time Records")
        records_window.geometry("900x600")
        records_window.configure(bg=self.colors['light'])
        
        # Header
        header = tk.Frame(records_window, bg=self.colors['primary'], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🕒 TIME RECORDS", 
                font=("Arial", 22, "bold"), fg=self.colors['white'], 
                bg=self.colors['primary']).pack(expand=True)
        
        if not records:
            # Empty state
            empty_frame = tk.Frame(records_window, bg=self.colors['white'])
            empty_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            tk.Label(empty_frame, text="📭", font=("Arial", 48), 
                    fg=self.colors['light'], bg=self.colors['white']).pack(pady=(50, 20))
            tk.Label(empty_frame, text="No time records found", 
                    font=("Arial", 16), fg=self.colors['secondary'], 
                    bg=self.colors['white']).pack()
        else:
            # Create modern table
            table_frame = tk.Frame(records_window, bg=self.colors['white'])
            table_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Configure style
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('Treeview', 
                          background=self.colors['white'],
                          fieldbackground=self.colors['white'],
                          borderwidth=0,
                          font=('Arial', 10))
            style.configure('Treeview.Heading', 
                          background=self.colors['light'],
                          font=('Arial', 11, 'bold'))
            style.map('Treeview', background=[('selected', self.colors['info'])])
            
            # Create treeview
            tree = ttk.Treeview(table_frame, 
                               columns=('Date', 'Time', 'ID', 'Name', 'Type', 'Status'), 
                               show='tree headings', height=20)
            
            # Configure columns
            tree.column('#0', width=0, stretch=False)
            tree.column('Date', width=120)
            tree.column('Time', width=100)
            tree.column('ID', width=120)
            tree.column('Name', width=200)
            tree.column('Type', width=100)
            tree.column('Status', width=80)
            
            # Configure headings
            for col in ['Date', 'Time', 'ID', 'Name', 'Type', 'Status']:
                tree.heading(col, text=col)
            
            # Add records with alternating colors
            for i, record in enumerate(records):
                values = (
                    record.get('date', 'N/A'),
                    record.get('time', 'N/A'),
                    record.get('student_id', 'N/A'),
                    record.get('student_name', 'N/A'),
                    record.get('user_type', 'STUDENT'),
                    record.get('status', 'N/A')
                )
                
                tag = 'even' if i % 2 == 0 else 'odd'
                status_tag = 'in' if record.get('status') == 'IN' else 'out'
                tree.insert('', 'end', values=values, tags=(tag, status_tag))
            
            # Configure tags
            tree.tag_configure('even', background=self.colors['light'])
            tree.tag_configure('odd', background=self.colors['white'])
            tree.tag_configure('in', foreground=self.colors['success'])
            tree.tag_configure('out', foreground=self.colors['accent'])
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
        
        # Close button
        close_btn = tk.Button(records_window, text="CLOSE", 
                             font=("Arial", 12, "bold"), 
                             bg=self.colors['accent'], fg=self.colors['white'],
                             relief='flat', bd=0, cursor="hand2",
                             padx=40, pady=12, command=records_window.destroy)
        close_btn.pack(pady=20)
    
    def clear_time_records(self):
        """Clear all time records - FIXED"""
        # Custom confirmation dialog
        if messagebox.askyesno("Clear Records", 
                              "Delete ALL time records?\n\n" +
                              "This will permanently remove all attendance data!",
                              icon='warning'):
            # Double confirmation
            if messagebox.askyesno("Final Confirmation", 
                                 "Are you ABSOLUTELY SURE?\n\n" +
                                 "All time records will be deleted permanently!",
                                 icon='warning'):
                # FIXED: Call the function directly instead of through run_function
                try:
                    # Import the function directly
                    from database.db_operations import clear_all_time_records
                    
                    if clear_all_time_records():
                        messagebox.showinfo("✅ Success", 
                                          "All time records have been cleared successfully!",
                                          icon='info')
                    else:
                        messagebox.showerror("❌ Error", 
                                           "Failed to clear records. Please try again.",
                                           icon='error')
                except Exception as e:
                    messagebox.showerror("❌ Error", 
                                       f"Failed to clear records:\n\n{str(e)}",
                                       icon='error')
    
    def open_dashboard(self):
        """Open web dashboard"""
        import webbrowser
        try:
            webbrowser.open("http://localhost:5000")
            messagebox.showinfo("Dashboard Opened", 
                              "Web dashboard opened in your browser!\n\n" +
                              "Default login: admin / motorpass123",
                              icon='info')
        except:
            messagebox.showerror("Error", "Failed to open web dashboard")
    
    def exit_system(self):
        """Exit the system"""
        if messagebox.askyesno("Exit Admin Panel", 
                              "Exit the admin panel?\n\n" +
                              "You will return to the main menu.",
                              icon='question'):
            self.close()
    
    def show_office_management(self):
        """Show office management window"""
        # Create office management window
        office_window = tk.Toplevel(self.root)
        office_window.title("System Maintenance - Office Management")
        office_window.geometry("700x600")
        office_window.configure(bg=self.colors['white'])
        
        # Center window
        office_window.update_idletasks()
        x = (office_window.winfo_screenwidth() // 2) - (350)
        y = (office_window.winfo_screenheight() // 2) - (300)
        office_window.geometry(f"700x600+{x}+{y}")
        
        # Header
        header = tk.Frame(office_window, bg=self.colors['primary'], height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg=self.colors['primary'])
        header_content.pack(expand=True)
        
        tk.Label(header_content, text="🏢 SYSTEM MAINTENANCE", 
                font=("Arial", 20, "bold"), fg=self.colors['white'], 
                bg=self.colors['primary']).pack(pady=15)
        
        tk.Label(header_content, text="Office Management & Security Code Configuration", 
                font=("Arial", 11), fg=self.colors['light'], 
                bg=self.colors['primary']).pack()
        
        # Content
        content = tk.Frame(office_window, bg=self.colors['white'])
        content.pack(fill="both", expand=True)
        
        # Add office management section
        self.create_office_management_section(content)
        
        # Footer with close button
        footer = tk.Frame(office_window, bg=self.colors['light'], height=60)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        close_btn = tk.Button(footer, text="✅ CLOSE", 
                             font=("Arial", 12, "bold"), 
                             bg=self.colors['accent'], fg=self.colors['white'],
                             relief='flat', bd=0, cursor="hand2",
                             padx=40, pady=12, command=office_window.destroy)
        close_btn.pack(pady=15)

    def create_office_management_section(self, parent):
        """Add office management to admin panel"""
        try:
            from database.office_operation import get_all_offices, add_office, update_office_code, delete_office
        except ImportError:
            # Show error if office operations not available
            error_frame = tk.Frame(parent, bg=self.colors['white'])
            error_frame.pack(fill="x", padx=10, pady=5)
            tk.Label(error_frame, text="⚠️ Office Management System Not Available", 
                    font=("Arial", 12, "bold"), fg=self.colors['accent'], 
                    bg=self.colors['white']).pack(pady=20)
            return
        
        # Office Management Frame
        office_frame = tk.LabelFrame(parent, text="🏢 Office Management & Security Codes", 
                                    font=("Arial", 12, "bold"), 
                                    bg=self.colors['white'], fg=self.colors['primary'],
                                    relief="ridge", bd=2)
        office_frame.pack(fill="x", padx=10, pady=5)
        
        # Instructions
        instruction_label = tk.Label(office_frame, 
                                    text="Manage visitor offices and their 3-digit security codes for timeout verification",
                                    font=("Arial", 10), fg=self.colors['secondary'],
                                    bg=self.colors['white'])
        instruction_label.pack(pady=(10, 0))
        
        # Office list with scrollbar
        list_frame = tk.Frame(office_frame, bg=self.colors['white'])
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        offices_list = tk.Listbox(list_frame, height=8, font=("Arial", 10))
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=offices_list.yview)
        offices_list.configure(yscrollcommand=scrollbar.set)
        
        offices_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def refresh_office_list():
            offices_list.delete(0, tk.END)
            offices = get_all_offices()
            for office in offices:
                offices_list.insert(tk.END, f"{office['office_name']} (Code: {office['office_code']})")
        
        # Buttons frame
        btn_frame = tk.Frame(office_frame, bg=self.colors['white'])
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        def add_new_office():
            office_name = simpledialog.askstring("Add Office", "Enter office name:")
            if office_name and office_name.strip():
                if add_office(office_name.strip()):
                    messagebox.showinfo("Success", f"Office '{office_name}' added successfully!\nA unique 3-digit code has been generated.")
                    refresh_office_list()
                else:
                    messagebox.showerror("Error", "Failed to add office!")
        
        def update_office_code_gui():
            selection = offices_list.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select an office first!")
                return
            
            office_text = offices_list.get(selection[0])
            office_name = office_text.split(" (Code:")[0]
            current_code = office_text.split("Code: ")[1].replace(")", "")
            
            new_code = simpledialog.askstring("Update Security Code", 
                                             f"Current code for '{office_name}': {current_code}\n\nEnter new 3-digit code:")
            if new_code and new_code.strip():
                if update_office_code(office_name, new_code.strip()):
                    messagebox.showinfo("Success", f"Security code updated for '{office_name}'!")
                    refresh_office_list()
                else:
                    messagebox.showerror("Error", "Failed to update code! Make sure it's exactly 3 digits and not already in use.")
        
        def delete_office_gui():
            selection = offices_list.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select an office first!")
                return
            
            office_text = offices_list.get(selection[0])
            office_name = office_text.split(" (Code:")[0]
            
            if messagebox.askyesno("Confirm Delete", 
                                  f"Delete office '{office_name}'?\n\nThis will:\n• Remove the office from visitor selection\n• Disable its security code\n• This action cannot be undone!"):
                if delete_office(office_name):
                    messagebox.showinfo("Success", f"Office '{office_name}' deleted!")
                    refresh_office_list()
                else:
                    messagebox.showerror("Error", "Failed to delete office!")
        
        def show_office_codes():
            """Show all office codes for reference"""
            offices = get_all_offices()
            if not offices:
                messagebox.showinfo("No Offices", "No offices found in the system.")
                return
            
            codes_text = "🏢 OFFICE SECURITY CODES:\n" + "="*40 + "\n"
            for office in offices:
                codes_text += f"• {office['office_name']}: {office['office_code']}\n"
            
            codes_text += "\n⚠️ These codes are used for secure guest timeout verification."
            
            # Create a window to display codes
            codes_window = tk.Toplevel(self.root)
            codes_window.title("Office Security Codes")
            codes_window.geometry("400x300")
            codes_window.configure(bg=self.colors['white'])
            
            # Center window
            codes_window.update_idletasks()
            x = (codes_window.winfo_screenwidth() // 2) - (200)
            y = (codes_window.winfo_screenheight() // 2) - (150)
            codes_window.geometry(f"400x300+{x}+{y}")
            
            # Text widget with scrollbar
            text_frame = tk.Frame(codes_window, bg=self.colors['white'])
            text_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            text_widget = tk.Text(text_frame, font=("Courier", 11), wrap="word")
            text_scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=text_scrollbar.set)
            
            text_widget.insert("1.0", codes_text)
            text_widget.config(state="disabled")  # Make read-only
            
            text_widget.pack(side="left", fill="both", expand=True)
            text_scrollbar.pack(side="right", fill="y")
            
            # Close button
            tk.Button(codes_window, text="Close", command=codes_window.destroy,
                     bg=self.colors['primary'], fg="white", font=("Arial", 10, "bold"),
                     cursor="hand2").pack(pady=10)
        
        # Buttons row 1
        btn_row1 = tk.Frame(btn_frame, bg=self.colors['white'])
        btn_row1.pack(fill="x", pady=(0, 5))
        
        tk.Button(btn_row1, text="➕ Add Office", command=add_new_office,
                 bg=self.colors['success'], fg="white", font=("Arial", 9, "bold"),
                 cursor="hand2", padx=15, pady=5).pack(side="left", padx=5)
        
        tk.Button(btn_row1, text="🔄 Update Code", command=update_office_code_gui,
                 bg=self.colors['warning'], fg="white", font=("Arial", 9, "bold"),
                 cursor="hand2", padx=15, pady=5).pack(side="left", padx=5)
        
        tk.Button(btn_row1, text="🗑️ Delete Office", command=delete_office_gui,
                 bg=self.colors['accent'], fg="white", font=("Arial", 9, "bold"),
                 cursor="hand2", padx=15, pady=5).pack(side="left", padx=5)
        
        # Buttons row 2
        btn_row2 = tk.Frame(btn_frame, bg=self.colors['white'])
        btn_row2.pack(fill="x")
        
        tk.Button(btn_row2, text="🔍 View All Codes", command=show_office_codes,
                 bg=self.colors['info'], fg="white", font=("Arial", 9, "bold"),
                 cursor="hand2", padx=15, pady=5).pack(side="left", padx=5)
        
        tk.Button(btn_row2, text="🔄 Refresh List", command=refresh_office_list,
                 bg=self.colors['secondary'], fg="white", font=("Arial", 9, "bold"),
                 cursor="hand2", padx=15, pady=5).pack(side="right", padx=5)
        
        # Load initial data
        refresh_office_list()
    
    # Helper functions
    def run_function(self, function_name):
        """Run admin function and show result"""
        try:
            result = self.admin_functions[function_name]()
            
            # Success messages with icons
            messages = {
                'enroll': ("✅ Success", "Enrollment completed successfully!\nCheck terminal for details."),
                'sync': ("🔄 Sync Complete", "Database synchronized successfully!\nCheck terminal for details."),
                'clear_records': ("🧹 Records Cleared", "All time records have been cleared successfully.")
            }
            
            if function_name in messages:
                title, msg = messages[function_name]
                self.root.after(0, lambda: messagebox.showinfo(title, msg, icon='info'))
                
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda: messagebox.showerror("❌ Error", f"Operation failed:\n\n{str(error_message)}"))
    
    def close(self):
        """Close the GUI"""
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
    
    def run(self):
        """Run the GUI"""
        try:
            # Bind escape key
            self.root.bind('<Escape>', lambda e: self.close())
            
            # Start main loop
            self.root.mainloop()
        except Exception as e:
            print(f"Error running GUI: {e}")
            self.close()
            
    def setup_window(self):
        """Setup the main window with enhanced styling"""
        self.root.title("MotorPass - Admin Control Center")
        self.root.configure(bg=self.colors['light'])
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size (90% of screen for better view)
        window_width = int(screen_width * 0.90)
        window_height = int(screen_height * 0.90)
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        self.root.minsize(1000, 700)
        
    def create_variables(self):
        """Create all tkinter variables"""
        self.time_string = tk.StringVar()
        self.date_string = tk.StringVar()
        self.status_text = tk.StringVar(value="🔐 Admin authentication required")
        self.update_time()
        
    def update_time(self):
        """Update time display"""
        try:
            if not hasattr(self, 'root') or not self.root.winfo_exists():
                return
                
            now = datetime.now()
            self.time_string.set(now.strftime("%I:%M:%S %p"))
            self.date_string.set(now.strftime("%A, %B %d, %Y"))
            
            if self.root.winfo_exists():
                self.root.after(1000, self.update_time)
        except:
            pass
    
    def create_authentication_screen(self):
        """Create the authentication screen"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container with gradient background
        main_container = tk.Frame(self.root, bg=self.colors['primary'])
        main_container.pack(fill="both", expand=True)
        
        # Create gradient effect
        gradient_frame = tk.Canvas(main_container, highlightthickness=0)
        gradient_frame.pack(fill="both", expand=True)
        
        # Authentication card
        auth_card = tk.Frame(gradient_frame, bg=self.colors['white'], relief='flat')
        auth_card.place(relx=0.5, rely=0.5, anchor='center', width=500, height=450)
        
        # Card shadow effect
        shadow = tk.Frame(gradient_frame, bg='#D0D0D0')
        shadow.place(relx=0.5, rely=0.5, anchor='center', width=510, height=460)
        auth_card.lift()
        
        # Logo section
        logo_frame = tk.Frame(auth_card, bg=self.colors['primary'], height=120)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        
        # Logo
        logo_container = tk.Frame(logo_frame, bg=self.colors['gold'], width=80, height=80)
        logo_container.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(logo_container, text="🛡️", font=("Arial", 36), 
                bg=self.colors['gold'], fg=self.colors['primary']).place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        tk.Label(auth_card, text="ADMIN ACCESS CONTROL", 
                font=("Arial", 24, "bold"), fg=self.colors['primary'], bg=self.colors['white']).pack(pady=(30, 10))
        
        # Subtitle
        tk.Label(auth_card, text="Fingerprint Authentication Required", 
                font=("Arial", 14), fg=self.colors['secondary'], bg=self.colors['white']).pack(pady=(0, 30))
        
        # Status with animated dots
        status_frame = tk.Frame(auth_card, bg=self.colors['white'])
        status_frame.pack(pady=20)
        
        self.status_label = tk.Label(status_frame, textvariable=self.status_text, 
                                    font=("Arial", 12), fg=self.colors['info'], bg=self.colors['white'])
        self.status_label.pack()
        
        # Authentication button with hover effect
        auth_btn_frame = tk.Frame(auth_card, bg=self.colors['white'])
        auth_btn_frame.pack(pady=30)
        
        self.auth_button = tk.Button(auth_btn_frame, text="🔓 START AUTHENTICATION", 
                                    font=("Arial", 14, "bold"), 
                                    bg=self.colors['success'], fg=self.colors['white'],
                                    activebackground=self.colors['info'],
                                    activeforeground=self.colors['white'],
                                    padx=30, pady=15, cursor="hand2",
                                    relief='flat', bd=0,
                                    command=self.start_authentication)
        self.auth_button.pack()
        
        # Add hover effects
        self.auth_button.bind("<Enter>", lambda e: self.auth_button.config(bg=self.colors['info']))
        self.auth_button.bind("<Leave>", lambda e: self.auth_button.config(bg=self.colors['success']))
        
        # Exit button
        exit_btn = tk.Button(auth_card, text="EXIT", 
                            font=("Arial", 11), bg=self.colors['secondary'], fg=self.colors['white'],
                            activebackground=self.colors['accent'],
                            padx=25, pady=8, cursor="hand2", relief='flat', bd=0,
                            command=self.close)
        exit_btn.pack(pady=(0, 20))
    
    def start_authentication(self):
        """Start fingerprint authentication"""
        self.status_text.set("🔄 Authenticating... Place finger on sensor")
        self.auth_button.config(state='disabled', text="⏳ AUTHENTICATING...")
        
        # Run authentication in thread
        thread = threading.Thread(target=self.run_authentication, daemon=True)
        thread.start()
    
    def run_authentication(self):
        """Run authentication process"""
        try:
            # Call the authentication function
            if self.admin_functions['authenticate']():
                self.authenticated = True
                self.root.after(0, self.show_admin_panel)
            else:
                self.root.after(0, lambda: self.status_text.set("❌ Authentication failed! Access denied."))
                self.root.after(0, lambda: self.auth_button.config(state='normal', text="🔓 START AUTHENTICATION"))
                self.root.after(2000, lambda: self.status_text.set("🔐 Admin authentication required"))
        except Exception as e:
            self.root.after(0, lambda: self.status_text.set(f"❌ Error: {str(e)}"))
            self.root.after(0, lambda: self.auth_button.config(state='normal', text="🔓 START AUTHENTICATION"))
    
    def show_admin_panel(self):
        """Show the enhanced main admin panel"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['light'])
        main_container.pack(fill="both", expand=True)
        
        # Enhanced header
        self.create_enhanced_header(main_container)
        
        # Content area with sidebar
        content_container = tk.Frame(main_container, bg=self.colors['light'])
        content_container.pack(fill="both", expand=True)
        
        # Stats sidebar
        self.create_stats_sidebar(content_container)
        
        # Main content area
        main_content = tk.Frame(content_container, bg=self.colors['white'])
        main_content.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)
        
        # Menu cards
        self.create_menu_cards(main_content)
        
        # Footer
        self.create_enhanced_footer(main_container)
    
    def create_enhanced_header(self, parent):
        """Create enhanced header with modern design"""
        header = tk.Frame(parent, bg=self.colors['primary'], height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Add subtle shadow
        shadow = tk.Frame(parent, bg='#E0E0E0', height=2)
        shadow.pack(fill="x")
        
        # Header content
        header_content = tk.Frame(header, bg=self.colors['primary'])
        header_content.pack(fill="both", expand=True, padx=30)
        
        # Logo and title section
        left_section = tk.Frame(header_content, bg=self.colors['primary'])
        left_section.pack(side="left", fill="y")
        
        # Modern logo
        logo_bg = tk.Frame(left_section, bg=self.colors['gold'], width=50, height=50)
        logo_bg.pack(side="left", pady=15)
        logo_bg.pack_propagate(False)
        tk.Label(logo_bg, text="⚡", font=("Arial", 24), 
                bg=self.colors['gold'], fg=self.colors['primary']).place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        title_section = tk.Frame(left_section, bg=self.colors['primary'])
        title_section.pack(side="left", padx=(20, 0), fill="y")
        
        tk.Label(title_section, text="ADMIN CONTROL CENTER", 
                font=("Arial", 24, "bold"), fg=self.colors['white'], bg=self.colors['primary']).pack(anchor="w", pady=(15, 0))
        tk.Label(title_section, text="MotorPass Management System",
                font=("Arial", 11), fg=self.colors['light'], bg=self.colors['primary']).pack(anchor="w")
        
        # Right section with clock
        right_section = tk.Frame(header_content, bg=self.colors['primary'])
        right_section.pack(side="right", fill="y")
        
        # Modern clock display
        clock_container = tk.Frame(right_section, bg=self.colors['secondary'], relief='flat')
        clock_container.pack(pady=15, padx=10)
        
        time_frame = tk.Frame(clock_container, bg=self.colors['secondary'])
        time_frame.pack(padx=20, pady=10)
        
        tk.Label(time_frame, textvariable=self.time_string, font=("Arial", 20, "bold"), 
                fg=self.colors['gold'], bg=self.colors['secondary']).pack()
        tk.Label(time_frame, textvariable=self.date_string, font=("Arial", 10), 
                fg=self.colors['light'], bg=self.colors['secondary']).pack()
    
    def create_stats_sidebar(self, parent):
        """Create statistics sidebar"""
        sidebar = tk.Frame(parent, bg=self.colors['secondary'], width=300)
        sidebar.pack(side="left", fill="y", padx=(20, 20), pady=20)
        sidebar.pack_propagate(False)
        
        # Title
        tk.Label(sidebar, text="📊 LIVE STATISTICS", 
                font=("Arial", 16, "bold"), fg=self.colors['white'], 
                bg=self.colors['secondary']).pack(pady=20)
        
        # Load stats
        try:
            stats = self.admin_functions['get_stats']()
        except:
            stats = {}
        
        # Stat cards
        self.create_stat_card(sidebar, "👥", "Total Users", 
                            stats.get('total_students', 0) + stats.get('total_staff', 0), 
                            self.colors['info'])
        
        self.create_stat_card(sidebar, "🎓", "Students", 
                            stats.get('total_students', 0), 
                            self.colors['success'])
        
        self.create_stat_card(sidebar, "👔", "Staff", 
                            stats.get('total_staff', 0), 
                            self.colors['warning'])
        
        self.create_stat_card(sidebar, "🚗", "Currently Inside", 
                            stats.get('users_currently_in', 0), 
                            self.colors['accent'])
        
        # Activity indicator
        activity_frame = tk.Frame(sidebar, bg=self.colors['primary'])
        activity_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(activity_frame, text="📈 Today's Activity", 
                font=("Arial", 12, "bold"), fg=self.colors['white'], 
                bg=self.colors['primary']).pack(pady=10)
        
        tk.Label(activity_frame, text=f"{stats.get('todays_activity', 0)} Actions", 
                font=("Arial", 18, "bold"), fg=self.colors['gold'], 
                bg=self.colors['primary']).pack(pady=(0, 10))
    
    def create_stat_card(self, parent, icon, label, value, color):
        """Create a statistics card"""
        card = tk.Frame(parent, bg=self.colors['dark'])
        card.pack(fill="x", padx=20, pady=10)
        
        # Content frame
        content = tk.Frame(card, bg=self.colors['dark'])
        content.pack(fill="x", padx=15, pady=15)
        
        # Icon and label
        top_row = tk.Frame(content, bg=self.colors['dark'])
        top_row.pack(fill="x")
        
        tk.Label(top_row, text=f"{icon} {label}", 
                font=("Arial", 12), fg=self.colors['light'], 
                bg=self.colors['dark']).pack(side="left")
        
        # Value
        tk.Label(content, text=str(value), 
                font=("Arial", 24, "bold"), fg=color, 
                bg=self.colors['dark']).pack(anchor="w", pady=(5, 0))
    
    def create_menu_cards(self, parent):
        """Create enhanced menu cards - FIXED with proper row3 definition"""
        # Title
        tk.Label(parent, text="SYSTEM FUNCTIONS", 
                font=("Arial", 20, "bold"), fg=self.colors['primary'], 
                bg=self.colors['white']).pack(pady=(20, 30))
        
        # Cards container
        cards_container = tk.Frame(parent, bg=self.colors['white'])
        cards_container.pack(fill="both", expand=True, padx=40)
        
        # Create three rows of cards - FIXED
        row1 = tk.Frame(cards_container, bg=self.colors['white'])
        row1.pack(fill="x", pady=(0, 20))
        
        row2 = tk.Frame(cards_container, bg=self.colors['white'])
        row2.pack(fill="x", pady=(0, 20))
        
        row3 = tk.Frame(cards_container, bg=self.colors['white'])  # FIXED: Now properly defined
        row3.pack(fill="x")
        
        # Row 1 cards
        self.create_function_card(row1, "👤", "Enroll New User", 
                                 "Register student/staff with fingerprint",
                                 self.enroll_user, self.colors['success'])
        
        self.create_function_card(row1, "👥", "View Users", 
                                 "Display all registered users",
                                 self.view_users, self.colors['info'])
        
        self.create_function_card(row1, "🗑️", "Delete User", 
                                 "Remove user fingerprint",
                                 self.delete_user, self.colors['accent'])
        
        # Row 2 cards
        self.create_function_card(row2, "🔄", "Sync Database", 
                                 "Import from Google Sheets",
                                 self.sync_database, self.colors['warning'])
        
        self.create_function_card(row2, "🕒", "Time Records", 
                                 "View attendance history",
                                 self.view_time_records, self.colors['secondary'])
        
        self.create_function_card(row2, "🧹", "Clear Records", 
                                 "Delete time records",
                                 self.clear_time_records, self.colors['dark'])
        
        # Row 3 - NEW: System Maintenance (Office Management)
        self.create_function_card(row3, "🏢", "System Maintenance", 
                                 "Manage visitor offices & security codes",
                                 self.show_office_management, self.colors['gold'])
    
    def create_function_card(self, parent, icon, title, description, command, color):
        """Create an enhanced function card"""
        # Card frame with shadow
        card_container = tk.Frame(parent, bg=self.colors['white'])
        card_container.pack(side="left", fill="both", expand=True, padx=10)
        
        # Shadow effect
        shadow = tk.Frame(card_container, bg='#D5D5D5')
        shadow.place(x=2, y=2, relwidth=1, relheight=1)
        
        # Main card
        card = tk.Frame(card_container, bg=self.colors['light'], relief='flat', bd=0)
        card.pack(fill="both", expand=True)
        
        # Content
        content = tk.Frame(card, bg=self.colors['light'])
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Icon circle
        icon_frame = tk.Frame(content, bg=self.colors['white'], width=60, height=60)
        icon_frame.pack(pady=(0, 15))
        icon_frame.pack_propagate(False)
        
        icon_label = tk.Label(icon_frame, text=icon, font=("Arial", 24), 
                             bg=self.colors['white'], fg=color)
        icon_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        tk.Label(content, text=title, font=("Arial", 14, "bold"), 
                fg=self.colors['dark'], bg=self.colors['light']).pack(pady=(0, 5))
        
        # Description
        tk.Label(content, text=description, font=("Arial", 10), 
                fg=self.colors['secondary'], bg=self.colors['light'],
                wraplength=150).pack()
        
        # Make entire card clickable
        for widget in [card, content, icon_frame, icon_label]:
            widget.bind("<Button-1>", lambda e: command())
            widget.config(cursor="hand2")
    
    def create_enhanced_footer(self, parent):
        """Create enhanced footer"""
        footer = tk.Frame(parent, bg=self.colors['dark'], height=70)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        
        footer_content = tk.Frame(footer, bg=self.colors['dark'])
        footer_content.pack(expand=True)
        
        # Buttons with modern style
        buttons_frame = tk.Frame(footer_content, bg=self.colors['dark'])
        buttons_frame.pack(pady=15)
        
        # Dashboard button
        dash_btn = tk.Button(buttons_frame, text="📊 WEB DASHBOARD", 
                            font=("Arial", 12, "bold"), 
                            bg=self.colors['gold'], fg=self.colors['dark'],
                            activebackground=self.colors['warning'],
                            padx=25, pady=10, cursor="hand2", relief='flat', bd=0,
                            command=self.open_dashboard)
        dash_btn.pack(side="left", padx=10)
        
        # Exit button
        exit_btn = tk.Button(buttons_frame, text="🚪 EXIT ADMIN PANEL", 
                            font=("Arial", 12, "bold"), 
                            bg=self.colors['accent'], fg=self.colors['white'],
                            activebackground='#C0392B',
                            padx=25, pady=10, cursor="hand2", relief='flat', bd=0,
                            command=self.exit_system)
        exit_btn.pack(side="left", padx=10)
        
        # Add hover effects
        dash_btn.bind("<Enter>", lambda e: dash_btn.config(bg=self.colors['warning']))
        dash_btn.bind("<Leave>", lambda e: dash_btn.config(bg=self.colors['gold']))
        
        exit_btn.bind("<Enter>", lambda e: exit_btn.config(bg='#C0392B'))
        exit_btn.bind("<Leave>", lambda e: exit_btn.config(bg=self.colors['accent']))


# Test function
if __name__ == "__main__":
    # Mock functions for testing
    mock_functions = {
        'authenticate': lambda: True,
        'enroll': lambda: print("Enrolling..."),
        'view_users': lambda: print("Viewing users..."),
        'delete_fingerprint': lambda slot: print(f"Deleting slot {slot}..."),
        'sync': lambda: print("Syncing..."),
        'get_time_records': lambda: [
            {'date': '2024-01-01', 'time': '08:00', 'student_id': '2021-001', 
             'student_name': 'John Doe', 'user_type': 'STUDENT', 'status': 'IN'},
            {'date': '2024-01-01', 'time': '17:00', 'student_id': '2021-001', 
             'student_name': 'John Doe', 'user_type': 'STUDENT', 'status': 'OUT'}
        ],
        'clear_records': lambda: print("Clearing records..."),
        'get_stats': lambda: {
            'total_students': 150,
            'total_staff': 25,
            'total_guests': 50,
            'students_currently_in': 45,
            'staff_currently_in': 10,
            'guests_currently_in': 5,
            'users_currently_in': 60,
            'todays_activity': 120
        }
    }
    
    app = AdminPanelGUI(mock_functions, skip_auth=True)
    app.run()
