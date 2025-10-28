"""
Authentication Manager
Handles user authentication, session management, and role-based access control
"""

from datetime import datetime
import json

class AuthManager:
    """
    Authentication and Authorization Manager
    
    Handles:
    - User session management
    - Role-based access control
    - Permission checking
    - Security logging
    """
    
    def __init__(self, database):
        self.db = database
        self.current_user = None
        self.session_start_time = None
        
        # Define role permissions
        self.role_permissions = {
            'owner': {
                'screens': ['main', 'inventory', 'transactions', 'payments', 'reports', 'sales_report', 'ledger', 'user_management', 'financial_statements'],
                'actions': ['create', 'read', 'update', 'delete', 'view_reports', 'manage_users', 'cash_investment']
            },
            'cashier': {
                'screens': ['main', 'transactions', 'payments'],
                'actions': ['create', 'read']  # No update/delete for past transactions
            }
        }
        
        # Screen access mapping for easy checking
        self.restricted_screens = {
            'inventory': ['owner'],
            'reports': ['owner'],
            'sales_report': ['owner'],
            'ledger': ['owner'],
            'user_management': ['owner'],
            'financial_statements': ['owner']
        }
        
        # Initialize default user if needed
        self.db.create_default_user()
    
    def login(self, username, password):
        """
        Authenticate user and start session
        
        Args:
            username (str): Username
            password (str): Plain text password
            
        Returns:
            dict: User data if successful, None if failed
        """
        try:
            user_data = self.db.authenticate_user(username, password)
            
            if user_data:
                self.current_user = user_data
                self.session_start_time = datetime.now()
                
                # Log successful login
                print(f"User {username} logged in successfully as {user_data['role']}")
                return user_data
            else:
                print(f"Login failed for username: {username}")
                return None
        except Exception as e:
            print(f"Login error: {e}")
            return None
    
    def logout(self):
        """End current user session"""
        if self.current_user:
            # Log logout action
            self.db.log_audit_action(
                self.current_user['user_id'], 
                "LOGOUT", 
                new_values=f"Session duration: {self.get_session_duration()}"
            )
            
            print(f"User {self.current_user['username']} logged out")
            self.current_user = None
            self.session_start_time = None
            return True
        return False
    
    def is_authenticated(self):
        """Check if user is currently logged in"""
        return self.current_user is not None
    
    def get_current_user(self):
        """Get current user information"""
        return self.current_user
    
    def get_current_role(self):
        """Get current user's role"""
        return self.current_user['role'] if self.current_user else None
    
    def get_session_duration(self):
        """Get current session duration"""
        if self.session_start_time:
            duration = datetime.now() - self.session_start_time
            return str(duration).split('.')[0]  # Remove microseconds
        return "0:00:00"
    
    def can_access_screen(self, screen_name):
        """
        Check if current user can access a screen
        
        Args:
            screen_name (str): Name of the screen to check
            
        Returns:
            bool: True if user can access, False otherwise
        """
        if not self.is_authenticated():
            return False
        
        user_role = self.get_current_role()
        
        # Check if screen is restricted
        if screen_name in self.restricted_screens:
            allowed_roles = self.restricted_screens[screen_name]
            return user_role in allowed_roles
        
        # Check against role permissions
        if user_role in self.role_permissions:
            allowed_screens = self.role_permissions[user_role]['screens']
            return screen_name in allowed_screens
        
        return False
    
    def can_perform_action(self, action):
        """
        Check if current user can perform an action
        
        Args:
            action (str): Action to check (create, read, update, delete, etc.)
            
        Returns:
            bool: True if user can perform action, False otherwise
        """
        if not self.is_authenticated():
            return False
        
        user_role = self.get_current_role()
        
        if user_role in self.role_permissions:
            allowed_actions = self.role_permissions[user_role]['actions']
            return action in allowed_actions
        
        return False
    
    def require_permission(self, screen_name=None, action=None):
        """
        Decorator-style permission checking
        
        Args:
            screen_name (str, optional): Screen to check access for
            action (str, optional): Action to check permission for
            
        Returns:
            bool: True if all checks pass, False otherwise
        """
        if not self.is_authenticated():
            return False
        
        if screen_name and not self.can_access_screen(screen_name):
            return False
        
        if action and not self.can_perform_action(action):
            return False
        
        return True
    
    def log_action(self, action, table_name=None, record_id=None, old_values=None, new_values=None):
        """
        Log user action for audit trail
        
        Args:
            action (str): Action performed
            table_name (str, optional): Database table affected
            record_id (int, optional): Record ID affected
            old_values (str, optional): Previous values
            new_values (str, optional): New values
        """
        if self.is_authenticated():
            self.db.log_audit_action(
                self.current_user['user_id'],
                action,
                table_name,
                record_id,
                old_values,
                new_values
            )
    
    def get_access_denied_message(self, screen_name=None, action=None):
        """
        Get appropriate access denied message
        
        Args:
            screen_name (str, optional): Screen that was restricted
            action (str, optional): Action that was restricted
            
        Returns:
            str: Access denied message
        """
        user_role = self.get_current_role() or "unknown"
        
        if screen_name:
            return f"Access Denied: {user_role.title()} users cannot access {screen_name.title()} screen"
        elif action:
            return f"Access Denied: {user_role.title()} users cannot perform {action} action"
        else:
            return f"Access Denied: Insufficient permissions for {user_role.title()} role"
    
    def create_user(self, username, password, role):
        """
        Create new user (owner only)
        
        Args:
            username (str): New username
            password (str): New password
            role (str): User role ('owner' or 'cashier')
            
        Returns:
            int: New user ID if successful, None if failed
        """
        if not self.can_perform_action('manage_users'):
            raise PermissionError("Only owners can create users")
        
        try:
            user_id = self.db.create_user(username, password, role, self.current_user['user_id'])
            self.log_action("CREATE_USER", "users", user_id, None, f"Created user: {username}")
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            raise e
    
    def change_password(self, user_id, new_password):
        """
        Change user password
        
        Args:
            user_id (int): User ID to change password for
            new_password (str): New password
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Users can change their own password, owners can change any password
        if (user_id != self.current_user['user_id'] and 
            not self.can_perform_action('manage_users')):
            raise PermissionError("Cannot change other user's password")
        
        try:
            self.db.update_user_password(user_id, new_password, self.current_user['user_id'])
            self.log_action("CHANGE_PASSWORD", "users", user_id)
            return True
        except Exception as e:
            print(f"Error changing password: {e}")
            raise e
    
    def get_audit_log(self, limit=100):
        """
        Get audit log (owner only)
        
        Args:
            limit (int): Maximum number of entries to return
            
        Returns:
            list: Audit log entries
        """
        if not self.can_perform_action('view_reports'):
            raise PermissionError("Only owners can view audit logs")
        
        return self.db.get_audit_log(limit=limit)
    
    def get_user_list(self):
        """
        Get list of all users (owner only)
        
        Returns:
            list: List of users
        """
        if not self.can_perform_action('manage_users'):
            raise PermissionError("Only owners can view user list")
        
        return self.db.get_all_users()
    
    def get_permitted_screens(self, role=None):
        """
        Get list of screens that a role can access
        
        Args:
            role (str, optional): Role to check. If None, uses current user's role
            
        Returns:
            list: List of permitted screen names
        """
        if role is None:
            role = self.get_current_role()
        
        if role in self.role_permissions:
            return self.role_permissions[role]['screens']
        
        return []  # No screens if role not found