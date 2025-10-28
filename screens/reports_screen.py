from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen


class ReportsScreen(MDScreen):
    """Screen to display business reports and analytics"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
    
    def on_enter(self):
        """Load reports data when screen is entered"""
        self.app = MDApp.get_running_app()
        self.load_reports_data()
    
    def load_reports_data(self):
        """Load and display financial summary data"""
        try:
            if not self.app:
                self.app = MDApp.get_running_app()
            
            # Calculate financial summary
            cursor = self.app.db.conn.cursor()
            
            # Total Sales
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM sales
            """)
            total_sales = cursor.fetchone()[0] or 0
            
            # Total Expenses (from cash disbursements)
            cursor.execute("""
                SELECT COALESCE(SUM(total_debit), 0) 
                FROM journal_entries 
                WHERE journal_type = 'cash_disbursement'
            """)
            total_expenses = cursor.fetchone()[0] or 0
            
            # Net Profit
            net_profit = total_sales - total_expenses
            
            # Inventory Value
            cursor.execute("""
                SELECT COALESCE(SUM(cost_price * quantity), 0) 
                FROM products 
                WHERE quantity > 0
            """)
            inventory_value = cursor.fetchone()[0] or 0
            
            # Update UI labels
            self.ids.total_sales_label.text = f"₱{total_sales:,.2f}"
            self.ids.total_expenses_label.text = f"₱{total_expenses:,.2f}"
            self.ids.net_profit_label.text = f"₱{net_profit:,.2f}"
            self.ids.inventory_value_label.text = f"₱{inventory_value:,.2f}"
            
            # Load recent activity
            self.load_recent_activity()
            
            print(f"Reports data loaded - Sales: ₱{total_sales:,.2f}, Expenses: ₱{total_expenses:,.2f}, Profit: ₱{net_profit:,.2f}")
            
        except Exception as e:
            print(f"Error loading reports data: {e}")
    
    def load_recent_activity(self):
        """Load recent transactions for activity feed"""
        try:
            from kivymd.uix.list import OneLineListItem
            
            # Clear existing activity
            activity_list = self.ids.recent_activity_list
            activity_list.clear_widgets()
            
            cursor = self.app.db.conn.cursor()
            cursor.execute("""
                SELECT journal_type, reference_no, description, date, total_debit
                FROM journal_entries
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            activities = cursor.fetchall()
            
            for activity in activities:
                journal_type, ref_no, description, date, amount = activity
                
                # Format activity text
                if journal_type == 'sales':
                    activity_text = f"Sale: {description} - ₱{amount:,.0f}"
                elif journal_type == 'cash_disbursement':
                    activity_text = f"Expense: {description} - ₱{amount:,.0f}"
                else:
                    activity_text = f"{journal_type.title()}: {description}"
                
                item = OneLineListItem(
                    text=activity_text,
                    theme_text_color="Secondary"
                )
                activity_list.add_widget(item)
                
        except Exception as e:
            print(f"Error loading recent activity: {e}")
    
    def generate_sales_report(self):
        """Navigate to dedicated sales report screen with charts"""
        try:
            print("Opening Sales Report Screen...")
            self.app.sm.current = 'sales_report'
        except Exception as e:
            print(f"Error opening sales report screen: {e}")
            # Fallback to dialog if screen doesn't exist
            self.show_report_dialog("Error", f"Unable to open sales report: {e}")
    
    def generate_inventory_report(self):
        """Navigate to dedicated inventory report screen with comprehensive analytics"""
        try:
            print("Opening Inventory Report Screen...")
            self.app.sm.current = 'inventory_report'
        except Exception as e:
            print(f"Error opening inventory report screen: {e}")
            # Fallback to legacy dialog if screen doesn't exist
            self.generate_legacy_inventory_report()
    
    def generate_legacy_inventory_report(self):
        """Generate legacy inventory report dialog (fallback)"""
        try:
            print("Generating Legacy Inventory Report...")
            
            cursor = self.app.db.conn.cursor()
            cursor.execute("""
                SELECT 
                    p.name,
                    p.quantity,
                    p.cost_price,
                    p.selling_price,
                    (p.cost_price * p.quantity) as total_value,
                    c.name as category
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.quantity ASC
            """)
            
            inventory_data = cursor.fetchall()
            
            # Show report dialog
            self.show_report_dialog("Inventory Report", self.format_inventory_report(inventory_data))
            
        except Exception as e:
            print(f"Error generating inventory report: {e}")
    
    def generate_financial_report(self):
        """Navigate to comprehensive financial statements screen"""
        try:
            print("Opening Financial Statements Screen...")
            self.app.sm.current = 'financial_statements'
        except Exception as e:
            print(f"Error opening financial statements screen: {e}")
            # Fallback to old behavior if screen doesn't exist
            self.generate_legacy_financial_report()
    
    def generate_legacy_financial_report(self):
        """Generate legacy financial report dialog (fallback)"""
        try:
            print("Generating Legacy Financial Report...")
            
            cursor = self.app.db.conn.cursor()
            
            # Get account balances
            cursor.execute("""
                SELECT 
                    a.account_name,
                    a.account_type,
                    COALESCE(SUM(
                        CASE 
                            WHEN jel.debit_amount > 0 THEN jel.debit_amount
                            ELSE -jel.credit_amount
                        END
                    ), 0) as balance
                FROM accounts a
                LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
                GROUP BY a.id, a.account_name, a.account_type
                ORDER BY a.account_type, a.account_name
            """)
            
            financial_data = cursor.fetchall()
            
            # Show report dialog
            self.show_report_dialog("Financial Report", self.format_financial_report(financial_data))
            
        except Exception as e:
            print(f"Error generating financial report: {e}")
    
    def generate_ledger_report(self):
        """Generate ledger report showing T-account journals for all transactions"""
        try:
            print("Generating Ledger Report...")
            
            cursor = self.app.db.conn.cursor()
            
            # Get all journal entries with their lines
            cursor.execute("""
                SELECT 
                    je.id,
                    je.journal_type,
                    je.reference_no,
                    je.description,
                    je.date,
                    je.total_debit,
                    je.total_credit,
                    jel.account_name,
                    jel.debit_amount,
                    jel.credit_amount,
                    jel.description as line_description
                FROM journal_entries je
                JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
                ORDER BY je.date DESC, je.id DESC, jel.id
            """)
            
            ledger_data = cursor.fetchall()
            
            # Show report dialog
            self.show_report_dialog("Ledger Report", self.format_ledger_report(ledger_data))
            
        except Exception as e:
            print(f"Error generating ledger report: {e}")
            self.show_report_dialog("Ledger Report", "Error generating ledger report. Please try again.")
    
    def format_sales_report(self, sales_data):
        """Format sales data for display"""
        if not sales_data:
            return "No sales data available."
        
        report = "SALES REPORT\n" + "="*50 + "\n\n"
        report += f"{'Date':<12} {'Transactions':<12} {'Total Sales':<15} {'Avg Transaction':<15}\n"
        report += "-" * 60 + "\n"
        
        total_sales = 0
        total_transactions = 0
        
        for row in sales_data:
            date, transactions, sales, avg_trans = row
            total_sales += sales
            total_transactions += transactions
            report += f"{date:<12} {transactions:<12} ₱{sales:>12,.2f} ₱{avg_trans:>12,.2f}\n"
        
        report += "-" * 60 + "\n"
        report += f"TOTALS: {total_transactions} transactions, ₱{total_sales:,.2f} total sales\n"
        
        return report
    
    def format_inventory_report(self, inventory_data):
        """Format inventory data for display"""
        if not inventory_data:
            return "No inventory data available."
        
        report = "INVENTORY REPORT\n" + "="*60 + "\n\n"
        report += f"{'Product':<20} {'Qty':<8} {'Cost':<12} {'Price':<12} {'Value':<12} {'Category':<15}\n"
        report += "-" * 85 + "\n"
        
        total_value = 0
        low_stock_items = 0
        
        for row in inventory_data:
            name, qty, cost, price, value, category = row
            total_value += value
            if qty <= 5:  # Low stock threshold
                low_stock_items += 1
                name = f"⚠️ {name}"
            
            report += f"{name[:19]:<20} {qty:<8} ₱{cost:>9.2f} ₱{price:>9.2f} ₱{value:>9.2f} {category[:14]:<15}\n"
        
        report += "-" * 85 + "\n"
        report += f"Total Inventory Value: ₱{total_value:,.2f}\n"
        report += f"Low Stock Items (≤5): {low_stock_items}\n"
        
        return report
    
    def format_financial_report(self, financial_data):
        """Format financial data for display"""
        if not financial_data:
            return "No financial data available."
        
        report = "FINANCIAL REPORT\n" + "="*50 + "\n\n"
        
        # Group by account type
        assets = []
        liabilities = []
        equity = []
        revenue = []
        expenses = []
        
        for row in financial_data:
            account_name, account_type, balance = row
            if account_type == 'asset':
                assets.append((account_name, balance))
            elif account_type == 'liability':
                liabilities.append((account_name, balance))
            elif account_type == 'equity':
                equity.append((account_name, balance))
            elif account_type == 'revenue':
                revenue.append((account_name, balance))
            elif account_type == 'expense':
                expenses.append((account_name, balance))
        
        # Format each section
        def format_section(title, accounts):
            section = f"{title}\n" + "-" * 30 + "\n"
            total = 0
            for name, balance in accounts:
                section += f"{name:<25} ₱{balance:>12,.2f}\n"
                total += balance
            section += f"{'TOTAL':<25} ₱{total:>12,.2f}\n\n"
            return section, total
        
        assets_section, total_assets = format_section("ASSETS", assets)
        liabilities_section, total_liabilities = format_section("LIABILITIES", liabilities)
        equity_section, total_equity = format_section("EQUITY", equity)
        revenue_section, total_revenue = format_section("REVENUE", revenue)
        expenses_section, total_expenses = format_section("EXPENSES", expenses)
        
        report += assets_section + liabilities_section + equity_section
        report += revenue_section + expenses_section
        
        net_income = total_revenue - total_expenses
        report += f"NET INCOME: ₱{net_income:,.2f}\n"
        
        return report
    
    def format_ledger_report(self, ledger_data):
        """Format ledger data for display in T-account style"""
        if not ledger_data:
            return "No journal entries available."
        
        report = "GENERAL LEDGER REPORT\n" + "="*60 + "\n\n"
        
        # Group entries by journal entry
        current_je_id = None
        journal_entries = {}
        
        for row in ledger_data:
            je_id, journal_type, ref_no, description, date, total_debit, total_credit, account, debit, credit, line_desc = row
            
            if je_id not in journal_entries:
                journal_entries[je_id] = {
                    'header': (journal_type, ref_no, description, date, total_debit, total_credit),
                    'lines': []
                }
            
            journal_entries[je_id]['lines'].append((account, debit, credit, line_desc))
        
        # Format each journal entry
        for je_id, entry in journal_entries.items():
            header = entry['header']
            lines = entry['lines']
            
            journal_type, ref_no, description, date, total_debit, total_credit = header
            
            report += f"Journal Entry #{je_id} - {journal_type.upper()}\n"
            report += f"Date: {date}  |  Reference: {ref_no or 'N/A'}  |  Total: ₱{total_debit:,.2f}\n"
            report += f"Description: {description}\n"
            report += "-" * 60 + "\n"
            
            # T-Account style display
            report += f"{'ACCOUNT':<25} {'DEBIT':<15} {'CREDIT':<15}\n"
            report += "-" * 60 + "\n"
            
            for account, debit, credit, line_desc in lines:
                debit_str = f"₱{debit:,.2f}" if debit > 0 else ""
                credit_str = f"₱{credit:,.2f}" if credit > 0 else ""
                report += f"{account:<25} {debit_str:<15} {credit_str:<15}\n"
                if line_desc and line_desc != description:
                    report += f"  └─ {line_desc}\n"
            
            report += "-" * 60 + "\n"
            report += f"{'TOTALS:':<25} ₱{total_debit:,.2f}     ₱{total_credit:,.2f}\n\n"
        
        return report
    
    def show_report_dialog(self, title, content):
        """Show report in a dialog"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.scrollview import MDScrollView
        from kivymd.uix.label import MDLabel
        from kivymd.uix.button import MDFlatButton
        
        # Create scrollable content
        scroll = MDScrollView(size_hint=(1, 1))
        label = MDLabel(
            text=content,
            theme_text_color="Primary",
            font_size="12sp",
            size_hint=(1, None),
            height=self.texture_size[1],
            text_size=(scroll.width, None),
            halign="left",
            valign="top"
        )
        scroll.add_widget(label)
        
        # Create dialog
        dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=scroll,
            size_hint=(0.8, 0.8),
            buttons=[
                MDFlatButton(
                    text="CLOSE",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        
        dialog.open()
    
    def refresh_reports(self):
        """Refresh all report data"""
        self.load_reports_data()
        print("Reports refreshed")
    
    def switch_screen(self, screen_name):
        """Switch to a different screen"""
        self.parent.current = screen_name