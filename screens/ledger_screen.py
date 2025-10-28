from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from datetime import datetime


class LedgerScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_account = None
        self.current_ledger_data = []
        
    def on_enter(self):
        """Load ledger data when screen is entered"""
        self.load_account_summary()
        self.update_ledger_stats()
    
    def load_account_summary(self):
        """Load summary of all accounts"""
        app = MDApp.get_running_app()
        try:
            # Get all accounts with their balances
            accounts = app.db.get_all_accounts_with_balances()
            
            # Ensure unique accounts (extra safety measure)
            unique_accounts = {}
            for account in accounts:
                account_id, account_name, account_type, balance = account[:4]
                key = (account_name, account_type)
                if key not in unique_accounts:
                    unique_accounts[key] = account
                else:
                    # If duplicate found, use the one with higher balance or lower ID
                    existing = unique_accounts[key]
                    if balance > existing[3] or (balance == existing[3] and account_id < existing[0]):
                        unique_accounts[key] = account
            
            accounts = list(unique_accounts.values())
            
            # Clear existing account list
            account_list = self.ids.account_list
            account_list.clear_widgets()
            
            if not accounts:
                # Show empty state
                self.show_empty_accounts_state()
                return
            
            # Group accounts by type
            account_groups = {
                'asset': [],
                'liability': [],
                'equity': [],
                'revenue': [],
                'expense': []
            }
            
            for account in accounts:
                account_type = account[2].lower()  # account_type
                if account_type in account_groups:
                    account_groups[account_type].append(account)
            
            # Display accounts grouped by type
            for account_type, accounts_in_type in account_groups.items():
                if accounts_in_type:
                    self.add_account_group(account_list, account_type.title(), accounts_in_type)
                    
            print(f"Loaded {len(accounts)} accounts in ledger")
            
        except Exception as e:
            print(f"Error loading account summary: {e}")
            self.show_error_state(str(e))
    
    def add_account_group(self, container, group_title, accounts):
        """Add a group of accounts to the display"""
        
        # Group header
        header_card = MDCard(
            size_hint_y=None,
            height="40dp",
            elevation=0,
            md_bg_color=[0.639, 0.114, 0.114, 1],  # App theme color
            padding="8dp"
        )
        
        header_label = MDLabel(
            text=f"[size=16][b]{group_title} Accounts[/b][/size]",
            markup=True,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            size_hint_y=None,
            height="24dp"
        )
        
        header_card.add_widget(header_label)
        container.add_widget(header_card)
        
        # Account items
        for account in accounts:
            self.add_account_item(container, account)
    
    def add_account_item(self, container, account):
        """Add a single account item to the display"""
        account_id, account_name, account_type, balance = account[:4]
        
        # Determine balance color based on account type and balance
        if account_type.lower() in ['asset', 'expense']:
            # Normal debit balance
            balance_color = [0.2, 0.6, 0.2, 1] if balance >= 0 else [0.8, 0.2, 0.2, 1]
        else:
            # Normal credit balance (liability, equity, revenue)
            balance_color = [0.2, 0.6, 0.2, 1] if balance >= 0 else [0.8, 0.2, 0.2, 1]
        
        account_card = MDCard(
            size_hint_y=None,
            height="60dp",
            elevation=0,
            line_color=[0.9, 0.9, 0.9, 1],
            line_width=1,
            padding="8dp",
            ripple_behavior=True,
            on_release=lambda x, acc_id=account_id, acc_name=account_name: self.view_account_ledger(acc_id, acc_name)
        )
        
        account_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="12dp",
            padding="8dp"
        )
        
        # Account name
        name_label = MDLabel(
            text=account_name,
            size_hint_x=0.5,
            theme_text_color="Primary",
            font_style="Subtitle2"
        )
        
        # Account type
        type_label = MDLabel(
            text=account_type.title(),
            size_hint_x=0.25,
            theme_text_color="Secondary",
            font_style="Caption"
        )
        
        # Account balance
        balance_label = MDLabel(
            text=f"₱{balance:,.2f}",
            size_hint_x=0.25,
            halign="right",
            theme_text_color="Custom",
            text_color=balance_color,
            font_style="Subtitle2",
            bold=True
        )
        
        account_layout.add_widget(name_label)
        account_layout.add_widget(type_label)
        account_layout.add_widget(balance_label)
        
        account_card.add_widget(account_layout)
        container.add_widget(account_card)
    
    def view_account_ledger(self, account_id, account_name):
        """View detailed ledger for a specific account with summary"""
        app = MDApp.get_running_app()
        self.selected_account = account_name
        
        try:
            # Get account summary (debits, credits, balance)
            account_summary = app.accounting.get_account_summary(account_name)
            
            if not account_summary:
                Snackbar(
                    text=f"Account '{account_name}' not found",
                    duration=3,
                    bg_color=[0.8, 0.2, 0.2, 1]
                ).open()
                return
            
            # Get ledger entries for this account
            ledger_entries = app.accounting.get_account_ledger(account_name)
            
            # Clear and populate ledger display
            ledger_container = self.ids.ledger_display
            ledger_container.clear_widgets()
            
            # Add account summary header
            self.add_account_summary_header(ledger_container, account_summary)
            
            # Add ledger entries if they exist
            if ledger_entries:
                self.add_ledger_entries_table(ledger_container, ledger_entries)
            else:
                self.add_no_transactions_message(ledger_container)
            
            # Update selected account display
            self.ids.selected_account_label.text = f"Ledger: {account_name}"
            
            print(f"Displaying ledger for {account_name} - {len(ledger_entries)} entries")
            
        except Exception as e:
            print(f"Error viewing account ledger: {e}")
            Snackbar(
                text=f"Error loading ledger for {account_name}",
                duration=3,
                bg_color=[0.8, 0.2, 0.2, 1]
            ).open()
    
    def add_account_summary_header(self, container, account_summary):
        """Add account summary header showing debits, credits, and balance"""
        # Main summary card
        summary_card = MDCard(
            size_hint_y=None,
            height="120dp",
            elevation=0,
            md_bg_color=[0.95, 0.95, 0.95, 1],
            padding="16dp"
        )
        
        summary_layout = MDBoxLayout(
            orientation='vertical',
            spacing="8dp"
        )
        
        # Account name and type
        header_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height="30dp"
        )
        
        account_name_label = MDLabel(
            text=f"[b]{account_summary['account_name']}[/b]",
            markup=True,
            size_hint_x=0.7,
            theme_text_color="Primary",
            font_style="H6"
        )
        
        account_type_label = MDLabel(
            text=f"({account_summary['account_type'].title()})",
            size_hint_x=0.3,
            halign="right",
            theme_text_color="Secondary",
            font_style="Body2"
        )
        
        header_layout.add_widget(account_name_label)
        header_layout.add_widget(account_type_label)
        
        # Summary figures in a grid
        figures_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="16dp",
            size_hint_y=None,
            height="60dp"
        )
        
        # Total Debits
        debit_card = MDCard(
            size_hint_x=0.33,
            elevation=0,
            md_bg_color=[0.8, 0.9, 0.8, 1],
            padding="8dp"
        )
        debit_layout = MDBoxLayout(orientation='vertical', spacing="4dp")
        debit_layout.add_widget(MDLabel(
            text="Total Debits",
            halign="center",
            font_style="Caption",
            theme_text_color="Secondary"
        ))
        debit_layout.add_widget(MDLabel(
            text=f"₱{account_summary['total_debits']:,.2f}",
            halign="center",
            font_style="Subtitle2",
            theme_text_color="Primary",
            bold=True
        ))
        debit_card.add_widget(debit_layout)
        
        # Total Credits
        credit_card = MDCard(
            size_hint_x=0.33,
            elevation=0,
            md_bg_color=[0.9, 0.8, 0.8, 1],
            padding="8dp"
        )
        credit_layout = MDBoxLayout(orientation='vertical', spacing="4dp")
        credit_layout.add_widget(MDLabel(
            text="Total Credits",
            halign="center",
            font_style="Caption",
            theme_text_color="Secondary"
        ))
        credit_layout.add_widget(MDLabel(
            text=f"₱{account_summary['total_credits']:,.2f}",
            halign="center",
            font_style="Subtitle2",
            theme_text_color="Primary",
            bold=True
        ))
        credit_card.add_widget(credit_layout)
        
        # Current Balance
        balance_card = MDCard(
            size_hint_x=0.34,
            elevation=0,
            md_bg_color=[0.8, 0.8, 0.9, 1],
            padding="8dp"
        )
        balance_layout = MDBoxLayout(orientation='vertical', spacing="4dp")
        balance_layout.add_widget(MDLabel(
            text="Current Balance",
            halign="center",
            font_style="Caption",
            theme_text_color="Secondary"
        ))
        
        # Color code the balance based on account type
        balance = account_summary['current_balance']
        balance_color = [0.2, 0.6, 0.2, 1] if balance >= 0 else [0.8, 0.2, 0.2, 1]
        
        balance_layout.add_widget(MDLabel(
            text=f"₱{balance:,.2f}",
            halign="center",
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=balance_color,
            bold=True
        ))
        balance_card.add_widget(balance_layout)
        
        figures_layout.add_widget(debit_card)
        figures_layout.add_widget(credit_card)
        figures_layout.add_widget(balance_card)
        
        summary_layout.add_widget(header_layout)
        summary_layout.add_widget(figures_layout)
        summary_card.add_widget(summary_layout)
        container.add_widget(summary_card)
        
        # Add spacing
        container.add_widget(MDBoxLayout(size_hint_y=None, height="16dp"))
    
    def add_no_transactions_message(self, container):
        """Add message when no transactions exist for the account"""
        message_card = MDCard(
            size_hint_y=None,
            height="80dp",
            elevation=0,
            md_bg_color=[0.98, 0.98, 0.98, 1],
            padding="16dp"
        )
        
        message_layout = MDBoxLayout(
            orientation='vertical',
            spacing="8dp"
        )
        
        message_layout.add_widget(MDLabel(
            text="No Transactions",
            halign="center",
            font_style="H6",
            theme_text_color="Secondary"
        ))
        
        message_layout.add_widget(MDLabel(
            text="This account has no transaction history yet.",
            halign="center",
            font_style="Body2",
            theme_text_color="Secondary"
        ))
        
        message_card.add_widget(message_layout)
        container.add_widget(message_card)
    
    def add_ledger_entries_table(self, container, ledger_entries):
        """Add a table showing all ledger entries for the account"""
        # Add section header
        entries_header = MDLabel(
            text="Transaction History",
            size_hint_y=None,
            height="30dp",
            theme_text_color="Primary",
            font_style="Subtitle1",
            bold=True
        )
        container.add_widget(entries_header)
        
        # Add table header
        header_card = MDCard(
            size_hint_y=None,
            height="40dp",
            elevation=0,
            md_bg_color=[0.533, 0.620, 0.451, 1],
            padding="8dp"
        )
        
        header_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="8dp"
        )
        
        # Column headers
        headers = [
            ("Date", 0.18),
            ("Description", 0.32),
            ("Ref", 0.12),
            ("Debit", 0.13),
            ("Credit", 0.13),
            ("Balance", 0.12)
        ]
        
        for header_text, width in headers:
            header_layout.add_widget(MDLabel(
                text=header_text,
                size_hint_x=width,
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1],
                font_style="Subtitle2",
                bold=True,
                halign="center" if header_text in ["Debit", "Credit", "Balance"] else "left"
            ))
        
        header_card.add_widget(header_layout)
        container.add_widget(header_card)
        
        # Add entries
        for i, entry in enumerate(ledger_entries):
            self.add_ledger_entry_row(container, entry, i % 2 == 0)
    
    def add_ledger_entry_row(self, container, entry, is_even_row):
        """Add a single ledger entry row"""
        # Row background color (alternating)
        bg_color = [0.98, 0.98, 0.98, 1] if is_even_row else [1, 1, 1, 1]
        
        entry_card = MDCard(
            size_hint_y=None,
            height="35dp",
            elevation=0,
            md_bg_color=bg_color,
            line_color=[0.95, 0.95, 0.95, 1],
            line_width=0.5,
            padding="8dp"
        )
        
        entry_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="8dp"
        )
        
        # Format date
        try:
            date_obj = datetime.fromisoformat(entry['date'].replace('Z', '+00:00'))
            date_str = date_obj.strftime('%m/%d/%y')
        except:
            date_str = entry['date'][:10]  # Fallback
        
        # Date
        entry_layout.add_widget(MDLabel(
            text=date_str,
            size_hint_x=0.18,
            theme_text_color="Primary",
            font_style="Body2"
        ))
        
        # Description (truncated if too long)
        description = entry['description']
        if len(description) > 30:
            description = description[:27] + "..."
        
        entry_layout.add_widget(MDLabel(
            text=description,
            size_hint_x=0.32,
            theme_text_color="Primary",
            font_style="Body2"
        ))
        
        # Reference
        entry_layout.add_widget(MDLabel(
            text=entry['reference'] or "",
            size_hint_x=0.12,
            theme_text_color="Secondary",
            font_style="Caption"
        ))
        
        # Debit
        debit_text = f"₱{entry['debit']:,.2f}" if entry['debit'] > 0 else ""
        entry_layout.add_widget(MDLabel(
            text=debit_text,
            size_hint_x=0.13,
            halign="right",
            theme_text_color="Custom",
            text_color=[0.2, 0.6, 0.2, 1] if entry['debit'] > 0 else [0.5, 0.5, 0.5, 1],
            font_style="Body2"
        ))
        
        # Credit
        credit_text = f"₱{entry['credit']:,.2f}" if entry['credit'] > 0 else ""
        entry_layout.add_widget(MDLabel(
            text=credit_text,
            size_hint_x=0.13,
            halign="right",
            theme_text_color="Custom",
            text_color=[0.8, 0.2, 0.2, 1] if entry['credit'] > 0 else [0.5, 0.5, 0.5, 1],
            font_style="Body2"
        ))
        
        # Running Balance
        balance_color = [0.2, 0.6, 0.2, 1] if entry['balance'] >= 0 else [0.8, 0.2, 0.2, 1]
        entry_layout.add_widget(MDLabel(
            text=f"₱{entry['balance']:,.2f}",
            size_hint_x=0.12,
            halign="right",
            theme_text_color="Custom",
            text_color=balance_color,
            font_style="Body2",
            bold=True
        ))
        
        entry_card.add_widget(entry_layout)
        container.add_widget(entry_card)
    
    def add_ledger_header(self, container, account_name):
        """Add header for ledger display"""
        header_card = MDCard(
            size_hint_y=None,
            height="50dp",
            elevation=0,
            md_bg_color=[0.533, 0.620, 0.451, 1],  # Green theme
            padding="8dp"
        )
        
        header_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="8dp"
        )
        
        # Column headers
        date_header = MDLabel(
            text="Date",
            size_hint_x=0.15,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            font_style="Subtitle2",
            bold=True
        )
        
        description_header = MDLabel(
            text="Description",
            size_hint_x=0.35,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            font_style="Subtitle2",
            bold=True
        )
        
        ref_header = MDLabel(
            text="Ref",
            size_hint_x=0.1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            font_style="Subtitle2",
            bold=True
        )
        
        debit_header = MDLabel(
            text="Debit",
            size_hint_x=0.15,
            halign="right",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            font_style="Subtitle2",
            bold=True
        )
        
        credit_header = MDLabel(
            text="Credit",
            size_hint_x=0.15,
            halign="right",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            font_style="Subtitle2",
            bold=True
        )
        
        balance_header = MDLabel(
            text="Balance",
            size_hint_x=0.1,
            halign="right",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            font_style="Subtitle2",
            bold=True
        )
        
        header_layout.add_widget(date_header)
        header_layout.add_widget(description_header)
        header_layout.add_widget(ref_header)
        header_layout.add_widget(debit_header)
        header_layout.add_widget(credit_header)
        header_layout.add_widget(balance_header)
        
        header_card.add_widget(header_layout)
        container.add_widget(header_card)
    
    def add_ledger_entry(self, container, entry, running_balance):
        """Add a single ledger entry to the display"""
        # entry format: (date, description, reference, debit_amount, credit_amount)
        date_str, description, reference, debit_amount, credit_amount = entry
        
        # Calculate running balance
        running_balance += debit_amount - credit_amount
        
        # Create entry card
        entry_card = MDCard(
            size_hint_y=None,
            height="50dp",
            elevation=0,
            line_color=[0.9, 0.9, 0.9, 1],
            line_width=1,
            padding="8dp"
        )
        
        entry_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="8dp"
        )
        
        # Format date
        try:
            if isinstance(date_str, str):
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = date_str
            formatted_date = date_obj.strftime("%m/%d")
        except:
            formatted_date = str(date_str)[:10]
        
        # Date
        date_label = MDLabel(
            text=formatted_date,
            size_hint_x=0.15,
            theme_text_color="Secondary",
            font_style="Caption"
        )
        
        # Description
        desc_label = MDLabel(
            text=description[:30] + "..." if len(description) > 30 else description,
            size_hint_x=0.35,
            theme_text_color="Primary",
            font_style="Body2"
        )
        
        # Reference
        ref_label = MDLabel(
            text=reference or "",
            size_hint_x=0.1,
            theme_text_color="Secondary",
            font_style="Caption"
        )
        
        # Debit amount
        debit_label = MDLabel(
            text=f"₱{debit_amount:,.2f}" if debit_amount > 0 else "",
            size_hint_x=0.15,
            halign="right",
            theme_text_color="Custom",
            text_color=[0.2, 0.6, 0.2, 1] if debit_amount > 0 else [0, 0, 0, 0],
            font_style="Body2"
        )
        
        # Credit amount
        credit_label = MDLabel(
            text=f"₱{credit_amount:,.2f}" if credit_amount > 0 else "",
            size_hint_x=0.15,
            halign="right",
            theme_text_color="Custom",
            text_color=[0.8, 0.2, 0.2, 1] if credit_amount > 0 else [0, 0, 0, 0],
            font_style="Body2"
        )
        
        # Running balance
        balance_color = [0.2, 0.6, 0.2, 1] if running_balance >= 0 else [0.8, 0.2, 0.2, 1]
        balance_label = MDLabel(
            text=f"₱{running_balance:,.2f}",
            size_hint_x=0.1,
            halign="right",
            theme_text_color="Custom",
            text_color=balance_color,
            font_style="Body2",
            bold=True
        )
        
        entry_layout.add_widget(date_label)
        entry_layout.add_widget(desc_label)
        entry_layout.add_widget(ref_label)
        entry_layout.add_widget(debit_label)
        entry_layout.add_widget(credit_label)
        entry_layout.add_widget(balance_label)
        
        entry_card.add_widget(entry_layout)
        container.add_widget(entry_card)
        
        return running_balance
    
    def show_empty_accounts_state(self):
        """Show empty state when no accounts exist"""
        account_list = self.ids.account_list
        
        empty_card = MDCard(
            size_hint_y=None,
            height="200dp",
            elevation=0,
            md_bg_color=[0.9, 0.9, 0.9, 1],
            padding="32dp"
        )
        
        empty_layout = MDBoxLayout(
            orientation='vertical',
            spacing="16dp"
        )
        
        empty_label = MDLabel(
            text="No Accounts Found",
            font_style="H6",
            halign="center",
            theme_text_color="Secondary"
        )
        
        subtitle_label = MDLabel(
            text="Accounts will appear here after your first transaction",
            font_style="Body2",
            halign="center",
            theme_text_color="Secondary"
        )
        
        empty_layout.add_widget(empty_label)
        empty_layout.add_widget(subtitle_label)
        empty_card.add_widget(empty_layout)
        
        account_list.add_widget(empty_card)
    
    def show_error_state(self, error_msg):
        """Show error state"""
        account_list = self.ids.account_list
        
        error_card = MDCard(
            size_hint_y=None,
            height="150dp",
            elevation=0,
            md_bg_color=[1, 0.9, 0.9, 1],
            padding="16dp"
        )
        
        error_layout = MDBoxLayout(
            orientation='vertical',
            spacing="8dp"
        )
        
        error_label = MDLabel(
            text="Error Loading Accounts",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Custom",
            text_color=[0.8, 0.2, 0.2, 1]
        )
        
        error_detail = MDLabel(
            text=error_msg,
            font_style="Caption",
            halign="center",
            theme_text_color="Secondary"
        )
        
        error_layout.add_widget(error_label)
        error_layout.add_widget(error_detail)
        error_card.add_widget(error_layout)
        
        account_list.add_widget(error_card)
    
    def update_ledger_stats(self):
        """Update ledger statistics"""
        app = MDApp.get_running_app()
        try:
            # Get overall statistics
            stats = app.db.get_dashboard_stats()
            
            # Update header stats
            self.ids.total_accounts_label.text = str(len(app.db.get_all_accounts_with_balances()))
            self.ids.total_entries_label.text = str(app.accounting.get_total_journal_entries())
            self.ids.trial_balance_label.text = "Balanced" if app.accounting.validate_trial_balance() else "Unbalanced"
            
            # Update trial balance color
            if app.accounting.validate_trial_balance():
                self.ids.trial_balance_label.text_color = [0.2, 0.6, 0.2, 1]  # Green
            else:
                self.ids.trial_balance_label.text_color = [0.8, 0.2, 0.2, 1]  # Red
            
        except Exception as e:
            print(f"Error updating ledger stats: {e}")
    
    def refresh_ledger(self):
        """Refresh the ledger display"""
        self.load_account_summary()
        self.update_ledger_stats()
        
        # Clear ledger display if no account is selected
        if not self.selected_account:
            ledger_container = self.ids.ledger_display
            ledger_container.clear_widgets()
            self.ids.selected_account_label.text = "Select an account to view its ledger"
        
        Snackbar(
            text="Ledger refreshed",
            duration=2,
            bg_color=[0.2, 0.6, 0.2, 1]
        ).open()
    
    def export_ledger(self):
        """Export ledger data (placeholder)"""
        if not self.selected_account:
            Snackbar(
                text="Please select an account first",
                duration=3,
                bg_color=[0.8, 0.6, 0.2, 1]
            ).open()
            return
        
        Snackbar(
            text=f"Exporting ledger for {self.selected_account}...",
            duration=3,
            bg_color=[0.2, 0.6, 0.2, 1]
        ).open()
        
        # TODO: Implement actual export functionality
        print(f"Export ledger for {self.selected_account}")
    
    def show_trial_balance(self):
        """Show trial balance dialog"""
        app = MDApp.get_running_app()
        
        try:
            # Get trial balance data
            accounts = app.db.get_all_accounts_with_balances()
            
            if not accounts:
                Snackbar(
                    text="No accounts found for trial balance",
                    duration=3
                ).open()
                return
            
            # Create trial balance content
            content = MDBoxLayout(
                orientation="vertical",
                spacing="8dp",
                size_hint_y=None,
                adaptive_height=True
            )
            
            # Header
            header = MDLabel(
                text="[size=18][b]Trial Balance[/b][/size]",
                markup=True,
                size_hint_y=None,
                height="40dp",
                halign="center"
            )
            content.add_widget(header)
            
            # Date
            date_label = MDLabel(
                text=f"As of {datetime.now().strftime('%B %d, %Y')}",
                size_hint_y=None,
                height="30dp",
                halign="center",
                theme_text_color="Secondary"
            )
            content.add_widget(date_label)
            
            # Table headers
            headers_layout = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height="40dp",
                spacing="8dp"
            )
            
            headers_layout.add_widget(MDLabel(text="Account", size_hint_x=0.5, bold=True))
            headers_layout.add_widget(MDLabel(text="Debit", size_hint_x=0.25, halign="right", bold=True))
            headers_layout.add_widget(MDLabel(text="Credit", size_hint_x=0.25, halign="right", bold=True))
            
            content.add_widget(headers_layout)
            
            # Account entries
            total_debits = 0
            total_credits = 0
            
            for account in accounts:
                account_name, account_type, balance = account[1], account[2], account[3]
                
                account_layout = MDBoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height="30dp",
                    spacing="8dp"
                )
                
                # Determine if balance goes in debit or credit column
                if account_type.lower() in ['asset', 'expense']:
                    # Normal debit balance
                    debit_amount = max(0, balance)
                    credit_amount = max(0, -balance)
                else:
                    # Normal credit balance
                    debit_amount = max(0, -balance)
                    credit_amount = max(0, balance)
                
                total_debits += debit_amount
                total_credits += credit_amount
                
                account_layout.add_widget(MDLabel(text=account_name, size_hint_x=0.5))
                account_layout.add_widget(MDLabel(
                    text=f"₱{debit_amount:,.2f}" if debit_amount > 0 else "",
                    size_hint_x=0.25,
                    halign="right"
                ))
                account_layout.add_widget(MDLabel(
                    text=f"₱{credit_amount:,.2f}" if credit_amount > 0 else "",
                    size_hint_x=0.25,
                    halign="right"
                ))
                
                content.add_widget(account_layout)
            
            # Totals
            totals_layout = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height="40dp",
                spacing="8dp"
            )
            
            totals_layout.add_widget(MDLabel(text="TOTAL", size_hint_x=0.5, bold=True))
            totals_layout.add_widget(MDLabel(
                text=f"₱{total_debits:,.2f}",
                size_hint_x=0.25,
                halign="right",
                bold=True
            ))
            totals_layout.add_widget(MDLabel(
                text=f"₱{total_credits:,.2f}",
                size_hint_x=0.25,
                halign="right",
                bold=True
            ))
            
            content.add_widget(totals_layout)
            
            # Balance check
            is_balanced = abs(total_debits - total_credits) < 0.01
            balance_text = "Trial Balance is Balanced" if is_balanced else "Trial Balance is NOT Balanced"
            balance_color = [0.2, 0.6, 0.2, 1] if is_balanced else [0.8, 0.2, 0.2, 1]
            
            balance_label = MDLabel(
                text=balance_text,
                size_hint_y=None,
                height="40dp",
                halign="center",
                theme_text_color="Custom",
                text_color=balance_color,
                bold=True
            )
            content.add_widget(balance_label)
            
            # Create dialog
            dialog = MDDialog(
                title="Trial Balance",
                type="custom",
                content_cls=content,
                size_hint=(0.9, 0.8),
                buttons=[
                    MDFlatButton(
                        text="CLOSE",
                        on_release=lambda x: dialog.dismiss()
                    )
                ]
            )
            
            dialog.open()
            
        except Exception as e:
            print(f"Error showing trial balance: {e}")
            Snackbar(
                text="Error generating trial balance",
                duration=3,
                bg_color=[0.8, 0.2, 0.2, 1]
            ).open()
    
    def switch_screen(self, screen_name):
        """Switch to a different screen"""
        app = MDApp.get_running_app()
        app.sm.current = screen_name
