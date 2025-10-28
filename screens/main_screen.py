from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

class MainScreen(MDScreen):
    def on_enter(self):
        """Load products and categories when screen is entered"""
        app = MDApp.get_running_app()
        # Schedule the product and category loading to happen after the UI is fully ready
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: app.load_products_from_db(), 0.5)
        Clock.schedule_once(lambda dt: app.load_categories_to_ui(), 0.6)
        Clock.schedule_once(lambda dt: self.update_navigation_permissions(), 0.7)
        self.update_dashboard_stats()
    
    def update_dashboard_stats(self):
        """Update the dashboard statistics cards"""
        app = MDApp.get_running_app()
        try:
            stats = app.db.get_dashboard_stats()
            
            # Update stats cards
            self.ids.total_sales_label.text = f"₱{stats['total_sales']:,.2f}"
            self.ids.cost_of_goods_sold_label.text = f"₱{stats['cost_of_goods_sold']:,.2f}"
            
            # Update gross profit with color coding
            gross_profit = stats['gross_profit']
            if gross_profit >= 0:
                self.ids.gross_profit_label.text = f"₱{gross_profit:,.2f}"
                self.ids.gross_profit_label.text_color = [1, 1, 1, 1]  # White for profit
            else:
                self.ids.gross_profit_label.text = f"-₱{abs(gross_profit):,.2f}"
                self.ids.gross_profit_label.text_color = [1, 0.8, 0.8, 1]  # Light red for loss
            
            self.ids.low_stock_label.text = str(stats['low_stock_count'])
            
            print(f"Dashboard stats updated - Sales: ₱{stats['total_sales']:,.2f}, COGS: ₱{stats['cost_of_goods_sold']:,.2f}, Gross Profit: ₱{gross_profit:,.2f}, Low Stock: {stats['low_stock_count']}")
            
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
    
    def switch_category(self, category):
        """Switch the displayed products based on selected category"""
        app = MDApp.get_running_app()
        
        # If category is "all", show all products, otherwise find category by name
        if category.lower() == "all":
            category_id = None
        else:
            # Get category ID from database by name
            categories = app.db.get_categories()
            category_id = None
            for cat in categories:
                if cat[1].lower() == category.lower():  # cat[1] is category name
                    category_id = cat[0]  # cat[0] is category ID
                    break
        
        app.load_products_from_db(category_id=category_id)
        print(f"Switched to category: {category}")
        
    def switch_screen(self, screen_name):
        """Switch to a different screen with authentication check"""
        app = MDApp.get_running_app()
        
        # Check if user is authenticated
        if not app.auth_manager.is_authenticated():
            self.show_access_denied("Please log in first")
            return
        
        # Check if user has permission to access the screen
        if not app.auth_manager.can_access_screen(screen_name):
            message = app.auth_manager.get_access_denied_message(screen_name)
            self.show_access_denied(message)
            return
        
        # Log the screen access
        app.auth_manager.log_action(f"ACCESS_SCREEN", "navigation", None, None, f"Accessed {screen_name} screen")
        
        # Switch to the screen
        self.parent.current = screen_name
    
    def show_access_denied(self, message):
        """Show access denied dialog"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        
        if hasattr(self, 'access_dialog') and self.access_dialog:
            self.access_dialog.dismiss()
        
        self.access_dialog = MDDialog(
            title="Access Denied",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=[0.639, 0.114, 0.114, 1],
                    on_release=lambda x: self.access_dialog.dismiss()
                ),
            ],
        )
        self.access_dialog.open()
    
    def logout(self):
        """Logout current user"""
        app = MDApp.get_running_app()
        
        if app.auth_manager.logout():
            # Clear any sensitive data from UI
            self.clear_user_data()
            # Navigate back to login screen
            self.parent.current = 'login'
    
    def clear_user_data(self):
        """Clear user-specific data from the interface"""
        # Clear cart
        app = MDApp.get_running_app()
        app.cart = {}
        app.cart_total = 0
        app.cart_visible = False
        
        # Update cart display
        if hasattr(app, 'update_cart_display'):
            app.update_cart_display()

    def on_stop(self):
        """Clean up when the app closes"""
        if hasattr(self, 'db'):
            self.db.close()
    
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