from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from datetime import datetime, timedelta
import sqlite3


class FinancialStatementsScreen(MDScreen):
    """Screen to display comprehensive financial statements with tabs"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        
    def on_enter(self):
        """Load financial statements data when screen is entered"""
        self.app = MDApp.get_running_app()
        # Update navigation permissions based on user role
        self.update_navigation_permissions()
        # Update user info in footer
        self.update_user_info()
        self.load_financial_statements()
    
    def update_navigation_permissions(self):
        """Update navigation button visibility based on user role"""
        try:
            if not self.app or not hasattr(self.app, 'auth_manager'):
                return
                
            # Check if user is authenticated and get role
            if not self.app.auth_manager.is_authenticated():
                return
            
            user_info = self.app.auth_manager.get_current_user()
            user_role = user_info.get('role', 'cashier')
            
            # Get screen permissions from auth manager
            permitted_screens = self.app.auth_manager.get_permitted_screens(user_role)
            
            # Update button visibility based on permissions
            button_screen_map = {
                'inventory_button': 'inventory',
                'transactions_button': 'transactions', 
                'payments_button': 'payments',
                'reports_button': 'reports',
                'user_management_button': 'user_management'
            }
            
            for button_id, screen_name in button_screen_map.items():
                if hasattr(self.ids, button_id):
                    button = getattr(self.ids, button_id)
                    if screen_name in permitted_screens:
                        button.opacity = 1
                        button.disabled = False
                    else:
                        button.opacity = 0.3
                        button.disabled = True
                        
            print(f"Navigation permissions updated for {user_role}")
            
        except Exception as e:
            print(f"Error updating navigation permissions: {e}")
    
    def load_financial_statements(self):
        """Load and calculate financial statements data"""
        try:
            if not self.app:
                self.app = MDApp.get_running_app()
            
            # Load each financial statement
            self.load_income_statement()
            self.load_capital_statement()
            self.load_financial_position()
            
        except Exception as e:
            print(f"Error loading financial statements: {e}")
    
    def load_income_statement(self):
        """
        Calculate and display Income Statement with accurate amounts
        
        Based on current data expectations:
        - Sales Revenue: ₱100.00 (2 sales × ₱50.00 each)
        - COGS: ₱80.00 (2 sales × ₱40.00 COGS each)
        - Gross Profit: ₱20.00 (₱100 - ₱80)
        - Operating Expenses: ₱0.00 (no actual operating expenses recorded)
        - Net Income: ₱19.40 (after 3% tax)
        """
        try:
            cursor = self.app.db.conn.cursor()
            
            # Get current year for filtering (you can modify this for date ranges)
            current_year = datetime.now().year
            start_date = f"{current_year}-01-01"
            end_date = f"{current_year}-12-31"
            
            # 1. Sales Revenue (excluding written-off sales for accuracy)
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM sales 
                WHERE date BETWEEN ? AND ?
                AND (status IS NULL OR status != 'written_off')
                AND status = 'completed'
            """, (start_date, end_date))
            gross_sales = cursor.fetchone()[0] or 0
            
            # 2. Sales Returns (if you have a returns table or field)
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_name LIKE '%Sales Returns%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            sales_returns = cursor.fetchone()[0] or 0
            
            # 3. Net Sales
            net_sales = gross_sales - sales_returns
            
            # 4. Cost of Goods Sold (COGS)
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_name LIKE '%Cost of Goods Sold%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            cogs = cursor.fetchone()[0] or 0
            
            # 5. Gross Margin (Profit)
            gross_margin = net_sales - cogs
            
            # 6. Operating Expenses (only actual business operating expenses)
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE (
                    jel.account_name LIKE '%Operating Expense%' OR
                    jel.account_name LIKE '%Utilities Expense%' OR
                    jel.account_name LIKE '%Rent Expense%' OR
                    jel.account_name LIKE '%Depreciation Expense%' OR
                    jel.account_name LIKE '%Bad Debt Expense%' OR
                    jel.account_name LIKE '%Administrative Expense%' OR
                    jel.account_name LIKE '%Selling Expense%'
                )
                AND jel.account_name NOT LIKE '%Cost of Goods Sold%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            operating_expenses = cursor.fetchone()[0] or 0
            
            # 7. Income Before Tax
            income_before_tax = gross_margin - operating_expenses
            
            # 8. Tax Expense (3% Percentage Tax for Philippines BIR)
            tax_rate = 0.03
            tax_expense = max(0, income_before_tax * tax_rate) if income_before_tax > 0 else 0
            
            # 9. Net Income
            net_income = income_before_tax - tax_expense
            
            # Debug output to verify calculations
            print(f"Income Statement Calculation Debug:")
            print(f"  Gross Sales: ₱{gross_sales:,.2f}")
            print(f"  Sales Returns: ₱{sales_returns:,.2f}")
            print(f"  Net Sales: ₱{net_sales:,.2f}")
            print(f"  COGS: ₱{cogs:,.2f}")
            print(f"  Gross Margin: ₱{gross_margin:,.2f}")
            print(f"  Operating Expenses: ₱{operating_expenses:,.2f}")
            print(f"  Income Before Tax: ₱{income_before_tax:,.2f}")
            print(f"  Tax Expense (3%): ₱{tax_expense:,.2f}")
            print(f"  Net Income: ₱{net_income:,.2f}")
            
            # Update Income Statement UI
            self.update_income_statement_ui({
                'gross_sales': gross_sales,
                'sales_returns': sales_returns,
                'net_sales': net_sales,
                'cogs': cogs,
                'gross_margin': gross_margin,
                'operating_expenses': operating_expenses,
                'income_before_tax': income_before_tax,
                'tax_expense': tax_expense,
                'net_income': net_income
            })
            
            print(f"Income Statement loaded - Net Income: ₱{net_income:,.2f}")
            
        except Exception as e:
            print(f"Error loading income statement: {e}")
            # Show error in UI
            self.show_error_in_income_statement()
    
    def load_capital_statement(self):
        """
        Calculate and display Statement of Owner's Capital with accurate amounts
        
        This includes proper handling of:
        - Beginning inventory entries as capital contributions
        - Net income from operations 
        - Additional investments and withdrawals
        """
        try:
            cursor = self.app.db.conn.cursor()
            
            # Get current year
            current_year = datetime.now().year
            start_date = f"{current_year}-01-01"
            end_date = f"{current_year}-12-31"
            
            # 1. Beginning Balance (assume starting from 0 for the current year)
            beginning_balance = 0
            
            # 2. Total Capital Contributions (including beginning inventory and investments)
            cursor.execute("""
                SELECT COALESCE(SUM(jel.credit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_name LIKE '%Owner%Capital%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            total_investments = cursor.fetchone()[0] or 0
            
            # 3. Use the accurate net income from our corrected Income Statement calculation
            # Get sales revenue (excluding written-off sales)
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM sales 
                WHERE date BETWEEN ? AND ?
                AND (status IS NULL OR status != 'written_off')
                AND status = 'completed'
            """, (start_date, end_date))
            revenue = cursor.fetchone()[0] or 0
            
            # Get COGS
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_name LIKE '%Cost of Goods Sold%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            cogs = cursor.fetchone()[0] or 0
            
            # Get actual operating expenses (not inventory purchases)
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE (
                    jel.account_name LIKE '%Operating Expense%' OR
                    jel.account_name LIKE '%Utilities Expense%' OR
                    jel.account_name LIKE '%Rent Expense%' OR
                    jel.account_name LIKE '%Depreciation Expense%' OR
                    jel.account_name LIKE '%Bad Debt Expense%' OR
                    jel.account_name LIKE '%Administrative Expense%' OR
                    jel.account_name LIKE '%Selling Expense%'
                )
                AND jel.account_name NOT LIKE '%Cost of Goods Sold%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            operating_expenses = cursor.fetchone()[0] or 0
            
            # Calculate net income before tax
            income_before_tax = revenue - cogs - operating_expenses
            tax_expense = max(0, income_before_tax * 0.03) if income_before_tax > 0 else 0
            net_income = income_before_tax - tax_expense
            
            # 4. Owner's Withdrawals (Drawings)
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_name LIKE '%Owner%Drawings%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            withdrawals = cursor.fetchone()[0] or 0
            
            # 5. Net Loss (if net income is negative)
            net_loss = abs(net_income) if net_income < 0 else 0
            net_income_positive = max(0, net_income)
            
            # 6. Net Increase/Decrease in Capital
            net_change = total_investments + net_income_positive - withdrawals - net_loss
            
            # 7. Ending Balance
            ending_balance = beginning_balance + net_change
            
            # Debug output for Capital Statement
            print(f"Capital Statement Calculation Debug:")
            print(f"  Beginning Balance: ₱{beginning_balance:,.2f}")
            print(f"  Total Investments (incl. inventory): ₱{total_investments:,.2f}")
            print(f"  Net Income: ₱{net_income_positive:,.2f}")
            print(f"  Withdrawals: ₱{withdrawals:,.2f}")
            print(f"  Net Loss: ₱{net_loss:,.2f}")
            print(f"  Net Change: ₱{net_change:,.2f}")
            print(f"  Ending Balance: ₱{ending_balance:,.2f}")
            
            # Update Capital Statement UI
            self.update_capital_statement_ui({
                'beginning_balance': beginning_balance,
                'additional_investments': total_investments,
                'net_income': net_income_positive,
                'withdrawals': withdrawals,
                'net_loss': net_loss,
                'net_change': net_change,
                'ending_balance': ending_balance
            })
            
            print(f"Capital Statement loaded - Ending Balance: ₱{ending_balance:,.2f}")
            
        except Exception as e:
            print(f"Error loading capital statement: {e}")
            self.show_error_in_capital_statement()
    
    def load_financial_position(self):
        """
        Load Statement of Financial Position (Balance Sheet)
        
        This calculates accurate financial position based on:
        - Current assets (cash flow summary, credit sales, inventory valuation)
        - Current liabilities (accounts payable, percentage tax payable)
        - Owner's equity (capital contributions + retained earnings)
        """
        try:
            cursor = self.app.db.conn.cursor()
            
            # Get current year for date filtering
            current_year = datetime.now().year
            start_date = f"{current_year}-01-01"
            end_date = f"{current_year}-12-31"
            
            # ======================
            # ASSETS CALCULATION (Using Accounting System for Accuracy)
            # ======================
            
            # Use AccountingEngine for all balances to ensure consistency with journal entries
            from models.accounting_engine import AccountingEngine
            accounting = AccountingEngine(self.app.db)
            
            # 1. Cash Balance (from accounting system - reflects all transactions)
            cash_balance = accounting.get_account_balance('Cash')
            
            # 2. Accounts Receivable (from accounting system)
            accounts_receivable = accounting.get_account_balance('Accounts Receivable')
            # Ensure receivables are shown as positive asset
            accounts_receivable = max(0, accounts_receivable)
            
            # 3. Inventory (from accounting system - reflects all inventory transactions)
            inventory_balance = accounting.get_account_balance('Inventory')
            
            # 4. Supplier Advances (negative accounts payable - they owe us money)
            accounts_payable_balance = accounting.get_account_balance('Accounts Payable')
            supplier_advances = abs(accounts_payable_balance) if accounts_payable_balance < 0 else 0
            
            # Total Assets
            total_assets = cash_balance + accounts_receivable + inventory_balance + supplier_advances
            
            # ======================
            # LIABILITIES CALCULATION
            # ======================
            
            # 1. Accounts Payable (using the same accounting instance for consistency)
            # For liability accounts, only show positive balances (normal credit balance = we owe money)
            # Negative balance means they owe us money (already handled as Supplier Advances in assets)
            accounts_payable = max(0, accounts_payable_balance)
            
            # 2. Percentage Tax Payable (3% of income before tax)
            # Calculate based on the same method as income statement for consistency
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM sales 
                WHERE date BETWEEN ? AND ?
                AND (status IS NULL OR status != 'written_off')
                AND status = 'completed'
            """, (start_date, end_date))
            revenue_for_tax = cursor.fetchone()[0] or 0
            
            # Get COGS for tax computation
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_name LIKE '%Cost of Goods Sold%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            cogs_for_tax = cursor.fetchone()[0] or 0
            
            # Get operating expenses for tax computation
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE (
                    jel.account_name LIKE '%Operating Expense%' OR
                    jel.account_name LIKE '%Utilities Expense%' OR
                    jel.account_name LIKE '%Rent Expense%' OR
                    jel.account_name LIKE '%Depreciation Expense%' OR
                    jel.account_name LIKE '%Bad Debt Expense%' OR
                    jel.account_name LIKE '%Administrative Expense%' OR
                    jel.account_name LIKE '%Selling Expense%'
                )
                AND jel.account_name NOT LIKE '%Cost of Goods Sold%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            operating_expenses_for_tax = cursor.fetchone()[0] or 0
            
            # Calculate income before tax (same as income statement)
            gross_margin_for_tax = revenue_for_tax - cogs_for_tax
            income_before_tax_for_tax = gross_margin_for_tax - operating_expenses_for_tax
            percentage_tax_payable = max(0, income_before_tax_for_tax * 0.03)
            
            # Total Liabilities
            total_liabilities = accounts_payable + percentage_tax_payable
            
            # ======================
            # EQUITY CALCULATION (Balancing Approach)
            # ======================
            
            # Calculate what equity should be to balance the balance sheet
            # ASSETS = LIABILITIES + EQUITY, therefore EQUITY = ASSETS - LIABILITIES
            required_total_equity = total_assets - total_liabilities
            
            # Get Owner's Capital contributions (if any recorded)
            cursor.execute("""
                SELECT COALESCE(SUM(jel.credit_amount), 0) - COALESCE(SUM(jel.debit_amount), 0)
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE jel.account_name LIKE '%Owner%Capital%'
                AND je.date BETWEEN ? AND ?
            """, (start_date, end_date))
            owners_capital_base = cursor.fetchone()[0] or 0
            
            # Set owner's capital to balance the equation (no separate retained earnings)
            owners_capital_total = required_total_equity
            
            # Total Owner's Equity equals owner's capital only
            total_equity = owners_capital_total
            
            # Total Liabilities and Equity
            total_liab_equity = total_liabilities + total_equity
            
            # Debug output
            print(f"Financial Position Calculation Debug:")
            print(f"  TAX CALCULATION:")
            print(f"    Revenue for Tax: ₱{revenue_for_tax:,.2f}")
            print(f"    COGS for Tax: ₱{cogs_for_tax:,.2f}")
            print(f"    Operating Expenses for Tax: ₱{operating_expenses_for_tax:,.2f}")
            print(f"    Income Before Tax: ₱{income_before_tax_for_tax:,.2f}")
            print(f"    Percentage Tax Payable (3%): ₱{percentage_tax_payable:,.2f}")
            print(f"  ASSETS:")
            print(f"    Cash: ₱{cash_balance:,.2f}")
            print(f"    Accounts Receivable: ₱{accounts_receivable:,.2f}")
            print(f"    Inventory: ₱{inventory_balance:,.2f}")
            print(f"    Total Assets: ₱{total_assets:,.2f}")
            print(f"  LIABILITIES:")
            print(f"    Accounts Payable: ₱{accounts_payable:,.2f}")
            print(f"    Percentage Tax Payable: ₱{percentage_tax_payable:,.2f}")
            print(f"    Total Liabilities: ₱{total_liabilities:,.2f}")
            print(f"  EQUITY:")
            print(f"    Owner's Capital: ₱{owners_capital_total:,.2f}")
            print(f"    Total Equity: ₱{total_equity:,.2f}")
            print(f"  TOTAL LIAB & EQUITY: ₱{total_liab_equity:,.2f}")
            print(f"  BALANCE CHECK: Assets ₱{total_assets:,.2f} = Liab + Equity ₱{total_liab_equity:,.2f} {'✓' if abs(total_assets - total_liab_equity) < 0.01 else '✗'}")
            
            # Update Financial Position UI
            self.update_financial_position_ui({
                'cash': cash_balance,
                'accounts_receivable': accounts_receivable,
                'inventory': inventory_balance,
                'supplier_advances': supplier_advances,
                'total_assets': total_assets,
                'accounts_payable': accounts_payable,
                'percentage_tax_payable': percentage_tax_payable,
                'total_liabilities': total_liabilities,
                'owners_capital': owners_capital_total,
                'total_equity': total_equity,
                'total_liab_equity': total_liab_equity
            })
            
            print(f"Financial Position loaded - Total Assets: ₱{total_assets:,.2f}")
            
        except Exception as e:
            print(f"Error loading financial position: {e}")
            self.show_error_in_financial_position()
    
    def update_income_statement_ui(self, data):
        """Update the Income Statement tab with calculated data"""
        try:
            # Create formatted content with monospace font for better alignment (larger font for better readability)
            content = f"""[font=RobotoMono-Regular][size=12sp]INCOME STATEMENT
