#!/usr/bin/env python3
"""
Database Viewer Script
View and inspect the retail store database contents
"""

from database import Database

def view_database():
    """View database contents"""
    db = Database()
    
    print("=" * 60)
    print("RETAIL STORE DATABASE VIEWER")
    print("=" * 60)
    
    # View Categories
    print("\n[CATEGORIES]:")
    print("-" * 40)
    categories = db.get_categories()
    for cat in categories:
        print(f"ID: {cat[0]}, Name: {cat[1]}, Description: {cat[2]}")
    
    # View Products
    print("\n[PRODUCTS]:")
    print("-" * 40)
    products = db.get_products()
    for prod in products:
        print(f"ID: {prod[0]}, Name: {prod[1]}, Category: {prod[12] if len(prod) > 12 else 'N/A'}")
        print(f"    Cost: P{prod[3]:.2f}, Price: P{prod[4]:.2f}, Stock: {prod[5]}, SKU: {prod[7]}")
    
    # View Customers
    print("\n[CUSTOMERS]:")
    print("-" * 40)
    customers = db.get_customers()
    for cust in customers:
        print(f"ID: {cust[0]}, Name: {cust[1]}, Email: {cust[2]}, Credit Limit: P{cust[5]:,.2f}")
    
    # View Suppliers
    print("\n[SUPPLIERS]:")
    print("-" * 40)
    suppliers = db.get_suppliers()
    for supp in suppliers:
        print(f"ID: {supp[0]}, Name: {supp[1]}, Contact: {supp[2]}, Email: {supp[3]}")
    
    # View Sales
    print("\n[SALES]:")
    print("-" * 40)
    sales = db.get_sales()
    for sale in sales:
        customer_name = sale[8] if len(sale) > 8 and sale[8] else "Walk-in"
        print(f"Sale #{sale[0]}: P{sale[2]:,.2f} ({sale[5]}) - Customer: {customer_name}")
        print(f"    Date: {sale[7]}, Reference: {sale[6]}")
        
        # Show sale items
        sale_items = db.get_sale_items(sale[0])
        for item in sale_items:
            print(f"    - {item[6]}: {item[2]} x P{item[3]:.2f} = P{item[4]:.2f}")
    
    # View Cash Transactions Summary
    print("\n[CASH FLOW SUMMARY]:")
    print("-" * 40)
    cash_flow = db.get_cash_flow_summary()
    print(f"Cash In:  P{cash_flow['total_cash_in']:,.2f}")
    print(f"Cash Out: P{cash_flow['total_cash_out']:,.2f}")
    print(f"Net Flow: P{cash_flow['net_cash_flow']:,.2f}")
    
    # View detailed cash transactions
    print("\n[CASH IN TRANSACTIONS]:")
    print("-" * 40)
    cash_in = db.get_cash_in_transactions()
    for trans in cash_in:
        print(f"{trans[0]}: {trans[1]} - P{trans[2]:,.2f} (Ref: {trans[3]})")
    
    print("\n[CASH OUT TRANSACTIONS]:")
    print("-" * 40)
    cash_out = db.get_cash_out_transactions()
    for trans in cash_out:
        print(f"{trans[0]}: {trans[1]} - P{trans[2]:,.2f} (Ref: {trans[3]})")
    
    # View Journal Entries
    print("\n[JOURNAL ENTRIES]:")
    print("-" * 40)
    journal_entries = db.get_journal_entries()
    for entry in journal_entries:
        print(f"Entry #{entry[0]} ({entry[1]}): {entry[3]} - P{entry[5]:,.2f}")
        print(f"    Date: {entry[4]}, Ref: {entry[2]}")
        
        # Show journal lines
        lines = db.get_journal_entry_lines(entry[0])
        for line in lines:
            # line format: (id, journal_entry_id, account_name, debit_amount, credit_amount, description)
            try:
                debit_amount = float(line[3]) if line[3] else 0
                credit_amount = float(line[4]) if line[4] else 0
                
                if debit_amount > 0:  # Debit
                    print(f"    Dr. {line[2]}: P{debit_amount:,.2f}")
                if credit_amount > 0:  # Credit
                    print(f"    Cr. {line[2]}: P{credit_amount:,.2f}")
            except (ValueError, IndexError) as e:
                print(f"    Error displaying journal line: {e}")
    
    # View Low Stock Products
    print("\n[LOW STOCK ALERT]:")
    print("-" * 40)
    low_stock = db.get_low_stock_products()
    if low_stock:
        for prod in low_stock:
            print(f"WARNING: {prod[1]}: {prod[5]} units (Reorder at: {prod[6]})")
    else:
        print("No low stock items")
    
    # View Inventory Value
    print(f"\n[TOTAL INVENTORY VALUE]: P{db.get_inventory_value():,.2f}")
    
    db.close()

def view_table_structure():
    """View database table structure"""
    db = Database()
    cursor = db.conn.cursor()
    
    print("\n" + "=" * 60)
    print("DATABASE SCHEMA")
    print("=" * 60)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\n[TABLE: {table_name.upper()}]")
        print("-" * 40)
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            nullable = "NOT NULL" if col[3] else "NULL"
            default = f"DEFAULT {col[4]}" if col[4] else ""
            pk = "PRIMARY KEY" if col[5] else ""
            print(f"  {col[1]:<20} {col[2]:<10} {nullable:<8} {default:<15} {pk}")
    
    db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--schema":
        view_table_structure()
    else:
        view_database()
    
    print("\n" + "=" * 60)
    print("To view database schema, run: python view_db.py --schema")
    print("=" * 60)
