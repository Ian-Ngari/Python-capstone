import tkinter as tk
from tkinter import ttk, messagebox
import csv
import json
from datetime import datetime, timedelta
import hashlib
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DATA_DIR = "data"
USERS_FILE = "users.json"

EXCHANGE_RATES = {
    "KES": 1.0,
    "USD": 0.0078,
    "EUR": 0.0072,
    "GBP": 0.0062
}

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1000x700")
        self.current_user = None
        
        self.configure_theme()
        
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        self.setup_ui()

    def configure_theme(self):
        self.root.configure(bg='white')
        
        style = ttk.Style()
        style.theme_use('clam')  
        
        style.configure('.', background='white', foreground='black')
        style.configure('TFrame', background='white')
        style.configure('TLabel', background='white', foreground='black')
        style.configure('TButton', background='white', foreground='black', 
                       bordercolor='black', borderwidth=1)
        style.configure('TEntry', fieldbackground='white', foreground='black')
        style.configure('TCombobox', fieldbackground='white', foreground='black')
        style.configure('Treeview', background='white', foreground='black',
                       fieldbackground='white')
        style.configure('Treeview.Heading', background='white', foreground='black')
        style.configure('TLabelframe', background='white', foreground='black')
        style.configure('TLabelframe.Label', background='white', foreground='black')
        
        style.map('Treeview', background=[('selected', 'black')], 
                  foreground=[('selected', 'white')])
        style.map('TButton', background=[('active', 'black'), ('pressed', 'black')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        
        plt.style.use('grayscale')

    def setup_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        if not self.current_user:
            self.show_login_screen()
        else:
            self.show_main_app()

    def show_login_screen(self):
        self.clear_window()
        
        login_frame = ttk.LabelFrame(self.root, text="Login / Register", padding=20)
        login_frame.pack(pady=50, padx=50, fill=tk.BOTH, expand=True)
        
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(login_frame, text="Login", command=self.login).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(login_frame, text="Register", command=self.register).grid(row=2, column=1, padx=5, pady=10)

    def show_main_app(self):
        self.clear_window()
        
        menubar = tk.Menu(self.root, bg='white', fg='black', activebackground='black', activeforeground='white')
       
        file_menu = tk.Menu(menubar, tearoff=0, bg='white', fg='black', activebackground='black', activeforeground='white')
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        trans_menu = tk.Menu(menubar, tearoff=0, bg='white', fg='black', activebackground='black', activeforeground='white')
        trans_menu.add_command(label="Add Expense", command=self.add_expense)
        trans_menu.add_command(label="Add Income", command=self.add_income)
        trans_menu.add_command(label="View Expenses", command=lambda: self.view_transactions("expense"))
        trans_menu.add_command(label="View Income", command=lambda: self.view_transactions("income"))
        menubar.add_cascade(label="Transactions", menu=trans_menu)
        
        budget_menu = tk.Menu(menubar, tearoff=0, bg='white', fg='black', activebackground='black', activeforeground='white')
        budget_menu.add_command(label="Set Budget", command=self.set_budget)
        budget_menu.add_command(label="View Budgets", command=self.view_budgets)
        budget_menu.add_command(label="Check Budgets", command=self.check_budgets)
        menubar.add_cascade(label="Budgets", menu=budget_menu)
        
        report_menu = tk.Menu(menubar, tearoff=0, bg='white', fg='black', activebackground='black', activeforeground='white')
        report_menu.add_command(label="Generate Report", command=self.generate_report)
        report_menu.add_command(label="Check Bill Reminders", command=self.check_bill_reminders)
        menubar.add_cascade(label="Reports", menu=report_menu)
        
        self.root.config(menu=menubar)
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        welcome_label = ttk.Label(
            self.main_frame, 
            text=f"Welcome, {self.current_user}!",
            font=('Helvetica', 16, 'bold')
        )
        welcome_label.pack(pady=20)
        
        self.show_quick_summary()

    def show_quick_summary(self):
        summary_frame = ttk.LabelFrame(self.main_frame, text="Quick Summary", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        expenses = self.load_user_data("expense")
        income = self.load_user_data("income")
        budgets = self.load_user_data("budgets")
        
        total_expenses = sum(float(e["Amount"]) for e in expenses) if expenses else 0
        total_income = sum(float(i["Amount"]) for i in income) if income else 0
        net_balance = total_income - total_expenses
        
        ttk.Label(summary_frame, text=f"Total Expenses: KES {total_expenses:.2f}").pack(anchor=tk.W)
        ttk.Label(summary_frame, text=f"Total Income: KES {total_income:.2f}").pack(anchor=tk.W)
        ttk.Label(summary_frame, text=f"Net Balance: KES {net_balance:.2f}").pack(anchor=tk.W)
        
        # Check if expenses exceed income
        if total_expenses > total_income:
            messagebox.showwarning("Warning", "Your expenses exceed your income! Please review your spending.")

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def load_users(self):
        try:
            with open(os.path.join(DATA_DIR, USERS_FILE), "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_users(self, users):
        try:
            with open(os.path.join(DATA_DIR, USERS_FILE), "w") as file:
                json.dump(users, file, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save users: {str(e)}")
            return False

    def load_user_data(self, data_type):
        users = self.load_users()
        if self.current_user not in users:
            return []
        
        if data_type not in users[self.current_user]["data_files"]:
            self.initialize_user_data(self.current_user)
            
        filename = users[self.current_user]["data_files"].get(data_type)
        if not filename:
            return []
        
        filepath = os.path.join(DATA_DIR, filename)
        
        try:
            if data_type == "budgets":
                if os.path.exists(filepath):
                    with open(filepath, "r") as file:
                        return json.load(file)
                return {}
            else:
                data = []
                if os.path.exists(filepath):
                    with open(filepath, "r") as file:
                        reader = csv.DictReader(file)
                        data = list(reader)
                return data
        except Exception as e:
            messagebox.showerror("Error", f"Error loading {data_type}: {str(e)}")
            return [] if data_type != "budgets" else {}

    def save_user_data(self, data, data_type, fieldnames=None):
        users = self.load_users()
        if self.current_user not in users:
            messagebox.showerror("Error", "User not found!")
            return False
        
        if data_type not in users[self.current_user]["data_files"]:
            self.initialize_user_data(self.current_user)
            
        filename = users[self.current_user]["data_files"].get(data_type)
        if not filename:
            messagebox.showerror("Error", f"Filename not configured for {data_type}!")
            return False
        
        filepath = os.path.join(DATA_DIR, filename)
        
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            
            if data_type == "budgets":
                with open(filepath, "w") as file:
                    json.dump(data, file, indent=4)
            else:
                cleaned_data = []
                for row in data:
                    cleaned_row = {field: row.get(field, "") for field in fieldnames}
                    cleaned_data.append(cleaned_row)
                
                with open(filepath, "w", newline="", encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(cleaned_data)
            
            return True
        except PermissionError:
            messagebox.showerror("Error", f"Permission denied when saving to {filepath}")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save {data_type}: {str(e)}")
            return False

    def initialize_user_data(self, username):
        users = self.load_users()
        if username not in users:
            return
        
        if "data_files" not in users[username]:
            users[username]["data_files"] = {
                "expense": f"{username}_expenses.csv",
                "income": f"{username}_income.csv",
                "budgets": f"{username}_budgets.json"
            }
            self.save_users(users)
        
        user_data = users[username]["data_files"]
        
        expense_file = os.path.join(DATA_DIR, user_data["expense"])
        if not os.path.exists(expense_file):
            with open(expense_file, "w", newline="", encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["Date", "Category", "Amount", "Original_Amount", "Notes"])
                writer.writeheader()
        
        income_file = os.path.join(DATA_DIR, user_data["income"])
        if not os.path.exists(income_file):
            with open(income_file, "w", newline="", encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["Date", "Source", "Amount", "Original_Amount", "Notes"])
                writer.writeheader()
        
        budgets_file = os.path.join(DATA_DIR, user_data["budgets"])
        if not os.path.exists(budgets_file):
            with open(budgets_file, "w", encoding='utf-8') as file:
                json.dump({}, file)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        users = self.load_users()
        
        if username in users and users[username]["password"] == self.hash_password(password):
            self.current_user = username
            
            self.initialize_user_data(username)
            self.setup_ui()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        users = self.load_users()
        
        if username in users:
            messagebox.showerror("Error", "Username already exists!")
            return
        
        users[username] = {
            "password": self.hash_password(password),
            "data_files": {
                "expense": f"{username}_expenses.csv",
                "income": f"{username}_income.csv",
                "budgets": f"{username}_budgets.json"
            }
        }
        
        if self.save_users(users):
            self.initialize_user_data(username)
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)

    def logout(self):
        self.current_user = None
        self.setup_ui()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def add_expense(self):
        self.add_transaction("expense")

    def add_income(self):
        self.add_transaction("income")

    def add_transaction(self, transaction_type):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add {transaction_type.capitalize()}")
        dialog.geometry("400x400")
        dialog.grab_set()  
        
        ttk.Label(dialog, text="Date (YYYY-MM-DD):").pack(pady=(10,0))
        date_entry = ttk.Entry(dialog)
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        date_entry.pack()
        
        ttk.Label(dialog, text="Currency:").pack(pady=(10,0))
        currency_var = tk.StringVar(value="KES")
        currency_menu = ttk.OptionMenu(dialog, currency_var, "KES", *EXCHANGE_RATES.keys())
        currency_menu.pack()
        
        ttk.Label(dialog, text="Amount:").pack(pady=(10,0))
        amount_entry = ttk.Entry(dialog)
        amount_entry.pack()
        
        if transaction_type == "expense":
            ttk.Label(dialog, text="Category:").pack(pady=(10,0))
            category_source_entry = ttk.Entry(dialog)
            category_source_entry.pack()
        else:
            ttk.Label(dialog, text="Source:").pack(pady=(10,0))
            category_source_entry = ttk.Entry(dialog)
            category_source_entry.pack()
        
        ttk.Label(dialog, text="Notes:").pack(pady=(10,0))
        notes_entry = ttk.Entry(dialog)
        notes_entry.pack()
        
        def save_transaction():
            try:
                date = date_entry.get()
                datetime.strptime(date, '%Y-%m-%d')  
                
                currency = currency_var.get()
                amount = float(amount_entry.get())
                notes = notes_entry.get()
                
                if transaction_type == "expense":
                    category = category_source_entry.get().strip()
                    if not category:
                        messagebox.showerror("Error", "Please enter a category")
                        return
                else:
                    source = category_source_entry.get().strip()
                    if not source:
                        messagebox.showerror("Error", "Please enter a source")
                        return
                
                amount_kes = round(amount * EXCHANGE_RATES[currency] / EXCHANGE_RATES["KES"], 2)
                
                # Check for negative balance when adding expense
                if transaction_type == "expense":
                    expenses = self.load_user_data("expense")
                    income = self.load_user_data("income")
                    total_expenses = sum(float(e["Amount"]) for e in expenses) if expenses else 0
                    total_income = sum(float(i["Amount"]) for i in income) if income else 0
                    
                    if (total_expenses + amount_kes) > total_income:
                        if not messagebox.askyesno("Warning", 
                                                  "This expense will make your total expenses exceed your income. Continue?"):
                            return
                
                transaction = {
                    "Date": date,
                    "Amount": str(amount_kes),
                    "Original_Amount": f"{amount:.2f} {currency}",
                    "Notes": notes
                }
                
                if transaction_type == "expense":
                    transaction["Category"] = category
                    fieldnames = ["Date", "Category", "Amount", "Original_Amount", "Notes"]
                else:
                    transaction["Source"] = source
                    fieldnames = ["Date", "Source", "Amount", "Original_Amount", "Notes"]
                
                existing_data = self.load_user_data(transaction_type)
                if not isinstance(existing_data, list):
                    existing_data = []
                
                updated_data = existing_data + [transaction]
                
                if not self.save_user_data(updated_data, transaction_type, fieldnames):
                    messagebox.showerror("Error", "Failed to save transaction")
                    return
                
                messagebox.showinfo("Success", f"{transaction_type.capitalize()} saved successfully!")
                dialog.destroy()
                self.show_quick_summary()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")

        ttk.Button(dialog, text="Save", command=save_transaction).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def view_transactions(self, transaction_type):
        data = self.load_user_data(transaction_type)
        
        if not data:
            messagebox.showinfo("Info", f"No {transaction_type} records found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"View {transaction_type.capitalize()}")
        dialog.geometry("900x600")
        
        # Create main container frame
        container = ttk.Frame(dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a canvas and scrollbar
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Pack the scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Make mouse wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        columns = ["ID", "Date", "Category/Source", "Amount (KES)", "Original Amount", "Notes"]
        tree = ttk.Treeview(scrollable_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.W)
        
        tree.column("ID", width=50)
        tree.column("Notes", width=200)
        
        for idx, trans in enumerate(data, 1):
            if transaction_type == "expense":
                tree.insert("", tk.END, values=(
                    idx,
                    trans["Date"],
                    trans["Category"],
                    f"{float(trans['Amount']):.2f}",
                    trans["Original_Amount"],
                    trans["Notes"]
                ))
            else:
                tree.insert("", tk.END, values=(
                    idx,
                    trans["Date"],
                    trans["Source"],
                    f"{float(trans['Amount']):.2f}",
                    trans["Original_Amount"],
                    trans["Notes"]
                ))
        
        tree.pack(fill=tk.BOTH, expand=True)

    def set_budget(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Set Budget")
        dialog.geometry("300x200")
        dialog.grab_set()
        
        ttk.Label(dialog, text="Category:").pack(pady=(10,0))
        category_entry = ttk.Entry(dialog)
        category_entry.pack()
        
        ttk.Label(dialog, text="Amount (KES):").pack(pady=(10,0))
        amount_entry = ttk.Entry(dialog)
        amount_entry.pack()
        
        def save_budget():
            category = category_entry.get().strip()
            try:
                amount = float(amount_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")
                return
            
            if not category:
                messagebox.showerror("Error", "Please enter a category")
                return
            
            budgets = self.load_user_data("budgets")
            budgets[category] = amount
            if self.save_user_data(budgets, "budgets"):
                messagebox.showinfo("Success", "Budget set successfully!")
                dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_budget).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def view_budgets(self):
        budgets = self.load_user_data("budgets")
        
        if not budgets:
            messagebox.showinfo("Info", "No budgets set yet")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("View Budgets")
        dialog.geometry("400x300")
        
        container = ttk.Frame(dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        columns = ["Category", "Amount (KES)"]
        tree = ttk.Treeview(scrollable_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor=tk.W)
        
        for category, amount in budgets.items():
            tree.insert("", tk.END, values=(category, f"{float(amount):.2f}"))
        
        tree.pack(fill=tk.BOTH, expand=True)

    def check_budgets(self):
        expenses = self.load_user_data("expense")
        budgets = self.load_user_data("budgets")
        
        if not budgets:
            messagebox.showinfo("Info", "No budgets set yet")
            return
        
        result = ""
        for category, limit in budgets.items():
            spent = sum(float(e["Amount"]) for e in expenses if e.get("Category") == category)
            remaining = float(limit) - spent
            result += f"{category}: KES {spent:.2f} / KES {limit:.2f} (KES {remaining:.2f} remaining)\n"
        
        messagebox.showinfo("Budget Status", result)

    def generate_report(self):
        expenses = self.load_user_data("expense")
        
        if not expenses:
            messagebox.showinfo("Info", "No expenses to generate report")
            return
        
        categories = {}
        for expense in expenses:
            category = expense["Category"]
            amount = float(expense["Amount"])
            categories[category] = categories.get(category, 0) + amount
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Monthly Spending Report")
        dialog.geometry("600x500")
        
        container = ttk.Frame(dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        report_text = tk.Text(scrollable_frame, height=10)
        report_text.pack(fill=tk.X, pady=10)
        
        report_text.insert(tk.END, "Monthly Spending Report (KES)\n\n")
        for category, total in categories.items():
            report_text.insert(tk.END, f"{category}: KES {total:.2f}\n")
        
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(categories.keys(), categories.values())
        ax.set_title("Monthly Spending by Category (KES)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        canvas_fig = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def check_bill_reminders(self):
        expenses = self.load_user_data("expense")
        today = datetime.now()
        upcoming_bills = []
        
        for e in expenses:
            if "Bill" in e.get("Category", ""):
                try:
                    bill_date = datetime.strptime(e["Date"], '%Y-%m-%d')
                    if today <= bill_date <= today + timedelta(days=7):
                        upcoming_bills.append(e)
                except ValueError:
                    continue
        
        if not upcoming_bills:
            messagebox.showinfo("Info", "No upcoming bills in the next 7 days")
            return
        
        result = "Upcoming Bills (Next 7 Days):\n\n"
        for bill in upcoming_bills:
            result += f"{bill['Date']} - {bill['Category']}: KES {float(bill['Amount']):.2f} ({bill['Original_Amount']})\n"
        
        messagebox.showinfo("Bill Reminders", result)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()