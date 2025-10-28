# --- Imports ---
# Use only absolute imports for consistency and clarity
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.core.text import LabelBase
from datetime import datetime
from models.database import Database
from models.accounting_engine import AccountingEngine
from models.auth_manager import AuthManager
from screens.ledger_screen import LedgerScreen
from screens.inventory_screen import InventoryScreen
from screens.main_screen import MainScreen
from screens.transactions_screen import TransactionsScreen
from screens.reports_screen import ReportsScreen
from screens.payments_screen import PaymentsScreen
from screens.sales_report_screen import SalesReportScreen
from screens.login_screen import LoginScreen
from screens.user_management_screen import UserManagementScreen
from screens.financial_statements_screen import FinancialStatementsScreen
from screens.inventory_report_screen import InventoryReportScreen


# --- Helper function for safe widget access ---
def get_widget_safe(screen_manager, screen_name, widget_id):
    """
    Safely get a widget from a screen by name and widget id.
    Returns the widget if found, else None. Prevents AttributeError.
    """
    try:
        screen = screen_manager.get_screen(screen_name)
        widget = screen.ids.get(widget_id)
        if widget is None:
            print(f"Widget '{widget_id}' not found in screen '{screen_name}'")
        return widget
    except Exception as e:
        print(f"Error accessing widget '{widget_id}' in screen '{screen_name}': {e}")
        return None


# Register the custom font
try:
    LabelBase.register(name="Candice", fn_regular="assets/fonts/CANDY.TTF")
    LabelBase.register(name="Brico", fn_regular="assets/fonts/Brico.ttf")
except Exception as e:
    print(f"Font loading warning: {e}")
    # Continue without custom fonts


