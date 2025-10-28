from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDFillRoundFlatButton
import time
import random

class InventoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_products = []  # Store current products for search
        
    def go_back(self):
        """Navigate back to main screen"""
        app = MDApp.get_running_app()
        app.sm.current = 'main'
        
    def on_enter(self):
        """Load inventory when screen is entered"""
        # Check authentication and permissions
        app = MDApp.get_running_app()
        if not app.auth_manager.can_access_screen('inventory'):
            # Redirect back to main screen with error message
            self.show_access_denied()
            app.sm.current = 'main'
            return
        
        # Log screen access
        app.auth_manager.log_action("ACCESS_INVENTORY", "navigation")
        
        self.load_inventory()
        self.update_stats()
        self.update_navigation_permissions()
    
    def show_access_denied(self):
        """Show access denied message"""
        app = MDApp.get_running_app()
        message = app.auth_manager.get_access_denied_message('inventory')
        
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=message, duration=3).open()
    
    def show_permission_denied(self, action):
        """Show permission denied message for specific action"""
        app = MDApp.get_running_app()
        message = app.auth_manager.get_access_denied_message(action=action)
        
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=message, duration=3).open()
    
    def load_inventory(self):
        """Load inventory data from database"""
        app = MDApp.get_running_app()
        products = app.db.get_products()
        self.current_products = products
        
        try:
            # Clear existing list
            product_list = self.ids.product_list
            product_list.clear_widgets()
            
            # Add products to list with enhanced UI
            for product in products:
                self.add_product_row(product, product_list)
                
            print(f"Loaded {len(products)} products to inventory screen")
            
        except Exception as e:
            print(f"Error loading inventory UI: {e}")
            # Fallback: print products
            for product in products:
                print(f"Inventory: {product[1]} - Stock: {product[5]} - Price: ₱{product[4]:,.2f}")
    
    def add_product_row(self, product, container):
        """Add a single product row to the inventory display"""

        # Determine stock status and color
        stock_level = product[5]  # quantity
        reorder_level = product[6]  # reorder_level
        
        if stock_level <= 0:
            stock_color = [0.427, 0.137, 0.137, 1]  # POS Dark Red for no stock
            stock_icon = ""
        elif stock_level <= reorder_level:
            stock_color = [0.831, 0.686, 0.216, 1]  # POS Gold for low stock
            stock_icon = ""
        else:
            stock_color = [0.533, 0.620, 0.451, 1]  # POS Green for good stock
            stock_icon = ""
        
        # Create product row card
        row_card = MDCard(
            size_hint_y=None,
            height="60dp",
            padding="8dp",
            md_bg_color=[1, 1, 1, 1],
            elevation=0,
            line_color=[0.9, 0.9, 0.9, 1],  # Light gray outline
            line_width=1
        )
        
        row_layout = MDBoxLayout(
            padding="8dp",
            spacing="8dp"
        )
        
        # Product name with status icon
        name_label = MDLabel(
            text=f"{stock_icon} {product[1]}",
            size_hint_x=0.25,
            theme_text_color="Primary"
        )
        
        # SKU
        sku_label = MDLabel(
            text=product[7] or "N/A",
            size_hint_x=0.15,
            theme_text_color="Secondary"
        )
        
        # Stock with color coding
        stock_label = MDLabel(
            text=str(stock_level),
            size_hint_x=0.12,
            halign="center",
            theme_text_color="Custom",
            text_color=stock_color,
            bold=True
        )
        
        # Cost price
        cost_label = MDLabel(
            text=f"₱{product[3]:,.2f}",
            size_hint_x=0.15,
            halign="right",
            theme_text_color="Secondary"
        )
        
        # Selling price
        price_label = MDLabel(
            text=f"₱{product[4]:,.2f}",
            size_hint_x=0.15,
            halign="right",
            theme_text_color="Primary",
            bold=True
        )
        
        # Action buttons
        actions_layout = MDBoxLayout(
            size_hint_x=0.18,
            spacing="4dp"
        )
        
        edit_btn = MDIconButton(
            icon="pencil",
            theme_icon_color="Custom",
            icon_color=[0.533, 0.620, 0.451, 1],  # POS Green
            on_release=lambda x, p=product: self.edit_product(p[0])
        )
        
        delete_btn = MDIconButton(
            icon="delete",
            theme_icon_color="Custom",
            icon_color=[0.427, 0.137, 0.137, 1],  # POS Dark Red
            on_release=lambda x, p=product: self.confirm_delete_product(p[0], p[1])
        )
        
        adjust_btn = MDIconButton(
            icon="tune",
            theme_icon_color="Custom",
            icon_color=[0.831, 0.686, 0.216, 1],  # POS Gold
            on_release=lambda x, p=product: self.adjust_stock(p[0], p[1])
        )
        
        actions_layout.add_widget(edit_btn)
        actions_layout.add_widget(adjust_btn)
        actions_layout.add_widget(delete_btn)
        
        # Add all elements to row
        row_layout.add_widget(name_label)
        row_layout.add_widget(sku_label)
        row_layout.add_widget(stock_label)
        row_layout.add_widget(cost_label)
        row_layout.add_widget(price_label)
        row_layout.add_widget(actions_layout)
        
        row_card.add_widget(row_layout)
        container.add_widget(row_card)
    
    def search_products(self, search_text):
        """Filter products based on search text"""
        if not search_text:
            self.load_inventory()
            return
        
        filtered_products = []
        search_lower = search_text.lower()
        
        for product in self.current_products:
            # Search in name and SKU only (no description anymore)
            if (search_lower in product[1].lower() or  # name
                (product[7] and search_lower in product[7].lower())):  # sku
                filtered_products.append(product)
        
        # Update display with filtered products
        try:
            product_list = self.ids.product_list
            product_list.clear_widgets()
            
            for product in filtered_products:
                self.add_product_row(product, product_list)
                
        except Exception as e:
            print(f"Error filtering products: {e}")
    
    def add_product(self):
        """Show add product dialog with comprehensive form fields"""
        self.add_product_dialog()
    


    def add_product_dialog(self):
        """
        Opens a KivyMD dialog with input fields for adding a new product.
        Includes validation, auto-generated SKU, and proper spacing.
        """
        
        # Scrollable content layout
        scroll_content = MDBoxLayout(
            orientation="vertical",
            spacing="12dp",
            size_hint_y=None,
            adaptive_height=True,
            padding="16dp"
        )

        # Product Name
        self.product_name_field = MDTextField(
            hint_text="Product Name *",
            required=True,
            helper_text="Enter the product name (required)",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )

        # Get categories from database
        app = MDApp.get_running_app()
        categories = app.db.get_categories()
        self.available_categories = {cat[1]: cat[0] for cat in categories}  # {name: id}

        # Category dropdown
        self.selected_category = None
        self.category_button = MDFillRoundFlatButton(
            text="Select Category *",
            size_hint_y=None,
            height="60dp",
            md_bg_color=[0.9, 0.9, 0.9, 1],
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 1]
        )
        
        # Create dropdown menu
        menu_items = []
        for category_name in self.available_categories.keys():
            menu_items.append({
                "text": category_name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=category_name: self.set_category(x),
            })
        
        self.category_dropdown = MDDropdownMenu(
            caller=self.category_button,
            items=menu_items,
            width_mult=4,
        )
        
        self.category_button.bind(on_release=self.category_dropdown.open)

        # Cost Price
        self.product_cost_field = MDTextField(
            hint_text="Cost Price *",
            required=True,
            input_filter="float",
            helper_text="Enter cost price in ₱ (numbers only)",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )

        # Selling Price
        self.product_selling_field = MDTextField(
            hint_text="Selling Price *",
            required=True,
            input_filter="float",
            helper_text="Enter selling price in ₱ (numbers only)",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )

        # Stock Quantity
        self.product_quantity_field = MDTextField(
            hint_text="Stock Quantity *",
            required=True,
            input_filter="int",
            text="0",
            helper_text="Enter initial stock quantity (numbers only)",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )

        # Generate SKU silently
        self.auto_sku = self.generate_auto_sku()

        # Reorder Level
        self.product_reorder_field = MDTextField(
            hint_text="Reorder Level",
            input_filter="int",
            text="10",
            helper_text="Minimum stock level for reorder alerts",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )

        # Add fields to content
        for widget in [
            self.product_name_field,
            self.category_button,
            self.product_cost_field,
            self.product_selling_field,
            self.product_quantity_field,
            self.product_reorder_field
        ]:
            scroll_content.add_widget(widget)



        # Scroll container
        scroll = MDScrollView(size_hint=(1, 1))
        scroll.add_widget(scroll_content)

        # Dialog
        self.product_dialog = MDDialog(
            type="custom",
            content_cls=scroll,
            size_hint=(0.9, 0.8),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=[0.5, 0.5, 0.5, 1],
                    on_release=self.close_product_dialog
                ),
                MDRaisedButton(
                    text="ADD PRODUCT",
                    md_bg_color=[0.639, 0.114, 0.114, 1],  # Example theme color
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1],
                    on_release=self.save_product
                ),
            ],
        )

        self.product_dialog.open()

    def set_product_name(self, product_name):
        """Set the selected product name and auto-fill fields if product exists"""
        self.selected_product_name = product_name
        if hasattr(self, 'name_field'):
            self.name_field.text = product_name

        # Check if product exists and auto-fill fields
        app = MDApp.get_running_app()
        existing_products = app.db.get_products()

        for prod in existing_products:
            if prod[1] == product_name:  # prod[1] is product name
                # Auto-fill all fields with existing data
                if hasattr(self, 'category_field'):
                    # Get category name from the product data
                    categories = app.db.get_categories()
                    category_name = None
                    for cat in categories:
                        if cat[0] == prod[2]:  # prod[2] is category_id, cat[0] is category id
                            category_name = cat[1]  # cat[1] is category name
                            break
                    if category_name:
                        self.category_field.text = category_name
                        self.selected_category = category_name

                # Auto-fill other fields if they exist
                if hasattr(self, 'cost_field'):
                    self.cost_field.text = str(prod[3]) if prod[3] else ""  # cost_price
                if hasattr(self, 'price_field'):
                    self.price_field.text = str(prod[4]) if prod[4] else ""  # selling_price
                if hasattr(self, 'quantity_field'):
                    self.quantity_field.text = "0"  # Set to 0 for restocking - user enters quantity to ADD
                if hasattr(self, 'reorder_field'):
                    self.reorder_field.text = str(prod[6]) if prod[6] else "5"  # reorder_level

                break

        self.product_name_dropdown.dismiss()

    def set_category(self, category_name):
        """Set the selected category and update the text field"""
        self.selected_category = category_name
        if hasattr(self, 'category_field'):
            self.category_field.text = category_name
        self.category_dropdown.dismiss()

    def generate_auto_sku(self):
        """
        Generate an automatic SKU in the format:
        PROD-YYYYMMDD-XXXX (XXXX = random 4-digit number).
        """
        timestamp = time.strftime("%Y%m%d")
        app = MDApp.get_running_app()
        existing_skus = app.db.get_all_skus()

        while True:
            random_suffix = f"{random.randint(1000, 9999)}"
            auto_sku = f"PROD-{timestamp}-{random_suffix}"
            if auto_sku not in existing_skus:
                return auto_sku

    def save_product(self, *args):
        """
        Validates form data and saves the new product to the database.
        Includes comprehensive validation and error handling.
        """
        try:
            # Validate all required fields
            validation_result = self.validate_product_fields()
            
            if not validation_result['is_valid']:
                self.show_validation_error(validation_result['errors'])
                return
            
            # Get validated data
            product_data = validation_result['data']
            
            # Save to database using parameterized query
            app = MDApp.get_running_app()
            product_id = app.db.add_product(
                name=product_data['name'],
                category_id=product_data['category_id'],
                cost_price=product_data['cost_price'],
                selling_price=product_data['selling_price'],
                quantity=product_data['quantity'],
                reorder_level=product_data['reorder_level'],
                sku=product_data['sku'],
                description=product_data['description']
            )
            
            if product_id:
                print(f"Product '{product_data['name']}' added successfully with ID: {product_id}")
                self.close_product_dialog()
                self.refresh_product_list()
                self.show_success_message(f"Product '{product_data['name']}' added successfully!")
            else:
                self.show_error_message("Failed to add product. SKU might already exist.")
                
        except Exception as e:
            print(f"Error saving product: {e}")
            self.show_error_message(f"An error occurred: {str(e)}")
    
    def validate_product_fields(self):
        """
        Validates all product form fields and returns validation result.
        Returns dict with 'is_valid', 'data', and 'errors' keys.
        """
        errors = []
        data = {}
        
        # Validate product name (required)
        name = self.product_name_field.text.strip()
        if not name:
            errors.append("Product name is required")
        elif len(name) < 2:
            errors.append("Product name must be at least 2 characters")
        else:
            data['name'] = name
        
        # Validate category (required)
        if not self.selected_category:
            errors.append("Category is required - please select from dropdown")
        else:
            category_id = self.available_categories.get(self.selected_category)
            if category_id:
                data['category_id'] = category_id
            else:
                errors.append("Invalid category selected")
        
        # Validate cost price (required, numeric, positive)
        try:
            cost_price = float(self.product_cost_field.text.strip())
            if cost_price < 0:
                errors.append("Cost price must be positive")
            else:
                data['cost_price'] = cost_price
        except (ValueError, TypeError):
            errors.append("Cost price must be a valid number")
        
        # Validate selling price (required, numeric, positive)
        try:
            selling_price = float(self.product_selling_field.text.strip())
            if selling_price < 0:
                errors.append("Selling price must be positive")
            else:
                data['selling_price'] = selling_price
        except (ValueError, TypeError):
            errors.append("Selling price must be a valid number")
        
        # Validate quantity (required, integer, non-negative)
        try:
            quantity = int(self.product_quantity_field.text.strip())
            if quantity < 0:
                errors.append("Quantity cannot be negative")
            else:
                data['quantity'] = quantity
        except (ValueError, TypeError):
            errors.append("Quantity must be a valid whole number")
        
        # Validate reorder level (optional, integer, non-negative)
        reorder_text = self.product_reorder_field.text.strip()
        if reorder_text:
            try:
                reorder_level = int(reorder_text)
                if reorder_level < 0:
                    errors.append("Reorder level cannot be negative")
                else:
                    data['reorder_level'] = reorder_level
            except (ValueError, TypeError):
                errors.append("Reorder level must be a valid whole number")
        else:
            data['reorder_level'] = 10  # Default value
        
        # Use auto-generated SKU
        data['sku'] = self.auto_sku
        
        # No description field anymore
        data['description'] = None
        
        return {
            'is_valid': len(errors) == 0,
            'data': data,
            'errors': errors
        }
    
    def get_or_create_category(self, category_name):
        """
        Gets category ID by name, or creates a new category if it doesn't exist.
        Returns category ID or None if creation fails.
        """
        app = MDApp.get_running_app()
        
        # First, try to get existing category
        category_id = app.db.get_category_id_by_name(category_name)
        
        if category_id:
            return category_id
        
        # If category doesn't exist, create it
        try:
            cursor = app.db.conn.cursor()
            cursor.execute(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                (category_name, f"Auto-created category: {category_name}")
            )
            app.db.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating category: {e}")
            return None
    
    def refresh_product_list(self):
        """
        Refreshes the product display on the current screen.
        Updates both inventory list and main screen if needed.
        """
        try:
            # Refresh current inventory screen
            self.load_inventory()
            
            # Update inventory statistics
            self.update_stats()
            
            # If main screen is available, refresh it too
            app = MDApp.get_running_app()
            if hasattr(app, 'sm') and app.sm:
                main_screen = app.sm.get_screen('main')
                if hasattr(main_screen, 'load_products_to_grid'):
                    main_screen.load_products_to_grid()
                if hasattr(main_screen, 'update_dashboard_stats'):
                    main_screen.update_dashboard_stats()
            
            print("Product list refreshed successfully")
            
        except Exception as e:
            print(f"Error refreshing product list: {e}")
    
    def close_product_dialog(self, *args):
        """Closes the product dialog"""
        if hasattr(self, 'product_dialog'):
            self.product_dialog.dismiss()
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.dismiss()
    
    def show_validation_error(self, errors):
        """Shows validation errors to the user"""
        from kivymd.uix.snackbar import Snackbar
        
        error_message = "Please fix the following errors:\n• " + "\n• ".join(errors)
        
        Snackbar(
            text=error_message,
            duration=4,
            bg_color=[0.8, 0.2, 0.2, 1]
        ).open()
    
    def show_success_message(self, message):
        """Shows success message to the user"""
        from kivymd.uix.snackbar import Snackbar
        
        Snackbar(
            text=message,
            duration=3,
            bg_color=[0.2, 0.6, 0.2, 1]
        ).open()
    
    def show_error_message(self, message):
        """Shows error message to the user"""
        from kivymd.uix.snackbar import Snackbar
        
        Snackbar(
            text=message,
            duration=4,
            bg_color=[0.8, 0.2, 0.2, 1]
        ).open()
    
    def edit_product(self, product_id):
        """Edit existing product"""
        app = MDApp.get_running_app()
        
        # Check permission
        if not app.auth_manager.can_perform_action('update'):
            self.show_permission_denied('update products')
            return
        
        product = app.db.get_product_by_id(product_id)
        
        if not product:
            print(f"Product {product_id} not found")
            return
        
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDRaisedButton, MDFlatButton
        from kivymd.uix.boxlayout import MDBoxLayout
        
        # Create form fields with current values
        content = MDBoxLayout(
            orientation="vertical",
            spacing="12dp",
            size_hint_y=None,
            height="400dp"
        )
        
        self.edit_name_field = MDTextField(hint_text="Product Name", text=product[1])
        self.edit_cost_field = MDTextField(hint_text="Cost Price", text=str(product[3]), input_filter="float")
        self.edit_price_field = MDTextField(hint_text="Selling Price", text=str(product[4]), input_filter="float")
        self.edit_quantity_field = MDTextField(hint_text="Quantity", text=str(product[5]), input_filter="int")
        self.edit_reorder_field = MDTextField(hint_text="Reorder Level", text=str(product[6]), input_filter="int")

        def set_payment_type(self, payment_type):
            self.selected_payment_type = payment_type



        content.add_widget(self.edit_name_field)
        content.add_widget(self.edit_cost_field)
        content.add_widget(self.edit_price_field)
        content.add_widget(self.edit_quantity_field)
        content.add_widget(self.edit_reorder_field)
        
        self.edit_dialog = MDDialog(
            title=f"Edit Product: {product[1]}",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.edit_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="UPDATE",
                    md_bg_color=[0.533, 0.620, 0.451, 1],  # POS Green
                    theme_text_color="Custom", 
                    text_color=[1, 1, 1, 1],
                    on_release=lambda x: self.save_edited_product(product_id)
                ),
            ],
        )
        self.edit_dialog.open()
    
    def save_edited_product(self, product_id):
        """Save edited product to database"""
        app = MDApp.get_running_app()
        
        try:
            # Update product in database
            success = app.db.update_product(
                product_id,
                name=self.edit_name_field.text,
                cost_price=float(self.edit_cost_field.text),
                selling_price=float(self.edit_price_field.text),
                quantity=int(self.edit_quantity_field.text),
                reorder_level=int(self.edit_reorder_field.text),
                sku=self.edit_sku_field.text if self.edit_sku_field.text else None,
                description=None  # No description field anymore
            )
            
            if success:
                print(f"Product updated successfully!")
                self.edit_dialog.dismiss()
                self.load_inventory()  # Refresh the list
                self.update_stats()
            else:
                print("Error updating product")
                
        except ValueError as e:
            print(f"Invalid input: {e}")
        except Exception as e:
            print(f"Error updating product: {e}")
    
    def confirm_delete_product(self, product_id, product_name):
        """Show confirmation dialog before deleting product"""
        app = MDApp.get_running_app()
        
        # Check permission
        if not app.auth_manager.can_perform_action('delete'):
            self.show_permission_denied('delete products')
            return
        
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton, MDFlatButton
        
        self.delete_dialog = MDDialog(
            title="Confirm Delete",
            text=f"Are you sure you want to delete '{product_name}'?\n\nThis action cannot be undone.",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.delete_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="DELETE",
                    md_bg_color=[0.427, 0.137, 0.137, 1],  # POS Dark Red
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1],
                    on_release=lambda x: self.delete_product(product_id)
                ),
            ],
        )
        self.delete_dialog.open()
    
    def delete_product(self, product_id):
        """Delete product from inventory"""
        app = MDApp.get_running_app()
        
        # Get product info before deletion for audit log
        product = app.db.get_product_by_id(product_id)
        product_name = product[1] if product else f"Product ID {product_id}"
        
        if app.db.delete_product(product_id):
            # Log the deletion
            app.auth_manager.log_action(
                "DELETE_PRODUCT", 
                "products", 
                product_id,
                f"Deleted product: {product_name}",
                None
            )
            
            self.delete_dialog.dismiss()
            self.load_inventory()  # Refresh list
            self.update_stats()
            print(f"Product {product_id} deleted successfully")
        else:
            print(f"Failed to delete product {product_id}")
    
    def adjust_stock(self, product_id, product_name):
        """Show stock adjustment dialog"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDRaisedButton, MDFlatButton
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.selectioncontrol import MDSelectionControl
        from kivymd.uix.label import MDLabel
        
        content = MDBoxLayout(
            orientation="vertical",
            spacing="12dp",
            size_hint_y=None,
            height="200dp"
        )
        
        content.add_widget(MDLabel(text=f"Adjust stock for: {product_name}"))
        
        self.adjustment_type = "increase"
        self.adjustment_quantity = MDTextField(hint_text="Quantity", input_filter="int")
        self.adjustment_reason = MDTextField(hint_text="Reason (Optional)")
        
        # Radio buttons for increase/decrease
        from kivymd.uix.gridlayout import MDGridLayout
        radio_layout = MDGridLayout(cols=2, size_hint_y=None, height="40dp")
        
        # These would be proper radio buttons in a full implementation
        increase_btn = MDRaisedButton(
            text="Increase",
            md_bg_color=[0.533, 0.620, 0.451, 1],  # POS Green
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=lambda x: setattr(self, 'adjustment_type', 'increase')
        )
        decrease_btn = MDRaisedButton(
            text="Decrease", 
            md_bg_color=[0.427, 0.137, 0.137, 1],  # POS Dark Red
            theme_icon_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=lambda x: setattr(self, 'adjustment_type', 'decrease')
        )
        
        radio_layout.add_widget(increase_btn)
        radio_layout.add_widget(decrease_btn)
        
        content.add_widget(radio_layout)
        content.add_widget(self.adjustment_quantity)
        content.add_widget(self.adjustment_reason)
        
        self.adjust_dialog = MDDialog(
            title="Stock Adjustment",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.adjust_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="ADJUST",
                    md_bg_color=[0.831, 0.686, 0.216, 1],  # POS Gold
                    theme_text_color="Custom",
                    text_color=[0.639, 0.114, 0.114, 1],  # POS Red text
                    on_release=lambda x: self.save_stock_adjustment(product_id)
                ),
            ],
        )
        self.adjust_dialog.open()
    
    def save_stock_adjustment(self, product_id):
        """Save stock adjustment to database"""
        app = MDApp.get_running_app()
        
        try:
            quantity = int(self.adjustment_quantity.text)
            reason = self.adjustment_reason.text or "Manual adjustment"
            
            success = app.db.add_inventory_adjustment(
                product_id=product_id,
                adjustment_type=self.adjustment_type,
                quantity=quantity,
                reason=reason
            )
            
            if success:
                print(f"Stock adjusted successfully!")
                self.adjust_dialog.dismiss()
                self.load_inventory()  # Refresh the list
                self.update_stats()
            else:
                print("Error adjusting stock")
                
        except ValueError:
            print("Please enter a valid quantity")
        except Exception as e:
            print(f"Error adjusting stock: {e}")
    
    def update_stats(self):
        """Update inventory statistics cards"""
        app = MDApp.get_running_app()
        
        try:
            # Calculate beginning inventory value
            beginning_inventory_value = 0
            beginning_inventory_count = 0
            
            # Get all inventory lots for beginning inventory (purchase_id is NULL)
            cursor = app.db.conn.cursor()
            cursor.execute("""
            SELECT il.quantity_remaining, il.cost_per_unit, pr.name
            FROM inventory_lots il
            JOIN products pr ON il.product_id = pr.id
            WHERE il.purchase_id IS NULL
            """)
            
            beginning_lots = cursor.fetchall()
            for lot in beginning_lots:
                beginning_inventory_value += lot[0] * lot[1]  # quantity_remaining * cost_per_unit
                beginning_inventory_count += lot[0]
            
            # Calculate purchases value
            purchases_value = 0
            purchases_count = 0
            
            cursor.execute("""
            SELECT il.quantity_remaining, il.cost_per_unit, pr.name
            FROM inventory_lots il
            JOIN products pr ON il.product_id = pr.id
            WHERE il.purchase_id IS NOT NULL
            """)
            
            purchase_lots = cursor.fetchall()
            for lot in purchase_lots:
                purchases_value += lot[0] * lot[1]  # quantity_remaining * cost_per_unit
                purchases_count += lot[0]
            
            # Calculate purchase returns value
            purchase_returns_value = 0
            purchase_returns_count = 0
            
            cursor.execute("""
            SELECT pr.quantity, pr.unit_cost
            FROM purchase_returns pr
            """)
            
            purchase_returns = cursor.fetchall()
            for pr in purchase_returns:
                purchase_returns_value += pr[0] * pr[1]  # quantity * unit_cost
                purchase_returns_count += pr[0]
            
            # Calculate sales returns value
            sales_returns_value = 0
            sales_returns_count = 0
            
            cursor.execute("""
            SELECT sr.quantity, sr.unit_price
            FROM sales_returns sr
            """)
            
            sales_returns = cursor.fetchall()
            for sr in sales_returns:
                sales_returns_value += sr[0] * sr[1]  # quantity * unit_price
                sales_returns_count += sr[0]
            
            # Calculate total available for sale
            total_available_value = app.db.get_total_available_for_sale()
            
            # Update UI labels
            self.ids.beginning_inventory_amount_label.text = f"₱{beginning_inventory_value:,.2f}"
            self.ids.beginning_inventory_label.text = f"{beginning_inventory_count} items"
            
            self.ids.purchases_amount_label.text = f"₱{purchases_value:,.2f}"
            self.ids.purchases_label.text = f"{purchases_count} items"
            
            self.ids.purchase_returns_label.text = f"₱{purchase_returns_value:,.2f}"
            self.ids.sales_returns_label.text = f"₱{sales_returns_value:,.2f}"
            
            self.ids.total_available_label.text = f"₱{total_available_value:,.2f}"
            
            print(f"Inventory stats updated - Beginning: ₱{beginning_inventory_value:,.2f} ({beginning_inventory_count} items), Purchases: ₱{purchases_value:,.2f} ({purchases_count} items), Sales Returns: ₱{sales_returns_value:,.2f}, Total Available: ₱{total_available_value:,.2f}")
            
        except Exception as e:
            print(f"Error updating inventory stats: {e}")
            # Set default values
            self.ids.beginning_inventory_amount_label.text = "₱0.00"
            self.ids.beginning_inventory_label.text = "No data"
            self.ids.purchases_amount_label.text = "₱0.00"
            self.ids.purchases_label.text = "No data"
            self.ids.purchase_returns_label.text = "₱0.00"
            self.ids.sales_returns_label.text = "₱0.00"
            self.ids.total_available_label.text = "₱0.00"
    def add_product(self):
        """Show add product dialog"""
        self.show_product_dialog()
    
    def edit_product(self, product_id):
        """Show edit product dialog"""
        app = MDApp.get_running_app()
        product = app.db.get_product_by_id(product_id)
        if product:
            self.show_product_dialog(product)
        else:
            print(f"Product with ID {product_id} not found")
    
    def show_product_dialog(self, product=None):
        """Show add/edit product dialog with improved UI"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        from kivymd.uix.gridlayout import MDGridLayout
        
        is_edit = product is not None
        
        # Get categories for dropdown
        app = MDApp.get_running_app()
        categories = app.db.get_categories()
        
        # Main container with card styling
        main_content = MDCard(
            orientation="vertical",
            spacing="16dp",
            size_hint_y=None,
            height="600dp",  # Fixed height instead of adaptive
            padding="24dp",
            elevation=0,
            md_bg_color=[1, 1, 1, 1],  # White background
            radius=[12, 12, 12, 12]
        )
        
        # Header section with icon and title
        header_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="12dp",
            size_hint_y=None,
            height="48dp",
            adaptive_height=True
        )
        
        # Header icon
        header_icon = MDIconButton(
            icon="package-variant-closed" if not is_edit else "pencil",
            theme_icon_color="Custom",
            icon_color=[0.2, 0.6, 0.2, 1],  # Green color
            icon_size="32dp",
            disabled=True
        )
        
        # Header title
        header_title = MDLabel(
            text=f"[size=20][b]{'Edit Product' if is_edit else 'Add New Product'}[/b][/size]",
            markup=True,
            theme_text_color="Primary",
            size_hint_y=None,
            height="48dp",
            valign="middle"
        )
        
        header_layout.add_widget(header_icon)
        header_layout.add_widget(header_title)
        main_content.add_widget(header_layout)
        
        # Form container
        form_container = MDBoxLayout(
            orientation="vertical",
            spacing="16dp",
            size_hint_y=None,
            adaptive_height=True
        )
        
        # Product Name with dropdown and manual entry
        name_container = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="68dp",
            adaptive_height=True
        )
        
        name_icon = MDIconButton(
            icon="tag-text",
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 1],
            icon_size="24dp",
            disabled=True,
            size_hint_x=None,
            width="40dp"
        )
        
        # Product name dropdown button
        self.selected_product_name = None
        self.product_name_button = MDFillRoundFlatButton(
            text="Select",
            size_hint_x=0.3,
            size_hint_y=None,
            height="56dp",
            md_bg_color=[0.9, 0.9, 0.9, 1],
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 1]
        )
        
        # Manual product name entry field
        self.name_field = MDTextField(
            hint_text="Or enter product name manually",
            text=product[1] if is_edit else "",
            multiline=False,
            size_hint_x=0.7,
            size_hint_y=None,
            height="56dp",
            mode="rectangle",
            helper_text="Select from dropdown or type new product name",
            helper_text_mode="on_focus"
        )
        
        # Get existing products for dropdown
        app = MDApp.get_running_app()
        existing_products = app.db.get_products()
        
        # Create dropdown menu with existing product names
        product_menu_items = []
        for prod in existing_products:
            product_name = prod[1]  # product name
            product_menu_items.append({
                "text": product_name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=product_name: self.set_product_name(x),
            })
        
        self.product_name_dropdown = MDDropdownMenu(
            caller=self.product_name_button,
            items=product_menu_items,
            width_mult=4,
        )
        
        self.product_name_button.bind(on_release=lambda x: self.product_name_dropdown.open())
        
        # If editing, set the current product name
        if is_edit and product[1]:
            self.selected_product_name = product[1]
            self.name_field.text = product[1]
        
        name_container.add_widget(name_icon)
        name_container.add_widget(self.product_name_button)
        name_container.add_widget(self.name_field)
        form_container.add_widget(name_container)
        
        # Category with dropdown and manual entry
        category_container = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="68dp",
            adaptive_height=True
        )
        
        category_icon = MDIconButton(
            icon="shape",
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 1],
            icon_size="24dp",
            disabled=True,
            size_hint_x=None,
            width="40dp"
        )
        
        # Category dropdown button
        self.selected_category = None
        self.category_button = MDFillRoundFlatButton(
            text="Select",
            size_hint_x=0.3,
            size_hint_y=None,
            height="56dp",
            md_bg_color=[0.9, 0.9, 0.9, 1],
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 1]
        )
        
        # Manual category entry field
        self.category_field = MDTextField(
            hint_text="Or enter category manually",
            text=product[2] if is_edit else "",
            multiline=False,
            size_hint_x=0.7,
            size_hint_y=None,
            height="56dp",
            mode="rectangle",
            helper_text="Select from dropdown or type new category",
            helper_text_mode="on_focus"
        )
        
        # Create dropdown menu with existing categories
        menu_items = []
        for category in categories:
            category_name = category[1]  # category name
            menu_items.append({
                "text": category_name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=category_name: self.set_category(x),
            })
        
        self.category_dropdown = MDDropdownMenu(
            caller=self.category_button,
            items=menu_items,
            width_mult=4,
        )
        
        self.category_button.bind(on_release=lambda x: self.category_dropdown.open())
        
        # If editing, set the current category
        if is_edit and product[2]:
            self.selected_category = product[2]
            self.category_field.text = product[2]
        
        category_container.add_widget(category_icon)
        category_container.add_widget(self.category_button)
        category_container.add_widget(self.category_field)
        form_container.add_widget(category_container)
        
        # Price section with grid layout
        price_grid = MDGridLayout(
            cols=2,
            spacing="12dp",
            size_hint_y=None,
            adaptive_height=True
        )
        
        # Cost Price
        cost_container = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="68dp",
            adaptive_height=True
        )
        
        cost_icon = MDIconButton(
            icon="currency-php",
            theme_icon_color="Custom",
            icon_color=[0.8, 0.4, 0.4, 1],  # Red for cost
            icon_size="24dp",
            disabled=True,
            size_hint_x=None,
            width="40dp"
        )
        
        self.cost_field = MDTextField(
            hint_text="Cost Price",
            text=str(product[3]) if is_edit else "",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height="56dp",
            mode="rectangle",
            helper_text="Purchase price",
            helper_text_mode="on_focus"
        )
        
        cost_container.add_widget(cost_icon)
        cost_container.add_widget(self.cost_field)
        
        # Selling Price
        price_container = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="68dp",
            adaptive_height=True
        )
        
        price_icon = MDIconButton(
            icon="currency-php",
            theme_icon_color="Custom",
            icon_color=[0.2, 0.6, 0.2, 1],  # Green for selling
            icon_size="24dp",
            disabled=True,
            size_hint_x=None,
            width="40dp"
        )
        
        self.price_field = MDTextField(
            hint_text="Selling Price",
            text=str(product[4]) if is_edit else "",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height="56dp",
            mode="rectangle",
            helper_text="Retail price",
            helper_text_mode="on_focus"
        )
        
        price_container.add_widget(price_icon)
        price_container.add_widget(self.price_field)
        
        price_grid.add_widget(cost_container)
        price_grid.add_widget(price_container)
        form_container.add_widget(price_grid)
        
        # Inventory section with grid layout
        inventory_grid = MDGridLayout(
            cols=2,
            spacing="12dp",
            size_hint_y=None,
            adaptive_height=True
        )
        
        # Quantity
        qty_container = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="68dp",
            adaptive_height=True
        )
        
        qty_icon = MDIconButton(
            icon="cube-outline",
            theme_icon_color="Custom",
            icon_color=[0.2, 0.4, 0.8, 1],  # Blue for quantity
            icon_size="24dp",
            disabled=True,
            size_hint_x=None,
            width="40dp"
        )
        
        self.quantity_field = MDTextField(
            hint_text="Stock Quantity",
            text=str(product[5]) if is_edit else "0",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height="56dp",
            mode="rectangle",
            helper_text="Current stock",
            helper_text_mode="on_focus"
        )
        
        qty_container.add_widget(qty_icon)
        qty_container.add_widget(self.quantity_field)
        
        # Reorder Level
        reorder_container = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="68dp",
            adaptive_height=True
        )
        
        reorder_icon = MDIconButton(
            icon="alert-circle-outline",
            theme_icon_color="Custom",
            icon_color=[0.8, 0.6, 0.2, 1],  # Orange for alert
            icon_size="24dp",
            disabled=True,
            size_hint_x=None,
            width="40dp"
        )
        
        self.reorder_field = MDTextField(
            hint_text="Reorder Level",
            text=str(product[6]) if is_edit else "5",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height="56dp",
            mode="rectangle",
            helper_text="Low stock alert",
            helper_text_mode="on_focus"
        )
        
        reorder_container.add_widget(reorder_icon)
        reorder_container.add_widget(self.reorder_field)
        
        inventory_grid.add_widget(qty_container)
        inventory_grid.add_widget(reorder_container)
        form_container.add_widget(inventory_grid)
        
        # Beginning Inventory Checkbox (only for new products)
        if not is_edit:
            from kivymd.uix.selectioncontrol import MDCheckbox
            
            beginning_inventory_container = MDBoxLayout(
                orientation="horizontal",
                spacing="12dp",
                size_hint_y=None,
                height="68dp",
                adaptive_height=True
            )
            
            beginning_inventory_icon = MDIconButton(
                icon="checkbox-marked-circle",
                theme_icon_color="Custom",
                icon_color=[0.2, 0.6, 0.2, 1],  # Green for beginning inventory
                icon_size="24dp",
                disabled=True,
                size_hint_x=None,
                width="40dp"
            )
            
            checkbox_layout = MDBoxLayout(
                orientation="horizontal",
                spacing="8dp",
                size_hint_y=None,
                height="48dp"
            )
            
            self.beginning_inventory_checkbox = MDCheckbox(
                size_hint=(None, None),
                size=("32dp", "32dp"),
                active=False
            )
            
            checkbox_label = MDLabel(
                text="Record as Beginning Inventory",
                theme_text_color="Primary",
                size_hint_y=None,
                height="48dp",
                halign="left",
                valign="center"
            )
            checkbox_label.bind(texture_size=checkbox_label.setter('text_size'))
            
            checkbox_layout.add_widget(self.beginning_inventory_checkbox)
            checkbox_layout.add_widget(checkbox_label)
            
            beginning_inventory_container.add_widget(beginning_inventory_icon)
            beginning_inventory_container.add_widget(checkbox_layout)
            
            form_container.add_widget(beginning_inventory_container)
        
        main_content.add_widget(form_container)

        # Payment options
        payment_options_container = MDBoxLayout(
            orientation="vertical",
            spacing="12dp",
            size_hint_y=None,
            height="120dp",
            adaptive_height=True
        )
        
        # Payment type header
        payment_header = MDLabel(
            text="Select Payment Type:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        
        # Selected payment display
        self.selected_payment_label = MDLabel(
            text="[b]Selected: Cash[/b]",
            markup=True,
            theme_text_color="Custom",
            text_color=[0.2, 0.6, 0.2, 1],  # Green for cash
            font_style="Body1",
            size_hint_y=None,
            height="25dp"
        )
        
        self.selected_payment_type = "cash"  # Default
        
        def set_payment_type(payment_type):
            self.selected_payment_type = payment_type
            # Update display label
            if payment_type == "cash":
                self.selected_payment_label.text = "[b]Selected: Cash[/b]"
                self.selected_payment_label.text_color = [0.2, 0.6, 0.2, 1]  # Green
            else:
                self.selected_payment_label.text = "[b]Selected: Credit[/b]"
                self.selected_payment_label.text_color = [0.8, 0.6, 0.2, 1]  # Orange
                
            # Update button appearances
            update_button_styles()
        
        def update_button_styles():
            if self.selected_payment_type == "cash":
                cash_btn.md_bg_color = [0.2, 0.6, 0.2, 1]  # Bright green
                cash_btn.elevation = 0
                credit_btn.md_bg_color = [0.5, 0.5, 0.5, 1]  # Gray
                credit_btn.elevation = 0
            else:
                cash_btn.md_bg_color = [0.5, 0.5, 0.5, 1]  # Gray
                cash_btn.elevation = 0
                credit_btn.md_bg_color = [0.8, 0.6, 0.2, 1]  # Bright orange
                credit_btn.elevation = 0
        
        self.set_payment_type = set_payment_type
        
        # Button container
        button_container = MDBoxLayout(
            orientation="horizontal",
            spacing="16dp",
            size_hint_y=None,
            height="50dp"
        )
        
        cash_btn = MDRaisedButton(
            text="Cash",
            md_bg_color=[0.2, 0.6, 0.2, 1],
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            elevation=0,  # Start selected
            size_hint_x=0.5,
            on_release=lambda x: self.set_payment_type("cash")
        )
        credit_btn = MDRaisedButton(
            text="A/P",
            md_bg_color=[0.5, 0.5, 0.5, 1],  # Start unselected
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            elevation=0,  # Start unselected
            size_hint_x=0.5,
            on_release=lambda x: self.set_payment_type("credit")
        )
        
        button_container.add_widget(cash_btn)
        button_container.add_widget(credit_btn)
        
        payment_options_container.add_widget(payment_header)
        payment_options_container.add_widget(self.selected_payment_label)
        payment_options_container.add_widget(button_container)
        main_content.add_widget(payment_options_container)

        
        # Dialog actions
        def save_product(instance):
            try:
                # Validate input
                if not self.name_field.text.strip():
                    print("Product name is required")
                    return
                
                if not self.cost_field.text or not self.price_field.text:
                    print("Cost price and selling price are required")
                    return
                
                # Prepare data
                product_data = {
                    'name': self.name_field.text.strip(),
                    'category_name': self.selected_category or self.category_field.text.strip() or 'General',
                    'cost_price': float(self.cost_field.text),
                    'selling_price': float(self.price_field.text),
                    'quantity': int(self.quantity_field.text) if self.quantity_field.text else 0,
                    'reorder_level': int(self.reorder_field.text) if self.reorder_field.text else 5,
                    'sku': product[7] if is_edit else self.generate_auto_sku(),  # Keep existing SKU for edits, auto-generate for new
                    'description': None  # No description field anymore
                }
                payment_type = self.selected_payment_type
                if is_edit:
                    # ...existing edit logic...
                    pass
                else:
                    # Check if product already exists
                    existing_product = app.db.get_product_by_name(product_data['name'])
                    
                    if existing_product:
                        # Product exists - restock existing product
                        print(f"Restocking existing product '{product_data['name']}' with {product_data['quantity']} units")
                        
                        # Check if beginning inventory checkbox is checked
                        is_beginning_inventory = hasattr(self, 'beginning_inventory_checkbox') and self.beginning_inventory_checkbox.active
                        
                        # Only create database purchase record if NOT beginning inventory
                        db_purchase_id = None
                        if not is_beginning_inventory:
                            db_purchase_items = [{
                                'product_id': existing_product[0],
                                'quantity': product_data['quantity'],
                                'unit_cost': product_data['cost_price']
                            }]
                            
                            db_purchase_id = app.db.create_purchase(
                                items=db_purchase_items,
                                supplier_id=None,  # No supplier specified in inventory screen
                                payment_type=payment_type,
                                reference_no=f"STOCK-UP-{existing_product[0]}"
                            )
                            
                            if db_purchase_id:
                                print(f"Database purchase record created for stock increase: ID #{db_purchase_id}")
                        else:
                            print(f"Beginning inventory restock - no purchase record created")
                        
                        # Create inventory lot for FIFO costing
                        # For beginning inventory: purchase_id = None
                        # For regular purchases: purchase_id = actual purchase record ID
                        lot_id = app.db.add_inventory_lot(
                            product_id=existing_product[0],
                            purchase_id=db_purchase_id,  # None for beginning inventory, purchase ID for regular purchases
                            quantity=product_data['quantity'],
                            cost_per_unit=product_data['cost_price']
                        )
                        
                        if lot_id:
                            print(f"Created inventory lot #{lot_id} for FIFO costing")
                        
                        # Sync product quantities to ensure accuracy
                        app.db.sync_product_quantities_with_inventory_lots()
                        
                        # Process accounting for stock increase (purchase)
                        if product_data['quantity'] > 0:
                                total_cost = product_data['cost_price'] * product_data['quantity']
                                
                                app.accounting.process_inventory_purchase(
                                    purchase_id=f"STOCK-UP-{existing_product[0]}",
                                    purchase_items=[{
                                        'product_name': product_data['name'],
                                        'cost': total_cost
                                    }],
                                    total_amount=total_cost,
                                    payment_type=payment_type,
                                    is_beginning_inventory=is_beginning_inventory  # Now respects the checkbox!
                                )
                        else:
                            print(f"Failed to update stock for product '{product_data['name']}'")
                            return
                    else:
                        # Product doesn't exist - create new product
                        category_id = app.db.get_category_id_by_name(product_data['category_name'])
                        if not category_id:
                            category_id = app.db.add_category(product_data['category_name'])
                        product_id = app.db.add_product(
                            name=product_data['name'],
                            category_id=category_id,
                            cost_price=product_data['cost_price'],
                            selling_price=product_data['selling_price'],
                            quantity=0,  # Always start with 0, let inventory lots manage quantity
                            reorder_level=product_data['reorder_level'],
                            sku=product_data['sku'],
                            description=product_data['description']
                        )
                        if product_id:
                            print(f"Product '{product_data['name']}' added successfully")
                            
                            # Check if beginning inventory checkbox is checked FIRST
                            is_beginning_inventory = hasattr(self, 'beginning_inventory_checkbox') and self.beginning_inventory_checkbox.active
                            
                            # Create inventory lot and purchase records based on checkbox state
                            if product_data['quantity'] > 0:
                                purchase_id_for_lot = None  # Default for beginning inventory
                                
                                # If NOT beginning inventory, create proper purchase record first
                                if not is_beginning_inventory:
                                    db_purchase_items = [{
                                        'product_id': product_id,
                                        'quantity': product_data['quantity'],
                                        'unit_cost': product_data['cost_price']
                                    }]
                                    
                                    purchase_id_for_lot = app.db.create_purchase(
                                        items=db_purchase_items,
                                        supplier_id=None,
                                        payment_type=payment_type,
                                        reference_no=f"INV-{product_id}"
                                    )
                                    
                                    if purchase_id_for_lot:
                                        print(f"Created purchase record #{purchase_id_for_lot} for new product")
                                
                                # Create inventory lot with correct purchase_id
                                lot_id = app.db.add_inventory_lot(
                                    product_id=product_id,
                                    purchase_id=purchase_id_for_lot,  # None for beginning inventory, purchase_id for regular
                                    quantity=product_data['quantity'],
                                    cost_per_unit=product_data['cost_price']
                                )
                                
                                if lot_id:
                                    lot_type = "beginning inventory" if is_beginning_inventory else "purchase"
                                    print(f"Created {lot_type} lot #{lot_id} for FIFO costing")
                            
                            # Sync product quantities to ensure accuracy
                            app.db.sync_product_quantities_with_inventory_lots()
                            
                            # --- Ledger & Chart of Accounts Logic ---
                            try:
                                if product_data['quantity'] > 0:
                                    total_cost = product_data['cost_price'] * product_data['quantity']
                                    
                                    # Process accounting entries
                                    app.accounting.process_inventory_purchase(
                                        purchase_id=f"INV-{product_id}",
                                        purchase_items=[{
                                            'product_name': product_data['name'],
                                            'cost': total_cost
                                        }],
                                        total_amount=total_cost,
                                        payment_type=payment_type,
                                        is_beginning_inventory=is_beginning_inventory
                                    )
                                    
                                    if is_beginning_inventory:
                                        print(f"Beginning inventory recorded: {product_data['name']} - ₱{total_cost:,.2f}")
                                    else:
                                        print(f"Purchase recorded: {product_data['name']} - ₱{total_cost:,.2f} ({payment_type})")
                            except Exception as e:
                                print(f"Error processing accounting: {e}")
                        else:
                            print("Failed to add product")
                self.load_inventory()
                self.update_stats()  # Update stats after successful product addition
                dialog.dismiss()
            except ValueError as e:
                print(f"Invalid input: {e}")
            except Exception as e:
                print(f"Error saving product: {e}")
        
        def cancel_dialog(instance):
            if hasattr(self, 'category_dropdown'):
                self.category_dropdown.dismiss()
            if hasattr(self, 'product_name_dropdown'):
                self.product_name_dropdown.dismiss()
            dialog.dismiss()
        
        # Create enhanced dialog with improved styling
        dialog = MDDialog(
            type="custom",
            content_cls=main_content,
            size_hint=(0.95, 0.85),
            auto_dismiss=False,
            buttons=[
                MDFlatButton(
                    text="  CANCEL  ",
                    theme_text_color="Custom",
                    text_color=[0.5, 0.5, 0.5, 1],
                    md_bg_color=[0.95, 0.95, 0.95, 1],
                    font_size="16sp",
                    on_release=cancel_dialog
                ),
                MDRaisedButton(
                    text=f"  {'UPDATE PRODUCT' if is_edit else 'ADD PRODUCT'}  ",
                    md_bg_color=[0.2, 0.6, 0.2, 1],  # Green color
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1],
                    font_size="16sp",
                    elevation=0,
                    on_release=save_product
                ),
            ],
        )
        
        dialog.open()
    
    def confirm_delete_product(self, product_id, product_name):
        """Show confirmation dialog for product deletion"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton, MDFlatButton
        from kivymd.uix.label import MDLabel
        
        def delete_product(instance):
            app = MDApp.get_running_app()
            
            # Get product details for accounting
            product = app.db.get_product_by_id(product_id)
            if product and product[5] > 0:  # Has stock
                # Process inventory adjustment for remaining stock
                app.accounting.process_inventory_adjustment(
                    product_id=product_id,
                    adjustment_type='decrease',
                    quantity=product[5],
                    reason=f"Product deletion - {product_name}"
                )
            
            success = app.db.delete_product(product_id)
            if success:
                print(f"Product '{product_name}' deleted successfully")
                self.load_inventory()
            else:
                print(f"Failed to delete product '{product_name}'")
            
            dialog.dismiss()
        
        def cancel_delete(instance):
            dialog.dismiss()
        
        dialog = MDDialog(
            title="Delete Product",
            text=f"Are you sure you want to delete '{product_name}'?\n\nThis action cannot be undone.",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=[0.533, 0.620, 0.451, 1],
                    on_release=cancel_delete
                ),
                MDRaisedButton(
                    text="DELETE",
                    md_bg_color=[0.427, 0.137, 0.137, 1],
                    on_release=delete_product
                ),
            ],
        )
        
        dialog.open()
    
    def adjust_stock(self, product_id, product_name):
        """Show stock adjustment dialog"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDRaisedButton, MDFlatButton
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        
        app = MDApp.get_running_app()
        product = app.db.get_product_by_id(product_id)
        
        if not product:
            print("Product not found")
            return
        
        current_stock = product[5]
        
        # Create form
        content = MDBoxLayout(
            orientation="vertical",
            spacing="16dp",
            size_hint_y=None,
            height="250dp",
            adaptive_height=True
        )
        
        # Current stock info
        current_label = MDLabel(
            text=f"Current Stock: {current_stock} units",
            font_style="Subtitle1",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp"
        )
        
        # New quantity field
        new_qty_field = MDTextField(
            hint_text="New Quantity",
            text=str(current_stock),
            multiline=False,
            input_filter="int"
        )
        
        # Reason field
        reason_field = MDTextField(
            hint_text="Reason for adjustment",
            text="",
            multiline=True,
            max_height="60dp"
        )
        
        content.add_widget(current_label)
        content.add_widget(new_qty_field)
        content.add_widget(reason_field)
        
        def apply_adjustment(instance):
            try:
                new_quantity = int(new_qty_field.text)
                reason = reason_field.text.strip() or "Stock adjustment"
                
                if new_quantity == current_stock:
                    print("No change in quantity")
                    dialog.dismiss()
                    return
                
                # Update product quantity
                app.db.update_product_quantity(product_id, new_quantity)
                
                # Process accounting adjustment
                qty_diff = new_quantity - current_stock
                adjustment_type = 'increase' if qty_diff > 0 else 'decrease'
                
                app.accounting.process_inventory_adjustment(
                    product_id=product_id,
                    adjustment_type=adjustment_type,
                    quantity=abs(qty_diff),
                    reason=reason
                )
                
                print(f"Stock adjusted for '{product_name}': {current_stock} → {new_quantity}")
                
                # Refresh display
                self.load_inventory()
                dialog.dismiss()
                
            except ValueError:
                print("Invalid quantity entered")
            except Exception as e:
                print(f"Error adjusting stock: {e}")
        
        def cancel_adjustment(instance):
            dialog.dismiss()
        
        dialog = MDDialog(
            title=f"Adjust Stock - {product_name}",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=[0.427, 0.137, 0.137, 1],
                    on_release=cancel_adjustment
                ),
                MDRaisedButton(
                    text="APPLY",
                    md_bg_color=[0.533, 0.620, 0.451, 1],
                    on_release=apply_adjustment
                ),
            ],
        )
        
        dialog.open()
    
    def show_low_stock(self):
        """Filter and show only low stock products"""
        app = MDApp.get_running_app()
        low_stock_products = []
        
        for product in self.current_products:
            stock_level = product[5]  # quantity
            reorder_level = product[6]  # reorder_level
            if stock_level <= reorder_level:
                low_stock_products.append(product)
        
        try:
            # Clear existing list
            product_list = self.ids.product_list
            product_list.clear_widgets()
            
            if low_stock_products:
                # Add low stock products to list
                for product in low_stock_products:
                    self.add_product_row(product, product_list)
                
                print(f"Showing {len(low_stock_products)} low stock products")
            else:
                # Show message that no low stock items
                from kivymd.uix.boxlayout import MDBoxLayout
                from kivymd.uix.label import MDLabel
                
                card = MDCard(
                    size_hint_y=None,
                    height="120dp",
                    elevation=0,
                    md_bg_color=[0.533, 0.620, 0.451, 1],  # Green
                    padding="16dp",
                    line_color=[0.4, 0.5, 0.3, 1],  # Darker green outline
                    line_width=2
                )
                
                layout = MDBoxLayout(
                    orientation='vertical',
                    spacing="8dp"
                )
                
                title_label = MDLabel(
                    text="All Stock Levels Good!",
                    font_style="H6",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1]
                )
                
                subtitle_label = MDLabel(
                    text="No products are below their reorder levels.",
                    font_style="Body2",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1]
                )
                
                layout.add_widget(title_label)
                layout.add_widget(subtitle_label)
                card.add_widget(layout)
                
                product_list.add_widget(card)
                print("No low stock items found")
                
        except Exception as e:
            print(f"Error showing low stock: {e}")
        
    def show_returns_dialog(self):
        """Show dialog for processing returns (sales or purchase returns)"""
        from kivymd.uix.selectioncontrol import MDCheckbox
        from kivymd.uix.menu import MDDropdownMenu
        
        # Create dialog content
        content = MDBoxLayout(
            orientation="vertical",
            spacing="16dp",
            size_hint_y=None,
            height="400dp",
            padding="16dp"
        )
        
        # Return type selection
        content.add_widget(MDLabel(
            text="Return Type",
            theme_text_color="Primary",
            font_style="H6",
            bold=True
        ))
        
        return_type_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="5dp",
            size_hint_y=None,
            height="40dp"
            
        )
        
        # Radio buttons for return type
        self.sales_return_checkbox = MDCheckbox(
            group="return_type",
            size_hint=(None, None),
            size=("24dp", "24dp"),
            pos_hint={'center_y': 0.5},
            active=True  # Default to sales return
        )
        self.purchase_return_checkbox = MDCheckbox(
            group="return_type",
            size_hint=(None, None),
            size=("24dp", "24dp"),
            pos_hint={'center_y': 0.5}
        )
        
        # Bind checkbox changes to update product dropdown
        self.sales_return_checkbox.bind(active=self.on_return_type_change)
        self.purchase_return_checkbox.bind(active=self.on_return_type_change)
        
        return_type_layout.add_widget(self.sales_return_checkbox)
        return_type_layout.add_widget(MDLabel(text="Sales Return", size_hint_x=0.4))
        return_type_layout.add_widget(self.purchase_return_checkbox)
        return_type_layout.add_widget(MDLabel(text="Purchase Return", size_hint_x=0.4))
        
        content.add_widget(return_type_layout)
        
        # Product selection
        content.add_widget(MDLabel(
            text="Select Product",
            theme_text_color="Primary",
            font_style="H6",
            bold=True
        ))
        
        # Product dropdown button
        self.product_dropdown_button = MDRaisedButton(
            text="Choose a product...",
            pos_hint={'center_x': 0.5},
            size_hint_x=1,
            size_hint_y=None,
            height="50dp"
        )
        
        # Create dropdown menu with products - will be populated dynamically
        self.app = MDApp.get_running_app()
        
        self.product_dropdown_menu = MDDropdownMenu(
            caller=self.product_dropdown_button,
            items=[],  # Empty initially
            position="bottom",
            width_mult=5,
        )
        
        self.product_dropdown_button.bind(on_release=lambda x: self.open_product_dropdown())
        
        # Initialize dropdown with sales return data
        self.update_product_dropdown()
        content.add_widget(self.product_dropdown_button)
        
        # Quantity input
        content.add_widget(MDLabel(
            text="Quantity to Return",
            theme_text_color="Primary",
            font_style="H6",
            bold=True
        ))
        
        self.quantity_input = MDTextField(
            hint_text="Enter quantity",
            helper_text="Must be a positive number",
            helper_text_mode="on_focus",
            input_filter="int",  # Only allow integers
            size_hint_y=None,
            height="40dp"
        )
        
        content.add_widget(self.quantity_input)
        
        # Reason input (optional)
        content.add_widget(MDLabel(
            text="Reason (Optional)",
            theme_text_color="Primary",
            font_style="H6",
            bold=True
        ))
        
        self.reason_input = MDTextField(
            hint_text="Enter reason for return",
            multiline=True,
            size_hint_y=None,
            height="60dp"
        )
        
        content.add_widget(self.reason_input)
        
        # Create and show dialog
        self.returns_dialog = MDDialog(
            title="Process Return",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=[0.5, 0.5, 0.5, 1],
                    on_release=lambda x: self.returns_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="PROCESS RETURN",
                    md_bg_color=[0.831, 0.686, 0.216, 1],  # POS Gold
                    theme_text_color="Custom",
                    text_color=[0.639, 0.114, 0.114, 1],  # POS Red text
                    on_release=self.process_return
                ),
            ],
        )
        
        # Store selected product
        self.selected_product_for_return = None
        
        self.returns_dialog.open()
    
    def on_return_type_change(self, checkbox, active):
        """Handle return type selection change"""
        if active:  # Only act when checkbox becomes active
            # Reset product selection when type changes
            self.selected_product_for_return = None
            self.product_dropdown_button.text = "Choose a product..."
            self.update_product_dropdown()
    
    def update_product_dropdown(self):
        """Update product dropdown based on selected return type"""
        return_type = "sales" if self.sales_return_checkbox.active else "purchase"
        
        products = self.app.db.get_products()
        menu_items = []
        
        cursor = self.app.db.conn.cursor()
        
        for product in products:
            product_id = product[0]
            product_name = product[1]
            current_stock = product[5]
            
            if return_type == "sales":
                # Get total sold quantity for this product
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0)
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    WHERE si.product_id = ? AND s.status = 'completed'
                """, (product_id,))
                total_sold = cursor.fetchone()[0] or 0
                
                # Get total already returned quantity for sales
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0)
                    FROM sales_returns
                    WHERE product_id = ?
                """, (product_id,))
                total_returned_sales = cursor.fetchone()[0] or 0
                
                available_for_return = total_sold - total_returned_sales
                display_text = f"{product_name} (Returnable: {available_for_return})"
                
            else:  # purchase return
                # Get total purchased quantity for this product
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0)
                    FROM purchase_items pi
                    JOIN purchases p ON pi.purchase_id = p.id
                    WHERE pi.product_id = ? AND p.status = 'received'
                """, (product_id,))
                total_purchased = cursor.fetchone()[0] or 0
                
                # Get total already returned quantity for purchases
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0)
                    FROM purchase_returns
                    WHERE product_id = ?
                """, (product_id,))
                total_returned_purchases = cursor.fetchone()[0] or 0
                
                available_for_return = min(total_purchased - total_returned_purchases, current_stock)
                display_text = f"{product_name} (Returnable: {available_for_return}, Stock: {current_stock})"
            
            # Add to menu if there's something returnable
            if available_for_return > 0:
                menu_items.append({
                    "viewclass": "OneLineListItem",
                    "text": display_text,
                    "on_release": lambda x=product, r=available_for_return: self.select_product_for_return(x, r),
                })
        
        # Update dropdown menu items
        self.product_dropdown_menu.items = menu_items
    
    def open_product_dropdown(self):
        """Open the product dropdown menu"""
        # Update items first
        self.update_product_dropdown()
        
        # Then open the menu if there are items
        if self.product_dropdown_menu.items:
            self.product_dropdown_menu.open()
        else:
            from kivymd.uix.snackbar import Snackbar
            return_type = "sales" if self.sales_return_checkbox.active else "purchase"
            Snackbar(text=f"No products available for {return_type} return", duration=3).open()
    
    def select_product_for_return(self, product, available_for_return=None):
        """Handle product selection for return"""
        self.selected_product_for_return = product
        return_type = "sales" if self.sales_return_checkbox.active else "purchase"
        
        if available_for_return is not None:
            if return_type == "sales":
                self.product_dropdown_button.text = f"{product[1]} (Returnable: {available_for_return})"
            else:
                self.product_dropdown_button.text = f"{product[1]} (Returnable: {available_for_return}, Stock: {product[5]})"
        else:
            # Fallback to old display
            self.product_dropdown_button.text = f"{product[1]} (Stock: {product[5]})"
            
        self.product_dropdown_menu.dismiss()
    
    def process_return(self, *args):
        """Process the return based on user input"""
        try:
            # Validate return type
            if not self.sales_return_checkbox.active and not self.purchase_return_checkbox.active:
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text="Please select return type (Sales or Purchase)", duration=3).open()
                return
            
            return_type = "sales" if self.sales_return_checkbox.active else "purchase"
            
            # Validate product selection
            if not self.selected_product_for_return:
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text="Please select a product to return", duration=3).open()
                return
            
            # Validate quantity
            try:
                quantity = int(self.quantity_input.text.strip())
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except (ValueError, AttributeError):
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text="Please enter a valid quantity", duration=3).open()
                return
            
            # Get product details and validate stock for sales returns
            product = self.selected_product_for_return
            product_id = product[0]
            product_name = product[1]
            current_stock = product[5]
            unit_cost = product[3]  # cost_price
            reason = self.reason_input.text.strip() or "Return processed"
            
            app = MDApp.get_running_app()
            
            # Process the return based on type
            if return_type == "sales":
                # For sales returns, validate against sold quantities not current stock
                cursor = app.db.conn.cursor()
                
                # Get total sold quantity for this product
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0)
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    WHERE si.product_id = ? AND s.status = 'completed'
                """, (product_id,))
                total_sold = cursor.fetchone()[0] or 0
                
                # Get total already returned quantity for sales
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0)
                    FROM sales_returns
                    WHERE product_id = ?
                """, (product_id,))
                total_returned_sales = cursor.fetchone()[0] or 0
                
                # Calculate available quantity for return
                available_for_return = total_sold - total_returned_sales
                
                if quantity > available_for_return:
                    from kivymd.uix.snackbar import Snackbar
                    Snackbar(text=f"Cannot return {quantity} items. Only {available_for_return} items available for return (sold: {total_sold}, already returned: {total_returned_sales}).", duration=5).open()
                    return
                
                success = app.db.add_sales_return(0, product_id, quantity, unit_cost, reason)  # sale_id = 0 for generic
                
                if success:
                    message = f"Sales return processed: {quantity} x {product_name}"
                else:
                    from kivymd.uix.snackbar import Snackbar
                    Snackbar(text="Failed to process sales return", duration=3).open()
                    return
                    
            else:  # purchase return
                # For purchase returns, validate against purchased quantities not current stock
                cursor = app.db.conn.cursor()
                
                # Get total purchased quantity for this product
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0)
                    FROM purchase_items pi
                    JOIN purchases p ON pi.purchase_id = p.id
                    WHERE pi.product_id = ? AND p.status = 'received'
                """, (product_id,))
                total_purchased = cursor.fetchone()[0] or 0
                
                # Get total already returned quantity for purchases
                cursor.execute("""
                    SELECT COALESCE(SUM(quantity), 0)
                    FROM purchase_returns
                    WHERE product_id = ?
                """, (product_id,))
                total_returned_purchases = cursor.fetchone()[0] or 0
                
                # Calculate available quantity for return
                available_for_return = total_purchased - total_returned_purchases
                
                if quantity > available_for_return:
                    from kivymd.uix.snackbar import Snackbar
                    Snackbar(text=f"Cannot return {quantity} items. Only {available_for_return} items available for return (purchased: {total_purchased}, already returned: {total_returned_purchases}).", duration=5).open()
                    return
                
                # Additional check: ensure we have enough current stock to physically remove
                if quantity > current_stock:
                    from kivymd.uix.snackbar import Snackbar
                    Snackbar(text=f"Cannot process return. Not enough current stock ({current_stock}) to remove {quantity} items from inventory.", duration=5).open()
                    return
                
                # Find the most recent purchase for this product to use correct payment method
                cursor = app.db.conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.payment_type 
                    FROM purchases p
                    JOIN purchase_items pi ON p.id = pi.purchase_id
                    WHERE pi.product_id = ? AND p.status = 'received'
                    ORDER BY p.date DESC, p.id DESC
                    LIMIT 1
                """, (product_id,))
                
                recent_purchase = cursor.fetchone()
                if recent_purchase:
                    recent_purchase_id, payment_type = recent_purchase
                    print(f"Using purchase ID {recent_purchase_id} ({payment_type}) for return")
                else:
                    recent_purchase_id = 0  # Fallback to generic
                    print("No recent purchase found, using generic return")
                
                success = app.db.add_purchase_return(recent_purchase_id, product_id, quantity, unit_cost, reason)
                
                if success:
                    message = f"Purchase return processed: {quantity} x {product_name}"
                else:
                    from kivymd.uix.snackbar import Snackbar
                    Snackbar(text="Failed to process purchase return", duration=3).open()
                    return
            
            # Close dialog and show success message
            self.returns_dialog.dismiss()
            
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text=message, duration=4).open()
            
            # Refresh inventory and stats
            self.load_inventory()
            self.update_stats()
            
            if success:
                print(f"Return processed successfully: {return_type} return for {product_name} x {quantity}")
            
        except Exception as e:
            print(f"Error processing return: {e}")
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="Error processing return. Please try again.", duration=3).open()

    def show_cash_investment_dialog(self):
        """Show dialog for recording cash investment"""
        app = MDApp.get_running_app()
        
        # Check permissions
        if not app.auth_manager.can_perform_action('cash_investment'):
            self.show_permission_denied('cash_investment')
            return
        
        # Create dialog content
        content = MDBoxLayout(
            orientation="vertical",
            spacing="16dp",
            size_hint_y=None,
            height="300dp",
            padding="16dp"
        )
        
        # Investment amount input
        content.add_widget(MDLabel(
            text="Investment Amount",
            theme_text_color="Primary",
            font_style="H6",
            bold=True
        ))
        
        self.investment_amount_input = MDTextField(
            hint_text="Enter amount (₱)",
            helper_text="Enter the cash amount to invest in the business",
            helper_text_mode="on_focus",
            input_filter="float",  # Allow decimal numbers
            size_hint_y=None,
            height="40dp"
        )
        
        content.add_widget(self.investment_amount_input)
        
        # Description input (optional)
        content.add_widget(MDLabel(
            text="Description (Optional)",
            theme_text_color="Primary",
            font_style="H6",
            bold=True
        ))
        
        self.investment_description_input = MDTextField(
            hint_text="e.g., Owner cash investment, Additional capital contribution",
            text="Owner cash investment",  # Default description
            multiline=True,
            size_hint_y=None,
            height="60dp"
        )
        
        content.add_widget(self.investment_description_input)
        
        # Create and show dialog
        self.investment_dialog = MDDialog(
            title="Record Cash Investment",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=[0.5, 0.5, 0.5, 1],
                    on_release=lambda x: self.investment_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="RECORD INVESTMENT",
                    md_bg_color=[0.533, 0.620, 0.451, 1],  # POS Green
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1],  # White text
                    on_release=self.process_cash_investment
                ),
            ],
        )
        
        self.investment_dialog.open()

    def process_cash_investment(self, instance):
        """Process the cash investment transaction"""
        try:
            # Validate amount
            try:
                amount = float(self.investment_amount_input.text.strip())
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except (ValueError, AttributeError):
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text="Please enter a valid investment amount", duration=3).open()
                return
            
            # Get description
            description = self.investment_description_input.text.strip() or "Owner cash investment"
            
            app = MDApp.get_running_app()
            
            # Process the cash investment
            transaction_id = app.db.add_cash_investment(amount, description)
            
            if transaction_id:
                # Close dialog and show success message
                self.investment_dialog.dismiss()
                
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text=f"Cash investment recorded: ₱{amount:,.2f}", duration=4).open()
                
                # Log the action
                app.auth_manager.log_action("CASH_INVESTMENT", f"Recorded investment of ₱{amount:,.2f}")
                
                # Refresh stats to show updated cash position
                self.update_stats()
                
                print(f"Cash investment processed successfully: ₱{amount:,.2f} - {description}")
            else:
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text="Failed to record cash investment", duration=3).open()
                
        except Exception as e:
            print(f"Error processing cash investment: {e}")
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="Error recording investment. Please try again.", duration=3).open()
        
    def update_navigation_permissions(self):
        """Update navigation button visibility based on user role"""
        try:
            app = MDApp.get_running_app()
            
            if not app.auth_manager or not app.auth_manager.is_authenticated():
                return
                
            role = app.auth_manager.get_current_role()
            
            # Disable restricted buttons for cashiers
            if role == 'cashier':
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