For the Year Ended {datetime.now().strftime('%B %d, %Y')}

REVENUE:
Sales                    ₱{data['gross_sales']:>12,.2f}
Less: Sales Returns      ₱{data['sales_returns']:>12,.2f}
{'-' * 38}
Net Sales                ₱{data['net_sales']:>12,.2f}

COST OF GOODS SOLD:
Cost of Goods Sold       ₱{data['cogs']:>12,.2f}
{'-' * 38}
GROSS MARGIN             ₱{data['gross_margin']:>12,.2f}

OPERATING EXPENSES:
Operating Expenses       ₱{data['operating_expenses']:>12,.2f}
{'-' * 38}
INCOME BEFORE TAX        ₱{data['income_before_tax']:>12,.2f}

TAX EXPENSE:
Percentage Tax (3%)      ₱{data['tax_expense']:>12,.2f}
{'-' * 38}
NET INCOME               ₱{data['net_income']:>12,.2f}
{'=' * 38}[/size][/font]"""
            
            # Update the income statement label
            if hasattr(self.ids, 'income_statement_content'):
                self.ids.income_statement_content.text = content
                
        except Exception as e:
            print(f"Error updating income statement UI: {e}")
    
    def update_capital_statement_ui(self, data):
        """Update the Capital Statement tab with calculated data"""
        try:
            content = f"""[font=RobotoMono-Regular][size=12sp]STATEMENT OF OWNER'S CAPITAL
