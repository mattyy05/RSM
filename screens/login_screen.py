"""
Login Screen
Handles user authentication interface
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.app import MDApp
from kivy.uix.widget import Widget


class LoginScreen(MDScreen):
    """
    Login Screen for User Authentication
    
    Features:
    - Username/password input
    - Login validation
    - Error handling
    - Session management
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        
    def on_enter(self):
        """Called when screen is entered"""
        # Clear any previous login data
        if hasattr(self.ids, 'username_field'):
            self.ids.username_field.text = ""
        if hasattr(self.ids, 'password_field'):
            self.ids.password_field.text = ""
        
        # Focus on username field
        if hasattr(self.ids, 'username_field'):
            self.ids.username_field.focus = True
    
    def attempt_login(self):
        """
        Attempt to log in with provided credentials
        """
        try:
            # Get field values
            username = self.ids.username_field.text.strip()
            password = self.ids.password_field.text
            
            # Validate input
            if not username:
                self.show_error_dialog("Please enter your username")
                return
            
            if not password:
                self.show_error_dialog("Please enter your password")
                return
            
            # Get app instance and auth manager
            app = MDApp.get_running_app()
            
            if not hasattr(app, 'auth_manager'):
                self.show_error_dialog("Authentication system not initialized")
                return
            
            # Show loading state (optional)
            self.ids.login_button.text = "Logging in..."
            self.ids.login_button.disabled = True
            
            # Attempt authentication
            user_data = app.auth_manager.login(username, password)
            
            if user_data:
                # Login successful
                print(f"Login successful for {username} ({user_data['role']})")
                
                # Navigate to main screen
                app.root.current = 'main'
                
                # Update main screen with user info
                self.update_main_screen_user_info(user_data)
                
                # Show welcome message
                self.show_success_dialog(
                    f"Welcome back, {user_data['username']}!",
                    f"Logged in as {user_data['role'].title()}"
                )
                
            else:
                # Login failed
                self.show_error_dialog(
                    "Login Failed",
                    "Invalid username or password. Please try again."
                )
            
        except Exception as e:
            print(f"Login error: {e}")
            self.show_error_dialog(
                "Login Error", 
                f"An error occurred during login: {str(e)}"
            )
        finally:
            # Reset login button
            self.ids.login_button.text = "LOGIN"
            self.ids.login_button.disabled = False
    
    def update_main_screen_user_info(self, user_data):
        """
        Update main screen with current user information
        
        Args:
            user_data (dict): User information
        """
        try:
            app = MDApp.get_running_app()
            main_screen = app.root.get_screen('main')
            
            # Update user info label if it exists
            if hasattr(main_screen.ids, 'user_info_label'):
                main_screen.ids.user_info_label.text = (
                    f"Logged in as: {user_data['username']} ({user_data['role'].title()})"
                )
            
            # Update navigation buttons based on role
            self.update_navigation_permissions(main_screen, user_data['role'])
            
        except Exception as e:
            print(f"Error updating main screen: {e}")
    
    def update_navigation_permissions(self, main_screen, role):
        """
        Update navigation button visibility based on user role
        
        Args:
            main_screen: Main screen instance
            role (str): User role
        """
        try:
            app = MDApp.get_running_app()
            
            # Get role permissions from auth manager
            if hasattr(app, 'auth_manager'):
                # Disable restricted buttons for cashiers
                if role == 'cashier':
                    # Find and disable inventory button
                    if hasattr(main_screen.ids, 'inventory_button'):
                        main_screen.ids.inventory_button.disabled = True
                        main_screen.ids.inventory_button.md_bg_color = [0.5, 0.5, 0.5, 1]
                    
                    # Find and disable reports button
                    if hasattr(main_screen.ids, 'reports_button'):
                        main_screen.ids.reports_button.disabled = True
                        main_screen.ids.reports_button.md_bg_color = [0.5, 0.5, 0.5, 1]
                    
                    # Find and disable user management button
                    if hasattr(main_screen.ids, 'user_management_button'):
                        main_screen.ids.user_management_button.disabled = True
                        main_screen.ids.user_management_button.md_bg_color = [0.5, 0.5, 0.5, 1]
                
                elif role == 'owner':
                    # Enable all buttons for owners
                    if hasattr(main_screen.ids, 'inventory_button'):
                        main_screen.ids.inventory_button.disabled = False
                        main_screen.ids.inventory_button.md_bg_color = [0.639, 0.114, 0.114, 1]
                    
                    if hasattr(main_screen.ids, 'reports_button'):
                        main_screen.ids.reports_button.disabled = False
                        main_screen.ids.reports_button.md_bg_color = [0.639, 0.114, 0.114, 1]
                    
                    if hasattr(main_screen.ids, 'user_management_button'):
                        main_screen.ids.user_management_button.disabled = False
                        main_screen.ids.user_management_button.md_bg_color = [0.639, 0.114, 0.114, 1]
            
        except Exception as e:
            print(f"Error updating navigation permissions: {e}")
    
    def show_error_dialog(self, title, text=None):
        """
        Show error dialog
        
        Args:
            title (str): Dialog title or message if text is None
            text (str, optional): Dialog text content
        """
        if text is None:
            text = title
            title = "Error"
        
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=[0.639, 0.114, 0.114, 1],
                    on_release=self.close_dialog
                ),
            ],
        )
        self.dialog.open()
    
    def show_success_dialog(self, title, text=None):
        """
        Show success dialog
        
        Args:
            title (str): Dialog title
            text (str, optional): Dialog text content
        """
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title=title,
            text=text or "",
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=[0.533, 0.620, 0.451, 1],
                    on_release=self.close_dialog
                ),
            ],
        )
        self.dialog.open()
    
    def close_dialog(self, *args):
        """Close any open dialog"""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
    
    def on_enter_key(self, instance):
        """
        Handle Enter key press in password field
        
        Args:
            instance: TextField instance
        """
        self.attempt_login()
    
    def show_forgot_password_dialog(self):
        """Show forgot password dialog (placeholder)"""
        self.show_error_dialog(
            "Forgot Password",
            "Please contact your system administrator to reset your password."
        )