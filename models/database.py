import sqlite3
from datetime import datetime
import os
import hashlib
import secrets
import bcrypt

class Database:
    def __init__(self):
        # Create the database path relative to the current working directory
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'retail_store.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create Product Categories table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT NOT NULL
        )
        """)

        # Create Products/Inventory table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            quantity INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 10,
            sku TEXT UNIQUE,
            description TEXT,
            supplier TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """)

        # Create Users table for authentication
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('owner', 'cashier')),
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        """)

        # Create Audit Log table for tracking user actions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            ip_address TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Create Customers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            credit_limit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """)

        # Create Suppliers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            balance REAL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """)

        # Create Cash Transaction Types table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cash_transaction_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
        """)

        # Create Cash Transactions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cash_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            reference_no TEXT,
            description TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (type_id) REFERENCES cash_transaction_types (id)
        )
        """)

        # Create Non-Cash Transaction Types table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS non_cash_transaction_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
        """)

        # Create Non-Cash Transactions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS non_cash_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            reference_no TEXT,
            description TEXT,
            customer_id INTEGER,
            supplier_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (type_id) REFERENCES non_cash_transaction_types (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        )
        """)

        # Create Sales table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            total_amount REAL NOT NULL,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            payment_type TEXT NOT NULL, -- 'cash' or 'credit'
            status TEXT DEFAULT 'completed',
            reference_no TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
        """)

        # Create Sale Items table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)

        # Create Purchases table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            total_amount REAL NOT NULL,
            discount REAL DEFAULT 0,
            payment_type TEXT NOT NULL, -- 'cash' or 'credit'
            status TEXT DEFAULT 'received',
            reference_no TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        )
        """)

        # Create Purchase Items table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            total_cost REAL NOT NULL,
            FOREIGN KEY (purchase_id) REFERENCES purchases (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)

        # Create Purchase Returns table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            total_cost REAL NOT NULL,
            reason TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (purchase_id) REFERENCES purchases (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)

        # Create Sales Returns table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            reason TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)

        # Create Inventory Lots table for FIFO costing
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            purchase_id INTEGER,
            quantity_purchased INTEGER NOT NULL,
            quantity_remaining INTEGER NOT NULL,
            cost_per_unit REAL NOT NULL,
            date_acquired TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (purchase_id) REFERENCES purchases (id)
        )
        """)

        # Create Adjustments table (for inventory adjustments)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            adjustment_type TEXT NOT NULL, -- 'increase' or 'decrease'
            quantity INTEGER NOT NULL,
            reason TEXT,
            reference_no TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)

        # Create Journal Entries table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_type TEXT NOT NULL, -- 'cash_receipt', 'cash_disbursement', 'ap', 'general', 'sales'
            reference_no TEXT,
            description TEXT,
            date TEXT NOT NULL,
            total_debit REAL NOT NULL,
            total_credit REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # Create Journal Entry Lines table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entry_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_entry_id INTEGER NOT NULL,
            account_name TEXT NOT NULL,
            debit_amount REAL DEFAULT 0,
            credit_amount REAL DEFAULT 0,
            description TEXT,
            FOREIGN KEY (journal_entry_id) REFERENCES journal_entries (id)
        )
        """)

        # Create Accounts table (Chart of Accounts)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_code TEXT UNIQUE NOT NULL,
            account_name TEXT NOT NULL,
            account_type TEXT NOT NULL, -- 'asset', 'liability', 'equity', 'revenue', 'expense'
            parent_account_id INTEGER,
            balance REAL DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (parent_account_id) REFERENCES accounts (id)
        )
        """)

        # No default categories - user will add them manually
        # Categories table is ready for user input

        # Insert Cash transaction types if they don't exist
        cursor.execute("""
        INSERT OR IGNORE INTO cash_transaction_types (name, category, description)
        VALUES 
            -- Cash-in types
            ('Cash Sales', 'Cash-in', 'Revenue from direct cash sales'),
            ('Collections', 'Cash-in', 'Collection of receivables'),
            ('Customer Payment', 'Cash-in', 'Payments received from customers'),
            ('Investment', 'Cash-in', 'Capital investment in the business'),
            ('Unearned Sales', 'Cash-in', 'Advance payments received'),
            
            -- Cash-out types
            ('Expenses', 'Cash-out', 'Operating and administrative expenses'),
            ('Payables', 'Cash-out', 'Payment of accounts payable'),
            ('Supplier Payment', 'Cash-out', 'Payments made to suppliers'),
            ('Assets', 'Cash-out', 'Purchase of business assets'),
            ('Inventories', 'Cash-out', 'Purchase of inventory items'),
            ('Drawings', 'Cash-out', 'Owner withdrawals from business'),
            ('Bad Debt Write-off', 'Cash-out', 'Write-off of uncollectible accounts receivable')
        """)

        # Insert Non-Cash transaction types
        cursor.execute("""
        INSERT OR IGNORE INTO non_cash_transaction_types (name, category, description)
        VALUES 
            -- Non-cash in types
            ('Credit Sales', 'Non-cash-in', 'Sales on credit to customers'),
            ('Returns', 'Non-cash-in', 'Customer returns and refunds'),
            
            -- Non-cash out types
            ('Credit Purchases', 'Non-cash-out', 'Purchases on credit from suppliers'),
            ('Purchase Returns', 'Non-cash-out', 'Returns to suppliers')
        """)

        # Insert default chart of accounts
        cursor.execute("""
        INSERT OR IGNORE INTO accounts (account_code, account_name, account_type, created_at)
        VALUES 
            -- Assets
            ('1001', 'Cash', 'asset', ?),
            ('1002', 'Accounts Receivable', 'asset', ?),
            ('1003', 'Inventory', 'asset', ?),
            ('1004', 'Equipment', 'asset', ?),
            ('1005', 'Accumulated Depreciation - Equipment', 'asset', ?),
            
            -- Liabilities
            ('2001', 'Accounts Payable', 'liability', ?),
            ('2002', 'Unearned Revenue', 'liability', ?),
            
            -- Equity
            ('3001', 'Owner Capital', 'equity', ?),
            ('3002', 'Owner Drawings', 'equity', ?),
            ('3003', 'Retained Earnings', 'equity', ?),
            
            -- Revenue
            ('4001', 'Sales Revenue', 'revenue', ?),
            ('4002', 'Service Revenue', 'revenue', ?),
            ('4003', 'Sales Returns', 'revenue', ?),
            
            -- Expenses
            ('5001', 'Cost of Goods Sold', 'expense', ?),
            ('5002', 'Operating Expenses', 'expense', ?),
            ('5003', 'Depreciation Expense', 'expense', ?),
            ('6200', 'Utilities Expense', 'expense', ?),
            ('6600', 'Bad Debt Expense', 'expense', ?)
        """, tuple([datetime.now().isoformat()] * 18))

        self.conn.commit()

    def add_cash_in(self, type_name, amount, description="", reference_no=None):
        """Add a cash-in transaction"""
        cursor = self.conn.cursor()
        
        # Get the type_id for the transaction type
        cursor.execute("SELECT id FROM cash_transaction_types WHERE name = ? AND category = 'Cash-in'", (type_name,))
        type_id = cursor.fetchone()
        
        if type_id:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            INSERT INTO cash_transactions 
                (type_id, amount, date, reference_no, description, created_at)
            VALUES 
                (?, ?, ?, ?, ?, ?)
            """, (type_id[0], amount, now, reference_no, description, now))
            
            self.conn.commit()
            return True
        return False

    def get_cash_in_transactions(self, type_name=None, start_date=None, end_date=None):
        """Get cash-in transactions with optional filters"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            ct.date,
            ctt.name as type,
            ct.amount,
            ct.reference_no,
            ct.description
        FROM cash_transactions ct
        JOIN cash_transaction_types ctt ON ct.type_id = ctt.id
        WHERE ctt.category = 'Cash-in'
        """
        params = []
        
        if type_name:
            query += " AND ctt.name = ?"
            params.append(type_name)
            
        if start_date:
            query += " AND ct.date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND ct.date <= ?"
            params.append(end_date)
            
        query += " ORDER BY ct.date DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_total_cash_in(self, type_name=None):
        """Get total cash-in amount with optional type filter"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT SUM(ct.amount)
        FROM cash_transactions ct
        JOIN cash_transaction_types ctt ON ct.type_id = ctt.id
        WHERE ctt.category = 'Cash-in'
        """
        params = []
        
        if type_name:
            query += " AND ctt.name = ?"
            params.append(type_name)
            
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result[0] else 0.0

    def add_cash_out(self, type_name, amount, description="", reference_no=None):
        """Add a cash-out transaction"""
        cursor = self.conn.cursor()
        
        # Get the type_id for the transaction type
        cursor.execute("SELECT id FROM cash_transaction_types WHERE name = ? AND category = 'Cash-out'", (type_name,))
        type_id = cursor.fetchone()
        
        if type_id:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            INSERT INTO cash_transactions 
                (type_id, amount, date, reference_no, description, created_at)
            VALUES 
                (?, ?, ?, ?, ?, ?)
            """, (type_id[0], amount, now, reference_no, description, now))
            
            self.conn.commit()
            return True
        return False

    def get_cash_out_transactions(self, type_name=None, start_date=None, end_date=None):
        """Get cash-out transactions with optional filters"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            ct.date,
            ctt.name as type,
            ct.amount,
            ct.reference_no,
            ct.description
        FROM cash_transactions ct
        JOIN cash_transaction_types ctt ON ct.type_id = ctt.id
        WHERE ctt.category = 'Cash-out'
        """
        params = []
        
        if type_name:
            query += " AND ctt.name = ?"
            params.append(type_name)
            
        if start_date:
            query += " AND ct.date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND ct.date <= ?"
            params.append(end_date)
            
        query += " ORDER BY ct.date DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_total_cash_out(self, type_name=None):
        """Get total cash-out amount with optional type filter"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT SUM(ct.amount)
        FROM cash_transactions ct
        JOIN cash_transaction_types ctt ON ct.type_id = ctt.id
        WHERE ctt.category = 'Cash-out'
        """
        params = []
        
        if type_name:
            query += " AND ctt.name = ?"
            params.append(type_name)
            
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result[0] else 0.0

    def get_cash_balance(self):
        """Get current cash balance (Cash-in minus Cash-out)"""
        total_in = self.get_total_cash_in()
        total_out = self.get_total_cash_out()
        return total_in - total_out

    def close(self):
        """Close the database connection"""
        self.conn.close()

    # ========== PRODUCT/INVENTORY MANAGEMENT ==========
    
    def add_product(self, name, category_id, cost_price, selling_price, quantity=0, 
                   reorder_level=10, sku=None, description="", supplier=""):
        """Add a new product to inventory"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        try:
            cursor.execute("""
            INSERT INTO products 
                (name, category_id, cost_price, selling_price, quantity, 
                 reorder_level, sku, description, supplier, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, category_id, cost_price, selling_price, quantity, 
                  reorder_level, sku, description, supplier, now, now))
            
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def update_product(self, product_id, **kwargs):
        """Update product information"""
        cursor = self.conn.cursor()
        
        valid_fields = ['name', 'category_id', 'cost_price', 'selling_price', 
                       'quantity', 'reorder_level', 'sku', 'description', 'supplier']
        
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in valid_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(product_id)
            
            query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            self.conn.commit()
            return True
        return False

    def get_products(self, category_id=None, low_stock=False):
        """Get products with optional filters"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
        """
        params = []
        
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
            
        if low_stock:
            query += " AND p.quantity <= p.reorder_level"
            
        query += " ORDER BY p.name"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_product_by_id(self, product_id):
        """Get a specific product by ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
        """, (product_id,))
        return cursor.fetchone()

    def get_product_by_sku(self, sku):
        """Get a product by SKU - used for checking uniqueness"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.sku = ?
        """, (sku,))
        return cursor.fetchone()

    def get_product_by_name(self, name):
        """Get a product by name - used for checking if product already exists"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.name = ?
        """, (name,))
        return cursor.fetchone()

    def update_product_quantity(self, product_id, new_quantity):
        """Update product quantity"""
        return self.update_product(product_id, quantity=new_quantity)

    def delete_product(self, product_id):
        """Delete a product"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ========== CATEGORY MANAGEMENT ==========
    
    def add_category(self, name, description=""):
        """Add a new category"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO categories (name, description, created_at)
            VALUES (?, ?, ?)
            """, (name, description, datetime.now().isoformat()))
            
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_categories(self):
        """Get all categories"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name")
        return cursor.fetchall()
    
    def get_category_id_by_name(self, category_name):
        """Get category ID by name, return None if not found"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    # ========== SALES MANAGEMENT ==========
    
    def create_sale(self, items, customer_id=None, payment_type='cash', 
                   discount=0, tax=0, reference_no=None):
        """Create a new sale with items"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        # Calculate total
        total_amount = sum(item['quantity'] * item['unit_price'] for item in items)
        total_amount = total_amount - discount + tax
        
        try:
            # Validate stock availability before creating sale
            for item in items:
                total_cost, lots_consumed = self.get_fifo_cost(item['product_id'], item['quantity'])
                if total_cost is None:
                    # Not enough stock for this item
                    self.conn.rollback()
                    return None
            
            # Create sale record
            cursor.execute("""
            INSERT INTO sales 
                (customer_id, total_amount, discount, tax, payment_type, 
                 reference_no, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (customer_id, total_amount, discount, tax, payment_type, 
                  reference_no, now, now))
            
            sale_id = cursor.lastrowid
            
            # Add sale items (quantity updates will be handled by accounting engine)
            for item in items:
                # Add sale item
                total_price = item['quantity'] * item['unit_price']
                cursor.execute("""
                INSERT INTO sale_items 
                    (sale_id, product_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
                """, (sale_id, item['product_id'], item['quantity'], 
                      item['unit_price'], total_price))
            
            # Record cash transaction if cash sale
            if payment_type == 'cash':
                self.add_cash_in('Cash Sales', total_amount, 
                               f"Sale #{sale_id}", reference_no)
            else:
                # Record non-cash transaction for credit sale
                self.add_non_cash_in('Credit Sales', total_amount, 
                                   f"Credit Sale #{sale_id}", reference_no, customer_id)
            
            self.conn.commit()
            return sale_id
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating sale: {e}")
            return None

    def get_sales(self, start_date=None, end_date=None, customer_id=None):
        """Get sales with optional filters"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT s.*, c.name as customer_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND s.date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND s.date <= ?"
            params.append(end_date)
            
        if customer_id:
            query += " AND s.customer_id = ?"
            params.append(customer_id)
            
        query += " ORDER BY s.date DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_sale_items(self, sale_id):
        """Get items for a specific sale"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT si.*, p.name as product_name
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
        """, (sale_id,))
        return cursor.fetchall()

    # ========== PURCHASE MANAGEMENT ==========
    
    def create_purchase(self, items, supplier_id=None, payment_type='cash', 
                       discount=0, reference_no=None):
        """Create a new purchase with items"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        # Calculate total
        total_amount = sum(item['quantity'] * item['unit_cost'] for item in items)
        total_amount = total_amount - discount
        
        try:
            # Create purchase record
            cursor.execute("""
            INSERT INTO purchases 
                (supplier_id, total_amount, discount, payment_type, 
                 reference_no, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (supplier_id, total_amount, discount, payment_type, 
                  reference_no, now, now))
            
            purchase_id = cursor.lastrowid
            
            # Add purchase items and update inventory
            for item in items:
                # Add purchase item
                total_cost = item['quantity'] * item['unit_cost']
                cursor.execute("""
                INSERT INTO purchase_items 
                    (purchase_id, product_id, quantity, unit_cost, total_cost)
                VALUES (?, ?, ?, ?, ?)
                """, (purchase_id, item['product_id'], item['quantity'], 
                      item['unit_cost'], total_cost))
                
                # Update product quantity and cost
                cursor.execute("""
                UPDATE products 
                SET quantity = quantity + ?, cost_price = ?, updated_at = ?
                WHERE id = ?
                """, (item['quantity'], item['unit_cost'], now, item['product_id']))
            
            # Record cash transaction if cash purchase
            if payment_type == 'cash':
                self.add_cash_out('Inventories', total_amount, 
                                f"Purchase #{purchase_id}", reference_no)
            else:
                # Record non-cash transaction for credit purchase
                # If no supplier specified, create/use default "Unknown Supplier"
                if supplier_id is None:
                    # Check if "Unknown Supplier" already exists
                    cursor.execute("SELECT id FROM suppliers WHERE name = 'Unknown Supplier'")
                    result = cursor.fetchone()
                    
                    if result:
                        supplier_id = result[0]
                    else:
                        # Create "Unknown Supplier" record
                        cursor.execute("""
                        INSERT INTO suppliers (name, contact_person, email, phone, address, balance, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, ("Unknown Supplier", "", "", "", "Default supplier for unassigned purchases", 0, now))
                        supplier_id = cursor.lastrowid
                    
                    # Update the purchase record with the supplier_id
                    cursor.execute("UPDATE purchases SET supplier_id = ? WHERE id = ?", (supplier_id, purchase_id))
                
                self.add_non_cash_out('Credit Purchases', total_amount, 
                                    f"Credit Purchase #{purchase_id}", reference_no, supplier_id)
            
            self.conn.commit()
            return purchase_id
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating purchase: {e}")
            return None

    # ========== CUSTOMER MANAGEMENT ==========
    
    def add_customer(self, name, email="", phone="", address="", credit_limit=0):
        """Add a new customer"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO customers (name, email, phone, address, credit_limit, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, phone, address, credit_limit, datetime.now().isoformat()))
        
        self.conn.commit()
        return cursor.lastrowid

    def get_customers(self):
        """Get all customers"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY name")
        return cursor.fetchall()

    def update_customer_balance(self, customer_id, amount):
        """Update customer balance (for credit sales/payments)"""
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE customers SET balance = balance + ? WHERE id = ?
        """, (amount, customer_id))
        self.conn.commit()

    # ========== SUPPLIER MANAGEMENT ==========
    
    def add_supplier(self, name, contact_person="", email="", phone="", address=""):
        """Add a new supplier"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO suppliers (name, contact_person, email, phone, address, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, contact_person, email, phone, address, datetime.now().isoformat()))
        
        self.conn.commit()
        return cursor.lastrowid

    def get_suppliers(self):
        """Get all suppliers"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM suppliers ORDER BY name")
        return cursor.fetchall()

    def update_supplier_balance(self, supplier_id, amount):
        """Update supplier balance (for credit purchases/payments)"""
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE suppliers SET balance = balance + ? WHERE id = ?
        """, (amount, supplier_id))
        self.conn.commit()

    # ========== NON-CASH TRANSACTIONS ==========
    
    def add_non_cash_in(self, type_name, amount, description="", reference_no=None, customer_id=None):
        """Add a non-cash in transaction"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id FROM non_cash_transaction_types WHERE name = ? AND category = 'Non-cash-in'", (type_name,))
        type_id = cursor.fetchone()
        
        if type_id:
            now = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO non_cash_transactions 
                (type_id, amount, date, reference_no, description, customer_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (type_id[0], amount, now, reference_no, description, customer_id, now))
            
            # Update customer balance if applicable
            if customer_id and type_name == 'Credit Sales':
                self.update_customer_balance(customer_id, amount)
            
            self.conn.commit()
            return True
        return False

    def add_non_cash_out(self, type_name, amount, description="", reference_no=None, supplier_id=None):
        """Add a non-cash out transaction"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id FROM non_cash_transaction_types WHERE name = ? AND category = 'Non-cash-out'", (type_name,))
        type_id = cursor.fetchone()
        
        if type_id:
            now = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO non_cash_transactions 
                (type_id, amount, date, reference_no, description, supplier_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (type_id[0], amount, now, reference_no, description, supplier_id, now))
            
            # Update supplier balance if applicable
            if supplier_id and type_name == 'Credit Purchases':
                self.update_supplier_balance(supplier_id, amount)
            
            self.conn.commit()
            return True
        return False

    # ========== INVENTORY ADJUSTMENTS ==========
    
    def add_inventory_adjustment(self, product_id, adjustment_type, quantity, reason="", reference_no=None):
        """Add inventory adjustment"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        try:
            # Add adjustment record
            cursor.execute("""
            INSERT INTO inventory_adjustments 
                (product_id, adjustment_type, quantity, reason, reference_no, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product_id, adjustment_type, quantity, reason, reference_no, now, now))
            
            # Update product quantity
            if adjustment_type == 'increase':
                cursor.execute("""
                UPDATE products SET quantity = quantity + ?, updated_at = ? WHERE id = ?
                """, (quantity, now, product_id))
            else:  # decrease
                cursor.execute("""
                UPDATE products SET quantity = quantity - ?, updated_at = ? WHERE id = ?
                """, (quantity, now, product_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error adding inventory adjustment: {e}")
            return False

    # ========== JOURNAL ENTRIES ==========
    
    def create_journal_entry(self, journal_type, lines, reference_no=None, description=""):
        """Create a journal entry with multiple lines"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        total_debit = sum(line.get('debit_amount', 0) for line in lines)
        total_credit = sum(line.get('credit_amount', 0) for line in lines)
        
        if total_debit != total_credit:
            raise ValueError("Total debits must equal total credits")
        
        try:
            # Create journal entry
            cursor.execute("""
            INSERT INTO journal_entries 
                (journal_type, reference_no, description, date, total_debit, total_credit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (journal_type, reference_no, description, now, total_debit, total_credit, now))
            
            journal_id = cursor.lastrowid
            
            # Add journal entry lines
            for line in lines:
                cursor.execute("""
                INSERT INTO journal_entry_lines 
                    (journal_entry_id, account_name, debit_amount, credit_amount, description)
                VALUES (?, ?, ?, ?, ?)
                """, (journal_id, line['account_name'], 
                      line.get('debit_amount', 0), line.get('credit_amount', 0), 
                      line.get('description', '')))
            
            self.conn.commit()
            return journal_id
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating journal entry: {e}")
            return None

    # ========== REPORTING METHODS ==========
    
    def get_cash_flow_summary(self, start_date=None, end_date=None):
        """Get cash flow summary"""
        total_cash_in = self.get_total_cash_in()
        total_cash_out = self.get_total_cash_out()
        
        return {
            'total_cash_in': total_cash_in,
            'total_cash_out': total_cash_out,
            'net_cash_flow': total_cash_in - total_cash_out
        }

    def get_inventory_value(self):
        """Get total inventory value at cost"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(quantity * cost_price) FROM products")
        result = cursor.fetchone()
        return result[0] if result[0] else 0.0

    def get_low_stock_products(self):
        """Get products that are at or below reorder level"""
        return self.get_products(low_stock=True)

    def get_sales_summary(self, start_date=None, end_date=None):
        """Get sales summary"""
        cursor = self.conn.cursor()
        
        query = "SELECT COUNT(*), SUM(total_amount) FROM sales WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        return {
            'total_sales': result[0] if result[0] else 0,
            'total_revenue': result[1] if result[1] else 0.0
        }

    def get_journal_entries(self, journal_type=None, start_date=None, end_date=None):
        """Get journal entries with optional filters"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT je.*, COUNT(jel.id) as line_count
        FROM journal_entries je
        LEFT JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
        WHERE 1=1
        """
        params = []
        
        if journal_type:
            query += " AND je.journal_type = ?"
            params.append(journal_type)
            
        if start_date:
            query += " AND je.date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND je.date <= ?"
            params.append(end_date)
            
        query += " GROUP BY je.id ORDER BY je.date DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_journal_entry_lines(self, journal_entry_id):
        """Get lines for a specific journal entry"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT * FROM journal_entry_lines 
        WHERE journal_entry_id = ?
        ORDER BY id
        """, (journal_entry_id,))
        return cursor.fetchall()

    def get_account_balance(self, account_name):
        """Get balance for a specific account"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT 
            SUM(debit_amount) - SUM(credit_amount) as balance
        FROM journal_entry_lines 
        WHERE account_name = ?
        """, (account_name,))
        result = cursor.fetchone()
        return result[0] if result[0] else 0.0

    # Dashboard Statistics Methods
    def get_total_sales(self):
        """Get total sales revenue"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) 
        FROM sales 
        WHERE status = 'completed'
        """)
        result = cursor.fetchone()
        return result[0] if result else 0.0

    def get_total_expenses(self):
        """Get total expenses (purchases + other expenses)"""
        cursor = self.conn.cursor()
        
        # Get total purchases
        cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) 
        FROM purchases
        """)
        purchases = cursor.fetchone()[0] or 0.0
        
        # Get other expenses from journal entries
        cursor.execute("""
        SELECT COALESCE(SUM(debit_amount), 0)
        FROM journal_entry_lines 
        WHERE account_name LIKE '%Expense%' 
        OR account_name LIKE '%Cost%'
        """)
        expenses = cursor.fetchone()[0] or 0.0
        
        return purchases + expenses

    def get_net_profit(self):
        """Calculate net profit (sales - expenses)"""
        total_sales = self.get_total_sales()
        total_expenses = self.get_total_expenses()
        return total_sales - total_expenses

    def get_cost_of_goods_sold(self):
        """Calculate Cost of Goods Sold (COGS) - cost of products sold"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT COALESCE(SUM(si.quantity * p.cost_price), 0)
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE s.status = 'completed'
        """)
        result = cursor.fetchone()
        return result[0] if result else 0.0

    def get_gross_profit(self):
        """Calculate gross profit (sales revenue - COGS)"""
        total_sales = self.get_total_sales()
        cogs = self.get_cost_of_goods_sold()
        return total_sales - cogs

    def get_low_stock_count(self):
        """Get count of products with low stock"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT COUNT(*) 
        FROM products 
        WHERE quantity <= reorder_level
        """)
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_beginning_inventory_date(self):
        """Get the date and time of the last inventory adjustment"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT MAX(date) FROM inventory_adjustments
        """)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No adjustments"

    def get_beginning_inventory_amount(self):
        """Get the total value of beginning inventory based on last adjustments"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT SUM(ia.quantity * p.cost_price) as total_value
        FROM inventory_adjustments ia
        JOIN products p ON ia.product_id = p.id
        WHERE ia.adjustment_type = 'increase'
        """)
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0.0

    def get_last_purchase_date(self):
        """Get the date and time of the last purchase"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT MAX(date) FROM purchases
        """)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No purchases"

    def get_total_purchase_amount(self):
        """Get the total amount of all purchases"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) FROM purchases
        """)
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0.0

    def get_purchase_returns_value(self):
        """Get total value of purchase returns"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT COALESCE(SUM(total_cost), 0) FROM purchase_returns
        """)
        result = cursor.fetchone()
        return result[0] if result else 0.0

    def get_sales_returns_value(self):
        """Get total value of sales returns"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT COALESCE(SUM(total_price), 0) FROM sales_returns
        """)
        result = cursor.fetchone()
        return result[0] if result else 0.0

    def get_total_available_for_sale(self):
        """Get total value of inventory available for sale"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT COALESCE(SUM(quantity * cost_price), 0) FROM products
        """)
        result = cursor.fetchone()
        return result[0] if result else 0.0

    def add_purchase_return(self, purchase_id, product_id, quantity, unit_cost, reason=""):
        """Add a purchase return and create journal entry based on original purchase payment method"""
        total_cost = quantity * unit_cost
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = self.conn.cursor()
        try:
            # Get the original purchase payment type to determine correct journal entries
            payment_type = 'credit'  # Default assumption
            if purchase_id and purchase_id > 0:
                cursor.execute("SELECT payment_type FROM purchases WHERE id = ?", (purchase_id,))
                purchase_result = cursor.fetchone()
                if purchase_result:
                    payment_type = purchase_result[0]
            
            # Insert into purchase_returns
            cursor.execute("""
            INSERT INTO purchase_returns (purchase_id, product_id, quantity, unit_cost, total_cost, reason, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (purchase_id, product_id, quantity, unit_cost, total_cost, reason, date, date))
            
            # Decrease inventory quantity
            cursor.execute("""
            UPDATE products SET quantity = quantity - ? WHERE id = ?
            """, (quantity, product_id))
            
            # Create journal entries based on original purchase payment method
            if payment_type == 'cash':
                # Original cash purchase: Dr. Inventory, Cr. Cash (we paid cash)
                # For cash return: Dr. Cash (we get cash back), Cr. Inventory (we return goods)
                entries = [
                    {'account': 'Cash', 'debit': total_cost, 'credit': 0, 'description': f'Cash received for purchase return - {reason}'},
                    {'account': 'Inventory', 'debit': 0, 'credit': total_cost, 'description': f'Inventory returned - {reason}'}
                ]
            else:
                # Original credit purchase: Dr. Inventory, Cr. Accounts Payable (we owe money)
                # For credit return: Dr. Accounts Payable (reduce what we owe), Cr. Inventory (we return goods)
                entries = [
                    {'account': 'Accounts Payable', 'debit': total_cost, 'credit': 0, 'description': f'Reduce liability for purchase return - {reason}'},
                    {'account': 'Inventory', 'debit': 0, 'credit': total_cost, 'description': f'Inventory returned - {reason}'}
                ]
            
            # Create accounting journal entry
            from models.accounting_engine import AccountingEngine
            accounting = AccountingEngine(self)
            return_id = cursor.lastrowid
            journal_ref = f'PR-{return_id}'
            journal_desc = f'Purchase Return ({payment_type}) - {reason}'
            
            accounting.create_journal_entry('general', journal_ref, journal_desc, entries, date)
            
            self.conn.commit()
            print(f"Purchase return processed: {payment_type} purchase, ₱{total_cost:.2f}")
            return return_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_sales_return(self, sale_id, product_id, quantity, unit_price, reason=""):
        """Add a sales return and create journal entry"""
        total_selling = quantity * unit_price
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        cost_price = product[3]  # cost_price from products table
        total_cost = quantity * cost_price
        margin = total_selling - total_cost
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = self.conn.cursor()
        try:
            # Insert into sales_returns
            cursor.execute("""
            INSERT INTO sales_returns (sale_id, product_id, quantity, unit_price, total_price, reason, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sale_id, product_id, quantity, unit_price, total_selling, reason, date, date))
            
            # Increase inventory quantity
            cursor.execute("""
            UPDATE products SET quantity = quantity + ? WHERE id = ?
            """, (quantity, product_id))
            
            # Create journal entry for sales return (proper accounting treatment):
            # Dr. Sales Returns (contra-revenue account)
            # Dr. Inventory (restore inventory at cost)
            # Cr. Cost of Goods Sold (reverse COGS)
            # Cr. Cash (refund to customer)
            entries = [
                {'account': 'Sales Returns', 'debit': total_selling, 'credit': 0, 'description': f'Sales Return - {reason}'},
                {'account': 'Inventory', 'debit': total_cost, 'credit': 0, 'description': f'Inventory restored - {reason}'},
                {'account': 'Cost of Goods Sold', 'debit': 0, 'credit': total_cost, 'description': f'COGS reversal - {reason}'},
                {'account': 'Cash', 'debit': 0, 'credit': total_selling, 'description': f'Cash refund - {reason}'}
            ]
            # Create accounting journal entry
            from models.accounting_engine import AccountingEngine
            accounting = AccountingEngine(self)
            accounting.create_journal_entry('general', f'SR-{cursor.lastrowid}', f'Sales Return - {reason}', entries, date)
            
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_inventory_lot(self, product_id, purchase_id, quantity, cost_per_unit, date_acquired=None):
        """Add a new inventory lot for FIFO costing and update product quantity"""
        if date_acquired is None:
            date_acquired = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO inventory_lots 
            (product_id, purchase_id, quantity_purchased, quantity_remaining, 
             cost_per_unit, date_acquired, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (product_id, purchase_id, quantity, quantity, cost_per_unit, 
              date_acquired, datetime.now().isoformat()))
        
        lot_id = cursor.lastrowid
        
        # Update product quantity
        cursor.execute("""
        UPDATE products 
        SET quantity = quantity + ?, updated_at = ?
        WHERE id = ?
        """, (quantity, datetime.now().isoformat(), product_id))
        
        self.conn.commit()
        return lot_id

    def get_inventory_lots(self, product_id):
        """Get all inventory lots for a product, ordered by date acquired (FIFO)"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT * FROM inventory_lots 
        WHERE product_id = ? AND quantity_remaining > 0
        ORDER BY date_acquired ASC
        """, (product_id,))
        return cursor.fetchall()

    def consume_inventory_lot(self, lot_id, quantity_consumed):
        """Reduce quantity remaining in an inventory lot and update product quantity"""
        cursor = self.conn.cursor()
        
        # First, get the product_id for this lot
        cursor.execute("SELECT product_id FROM inventory_lots WHERE id = ?", (lot_id,))
        result = cursor.fetchone()
        if not result:
            return False
            
        product_id = result[0]
        
        # Update inventory lot
        cursor.execute("""
        UPDATE inventory_lots 
        SET quantity_remaining = quantity_remaining - ?
        WHERE id = ? AND quantity_remaining >= ?
        """, (quantity_consumed, lot_id, quantity_consumed))
        
        # Update product quantity
        if cursor.rowcount > 0:
            cursor.execute("""
            UPDATE products 
            SET quantity = quantity - ?, updated_at = ?
            WHERE id = ?
            """, (quantity_consumed, datetime.now().isoformat(), product_id))
        
        self.conn.commit()
        return cursor.rowcount > 0

    def get_fifo_cost(self, product_id, quantity_needed):
        """
        Calculate FIFO cost for a given quantity of a product
        Returns total cost and list of lots consumed
        """
        lots = self.get_inventory_lots(product_id)
        total_cost = 0
        lots_consumed = []
        remaining_needed = quantity_needed
        
        for lot in lots:
            if remaining_needed <= 0:
                break
                
            available = lot[4]  # quantity_remaining
            consume_qty = min(remaining_needed, available)
            
            cost = consume_qty * lot[5]  # cost_per_unit
            total_cost += cost
            
            lots_consumed.append({
                'lot_id': lot[0],
                'quantity_consumed': consume_qty,
                'cost_per_unit': lot[5],
                'total_cost': cost
            })
            
            remaining_needed -= consume_qty
        
        if remaining_needed > 0:
            # Not enough inventory
            return None, None
        
        return total_cost, lots_consumed

    def get_inventory_stats(self):
        """Get inventory-specific statistics for FIFO implementation"""
        return {
            'beginning_inventory_date': self.get_beginning_inventory_date(),
            'beginning_inventory_amount': self.get_beginning_inventory_amount(),
            'last_purchase_date': self.get_last_purchase_date(),
            'total_purchase_amount': self.get_total_purchase_amount(),
            'purchase_returns_value': self.get_purchase_returns_value(),
            'sales_returns_value': self.get_sales_returns_value(),
            'total_available_value': self.get_total_available_for_sale()
        }

    def get_dashboard_stats(self):
        """Get all dashboard statistics in one call"""
        return {
            'total_sales': self.get_total_sales(),
            'cost_of_goods_sold': self.get_cost_of_goods_sold(),
            'gross_profit': self.get_gross_profit(),
            'low_stock_count': self.get_low_stock_count()
        }

    def get_all_accounts_with_balances(self):
        """Get all accounts with their current balances (ensuring unique accounts only)"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
            SELECT a.id, a.account_name, a.account_type, a.balance
            FROM accounts a
            GROUP BY a.account_name, a.account_type
            HAVING a.id = MIN(a.id)
            ORDER BY a.account_type, a.account_name
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting accounts with balances: {e}")
            return []
    
    def get_all_skus(self):
        """Get all existing SKUs to avoid duplicates"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT sku FROM products WHERE sku IS NOT NULL AND sku != ''")
            skus = cursor.fetchall()
            return [sku[0] for sku in skus]
        except Exception as e:
            print(f"Error getting SKUs: {e}")
            return []

    def update_supplier_balance(self, supplier_id, amount):
        """Update supplier balance (for credit purchases/payments)"""
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE suppliers SET balance = balance + ? WHERE id = ?
        """, (amount, supplier_id))
        self.conn.commit()

    def get_credit_sales(self, customer_id=None):
        """Get all credit sales with outstanding balances (unpaid)"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT s.id, s.customer_id, COALESCE(c.name, 'Walk-in Customer') as customer_name, s.total_amount, 
               s.date, s.reference_no, 
               CASE 
                   WHEN s.customer_id IS NULL THEN 
                       -- For walk-in customers, calculate outstanding by subtracting payments from sale amount
                       s.total_amount - COALESCE(
                           (SELECT SUM(amount) FROM cash_transactions ct 
                            JOIN cash_transaction_types ctt ON ct.type_id = ctt.id
                            WHERE ctt.name = 'Customer Payment' 
                            AND ct.description LIKE '%sale #' || s.id || '%'), 0)
                   ELSE COALESCE(c.balance, 0)  -- For registered customers, use customer balance
               END as outstanding_balance
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE s.payment_type = 'credit' AND s.status = 'completed' 
        AND (
            (s.customer_id IS NULL AND 
             s.total_amount > COALESCE(
                 (SELECT SUM(amount) FROM cash_transactions ct 
                  JOIN cash_transaction_types ctt ON ct.type_id = ctt.id
                  WHERE ctt.name = 'Customer Payment' 
                  AND ct.description LIKE '%sale #' || s.id || '%'), 0)) OR  -- Walk-in credit sales with remaining balance
            (s.customer_id IS NOT NULL AND COALESCE(c.balance, 0) > 0)  -- Registered customer credit sales
        )
        """
        params = []
        
        if customer_id:
            query += " AND s.customer_id = ?"
            params.append(customer_id)
            
        query += " ORDER BY s.date DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_credit_purchases(self, supplier_id=None):
        """Get all credit purchases with outstanding balances (unpaid)"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT p.id, p.supplier_id, COALESCE(s.name, 'Unknown Supplier') as supplier_name, p.total_amount,
               p.date, p.reference_no, p.total_amount as purchase_amount
        FROM purchases p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.payment_type = 'credit' AND p.status = 'received' 
        AND COALESCE(s.balance, 0) > 0
        """
        params = []
        
        if supplier_id:
            query += " AND p.supplier_id = ?"
            params.append(supplier_id)
            
        query += " ORDER BY p.date DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def record_customer_payment(self, customer_id, amount, reference_no=None, description=""):
        """Record a payment from a customer (reduces customer balance)"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        # Add to cash transactions (cash inflow)
        cursor.execute("""
        INSERT INTO cash_transactions (type_id, amount, date, reference_no, description, created_at)
        VALUES ((SELECT id FROM cash_transaction_types WHERE name = 'Customer Payment'), ?, ?, ?, ?, ?)
        """, (amount, now, reference_no, description, now))

        # Update customer balance only if customer_id is not None
        # For walk-in customers (customer_id=None), we don't maintain individual balances
        if customer_id is not None:
            self.update_customer_balance(customer_id, -amount)

        # Create accounting journal entry
        from models.accounting_engine import AccountingEngine
        accounting = AccountingEngine(self)
        accounting.process_customer_payment(customer_id, amount, reference_no, description)

        self.conn.commit()
        return cursor.lastrowid

    def record_supplier_payment(self, supplier_id, amount, reference_no=None, description=""):
        """Record a payment to a supplier (reduces supplier balance)"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        # Handle NULL supplier_id by creating/using a default "Unknown Supplier"
        if supplier_id is None:
            # Check if "Unknown Supplier" already exists
            cursor.execute("SELECT id FROM suppliers WHERE name = 'Unknown Supplier'")
            result = cursor.fetchone()
            
            if result:
                supplier_id = result[0]
            else:
                # Create "Unknown Supplier" record
                cursor.execute("""
                INSERT INTO suppliers (name, contact_person, email, phone, address, balance, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("Unknown Supplier", "", "", "", "Default supplier for unassigned purchases", 0, now))
                supplier_id = cursor.lastrowid

        # Add to cash transactions (cash outflow)
        cursor.execute("""
        INSERT INTO cash_transactions (type_id, amount, date, reference_no, description, created_at)
        VALUES ((SELECT id FROM cash_transaction_types WHERE name = 'Supplier Payment'), ?, ?, ?, ?, ?)
        """, (amount, now, reference_no, description, now))

        # Update supplier balance (negative amount reduces balance)
        self.update_supplier_balance(supplier_id, -amount)

        # Create accounting journal entry
        from models.accounting_engine import AccountingEngine
        accounting = AccountingEngine(self)
        accounting.process_supplier_payment(supplier_id, amount, reference_no, description)

        self.conn.commit()
        return cursor.lastrowid

    def record_bad_debt_write_off(self, customer_id, sale_id, amount, description=""):
        """Record a bad debt write-off for an uncollectible account receivable"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        try:
            # First, verify the sale exists and is a credit sale with outstanding balance
            cursor.execute("""
                SELECT s.total_amount, COALESCE(c.balance, 0) as customer_balance
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.id = ? AND s.payment_type = 'credit' AND s.status = 'completed'
            """, (sale_id,))
            
            sale_data = cursor.fetchone()
            if not sale_data:
                raise ValueError(f"Sale #{sale_id} not found or not a valid credit sale")
            
            sale_amount, customer_balance = sale_data
            
            # For bad debt write-off, validate against the sale amount (what we're writing off)
            # We allow writing off up to the full sale amount
            if amount > sale_amount:
                raise ValueError(f"Write-off amount ₱{amount:,.2f} exceeds sale amount ₱{sale_amount:,.2f}")
            
            if amount <= 0:
                raise ValueError("Write-off amount must be greater than zero")

            # Record the bad debt transaction
            cursor.execute("""
            INSERT INTO cash_transactions (type_id, amount, date, reference_no, description, created_at)
            VALUES ((SELECT id FROM cash_transaction_types WHERE name = 'Bad Debt Write-off'), ?, ?, ?, ?, ?)
            """, (amount, now, f"BD-{sale_id}", description or f"Bad debt write-off for sale #{sale_id}", now))

            # Update customer balance (negative amount reduces balance)
            self.update_customer_balance(customer_id, -amount)

            # Mark the sale as written off to prevent it from showing in active transactions
            cursor.execute("""
                UPDATE sales SET status = 'written_off' WHERE id = ?
            """, (sale_id,))
            
            self.conn.commit()
            print(f"Sale #{sale_id} marked as written off due to bad debt")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error recording bad debt write-off: {e}")
            raise e
    
    # =====================================================
    # USER AUTHENTICATION AND AUTHORIZATION METHODS
    # =====================================================
    
    def create_default_user(self):
        """Create default admin user if no users exist"""
        cursor = self.conn.cursor()
        try:
            # Check if any users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                # Create default owner account
                default_password = "admin123"
                password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())
                
                cursor.execute("""
                INSERT INTO users (username, password_hash, role, is_active, created_at)
                VALUES (?, ?, 'owner', 1, ?)
                """, ("admin", password_hash.decode('utf-8'), datetime.now().isoformat()))
                
                self.conn.commit()
                print("Default admin user created. Username: admin, Password: admin123")
                print("Please change the default password after first login!")
                return True
            return False
        except Exception as e:
            print(f"Error creating default user: {e}")
            self.conn.rollback()
            return False
    
    def create_user(self, username, password, role, created_by_user_id):
        """Create a new user account"""
        cursor = self.conn.cursor()
        try:
            # Validate role
            if role not in ['owner', 'cashier']:
                raise ValueError("Role must be 'owner' or 'cashier'")
            
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Insert new user
            cursor.execute("""
            INSERT INTO users (username, password_hash, role, is_active, created_at, created_by)
            VALUES (?, ?, ?, 1, ?, ?)
            """, (username, password_hash.decode('utf-8'), role, datetime.now().isoformat(), created_by_user_id))
            
            user_id = cursor.lastrowid
            self.conn.commit()
            
            # Log the action
            self.log_audit_action(created_by_user_id, "CREATE_USER", "users", user_id, 
                                None, f"Created user: {username} with role: {role}")
            
            return user_id
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise ValueError("Username already exists")
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error creating user: {e}")
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        cursor = self.conn.cursor()
        try:
            # Get user data
            cursor.execute("""
            SELECT id, username, password_hash, role, is_active, last_login
            FROM users WHERE username = ? AND is_active = 1
            """, (username,))
            
            user_data = cursor.fetchone()
            if not user_data:
                return None
            
            user_id, db_username, password_hash, role, is_active, last_login = user_data
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                # Update last login
                cursor.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
                """, (datetime.now().isoformat(), user_id))
                self.conn.commit()
                
                # Log successful login
                self.log_audit_action(user_id, "LOGIN", "users", user_id, None, f"User {username} logged in")
                
                return {
                    'user_id': user_id,
                    'username': db_username,
                    'role': role,
                    'last_login': last_login
                }
            else:
                # Log failed login attempt
                self.log_audit_action(None, "FAILED_LOGIN", "users", None, None, f"Failed login attempt for {username}")
                return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user information by ID"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
            SELECT id, username, role, is_active, created_at, last_login
            FROM users WHERE id = ?
            """, (user_id,))
            
            user_data = cursor.fetchone()
            if user_data:
                return {
                    'user_id': user_data[0],
                    'username': user_data[1],
                    'role': user_data[2],
                    'is_active': user_data[3],
                    'created_at': user_data[4],
                    'last_login': user_data[5]
                }
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_user_password(self, user_id, new_password, updated_by_user_id):
        """Update user password"""
        cursor = self.conn.cursor()
        try:
            # Get current user info for audit
            old_user = self.get_user_by_id(user_id)
            if not old_user:
                raise ValueError("User not found")
            
            # Hash new password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute("""
            UPDATE users SET password_hash = ? WHERE id = ?
            """, (password_hash.decode('utf-8'), user_id))
            
            self.conn.commit()
            
            # Log the action
            self.log_audit_action(updated_by_user_id, "UPDATE_PASSWORD", "users", user_id,
                                None, f"Password updated for user: {old_user['username']}")
            
            return True
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error updating password: {e}")
    
    def deactivate_user(self, user_id, deactivated_by_user_id):
        """Deactivate a user account"""
        cursor = self.conn.cursor()
        try:
            # Get current user info for audit
            old_user = self.get_user_by_id(user_id)
            if not old_user:
                raise ValueError("User not found")
            
            cursor.execute("""
            UPDATE users SET is_active = 0 WHERE id = ?
            """, (user_id,))
            
            self.conn.commit()
            
            # Log the action
            self.log_audit_action(deactivated_by_user_id, "DEACTIVATE_USER", "users", user_id,
                                f"is_active: {old_user['is_active']}", "is_active: 0")
            
            return True
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error deactivating user: {e}")
    
    def get_all_users(self):
        """Get all users (for admin management)"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
            SELECT id, username, role, is_active, created_at, last_login
            FROM users ORDER BY username
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'role': row[2],
                    'is_active': row[3],
                    'created_at': row[4],
                    'last_login': row[5]
                })
            return users
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def log_audit_action(self, user_id, action, table_name=None, record_id=None, 
                        old_values=None, new_values=None, ip_address=None):
        """Log user actions for audit trail"""
        cursor = self.conn.cursor()
        try:
            # Get username if user_id provided
            username = "system"
            if user_id:
                user = self.get_user_by_id(user_id)
                username = user['username'] if user else f"user_id:{user_id}"
            
            cursor.execute("""
            INSERT INTO audit_log (user_id, username, action, table_name, record_id, 
                                 old_values, new_values, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, action, table_name, record_id, old_values, 
                  new_values, ip_address, datetime.now().isoformat()))
            
            self.conn.commit()
        except Exception as e:
            print(f"Error logging audit action: {e}")
    
    def get_audit_log(self, user_id=None, action=None, limit=100):
        """Get audit log entries"""
        cursor = self.conn.cursor()
        try:
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if action:
                query += " AND action = ?"
                params.append(action)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'id': row[0],
                    'user_id': row[1],
                    'username': row[2],
                    'action': row[3],
                    'table_name': row[4],
                    'record_id': row[5],
                    'old_values': row[6],
                    'new_values': row[7],
                    'ip_address': row[8],
                    'timestamp': row[9]
                })
            return logs
        except Exception as e:
            print(f"Error getting audit log: {e}")
            return []
    
    def get_all_users_for_management(self):
        """Get all users from database for management interface"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
            SELECT id, username, role, is_active, created_at, last_login
            FROM users 
            ORDER BY created_at DESC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting users for management: {e}")
            return []
    
    def create_user_by_admin(self, username, password_hash, role, created_by_user_id):
        """Create a new user (admin function)"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO users (username, password_hash, role, is_active, created_at, created_by)
            VALUES (?, ?, ?, 1, ?, ?)
            """, (username, password_hash, role, datetime.now().isoformat(), created_by_user_id))
            
            user_id = cursor.lastrowid
            self.conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return None  # Username already exists
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating user: {e}")
            return None
    
    def delete_user_by_admin(self, user_id):
        """Delete a user (admin function)"""
        cursor = self.conn.cursor()
        try:
            # Prevent deletion of admin user
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result and result[0] == 'admin':
                return False  # Cannot delete admin user
            
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            print(f"Error deleting user: {e}")
            return False

            self.conn.commit()
            print(f"Bad debt write-off recorded: ₱{amount:,.2f} for customer #{customer_id}, sale #{sale_id}")
            return cursor.lastrowid

        except Exception as e:
            self.conn.rollback()
            print(f"Error recording bad debt write-off: {e}")
            raise

    def sync_product_quantities_with_inventory_lots(self):
        """Sync product quantities with the sum of remaining inventory lots"""
        cursor = self.conn.cursor()
        
        try:
            # Update product quantities based on inventory lots
            cursor.execute("""
            UPDATE products 
            SET quantity = (
                SELECT COALESCE(SUM(quantity_remaining), 0)
                FROM inventory_lots 
                WHERE inventory_lots.product_id = products.id
            ),
            updated_at = ?
            """, (datetime.now().isoformat(),))
            
            self.conn.commit()
            print("Product quantities synced with inventory lots")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error syncing product quantities: {e}")
            return False

    def add_cash_investment(self, amount, description="Owner cash investment"):
        """Add cash investment to the business and create journal entry"""
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = self.conn.cursor()
        try:
            # Get the Investment transaction type ID
            cursor.execute("""
            SELECT id FROM cash_transaction_types WHERE name = 'Investment'
            """)
            investment_type = cursor.fetchone()
            if not investment_type:
                raise ValueError("Investment transaction type not found")
            
            type_id = investment_type[0]
            
            # Insert into cash_transactions table
            cursor.execute("""
            INSERT INTO cash_transactions (type_id, amount, date, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (type_id, amount, date, description, date))
            
            transaction_id = cursor.lastrowid
            
            # Create journal entry for cash investment:
            # Dr. Cash (increase asset)  
            # Cr. Owner Capital (increase equity)
            entries = [
                {'account': 'Cash', 'debit': amount, 'credit': 0, 'description': description},
                {'account': 'Owner Capital', 'debit': 0, 'credit': amount, 'description': description}
            ]
            
            # Create accounting journal entry
            from models.accounting_engine import AccountingEngine
            accounting = AccountingEngine(self)
            accounting.create_journal_entry('general', f'INV-{transaction_id}', description, entries, date)
            
            self.conn.commit()
            return transaction_id
        except Exception as e:
            self.conn.rollback()
            raise e