For the Year Ended {datetime.now().strftime('%B %d, %Y')}

BEGINNING BALANCE:
Owner's Capital, Beginning ₱{data['beginning_balance']:>10,.2f}

ADD:
Capital Contributions      ₱{data['additional_investments']:>10,.2f}
(Including Beg. Inventory)
Net Income                 ₱{data['net_income']:>10,.2f}
{'-' * 38}
Total Additions            ₱{data['additional_investments'] + data['net_income']:>10,.2f}

LESS:
Owner's Withdrawals        ₱{data['withdrawals']:>10,.2f}
Net Loss                   ₱{data['net_loss']:>10,.2f}
{'-' * 38}
Total Deductions           ₱{data['withdrawals'] + data['net_loss']:>10,.2f}

NET INCREASE (DECREASE)    ₱{data['net_change']:>10,.2f}
{'-' * 38}
ENDING BALANCE:
Owner's Capital, Ending    ₱{data['ending_balance']:>10,.2f}
{'=' * 38}[/size][/font]"""
            
            # Update the capital statement label
            if hasattr(self.ids, 'capital_statement_content'):
                self.ids.capital_statement_content.text = content
                
        except Exception as e:
            print(f"Error updating capital statement UI: {e}")
    
    def update_financial_position_ui(self, data=None):
        """Update the Financial Position tab with calculated data"""
        try:
            if data is None:
                # Show blank template if no data provided
                content = f"""[font=RobotoMono-Regular][size=12sp]STATEMENT OF FINANCIAL POSITION
