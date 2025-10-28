from datetime import datetime
from dataclasses import dataclass
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.tab import MDTabsBase

@dataclass
class AccountingEngine:
    """
    Comprehensive Accounting Engine for Double-Entry Bookkeeping
    Handles all accounting transactions, journal entries, and ledger updates
    """
    
    def __init__(self, database):
        self.db = database
        # Skip chart initialization - accounts are managed externally
        print("📚 AccountingEngine initialized (chart of accounts managed externally)")
    
    def needs_chart_initialization(self):
        """Check if the chart of accounts needs to be initialized"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts")
            count = cursor.fetchone()[0]
            return count == 0  # Only initialize if no accounts exist
        except:
            return True  # Initialize if there's an error checking
    
    def initialize_chart_of_accounts(self):
        """Initialize the chart of accounts with standard retail business accounts"""
        accounts = [
            # ASSETS
            ('1000', 'Cash', 'asset', None),
            ('1100', 'Accounts Receivable', 'asset', None),
            ('1200', 'Inventory', 'asset', None),
            ('1300', 'Prepaid Expenses', 'asset', None),
            ('1500', 'Equipment', 'asset', None),
            ('1600', 'Accumulated Depreciation - Equipment', 'asset', None),
            
            # LIABILITIES
            ('2000', 'Accounts Payable', 'liability', None),
            ('2100', 'Sales Tax Payable', 'liability', None),
            ('2200', 'Accrued Expenses', 'liability', None),
            ('2500', 'Notes Payable', 'liability', None),
            
            # EQUITY
            ('3000', 'Owner\'s Capital', 'equity', None),
            ('3100', 'Retained Earnings', 'equity', None),
            ('3200', 'Owner\'s Drawings', 'equity', None),
            
            # REVENUE
            ('4000', 'Sales Revenue', 'revenue', None),
            ('4100', 'Service Revenue', 'revenue', None),
            ('4200', 'Other Income', 'revenue', None),
            ('4300', 'Sales Returns', 'revenue', None),  # Contra revenue account
            
            # EXPENSES
            ('5000', 'Cost of Goods Sold', 'expense', None),
            ('6000', 'Operating Expenses', 'expense', None),
            ('6100', 'Rent Expense', 'expense', None),
            ('6200', 'Utilities Expense', 'expense', None),
            ('6300', 'Depreciation Expense', 'expense', None),
            ('6400', 'Advertising Expense', 'expense', None),
            ('6500', 'Office Supplies Expense', 'expense', None),
            ('6600', 'Bad Debt Expense', 'expense', None),
        ]
        
        for code, name, acc_type, parent in accounts:
            self.create_account(code, name, acc_type, parent)
    
    def create_account(self, account_code, account_name, account_type, parent_account_id=None):
        """Create a new account in the chart of accounts"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO accounts (account_code, account_name, account_type, parent_account_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (account_code, account_name, account_type, parent_account_id, datetime.now().isoformat()))
            self.db.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating account: {e}")
            return None
    
    def create_journal_entry(self, journal_type, reference_no, description, entries, date=None):
        """
        Create a journal entry with multiple debit/credit lines
        
        Args:
            journal_type: Type of journal ('sales', 'cash_receipt', 'cash_disbursement', 'general', 'ap')
            reference_no: Reference number for the transaction
            description: Description of the transaction
            entries: List of dictionaries with 'account', 'debit', 'credit', 'description'
            date: Transaction date (defaults to now)
        
        Returns:
            journal_entry_id if successful, None otherwise
        """
        if date is None:
            date = datetime.now().isoformat()
        
        # Validate entries are balanced
        total_debits = sum(entry.get('debit', 0) for entry in entries)
        total_credits = sum(entry.get('credit', 0) for entry in entries)
        
        if abs(total_debits - total_credits) > 0.01:  # Allow for small rounding differences
            raise ValueError(f"Journal entry not balanced. Debits: {total_debits}, Credits: {total_credits}")
        
        try:
            cursor = self.db.conn.cursor()
            
            # Create journal entry header
            cursor.execute("""
                INSERT INTO journal_entries (journal_type, reference_no, description, date, total_debit, total_credit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (journal_type, reference_no, description, date, total_debits, total_credits, datetime.now().isoformat()))
            
            journal_entry_id = cursor.lastrowid
            
            # Create journal entry lines
            for entry in entries:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_name, debit_amount, credit_amount, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    journal_entry_id,
                    entry['account'],
                    entry.get('debit', 0),
                    entry.get('credit', 0),
                    entry.get('description', '')
                ))
                
                # Update account balances
                self.update_account_balance(entry['account'], entry.get('debit', 0), entry.get('credit', 0))
            
            self.db.conn.commit()
            print(f"Journal Entry #{journal_entry_id} created: {description}")
            self.print_journal_entry(journal_entry_id)
            return journal_entry_id
            
        except Exception as e:
            self.db.conn.rollback()
            print(f"Error creating journal entry: {e}")
            return None
    
    def update_account_balance(self, account_name, debit_amount, credit_amount):
        """Update account balance based on account type and transaction amounts"""
        try:
            cursor = self.db.conn.cursor()
            
            # Get account type
            cursor.execute("SELECT account_type FROM accounts WHERE account_name = ?", (account_name,))
            result = cursor.fetchone()
            
            if not result:
                print(f"⚠️ Account '{account_name}' not found in chart of accounts")
                return
            
            account_type = result[0]
            
            # Calculate balance change based on account type
            # Assets and Expenses: Debit increases, Credit decreases
            # Liabilities, Equity, Revenue: Credit increases, Debit decreases
            if account_type in ['asset', 'expense']:
                balance_change = debit_amount - credit_amount
            else:  # liability, equity, revenue
                balance_change = credit_amount - debit_amount
            
            # Update account balance
            cursor.execute("""
                UPDATE accounts 
                SET balance = balance + ? 
                WHERE account_name = ?
            """, (balance_change, account_name))
            
        except Exception as e:
            print(f"Error updating account balance: {e}")
    
    def process_sales_transaction(self, sale_id, sale_items, total_amount, payment_type='cash'):
        """
        Process a sales transaction with FIFO costing
        
        Journal Entries:
        1. Record the sale:
           Dr. Cash/Accounts Receivable    XXX
           Cr. Sales Revenue                   XXX
           
        2. Record cost of goods sold (using FIFO):
           Dr. Cost of Goods Sold         XXX
           Cr. Inventory                       XXX
        """
        reference_no = f"SALE-{sale_id}"
        
        # Calculate total cost of goods sold using FIFO
        total_cogs = 0
        inventory_details = []
        
        for item in sale_items:
            product = self.db.get_product_by_id(item['product_id'])
            if product:
                # Use FIFO costing to get actual cost
                fifo_cost, lots_consumed = self.db.get_fifo_cost(item['product_id'], item['quantity'])
                
                if fifo_cost is not None:
                    # Consume the inventory lots
                    for lot in lots_consumed:
                        self.db.consume_inventory_lot(lot['lot_id'], lot['quantity_consumed'])
                    
                    total_cogs += fifo_cost
                    inventory_details.append(f"{product[1]} (Qty: {item['quantity']})")
                else:
                    # Not enough inventory - this should not happen due to validation in create_sale
                    # but handle gracefully if it does
                    print(f"Critical: Not enough inventory for {product[1]} during accounting (this should not happen)")
                    # Use average cost as fallback but log the issue
                    item_cogs = product[3] * item['quantity']  # cost_price * quantity
                    total_cogs += item_cogs
                    inventory_details.append(f"{product[1]} (Qty: {item['quantity']}) - INSUFFICIENT STOCK")
        
        # Determine cash or credit account
        cash_account = "Cash" if payment_type == 'cash' else "Accounts Receivable"
        
        # Create journal entries
        entries = [
            # Record the sale
            {
                'account': cash_account,
                'debit': total_amount,
                'credit': 0,
                'description': f'Sale of goods - {", ".join(inventory_details)}'
            },
            {
                'account': 'Sales Revenue',
                'debit': 0,
                'credit': total_amount,
                'description': f'Revenue from sale #{sale_id}'
            },
            # Record cost of goods sold
            {
                'account': 'Cost of Goods Sold',
                'debit': total_cogs,
                'credit': 0,
                'description': f'COGS for sale #{sale_id} (FIFO costing)'
            },
            {
                'account': 'Inventory',
                'debit': 0,
                'credit': total_cogs,
                'description': f'Inventory reduction for sale #{sale_id}'
            }
        ]
        
        return self.create_journal_entry(
            journal_type='sales',
            reference_no=reference_no,
            description=f'Sale #{sale_id} - {payment_type.title()} Sale (FIFO)',
            entries=entries
        )
    
    def process_inventory_purchase(self, purchase_id, purchase_items, total_amount, payment_type='cash', is_beginning_inventory=False):
        """
        Process inventory purchase transaction with FIFO costing
        
        Journal Entries:
        For Beginning Inventory:
        Dr. Inventory (Beginning)         XXX
        Cr. Owner's Capital               XXX
        
        For Regular Purchases:
        Dr. Inventory                     XXX
        Cr. Cash/Accounts Payable         XXX
        """
        reference_no = f"PUR-{purchase_id}" if not is_beginning_inventory else f"BEG-{purchase_id}"
        credit_account = "Owner Capital" if is_beginning_inventory else ("Cash" if payment_type == 'cash' else "Accounts Payable")
        journal_type = 'general' if is_beginning_inventory else ('ap' if payment_type == 'credit' else 'cash_disbursement')
        description = f'Beginning Inventory #{purchase_id}' if is_beginning_inventory else f'Inventory Purchase #{purchase_id}'
        
        entries = [
            {
                'account': 'Inventory',
                'debit': total_amount,
                'credit': 0,
                'description': description
            },
            {
                'account': credit_account,
                'debit': 0,
                'credit': total_amount,
                'description': f'Payment for {description.lower()}'
            }
        ]
        
        return self.create_journal_entry(
            journal_type=journal_type,
            reference_no=reference_no,
            description=description,
            entries=entries
        )
    
    def process_expense_transaction(self, expense_type, amount, description, payment_type='cash'):
        """
        Process expense transactions
        
        Journal Entries:
        Dr. [Expense Account]           XXX
        Cr. Cash/Accounts Payable          XXX
        """
        reference_no = f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        credit_account = "Cash" if payment_type == 'cash' else "Accounts Payable"
        
        # Map expense types to accounts
        expense_accounts = {
            'rent': 'Rent Expense',
            'utilities': 'Utilities Expense',
            'office_supplies': 'Office Supplies Expense',
            'advertising': 'Advertising Expense',
            'general': 'Operating Expenses'
        }
        
        expense_account = expense_accounts.get(expense_type, 'Operating Expenses')
        
        entries = [
            {
                'account': expense_account,
                'debit': amount,
                'credit': 0,
                'description': description
            },
            {
                'account': credit_account,
                'debit': 0,
                'credit': amount,
                'description': f'Payment for {description}'
            }
        ]
        
        return self.create_journal_entry(
            journal_type='cash_disbursement',
            reference_no=reference_no,
            description=description,
            entries=entries
        )
    
    def process_customer_payment(self, customer_id, amount, reference_no=None, description=""):
        """
        Process customer payment (cash inflow from customer)
        
        Journal Entries:
        Dr. Cash                     XXX
        Cr. Accounts Receivable         XXX
        """
        reference_no = reference_no or f"CUST-PMT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        entries = [
            {
                'account': 'Cash',
                'debit': amount,
                'credit': 0,
                'description': f'Customer payment - {description}'
            },
            {
                'account': 'Accounts Receivable',
                'debit': 0,
                'credit': amount,
                'description': f'Payment received from customer'
            }
        ]
        
        return self.create_journal_entry(
            journal_type='cash_receipt',
            reference_no=reference_no,
            description=f'Customer Payment - {description}',
            entries=entries
        )
    
    def process_supplier_payment(self, supplier_id, amount, reference_no=None, description=""):
        """
        Process supplier payment (cash outflow to supplier)
        
        Journal Entries:
        Dr. Accounts Payable          XXX
        Cr. Cash                         XXX
        """
        reference_no = reference_no or f"SUPP-PMT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        entries = [
            {
                'account': 'Accounts Payable',
                'debit': amount,
                'credit': 0,
                'description': f'Supplier payment - {description}'
            },
            {
                'account': 'Cash',
                'debit': 0,
                'credit': amount,
                'description': f'Payment made to supplier'
            }
        ]
        
        return self.create_journal_entry(
            journal_type='cash_disbursement',
            reference_no=reference_no,
            description=f'Supplier Payment - {description}',
            entries=entries
        )
    
    def process_inventory_adjustment(self, product_id, adjustment_type, quantity, reason):
        """
        Process inventory adjustments
        
        Journal Entries (for shrinkage/loss):
        Dr. Operating Expenses          XXX
        Cr. Inventory                       XXX
        
        For additions (found inventory):
        Dr. Inventory                   XXX
        Cr. Other Income                    XXX
        """
        product = self.db.get_product_by_id(product_id)
        if not product:
            return None
        
        adjustment_value = product[3] * quantity  # cost_price * quantity
        reference_no = f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if adjustment_type == 'decrease':
            # Inventory shrinkage/loss
            entries = [
                {
                    'account': 'Operating Expenses',
                    'debit': adjustment_value,
                    'credit': 0,
                    'description': f'Inventory adjustment - {reason}'
                },
                {
                    'account': 'Inventory',
                    'debit': 0,
                    'credit': adjustment_value,
                    'description': f'Inventory reduction - {product[1]}'
                }
            ]
        else:
            # Inventory found/addition
            entries = [
                {
                    'account': 'Inventory',
                    'debit': adjustment_value,
                    'credit': 0,
                    'description': f'Inventory addition - {product[1]}'
                },
                {
                    'account': 'Other Income',
                    'debit': 0,
                    'credit': adjustment_value,
                    'description': f'Inventory found - {reason}'
                }
            ]
        
        return self.create_journal_entry(
            journal_type='general',
            reference_no=reference_no,
            description=f'Inventory Adjustment - {product[1]} ({adjustment_type} {quantity})',
            entries=entries
        )
    
    def print_journal_entry(self, journal_entry_id):
        """Print journal entry in grouped transaction format"""
        try:
            cursor = self.db.conn.cursor()
            
            # Get journal entry header
            cursor.execute("""
                SELECT journal_type, reference_no, description, date, total_debit, total_credit
                FROM journal_entries WHERE id = ?
            """, (journal_entry_id,))
            
            header = cursor.fetchone()
            if not header:
                return
            
            print(f"\nJOURNAL ENTRY #{journal_entry_id}")
            print(f"Type: {header[0]} | Ref: {header[1]} | Date: {header[3]}")
            print(f"Description: {header[2]}")
            print("="*60)
            
            # Get journal entry lines
            cursor.execute("""
                SELECT account_name, debit_amount, credit_amount, description
                FROM journal_entry_lines WHERE journal_entry_id = ?
                ORDER BY debit_amount DESC, credit_amount DESC
            """, (journal_entry_id,))
            
            lines = cursor.fetchall()
            
            # Group transactions logically for sales entries
            if header[0] == 'sales':
                # Group 1: Revenue transaction (Cash/AR and Sales Revenue)
                revenue_debits = []
                revenue_credits = []
                
                # Group 2: COGS transaction (COGS and Inventory)
                cogs_debits = []
                cogs_credits = []
                
                for line in lines:
                    account, debit, credit, desc = line
                    
                    if account in ['Cash', 'Accounts Receivable'] or 'Revenue' in account:
                        if debit > 0:
                            revenue_debits.append((account, debit))
                        if credit > 0:
                            revenue_credits.append((account, credit))
                    else:  # COGS and Inventory
                        if debit > 0:
                            cogs_debits.append((account, debit))
                        if credit > 0:
                            cogs_credits.append((account, credit))
                
                # Print revenue transaction
                for account, amount in revenue_debits:
                    print(f"DR  {account:<25} ₱{amount:>10,.2f}")
                for account, amount in revenue_credits:
                    print(f"    CR  {account:<21} ₱{amount:>10,.2f}")
                
                if cogs_debits or cogs_credits:
                    print()  # Blank line separator
                    
                    # Print COGS transaction
                    for account, amount in cogs_debits:
                        print(f"DR  {account:<25} ₱{amount:>10,.2f}")
                    for account, amount in cogs_credits:
                        print(f"    CR  {account:<21} ₱{amount:>10,.2f}")
            
            else:
                # For non-sales entries, use the original format
                for line in lines:
                    account, debit, credit, desc = line
                    if debit > 0:
                        print(f"DR  {account:<25} ₱{debit:>10,.2f}")
                    if credit > 0:
                        print(f"    CR  {account:<21} ₱{credit:>10,.2f}")
            
            print("="*60)
            print(f"Total Debits: ₱{header[4]:,.2f} | Total Credits: ₱{header[5]:,.2f}")
            print()
            
        except Exception as e:
            print(f"Error printing journal entry: {e}")
    
    def get_account_balance(self, account_name):
        """Get current balance of an account"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT balance FROM accounts WHERE account_name = ?", (account_name,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    def get_trial_balance(self):
        """Generate trial balance report"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT account_code, account_name, account_type, balance
                FROM accounts
                WHERE balance != 0 OR account_type IN ('asset', 'liability', 'equity')
                ORDER BY account_code
            """)
            
            return cursor.fetchall()
        except Exception as e:
            print(f"Error generating trial balance: {e}")
            return []
    
    def get_account_ledger(self, account_name):
        """Get detailed ledger entries for a specific account with running balance"""
        try:
            cursor = self.db.conn.cursor()
            
            # Get all journal entry lines for this account with running totals
            cursor.execute("""
            SELECT 
                je.created_at,
                je.journal_type,
                je.reference_no,
                je.description,
                jel.debit_amount,
                jel.credit_amount,
                je.id as journal_entry_id
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            WHERE jel.account_name = ?
            ORDER BY je.created_at, je.id
            """, (account_name,))
            
            entries = cursor.fetchall()
            
            # Calculate running balance for each entry
            ledger_entries = []
            running_balance = 0
            
            for entry in entries:
                created_at, journal_type, reference_no, description, debit, credit, journal_id = entry
                
                # Calculate running balance (debit increases, credit decreases for asset/expense accounts)
                running_balance += (debit or 0) - (credit or 0)
                
                ledger_entries.append({
                    'date': created_at,
                    'journal_type': journal_type,
                    'reference': reference_no,
                    'description': description,
                    'debit': debit or 0,
                    'credit': credit or 0,
                    'balance': running_balance,
                    'journal_id': journal_id
                })
            
            return ledger_entries
            
        except Exception as e:
            print(f"Error getting account ledger: {e}")
            return []
    
    def get_account_summary(self, account_name):
        """Get summary information for an account including total debits and credits"""
        try:
            cursor = self.db.conn.cursor()
            
            # Get account details
            cursor.execute("""
            SELECT account_name, account_type, balance 
            FROM accounts 
            WHERE account_name = ?
            """, (account_name,))
            
            account_info = cursor.fetchone()
            if not account_info:
                return None
            
            # Get total debits and credits
            cursor.execute("""
            SELECT 
                COALESCE(SUM(debit_amount), 0) as total_debits,
                COALESCE(SUM(credit_amount), 0) as total_credits,
                COUNT(*) as transaction_count
            FROM journal_entry_lines 
            WHERE account_name = ?
            """, (account_name,))
            
            totals = cursor.fetchone()
            
            return {
                'account_name': account_info[0],
                'account_type': account_info[1],
                'current_balance': account_info[2],
                'total_debits': totals[0],
                'total_credits': totals[1],
                'transaction_count': totals[2]
            }
            
        except Exception as e:
            print(f"Error getting account summary: {e}")
            return None
    
    def get_total_journal_entries(self):
        """Get total count of journal entries"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM journal_entries")
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting journal entries count: {e}")
            return 0
    
    def validate_trial_balance(self):
        """Validate that total debits equal total credits in all journal entries"""
        try:
            cursor = self.db.conn.cursor()
            
            # Sum all debits and credits from journal entry lines
            cursor.execute("""
            SELECT 
                COALESCE(SUM(debit_amount), 0) as total_debits,
                COALESCE(SUM(credit_amount), 0) as total_credits
            FROM journal_entry_lines
            """)
            
            result = cursor.fetchone()
            total_debits = result[0]
            total_credits = result[1]
            
            # Check if debits equal credits (within a small tolerance for floating point)
            difference = abs(total_debits - total_credits)
            is_balanced = difference < 0.01  # Allow 1 cent difference for rounding
            
            print(f"Trial Balance Check - Debits: ₱{total_debits:,.2f}, Credits: ₱{total_credits:,.2f}, Balanced: {is_balanced}")
            
            return is_balanced
            
        except Exception as e:
            print(f"Error validating trial balance: {e}")
            return False
        
    def process_bad_debt_write_off(self, customer_id, sale_id, amount, description=""):
        """
        Process bad debt write-off for uncollectible accounts receivable
        
        Journal Entry:
        Dr. Bad Debt Expense          XXX
        Cr. Accounts Receivable          XXX
        
        Args:
            customer_id: ID of the customer
            sale_id: ID of the original sale
            amount: Amount to write off
            description: Optional description
            
        Returns:
            journal_entry_id if successful, None otherwise
        """
        try:
            reference_no = f"BD-{sale_id}"
            
            # Create journal entry for bad debt write-off
            entries = [
                {
                    'account': 'Bad Debt Expense',
                    'debit': amount,
                    'credit': 0,
                    'description': f'Bad debt write-off for sale #{sale_id} - {description}'
                },
                {
                    'account': 'Accounts Receivable',
                    'debit': 0,
                    'credit': amount,
                    'description': f'Accounts receivable reduction for bad debt sale #{sale_id}'
                }
            ]
            
            journal_entry_id = self.create_journal_entry(
                journal_type='general',
                reference_no=reference_no,
                description=f'Bad debt write-off for customer #{customer_id}, sale #{sale_id}',
                entries=entries
            )
            
            if journal_entry_id:
                print(f"Bad debt write-off recorded: ₱{amount:,.2f} for sale #{sale_id}")
                return journal_entry_id
            else:
                print(f"Failed to record bad debt write-off for sale #{sale_id}")
                return None
                
        except Exception as e:
            print(f"Error processing bad debt write-off: {e}")
            return None

    def calculate_total_revenue(self):
        """Calculate total revenue from all sales"""
        return self.db.get_total_sales()

    def calculate_total_cogs(self):
        """Calculate total cost of goods sold"""
        return self.db.get_cost_of_goods_sold()

    def calculate_gross_profit(self):
        """Calculate gross profit (revenue - COGS)"""
        return self.db.get_gross_profit()


class Tab(MDFloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    pass
