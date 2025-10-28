"""
User Management Screen
Allows owners to manage user accounts (create, view, delete users)
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
import bcrypt


class UserManagementScreen(MDScreen):
    """User Management Screen for Owner Role"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.delete_dialog = None
    
    def on_enter(self):
        """Called when screen is entered"""
        app = MDApp.get_running_app()
        
        # Check permissions
        if not app.auth_manager.can_perform_action('manage_users'):
            message = app.auth_manager.get_access_denied_message(action='manage_users')
            Snackbar(text=message, duration=3).open()
            app.sm.current = 'main'
            return
        
        # Log screen access
        app.auth_manager.log_action("ACCESS_USER_MANAGEMENT", "navigation")
        
        # Load users
        self.load_users()
    
    def load_users(self):
        """Load all users and display them"""
        try:
            app = MDApp.get_running_app()
            users = app.db.get_all_users_for_management()
            users_container = self.ids.users_container
            users_container.clear_widgets()
            
            if not users:
                no_users_label = MDLabel(
                    text="No users found.",
                    theme_text_color="Secondary",
                    halign="center",
                    size_hint_y=None,
                    height="40dp"
                )
                users_container.add_widget(no_users_label)
                return
            
            for user in users:
                user_id, username, role, is_active, created_at, last_login = user
                
                # Create user card
                card = MDCard(
                    size_hint_y=None,
                    height="120dp",
                    padding="16dp",
                    md_bg_color=[1, 1, 1, 1],
                    elevation=2,
                    radius=[8, 8, 8, 8]
                )
                
                card_layout = MDBoxLayout(
                    orientation="horizontal",
                    spacing="16dp"
                )
                
                # User info
                info_layout = MDBoxLayout(
                    orientation="vertical",
                    size_hint_x=0.7,
                    spacing="4dp"
                )
                
                username_label = MDLabel(
                    text=f"Username: {username}",
                    theme_text_color="Primary",
                    font_style="Subtitle1",
                    bold=True
                )
                
                role_color = [0.533, 0.620, 0.451, 1] if role == 'owner' else [0.639, 0.114, 0.114, 1]
                role_label = MDLabel(
                    text=f"Role: {role.title()}",
                    theme_text_color="Custom",
                    text_color=role_color,
                    font_style="Body1"
                )
                
                status_text = "Active" if is_active else "Inactive"
                status_color = [0.533, 0.620, 0.451, 1] if is_active else [0.639, 0.114, 0.114, 1]
                status_label = MDLabel(
                    text=f"Status: {status_text}",
                    theme_text_color="Custom",
                    text_color=status_color,
                    font_style="Caption"
                )
                
                created_date = created_at[:10] if created_at else "Unknown"
                created_label = MDLabel(
                    text=f"Created: {created_date}",
                    theme_text_color="Secondary",
                    font_style="Caption"
                )
                
                info_layout.add_widget(username_label)
                info_layout.add_widget(role_label)
                info_layout.add_widget(status_label)
                info_layout.add_widget(created_label)
                
                card_layout.add_widget(info_layout)
                
                # Action buttons
                if username != 'admin':
                    actions_layout = MDBoxLayout(
                        orientation="vertical",
                        size_hint_x=0.3,
                        spacing="8dp"
                    )
                    
                    delete_btn = MDRaisedButton(
                        text="Delete User",
                        md_bg_color=[0.8, 0.2, 0.2, 1],
                        theme_text_color="Custom",
                        text_color=[1, 1, 1, 1],
                        size_hint_y=None,
                        height="40dp",
                        on_release=lambda x, uid=user_id, uname=username: self.confirm_delete_user(uid, uname)
                    )
                    
                    actions_layout.add_widget(delete_btn)
                    card_layout.add_widget(actions_layout)
                else:
                    admin_layout = MDBoxLayout(
                        orientation="vertical",
                        size_hint_x=0.3
                    )
                    
                    admin_label = MDLabel(
                        text="ADMIN USER",
                        theme_text_color="Custom",
                        text_color=[0.533, 0.620, 0.451, 1],
                        font_style="H6",
                        bold=True,
                        halign="center"
                    )
                    
                    admin_layout.add_widget(admin_label)
                    card_layout.add_widget(admin_layout)
                
                card.add_widget(card_layout)
                users_container.add_widget(card)
                
        except Exception as e:
            print(f"Error loading users: {e}")
            Snackbar(text=f"Error loading users: {str(e)}", duration=3).open()
    
    def show_add_user_dialog(self):
        """Show dialog to add new user"""
        content = MDBoxLayout(
            orientation="vertical",
            spacing="16dp",
            size_hint_y=None,
            height="250dp"
        )
        
        # Username field
        self.username_field = MDTextField(
            hint_text="Username",
            required=True,
            mode="rectangle",
            size_hint_y=None,
            height="60dp"
        )
        content.add_widget(self.username_field)
        
        # Password field
        self.password_field = MDTextField(
            hint_text="Password (minimum 6 characters)",
            password=True,
            required=True,
            mode="rectangle",
            size_hint_y=None,
            height="60dp"
        )
        content.add_widget(self.password_field)
        
        # Role selection
        role_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="16dp",
            size_hint_y=None,
            height="50dp"
        )
        
        # Cashier checkbox (default)
        cashier_box = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_x=0.5
        )
        
        self.cashier_checkbox = MDCheckbox(
            size_hint=(None, None),
            size=("32dp", "32dp"),
            active=True
        )
        cashier_label = MDLabel(
            text="Cashier",
            theme_text_color="Primary",
            font_style="Body1"
        )
        cashier_box.add_widget(self.cashier_checkbox)
        cashier_box.add_widget(cashier_label)
        
        # Owner checkbox
        owner_box = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_x=0.5
        )
        
        self.owner_checkbox = MDCheckbox(
            size_hint=(None, None),
            size=("32dp", "32dp"),
            active=False
        )
        owner_label = MDLabel(
            text="Owner",
            theme_text_color="Primary",
            font_style="Body1"
        )
        owner_box.add_widget(self.owner_checkbox)
        owner_box.add_widget(owner_label)
        
        # Bind checkboxes
        self.owner_checkbox.bind(active=self.on_role_checkbox)
        self.cashier_checkbox.bind(active=self.on_role_checkbox)
        
        role_layout.add_widget(cashier_box)
        role_layout.add_widget(owner_box)
        content.add_widget(role_layout)
        
        self.dialog = MDDialog(
            title="Add New User",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=[0.8, 0.2, 0.2, 1],
                    on_release=self.close_dialog
                ),
                MDRaisedButton(
                    text="CREATE USER",
                    md_bg_color=[0.533, 0.620, 0.451, 1],
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1],
                    on_release=self.create_user
                ),
            ],
        )
        self.dialog.open()
    
    def on_role_checkbox(self, checkbox, value):
        """Handle exclusive role selection"""
        if value:
            if checkbox == self.owner_checkbox:
                self.cashier_checkbox.active = False
            else:
                self.owner_checkbox.active = False
    
    def create_user(self, *args):
        """Create new user"""
        try:
            app = MDApp.get_running_app()
            
            username = self.username_field.text.strip()
            password = self.password_field.text.strip()
            role = "owner" if self.owner_checkbox.active else "cashier"
            
            # Validation
            if not username or not password:
                self.show_error("Please fill in all fields")
                return
            
            if len(password) < 6:
                self.show_error("Password must be at least 6 characters")
                return
            
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user
            current_user = app.auth_manager.get_current_user()
            user_id = app.db.create_user_by_admin(username, hashed_password, role, current_user['user_id'])
            
            if user_id:
                # Log the action
                app.auth_manager.log_action(
                    "CREATE_USER",
                    "users",
                    user_id,
                    None,
                    f"Created user: {username} with role: {role}"
                )
                
                print(f"User created successfully: {username} ({role})")
                self.close_dialog()
                self.load_users()
                
                Snackbar(
                    text=f"User '{username}' created successfully!",
                    duration=4
                ).open()
            else:
                self.show_error("Failed to create user. Username may already exist.")
                
        except Exception as e:
            print(f"Error creating user: {e}")
            self.show_error(f"Error creating user: {str(e)}")
    
    def confirm_delete_user(self, user_id, username):
        """Confirm user deletion"""
        self.delete_dialog = MDDialog(
            title="Confirm User Deletion",
            text=f"Are you sure you want to delete user '{username}'?",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=[0.533, 0.620, 0.451, 1],
                    on_release=lambda x: self.delete_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="DELETE USER",
                    md_bg_color=[0.8, 0.2, 0.2, 1],
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1],
                    on_release=lambda x: self.delete_user(user_id, username)
                ),
            ],
        )
        self.delete_dialog.open()
    
    def delete_user(self, user_id, username):
        """Delete user"""
        try:
            app = MDApp.get_running_app()
            
            success = app.db.delete_user_by_admin(user_id)
            if success:
                app.auth_manager.log_action(
                    "DELETE_USER",
                    "users",
                    user_id,
                    f"Deleted user: {username}",
                    None
                )
                
                print(f"User deleted: {username}")
                self.delete_dialog.dismiss()
                self.load_users()
                
                Snackbar(
                    text=f"User '{username}' deleted successfully!",
                    duration=3
                ).open()
            else:
                self.show_error("Failed to delete user.")
                
        except Exception as e:
            print(f"Error deleting user: {e}")
            self.show_error(f"Error deleting user: {str(e)}")
    
    def show_error(self, message):
        """Show error message"""
        Snackbar(
            text=message,
            duration=3,
            bg_color=[0.8, 0.2, 0.2, 1]
        ).open()
    
    def close_dialog(self, *args):
        """Close dialog"""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
    
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
        """Go back to main screen"""
        app = MDApp.get_running_app()
        app.sm.current = 'main'