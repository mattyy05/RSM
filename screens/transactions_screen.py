from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen


class TransactionsScreen(MDScreen):
    """Screen to display all accounting transactions and journal entries"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.show_written_off = False  # Flag to track whether to show written-off transactions
    
    def on_enter(self):
        """Load transactions when screen is entered"""
        self.app = MDApp.get_running_app()
        self.load_transactions()
        self.update_navigation_permissions()
    
    def load_transactions(self):
        """
        Load and display all transactions from the database
        
        This method fixes the transaction amount display issue by:
        1. Joining journal_entries with sales/purchases tables to get actual business amounts
        2. For sales: Shows the checkout amount (e.g., ₱500) instead of total debits (e.g., ₱800)
        3. For purchases: Shows the purchase amount instead of accounting totals
        4. For other transactions: Uses appropriate debit/credit amounts
        5. Filters out sales marked as 'written_off' due to bad debt to avoid confusion
        
        The fix ensures that transaction amounts match what users expect to see
        based on their actual business transactions, not accounting journal totals.
        When a credit sale is recorded as bad debt, it's marked as 'written_off' and
        excluded from the active transactions list.
        """
        try:
            if not self.app:
                self.app = MDApp.get_running_app()
            
            # Clear existing transactions
            transactions_list = self.ids.transactions_list
            transactions_list.clear_widgets()
            
            # Get all journal entries with their corresponding business transaction amounts and payment types
            # LEFT JOINs ensure we get the actual sale/purchase amounts when available
            # ENHANCED: Now includes payment_type from sales table for transaction display
            cursor = self.app.db.conn.cursor()
            # Build query based on written-off filter setting
            if self.show_written_off:
                # Show all transactions including written-off sales
                query = """
                    SELECT je.id, je.journal_type, je.reference_no, je.description, 
                           je.date, je.total_debit, je.total_credit, je.created_at,
                           s.total_amount as sale_amount,
                           s.payment_type as sale_payment_type,
                           s.id as sale_id,
                           p.total_amount as purchase_amount,
                           p.id as purchase_id,
                           s.status as sale_status
                    FROM journal_entries je
                    LEFT JOIN sales s ON je.reference_no = 'SALE-' || s.id AND je.journal_type = 'sales'
                    LEFT JOIN purchases p ON je.reference_no = 'PUR-' || p.id AND je.journal_type = 'purchase'
                    ORDER BY je.created_at DESC
                """
            else:
                # Hide written-off sales (default behavior)
                query = """
                    SELECT je.id, je.journal_type, je.reference_no, je.description, 
                           je.date, je.total_debit, je.total_credit, je.created_at,
                           s.total_amount as sale_amount,
                           s.payment_type as sale_payment_type,
                           s.id as sale_id,
                           p.total_amount as purchase_amount,
                           p.id as purchase_id,
                           s.status as sale_status
                    FROM journal_entries je
                    LEFT JOIN sales s ON je.reference_no = 'SALE-' || s.id AND je.journal_type = 'sales' 
                        AND (s.status IS NULL OR s.status != 'written_off')
                    LEFT JOIN purchases p ON je.reference_no = 'PUR-' || p.id AND je.journal_type = 'purchase'
                    WHERE (je.journal_type != 'sales' OR s.id IS NOT NULL)
                    ORDER BY je.created_at DESC
                """
            
            cursor.execute(query)
            
            transactions = cursor.fetchall()
            
            if not transactions:
                # Show empty state
                self.show_empty_state()
                return
            
            # Add each transaction to the list
            for transaction in transactions:
                self.add_transaction_item(transaction)
            
            # Update stats in header
            self.update_transaction_stats(len(transactions), transactions[0] if transactions else None)
                
            print(f"Loaded {len(transactions)} transactions")
            
        except Exception as e:
            print(f"Error loading transactions: {e}")
            self.show_error_state(str(e))
    
    def get_transaction_product_details(self, transaction):
        """
        Get product details for a transaction to display specific items sold/purchased
        Returns a formatted string with product names and quantities
        """
        try:
            # Unpack transaction data (includes sale_status field)
            (je_id, journal_type, ref_no, description, date, total_debit, total_credit, 
             created_at, sale_amount, sale_payment_type, sale_id, purchase_amount, purchase_id, sale_status) = transaction
            
            cursor = self.app.db.conn.cursor()
            
            if journal_type == 'sales' and sale_id:
                # Get sale items
                cursor.execute("""
                    SELECT si.quantity, p.name as product_name
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                    ORDER BY p.name
                """, (sale_id,))
                items = cursor.fetchall()
                
                if items:
                    if len(items) == 1:
                        qty, name = items[0]
                        return f"{int(qty)}x {name}"
                    elif len(items) <= 3:
                        item_list = [f"{int(qty)}x {name}" for qty, name in items]
                        return ", ".join(item_list)
                    else:
                        # Show first 2 items + count
                        item_list = [f"{int(items[0][0])}x {items[0][1]}", f"{int(items[1][0])}x {items[1][1]}"]
                        remaining = len(items) - 2
                        return f"{', '.join(item_list)} +{remaining} more"
            
            elif journal_type == 'purchase' and purchase_id:
                # Get purchase items
                cursor.execute("""
                    SELECT pi.quantity, p.name as product_name
                    FROM purchase_items pi
                    JOIN products p ON pi.product_id = p.id
                    WHERE pi.purchase_id = ?
                    ORDER BY p.name
                """, (purchase_id,))
                items = cursor.fetchall()
                
                if items:
                    if len(items) == 1:
                        qty, name = items[0]
                        return f"{int(qty)}x {name}"
                    elif len(items) <= 3:
                        item_list = [f"{int(qty)}x {name}" for qty, name in items]
                        return ", ".join(item_list)
                    else:
                        # Show first 2 items + count
                        item_list = [f"{int(items[0][0])}x {items[0][1]}", f"{int(items[1][0])}x {items[1][1]}"]
                        remaining = len(items) - 2
                        return f"{', '.join(item_list)} +{remaining} more"
            
            # For non-sales/purchase transactions, return empty
            return ""
            
        except Exception as e:
            print(f"Error getting product details: {e}")
            return ""

    def add_transaction_item(self, transaction):
        """
        Enhanced transaction item display with payment type specification
        
        This method handles the display logic for showing:
        - Correct transaction amounts (₱500 not ₱800)
        - Payment method specification (Cash vs A/R)
        - Enhanced visual indicators for payment types
        - Improved transaction categorization
        
        The enhancement ensures users can clearly see payment methods used
        and amounts match their business expectations.
        """
        from kivymd.uix.card import MDCard
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        from kivymd.uix.button import MDIconButton
        from datetime import datetime
        
        # Unpack transaction data (now includes sale_status field)
        trans_id, journal_type, ref_no, description, date, total_debit, total_credit, created_at, sale_amount, sale_payment_type, sale_id, purchase_amount, purchase_id, sale_status = transaction
        
        # AMOUNT DETERMINATION: Correct amount display logic
        # This is the core fix for the ₱500 → ₱800 issue
        if journal_type == 'sales' and sale_amount is not None:
            # For sales transactions, show the actual sale amount (checkout amount)
            # NOT the total_debit which includes sale amount + cost of goods sold
            display_amount = sale_amount
            amount_description = "Sale Amount"
        elif journal_type == 'purchase' and purchase_amount is not None:
            # For purchase transactions, show the actual purchase amount
            display_amount = purchase_amount
            amount_description = "Purchase Amount"
        elif journal_type == 'cash_receipt':
            # For cash receipts, show the credit amount (money coming in)
            display_amount = total_credit
            amount_description = "Cash Received"
        elif journal_type == 'cash_disbursement':
            # For cash disbursements, show the debit amount (money going out)
            display_amount = total_debit
            amount_description = "Cash Paid"
        elif journal_type == 'ap':
            # For accounts payable, show the credit amount
            display_amount = total_credit
            amount_description = "Amount Owed"
        else:
            # For other types, show total_debit or total_credit (whichever is larger)
            # This handles general journal entries and adjustments
            display_amount = max(total_debit, total_credit)
            amount_description = "Transaction Amount"
        
        # PAYMENT TYPE DETERMINATION: Enhanced transaction labeling
        transaction_label = journal_type.upper()
        payment_indicator = ""
        
        if journal_type == 'sales' and sale_payment_type:
            if sale_payment_type == 'cash':
                payment_indicator = ""
                transaction_label = "CASH SALE"
            elif sale_payment_type == 'credit':
                payment_indicator = ""
                transaction_label = "CREDIT SALE (A/R)"
            else:
                payment_indicator = f" ({sale_payment_type.upper()})"
        
        # DATE PARSING: Enhanced date handling
        try:
            if isinstance(date, str):
                date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
            else:
                date_obj = date
            date_str = date_obj.strftime("%Y-%m-%d %H:%M")
        except:
            date_str = str(date)[:16]
        
        # 🎨 CARD CREATION: Enhanced visual design with dynamic height
        card = MDCard(
            size_hint_y=None,
            height="180dp",  # Increased height to prevent text overlap
            elevation=0,
            padding="12dp",
            spacing="4dp",
            md_bg_color=[1, 1, 1, 1],
            line_color=[0.8, 0.8, 0.8, 1],  # Light gray outline
            line_width=1
        )
        
        # Main content layout
        main_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="12dp",
            padding="4dp",
            adaptive_height=True
        )
        
        # Left side - Enhanced transaction info
        info_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=0.7,
            spacing="2dp",
            adaptive_height=True
        )
        
        # Enhanced transaction title with payment indicator
        title_label = MDLabel(
            text=f"[b]{transaction_label}{payment_indicator} - {ref_no}[/b]",
            markup=True,
            font_style="Subtitle1",
            size_hint_y=None,
            height="22dp",
            theme_text_color="Primary",
            text_size=(None, None)
        )
        
        # Description
        desc_label = MDLabel(
            text=description,
            font_style="Body2",
            size_hint_y=None,
            height="18dp",
            theme_text_color="Secondary",
            text_size=(None, None)
        )
        
        # Product Details (for sales and purchases)
        product_details = self.get_transaction_product_details(transaction)
        if product_details:
            products_label = MDLabel(
                text=f"Items: {product_details}",
                font_style="Body2",
                size_hint_y=None,
                height="18dp",
                theme_text_color="Primary",
                markup=True,
                text_size=(None, None)
            )
        else:
            products_label = None
        
        # Enhanced date and payment type info
        date_label = MDLabel(
            text=f"Date: {date_str}",
            font_style="Caption",
            size_hint_y=None,
            height="14dp",
            theme_text_color="Hint",
            text_size=(None, None)
        )
        
        # Payment method specification for sales
        if journal_type == 'sales' and sale_payment_type:
            payment_method_text = "Cash Payment" if sale_payment_type == 'cash' else "Accounts Receivable"
            payment_label = MDLabel(
                text=f"Payment: {payment_method_text}",
                font_style="Caption",
                size_hint_y=None,
                height="14dp",
                theme_text_color="Secondary",
                text_size=(None, None)
            )
        else:
            # For non-sales, show transaction type
            payment_label = MDLabel(
                text=f"Type: {journal_type.replace('_', ' ').title()}",
                font_style="Caption",
                size_hint_y=None,
                height="14dp",
                theme_text_color="Secondary",
                text_size=(None, None)
            )
        
        # Enhanced amount info - Shows the correct business transaction amount
        # This fixes the ₱500 checkout showing as ₱800 issue
        amount_label = MDLabel(
            text=f"{amount_description}: ₱{display_amount:,.2f}",
            font_style="Subtitle2",
            size_hint_y=None,
            height="18dp",
            theme_text_color="Primary",
            text_size=(None, None)
        )
        
        info_layout.add_widget(title_label)
        info_layout.add_widget(desc_label)
        if products_label:
            info_layout.add_widget(products_label)
        info_layout.add_widget(date_label)
        info_layout.add_widget(payment_label)  # New payment method info
        info_layout.add_widget(amount_label)
        
        # Right side - Enhanced actions and status
        action_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=0.3,
            spacing="4dp",
            adaptive_height=True
        )
        
        # Enhanced transaction type badge with payment-specific colors
        type_colors = {
            'sales': [0.533, 0.620, 0.451, 1] if sale_payment_type == 'cash' else [0.831, 0.686, 0.216, 1],  # Green for cash, Gold for A/R
            'cash_receipt': [0.533, 0.620, 0.451, 1],  # Green
            'cash_disbursement': [0.639, 0.114, 0.114, 1],  # Red
            'ap': [1, 0.647, 0, 1],  # Orange
            'general': [0.427, 0.137, 0.137, 1]  # Dark red
        }
        
        # Select badge color based on transaction and payment type
        badge_color = type_colors.get(journal_type, [0.5, 0.5, 0.5, 1])
        
        # Update badge color if it was changed for written-off status
        if journal_type == 'sales' and sale_status == 'written_off':
            final_badge_color = [0.8, 0.2, 0.2, 1]  # Red for written-off
        else:
            final_badge_color = badge_color
        
        type_card = MDCard(
            size_hint_y=None,
            height="32dp",
            md_bg_color=final_badge_color,
            radius=[16],
            padding="8dp"
        )
        
        # Enhanced badge text with payment info and written-off status
        if journal_type == 'sales' and sale_payment_type:
            if sale_status == 'written_off':
                badge_text = "Written Off"
                badge_color = [0.8, 0.2, 0.2, 1]  # Red color for written-off
            else:
                badge_text = "Cash" if sale_payment_type == 'cash' else "A/R"
        else:
            badge_text = journal_type.replace('_', ' ').title()
            
        type_label = MDLabel(
            text=badge_text,
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )
        
        type_card.add_widget(type_label)
        
        # View details button
        view_btn = MDIconButton(
            icon="eye",
            theme_icon_color="Custom",
            icon_color=[0.639, 0.114, 0.114, 1],
            on_release=lambda x, tid=trans_id: self.view_transaction_details(tid)
        )
        
        action_layout.add_widget(type_card)
        action_layout.add_widget(view_btn)
        
        main_layout.add_widget(info_layout)
        main_layout.add_widget(action_layout)
        card.add_widget(main_layout)
        
        # Add to transactions list
        self.ids.transactions_list.add_widget(card)
    
    def view_transaction_details(self, transaction_id):
        """Show detailed view of a specific transaction"""
        try:
            cursor = self.app.db.conn.cursor()
            
            # Get journal entry header
            cursor.execute("""
                SELECT journal_type, reference_no, description, date, total_debit, total_credit
                FROM journal_entries WHERE id = ?
            """, (transaction_id,))
            
            header = cursor.fetchone()
            if not header:
                print("Transaction not found")
                return
            
            # Get journal entry lines
            cursor.execute("""
                SELECT account_name, debit_amount, credit_amount, description
                FROM journal_entry_lines WHERE journal_entry_id = ?
                ORDER BY debit_amount DESC, credit_amount DESC
            """, (transaction_id,))
            
            lines = cursor.fetchall()
            
            # Display in console (you can enhance this with a popup dialog)
            print(f"\nTRANSACTION DETAILS #{transaction_id}")
            print(f"Type: {header[0]} | Ref: {header[1]} | Date: {header[3]}")
            print(f"Description: {header[2]}")
            print("="*60)
            
            for line in lines:
                account, debit, credit, desc = line
                if debit > 0:
                    print(f"DR  {account:<25} ₱{debit:>10,.2f}")
                if credit > 0:
                    print(f"    CR  {account:<21} ₱{credit:>10,.2f}")
            
            print("="*60)
            print(f"Total Debits: ₱{header[4]:,.2f} | Total Credits: ₱{header[5]:,.2f}\n")
            
        except Exception as e:
            print(f"Error viewing transaction details: {e}")
    
    def show_empty_state(self):
        """Show message when no transactions exist"""
        from kivymd.uix.card import MDCard
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        from kivymd.icon_definitions import md_icons
        
        card = MDCard(
            size_hint_y=None,
            height="200dp",
            elevation=0,
            md_bg_color=[0.98, 0.98, 0.98, 1],
            padding="32dp",
            line_color=[0.9, 0.9, 0.9, 1],  # Light gray outline
            line_width=1
        )
        
        layout = MDBoxLayout(
            orientation='vertical',
            spacing="16dp"
        )
        
        icon_label = MDLabel(
            text="",
            font_size="48sp",
            halign="center",
            size_hint_y=None,
            height="60dp"
        )
        
        title_label = MDLabel(
            text="No Transactions Yet",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height="40dp",
            theme_text_color="Primary"
        )
        
        subtitle_label = MDLabel(
            text="Start making sales or recording expenses to see transactions here.",
            font_style="Body2",
            halign="center",
            size_hint_y=None,
            height="60dp",
            theme_text_color="Secondary"
        )
        
        layout.add_widget(icon_label)
        layout.add_widget(title_label)
        layout.add_widget(subtitle_label)
        card.add_widget(layout)
        
        self.ids.transactions_list.add_widget(card)
    
    def show_error_state(self, error_msg):
        """Show error message"""
        from kivymd.uix.card import MDCard
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        
        card = MDCard(
            size_hint_y=None,
            height="150dp",
            elevation=0,
            md_bg_color=[1, 0.9, 0.9, 1],
            padding="16dp",
            line_color=[1, 0.6, 0.6, 1],  # Light red outline for error
            line_width=2
        )
        
        layout = MDBoxLayout(
            orientation='vertical',
            spacing="8dp"
        )
        
        title_label = MDLabel(
            text="Error Loading Transactions",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Error"
        )
        
        error_label = MDLabel(
            text=error_msg,
            font_style="Body2",
            halign="center",
            theme_text_color="Secondary"
        )
        
        layout.add_widget(title_label)
        layout.add_widget(error_label)
        card.add_widget(layout)
        
        self.ids.transactions_list.add_widget(card)
    
    def refresh_transactions(self):
        """Refresh the transactions list"""
        self.load_transactions()
        print("Transactions refreshed")
    
    def update_transaction_stats(self, total_count, latest_transaction):
        """Update the statistics in the header"""
        try:
            # Update total transactions count (with safe fallback)
            try:
                self.ids.total_transactions_label.text = str(total_count)
            except AttributeError:
                print("Warning: total_transactions_label not found in UI")
            
            # Update last transaction info
            if latest_transaction:
                try:
                    # Parse the latest transaction info (now includes sale_amount, sale_payment_type, and purchase_amount)
                    trans_id, journal_type, ref_no, description, date, total_debit, total_credit, created_at, sale_amount, sale_payment_type, purchase_amount = latest_transaction
                    
                    # Format the last transaction text using the correct amount
                    if journal_type == 'sales' and sale_amount is not None:
                        last_text = f"Sale ₱{sale_amount:,.0f}"
                    elif journal_type == 'purchase' and purchase_amount is not None:
                        last_text = f"Purchase ₱{purchase_amount:,.0f}"
                    elif journal_type == 'cash_disbursement':
                        last_text = f"Expense ₱{total_debit:,.0f}"
                    elif journal_type == 'cash_receipt':
                        last_text = f"Cash In ₱{total_credit:,.0f}"
                    elif journal_type == 'general':
                        last_text = f"Adjustment ₱{max(total_debit, total_credit):,.0f}"
                    else:
                        last_text = f"{journal_type.title()}"
                    
                    try:
                        self.ids.last_transaction_label.text = last_text
                    except AttributeError:
                        print("Warning: last_transaction_label not found in UI")
                        
                except ValueError as ve:
                    # Handle case where transaction structure is different (old format)
                    print(f"Transaction unpacking error: {ve}")
                    if len(latest_transaction) >= 8:
                        trans_id, journal_type, ref_no, description, date, total_debit, total_credit, created_at = latest_transaction[:8]
                        if journal_type == 'sales':
                            last_text = f"Sale ₱{total_debit:,.0f}"
                        elif journal_type == 'cash_disbursement':
                            last_text = f"Expense ₱{total_debit:,.0f}"
                        else:
                            last_text = f"{journal_type.title()}"
                        
                        try:
                            self.ids.last_transaction_label.text = last_text
                        except AttributeError:
                            print("Warning: last_transaction_label not found in UI")
            else:
                try:
                    self.ids.last_transaction_label.text = "None"
                except AttributeError:
                    print("Warning: last_transaction_label not found in UI")
                
        except Exception as e:
            print(f"Error updating transaction stats: {e}")
            # Ensure UI doesn't break even if stats update fails
            try:
                if hasattr(self, 'ids'):
                    if hasattr(self.ids, 'total_transactions_label'):
                        self.ids.total_transactions_label.text = str(total_count) if total_count else "0"
                    if hasattr(self.ids, 'last_transaction_label'):
                        self.ids.last_transaction_label.text = "Error"
            except:
                pass  # Fail silently to prevent UI crashes
    
    def update_navigation_permissions(self):
        """Update navigation button visibility based on user role"""
        try:
            app = MDApp.get_running_app()
            
            if not app.auth_manager or not app.auth_manager.is_authenticated():
                return
                
            role = app.auth_manager.get_current_role()
            
            # Disable restricted buttons for cashiers
            if role == 'cashier':
                # Disable inventory button
                if hasattr(self.ids, 'inventory_button'):
                    self.ids.inventory_button.disabled = True
                    self.ids.inventory_button.md_bg_color = [0.5, 0.5, 0.5, 1]
                    self.ids.inventory_button.opacity = 0.5
                
                # Disable reports button
                if hasattr(self.ids, 'reports_button'):
                    self.ids.reports_button.disabled = True
                    self.ids.reports_button.md_bg_color = [0.5, 0.5, 0.5, 1]
                    self.ids.reports_button.opacity = 0.5
                
                # Disable user management button
                if hasattr(self.ids, 'user_management_button'):
                    self.ids.user_management_button.disabled = True
                    self.ids.user_management_button.md_bg_color = [0.5, 0.5, 0.5, 1]
                    self.ids.user_management_button.opacity = 0.5
                    
            elif role == 'owner':
                # Enable all buttons for owners
                if hasattr(self.ids, 'inventory_button'):
                    self.ids.inventory_button.disabled = False
                    self.ids.inventory_button.md_bg_color = [0.639, 0.114, 0.114, 1]
                    self.ids.inventory_button.opacity = 1.0
                
                if hasattr(self.ids, 'reports_button'):
                    self.ids.reports_button.disabled = False
                    self.ids.reports_button.md_bg_color = [0.639, 0.114, 0.114, 1]
                    self.ids.reports_button.opacity = 1.0
                
                if hasattr(self.ids, 'user_management_button'):
                    self.ids.user_management_button.disabled = False
                    self.ids.user_management_button.md_bg_color = [0.639, 0.114, 0.114, 1]
                    self.ids.user_management_button.opacity = 1.0
                    
        except Exception as e:
            print(f"Error updating navigation permissions: {e}")
    
    def switch_screen(self, screen_name):
        """Switch to a different screen with permission check"""
        app = MDApp.get_running_app()
        
        # Check if user has permission to access the screen
        if app.auth_manager and not app.auth_manager.can_access_screen(screen_name):
            from kivymd.uix.snackbar import Snackbar
            message = app.auth_manager.get_access_denied_message(screen=screen_name)
            Snackbar(text=message, duration=3).open()
            return
        
        self.parent.current = screen_name
    
    def toggle_written_off_display(self):
        """Toggle between showing and hiding written-off transactions"""
        try:
            self.show_written_off = not self.show_written_off
            
            # Update button appearance
            button = self.ids.written_off_toggle
            if self.show_written_off:
                button.text = "Hide Written-off"
                button.md_bg_color = [0.8, 0.2, 0.2, 1]  # Red when showing written-off
            else:
                button.text = "Show Written-off"
                button.md_bg_color = [0.5, 0.5, 0.5, 1]  # Gray when hiding written-off
            
            # Reload transactions with new filter
            self.load_transactions()
            
            status = "showing" if self.show_written_off else "hiding"
            print(f"Toggled written-off transactions display - now {status} written-off sales")
            
        except Exception as e:
            print(f"Error toggling written-off display: {e}")