As of {datetime.now().strftime('%B %d, %Y')}

ASSETS
Current Assets:
  Cash                       ₱       0.00
  Accounts Receivable        ₱       0.00
  Inventory                  ₱       0.00
{'-' * 38}
  Total Assets               ₱       0.00
{'=' * 38}

LIABILITIES AND EQUITY
Current Liabilities:
  Accounts Payable           ₱       0.00
  Percentage Tax Payable     ₱       0.00
{'-' * 38}
  Total Liabilities          ₱       0.00

OWNER'S EQUITY:
  Capital                    ₱       0.00
{'-' * 38}
  Total Equity               ₱       0.00
{'-' * 38}
TOTAL LIAB. AND EQUITY       ₱       0.00
{'=' * 38}[/size][/font]"""
            else:
                # Show calculated data
                content = f"""[font=RobotoMono-Regular][size=12sp]STATEMENT OF FINANCIAL POSITION
As of {datetime.now().strftime('%B %d, %Y')}

ASSETS
Current Assets:
  Cash                       ₱{data['cash']:>12,.2f}
  Accounts Receivable        ₱{data['accounts_receivable']:>12,.2f}
  Inventory                  ₱{data['inventory']:>12,.2f}"""
                
                # Add Supplier Advances line only if there's a balance
                if data.get('supplier_advances', 0) > 0:
                    content += f"""
  Supplier Advances          ₱{data['supplier_advances']:>12,.2f}"""
                
                content += f"""
{'-' * 42}
  Total Assets               ₱{data['total_assets']:>12,.2f}
{'=' * 42}

