import csv
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import getpass
import hashlib
import os


DATA_DIR = "data"
EXPENSES_FILE = "expenses.csv"
INCOME_FILE = "income.csv"
BUDGETS_FILE = "budgets.json"
USERS_FILE = "users.json"


EXCHANGE_RATES = {
    "KES": 1.0,    
    "USD": 0.0078,   
    "EUR": 0.0072,   
    "GBP": 0.0062    
}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    try:
        with open(os.path.join(DATA_DIR, USERS_FILE), "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_users(users):
    with open(os.path.join(DATA_DIR, USERS_FILE), "w") as file:
        json.dump(users, file)


def register_user():
    users = load_users()
    username = input("Enter username: ")
    if username in users:
        print("Username already exists!")
        return False
    
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        print("Passwords don't match!")
        return False
    
    users[username] = {
        "password": hash_password(password),
        "data_files": {
            "expenses": f"{username}_expenses.csv",
            "income": f"{username}_income.csv",
            "budgets": f"{username}_budgets.json"
        }
    }
    save_users(users)
    
    
    initialize_user_data(username)
    print("Registration successful!")
    return True


def initialize_user_data(username):
    users = load_users()
    user_data = users[username]["data_files"]
    
    
    if not os.path.exists(os.path.join(DATA_DIR, user_data["expenses"])):
        with open(os.path.join(DATA_DIR, user_data["expenses"]), "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["Date", "Category", "Amount", "Original_Amount", "Notes"])
            writer.writeheader()
    
    
    if not os.path.exists(os.path.join(DATA_DIR, user_data["income"])):
        with open(os.path.join(DATA_DIR, user_data["income"]), "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["Date", "Source", "Amount", "Original_Amount", "Notes"])
            writer.writeheader()
    
    
    if not os.path.exists(os.path.join(DATA_DIR, user_data["budgets"])):
        with open(os.path.join(DATA_DIR, user_data["budgets"]), "w") as file:
            json.dump({}, file)


def login():
    users = load_users()
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    if username in users and users[username]["password"] == hash_password(password):
        print("Login successful!")
        return username
    else:
        print("Invalid username or password!")
        return None


def load_user_data(username, data_type):
    users = load_users()
    if username not in users:
        return []
    
    filename = users[username]["data_files"].get(data_type)
    if not filename:
        return []
    
    try:
        if data_type == "budgets":
            with open(os.path.join(DATA_DIR, filename), "r") as file:
                return json.load(file)
        else:
            with open(os.path.join(DATA_DIR, filename), "r") as file:
                reader = csv.DictReader(file)
                return list(reader)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_user_data(username, data, data_type, fieldnames=None):
    users = load_users()
    if username not in users:
        return False
    
    filename = users[username]["data_files"].get(data_type)
    if not filename:
        return False
    
    try:
        if data_type == "budgets":
            with open(os.path.join(DATA_DIR, filename), "w") as file:
                json.dump(data, file)
        else:
            with open(os.path.join(DATA_DIR, filename), "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def convert_currency(amount, from_currency, to_currency="KES"):
    return amount * EXCHANGE_RATES[to_currency] / EXCHANGE_RATES[from_currency]


def add_transaction(transaction_type):
    date = input(f"Date (YYYY-MM-DD) [Today: {datetime.now().strftime('%Y-%m-%d')}]: ") or datetime.now().strftime('%Y-%m-%d')
    
    print("\nSelect Currency:")
    for i, currency in enumerate(EXCHANGE_RATES.keys(), 1):
        print(f"{i}. {currency}")
    currency_choice = int(input("Enter currency number (1-4): ")) - 1
    currency = list(EXCHANGE_RATES.keys())[currency_choice]
    
    amount = float(input(f"Amount in {currency}: "))
    amount_kes = convert_currency(amount, currency, "KES")
    notes = input("Notes: ")

    if transaction_type == "expense":
        category = input("Category (Food, Bills, etc.): ")
        return {
            "Date": date, 
            "Category": category, 
            "Amount": amount_kes, 
            "Original_Amount": f"{amount:.2f} {currency}",
            "Notes": notes
        }
    else:
        source = input("Source (Salary, Freelance, etc.): ")
        return {
            "Date": date, 
            "Source": source, 
            "Amount": amount_kes, 
            "Original_Amount": f"{amount:.2f} {currency}",
            "Notes": notes
        }


def display_transactions(transactions, transaction_type):
    if not transactions:
        print(f"No {transaction_type} records found!")
        return
    
    print(f"\n{'ID':<5} {'Date':<12} {'Category/Source':<20} {'Amount (KES)':<15} {'Original Amount':<20} {'Notes':<20}")
    print("-" * 90)
    for idx, trans in enumerate(transactions, 1):
        if transaction_type == "expense":
            print(f"{idx:<5} {trans['Date']:<12} {trans['Category']:<20} {float(trans['Amount']):<15.2f} {trans['Original_Amount']:<20} {trans['Notes']:<20}")
        else:
            print(f"{idx:<5} {trans['Date']:<12} {trans['Source']:<20} {float(trans['Amount']):<15.2f} {trans['Original_Amount']:<20} {trans['Notes']:<20}")


def update_transaction(transactions, transaction_type):
    display_transactions(transactions, transaction_type)
    if not transactions:
        return False
    
    try:
        trans_id = int(input(f"\nEnter ID of {transaction_type} to update (1-{len(transactions)}): ")) - 1
        if 0 <= trans_id < len(transactions):
            print(f"\nUpdating {transaction_type}:")
            print("Leave field blank to keep current value")
            
            transaction = transactions[trans_id]
            
            
            new_date = input(f"Date [{transaction['Date']}]: ") or transaction['Date']
            
            print("\nCurrent Currency:", transaction['Original_Amount'].split()[1])
            print("Select New Currency:")
            for i, currency in enumerate(EXCHANGE_RATES.keys(), 1):
                print(f"{i}. {currency}")
            currency_choice = input("Enter currency number (1-4) [Keep current]: ")
            if currency_choice:
                currency_choice = int(currency_choice) - 1
                currency = list(EXCHANGE_RATES.keys())[currency_choice]
            else:
                currency = transaction['Original_Amount'].split()[1]
            
            current_amount = float(transaction['Original_Amount'].split()[0])
            new_amount = input(f"Amount [{current_amount:.2f}]: ")
            new_amount = float(new_amount) if new_amount else current_amount
            new_amount_kes = convert_currency(new_amount, currency, "KES")
            
            if transaction_type == "expense":
                new_category = input(f"Category [{transaction['Category']}]: ") or transaction['Category']
            else:
                new_source = input(f"Source [{transaction['Source']}]: ") or transaction['Source']
            
            new_notes = input(f"Notes [{transaction['Notes']}]: ") or transaction['Notes']
            
            
            transaction['Date'] = new_date
            transaction['Amount'] = new_amount_kes
            transaction['Original_Amount'] = f"{new_amount:.2f} {currency}"
            transaction['Notes'] = new_notes
            
            if transaction_type == "expense":
                transaction['Category'] = new_category
            else:
                transaction['Source'] = new_source
            
            print(f"{transaction_type} updated successfully!")
            return True
        else:
            print("Invalid ID!")
    except ValueError:
        print("Please enter a valid number!")
    
    return False


def delete_transaction(transactions, transaction_type):
    display_transactions(transactions, transaction_type)
    if not transactions:
        return False
    
    try:
        trans_id = int(input(f"\nEnter ID of {transaction_type} to delete (1-{len(transactions)}): ")) - 1
        if 0 <= trans_id < len(transactions):
            confirm = input(f"Are you sure you want to delete this {transaction_type}? (y/n): ").lower()
            if confirm == 'y':
                deleted = transactions.pop(trans_id)
                print(f"{transaction_type} deleted successfully!")
                return True
        else:
            print("Invalid ID!")
    except ValueError:
        print("Please enter a valid number!")
    
    return False


def display_budgets(budgets):
    if not budgets:
        print("No budgets set yet!")
        return
    
    print("\nCurrent Budgets:")
    print(f"{'ID':<5} {'Category':<20} {'Amount (KES)':<15}")
    print("-" * 40)
    for idx, (category, amount) in enumerate(budgets.items(), 1):
        print(f"{idx:<5} {category:<20} {float(amount):<15.2f}")


def update_budget(budgets):
    display_budgets(budgets)
    if not budgets:
        return False
    
    try:
        budget_id = int(input("\nEnter ID of budget to update (1-{}): ".format(len(budgets)))) - 1
        if 0 <= budget_id < len(budgets):
            category = list(budgets.keys())[budget_id]
            new_amount = input(f"New amount for {category} (KES) [Current: {budgets[category]}]: ")
            if new_amount:
                budgets[category] = float(new_amount)
                print("Budget updated successfully!")
                return True
            else:
                print("No changes made.")
        else:
            print("Invalid ID!")
    except ValueError:
        print("Please enter a valid number!")
    
    return False


def delete_budget(budgets):
    display_budgets(budgets)
    if not budgets:
        return False
    
    try:
        budget_id = int(input("\nEnter ID of budget to delete (1-{}): ".format(len(budgets)))) - 1
        if 0 <= budget_id < len(budgets):
            category = list(budgets.keys())[budget_id]
            confirm = input(f"Are you sure you want to delete the budget for {category}? (y/n): ").lower()
            if confirm == 'y':
                del budgets[category]
                print("Budget deleted successfully!")
                return True
        else:
            print("Invalid ID!")
    except ValueError:
        print("Please enter a valid number!")
    
    return False


def check_budget(expenses, budgets):
    if not budgets:
        print("No budgets set yet!")
        return

    for category, limit in budgets.items():
        spent = sum(float(e["Amount"]) for e in expenses if e["Category"] == category)
        print(f"{category}: KES {spent:.2f} / KES {limit:.2f} (KES {limit - spent:.2f} remaining)")


def generate_report(expenses):
    categories = {}
    for expense in expenses:
        category = expense["Category"]
        amount = float(expense["Amount"])
        categories[category] = categories.get(category, 0) + amount

    print("\n📊 Monthly Spending Report (KES)")
    for category, total in categories.items():
        print(f"{category}: KES {total:.2f}")

    if input("\nShow chart? (y/n): ").lower() == "y":
        plt.bar(categories.keys(), categories.values())
        plt.title("Monthly Spending by Category (KES)")
        plt.show()


def check_bill_reminders(expenses):
    today = datetime.now()
    upcoming_bills = [
        e for e in expenses
        if "Bill" in e["Category"] and 
        datetime.strptime(e["Date"], "%Y-%m-%d") <= today + timedelta(days=7)
    ]

    if upcoming_bills:
        print("\n⚠️ Upcoming Bills (Next 7 Days)")
        for bill in upcoming_bills:
            print(f"{bill['Date']} - {bill['Category']}: KES {bill['Amount']:.2f} ({bill['Original_Amount']})")


def main_menu(username):
    while True:
        expenses = load_user_data(username, "expenses")
        income = load_user_data(username, "income")
        budgets = load_user_data(username, "budgets")

        print("\n💵 Expense Tracker (KES) - User:", username)
        print("1. Add Expense")
        print("2. Add Income")
        print("3. View Expenses")
        print("4. View Income")
        print("5. Update Expense")
        print("6. Update Income")
        print("7. Delete Expense")
        print("8. Delete Income")
        print("9. Set Budget")
        print("10. View Budgets")
        print("11. Update Budget")
        print("12. Delete Budget")
        print("13. Check Budgets")
        print("14. Generate Report")
        print("15. Check Bill Reminders")
        print("16. Logout")

        choice = input("Choose an option (1-16): ")

        if choice == "1":
            expenses.append(add_transaction("expense"))
            save_user_data(username, expenses, "expenses", ["Date", "Category", "Amount", "Original_Amount", "Notes"])
        elif choice == "2":
            income.append(add_transaction("income"))
            save_user_data(username, income, "income", ["Date", "Source", "Amount", "Original_Amount", "Notes"])
        elif choice == "3":
            display_transactions(expenses, "expense")
        elif choice == "4":
            display_transactions(income, "income")
        elif choice == "5":
            if update_transaction(expenses, "expense"):
                save_user_data(username, expenses, "expenses", ["Date", "Category", "Amount", "Original_Amount", "Notes"])
        elif choice == "6":
            if update_transaction(income, "income"):
                save_user_data(username, income, "income", ["Date", "Source", "Amount", "Original_Amount", "Notes"])
        elif choice == "7":
            if delete_transaction(expenses, "expense"):
                save_user_data(username, expenses, "expenses", ["Date", "Category", "Amount", "Original_Amount", "Notes"])
        elif choice == "8":
            if delete_transaction(income, "income"):
                save_user_data(username, income, "income", ["Date", "Source", "Amount", "Original_Amount", "Notes"])
        elif choice == "9":
            category = input("Category to budget (e.g., Food): ")
            limit = float(input("Budget limit (KES): "))
            budgets[category] = limit
            save_user_data(username, budgets, "budgets")
        elif choice == "10":
            display_budgets(budgets)
        elif choice == "11":
            if update_budget(budgets):
                save_user_data(username, budgets, "budgets")
        elif choice == "12":
            if delete_budget(budgets):
                save_user_data(username, budgets, "budgets")
        elif choice == "13":
            check_budget(expenses, budgets)
        elif choice == "14":
            generate_report(expenses)
        elif choice == "15":
            check_bill_reminders(expenses)
        elif choice == "16":
            print("Logging out...")
            return
        else:
            print("Invalid choice!")


def main():
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    while True:
        print("\nWelcome to Expense Tracker!")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        
        choice = input("Choose an option (1-3): ")
        
        if choice == "1":
            username = login()
            if username:
                main_menu(username)
        elif choice == "2":
            if register_user():
                print("Please login with your new account.")
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()