class RetailStoreManager(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart = {}  # Dictionary to store cart items: {product_id: {'product_data': product, 'quantity': count}}
        self.cart_total = 0  # Track cart total without tax
        self.cart_visible = False  # Track cart visibility
        self.db = Database()  # Initialize database
        self.accounting = AccountingEngine(self.db)  # Initialize accounting engine
        self.auth_manager = AuthManager(self.db)  # Initialize authentication manager
        self.products_data = []  # Store products data for easy access
        self.categories_data = []  # Cache categories for performance
        self.products_cache_timestamp = None  # Track last product cache update
        self.categories_cache_timestamp = None  # Track last category cache update

    def build(self):
        # Set the window size
        Window.size = (1920, 1080)


        # Create the screen manager
        self.sm = MDScreenManager()

        
        # Load all KV files
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/login.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/main.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/inventory.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/transactions.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/reports.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/ledger.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/payments.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/sales_report.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/user_management.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/financial_statements.kv')
        Builder.load_file('c:/Users/mateo/OneDrive/Desktop/python/msme - Copy/src/views/inventory_report.kv')
        
        # Add screens - login screen first
        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(InventoryScreen(name='inventory'))
        self.sm.add_widget(TransactionsScreen(name='transactions'))
        self.sm.add_widget(ReportsScreen(name='reports'))
        self.sm.add_widget(LedgerScreen(name='ledger'))
        self.sm.add_widget(PaymentsScreen(name='payments'))
        self.sm.add_widget(SalesReportScreen(name='sales_report'))
        self.sm.add_widget(UserManagementScreen(name='user_management'))
        self.sm.add_widget(FinancialStatementsScreen(name='financial_statements'))
        self.sm.add_widget(InventoryReportScreen(name='inventory_report'))
        
        # Load initial data (but don't try to update UI yet)
        self.load_products_data()
        
        # Set initial screen to login
        self.sm.current = 'login'
        
        # Schedule initial product loading for UI after everything is ready
        from kivy.clock import Clock
        Clock.schedule_once(self.delayed_product_load, 1.0)
        
        # Schedule session timer updates every second
        Clock.schedule_interval(self.update_session_timer, 1.0)
        
        return self.sm
    
    def delayed_product_load(self, dt):
        """Load products into UI after a delay to ensure UI is ready"""
        print("Loading products into UI...")
        self.load_products_from_db()
    
    def update_session_timer(self, dt):
        """Update session timer in the main screen"""
        try:
            if (self.auth_manager.is_authenticated() and 
                hasattr(self.sm, 'current') and 
                self.sm.current == 'main'):
                
                main_screen = self.sm.get_screen('main')
                if hasattr(main_screen.ids, 'session_time_label'):
                    session_duration = self.auth_manager.get_session_duration()
                    main_screen.ids.session_time_label.text = f"Session: {session_duration}"
        except Exception as e:
            # Silent fail - don't log every timer update error
            pass
    
    def require_authentication(self, action=None):
        """
        Decorator-style authentication check
        
        Args:
            action (str, optional): Specific action to check permission for
            
        Returns:
            bool: True if authenticated and authorized, False otherwise
        """
        if not self.auth_manager.is_authenticated():
            self.show_login_required_dialog()
            return False
        
        if action and not self.auth_manager.can_perform_action(action):
            self.show_permission_denied_dialog(action)
            return False
        
        return True
    
    def show_login_required_dialog(self):
        """Show login required dialog"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        
        dialog = MDDialog(
            title="Authentication Required",
            text="Please log in to access this feature.",
            buttons=[
                MDFlatButton(
                    text="Login",
                    theme_text_color="Custom",
                    text_color=[0.533, 0.620, 0.451, 1],
                    on_release=lambda x: [dialog.dismiss(), setattr(self.sm, 'current', 'login')]
                ),
                MDFlatButton(
                    text="Cancel",
                    theme_text_color="Custom",
                    text_color=[0.639, 0.114, 0.114, 1],
                    on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
        dialog.open()
    
    def show_permission_denied_dialog(self, action):
        """Show permission denied dialog"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        
        message = self.auth_manager.get_access_denied_message(action=action)
        
        dialog = MDDialog(
            title="Permission Denied",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=[0.639, 0.114, 0.114, 1],
                    on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
        dialog.open()
    
    def init_database_if_needed(self):
        """Check database status (sample data loading disabled)"""
        products = self.db.get_products()
        if not products:
            print("Database is empty - ready for your own data input!")
            print("Note: Automatic sample data loading has been disabled.")
            print("You can now add your own products through the Inventory screen.")
        else:
            print(f"Found {len(products)} existing products in database")
            # No automatic sample data loading anymore
    
    def load_products_data(self, force_refresh=False):
        """
        Load products data from database on startup or when forced.
        Uses caching to avoid unnecessary DB queries for performance.
        """
        import time
        now = time.time()
        # Refresh cache if forced or cache is old (>60s)
        if force_refresh or not self.products_cache_timestamp or (now - self.products_cache_timestamp > 60):
            try:
                self.products_data = self.db.get_products()
                self.products_cache_timestamp = now
                print(f"Loaded {len(self.products_data)} products from database (refreshed)")
            except Exception as e:
                print(f"Error loading products: {e}")
                self.products_data = []
        else:
            print(f"Using cached products ({len(self.products_data)})")

    def load_categories_data(self, force_refresh=False):
        """
        Load categories from database with caching for performance.
        """
        import time
        now = time.time()
        if force_refresh or not self.categories_cache_timestamp or (now - self.categories_cache_timestamp > 60):
            try:
                self.categories_data = self.db.get_categories()
                self.categories_cache_timestamp = now
                print(f"Loaded {len(self.categories_data)} categories from database (refreshed)")
            except Exception as e:
                print(f"Error loading categories: {e}")
                self.categories_data = []
        else:
            print(f"Using cached categories ({len(self.categories_data)})")

    def update_dashboard_stats(self):
        """Update dashboard statistics from database"""
        try:
            summary = self.get_database_summary()
            print(f"Dashboard stats - Sales: ₱{summary['sales']['total_revenue']:,.2f}, Inventory: ₱{summary['inventory_value']:,.2f}")
        except Exception as e:
            print(f"Error updating dashboard: {e}")
        
    def add_to_cart(self, product, price):
        """Add a product to the cart (legacy method for hardcoded products)"""
        # Create a unique ID for legacy products (using product name as ID)
        product_id = f"legacy_{product.replace(' ', '_').lower()}"
        
        if product_id in self.cart:
            self.cart[product_id]['quantity'] += 1
            print(f"Increased quantity: {product} - Qty: {self.cart[product_id]['quantity']}")
        else:
            self.cart[product_id] = {
                'product_data': {
                    "product_id": product_id,
                    "product": product,
                    "price": price,
                    "cost_price": price * 0.7  # Assume 30% margin
                },
                'quantity': 1
            }
            print(f"Added to cart: {product} - ₱{price:,.2f}")
        
        self.cart_total += price

        # Show cart if it's not visible
        if not self.cart_visible:
            self.toggle_cart_visibility()

        # Update cart UI
        self.update_cart_ui()

    def add_to_cart_from_db(self, product):
        """Add a product from database to cart"""
        if product[5] <= 0:  # Check stock (quantity is at index 5)
            print(f"Product {product[1]} is out of stock!")
            return
            
        product_id = product[0]
        
        # Check if product already exists in cart
        if product_id in self.cart:
            # Check if we can add more (don't exceed stock)
            current_qty = self.cart[product_id]['quantity']
            if current_qty >= product[5]:  # Can't exceed available stock
                print(f"Cannot add more {product[1]} - maximum stock ({product[5]}) reached in cart!")
                return
            
            # Increase quantity
            self.cart[product_id]['quantity'] += 1
            self.cart_total += product[4]
            print(f"Increased quantity: {product[1]} - Qty: {self.cart[product_id]['quantity']}")
        else:
            # Add new item to cart
            self.cart[product_id] = {
                'product_data': {
                    "product_id": product[0],  # id
                    "name": product[1],        # name
                    "price": product[4],       # selling_price
                    "cost_price": product[3]   # cost_price
                },
                'quantity': 1
            }
            self.cart_total += product[4]
            print(f"Added to cart: {product[1]} - ₱{product[4]:,.2f}")
        
        # Show cart if not visible
        if not self.cart_visible:
            self.toggle_cart_visibility()
        
        # Update cart UI
        self.update_cart_ui()

    def update_cart_ui(self):
        """Update cart UI with current items and checkout button state"""
        try:
            from kivymd.uix.card import MDCard
            from kivymd.uix.label import MDLabel
            from kivymd.uix.boxlayout import MDBoxLayout
            from kivymd.uix.button import MDIconButton
            
            cart_list = self.root.get_screen('main').ids.cart_items
            cart_list.clear_widgets()
            
            for product_id, cart_item in self.cart.items():
                product_data = cart_item['product_data']
                quantity = cart_item['quantity']
                total_price = product_data['price'] * quantity
                
                # Create cart item card
                item_card = MDCard(
                    size_hint_y=None,
                    height="80dp",
                    padding="8dp",
                    md_bg_color=[0.95, 0.95, 0.95, 1],
                    elevation=0,
                    line_color=[0.8, 0.8, 0.8, 1],  # Light gray outline
                    line_width=1,
                    on_release=lambda x, pid=product_id: self.show_quantity_controls(pid)
                )
                
                item_layout = MDBoxLayout(
                    orientation="horizontal",
                    spacing="8dp"
                )
                
                # Product info
                info_layout = MDBoxLayout(
                    orientation="vertical",
                    size_hint_x=0.8
                )
                
                product_label = MDLabel(
                    text=f"{product_data['name']}",
                    theme_text_color="Primary",
                    font_style="Subtitle1",
                    size_hint_y=0.6
                )
                
                price_label = MDLabel(
                    text=f"₱{product_data['price']:,.2f} × {quantity} = ₱{total_price:,.2f}",
                    theme_text_color="Secondary",
                    font_style="Caption",
                    size_hint_y=0.4
                )
                
                info_layout.add_widget(product_label)
                info_layout.add_widget(price_label)
                
                # Quantity badge
                qty_layout = MDBoxLayout(
                    orientation="vertical",
                    size_hint_x=0.2
                )
                
                qty_label = MDLabel(
                    text=f"{quantity}",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=[0.639, 0.114, 0.114, 1],  # POS Red
                    font_style="H6",
                    bold=True
                )
                
                qty_layout.add_widget(qty_label)
                
                item_layout.add_widget(info_layout)
                item_layout.add_widget(qty_layout)
                item_card.add_widget(item_layout)
                
                cart_list.add_widget(item_card)
            
            self.update_cart_display()
        except Exception as e:
            print(f"Error updating cart UI: {e}")
        
    def get_product_icon(self, product):
        """Return appropriate icon for product"""
        product_lower = product.lower()
        if "iphone" in product_lower or "samsung" in product_lower:
            return "cellphone"
        elif "headphones" in product_lower:
            return "headphones"
        elif "jeans" in product_lower or "t-shirt" in product_lower:
            return "tshirt-crew"
        elif "book" in product_lower:
            return "book"
        elif "garden" in product_lower or "tools" in product_lower:
            return "hammer-screwdriver"
        else:
            return "shopping"
        
    def toggle_cart_visibility(self):
        """Toggle the visibility of the shopping cart"""
        try:
            cart_widget = self.root.get_screen('main').ids.cart_widget
            if self.cart and not self.cart_visible:  # If cart has items and is not visible
                cart_widget.opacity = 1
                cart_widget.size_hint_x = 0.25
                cart_widget.disabled = False
                self.cart_visible = True
            elif not self.cart:  # If cart is empty
                cart_widget.opacity = 0
                cart_widget.size_hint_x = 0
                cart_widget.disabled = True
                self.cart_visible = False
        except Exception as e:
            print(f"Error toggling cart visibility: {e}")
            
    def remove_from_cart(self, product_id):
        """Remove an item completely from the cart"""
        if product_id not in self.cart:
            return
            
        cart_item = self.cart[product_id]
        product_data = cart_item['product_data']
        quantity = cart_item['quantity']
        
        # Update total
        self.cart_total -= product_data['price'] * quantity
        
        # Remove from cart
        del self.cart[product_id]
        
        # Hide cart if empty
        if not self.cart:
            self.toggle_cart_visibility()
        
        # Update UI
        self.update_cart_ui()
        self.close_quantity_dialog()
            
        print(f"Removed {product_data.get('name', product_data.get('product', 'Unknown Product'))} from cart")
        
    def get_product_stock(self, product_id):
        """Get current stock for a product"""
        try:
            product = self.db.get_product_by_id(product_id)
            return product[5] if product else 0  # quantity is at index 5
        except Exception as e:
            print(f"Error getting product stock: {e}")
            return 0

    def update_cart_display(self):
        """Update the cart total display and checkout button state"""
        try:
            cart_label = self.root.get_screen('main').ids.cart_total
            if hasattr(cart_label, 'text'):
                cart_label.text = f"Total: ₱ {self.cart_total:,.2f}"
            # Update checkout button state manually
            self.update_checkout_button_state()
            # Check if we need to hide the cart (when it becomes empty)
            if not self.cart:
                self.toggle_cart_visibility()
        except Exception as e:
            print(f"Error updating cart display: {e}")

    def update_checkout_button_state(self):
        """Update the checkout button enabled/disabled state based on cart contents"""
        try:
            main_screen = self.root.get_screen('main')
            checkout_button = main_screen.ids.get('checkout_button')
            if checkout_button:
                # Enable checkout button if cart has items, disable if empty
                checkout_button.disabled = len(self.cart) == 0
                # Update button appearance
                if len(self.cart) == 0:
                    checkout_button.md_bg_color = [0.7, 0.7, 0.7, 1]  # Gray when disabled
                    checkout_button.text_color = [0.5, 0.5, 0.5, 1]  # Gray text when disabled
                else:
                    checkout_button.md_bg_color = [0.831, 0.686, 0.216, 1]  # Gold when enabled (from KV)
                    checkout_button.text_color = [0.5, 0.2, 0, 1]  # Dark brown text when enabled
                print(f"Checkout button updated: disabled={checkout_button.disabled}, color={checkout_button.md_bg_color}")
        except Exception as e:
            print(f"Error updating checkout button state: {e}")

    # Widget access: show user-friendly message if widget missing
    def get_widget_or_notify(self, screen_name, widget_id):
        """
        Get widget by id, show user-friendly message if missing.
        Returns widget or None.
        """
        try:
            screen = self.root.get_screen(screen_name)
            widget = screen.ids.get(widget_id)
            if widget is None:
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text=f"Widget '{widget_id}' not found in '{screen_name}' screen.", duration=3).open()
            return widget
        except Exception as e:
            print(f"Error accessing widget '{widget_id}' in screen '{screen_name}': {e}")
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text=f"Error accessing widget '{widget_id}' in '{screen_name}'.", duration=3).open()
            return None

    def show_quantity_controls(self, product_id):
        """Show dialog to adjust quantity or remove item"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        
        if product_id not in self.cart:
            return
            
        cart_item = self.cart[product_id]
        product_data = cart_item['product_data']
        current_qty = cart_item['quantity']
        
        content = MDBoxLayout(
            orientation="vertical",
            spacing="16dp",
            size_hint_y=None,
            height="150dp"
        )
        
        # Product info
        content.add_widget(MDLabel(
            text=f"{product_data.get('name', product_data.get('product', 'Unknown Product'))}",
            theme_text_color="Primary",
            font_style="H6"
        ))
        
        # Quantity controls
        qty_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="16dp",
            size_hint_y=None,
            height="40dp"
        )
        
        # Decrease button
        decrease_btn = MDIconButton(
            icon="minus-circle",
            theme_icon_color="Custom",
            icon_color=[0.8, 0.2, 0.2, 1],
            on_release=lambda x: self.adjust_quantity(product_id, -1)
        )
        
        # Quantity label
        qty_label = MDLabel(
            text=f"Qty: {current_qty}",
            halign="center",
            theme_text_color="Primary",
            font_style="H6"
        )
        
        # Increase button
        increase_btn = MDIconButton(
            icon="plus-circle",
            theme_icon_color="Custom",
            icon_color=[0.2, 0.7, 0.2, 1],
            on_release=lambda x: self.adjust_quantity(product_id, 1)
        )
        
        qty_layout.add_widget(decrease_btn)
        qty_layout.add_widget(qty_label)
        qty_layout.add_widget(increase_btn)
        content.add_widget(qty_layout)
        
        self.quantity_dialog = MDDialog(
            title="Adjust Quantity",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="REMOVE",
                    theme_text_color="Custom",
                    text_color=[0.8, 0.2, 0.2, 1],
                    on_release=lambda x: self.remove_from_cart(product_id)
                ),
                MDRaisedButton(
                    text="DONE",
                    md_bg_color=[0.533, 0.620, 0.451, 1],
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1],
                    on_release=lambda x: self.close_quantity_dialog()
                ),
            ],
        )
        
        # Store references for updating
        self.current_qty_label = qty_label
        self.current_product_id = product_id
        
        self.quantity_dialog.open()
    
    def close_quantity_dialog(self):
        """Close the quantity dialog and clear references"""
        if hasattr(self, 'quantity_dialog') and self.quantity_dialog:
            self.quantity_dialog.dismiss()
        # Clear references
        if hasattr(self, 'current_qty_label'):
            delattr(self, 'current_qty_label')
        if hasattr(self, 'current_product_id'):
            delattr(self, 'current_product_id')
    
    def adjust_quantity(self, product_id, change):
        """Adjust the quantity of an item in the cart"""
        if product_id not in self.cart:
            return
            
        cart_item = self.cart[product_id]
        new_quantity = cart_item['quantity'] + change
        
        if new_quantity <= 0:
            self.remove_from_cart(product_id)
            return
            
        # Check stock availability
        product_data = cart_item['product_data']
        available_stock = self.get_product_stock(product_data['product_id'])
        
        if new_quantity > available_stock:
            print(f"Cannot increase quantity - only {available_stock} in stock")
            return
            
        # Update quantity and total
        old_quantity = cart_item['quantity']
        cart_item['quantity'] = new_quantity
        price_change = (new_quantity - old_quantity) * product_data['price']
        self.cart_total += price_change
        
        # Update UI
        self.update_cart_ui()
        
        # Update quantity dialog if open
        if hasattr(self, 'quantity_dialog') and self.quantity_dialog and hasattr(self, 'current_qty_label'):
            self.current_qty_label.text = f"Qty: {new_quantity}"
            self.current_qty_label.canvas.ask_update()
            
        print(f"Updated {product_data.get('name', product_data.get('product', 'Unknown Product'))} quantity to {new_quantity}")
    
    def checkout_with_selected_payment(self):
        """
        Enhanced POS checkout functionality with comprehensive payment method detection
        
        Key Features:
        1. Detects which payment method is selected from radio buttons
        2. Validates cart contents and payment selection
        3. Provides detailed error handling for edge cases
        4. Falls back to cash payment if detection fails
        5. Optimized for POS performance requirements
        
        Error Handling:
        - Empty cart validation
        - Payment method detection failure
        - UI component access errors
        - Database connection issues
        
        Performance Optimizations:
        - Single UI access per checkout
        - Minimal database queries
        - Fast payment type detection
        - Efficient error recovery
        """
        try:
            # VALIDATION: Check if cart has items before processing
            if not self.cart or len(self.cart) == 0:
                self.show_checkout_error("Cart is empty! Please add items before checkout.", "warning")
                return False
            
            # VALIDATION: Verify cart total is positive
            if self.cart_total <= 0:
                self.show_checkout_error("Invalid cart total! Please refresh the cart.", "error")
                return False
            
            # PAYMENT DETECTION: Get the main screen to access radio button states
            main_screen = self.root.get_screen('main')
            
            # Check if UI components exist (edge case handling)
            if not hasattr(main_screen, 'ids'):
                print("Warning: UI components not ready, defaulting to cash payment")
                return self.checkout('cash')
            
            # Access payment selection checkboxes with error handling
            try:
                cash_radio = main_screen.ids.cash_radio
                ar_radio = main_screen.ids.ar_radio
            except AttributeError as e:
                print(f"Warning: Payment selection UI not found ({e}), defaulting to cash")
                return self.checkout('cash')
            
            # PAYMENT TYPE DETECTION: Determine which payment method is selected
            payment_type = None
            payment_display_name = None
            
            # Primary detection: Check radio button states
            if hasattr(cash_radio, 'active') and cash_radio.active:
                payment_type = 'cash'
                payment_display_name = 'Cash Payment'
                print("Cash payment method detected and selected")
            elif hasattr(ar_radio, 'active') and ar_radio.active:
                payment_type = 'credit'
                payment_display_name = 'Accounts Receivable Payment'
                print("Accounts Receivable payment method detected and selected")
            else:
                # Edge case: No selection detected (should not happen with proper UI)
                payment_type = 'cash'
                payment_display_name = 'Cash Payment (Default)'
                print("No payment method detected, defaulting to cash payment")
            
            # LOG: Payment processing start
            print(f"\nPOS CHECKOUT INITIATED")
            print(f"   Payment Method: {payment_display_name}")
            print(f"   Cart Items: {len(self.cart)} products")
            print(f"   Total Amount: ₱{self.cart_total:,.2f}")
            print(f"   Processing Type: {payment_type}")
            
            # PROCESS: Execute the checkout with detected payment type
            checkout_success = self.checkout(payment_type)
            
            if checkout_success:
                # UI FEEDBACK: Reset payment selection to cash for next transaction
                try:
                    cash_radio.active = True
                    ar_radio.active = False
                    print("Payment selection reset to cash for next transaction")
                except:
                    print("⚠️ Could not reset payment selection (non-critical)")
                
                return True
            else:
                return False
            
        except Exception as e:
            # CRITICAL ERROR HANDLING: Comprehensive error recovery
            error_msg = f"Critical error during checkout: {str(e)}"
            print(f"{error_msg}")
            
            # Show user-friendly error message
            self.show_checkout_error(
                "Checkout failed due to a system error. Please try again or contact support.",
                "error"
            )
            
            # Attempt fallback to cash payment if cart is valid
            try:
                if self.cart and self.cart_total > 0:
                    print("Attempting fallback to cash payment...")
                    return self.checkout('cash')
            except:
                print("Fallback checkout also failed")
            
            return False
    
    def show_checkout_error(self, message, error_type="info"):
        """
        Display user-friendly checkout error messages
        
        Args:
            message (str): Error message to display
            error_type (str): Type of error - 'info', 'warning', 'error'
        """
        try:
            from kivymd.uix.snackbar import Snackbar
            snackbar = Snackbar(duration=5)
            snackbar.text = message
            snackbar.open()
            
        except Exception as e:
            # Fallback: Print to console if snackbar fails
            print(f"CHECKOUT MESSAGE: {message}")
            print(f"Note: Could not display snackbar ({e})")
    
    def checkout(self, payment_type='cash'):

        # VALIDATION PHASE: Comprehensive input validation
        if not self.cart:
            print("CHECKOUT FAILED: Cart is empty - cannot process checkout")
            self.show_checkout_error("Cart is empty! Please add items before checkout.", "warning")
            return False
            
        # Validate payment type with comprehensive checking
        valid_payment_types = ['cash', 'credit']
        if payment_type not in valid_payment_types:
            print(f"CHECKOUT FAILED: Invalid payment type '{payment_type}'. Must be one of: {valid_payment_types}")
            self.show_checkout_error(f"Invalid payment type: {payment_type}. Defaulting to cash.", "warning")
            payment_type = 'cash'  # Fallback to cash
            
        # Edge case: Validate cart total
        if self.cart_total <= 0:
            print("CHECKOUT FAILED: Invalid cart total (≤ 0)")
            self.show_checkout_error("Invalid cart total. Please refresh your cart.", "error")
            return False
            
        # Edge case: Validate cart items have valid data
        try:
            for product_id, cart_item in self.cart.items():
                if not cart_item.get('product_data') or not cart_item.get('quantity'):
                    print(f"CHECKOUT FAILED: Invalid cart item data for product {product_id}")
                    self.show_checkout_error("Invalid item in cart. Please refresh and try again.", "error")
                    return False
        except Exception as e:
            print(f"CHECKOUT FAILED: Cart validation error: {e}")
            self.show_checkout_error("Cart validation failed. Please refresh your cart.", "error")
            return False
            
        # AUTHENTICATION CHECK: Verify user can create sales
        if not self.require_authentication('create'):
            return False
        
        # � PROCESSING PHASE: Start checkout processing
        payment_display_name = "Cash" if payment_type == 'cash' else "A/R"
        print(f"\n ENHANCED POS CHECKOUT PROCESSING")
        print(f"Payment Method: {payment_display_name} ({payment_type})")
        print(f"Cart Items: {len(self.cart)} products")
        print(f"Total Amount: ₱{self.cart_total:,.2f}")
        print(f"Transaction Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"User: {self.auth_manager.get_current_user()['username']} ({self.auth_manager.get_current_role()})")
            
        try:
            # DATABASE PHASE: Prepare items for sale creation with validation
            sale_items = []
            total_cost = 0
            
            for product_id, cart_item in self.cart.items():
                product_data = cart_item['product_data']
                quantity = cart_item['quantity']
                
                # Validate product data integrity
                required_fields = ['product_id', 'price', 'name']
                if not all(key in product_data for key in required_fields):
                    missing_fields = [key for key in required_fields if key not in product_data]
                    print(f"Warning: Product {product_id} missing fields: {missing_fields}")
                    print(f"Available fields: {list(product_data.keys())}")
                    
                    # Try to use available data or reasonable defaults
                    if 'product_id' not in product_data:
                        product_data['product_id'] = product_id
                    if 'name' not in product_data:
                        product_data['name'] = f"Product {product_id}"
                    if 'price' not in product_data:
                        print(f"Critical: Product {product_id} has no price data")
                        raise ValueError(f"Product {product_id} has no price information")
                
                # Validate quantity
                if quantity <= 0:
                    raise ValueError(f"Invalid quantity {quantity} for product {product_data['name']}")
                
                # Calculate item cost for accounting
                unit_cost = product_data.get('cost_price', product_data['price'] * 0.6)  # Fallback cost estimation
                total_cost += unit_cost * quantity
                
                sale_items.append({
                    'product_id': product_data['product_id'],
                    'quantity': quantity,
                    'unit_price': product_data['price'],
                    'product_name': product_data['name']  # For logging
                })
            
            print(f"Items prepared: {len(sale_items)} products")
            print(f"Estimated COGS: ₱{total_cost:,.2f}")
            
            # CREATE SALE: Store sale in database with enhanced error handling
            reference_no = datetime.now().strftime("%Y%m%d%H%M%S")
            
            sale_id = self.db.create_sale(
                items=sale_items,
                customer_id=None,  # Walk-in customer (could be enhanced for A/R with customer selection)
                payment_type=payment_type,  # Store the selected payment type for transaction display
                reference_no=reference_no
            )
            
            if not sale_id:
                print("CHECKOUT FAILED: Database sale creation failed")
                self.show_checkout_error("Failed to create sale record. Please try again.", "error")
                return False
            
            #  SUCCESS LOGGING: Sale created successfully
            transaction_type = "Cash Sale" if payment_type == 'cash' else "Credit Sale (A/R)"
            print(f"{transaction_type} #{sale_id} created successfully")
            print(f"   Reference: {reference_no}")
            print(f"   Total: ₱{self.cart_total:,.2f}")
            
            # 📚 ACCOUNTING PHASE: Process automatic double-entry accounting
            print(f"\n📚 PROCESSING {payment_type.upper()} ACCOUNTING ENTRIES...")
            
            journal_entry_id = self.accounting.process_sales_transaction(
                sale_id=sale_id,
                sale_items=sale_items,
                total_amount=self.cart_total,
                payment_type=payment_type  # Pass payment type for correct account selection
            )
            
            if journal_entry_id:
                print(f"{payment_type.title()} accounting entries recorded")
                print(f"   Journal Entry ID: #{journal_entry_id}")
                
                # AUDIT LOGGING: Log the sale transaction
                current_user = self.auth_manager.get_current_user()
                sale_summary = f"Sale #{sale_id}: {len(sale_items)} items, Total: ₱{self.cart_total:,.2f}, Payment: {payment_type}"
                self.auth_manager.log_action(
                    "PROCESS_SALE", 
                    "sales", 
                    sale_id,
                    None,
                    sale_summary
                )
                
                # BALANCE REPORTING: Show updated account balances based on payment type
                try:
                    if payment_type == 'cash':
                        cash_balance = self.accounting.get_account_balance('Cash')
                        print(f"\nUPDATED CASH ACCOUNT BALANCES:")
                        print(f"   Cash Account: ₱{cash_balance:,.2f}")
                    else:  # credit/accounts receivable
                        ar_balance = self.accounting.get_account_balance('Accounts Receivable')
                        print(f"\nUPDATED A/R ACCOUNT BALANCES:")
                        print(f"   Accounts Receivable: ₱{ar_balance:,.2f}")
                    
                    # Common account balances for both payment types
                    sales_balance = self.accounting.get_account_balance('Sales Revenue')
                    inventory_balance = self.accounting.get_account_balance('Inventory')
                    cogs_balance = self.accounting.get_account_balance('Cost of Goods Sold')
                    
                    print(f"   Sales Revenue: ₱{sales_balance:,.2f}")
                    print(f"   Inventory: ₱{inventory_balance:,.2f}")
                    print(f"   Cost of Goods Sold: ₱{cogs_balance:,.2f}")
                    
                except Exception as balance_error:
                    print(f"⚠️ Warning: Could not retrieve account balances: {balance_error}")
                
                # UI REFRESH PHASE: Update all relevant screens
                print(f"\nREFRESHING UI COMPONENTS...")
                try:
                    self.refresh_transactions_screen()
                    print("   Transactions screen refreshed")
                except Exception as e:
                    print(f"   ⚠️ Transactions screen refresh failed: {e}")
                
                try:
                    self.refresh_inventory_screen()
                    print("   Inventory screen refreshed")
                except Exception as e:
                    print(f"   ⚠️ Inventory screen refresh failed: {e}")
                    
            else:
                print(f"⚠️ WARNING: {payment_type.title()} accounting entries failed to process")
                self.show_checkout_error("Sale completed but accounting entries failed. Please verify in reports.", "warning")
            
            # 💾 CART CLEANUP PHASE: Store checkout total before clearing for success messages
            checkout_total = self.cart_total
            item_count = len(self.cart)
            
            # Clear cart state
            self.cart = {}
            self.cart_total = 0
            
            print(f"\nCART CLEANUP COMPLETED")
            print(f"   🗑️ Cleared {item_count} items from cart")
            print(f"   Processed total: ₱{checkout_total:,.2f}")
            
            # UI UPDATE PHASE: Refresh product displays and cart UI
            try:
                # Refresh products to update stock display
                self.load_products_from_db()
                print("   Product stock displays updated")
                
                # Clear cart display components
                cart_list = self.root.get_screen('main').ids.cart_items
                cart_list.clear_widgets()
                print("   Cart UI cleared")
                
                # Update cart total display
                self.update_cart_display()
                print("   Cart display updated")
                
                # Update dashboard statistics
                self.update_dashboard_stats()
                print("   Dashboard stats updated")
                
            except Exception as ui_error:
                print(f"   ⚠️ UI update warning: {ui_error}")
            
            # SUCCESS PHASE: Show payment-specific success messages
            if payment_type == 'cash':
                success_message = f"Cash sale completed! ₱{checkout_total:,.2f} received"
                console_message = f"CASH CHECKOUT COMPLETED SUCCESSFULLY"
            else:
                success_message = f"Credit sale completed! ₱{checkout_total:,.2f} added to A/R"
                console_message = f"ACCOUNTS RECEIVABLE CHECKOUT COMPLETED SUCCESSFULLY"
                
            print(f"\n{console_message}")
            print(f"   Amount: ₱{checkout_total:,.2f}")
            print(f"   Sale ID: #{sale_id}")
            print(f"   Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show user-friendly success notification
            try:
                from kivymd.uix.snackbar import Snackbar
                snackbar = Snackbar(duration=4)
                snackbar.text = success_message
                snackbar.open()
            except Exception as snackbar_error:
                print(f"   ⚠️ Success message display failed: {snackbar_error}")
            
            return True  # Checkout completed successfully
                
        except Exception as e:
            # ERROR HANDLING PHASE: Comprehensive error recovery
            error_message = f"Checkout processing error: {str(e)}"
            print(f"\nCHECKOUT PROCESSING FAILED")
            print(f"   Error: {error_message}")
            print(f"   Payment Method: {payment_type}")
            print(f"   Cart Total: ₱{self.cart_total:,.2f}")
            print(f"   Error Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show user-friendly error message
            self.show_checkout_error(
                f"Checkout failed: {str(e)}. Please try again or contact support.",
                "error"
            )
            
            return False  # Checkout failed
    
    def process_expense(self, expense_type, amount, description, payment_type='cash'):
        """Process business expense with automatic accounting"""
        journal_entry_id = self.accounting.process_expense_transaction(
            expense_type=expense_type,
            amount=amount,
            description=description,
            payment_type=payment_type
        )
        
        if journal_entry_id:
            print(f"Expense recorded: {description} - ₱{amount:,.2f}")
            return journal_entry_id
        else:
            print(f"Failed to record expense: {description}")
            return None
    
    def process_inventory_purchase(self, purchase_items, total_amount, payment_type='cash', supplier_id=None):
        """Process inventory purchase with automatic accounting"""
        purchase_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create database purchase record if it's a credit purchase or has a supplier
        db_purchase_id = None
        if payment_type == 'credit' or supplier_id:
            # Convert purchase_items format for database
            db_items = []
            for item in purchase_items:
                db_items.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'unit_cost': item.get('unit_cost', item.get('cost_price', 0))
                })
            
            db_purchase_id = self.db.create_purchase(
                items=db_items,
                supplier_id=supplier_id,
                payment_type=payment_type,
                reference_no=f"PUR-{purchase_id}"
            )
            
            if db_purchase_id:
                print(f"Database purchase record created: ID #{db_purchase_id}")
            else:
                print("Warning: Failed to create database purchase record")
        
        journal_entry_id = self.accounting.process_inventory_purchase(
            purchase_id=purchase_id,
            purchase_items=purchase_items,
            total_amount=total_amount,
            payment_type=payment_type
        )
        
        if journal_entry_id:
            print(f"Inventory purchase recorded: Purchase #{purchase_id} - ₱{total_amount:,.2f}")
            return journal_entry_id
        else:
            print(f"Failed to record inventory purchase")
            return None
    
    def view_trial_balance(self):
        """Display trial balance report"""
        print("\n" + "="*80)
        print("TRIAL BALANCE REPORT")
        print("="*80)
        
        trial_balance = self.accounting.get_trial_balance()
        total_debits = 0
        total_credits = 0
        
        print(f"{'Code':<6} {'Account Name':<30} {'Type':<10} {'Balance':<15}")
        print("-" * 80)
        
        for account in trial_balance:
            code, name, acc_type, balance = account
            
            if acc_type in ['asset', 'expense']:
                # Normal debit balance accounts
                if balance >= 0:
                    debit_balance = balance
                    credit_balance = 0
                else:
                    debit_balance = 0
                    credit_balance = abs(balance)
            else:
                # Normal credit balance accounts (liability, equity, revenue)
                if balance >= 0:
                    debit_balance = 0
                    credit_balance = balance
                else:
                    debit_balance = abs(balance)
                    credit_balance = 0
            
            total_debits += debit_balance
            total_credits += credit_balance
            
            balance_str = f"₱{abs(balance):>10,.2f} {'DR' if debit_balance > 0 else 'CR' if credit_balance > 0 else ''}"
            print(f"{code:<6} {name:<30} {acc_type:<10} {balance_str:<15}")
        
        print("-" * 80)
        print(f"{'TOTALS':<47} ₱{total_debits:>10,.2f} DR  ₱{total_credits:>10,.2f} CR")
        
        if abs(total_debits - total_credits) < 0.01:
            print("Trial Balance is BALANCED")
        else:
            print(f"Trial Balance is OUT OF BALANCE by ₱{abs(total_debits - total_credits):,.2f}")
        
        print("="*80)
    
    def view_account_balance(self, account_name):
        """View specific account balance"""
        balance = self.accounting.get_account_balance(account_name)
        print(f"{account_name}: ₱{balance:,.2f}")
        return balance
    
    def demo_accounting_functions(self):
        """Demo method to showcase accounting functionality"""
        print("\n🎯 ACCOUNTING SYSTEM DEMO")
        print("="*60)
        
        # Demo 1: Process some expenses
        print("\n1️⃣ Recording Business Expenses:")
        self.process_expense('rent', 15000, 'Monthly store rent', 'cash')
        self.process_expense('utilities', 2500, 'Electricity bill', 'cash')
        self.process_expense('office_supplies', 800, 'Office supplies', 'cash')
        
        # Demo 2: Process inventory purchase
        print("\n2️⃣ Recording Inventory Purchase:")
        purchase_items = [{'product_name': 'General Inventory', 'cost': 25000}]
        self.process_inventory_purchase(purchase_items, 25000, 'cash')
        
        # Demo 3: Show account balances
        print("\n3️⃣ Current Account Balances:")
        key_accounts = ['Cash', 'Sales Revenue', 'Inventory', 'Cost of Goods Sold', 'Operating Expenses']
        for account in key_accounts:
            self.view_account_balance(account)
        
        # Demo 4: Show trial balance
        print("\n4️⃣ Trial Balance:")
        self.view_trial_balance()
    
    def refresh_transactions_screen(self):
        """Refresh the transactions screen if it's available"""
        try:
            # Check if transactions screen exists
            transactions_screen = None
            for screen in self.sm.screens:
                if screen.name == 'transactions':
                    transactions_screen = screen
                    break
            
            if transactions_screen and hasattr(transactions_screen, 'load_transactions'):
                # If the transactions screen is currently active, refresh it
                if self.sm.current == 'transactions':
                    transactions_screen.load_transactions()
                    print("Transactions screen refreshed")
        except Exception as e:
            print(f"Note: Could not refresh transactions screen: {e}")
    
    def refresh_inventory_screen(self):
        """Refresh the inventory screen if it's available"""
        try:
            # Check if inventory screen exists
            inventory_screen = None
            for screen in self.sm.screens:
                if screen.name == 'inventory':
                    inventory_screen = screen
                    break
            
            if inventory_screen and hasattr(inventory_screen, 'load_inventory'):
                # If the inventory screen is currently active, refresh it
                if self.sm.current == 'inventory':
                    inventory_screen.load_inventory()
                    print("Inventory screen refreshed")
        except Exception as e:
            print(f"Note: Could not refresh inventory screen: {e}")

    def load_products_from_db(self, category_id=None):
        """Load products from database and display in UI"""
        products = self.db.get_products(category_id=category_id)
        self.products_data = products  # Store for easy access
        
        # Clear current products display
        try:
            # Try to get the products grid
            main_screen = self.root.get_screen('main')
            if not hasattr(main_screen, 'ids') or 'products_grid' not in main_screen.ids:
                print("Products grid not found, UI may not be ready yet")
                return
                
            products_grid = main_screen.ids.products_grid
            products_grid.clear_widgets()
            
            # Add products to grid
            for product in products:
                from kivymd.uix.card import MDCard
                from kivymd.uix.label import MDLabel
                from kivymd.uix.boxlayout import MDBoxLayout
                
                # Create product card
                card = MDCard(
                    orientation="vertical",
                    padding="8dp",
                    size_hint_y=None,
                    height="200dp",
                    ripple_behavior=True,
                    md_bg_color=[1, 1, 1, 1],
                    elevation=0,
                    line_color=[0.639, 0.114, 0.114, 0.3],  # Red outline with transparency
                    line_width=1,
                    on_release=lambda x, p=product: self.add_to_cart_from_db(p)
                )
                
                layout = MDBoxLayout(orientation='vertical', padding="8dp", spacing="4dp")
                
                # Product name
                name_label = MDLabel(
                    text=product[1],  # product name
                    halign="center",
                    theme_text_color="Primary",
                    font_style="Subtitle1",
                    text_size=(None, None)
                )
                
                # Product price
                price_label = MDLabel(
                    text=f"₱{product[4]:,.2f}",  # selling_price
                    halign="center",
                    theme_text_color="Primary",
                    font_style="H6"
                )
                
                # Stock info
                stock_color = "Error" if product[5] <= product[6] else "Secondary"  # quantity <= reorder_level
                stock_label = MDLabel(
                    text=f"Stock: {product[5]}",  # quantity
                    halign="center",
                    theme_text_color=stock_color,
                    font_style="Caption"
                )
                
                layout.add_widget(name_label)
                layout.add_widget(price_label)
                layout.add_widget(stock_label)
                card.add_widget(layout)
                
                products_grid.add_widget(card)
                
            print(f"Loaded {len(products)} products to UI")
            
        except Exception as e:
            print(f"Error loading products to UI: {e}")
            # Fallback: just print products
            for product in products:
                print(f"Product: {product[1]} - ₱{product[4]:.2f} (Stock: {product[5]})")

    def load_categories_to_ui(self):
        """Load categories from database and create category buttons dynamically"""
        try:
            # Get the main screen
            main_screen = self.root.get_screen('main')
            if not hasattr(main_screen, 'ids') or 'dynamic_categories_container' not in main_screen.ids:
                print("Categories container not found, UI may not be ready yet")
                return
                
            categories_container = main_screen.ids.dynamic_categories_container
            categories_container.clear_widgets()
            
            # Get categories from database
            categories = self.db.get_categories()
            
            if len(categories) == 0:
                # Show a message when no categories exist
                from kivymd.uix.label import MDLabel
                no_categories_label = MDLabel(
                    text="No categories yet. Add categories in Inventory Management.",
                    theme_text_color="Secondary",
                    halign="center",
                    size_hint_y=None,
                    height="40dp"
                )
                categories_container.add_widget(no_categories_label)
                return
            
            # Create category buttons dynamically
            for category in categories:
                from kivymd.uix.card import MDCard
                from kivymd.uix.label import MDLabel
                from kivymd.uix.boxlayout import MDBoxLayout
                
                category_id, category_name = category[0], category[1]
                
                # Create category card
                card = MDCard(
                    size_hint_y=None,
                    height="120dp",
                    ripple_behavior=True,
                    padding="8dp"
                )
                
                # Set up click event
                card.bind(on_release=lambda x, cat_name=category_name: main_screen.switch_category(cat_name))
                
                # Create layout for card content
                layout = MDBoxLayout(
                    orientation='vertical',
                    spacing="4dp"
                )
                
                # Add generic category icon (fallback to emoji if image missing)
                name_label = MDLabel(
                    text=f"{category_name}",  # Category folder emoji with name
                    halign="center",
                    size_hint_y=1.0,
                    theme_text_color="Primary",
                    font_style="Body1"
                )
                
                # Add widgets to layout
                layout.add_widget(name_label)
                card.add_widget(layout)
                
                # Add card to container
                categories_container.add_widget(card)
                
            print(f"Loaded {len(categories)} categories to UI")
            
        except Exception as e:
            print(f"Error loading categories to UI: {e}")
                
    def get_database_summary(self):
        """Get comprehensive database summary for reporting"""
        summary = {
            'cash_flow': self.db.get_cash_flow_summary(),
            'sales': self.db.get_sales_summary(),
            'inventory_value': self.db.get_inventory_value(),
            'low_stock_count': len(self.db.get_low_stock_products()),
            'categories': len(self.db.get_categories()),
            'products': len(self.db.get_products()),
            'customers': len(self.db.get_customers()),
            'suppliers': len(self.db.get_suppliers())
        }
        return summary

    def update_dashboard_stats(self):
        """Update dashboard statistics across all screens"""
        try:
            current_screen = self.sm.current
            screen = self.sm.get_screen(current_screen)
            
            # Check if the current screen has an update_dashboard_stats method
            if hasattr(screen, 'update_dashboard_stats') and callable(getattr(screen, 'update_dashboard_stats')):
                screen.update_dashboard_stats()
            else:
                # Fallback: just print stats
                stats = self.db.get_dashboard_stats()
                print(f"Dashboard stats - Sales: ₱{stats['total_sales']:,.2f}, COGS: ₱{stats['cost_of_goods_sold']:,.2f}, Gross Profit: ₱{stats['gross_profit']:,.2f}, Low Stock: {stats['low_stock_count']}")
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
    
    def get_current_date(self):
        """Get current date formatted for display"""
        try:
            return datetime.now().strftime('%B %d, %Y')
        except Exception as e:
            print(f"Error getting current date: {e}")
            return "Unknown Date"

if __name__ == '__main__':
    RetailStoreManager().run()