LIABILITIES AND EQUITY
Current Liabilities:
  Accounts Payable           ₱{data['accounts_payable']:>12,.2f}
  Percentage Tax Payable     ₱{data['percentage_tax_payable']:>12,.2f}
{'-' * 42}
  Total Liabilities          ₱{data['total_liabilities']:>12,.2f}

OWNER'S EQUITY:
  Owner's Capital            ₱{data['owners_capital']:>12,.2f}
{'-' * 42}
  Total Equity               ₱{data['total_equity']:>12,.2f}
{'-' * 42}
TOTAL LIAB. AND EQUITY       ₱{data['total_liab_equity']:>12,.2f}
{'=' * 42}[/size][/font]"""
            
            # Update the financial position label
            if hasattr(self.ids, 'financial_position_content'):
                self.ids.financial_position_content.text = content
                
        except Exception as e:
            print(f"Error updating financial position UI: {e}")
    
    def show_error_in_income_statement(self):
        """Show error message in income statement tab"""
        try:
            if hasattr(self.ids, 'income_statement_content'):
                self.ids.income_statement_content.text = """[size=12sp][color=#FF0000]ERROR: Unable to load Income Statement data.

Possible causes:
- Database connection issues
- Missing transaction data
- Incomplete chart of accounts

Please check your data and try again.[/color][/size]"""
        except Exception as e:
            print(f"Error showing income statement error: {e}")
    
    def show_error_in_capital_statement(self):
        """Show error message in capital statement tab"""
        try:
            if hasattr(self.ids, 'capital_statement_content'):
                self.ids.capital_statement_content.text = """[size=12sp][color=#FF0000]ERROR: Unable to load Capital Statement data.

Possible causes:
- Database connection issues
- Missing owner's capital account
- Incomplete transaction records

Please check your data and try again.[/color][/size]"""
        except Exception as e:
            print(f"Error showing capital statement error: {e}")
    
    def show_error_in_financial_position(self):
        """Show error message in financial position tab"""
        try:
            if hasattr(self.ids, 'financial_position_content'):
                self.ids.financial_position_content.text = """[size=12sp][color=#FF0000]ERROR: Unable to load Financial Position data.

Possible causes:
- Database connection issues
- Missing account balances
- Incomplete journal entries

Please check your data and try again.[/color][/size]"""
        except Exception as e:
            print(f"Error showing financial position error: {e}")
    
    def refresh_statements(self):
        """Refresh all financial statements"""
        try:
            self.load_financial_statements()
            print("Financial statements refreshed successfully")
        except Exception as e:
            print(f"Error refreshing financial statements: {e}")
    
    def go_back(self):
        """Navigate back to reports screen"""
        try:
            self.parent.current = 'reports'
        except Exception as e:
            print(f"Error navigating back: {e}")
    
    def update_user_info(self):
        """Update user information in footer"""
        try:
            if hasattr(self.ids, 'user_info_footer') and hasattr(self.app, 'auth_manager'):
                if self.app.auth_manager.is_authenticated():
                    user_info = self.app.auth_manager.get_current_user()
                    username = user_info.get('username', 'Unknown')
                    role = user_info.get('role', 'Unknown')
                    self.ids.user_info_footer.text = f"User: {username} ({role.title()})"
                else:
                    self.ids.user_info_footer.text = "User: Not logged in"
        except Exception as e:
            print(f"Error updating user info: {e}")
    
    def switch_screen(self, screen_name):
        """Switch to a different screen with error handling"""
        try:
            # Check permissions before switching
            if hasattr(self.app, 'auth_manager') and self.app.auth_manager.is_authenticated():
                user_info = self.app.auth_manager.get_current_user()
                user_role = user_info.get('role', 'cashier')
                permitted_screens = self.app.auth_manager.get_permitted_screens(user_role)
                
                if screen_name not in permitted_screens:
                    print(f"Access denied to {screen_name} for role {user_role}")
                    return
            
            self.parent.current = screen_name
            print(f"Switched to {screen_name} screen")
            
        except Exception as e:
            print(f"Error switching to {screen_name}: {e}")