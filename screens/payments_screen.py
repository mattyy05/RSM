from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton, MDFlatButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import OneLineListItem
from kivy.metrics import dp
import time
from datetime import datetime


class Tab(MDFloatLayout, MDTabsBase):
    """Tab class for MDTabs"""
    pass


class PaymentsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.customer_payments_data = []  # Cache for customer credit sales
        self.supplier_payments_data = []  # Cache for supplier credit purchases
        self.current_customer_filter = None
        self.current_supplier_filter = None
        
        # Operating expense types from accounting engine
        self.expense_types = {
            'rent': 'Rent Expense',
            'utilities': 'Utilities Expense', 
            'office_supplies': 'Office Supplies Expense',
            'advertising': 'Advertising Expense',
            'general': 'Operating Expenses'
        }
        
        # For the dropdown menu
        self.expense_dropdown = None
        self.selected_expense_type = None

    def on_enter(self):
        """Load payments data when screen is entered"""
        self.load_customer_payments()
        self.load_supplier_payments()
        self.load_expenses()
        self.update_navigation_permissions()

    def load_customer_payments(self):
        """Load customer credit sales data"""
        try:
            app = MDApp.get_running_app()
            # Get credit sales with customer info
            self.customer_payments_data = app.db.get_credit_sales()

            # Update the customer payments tab
            self.update_customer_payments_display()

        except Exception as e:
            print(f"Error loading customer payments: {e}")
            self.show_error_dialog("Error", f"Failed to load customer payments: {str(e)}")

    def load_supplier_payments(self):
        """Load supplier credit purchases data"""
        try:
            app = MDApp.get_running_app()
            # Get credit purchases with supplier info
            self.supplier_payments_data = app.db.get_credit_purchases()

            # Update the supplier payments tab
            self.update_supplier_payments_display()

        except Exception as e:
            print(f"Error loading supplier payments: {e}")
            self.show_error_dialog("Error", f"Failed to load supplier payments: {str(e)}")

    def load_expenses(self):
        """Load expenses data"""
        try:
            # Update the expenses tab
            self.update_expenses_display()

        except Exception as e:
            print(f"Error loading expenses: {e}")
            self.show_error_dialog("Error", f"Failed to load expenses: {str(e)}")

    def update_expenses_display(self):
        """Update the display of expenses"""
        try:
            expenses_tab = self.ids.expenses_tab_content
            expenses_tab.clear_widgets()

            # Create main layout
            main_layout = MDBoxLayout(orientation='vertical', spacing=dp(20))

            # Add expense recording form
            form_card = MDCard(
                orientation='vertical',
                padding=dp(20),
                size_hint=(1, None),
                height=dp(300),
                elevation=0
            )

            form_card.add_widget(MDLabel(
                text="[size=18][font=Brico]Record New Expense[/font][/size]",
                markup=True,
                theme_text_color="Primary",
                halign="center"
            ))

            # Expense type dropdown
            expense_type_layout = MDBoxLayout(orientation='vertical', spacing=dp(5))
            expense_type_layout.add_widget(MDLabel(
                text="Expense Type:",
                theme_text_color="Secondary",
                font_style="Caption"
            ))

            # Create dropdown button for expense type selection
            self.expense_type_button = MDFlatButton(
                text="Select Expense Type",
                size_hint=(1, None),
                height=dp(40),
                theme_bg_color="Custom",
                md_bg_color=[0.9, 0.9, 0.9, 1],  # Light gray background
                text_color=[0.2, 0.2, 0.2, 1],   # Dark text
                on_release=self.show_expense_type_menu
            )
            expense_type_layout.add_widget(self.expense_type_button)
            form_card.add_widget(expense_type_layout)

            # Amount field
            amount_layout = MDBoxLayout(orientation='vertical', spacing=dp(5))
            amount_layout.add_widget(MDLabel(
                text="Amount (₱):",
                theme_text_color="Secondary",
                font_style="Caption"
            ))

            self.expense_amount_field = MDTextField(
                hint_text="Enter amount",
                mode="rectangle",
                input_filter="float",
                size_hint=(1, None),
                height=dp(40)
            )
            amount_layout.add_widget(self.expense_amount_field)
            form_card.add_widget(amount_layout)

            # Description field
            desc_layout = MDBoxLayout(orientation='vertical', spacing=dp(5))
            desc_layout.add_widget(MDLabel(
                text="Description:",
                theme_text_color="Secondary",
                font_style="Caption"
            ))

            self.expense_desc_field = MDTextField(
                hint_text="Enter description",
                mode="rectangle",
                size_hint=(1, None),
                height=dp(40)
            )
            desc_layout.add_widget(self.expense_desc_field)
            form_card.add_widget(desc_layout)

            # Record button
            button_layout = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(10),
                size_hint=(1, None),
                height=dp(50)
            )

            record_btn = MDFlatButton(
                text="Record Expense",
                size_hint=(1, None),
                height=dp(45),
                md_bg_color=[0.2, 0.6, 0.2, 1],  # Green for positive action
                text_color=[1, 1, 1, 1],  # White text
                on_release=self.record_expense
            )
            button_layout.add_widget(record_btn)
            form_card.add_widget(button_layout)

            main_layout.add_widget(form_card)

            # Add recent expenses section
            recent_card = MDCard(
                orientation='vertical',
                padding=dp(20),
                size_hint=(1, None),
                height=dp(200),
                elevation=0
            )

            recent_card.add_widget(MDLabel(
                text="[size=18][font=Brico]Recent Expenses[/font][/size]",
                markup=True,
                theme_text_color="Primary",
                halign="center"
            ))

            # Placeholder for recent expenses
            recent_layout = MDBoxLayout(orientation='vertical', spacing=dp(5))
            recent_layout.add_widget(MDLabel(
                text="No recent expenses recorded",
                halign="center",
                theme_text_color="Secondary",
                font_style="Caption"
            ))
            recent_card.add_widget(recent_layout)

            main_layout.add_widget(recent_card)

            expenses_tab.add_widget(main_layout)

        except Exception as e:
            print(f"Error updating expenses display: {e}")

    def show_expense_type_menu(self, button):
        """Show dropdown menu for expense type selection"""
        menu_items = []
        for expense_code, expense_name in self.expense_types.items():
            menu_items.append({
                "text": expense_name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=expense_code, y=expense_name: self.select_expense_type(x, y),
            })
        
        self.expense_dropdown = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
        )
        self.expense_dropdown.open()

    def select_expense_type(self, expense_code, expense_name):
        """Handle expense type selection"""
        self.selected_expense_type = expense_code
        self.expense_type_button.text = expense_name
        if self.expense_dropdown:
            self.expense_dropdown.dismiss()

    def record_expense(self, instance):
        """Record a new expense"""
        try:
            # Get input values
            selected_expense = self.selected_expense_type
            amount_text = self.expense_amount_field.text.strip()
            description = self.expense_desc_field.text.strip()

            # Validate inputs
            if not selected_expense:
                self.show_error_dialog("Error", "Please select an expense type.")
                return

            if not amount_text:
                self.show_error_dialog("Error", "Please enter an amount.")
                return

            try:
                amount = float(amount_text)
            except ValueError:
                self.show_error_dialog("Error", "Please enter a valid amount.")
                return

            if amount <= 0:
                self.show_error_dialog("Error", "Amount must be greater than zero.")
                return

            if not description:
                self.show_error_dialog("Error", "Please enter a description.")
                return

            # Use the selected expense type directly
            expense_type = selected_expense

            # Record the expense
            app = MDApp.get_running_app()
            journal_entry_id = app.accounting.process_expense_transaction(
                expense_type=expense_type,
                amount=amount,
                description=description,
                payment_type='cash'
            )

            if journal_entry_id:
                self.show_success_dialog(
                    "Expense Recorded",
                    f"Expense of ₱{amount:,.2f} recorded successfully!\n\nJournal Entry ID: #{journal_entry_id}"
                )

                # Clear form
                self.selected_expense_type = None
                self.expense_type_button.text = "Select Expense Type"
                self.expense_amount_field.text = ""
                self.expense_desc_field.text = ""

                # Refresh display
                self.update_expenses_display()
            else:
                self.show_error_dialog("Warning", "Expense recorded but accounting entry failed.")

        except Exception as e:
            print(f"Error recording expense: {e}")
            self.show_error_dialog("Error", f"Failed to record expense: {str(e)}")

    def update_customer_payments_display(self):
        """Update the display of customer payments"""
        try:
            customer_tab = self.ids.customer_payments_tab
            customer_tab.clear_widgets()

            if not self.customer_payments_data:
                # Show empty state
                empty_layout = MDBoxLayout(
                    orientation='vertical',
                    padding=dp(20),
                    spacing=dp(10)
                )
                empty_layout.add_widget(MDLabel(
                    text="No outstanding customer payments",
                    halign="center",
                    theme_text_color="Secondary"
                ))
                customer_tab.add_widget(empty_layout)
                return

            # Create scrollable list
            scroll = MDScrollView()
            layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None)
            layout.bind(minimum_height=layout.setter('height'))

            for payment in self.customer_payments_data:
                sale_id, customer_id, customer_name, amount, date, ref_no, balance = payment

                # Create payment card
                card = MDCard(
                    orientation='vertical',
                    padding=dp(15),
                    size_hint=(1, None),
                    height=dp(120),
                    elevation=0
                )

                # Header with customer name and amount
                header_layout = MDBoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(30)
                )

                header_layout.add_widget(MDLabel(
                    text=f"[b]{customer_name}[/b]",
                    markup=True,
                    theme_text_color="Primary",
                    font_style="H6"
                ))

                header_layout.add_widget(MDLabel(
                    text=f"₱{amount:,.2f}",
                    halign="right",
                    theme_text_color="Primary",
                    font_style="H6"
                ))

                card.add_widget(header_layout)

                # Details
                details_layout = MDBoxLayout(
                    orientation='vertical',
                    spacing=dp(5)
                )

                details_layout.add_widget(MDLabel(
                    text=f"Date: {date[:10]} | Ref: {ref_no or 'N/A'}",
                    theme_text_color="Secondary",
                    font_style="Body2"
                ))

                details_layout.add_widget(MDLabel(
                    text=f"Outstanding Balance: ₱{balance:,.2f}",
                    theme_text_color="Secondary",
                    font_style="Body2"
                ))

                card.add_widget(details_layout)

                # Action button
                button_layout = MDBoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=dp(10)
                )

                record_payment_btn = MDFlatButton(
                    text="Record Payment",
                    size_hint=(None, None),
                    size=(dp(150), dp(36)),
                    md_bg_color=[0.2, 0.6, 0.2, 1],  # Green for payment action
                    text_color=[1, 1, 1, 1],  # White text
                    elevation=0,
                    on_release=lambda x, cid=customer_id, sid=sale_id, amt=amount: self.show_payment_dialog(cid, sid, amt, 'customer')
                )

                record_bad_debt_btn = MDFlatButton(
                    text="Record Bad Debt",
                    size_hint=(None, None),
                    size=(dp(150), dp(36)),
                    md_bg_color=[0.8, 0.2, 0.2, 1],  # Red color to indicate caution
                    text_color=[1, 1, 1, 1],  # White text
                    elevation=0,
                    on_release=lambda x, cid=customer_id, sid=sale_id, bal=balance: self.show_bad_debt_dialog(cid, sid, bal)
                )

                button_layout.add_widget(record_payment_btn)
                button_layout.add_widget(record_bad_debt_btn)
                card.add_widget(button_layout)

                layout.add_widget(card)

            scroll.add_widget(layout)
            customer_tab.add_widget(scroll)

        except Exception as e:
            print(f"Error updating customer payments display: {e}")

    def update_supplier_payments_display(self):
        """Update the display of supplier payments"""
        try:
            supplier_tab = self.ids.supplier_payments_tab
            supplier_tab.clear_widgets()

            if not self.supplier_payments_data:
                # Show empty state
                empty_layout = MDBoxLayout(
                    orientation='vertical',
                    padding=dp(20),
                    spacing=dp(10)
                )
                empty_layout.add_widget(MDLabel(
                    text="No outstanding supplier payments",
                    halign="center",
                    theme_text_color="Secondary"
                ))
                supplier_tab.add_widget(empty_layout)
                return

            # Create scrollable list
            scroll = MDScrollView()
            layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None)
            layout.bind(minimum_height=layout.setter('height'))

            for payment in self.supplier_payments_data:
                purchase_id, supplier_id, supplier_name, amount, date, ref_no, balance = payment

                # Create payment card
                card = MDCard(
                    orientation='vertical',
                    padding=dp(15),
                    size_hint=(1, None),
                    height=dp(120),
                    elevation=0
                )

                # Header with supplier name and amount
                header_layout = MDBoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(30)
                )

                header_layout.add_widget(MDLabel(
                    text=f"[b]{supplier_name}[/b]",
                    markup=True,
                    theme_text_color="Primary",
                    font_style="H6"
                ))

                header_layout.add_widget(MDLabel(
                    text=f"₱{amount:,.2f}",
                    halign="right",
                    theme_text_color="Primary",
                    font_style="H6"
                ))

                card.add_widget(header_layout)

                # Details
                details_layout = MDBoxLayout(
                    orientation='vertical',
                    spacing=dp(5)
                )

                details_layout.add_widget(MDLabel(
                    text=f"Date: {date[:10]} | Ref: {ref_no or 'N/A'}",
                    theme_text_color="Secondary",
                    font_style="Body2"
                ))

                details_layout.add_widget(MDLabel(
                    text=f"Outstanding Balance: ₱{balance:,.2f}",
                    theme_text_color="Secondary",
                    font_style="Body2"
                ))

                card.add_widget(details_layout)

                # Action button
                button_layout = MDBoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=dp(10)
                )

                record_payment_btn = MDFlatButton(
                    text="Record Payment",
                    size_hint=(None, None),
                    size=(dp(150), dp(36)),
                    md_bg_color=[0.2, 0.6, 0.2, 1],  # Green for payment action
                    text_color=[1, 1, 1, 1],  # White text
                    elevation=0,
                    on_release=lambda x, sid=supplier_id, pid=purchase_id, amt=amount: self.show_payment_dialog(sid, pid, amt, 'supplier')
                )

                button_layout.add_widget(record_payment_btn)
                card.add_widget(button_layout)

                layout.add_widget(card)

            scroll.add_widget(layout)
            supplier_tab.add_widget(scroll)

        except Exception as e:
            print(f"Error updating supplier payments display: {e}")

    def show_payment_dialog(self, entity_id, transaction_id, max_amount, payment_type):
        """Show dialog to record a payment"""
        self.payment_dialog = None

        # Create dialog content
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(200)
        )

        # Amount input
        amount_field = MDTextField(
            hint_text="Payment Amount",
            helper_text=f"Maximum: ₱{max_amount:,.2f}",
            input_filter='float',
            max_text_length=15
        )
        content.add_widget(amount_field)

        # Reference input
        ref_field = MDTextField(
            hint_text="Reference Number (Optional)",
            max_text_length=50
        )
        content.add_widget(ref_field)

        # Description input
        desc_field = MDTextField(
            hint_text="Description (Optional)",
            max_text_length=100
        )
        content.add_widget(desc_field)

        # Store references for validation
        self.payment_amount_field = amount_field
        self.payment_ref_field = ref_field
        self.payment_desc_field = desc_field
        self.payment_entity_id = entity_id
        self.payment_transaction_id = transaction_id
        self.payment_max_amount = max_amount
        self.payment_type = payment_type

        # Create dialog
        entity_name = "Customer" if payment_type == 'customer' else "Supplier"
        self.payment_dialog = MDDialog(
            title=f"Record {entity_name} Payment",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    md_bg_color=[0.7, 0.7, 0.7, 1],  # Gray for cancel
                    text_color=[1, 1, 1, 1],  # White text
                    on_release=lambda x: self.payment_dialog.dismiss()
                ),
                MDFlatButton(
                    text="RECORD PAYMENT",
                    md_bg_color=[0.2, 0.5, 0.8, 1],  # Blue for primary action
                    text_color=[1, 1, 1, 1],  # White text
                    elevation=0,
                    on_release=lambda x: self.record_payment()
                )
            ]
        )

        self.payment_dialog.open()

    def record_payment(self):
        """Record the payment after validation"""
        try:
            # Get input values
            amount_text = self.payment_amount_field.text.strip()
            ref_no = self.payment_ref_field.text.strip()
            description = self.payment_desc_field.text.strip()

            # Validate amount
            if not amount_text:
                self.show_error_dialog("Error", "Please enter a payment amount.")
                return

            try:
                amount = float(amount_text)
            except ValueError:
                self.show_error_dialog("Error", "Please enter a valid payment amount.")
                return

            if amount <= 0:
                self.show_error_dialog("Error", "Payment amount must be greater than zero.")
                return

            if amount > self.payment_max_amount:
                self.show_error_dialog("Error", f"Payment amount cannot exceed ₱{self.payment_max_amount:,.2f}.")
                return

            # Record the payment
            app = MDApp.get_running_app()

            if self.payment_type == 'customer':
                # Record customer payment
                app.db.record_customer_payment(
                    self.payment_entity_id,
                    amount,
                    ref_no if ref_no else None,
                    description if description else f"Payment for sale #{self.payment_transaction_id}"
                )
                self.show_success_dialog("Success", f"Customer payment of ₱{amount:,.2f} recorded successfully!")

            else:
                # Record supplier payment
                app.db.record_supplier_payment(
                    self.payment_entity_id,
                    amount,
                    ref_no if ref_no else None,
                    description if description else f"Payment for purchase #{self.payment_transaction_id}"
                )
                self.show_success_dialog("Success", f"Supplier payment of ₱{amount:,.2f} recorded successfully!")

            # Close dialog and refresh data
            self.payment_dialog.dismiss()
            self.load_customer_payments()
            self.load_supplier_payments()
            
            # Refresh ledger to show updated account balances
            try:
                ledger_screen = app.sm.get_screen('ledger')
                if ledger_screen:
                    ledger_screen.load_account_summary()
                    ledger_screen.update_ledger_stats()
                    print("Ledger refreshed after payment recording")
            except Exception as e:
                print(f"Error refreshing ledger: {e}")

        except Exception as e:
            print(f"Error recording payment: {e}")
            self.show_error_dialog("Error", f"Failed to record payment: {str(e)}")

    def show_error_dialog(self, title, message):
        """Show error dialog"""
        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    md_bg_color=[0.8, 0.2, 0.2, 1],  # Red for error
                    text_color=[1, 1, 1, 1],  # White text
                    elevation=0,
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def show_success_dialog(self, title, message):
        """Show success dialog"""
        dialog = MDDialog(
            title=title,
            text=message,
        buttons=[
                MDFlatButton(
                    text="OK",
                    md_bg_color=[0.2, 0.6, 0.2, 1],  # Green for success
                    text_color=[1, 1, 1, 1],  # White text
                    elevation=0,
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def show_bad_debt_dialog(self, customer_id, sale_id, outstanding_balance):
        """Show dialog to confirm bad debt write-off"""
        self.bad_debt_dialog = None

        # Create dialog content
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(150)
        )

        # Warning message
        warning_label = MDLabel(
            text=".",
            theme_text_color="Error",
            font_style="Body2",
            halign="center"
        )
        content.add_widget(warning_label)

        # Amount display (read-only)
        amount_field = MDTextField(
            hint_text="Amount to Write Off",
            text=f"₱{outstanding_balance:,.2f}",
            readonly=True,
            helper_text="Full outstanding balance will be written off"
        )
        content.add_widget(amount_field)

        # Description input
        desc_field = MDTextField(
            hint_text="Reason/Description (Optional)",
            max_text_length=100,
            helper_text="Brief explanation for the bad debt write-off"
        )
        content.add_widget(desc_field)

        # Store references for validation
        self.bad_debt_amount_field = amount_field
        self.bad_debt_desc_field = desc_field
        self.bad_debt_customer_id = customer_id
        self.bad_debt_sale_id = sale_id
        self.bad_debt_outstanding_balance = outstanding_balance

        # Create dialog
        self.bad_debt_dialog = MDDialog(
            title="Confirm Bad Debt Write-off",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    md_bg_color=[0.7, 0.7, 0.7, 1],  # Gray for cancel
                    text_color=[1, 1, 1, 1],  # White text
                    on_release=lambda x: self.bad_debt_dialog.dismiss()
                ),
                MDFlatButton(
                    text="CONFIRM WRITE-OFF",
                    md_bg_color=[0.8, 0.2, 0.2, 1],  # Red color for caution
                    text_color=[1, 1, 1, 1],  # White text
                    elevation=0,
                    on_release=lambda x: self.record_bad_debt()
                )
            ]
        )

        self.bad_debt_dialog.open()

    def record_bad_debt(self):
        """Record the bad debt write-off after confirmation"""
        try:
            # Get input values
            description = self.bad_debt_desc_field.text.strip()

            # Use the full outstanding balance for write-off
            amount = self.bad_debt_outstanding_balance

            # Additional validation
            if amount <= 0:
                self.show_error_dialog("Error", "Invalid amount for write-off.")
                return

            # Record the bad debt in database
            app = MDApp.get_running_app()
            app.db.record_bad_debt_write_off(
                self.bad_debt_customer_id,
                self.bad_debt_sale_id,
                amount,
                description or f"Bad debt write-off for sale #{self.bad_debt_sale_id}"
            )

            # Record in accounting ledger
            journal_entry_id = app.accounting.process_bad_debt_write_off(
                self.bad_debt_customer_id,
                self.bad_debt_sale_id,
                amount,
                description
            )

            if journal_entry_id:
                self.show_success_dialog(
                    "Bad Debt Recorded",
                    f"Bad debt write-off of ₱{amount:,.2f} recorded successfully!\n\nJournal Entry ID: #{journal_entry_id}"
                )
            else:
                self.show_error_dialog("Warning", "Bad debt recorded in database but accounting entry failed.")

            # Close dialog and refresh data
            self.bad_debt_dialog.dismiss()
            self.load_customer_payments()
            self.load_supplier_payments()
            
            # Also refresh the transactions screen if it exists to remove the written-off transaction
            try:
                transactions_screen = app.sm.get_screen('transactions')
                if transactions_screen:
                    transactions_screen.load_transactions()
                    print("Transactions screen refreshed after bad debt write-off")
            except Exception as e:
                print(f"Could not refresh transactions screen: {e}")

        except ValueError as e:
            self.show_error_dialog("Validation Error", str(e))
        except Exception as e:
            print(f"Error recording bad debt: {e}")
            self.show_error_dialog("Error", f"Failed to record bad debt: {str(e)}")

    def on_leave(self):
        """Clean up when leaving the screen - dismiss any open dialogs"""
        # Dismiss all payment dialogs if open
        dialogs_to_dismiss = ['payment_dialog', 'bad_debt_dialog']
        for dialog_name in dialogs_to_dismiss:
            if hasattr(self, dialog_name):
                dialog = getattr(self, dialog_name)
                if dialog:
                    try:
                        dialog.dismiss()
                    except:
                        pass  # Dialog might already be dismissed

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
        """Switch to specified screen with permission check"""
        app = MDApp.get_running_app()
        
        # Check if user has permission to access the screen
        if app.auth_manager and not app.auth_manager.can_access_screen(screen_name):
            from kivymd.uix.snackbar import Snackbar
            message = app.auth_manager.get_access_denied_message(screen=screen_name)
            Snackbar(text=message, duration=3).open()
            return
        
        app.sm.current = screen_name

    def go_back(self):
        """Navigate back to main screen"""
        app = MDApp.get_running_app()
        app.sm.current = 'main'
