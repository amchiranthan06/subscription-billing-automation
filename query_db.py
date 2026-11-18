import sqlite3
import os
import sys

db_path = os.path.join(os.path.dirname(__file__), "billflow.db")
if not os.path.exists(db_path):
    print(f"Error: Database file not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 65)
print("             BILLFLOW SQL DATABASE VIEWER")
print("=" * 65)

# 1. Show all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [t[0] for t in cursor.fetchall() if not t[0].startswith("sqlite_")]
print(f"\n📂 TABLES FOUND ({len(tables)}):")
print(", ".join(tables))

# 2. Show Users
print("\n" + "=" * 65)
print(" 👤 TABLE: users (Authentication Data)")
print("=" * 65)
cursor.execute("SELECT id, name, email, role, created_at FROM users;")
users = cursor.fetchall()
if users:
    print(f"{'NAME':<15} {'EMAIL':<28} {'ROLE':<8} {'CREATED AT'}")
    print("-" * 65)
    for u in users:
        print(f"{u[1]:<15} {u[2]:<28} {u[3]:<8} {str(u[4])[:19]}")
else:
    print("No users found.")

# 3. Show Invoices
print("\n" + "=" * 65)
print(" 📄 TABLE: invoices (Milestone 2 - Task 1 Generated Invoices)")
print("=" * 65)
cursor.execute("SELECT invoice_number, subtotal, tax_amount, total_amount, status, created_at FROM invoices;")
invoices = cursor.fetchall()
if invoices:
    print(f"{'INVOICE #':<18} {'SUBTOTAL':<10} {'TAX':<10} {'TOTAL':<10} {'STATUS':<8}")
    print("-" * 65)
    for inv in invoices:
        print(f"{inv[0]:<18} ${inv[1]:<9} ${inv[2]:<9} ${inv[3]:<9} {inv[4]}")
else:
    print("No invoices found.")

# 4. Show Subscriptions
print("\n" + "=" * 65)
print(" 🔁 TABLE: subscriptions (Active Subscriptions)")
print("=" * 65)
cursor.execute("SELECT id, status, start_date, end_date FROM subscriptions;")
subs = cursor.fetchall()
if subs:
    for s in subs:
        print(f"Sub ID: {s[0]} | Status: {s[1]} | Period: {str(s[2])[:10]} to {str(s[3])[:10]}")
else:
    print("No subscriptions found.")

print("\n" + "=" * 65 + "\n")
conn.close()
